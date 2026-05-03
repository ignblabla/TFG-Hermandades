from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializadores.comunicado.comunicado_serializer import ComunicadoSerializer
from api.servicios.comunicado.comunicado_service import ComunicadoService


class ComunicadosRelacionadosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exclude_id):
        comunicados = ComunicadoService.obtener_comunicados_relacionados_usuario(request.user, exclude_id)

        serializer = ComunicadoSerializer(comunicados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)