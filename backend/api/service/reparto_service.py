from django.utils import timezone
from django.db import transaction
from django.db.models import Max
from ..models import Acto, PapeletaSitio, Puesto
from django.core.exceptions import ValidationError

class RepartoService:
    @staticmethod
    def ejecutar_asignacion_automatica(acto_id):
        """
        Algoritmo de asignación de insignias por antigüedad y preferencias.
        - Calcula disponibilidad dinámicamente (sin perder el cupo total).
        - Genera número de papeleta y fecha.
        - Gestiona estados NO_ASIGNADA.
        """
        try:
            acto = Acto.objects.get(id=acto_id)
        except Acto.DoesNotExist:
            raise ValidationError("El acto especificado no existe.")

        now = timezone.now()
        
        if not acto.fin_solicitud or now <= acto.fin_solicitud:
            raise ValidationError(f"El plazo de solicitud no ha finalizado aún. Acaba el: {acto.fin_solicitud}")

        puestos_candidatos = Puesto.objects.filter(
            acto=acto, 
            disponible=True
        )
        
        mapa_puestos = {}

        estados_ocupados = [
            PapeletaSitio.EstadoPapeleta.EMITIDA,
            PapeletaSitio.EstadoPapeleta.RECOGIDA,
            PapeletaSitio.EstadoPapeleta.LEIDA
        ]

        for p in puestos_candidatos:
            ocupadas_bd = p.papeletas_asignadas.filter(estado_papeleta__in=estados_ocupados).count()
            
            stock_real = p.numero_maximo_asignaciones - ocupadas_bd
            
            if stock_real > 0:
                p._stock_temp = stock_real 
                mapa_puestos[p.id] = p

        solicitudes = PapeletaSitio.objects.filter(
            acto=acto,
            es_solicitud_insignia=True,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto__isnull=True 
        ).select_related('hermano').order_by('hermano__numero_registro')

        asignaciones_realizadas = 0
        hermanos_sin_puesto = []

        with transaction.atomic():
            max_num_actual = PapeletaSitio.objects.filter(acto=acto).aggregate(
                max_val=Max('numero_papeleta')
            )['max_val']
            
            contador_papeleta = (max_num_actual or 0) + 1

            for solicitud in solicitudes:
                asignado = False
                
                preferencias = solicitud.preferencias.all().order_by('orden_prioridad')

                for pref in preferencias:
                    puesto_id = pref.puesto_solicitado_id
                    
                    if puesto_id in mapa_puestos:
                        puesto_obj = mapa_puestos[puesto_id]

                        if puesto_obj._stock_temp > 0:
                            
                            # --- ASIGNACIÓN ---
                            solicitud.puesto = puesto_obj
                            solicitud.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA 
                            solicitud.fecha_emision = now.date()
                            solicitud.numero_papeleta = contador_papeleta
                            solicitud.save()

                            contador_papeleta += 1 
                            asignaciones_realizadas += 1

                            puesto_obj._stock_temp -= 1
                            
                            if puesto_obj._stock_temp == 0:
                                puesto_obj.disponible = False
                                puesto_obj.save()
                                del mapa_puestos[puesto_id]

                            asignado = True
                            break 
                
                if not asignado:
                    solicitud.estado_papeleta = PapeletaSitio.EstadoPapeleta.NO_ASIGNADA
                    solicitud.save()
                    hermanos_sin_puesto.append(f"{solicitud.hermano} (Num: {solicitud.hermano.numero_registro})")

        return {
            "mensaje": "Proceso finalizado correctamente",
            "asignaciones": asignaciones_realizadas,
            "sin_asignar_count": len(hermanos_sin_puesto),
            "sin_asignar_lista": hermanos_sin_puesto
        }