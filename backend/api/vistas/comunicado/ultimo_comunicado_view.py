from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.serializadores.comunicado.ultimo_comunicado_serializer import ComunicadoSerializer
from api.servicios.comunicado.ultimo_comunicado_service import obtener_ultimo_comunicado_areas_usuario

class UltimoComunicadoAreaInteresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        comunicado = obtener_ultimo_comunicado_areas_usuario(request.user)
        
        if comunicado:
            serializer = ComunicadoSerializer(comunicado, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        return Response(
            {'detail': 'No hay comunicados recientes en sus áreas de interés.'}, 
            status=status.HTTP_404_NOT_FOUND
        )