from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from api.service.solicitar_papeleta_cirio_service import solicitar_papeleta_cirio

from ..serializers import SolicitudCirioSerializer

class SolicitarCirioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # El serializer ahora debe incluir 'numero_registro_vinculado' (opcional)
        serializer = SolicitudCirioSerializer(data=request.data)
        
        if serializer.is_valid():
            acto = serializer.validated_data['acto']
            puesto = serializer.validated_data['puesto']
            hermano = request.user
            
            # Extraemos el número de registro vinculado si existe en el payload
            numero_vinculado = serializer.validated_data.get('numero_registro_vinculado')

            try:
                # Llamamos al servicio unificado con el nuevo parámetro
                papeleta = solicitar_papeleta_cirio(
                    hermano=hermano, 
                    acto=acto, 
                    puesto=puesto,
                    numero_registro_vinculado=numero_vinculado
                )
                
                # Construimos el mensaje de éxito dinámicamente
                mensaje_exito = f"Solicitud para {puesto.nombre} realizada correctamente."
                if numero_vinculado:
                    mensaje_exito += f" Vinculada al hermano Nº {numero_vinculado}."

                return Response({
                    "status": "success",
                    "mensaje": mensaje_exito,
                    "id": papeleta.id,
                    "fecha": papeleta.fecha_solicitud
                }, status=status.HTTP_201_CREATED)
            
            except ValidationError as e:
                # Captura errores de negocio (fechas, antigüedad, cortejos diferentes, etc.)
                return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # Log del error para depuración interna
                print(f"Error inesperado en SolicitarCirioView: {str(e)}")
                return Response({"detail": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)      