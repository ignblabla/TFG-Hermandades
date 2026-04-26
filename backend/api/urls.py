from django.urls import path

from api.view.register_view import AprobarAltaHermanoView, HermanoCreateView
from api.view.GenerarQRPapeletaView import DescargarPapeletaPDFView, ValidarAccesoQRView
from api.view.gestion_solicitudes_views import CrearSolicitudUnificadaView, SolicitarCirioView
from api.vistas.cuota.cuota_view import MisCuotasListView
from api.vistas.solicitud_insignia.solicitud_insignia_view import DescargarListadoInsigniasView, DescargarListadoTodasInsigniasView, DescargarListadoVacantesView, EjecutarRepartoView, SolicitarInsigniaView
from api.vistas.papeleta_sitio.papeleta_sitio_view import MisPapeletasListView, TablaInsigniasActoView, TelegramWebhookView, UltimaPapeletaView
from api.vistas.solicitud_cirio.solicitud_cirio_view import DescargarListadoCiriosView, EjecutarRepartoCiriosView
from api.vistas.areas_de_interes.areas_de_interes_view import AreaInteresListView
from api.vistas.acto.acto_view import ActoCreateView, ActoDetalleView, ActoListAPIView, ProximaEstacionPenitenciaView, ProximosActosView
from api.vistas.tipo_acto.tipo_acto_view import TipoActoListView
from api.vistas.hermano.hermano_view import HermanoAdminDetailView, HermanoListView, UsuarioLogueadoView
from api.vistas.comunicado.comunicado_view import ChatComunicadosView, ComunicadoDetailView, ComunicadoListCreateView, ComunicadosRelacionadosView, MisComunicadosListView, UltimosComunicadosAreaInteresView
from api.vistas.tipo_puesto.tipo_puesto_view import TipoPuestoListView

from .views import CrearPuestoView, PuestoDetalleView

urlpatterns = [
    path("me/", UsuarioLogueadoView.as_view(), name="usuario-logueado"),
    path("hermanos/registro/", HermanoCreateView.as_view(), name="registro-hermano"),
    path("hermanos/<int:pk>/aprobar-alta/", AprobarAltaHermanoView.as_view(), name="aprobar-alta-hermano"),

    path("actos/proximos/", ProximosActosView.as_view(), name="proximos-actos"),
    path("actos/proxima-estacion/", ProximaEstacionPenitenciaView.as_view(), name="proxima-estacion"),

    path("actos/<int:pk>/", ActoDetalleView.as_view(), name="detalle-acto"),
    path("puestos/", CrearPuestoView.as_view(), name="crear-puesto"),
    path("puestos/<int:pk>/", PuestoDetalleView.as_view(), name="detalle-puesto"),
    path("tipos-puesto/", TipoPuestoListView.as_view(), name="lista-tipos-puesto"),
    path("tipos-acto/", TipoActoListView.as_view(), name="lista-tipos-acto"),

    path('actos/<int:pk>/reparto-automatico/', EjecutarRepartoView.as_view(), name='reparto-automatico'),

    path("papeletas/<int:pk>/descargar/", DescargarPapeletaPDFView.as_view(), name="descargar-papeleta"),

    path("control-acceso/validar/", ValidarAccesoQRView.as_view(), name="validar-qr"),

    #Urls para el panel de administrador
    path("hermanos/listado/", HermanoListView.as_view(), name="listado-hermanos"),
    path("hermanos/<int:pk>/gestion/", HermanoAdminDetailView.as_view(), name="gestion-hermano-detalle"),

    #UrlS para actos
    path('actos/crear/', ActoCreateView.as_view(), name='crear_acto'),
    # path('actos/<int:pk>/editar/', ActoUpdateView.as_view(), name='acto-update'),

    path("papeletas/solicitar-insignia/", SolicitarInsigniaView.as_view(), name="solicitar-insignia"),
    path("papeletas/solicitar-cirio/", SolicitarCirioView.as_view(), name="solicitar-cirio"),
    path("papeletas/solicitar-unificada/", CrearSolicitudUnificadaView.as_view(), name="solicitar-unificada"),

    path("comunicados/", ComunicadoListCreateView.as_view(), name="lista-crear-comunicados"),
    path("comunicados/<int:pk>/", ComunicadoDetailView.as_view(), name="detalle-comunicado"),
    path("comunicados/mis-noticias/", MisComunicadosListView.as_view(), name="mis-noticias"),
    path('comunicados/<int:exclude_id>/relacionados/', ComunicadosRelacionadosView.as_view(), name='comunicados-relacionados'),
    path('comunicados/ultimos-area-interes/', UltimosComunicadosAreaInteresView.as_view(), name='ultimos-comunicado-areas'),

    path("telegram/webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),

    path("comunicados/chat/", ChatComunicadosView.as_view(), name="chat-comunicados"),

    #Cuotas
    path('mis-cuotas/', MisCuotasListView.as_view(), name='mis_cuotas_list'),


    #Actos
    path('actos/', ActoListAPIView.as_view(), name='acto-list'),











    #Papeletas de sitio
    path('actos/<int:acto_id>/solicitudes-insignias/', TablaInsigniasActoView.as_view(), name='acto-solicitudes-insignias'),

    #Asignación de insignias
    path('actos/<int:pk>/descargar-listado-insignias/', DescargarListadoInsigniasView.as_view(), name='descargar-listado-insignias'),
    path('actos/<int:pk>/descargar-listado-vacantes/', DescargarListadoVacantesView.as_view(), name='descargar-listado-vacantes'),
    path('actos/<int:pk>/descargar-todas-insignias/', DescargarListadoTodasInsigniasView.as_view(), name='descargar-listado-total-insignias'),

    #Asignación de cirios
    path('actos/<int:acto_id>/reparto-cirios/', EjecutarRepartoCiriosView.as_view(), name='ejecutar-reparto'),
    path('actos/<int:pk>/descargar-listado-cirios/', DescargarListadoCiriosView.as_view(), name='descargar-listado-cirios'),

    #Papeletas de sitio
    path("papeletas/mis-papeletas/", MisPapeletasListView.as_view(), name="mis-papeletas"),
    path("papeletas/ultima/", UltimaPapeletaView.as_view(), name="ultima-papeleta"),

    #Áreas de interés
    path("areas-interes/", AreaInteresListView.as_view(), name="lista-areas-interes"),
]