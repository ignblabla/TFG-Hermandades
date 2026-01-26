from django.urls import path

from api.view.register_view import AprobarAltaHermanoView, HermanoCreateView
from api.view.solicitud_papeleta_insignia_view import SolicitarInsigniaView
from api.view.reparto_insignia_view import EjecutarRepartoView
from api.view.solicitar_cirio_view import SolicitarCirioView
from api.view.ejecutar_reparto_cirios_view import EjecutarRepartoCiriosView
# from api.view.ConsultaPapeletasView import MisPapeletasListView
from api.view.GenerarQRPapeletaView import DescargarPapeletaPDFView, ValidarAccesoQRView
from . import views

from .views import ActoUpdateView, CrearActoView, CrearSolicitudUnificadaView, HermanoAdminDetailView, HermanoListView, MisPapeletasListView, TipoActoListView, UsuarioLogueadoView, ActoListCreateView, ActoDetalleView, CrearPuestoView, TipoPuestoListView, PuestoDetalleView

urlpatterns = [
    path("me/", UsuarioLogueadoView.as_view(), name="usuario-logueado"),
    path("hermanos/registro/", HermanoCreateView.as_view(), name="registro-hermano"),
    path("hermanos/<int:pk>/aprobar-alta/", AprobarAltaHermanoView.as_view(), name="aprobar-alta-hermano"),
    path("actos/", ActoListCreateView.as_view(), name="crear-acto"),
    path("actos/<int:pk>/", ActoDetalleView.as_view(), name="detalle-acto"),
    path("puestos/", CrearPuestoView.as_view(), name="crear-puesto"),
    path("puestos/<int:pk>/", PuestoDetalleView.as_view(), name="detalle-puesto"),
    path("tipos-puesto/", TipoPuestoListView.as_view(), name="lista-tipos-puesto"),
    path("tipos-acto/", TipoActoListView.as_view(), name="lista-tipos-acto"),

    path("papeletas/solicitar-insignia/", SolicitarInsigniaView.as_view(), name="solicitar-insignia"),
    path("papeletas/solicitar-cirio/", SolicitarCirioView.as_view(), name="solicitar-cirio"),

    path('actos/<int:pk>/reparto-automatico/', EjecutarRepartoView.as_view(), name='reparto-automatico'),
    path('actos/<int:acto_id>/reparto-cirios/', EjecutarRepartoCiriosView.as_view(), name='ejecutar-reparto'),

    # path("papeletas/mis-papeletas/", MisPapeletasListView.as_view(), name="mis-papeletas"),
    path("papeletas/<int:pk>/descargar/", DescargarPapeletaPDFView.as_view(), name="descargar-papeleta"),

    path("control-acceso/validar/", ValidarAccesoQRView.as_view(), name="validar-qr"),

    #Urls para el panel de administrador
    path("hermanos/listado/", HermanoListView.as_view(), name="listado-hermanos"),
    path("hermanos/<int:pk>/gestion/", HermanoAdminDetailView.as_view(), name="gestion-hermano-detalle"),

    path("papeletas/mis-papeletas/", MisPapeletasListView.as_view(), name="mis-papeletas"),

    #UrlS para actos
    path('actos/crear/', CrearActoView.as_view(), name='crear_acto'),
    path('actos/<int:pk>/editar/', ActoUpdateView.as_view(), name='acto-update'),

    path("papeletas/solicitar-unificada/", CrearSolicitudUnificadaView.as_view(), name="solicitar-unificada"),
]