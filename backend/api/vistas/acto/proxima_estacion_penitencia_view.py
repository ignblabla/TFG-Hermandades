from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from api.serializadores.acto.acto_serializer import ActoCultoCardSerializer
from api.servicios.acto.acto_service import obtener_proxima_estacion_penitencia


class ProximaEstacionPenitenciaView(APIView):
    """
    Devuelve el próximo acto que sea 'Estación de Penitencia'
    y que aún no haya ocurrido, diseñado para la cuenta regresiva.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        proxima_estacion = obtener_proxima_estacion_penitencia()

        if proxima_estacion:
            serializer = ActoCultoCardSerializer(proxima_estacion)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            {"detail": "No hay ninguna Estación de Penitencia futura programada."}, 
            status=status.HTTP_404_NOT_FOUND
        )