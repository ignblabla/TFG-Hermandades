from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied

from api.serializadores.solicitud_baja.solicitud_baja_serializer import ListadoSolicitudesBajaSerializer
from api.servicios.solicitud_baja.solicitud_baja_service import obtener_solicitudes_baja_admin
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador


class AdminListadoSolicitudesBajaAPIView(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request, *args, **kwargs):
        try:
            solicitudes = obtener_solicitudes_baja_admin(usuario=request.user)

            serializer = ListadoSolicitudesBajaSerializer(solicitudes, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        except Exception as e:
            return Response(
                {"error": "Ocurrió un error inesperado al procesar la solicitud."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )