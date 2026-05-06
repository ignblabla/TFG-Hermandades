from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from api.models import SolicitudBaja
from api.serializadores.solicitud_baja.solicitud_baja_serializer import SolicitudBajaSerializer
from api.servicios.solicitud_baja.obtener_solicitudes_baja_admin_service import resolver_solicitud



class EsAdministrador(permissions.BasePermission):
    """
    Permite el acceso únicamente a los hermanos que tienen la propiedad esAdmin = True.
    """
    message = "No tienes permisos de administrador para realizar esta acción."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'esAdmin', False))



class ResolverSolicitudBajaView(APIView):
    """
    Permite a un administrador Aceptar o Denegar una solicitud de baja.
    Se espera recibir en el body: {"accion": "ACEPTAR"} o {"accion": "DENEGAR"}
    """
    permission_classes = [EsAdministrador]

    def post(self, request, pk, *args, **kwargs):
        solicitud = get_object_or_404(SolicitudBaja, pk=pk)
        accion = request.data.get('accion')

        if not accion:
            return Response(
                {"error": "Debe proporcionar el campo 'accion' en el cuerpo de la petición."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            solicitud_resuelta = resolver_solicitud(solicitud, accion.upper(), request.user)
            
            serializer = SolicitudBajaSerializer(solicitud_resuelta)
            
            mensaje = "Solicitud aprobada y hermano dado de baja correctamente." if accion.upper() == 'ACEPTAR' else "Solicitud denegada correctamente."
            
            return Response({
                "mensaje": mensaje,
                "solicitud": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)