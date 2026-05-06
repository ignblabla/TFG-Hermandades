from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from api.servicios.cuota.cuota_service import CuotaService


class NumeroCuotasPendientesView(APIView):
    """
    Vista que devuelve el número total de cuotas pendientes o devueltas
    del hermano autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        hermano_registrado = request.user
        total = CuotaService.contar_cuotas_pendientes_hermano(hermano_registrado)
        
        return Response({
            "total_pendientes": total
        })