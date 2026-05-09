from django.urls import path

from api.view.register_view import AprobarAltaHermanoView, HermanoCreateView
from api.view.gestion_solicitudes_views import CrearSolicitudUnificadaView
from api.vistas.cuota.cuota_view import MisCuotasListView
from api.vistas.solicitud_insignia.solicitud_insignia_view import SolicitarInsigniaView
from api.vistas.papeleta_sitio.papeleta_telegram_webhook_view import TelegramWebhookView
from api.vistas.solicitud_cirio.solicitud_cirio_view import SolicitarCirioView
from api.vistas.areas_de_interes.areas_de_interes_view import AreaInteresListView
from api.vistas.tipo_acto.tipo_acto_view import TipoActoListView
from api.vistas.comunicado.comunicado_view import ComunicadoDetailView
from api.vistas.tipo_puesto.tipo_puesto_view import TipoPuestoListView
from api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view import EjecutarRepartoView
from api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view import DescargarListadoInsigniasView
from api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view import DescargarListadoVacantesView
from api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view import DescargarListadoTodasInsigniasView
from api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view import EjecutarRepartoCiriosView
from api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view import DescargarListadoCiriosView
from api.vistas.papeleta_sitio.lista_asistentes_leidos_view import ListarAsistentesLeidosActoView
from api.vistas.papeleta_sitio.estadisticas_asistencia_view import EstadisticasAsistenciaView
from api.vistas.hermano.hermano_list_view import HermanoListView
from api.vistas.hermano.hermano_admin_detail_view import HermanoAdminDetailView
from api.vistas.hermano.estadisticas_hermano_view import EstadisticasHermanosView
from api.vistas.hermano.hermano_logueado_view import UsuarioLogueadoView
from api.vistas.acto.acto_detalle_view import ActoDetalleView
from api.vistas.acto.actos_proximos_view import ProximosActosView
from api.vistas.acto.proxima_estacion_penitencia_view import ProximaEstacionPenitenciaView
from api.vistas.acto.crear_acto_view import ActoCreateView
from api.vistas.acto.listado_actos_view import ActoListAPIView
from api.vistas.papeleta_sitio.ultima_papeleta_view import UltimaPapeletaView
from api.vistas.papeleta_sitio.listado_papeletas_view import MisPapeletasListView
from api.vistas.comunicado.listado_comunicados_view import MisComunicadosListView
from api.vistas.comunicado.ultimos_comunicados_areas_interes_view import UltimosComunicadosAreaInteresView
from api.vistas.comunicado.comunicados_relacionados_view import ComunicadosRelacionadosView
from api.vistas.comunicado.chat_comunicados_view import ChatComunicadosView
from api.vistas.comunicado.comunicados_general_view import ComunicadoListCreateView
from api.vistas.puesto.crear_puesto_view import CrearPuestoView
from api.vistas.puesto.puesto_detalle_view import PuestoDetalleView
from api.vistas.puesto.listado_puesto_view import PuestosPorActoListView
from api.vistas.puesto.resumen_puesto_view import ResumenPuestosActoAPIView
from api.vistas.solicitud_baja.solicitud_baja_view import SolicitudBajaAPIView
from api.vistas.solicitud_baja.listado_solicitudes_baja_admin_view import AdminListadoSolicitudesBajaAPIView
from api.vistas.cuota.cuotas_pendientes_view import MisCuotasPendientesView
from api.vistas.cuota.numero_cuotas_pendientes_view import NumeroCuotasPendientesView
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import ResolverSolicitudBajaView
from api.vistas.comunicado.comunicado_admin_list_view import ComunicadoAdminListView
from api.vistas.hermano.baja_hermano_admin_view import BajaHermanoAdminView
from api.vistas.papeleta_sitio.validar_acceso_qr_papeleta_view import ValidarAccesoQRView
from api.vistas.papeleta_sitio.descargar_papeleta_view import DescargarPapeletaPDFView


urlpatterns = [
    path("hermanos/registro/", HermanoCreateView.as_view(), name="registro-hermano"),
    path("hermanos/<int:pk>/aprobar-alta/", AprobarAltaHermanoView.as_view(), name="aprobar-alta-hermano"),
    path("papeletas/solicitar-unificada/", CrearSolicitudUnificadaView.as_view(), name="solicitar-unificada"),





    # Actos
    path("actos/<int:pk>/", ActoDetalleView.as_view(), name="detalle-acto"),
    path("actos/proximos/", ProximosActosView.as_view(), name="proximos-actos"),
    path('actos/crear/', ActoCreateView.as_view(), name='crear_acto'),
    path('actos/', ActoListAPIView.as_view(), name='acto-list'),
    path("actos/proxima-estacion/", ProximaEstacionPenitenciaView.as_view(), name="proxima-estacion"),
    path('actos/<int:acto_id>/asistentes-leidos/', ListarAsistentesLeidosActoView.as_view(), name='acto-asistentes-leidos'),
    path('actos/<int:acto_id>/estadisticas-asistencia/', EstadisticasAsistenciaView.as_view(), name='acto-estadisticas-asistencia'),
    path('actos/<int:acto_id>/puestos/', PuestosPorActoListView.as_view(), name='acto-puestos-list'),
    path('actos/<int:acto_id>/puestos/resumen/', ResumenPuestosActoAPIView.as_view(), name='resumen-puestos-acto'),

    # Áreas de interés
    path("areas-interes/", AreaInteresListView.as_view(), name="lista-areas-interes"),

    # Comunicados
    path("comunicados/chat/", ChatComunicadosView.as_view(), name="chat-comunicados"),
    path("comunicados/<int:pk>/", ComunicadoDetailView.as_view(), name="detalle-comunicado"),
    path("comunicados/", ComunicadoListCreateView.as_view(), name="lista-crear-comunicados"),
    path('comunicados/<int:exclude_id>/relacionados/', ComunicadosRelacionadosView.as_view(), name='comunicados-relacionados'),
    path("comunicados/mis-noticias/", MisComunicadosListView.as_view(), name="mis-noticias"),
    path('comunicados/ultimos-area-interes/', UltimosComunicadosAreaInteresView.as_view(), name='ultimos-comunicado-areas'),
    path('admin/comunicados/listado-total/', ComunicadoAdminListView.as_view(), name='admin-comunicados-total'),

    # Cuotas
    path('mis-cuotas/', MisCuotasListView.as_view(), name='mis_cuotas_list'),
    path('mis-cuotas-pendientes/', MisCuotasPendientesView.as_view(), name='mis-cuotas-pendientes'),
    path('mis-cuotas-pendientes/total/', NumeroCuotasPendientesView.as_view(), name='total-cuotas-pendientes'),

    # Hermanos
    path("hermanos/estadisticas/", EstadisticasHermanosView.as_view(), name="estadisticas-hermanos"),
    path("hermanos/<int:pk>/gestion/", HermanoAdminDetailView.as_view(), name="gestion-hermano-detalle"),
    path("hermanos/listado/", HermanoListView.as_view(), name="listado-hermanos"),
    path("me/", UsuarioLogueadoView.as_view(), name="usuario-logueado"),
    path('hermanos/<int:pk>/dar-de-baja/', BajaHermanoAdminView.as_view(), name='admin-dar-de-baja-hermano'),

    # Papeletas de sitio
    path("papeletas/mis-papeletas/", MisPapeletasListView.as_view(), name="mis-papeletas"),
    path("telegram/webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
    path("papeletas/ultima/", UltimaPapeletaView.as_view(), name="ultima-papeleta"),
    path("papeletas/<int:pk>/descargar/", DescargarPapeletaPDFView.as_view(), name="descargar-papeleta"),
    path("control-acceso/validar/", ValidarAccesoQRView.as_view(), name="validar-qr"),

    # Solicitud de baja
    path('solicitudes-baja/', SolicitudBajaAPIView.as_view(), name='crear-solicitud-baja'),
    path('admin/solicitudes-baja/', AdminListadoSolicitudesBajaAPIView.as_view(), name='admin-listado-bajas'),
    path('solicitudes-baja/<int:pk>/resolver/', ResolverSolicitudBajaView.as_view(), name='resolver-solicitud-baja'),

    # Solicitud de cirio
    path('actos/<int:pk>/descargar-listado-cirios/', DescargarListadoCiriosView.as_view(), name='descargar-listado-cirios'),
    path('actos/<int:acto_id>/reparto-cirios/', EjecutarRepartoCiriosView.as_view(), name='ejecutar-reparto'),
    path("papeletas/solicitar-cirio/", SolicitarCirioView.as_view(), name="solicitar-cirio"),

    # Solicitud de insignias
    path('actos/<int:pk>/descargar-listado-insignias/', DescargarListadoInsigniasView.as_view(), name='descargar-listado-insignias'),
    path('actos/<int:pk>/descargar-listado-vacantes/', DescargarListadoVacantesView.as_view(), name='descargar-listado-vacantes'),
    path('actos/<int:pk>/descargar-todas-insignias/', DescargarListadoTodasInsigniasView.as_view(), name='descargar-listado-total-insignias'),
    path('actos/<int:pk>/reparto-automatico/', EjecutarRepartoView.as_view(), name='reparto-automatico'),
    path("papeletas/solicitar-insignia/", SolicitarInsigniaView.as_view(), name="solicitar-insignia"),

    # Puesto
    path("puestos/", CrearPuestoView.as_view(), name="crear-puesto"),
    path("puestos/<int:pk>/", PuestoDetalleView.as_view(), name="detalle-puesto"),

    # Tipos de acto
    path("tipos-acto/", TipoActoListView.as_view(), name="lista-tipos-acto"),

    # Tipos de puesto
    path("tipos-puesto/", TipoPuestoListView.as_view(), name="lista-tipos-puesto"),

]