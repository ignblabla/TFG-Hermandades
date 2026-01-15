from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError

from ..service.solicitud_papeleta_insignia_service import SolicitudPapeletaService
from ..serializers import SolicitudInsigniaSerializer

class SolicitarInsigniaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = SolicitudPapeletaService()

        try:
            papeleta = service.crear_solicitud_insignia(request.user, request.data)

            response_serializer = SolicitudInsigniaSerializer(papeleta)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except DjangoValidationError as e:
            return Response({"error": e.message if hasattr(e, 'message') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)