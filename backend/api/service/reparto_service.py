from django.utils import timezone
from django.db import transaction
from django.db.models import Max, F, Count, Q
from ..models import Acto, PapeletaSitio, Puesto
from django.core.exceptions import ValidationError

class RepartoService:
    @staticmethod
    def ejecutar_asignacion_automatica(acto_id):
        """
        Algoritmo de asignación de insignias por antigüedad estricta.
        CORRECCIONES APLICADAS:
        1. Atomicidad completa: Lectura de stock y escritura ocurren dentro de la transacción.
        2. Bloqueo pesimista: Se usa select_for_update para evitar condiciones de carrera.
        3. Optimización: Uso de prefetch_related para evitar el problema N+1.
        4. Lógica: No se modifica el flag 'disponible' del Puesto, solo se gestiona stock en memoria.
        5. Ordenación: Manejo explícito de nulos en numero_registro.
        """
        try:
            acto = Acto.objects.get(id=acto_id)
        except Acto.DoesNotExist:
            raise ValidationError("El acto especificado no existe.")

        now = timezone.now()
        if acto.fin_solicitud and now <= acto.fin_solicitud:
            raise ValidationError(f"El plazo de solicitud no ha finalizado aún. Acaba el: {acto.fin_solicitud}")

        asignaciones_realizadas = 0
        hermanos_sin_puesto = []


        with transaction.atomic():

            puestos_candidatos = Puesto.objects.filter(
                acto=acto, 
                disponible=True
            ).select_for_update().annotate(
                total_ocupadas=Count(
                    'papeletas_asignadas',
                    filter=Q(papeletas_asignadas__estado_papeleta__in=[
                        PapeletaSitio.EstadoPapeleta.EMITIDA,
                        PapeletaSitio.EstadoPapeleta.RECOGIDA,
                        PapeletaSitio.EstadoPapeleta.LEIDA
                    ])
                )
            )
            
            mapa_puestos = {}

            for p in puestos_candidatos:
                
                stock_real = p.numero_maximo_asignaciones - p.total_ocupadas
                
                if stock_real > 0:
                    p._stock_temp = stock_real 
                    mapa_puestos[p.id] = p

            solicitudes = PapeletaSitio.objects.filter(
                acto=acto,
                es_solicitud_insignia=True,
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
                puesto__isnull=True 
            ).select_related(
                'hermano'
            ).prefetch_related(
                'preferencias', 
                'preferencias__puesto_solicitado'
            ).order_by(
                F('hermano__numero_registro').asc(nulls_last=True)
            )

            max_num_actual = PapeletaSitio.objects.filter(acto=acto).aggregate(
                max_val=Max('numero_papeleta')
            )['max_val']
            
            contador_papeleta = (max_num_actual or 0) + 1
            fecha_emision = now.date()

            for solicitud in solicitudes:
                asignado = False
                
                preferencias = solicitud.preferencias.all().order_by('orden_prioridad')

                for pref in preferencias:
                    puesto_id = pref.puesto_solicitado_id
                    
                    if puesto_id in mapa_puestos:
                        puesto_obj = mapa_puestos[puesto_id]

                        if puesto_obj._stock_temp > 0:
                            solicitud.puesto = puesto_obj
                            solicitud.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA 
                            solicitud.fecha_emision = fecha_emision
                            solicitud.numero_papeleta = contador_papeleta
                            solicitud.save()

                            contador_papeleta += 1 
                            asignaciones_realizadas += 1
                            puesto_obj._stock_temp -= 1

                            if puesto_obj._stock_temp == 0:
                                del mapa_puestos[puesto_id]

                            asignado = True
                            break
                
                if not asignado:
                    solicitud.estado_papeleta = PapeletaSitio.EstadoPapeleta.NO_ASIGNADA
                    solicitud.save()
                    hermanos_sin_puesto.append({
                        "id": solicitud.hermano.id,
                        "nombre": f"{solicitud.hermano.nombre} {solicitud.hermano.primer_apellido}",
                        "num_registro": solicitud.hermano.numero_registro
                    })

        return {
            "mensaje": "Proceso finalizado correctamente",
            "asignaciones": asignaciones_realizadas,
            "sin_asignar_count": len(hermanos_sin_puesto),
            "sin_asignar_lista": hermanos_sin_puesto
        }