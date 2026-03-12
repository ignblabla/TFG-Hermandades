# views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.serializers import CuotaSerializer
from api.pagination import PaginacionDiezElementos
from api.models import Cuota

class MisCuotasListView(generics.ListAPIView):
    """
    Lista las cuotas exclusivas del hermano autenticado.
    Paginadas de 10 en 10 y ordenadas de más recientes a más antiguas.
    """
    serializer_class = CuotaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PaginacionDiezElementos

    def get_queryset(self):
        return Cuota.objects.filter(
            hermano=self.request.user
        ).order_by('-anio', '-fecha_emision')