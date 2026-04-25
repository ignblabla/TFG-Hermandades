import os
import math
import requests
from django.db import transaction
from google import genai
from google.genai import types
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from api.models import AreaInteres, Comunicado, CuerpoPertenencia
from api.servicios.comunicado.gemini_service import generar_y_guardar_embedding_async
from api.servicios.comunicado.podcast_service import generar_y_guardar_podcast_async


class ComunicadoService:
    def _verificar_permisos(self, usuario):
        """Helper interno para validar permisos de Admin o Junta."""
        if not usuario.is_authenticated:
            raise PermissionDenied("No tienes permisos para gestionar comunicados.")

        if getattr(usuario, 'esAdmin', False):
            return

        if hasattr(usuario, 'cuerpos'):
            es_junta = usuario.cuerpos.filter(
                nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()
            
            if es_junta:
                return

        raise PermissionDenied("No tienes permisos para gestionar comunicados.")
        


    @transaction.atomic
    def create_comunicado(self, usuario, data_validada):
        self._verificar_permisos(usuario)

        data_validada.pop('autor', None) 
        data_validada.pop('autor_id', None)

        areas = data_validada.pop('areas_interes', [])

        comunicado = Comunicado.objects.create(autor=usuario, **data_validada)
        
        if areas:
            comunicado.areas_interes.set(areas)

        self._notificar_telegram(comunicado, areas)

        transaction.on_commit(
            lambda: generar_y_guardar_embedding_async(comunicado.id)
        )

        if comunicado.generar_podcast:
            transaction.on_commit(
                lambda: generar_y_guardar_podcast_async(comunicado.id)
            )

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
        self._verificar_permisos(usuario)

        if 'areas_interes' in data_validada:
            areas = data_validada.pop('areas_interes')
            comunicado_instance.areas_interes.set(areas)

        generar_nuevo_vector = False
        titulo_nuevo = data_validada.get('titulo')
        contenido_nuevo = data_validada.get('contenido')

        if (titulo_nuevo and titulo_nuevo != comunicado_instance.titulo) or \
        (contenido_nuevo and contenido_nuevo != comunicado_instance.contenido):
            generar_nuevo_vector = True

        for attr, value in data_validada.items():
            if not hasattr(comunicado_instance, attr):
                raise AttributeError(f"El campo '{attr}' no existe en el modelo Comunicado.")
            
            setattr(comunicado_instance, attr, value)

        comunicado_instance.save()

        if generar_nuevo_vector:
            transaction.on_commit(
                lambda: generar_y_guardar_embedding_async(comunicado_instance.id)
            )

            if comunicado_instance.generar_podcast:
                transaction.on_commit(
                    lambda: generar_y_guardar_podcast_async(comunicado_instance.id)
                )
            
        return comunicado_instance



    @transaction.atomic
    def delete_comunicado(self, usuario, comunicado_instance):
        """
        Borra un comunicado y limpia los archivos multimedia asociados del servidor.
        """
        self._verificar_permisos(usuario)

        imagen_adjunta = comunicado_instance.imagen_portada

        comunicado_instance.delete()

        if imagen_adjunta:
            def eliminar_archivo_seguro():
                try:
                    imagen_adjunta.delete(save=False)
                except Exception:
                    pass
            
            transaction.on_commit(eliminar_archivo_seguro)
            
        return True



    def obtener_ultimos_comunicados_areas_usuario(usuario):
        """
        Obtiene los 2 últimos comunicados publicados que pertenezcan a alguna 
        de las áreas de interés a las que está suscrito el usuario.
        Si no tiene áreas asignadas, devuelve los 2 últimos de TODOS_HERMANOS.
        """
        areas_usuario = usuario.areas_interes.all()

        if not areas_usuario.exists():
            return Comunicado.objects.filter(
                areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS
            ).distinct().order_by('-fecha_emision')[:2]

        return Comunicado.objects.filter(
            areas_interes__in=areas_usuario
        ).distinct().order_by('-fecha_emision')[:2]



    def obtener_comunicados_relacionados_usuario(usuario, comunicado_actual_id):
        """
        Obtiene los 3 últimos comunicados publicados de las áreas de interés del usuario,
        excluyendo explícitamente el comunicado que se está leyendo.
        Si no tiene áreas asignadas, devuelve los 3 últimos de TODOS_HERMANOS.
        """
        areas_usuario = usuario.areas_interes.all()

        queryset_base = Comunicado.objects.exclude(id=comunicado_actual_id)

        if not areas_usuario.exists():
            return queryset_base.filter(
                areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS
            ).distinct().order_by('-fecha_emision')[:3]

        return queryset_base.filter(
            areas_interes__in=areas_usuario
        ).distinct().order_by('-fecha_emision')[:3]