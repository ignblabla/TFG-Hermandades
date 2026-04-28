from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError

from api.serializers import SolicitudCirioSerializer
from api.servicios.solicitud_cirio.solicitud_cirio_service import SolicitudCirioTradicionalService


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
                service = SolicitudCirioTradicionalService()
                
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