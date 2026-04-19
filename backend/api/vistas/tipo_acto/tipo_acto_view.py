from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from api.servicios.tipo_acto.tipo_acto_service import get_tipos_acto_service
from api.serializadores.tipo_acto.tipo_acto_serializer import TipoActoSerializer

from rest_framework.response import Response


class TipoActoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipos = get_tipos_acto_service()
        serializer = TipoActoSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)