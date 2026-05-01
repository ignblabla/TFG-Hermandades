from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status

from api.serializadores.hermano.hermano_serializer import EstadisticasHermanosSerializer
from api.servicios.hermano.hermano_service import get_estadisticas_hermanos_service

from django.contrib.auth import get_user_model

User = get_user_model()


class EstadisticasHermanosView(APIView):
    """
    Endpoint para obtener estadísticas generales de la nómina de hermanos.
    Exclusivo para administradores.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, 'esAdmin', False):
            return Response(
                {"detail": "No tienes permisos para ver las estadísticas de la Hermandad."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            datos_estadisticas = get_estadisticas_hermanos_service()

            serializer = EstadisticasHermanosSerializer(datos_estadisticas)

            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": "Error al calcular las estadísticas.", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )