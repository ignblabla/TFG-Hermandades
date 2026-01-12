from django.urls import path
from . import views
from .views import UsuarioLogueadoView, ActoListCreateView, ActoDetalleView, CrearPuestoView, TipoPuestoListView, PuestoDetalleView

urlpatterns = [
    path("me/", UsuarioLogueadoView.as_view(), name="usuario-logueado"),
    path("actos/", ActoListCreateView.as_view(), name="crear-acto"),
    path("actos/<int:pk>/", ActoDetalleView.as_view(), name="detalle-acto"),
    path("puestos/", CrearPuestoView.as_view(), name="crear-puesto"),
    path("puestos/<int:pk>/", PuestoDetalleView.as_view(), name="detalle-puesto"),
    path("tipos-puesto/", TipoPuestoListView.as_view(), name="lista-tipos-puesto"),

]