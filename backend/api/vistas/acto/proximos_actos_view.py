from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from api.models import Acto
from api.serializadores.acto.acto_serializer import ActoCultoCardSerializer

class ProximosActosView(APIView):
    """
    Devuelve los 3 actos más próximos a partir de la fecha y hora actual,
    optimizados para las tarjetas del Dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ahora = timezone.now()

        proximos_actos = Acto.objects.filter(
            fecha__gte=ahora
        ).only(
            'id', 'nombre', 'fecha', 'lugar'
        ).order_by('fecha')[:3]

        serializer = ActoCultoCardSerializer(proximos_actos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)