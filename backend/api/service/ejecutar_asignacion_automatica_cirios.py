import uuid 
import math 
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Max 

from ..models import Acto, PapeletaSitio, Tramo, Puesto

def ejecutar_asignacion_automatica_cirios(acto_id: int):
    """
    Asigna tramos y números de papeleta equilibrando la carga (Reparto Equitativo)
    y utiliza bulk_update para optimizar el rendimiento en BBDD.
    """

    try:
        acto = Acto.objects.get(id=acto_id)
    except:
        raise ValidationError("El acto especificado no existe.")
    
    ahora = timezone.now()

    if not acto.inicio_solicitud_cirios:
        raise ValidationError("El acto no tiene configurada fecha de fin de solicitud.")
    
    if ahora <= acto.fin_solicitud_cirios:
        raise ValidationError(f"Aún no ha finalizado el plazo (Termina: {acto.fin_solicitud_cirios}).")
    
    with transaction.atomic():
        PapeletaSitio.objects.filter(
            acto=acto,
            es_solicitud_insignia=False
        ).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).update(
            tramo=None,
            numero_papeleta=None,
            fecha_emision=None,
            codigo_verificacion=None,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        )

        max_papeleta_existente = PapeletaSitio.objects.filter(
            acto=acto
        ).aggregate(Max('numero_papeleta'))['numero_papeleta__max']

        contador_global_papeleta = 1 if max_papeleta_existente is None else max_papeleta_existente + 1

        papeletas_para_actualizar = []

        flujos = [
            {'nombre': 'CRISTO', 'cortejo_bool': True, 'paso_enum': Tramo.PasoCortejo.CRISTO},
            {'nombre': 'VIRGEN', 'cortejo_bool': False, 'paso_enum': Tramo.PasoCortejo.VIRGEN},
        ]

        for flujo in flujos:
            qs_candidatos = PapeletaSitio.objects.filter(
                acto=acto,
                es_solicitud_insignia = False,
                puesto__cortejo_cristo=flujo['cortejo_bool'],
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
            ).select_related('hermano').order_by(
                'hermano__fecha_ingreso_corporacion', 
                'hermano__numero_registro',
                'hermano__fecha_nacimiento'
            )

            lista_candidatos = list(qs_candidatos)
            total_candidatos_pendientes = len(lista_candidatos)
            index_candidato_actual = 0

            qs_tramos = Tramo.objects.filter(
                acto=acto,
                paso=flujo['paso_enum']
            ).order_by('-numero_orden')
            
            lista_tramos = list(qs_tramos)
            total_tramos = len(lista_tramos)

            if total_tramos == 0 or total_candidatos_pendientes == 0:
                continue 

            for i, tramo_actual in enumerate(lista_tramos):
                if total_candidatos_pendientes <= 0:
                    break

                tramos_restantes = total_tramos - i
                
                cupo_ideal = math.ceil(total_candidatos_pendientes / tramos_restantes)
                cantidad_a_asignar = min(cupo_ideal, tramo_actual.numero_maximo_cirios)

                batch_hermanos = lista_candidatos[index_candidato_actual : index_candidato_actual + cantidad_a_asignar]

                fecha_hoy = ahora.date()
                
                for papeleta in batch_hermanos:
                    papeleta.tramo = tramo_actual
                    papeleta.numero_papeleta = contador_global_papeleta
                    papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
                    papeleta.fecha_emision = fecha_hoy
                    papeleta.codigo_verificacion = uuid.uuid4().hex[:32].upper()
                    
                    papeletas_para_actualizar.append(papeleta)
                    
                    contador_global_papeleta += 1

                cantidad_asignada_real = len(batch_hermanos)
                index_candidato_actual += cantidad_asignada_real
                total_candidatos_pendientes -= cantidad_asignada_real

        # --- PERSISTENCIA MASIVA (BULK UPDATE) ---
        if papeletas_para_actualizar:
            PapeletaSitio.objects.bulk_update(
                papeletas_para_actualizar, 
                fields=[
                    'tramo', 
                    'numero_papeleta', 
                    'estado_papeleta', 
                    'fecha_emision', 
                    'codigo_verificacion'
                ],
                batch_size=1000
            )

    return True