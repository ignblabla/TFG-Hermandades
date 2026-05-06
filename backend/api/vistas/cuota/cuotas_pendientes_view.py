from rest_framework import generics, permissions

from api.serializadores.cuota.cuota_serializer import CuotaPendienteSerializer
from api.servicios.cuota.cuota_service import CuotaService


class MisCuotasPendientesView(generics.ListAPIView):
    """
    Vista que devuelve un listado de las cuotas impagadas o pendientes
    del hermano autenticado que realiza la petición.
    """
    serializer_class = CuotaPendienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        hermano_registrado = self.request.user
        return CuotaService.obtener_cuotas_pendientes_hermano(hermano_registrado)