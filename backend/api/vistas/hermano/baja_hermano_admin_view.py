from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

# Asegúrate de importar el permiso correcto que usas en tu proyecto
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador
from api.servicios.hermano.hermano_service import dar_de_baja_hermano_service

User = get_user_model()

class BajaHermanoAdminView(APIView):
    """
    Endpoint para que un administrador dé de baja a un hermano de forma directa.
    """
    permission_classes = [EsAdministrador]

    def post(self, request, pk):
        try:
            hermano_dado_de_baja = dar_de_baja_hermano_service(
                usuario_solicitante=request.user,
                hermano_id=pk
            )
            
            return Response(
                {
                    "detail": f"El hermano {hermano_dado_de_baja.nombre} {hermano_dado_de_baja.primer_apellido} ha sido dado de baja correctamente.",
                    "estado_hermano": hermano_dado_de_baja.estado_hermano,
                    "fecha_baja_corporacion": hermano_dado_de_baja.fecha_baja_corporacion,
                    "is_active": hermano_dado_de_baja.is_active
                }, 
                status=status.HTTP_200_OK
            )
            
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)