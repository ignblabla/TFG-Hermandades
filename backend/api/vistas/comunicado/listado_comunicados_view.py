from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from api.models import AreaInteres, Comunicado
from api.serializadores.comunicado.comunicado_serializer import ComunicadoListSerializer

from django.db.models import Q


class MisComunicadosListView(generics.ListAPIView):
    """
    Devuelve los comunicados filtrados por las áreas de interés del usuario logueado,
    INCLUYENDO siempre los comunicados dirigidos a 'Todos los Hermanos'.
    """
    serializer_class = ComunicadoListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        mis_areas = usuario.areas_interes.all()

        queryset = Comunicado.objects.filter(
            Q(areas_interes__in=mis_areas) | 
            Q(areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS)
        ).distinct().order_by('-fecha_emision')

        return queryset