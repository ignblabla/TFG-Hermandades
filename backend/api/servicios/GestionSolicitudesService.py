from api.models import Acto, CuerpoPertenencia, PapeletaSitio, PreferenciaSolicitud
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError


class GestionSolicitudesService:
    # -----------------------------------------------------------------------------
    # SERVICES: SOLICITAR PAPELETA MODO UNIFICADO
    # -----------------------------------------------------------------------------
    @staticmethod
    def procesar_solicitud_unificada(hermano, acto, preferencias_data):
        ahora = timezone.now()

        # -----------------------------------------------------------------
        # 0. VALIDACIÓN DE MODALIDAD (¡NUEVO!)
        # -----------------------------------------------------------------
        # Esto es vital. Si el acto es TRADICIONAL, este endpoint debe rechazarlo.
        if acto.modalidad != Acto.ModalidadReparto.UNIFICADO:
            raise ValidationError(
                f"La solicitud unificada no está disponible para el acto '{acto.nombre}'. "
                f"Su modalidad es '{acto.get_modalidad_display()}'."
            )

        # -----------------------------------------------------------------
        # 1. VALIDACIÓN DE FECHAS (Regla estricta solicitada)
        # -----------------------------------------------------------------
        if not acto.inicio_solicitud or not acto.fin_solicitud:
            raise ValidationError("El plazo de solicitud no está configurado para este acto.")
            
        if ahora < acto.inicio_solicitud:
            raise ValidationError(f"El plazo de solicitud aún no ha comenzado. Empieza el {acto.inicio_solicitud}.")
        
        if ahora > acto.fin_solicitud:
            raise ValidationError(f"El plazo de solicitud finalizó el {acto.fin_solicitud}.")
        
        # -----------------------------------------------------------------
        # 2. VALIDACIÓN DE TIPO DE ACTO
        # -----------------------------------------------------------------
        if not acto.tipo_acto.requiere_papeleta:
            raise ValidationError(f"El acto '{acto.nombre}' no admite solicitudes de papeleta de sitio.")
        
        # -----------------------------------------------------------------
        # 3. VALIDACIÓN DE REGLAS DE PUESTOS (Tu nueva lógica aquí)
        # -----------------------------------------------------------------
        tipos_no_insignia_vistos = set()

        if preferencias_data:
            for item in preferencias_data:
                puesto = item['puesto_solicitado'] 
                
                tipo = puesto.tipo_puesto 

                if not tipo.es_insignia:
                    if tipo.id in tipos_no_insignia_vistos:
                        raise ValidationError(
                        f"No puedes solicitar más de un puesto del tipo '{tipo.nombre_tipo}' (ej: Cirio) en la misma solicitud."
                    )
                    tipos_no_insignia_vistos.add(tipo.id)
        
        # -----------------------------------------------------------------
        # 3. VALIDACIÓN DE CUERPOS DE PERTENENCIA
        # -----------------------------------------------------------------
        cuerpos_permitidos = [
            CuerpoPertenencia.NombreCuerpo.NAZARENOS,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL
        ]

        mis_cuerpos = hermano.cuerpos.all()

        if mis_cuerpos.exists():
            es_miembro_valido = mis_cuerpos.filter(nombre_cuerpo__in=cuerpos_permitidos).exists()
            if not es_miembro_valido:
                raise ValidationError("Tu cuerpo de pertenencia actual no permite solicitar papeleta de sitio para este acto.")
            
        # -----------------------------------------------------------------
        # 4. VALIDACIÓN DE UNICIDAD (Una papeleta por acto)
        # -----------------------------------------------------------------
        if PapeletaSitio.objects.filter(hermano=hermano, acto=acto).exists():
            raise ValidationError("Ya has realizado una solicitud de papeleta para este acto.")
        
        with transaction.atomic():
            nueva_papeleta = PapeletaSitio.objects.create(
                hermano=hermano,
                acto=acto,
                anio=ahora.year,
                fecha_solicitud=ahora,
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
                es_solicitud_insignia=False 
            )

            es_insignia_global = False

            if preferencias_data:
                for item in preferencias_data:
                    puesto = item['puesto_solicitado']
                    orden = item['orden_prioridad']
                    
                    if puesto.tipo_puesto.es_insignia:
                        es_insignia_global = True

                    PreferenciaSolicitud.objects.create(
                        papeleta=nueva_papeleta,
                        puesto_solicitado=puesto,
                        orden_prioridad=orden
                    )
            
            if es_insignia_global:
                nueva_papeleta.es_solicitud_insignia = True
                nueva_papeleta.save(update_fields=['es_solicitud_insignia'])

            return nueva_papeleta