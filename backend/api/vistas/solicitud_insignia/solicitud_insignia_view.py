from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from api.serializadores.solicitud_insignia.solicitud_insignia_serializer import SolicitudInsigniaSerializer
from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService
from api.models import Acto



class SolicitarInsigniaView(APIView):
    """
    Endpoint para solicitar insignias cuando el acto es TRADICIONAL.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SolicitudInsigniaSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                service = SolicitudInsigniaService()

                papeleta = service.procesar_solicitud_insignia_tradicional(
                    hermano=request.user,
                    acto=serializer.validated_data['acto'],
                    preferencias_data=serializer.validated_data['preferencias']
                )

                return Response(
                    SolicitudInsigniaSerializer(papeleta).data, 
                    status=status.HTTP_201_CREATED
                )

            except DjangoValidationError as e:
                mensaje = e.message if hasattr(e, 'message') else str(e)
                return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                return Response({"detail": "Error interno al procesar la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)