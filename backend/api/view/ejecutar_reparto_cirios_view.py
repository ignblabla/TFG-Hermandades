from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from api.service.ejecutar_asignacion_automatica_cirios import ejecutar_asignacion_automatica_cirios

class EjecutarRepartoCiriosView(APIView):
    """
    Endpoint administrativo para disparar el algoritmo de asignación de cirios.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, acto_id):
        try:
            # Capturamos el número de papeletas asignadas
            cantidad_asignadas = ejecutar_asignacion_automatica_cirios(acto_id)
            
            return Response({
                "mensaje": f"El reparto se ha ejecutado con éxito. Se han asignado {cantidad_asignadas} papeletas de sitio en los tramos.",
                "acto_id": acto_id,
                "asignadas": cantidad_asignadas
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            # Esto ahora te lanzará el error detallado de la telemetría si las papeletas no tienen puesto
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error interno del servidor durante el reparto.", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)