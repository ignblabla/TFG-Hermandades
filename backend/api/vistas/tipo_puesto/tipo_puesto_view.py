from rest_framework import status
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializadores.tipo_puesto.tipo_puesto_serializer import TipoPuestoSerializer
from api.servicios.tipo_puesto.tipo_puesto_service import get_tipos_puesto_service


class TipoPuestoListView(APIView):
    """
    Endpoint para listar los tipos de puestos disponibles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipos = get_tipos_puesto_service()
        serializer = TipoPuestoSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)