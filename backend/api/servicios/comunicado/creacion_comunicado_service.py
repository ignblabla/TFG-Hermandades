from django.db import transaction
from django.core.exceptions import PermissionDenied
import requests
from api.models import AreaInteres, Comunicado, CuerpoPertenencia
from django.conf import settings

from api.servicios import comunicado


class ComunicadoService:

    def _verificar_permisos(self, usuario):
        """Helper interno para validar permisos de Admin o Junta."""
        es_admin = getattr(usuario, 'esAdmin', False)
        es_junta = usuario.cuerpos.filter(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        ).exists()

        if not (es_admin or es_junta):
            raise PermissionDenied("No tienes permisos para gestionar comunicados.")
        

    @transaction.atomic
    def create_comunicado(self, usuario, data_validada):
        self._verificar_permisos(usuario)
        
        areas = data_validada.pop('areas_interes', [])
        comunicado = Comunicado.objects.create(autor=usuario, **data_validada)
        
        if areas:
            comunicado.areas_interes.set(areas)

        self._notificar_telegram(comunicado, areas)

        return comunicado
    
    def _notificar_telegram(self, comunicado, areas_ids):
        """
        Método auxiliar para enviar notificaciones con o sin imagen.
        """
        areas_con_telegram = AreaInteres.objects.filter(
            id__in=[a.id for a in areas_ids], 
            telegram_channel_id__isnull=False
        ).exclude(telegram_channel_id__exact='')

        canales_a_enviar = set(area.telegram_channel_id for area in areas_con_telegram)

        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            print("TELEGRAM_BOT_TOKEN no configurado.")
            return

        texto_mensaje = f"<b>🔔 Nuevo Comunicado: {comunicado.titulo}</b>\n\n{comunicado.contenido}"

        for channel_id in canales_a_enviar:
            try:
                if comunicado.imagen_portada:
                    url = f"https://api.telegram.org/bot{token}/sendPhoto"

                    caption = texto_mensaje
                    if len(caption) > 1000:
                        caption = caption[:1000] + "... (ver web)"

                    payload = {
                        "chat_id": channel_id,
                        "caption": caption,
                        "parse_mode": "HTML"
                    }

                    with comunicado.imagen_portada.open('rb') as imagen_file:
                        files = {'photo': imagen_file}
                        requests.post(url, data=payload, files=files, timeout=10)

                else:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"

                    mensaje = texto_mensaje
                    if len(mensaje) > 3000:
                        mensaje = mensaje[:3000] + "..."

                    payload = {
                        "chat_id": channel_id,
                        "text": mensaje,
                        "parse_mode": "HTML"
                    }
                    requests.post(url, data=payload, timeout=5)
                
            except Exception as e:
                print(f"Error enviando telegram al canal {channel_id}: {e}")


    @transaction.atomic
    def update_comunicado(self, usuario, comunicado_instance, data_validada):
        """
        Actualiza un comunicado existente.
        """
        self._verificar_permisos(usuario)

        if 'areas_interes' in data_validada:
            areas = data_validada.pop('areas_interes')
            comunicado_instance.areas_interes.set(areas)

        for attr, value in data_validada.items():
            setattr(comunicado_instance, attr, value)

        comunicado_instance.save()
        return comunicado_instance

    @transaction.atomic
    def delete_comunicado(self, usuario, comunicado_instance):
        """
        Borra un comunicado.
        """
        self._verificar_permisos(usuario)
        comunicado_instance.delete()