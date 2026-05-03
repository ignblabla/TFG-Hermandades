from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializadores.comunicado.comunicado_serializer import ComunicadoSerializer
from api.servicios.comunicado.comunicado_service import ComunicadoService


class UltimosComunicadosAreaInteresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        comunicados = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(request.user)
        
        if comunicados.exists():
            serializer = ComunicadoSerializer(comunicados, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        return Response(
            {'detail': 'No hay comunicados recientes en sus áreas de interés.'}, 
            status=status.HTTP_404_NOT_FOUND
        )