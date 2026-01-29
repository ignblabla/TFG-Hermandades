from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError

from api.servicios.solicitud_insignia_service import SolicitudInsigniaService

from ..servicios.papeleta_sitio_service import PapeletaSitioService
from ..serializers import (
    SolicitudInsigniaSerializer, 
    SolicitudCirioSerializer, 
    SolicitudUnificadaSerializer,
)

# -----------------------------------------------------------------------------
# VISTA 1: SOLICITUD DE INSIGNIA (MODALIDAD TRADICIONAL - FASE 1)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# VISTA 2: SOLICITUD DE CIRIO (MODALIDAD TRADICIONAL - FASE 2)
# -----------------------------------------------------------------------------
class SolicitarCirioView(APIView):
    """
    Endpoint para solicitar puesto directo (Cirio/Diputado) cuando el acto es TRADICIONAL.
    Permite vinculación de hermanos.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SolicitudCirioSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                service = PapeletaSitioService()
                
                acto = serializer.validated_data['acto']
                puesto = serializer.validated_data['puesto']
                numero_vinculado = serializer.validated_data.get('numero_registro_vinculado')

                papeleta = service.procesar_solicitud_cirio_tradicional(
                    hermano=request.user, 
                    acto=acto, 
                    puesto=puesto,
                    numero_registro_vinculado=numero_vinculado
                )
                
                mensaje_exito = f"Solicitud para {puesto.nombre} realizada correctamente."
                if numero_vinculado:
                    mensaje_exito += f" Vinculada al hermano Nº {numero_vinculado}."

                return Response({
                    "status": "success",
                    "mensaje": mensaje_exito,
                    "id": papeleta.id,
                    "numero_papeleta": papeleta.numero_papeleta,
                    "fecha": papeleta.fecha_solicitud
                }, status=status.HTTP_201_CREATED)
            
            except DjangoValidationError as e:
                mensaje = e.message if hasattr(e, 'message') else str(e)
                return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Error en SolicitarCirioView: {e}")
                return Response({"detail": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

                acto = serializer.validated_data['acto']
                preferencias = serializer.validated_data.get('preferencias_solicitadas', [])
                
                papeleta = service.procesar_solicitud_unificada(
                    hermano=request.user,
                    acto=acto,
                    preferencias_data=preferencias
                )

                return Response(
                    SolicitudUnificadaSerializer(papeleta).data, 
                    status=status.HTTP_201_CREATED
                )

            except DjangoValidationError as e:
                mensaje_error = e.message if hasattr(e, 'message') else str(e)
                return Response({"detail": mensaje_error}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                print(f"Error en Unificada: {e}")
                return Response({"detail": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)