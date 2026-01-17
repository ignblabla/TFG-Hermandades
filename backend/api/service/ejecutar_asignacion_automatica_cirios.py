import uuid # <--- 1. IMPORTAMOS LIBRERÍA UUID
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Max 

from ..models import Acto, PapeletaSitio, Tramo, Puesto

def ejecutar_asignacion_automatica_cirios(acto_id: int):
    """
    Asigna tramos y números de papeleta a las solicitudes de cirio
    basándose en la antigüedad del hermano y la capacidad de los tramos.
    """
    
    # 1. Obtención y validación del Acto
    try:
        acto = Acto.objects.get(id=acto_id)
    except Acto.DoesNotExist:
        raise ValidationError("El acto especificado no existe.")

    ahora = timezone.now()

    # Validamos que el plazo de solicitud haya terminado
    if not acto.fin_solicitud_cirios:
         raise ValidationError("El acto no tiene configurada fecha de fin de solicitud.")
    
    if ahora <= acto.fin_solicitud_cirios:
        raise ValidationError(f"Aún no ha finalizado el plazo de solicitudes (Termina: {acto.fin_solicitud_cirios}). No se puede realizar el reparto.")

    # 2. Ejecución Transaccional (Todo o nada)
    with transaction.atomic():
        
        # --- PASO PREVIO: LIMPIEZA ---
        # Reseteamos asignaciones previas para permitir re-ejecución.
        # Importante: Limpiamos también fecha de emisión y código para regenerarlos nuevos.
        papeletas_a_resetear = PapeletaSitio.objects.filter(
            acto=acto,
            es_solicitud_insignia=False
        ).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA)
        
        papeletas_a_resetear.update(
            tramo=None,
            numero_papeleta=None,
            fecha_emision=None,        # <--- Limpiamos fecha
            codigo_verificacion=None,  # <--- Limpiamos código
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        )

        # --- CÁLCULO DEL INICIO DEL CONTADOR ---
        max_papeleta_existente = PapeletaSitio.objects.filter(
            acto=acto
        ).aggregate(Max('numero_papeleta'))['numero_papeleta__max']

        if max_papeleta_existente is None:
            contador_global_papeleta = 1
        else:
            contador_global_papeleta = max_papeleta_existente + 1

        # --- ALGORITMO DE REPARTO ---
        
        flujos = [
            {'nombre': 'CRISTO', 'cortejo_bool': True, 'paso_enum': Tramo.PasoCortejo.CRISTO},
            {'nombre': 'VIRGEN', 'cortejo_bool': False, 'paso_enum': Tramo.PasoCortejo.VIRGEN},
        ]

        for flujo in flujos:
            # A. Obtener Candidatos
            candidatos = PapeletaSitio.objects.filter(
                acto=acto,
                es_solicitud_insignia=False,
                puesto__cortejo_cristo=flujo['cortejo_bool'],
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
            ).select_related('hermano').order_by(
                'hermano__fecha_ingreso_corporacion', 
                'hermano__numero_registro', 
                'hermano__fecha_nacimiento'
            )

            # B. Obtener Tramos Disponibles
            tramos = Tramo.objects.filter(
                acto=acto,
                paso=flujo['paso_enum']
            ).order_by('-numero_orden')

            if not tramos.exists() and candidatos.exists():
                continue 

            # C. Lógica de Asignación
            iterator_tramos = iter(tramos)
            tramo_actual = next(iterator_tramos, None)
            
            cupo_actual_llenado = 0 

            for papeleta in candidatos:
                asignado = False
                
                while tramo_actual and not asignado:
                    capacidad_tramo = tramo_actual.numero_maximo_cirios
                    
                    if cupo_actual_llenado < capacidad_tramo:
                        # --- ASIGNACIÓN DE DATOS ---
                        papeleta.tramo = tramo_actual
                        papeleta.numero_papeleta = contador_global_papeleta
                        papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
                        papeleta.fecha_emision = ahora.date()
                        papeleta.codigo_verificacion = uuid.uuid4().hex[:8].upper() 

                        papeleta.save()
                        # ---------------------------
                        
                        cupo_actual_llenado += 1
                        contador_global_papeleta += 1 
                        asignado = True
                    else:
                        # Tramo lleno, pasamos al siguiente
                        try:
                            tramo_actual = next(iterator_tramos)
                            cupo_actual_llenado = 0 
                        except StopIteration:
                            tramo_actual = None
                            break
                
                if not asignado and not tramo_actual:
                    pass

    return True