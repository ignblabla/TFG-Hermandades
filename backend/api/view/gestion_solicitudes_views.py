from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError

from api.servicios.solicitud_cirio.solicitud_cirio_service import SolicitudCirioTradicionalService

from ..servicios.papeleta_sitio_service import PapeletaSitioService
from ..serializers import (SolicitudCirioSerializer, SolicitudUnificadaSerializer)

# -----------------------------------------------------------------------------
# VISTA 3: SOLICITUD UNIFICADA (MODALIDAD UNIFICADA)
# -----------------------------------------------------------------------------
class CrearSolicitudUnificadaView(APIView):
    """
    Endpoint para solicitar Insignias y/o Cirios en una sola petición 
    cuando el acto es UNIFICADO.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SolicitudUnificadaSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                service = PapeletaSitioService()
                
                datos_para_servicio = {
                    'puesto_general_id': serializer.validated_data.get('puesto_general_id'),
                    'preferencias': serializer.validated_data.get('preferencias_solicitadas', [])
                }
                
                papeleta = service.procesar_solicitud_unificada(
                    hermano=request.user,
                    acto=serializer.validated_data['acto'],
                    datos_solicitud=datos_para_servicio
                )

                return Response(
                    SolicitudUnificadaSerializer(papeleta).data, 
                    status=status.HTTP_201_CREATED
                )

            except DjangoValidationError as e:
                return Response({"detail": e.message if hasattr(e, 'message') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                print(f"Error interno: {e}")
                return Response({"detail": "Error procesando la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)