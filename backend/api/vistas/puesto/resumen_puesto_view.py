from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from api.servicios.puesto.puesto_service import obtener_resumen_puestos_acto


class ResumenPuestosActoAPIView(APIView):
    """
    API View para obtener la métrica total de puestos de un acto,
    desglosada por pasos (Cristo/Virgen).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, acto_id, *args, **kwargs):
        resumen = obtener_resumen_puestos_acto(acto_id=acto_id)
        return Response(resumen, status=status.HTTP_200_OK)