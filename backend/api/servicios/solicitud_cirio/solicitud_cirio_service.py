import uuid
from io import BytesIO
import math 
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Max, Q

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from api.models import Acto, PapeletaSitio, Tramo, Puesto
from api.servicios.papeleta_telegram import TelegramWebhookService

class ReportesCiriosService:
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

                for papeleta in papeletas_para_actualizar:
                    if papeleta.hermano.telegram_chat_id:
                        nombre_puesto_asignado = papeleta.puesto.nombre if papeleta.puesto else "Cirio / Nazareno base"
                        
                        try:
                            TelegramWebhookService.notificar_papeleta_asignada(
                                chat_id=papeleta.hermano.telegram_chat_id,
                                nombre_hermano=papeleta.hermano.nombre,
                                nombre_acto=acto.nombre,
                                estado="ASIGNADA",
                                nombre_puesto=nombre_puesto_asignado
                            )
                        except Exception as e:
                            print(f"Error al enviar Telegram a {papeleta.hermano.nombre}: {e}")

            acto.fecha_ejecucion_cirios = ahora
            acto.save(update_fields=['fecha_ejecucion_cirios'])

        return len(papeletas_para_actualizar)



    @staticmethod
    def generar_pdf_cirios_asignados(acto, filtro_paso=None) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elementos = []
        styles = getSampleStyleSheet()

        titulo_texto = f"Asignación de Tramos y Cirios - {acto.nombre}"
        if filtro_paso == 'CRISTO':
            titulo_texto = f"Asignación Cirios (Cristo) - {acto.nombre}"
        elif filtro_paso == 'VIRGEN':
            titulo_texto = f"Asignación Cirios (Virgen) - {acto.nombre}"

        titulo = Paragraph(titulo_texto, styles['Title'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 20))

        asignaciones_query = PapeletaSitio.objects.filter(
            acto=acto,
            tramo__isnull=False
        ).filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True)
        )

        if filtro_paso:
            asignaciones_query = asignaciones_query.filter(tramo__paso=filtro_paso)

        asignaciones = asignaciones_query.select_related('hermano', 'puesto', 'tramo').order_by(
            F('hermano__numero_registro').asc(nulls_last=True) 
        )

        data = [["Nº Reg.", "Puesto", "Tramo", "Lado", "Orden"]]
        
        for asignacion in asignaciones:
            num_registro = str(asignacion.hermano.numero_registro) if asignacion.hermano.numero_registro else "Sin N.R."
            nombre_puesto = asignacion.puesto.nombre if asignacion.puesto else "Cirio"

            nombre_tramo = f"{asignacion.tramo.numero_orden}º - {asignacion.tramo.get_paso_display()}" if asignacion.tramo else "-"
            
            lado = asignacion.get_lado_display() if asignacion.lado else "-"
            orden = str(asignacion.orden_en_tramo) if asignacion.orden_en_tramo else "-"
            
            data.append([num_registro, nombre_puesto, nombre_tramo, lado, orden])

        if len(data) == 1:
            elementos.append(Paragraph("No se han asignado cirios para estos criterios.", styles['Normal']))
        else:
            table = Table(data, colWidths=[60, 140, 190, 80, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#800020")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elementos.append(table)

        doc.build(elementos)
        buffer.seek(0)
        return buffer