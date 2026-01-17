from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError
from api.service.ejecutar_asignacion_automatica_cirios import ejecutar_asignacion_automatica_cirios

class EjecutarRepartoCiriosView(APIView):
    """
    Endpoint administrativo para disparar el algoritmo de asignación de cirios.
    """
    permission_classes = [IsAuthenticated, IsAdminUser] # Solo admins

    def post(self, request, acto_id):
        try:
            # Llamada al servicio
            ejecutar_asignacion_automatica_cirios(acto_id)
            
            return Response({
                "mensaje": "El reparto de cirios se ha realizado correctamente.",
                "acto_id": acto_id
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Captura de errores inesperados para no tumbar el server
            return Response({"error": "Error interno del servidor durante el reparto.", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)