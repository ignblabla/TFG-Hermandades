from rest_framework import generics

from api.serializadores.acto.acto_serializer import ActoListSerializer
from api.pagination import PaginacionDoceElementos
from api.servicios.acto.acto_service import ActoService


class ActoListAPIView(generics.ListAPIView):
    """
    Vista para listar todos los Actos.
    Utiliza PaginacionDiezElementos para devolver 12 resultados por página.
    """
    serializer_class = ActoListSerializer
    pagination_class = PaginacionDoceElementos

    def get_queryset(self):
        return ActoService.get_todos_los_actos()