import uuid 
import math 
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Max 

from ..models import Acto, PapeletaSitio, Tramo, Puesto

def ejecutar_asignacion_automatica_cirios(acto_id: int):
    """
    Asigna tramos, números de papeleta y POSICIONES (orden y lado).
    Gestiona VINCULACIONES: Si A (antiguo) va con B (nuevo), ambos ocupan 
    el sitio que le corresponde a B.
    """

    try:
        acto = Acto.objects.get(id=acto_id)
    except Acto.DoesNotExist:
        raise ValidationError("El acto especificado no existe.")
    
    ahora = timezone.now()

    if not acto.inicio_solicitud_cirios:
        raise ValidationError("El acto no tiene configurada fecha de fin de solicitud.")
    
    # if ahora <= acto.fin_solicitud_cirios:
    #     raise ValidationError(f"Aún no ha finalizado el plazo (Termina: {acto.fin_solicitud_cirios}).")
    
    with transaction.atomic():
        # 1. LIMPIEZA PREVIA
        PapeletaSitio.objects.filter(
            acto=acto,
            es_solicitud_insignia=False
        ).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).update(
            tramo=None,
            numero_papeleta=None,
            fecha_emision=None,
            codigo_verificacion=None,
            orden_en_tramo=None,
            lado=None,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        )

        # 2. Obtener último número
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
            # ---------------------------------------------------------
            # A. OBTENCIÓN DE CANDIDATOS (Raw)
            # ---------------------------------------------------------
            # Obtenemos todos los candidatos del flujo actual.
            # Nota: El orden inicial en SQL da igual, lo haremos en Python.
            qs_candidatos = PapeletaSitio.objects.filter(
                acto=acto,
                es_solicitud_insignia=False,
                puesto__cortejo_cristo=flujo['cortejo_bool'],
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
            ).select_related('hermano')

            # Convertimos a lista para manipular en memoria
            raw_candidatos = list(qs_candidatos)
            
            # Mapa rápido para buscar papeletas por ID de hermano (necesario para las vinculaciones)
            # Key: ID del Hermano, Value: Objeto PapeletaSitio
            mapa_hermanos_papeletas = {p.hermano.id: p for p in raw_candidatos}
            
            # ---------------------------------------------------------
            # B. LÓGICA DE VINCULACIÓN Y REORDENAMIENTO
            # ---------------------------------------------------------
            grupos_procesados = [] # Lista de tuplas: (fecha_efectiva, [papeleta1, papeleta2])
            ids_procesados = set() # Para no duplicar hermanos ya agrupados

            for papeleta in raw_candidatos:
                if papeleta.id in ids_procesados:
                    continue

                grupo = [papeleta]
                ids_procesados.add(papeleta.id)
                
                # Determinamos la fecha de ordenación base
                fecha_efectiva = papeleta.hermano.fecha_ingreso_corporacion
                if not fecha_efectiva: # Fallback por si hay datos sucios
                    fecha_efectiva = timezone.now().date()

                # Revisamos si tiene vinculación
                if papeleta.vinculado_a:
                    id_vinculado = papeleta.vinculado_a.id
                    
                    # Verificamos si el hermano vinculado TAMBIÉN sale en este cortejo
                    if id_vinculado in mapa_hermanos_papeletas:
                        papeleta_vinculada = mapa_hermanos_papeletas[id_vinculado]
                        
                        # Si la otra papeleta no ha sido procesada aún, la añadimos al grupo
                        if papeleta_vinculada.id not in ids_procesados:
                            grupo.append(papeleta_vinculada)
                            ids_procesados.add(papeleta_vinculada.id)
                            
                            # LÓGICA CORE: Nos quedamos con la fecha MÁS RECIENTE (Menos antigüedad)
                            fecha_vinc = papeleta_vinculada.hermano.fecha_ingreso_corporacion
                            if fecha_vinc and fecha_vinc > fecha_efectiva:
                                fecha_efectiva = fecha_vinc

                # Añadimos criterios secundarios de ordenación (Num Registro) para desempatar fechas iguales
                registro_maximo = max(p.hermano.numero_registro for p in grupo if p.hermano.numero_registro)
                
                # Guardamos el grupo con su "fecha efectiva" para ordenar
                grupos_procesados.append({
                    'fecha_sort': fecha_efectiva,
                    'registro_sort': registro_maximo,
                    'papeletas': grupo
                })

            # ORDENACIÓN DE LA LISTA MAESTRA
            # Ordenamos los GRUPOS. Primero por fecha (ascendente: antiguos primero), luego por registro.
            # Al ordenar por fecha ascendente (1980, 1990, 2020), los más antiguos quedan en índice 0.
            grupos_procesados.sort(key=lambda x: (x['fecha_sort'], x['registro_sort']))

            # APLANAMIENTO (Flatten)
            # Convertimos la lista de grupos de vuelta a una lista plana de papeletas
            lista_candidatos_final = []
            for item in grupos_procesados:
                # Dentro del grupo (pareja), ¿quién va primero? 
                # Normalmente a la derecha va el más antiguo de la pareja, o por orden de lista.
                # Aquí los añadimos tal cual, pero garantizamos que van seguidos.
                lista_candidatos_final.extend(item['papeletas'])

            # ---------------------------------------------------------
            # C. ASIGNACIÓN A TRAMOS (Igual que antes)
            # ---------------------------------------------------------
            
            lista_candidatos = lista_candidatos_final
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
                
                contador_interno_tramo = 0 
                
                for papeleta in batch_hermanos:
                    papeleta.tramo = tramo_actual
                    papeleta.numero_papeleta = contador_global_papeleta
                    papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
                    papeleta.fecha_emision = fecha_hoy
                    papeleta.codigo_verificacion = uuid.uuid4().hex[:32].upper()
                    
                    papeleta.orden_en_tramo = (contador_interno_tramo // 2) + 1
                    
                    if contador_interno_tramo % 2 == 0:
                        papeleta.lado = PapeletaSitio.LadoTramo.DERECHA
                    else:
                        papeleta.lado = PapeletaSitio.LadoTramo.IZQUIERDA
                    
                    papeletas_para_actualizar.append(papeleta)
                    
                    contador_global_papeleta += 1
                    contador_interno_tramo += 1

                cantidad_asignada_real = len(batch_hermanos)
                index_candidato_actual += cantidad_asignada_real
                total_candidatos_pendientes -= cantidad_asignada_real

        if papeletas_para_actualizar:
            PapeletaSitio.objects.bulk_update(
                papeletas_para_actualizar, 
                fields=[
                    'tramo', 
                    'numero_papeleta', 
                    'estado_papeleta', 
                    'fecha_emision', 
                    'codigo_verificacion',
                    'orden_en_tramo',
                    'lado'
                ],
                batch_size=1000
            )

    return True