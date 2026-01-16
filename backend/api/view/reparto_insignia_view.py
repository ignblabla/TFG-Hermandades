from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.core.exceptions import ValidationError
from api.service.reparto_service import RepartoService

class EjecutarRepartoView(APIView):
    """
    Endpoint para ejecutar el algoritmo de asignación de puestos.
    Solo accesible para Administradores.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            resultado = RepartoService.ejecutar_asignacion_automatica(acto_id=pk)
            return Response(resultado, status=status.HTTP_200_OK)
        
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Errores inesperados
            return Response({"error": "Error interno del servidor", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)