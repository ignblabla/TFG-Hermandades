from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied

from api.serializadores.solicitud_baja.solicitud_baja_serializer import ListadoSolicitudesBajaSerializer
from api.servicios.solicitud_baja.obtener_solicitudes_baja_admin_service import obtener_solicitudes_baja_admin


class AdminListadoSolicitudesBajaAPIView(APIView):
    # Requerimos token de autenticación a nivel de vista
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Llamamos al servicio con el usuario que hace la petición
            solicitudes = obtener_solicitudes_baja_admin(usuario=request.user)
            
            # Serializamos la lista de resultados (many=True)
            serializer = ListadoSolicitudesBajaSerializer(solicitudes, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            # Capturamos el error de permisos y devolvemos un 403 Forbidden
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        except Exception as e:
            # Para depurar cualquier otro error inesperado en la terminal
            import traceback
            print("\n❌ ERROR EN LISTADO DE SOLICITUDES (ADMIN):")
            traceback.print_exc()
            return Response(
                {"error": "Ocurrió un error inesperado al procesar la solicitud."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )