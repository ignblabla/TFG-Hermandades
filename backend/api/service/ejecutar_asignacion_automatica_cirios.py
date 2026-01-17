from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F

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
        # Reseteamos asignaciones previas de CIRIOS (no insignias) para permitir re-ejecución
        # Ponemos estado en SOLICITADA, quitamos tramo y número.
        papeletas_a_resetear = PapeletaSitio.objects.filter(
            acto=acto,
            es_solicitud_insignia=False
        ).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA)
        
        papeletas_a_resetear.update(
            tramo=None,
            numero_papeleta=None,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        )

        # --- ALGORITMO DE REPARTO ---
        
        # Definimos los dos flujos de asignación
        flujos = [
            {'nombre': 'CRISTO', 'cortejo_bool': True, 'paso_enum': Tramo.PasoCortejo.CRISTO},
            {'nombre': 'VIRGEN', 'cortejo_bool': False, 'paso_enum': Tramo.PasoCortejo.VIRGEN},
        ]

        contador_global_papeleta = 1 # El número de papeleta suele ser único por acto, independientemente del paso

        for flujo in flujos:
            # A. Obtener Candidatos (Papeletas)
            # Filtramos por Acto, No Insignia, y el tipo de puesto elegido (Cristo/Virgen)
            # ORDENACIÓN CLAVE: Fecha ingreso ascendente (más antiguo primero)
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

            # B. Obtener Tramos Disponibles (Cubos)
            # Ordenamos por numero_orden DESCENDENTE. 
            # Asumimos que el Tramo con número más alto es el más cercano al paso (donde van los antiguos).
            # Ejemplo: Tramo 8 (Antiguos) -> Tramo 7 -> ... -> Tramo 1 (Nuevos/Niños)
            tramos = Tramo.objects.filter(
                acto=acto,
                paso=flujo['paso_enum']
            ).order_by('-numero_orden')

            if not tramos.exists() and candidatos.exists():
                # Log de advertencia o error si hay gente pero no tramos
                continue 

            # C. Lógica de Asignación (Filling Logic)
            iterator_tramos = iter(tramos)
            tramo_actual = next(iterator_tramos, None)
            
            # Control de capacidad en memoria para no hacer queries en cada iteración
            cupo_actual_llenado = 0 

            for papeleta in candidatos:
                asignado = False
                
                while tramo_actual and not asignado:
                    # Chequeamos capacidad del tramo actual
                    capacidad_tramo = tramo_actual.numero_maximo_cirios
                    
                    if cupo_actual_llenado < capacidad_tramo:
                        # HAY SITIO EN ESTE TRAMO
                        papeleta.tramo = tramo_actual
                        papeleta.numero_papeleta = contador_global_papeleta
                        papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA # O asignada
                        papeleta.save()
                        
                        cupo_actual_llenado += 1
                        contador_global_papeleta += 1
                        asignado = True
                    else:
                        # TRAMO LLENO -> PASAR AL SIGUIENTE (ANTERIOR EN ORDEN)
                        try:
                            tramo_actual = next(iterator_tramos)
                            cupo_actual_llenado = 0 # Reseteamos contador para el nuevo tramo
                        except StopIteration:
                            # NO HAY MÁS TRAMOS DISPONIBLES
                            # Opción A: Dejar sin asignar (se queda en tramo=None)
                            # Opción B: Forzar en el último tramo aunque exceda aforo (comentado)
                            tramo_actual = None
                            break
                
                if not asignado and not tramo_actual:
                    # Lógica de desborde: No caben más hermanos en la cofradía
                    # Podrías marcar estado como 'LISTA_ESPERA' o similar.
                    pass

    return True