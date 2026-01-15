from django.urls import path

from api.view.register_view import AprobarAltaHermanoView, HermanoCreateView
from api.view.solicitud_papeleta_insignia_view import SolicitarInsigniaView
from . import views
from .views import TipoActoListView, UsuarioLogueadoView, ActoListCreateView, ActoDetalleView, CrearPuestoView, TipoPuestoListView, PuestoDetalleView

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
]