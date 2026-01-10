from django.urls import path
from . import views
from .views import UsuarioLogueadoView, CrearActoView

urlpatterns = [
    # path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    # path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="delete-note"),
    path("me/", UsuarioLogueadoView.as_view(), name="usuario-logueado"),
    path("actos/", CrearActoView.as_view(), name="crear-acto"),
]