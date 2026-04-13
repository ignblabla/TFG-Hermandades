import uuid 
import math 
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Max, Q

from ..models import Acto, PapeletaSitio, Tramo, Puesto

def ejecutar_asignacion_automatica_cirios(acto_id: int):
    """
    Algoritmo de reparto de cirios con INTEGRIDAD DE GRUPOS.
    Retorna el número de papeletas que han sido asignadas con éxito.
    """
    with transaction.atomic():
        try:
            acto = Acto.objects.select_for_update().get(id=acto_id)
        except Acto.DoesNotExist:
            raise ValidationError("El acto especificado no existe.")
        
        if acto.fecha_ejecucion_cirios is not None:
            raise ValidationError(f"El reparto de cirios ya se ejecutó el {acto.fecha_ejecucion_cirios.strftime('%d/%m/%Y %H:%M')}.")
            
        if acto.modalidad == Acto.ModalidadReparto.TRADICIONAL and acto.fecha_ejecucion_reparto is None:
            raise ValidationError("No se puede ejecutar el reparto de cirios sin haber ejecutado previamente el de insignias.")
        
        if not acto.inicio_solicitud_cirios:
            raise ValidationError("El acto no tiene configuradas las fechas de solicitud de cirios.")
        
        ahora = timezone.now()
        fecha_hoy = ahora.date()

        # 1. Resetear el estado de las papeletas de cirio previas
        PapeletaSitio.objects.filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True),
            acto=acto
        ).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).update(
            tramo=None,
            numero_papeleta=None,
            fecha_emision=None,
            codigo_verificacion=None,
            orden_en_tramo=None,
            lado=None,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        )

        max_papeleta_existente = PapeletaSitio.objects.filter(
            acto=acto
        ).aggregate(Max('numero_papeleta'))['numero_papeleta__max']

        contador_global_papeleta = 1 if max_papeleta_existente is None else max_papeleta_existente + 1
        papeletas_para_actualizar = []
        candidatos_totales = 0

        flujos = [
            {'nombre': 'CRISTO', 'cortejo_bool': True, 'paso_enum': Tramo.PasoCortejo.CRISTO},
            {'nombre': 'VIRGEN', 'cortejo_bool': False, 'paso_enum': Tramo.PasoCortejo.VIRGEN},
        ]

        for flujo in flujos:
            qs_candidatos = PapeletaSitio.objects.filter(
                Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True),
                acto=acto,
                puesto__cortejo_cristo=flujo['cortejo_bool'],
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
            ).select_related('hermano')

            raw_candidatos = list(qs_candidatos)
            candidatos_totales += len(raw_candidatos)
            
            mapa_hermanos_papeletas = {p.hermano.id: p for p in raw_candidatos}
            
            mapa_solicitudes_inversas = {}
            for p in raw_candidatos:
                if p.vinculado_a_id:
                    target_id = p.vinculado_a_id
                    if target_id not in mapa_solicitudes_inversas:
                        mapa_solicitudes_inversas[target_id] = []
                    mapa_solicitudes_inversas[target_id].append(p)

            grupos_procesados = []
            ids_procesados = set()

            for papeleta in raw_candidatos:
                if papeleta.id in ids_procesados:
                    continue

                grupo = [papeleta]
                ids_procesados.add(papeleta.id)

                if papeleta.vinculado_a_id:
                    id_destino = papeleta.vinculado_a_id
                    if id_destino in mapa_hermanos_papeletas:
                        target_papeleta = mapa_hermanos_papeletas[id_destino]
                        if target_papeleta.id not in ids_procesados:
                            grupo.append(target_papeleta)
                            ids_procesados.add(target_papeleta.id)

                mi_hermano_id = papeleta.hermano.id
                if mi_hermano_id in mapa_solicitudes_inversas:
                    solicitantes = mapa_solicitudes_inversas[mi_hermano_id]
                    for solicitante in solicitantes:
                        if solicitante.id not in ids_procesados:
                            grupo.append(solicitante)
                            ids_procesados.add(solicitante.id)

                fechas = [p.hermano.fecha_ingreso_corporacion or fecha_hoy for p in grupo]
                fecha_efectiva_grupo = max(fechas)
                
                registros = [p.hermano.numero_registro or 999999 for p in grupo]
                registro_maximo_grupo = max(registros)

                grupos_procesados.append({
                    'fecha_sort': fecha_efectiva_grupo,
                    'registro_sort': registro_maximo_grupo,
                    'papeletas': grupo
                })

            grupos_procesados.sort(key=lambda x: (x['fecha_sort'], x['registro_sort']))

            qs_tramos = Tramo.objects.filter(
                acto=acto,
                paso=flujo['paso_enum']
            ).order_by('-numero_orden')

            lista_tramos = list(qs_tramos)

            total_grupos = len(grupos_procesados)
            total_tramos = len(lista_tramos)
            
            if total_tramos == 0 and total_grupos > 0:
                raise ValidationError(f"Hay hermanos solicitando sitio en {flujo['nombre']} pero no existen tramos configurados para ese paso.")
            
            index_grupo_actual = 0

            for i, tramo_actual in enumerate(lista_tramos):
                if index_grupo_actual >= total_grupos:
                    break

                tramos_restantes = total_tramos - i

                personas_restantes_count = sum(len(grupos_procesados[k]['papeletas']) for k in range(index_grupo_actual, total_grupos))

                if tramos_restantes > 0:
                    cupo_ideal = math.ceil(personas_restantes_count / tramos_restantes)
                else:
                    cupo_ideal = personas_restantes_count

                ocupacion_actual_tramo = 0
                contador_interno_tramo = 0 

                while index_grupo_actual < total_grupos:
                    grupo_data = grupos_procesados[index_grupo_actual]
                    grupo_papeletas = grupo_data['papeletas']
                    tamano_grupo = len(grupo_papeletas)

                    if (ocupacion_actual_tramo + tamano_grupo) > tramo_actual.numero_maximo_cirios:
                        if tamano_grupo > tramo_actual.numero_maximo_cirios:
                            raise ValidationError(f"El grupo vinculado al hermano {grupo_papeletas[0].hermano} tiene {tamano_grupo} personas y supera la capacidad total del tramo {tramo_actual.nombre} ({tramo_actual.numero_maximo_cirios}).")
                        break 

                    if ocupacion_actual_tramo >= cupo_ideal:
                        break 

                    for papeleta in grupo_papeletas:
                        papeleta.tramo = tramo_actual
                        papeleta.numero_papeleta = contador_global_papeleta
                        papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
                        papeleta.fecha_emision = fecha_hoy
                        papeleta.codigo_verificacion = uuid.uuid4().hex[:12].upper()

                        papeleta.orden_en_tramo = (contador_interno_tramo // 2) + 1
                        
                        if contador_interno_tramo % 2 == 0:
                            papeleta.lado = PapeletaSitio.LadoTramo.DERECHA
                        else:
                            papeleta.lado = PapeletaSitio.LadoTramo.IZQUIERDA
                        
                        papeletas_para_actualizar.append(papeleta)
                        
                        contador_global_papeleta += 1
                        contador_interno_tramo += 1

                    ocupacion_actual_tramo += tamano_grupo
                    index_grupo_actual += 1

            if index_grupo_actual < total_grupos:
                personas_sin_asignar = sum(len(grupos_procesados[k]['papeletas']) for k in range(index_grupo_actual, total_grupos))
                raise ValidationError(
                    f"ERROR DE AFORO EN {flujo['nombre']}: Se han quedado {personas_sin_asignar} hermanos sin asignar "
                    f"por falta de espacio físico en los tramos. Por favor, aumente el aforo máximo de los tramos o cree nuevos."
                )

        # NUEVA DEFENSA: Explicación exacta de por qué falla si hay 0 procesados
        if candidatos_totales == 0:
            sin_puesto = PapeletaSitio.objects.filter(acto=acto, puesto__isnull=True).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).count()
            es_insignia = PapeletaSitio.objects.filter(acto=acto, es_solicitud_insignia=True).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).count()
            total_activas = PapeletaSitio.objects.filter(acto=acto).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).count()
            
            raise ValidationError(
                f"No se ha encontrado ninguna papeleta válida para asignar a tramos. "
                f"Detalle del Acto (Total activas: {total_activas}) -> "
                f"Ignoradas por ser Insignias: {es_insignia} | "
                f"Ignoradas por NO tener Puesto asignado: {sin_puesto}. "
                f"Para que el algoritmo funcione, las papeletas de cirio DEBEN tener un Puesto asociado para saber si van en Cristo o Virgen."
            )

        if papeletas_para_actualizar:
            PapeletaSitio.objects.bulk_update(
                papeletas_para_actualizar, 
                fields=[
                    'tramo', 'numero_papeleta', 'estado_papeleta', 
                    'fecha_emision', 'codigo_verificacion', 
                    'orden_en_tramo', 'lado'
                ],
                batch_size=1000
            )

        acto.fecha_ejecucion_cirios = ahora
        acto.save(update_fields=['fecha_ejecucion_cirios'])

    # Retornamos cuántas se actualizaron para que la Vista nos lo diga
    return len(papeletas_para_actualizar)