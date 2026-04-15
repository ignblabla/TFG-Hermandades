from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.models import AreaInteres
from api.serializadores.areas_de_interes.areas_de_interes_serializer import AreaInteresSerializer


class AreaInteresListView(generics.ListAPIView):
    """
    Devuelve la lista de áreas disponibles para poblar los selectores en React.
    """
    queryset = AreaInteres.objects.all()
    serializer_class = AreaInteresSerializer
    permission_classes = [IsAuthenticated]