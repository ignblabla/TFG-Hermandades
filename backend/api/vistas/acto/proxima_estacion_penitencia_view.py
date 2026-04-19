from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from api.models import Acto, TipoActo
from api.serializadores.acto.acto_serializer import ActoCultoCardSerializer

class ProximaEstacionPenitenciaView(APIView):
    """
    Devuelve el próximo acto que sea 'Estación de Penitencia'
    y que aún no haya ocurrido, diseñado para la cuenta regresiva.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ahora = timezone.now()

        proxima_estacion = Acto.objects.filter(
            tipo_acto__tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            fecha__gte=ahora
        ).select_related('tipo_acto').order_by('fecha').first()

        if proxima_estacion:
            serializer = ActoCultoCardSerializer(proxima_estacion)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "No hay ninguna Estación de Penitencia futura programada."}, 
                status=status.HTTP_404_NOT_FOUND
            )