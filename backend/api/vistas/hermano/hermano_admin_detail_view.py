from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from api.serializadores.hermano.hermano_serializer import HermanoAdminUpdateSerializer
from api.servicios.hermano.hermano_service import update_hermano_por_admin_service
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()


class HermanoAdminDetailView(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request, pk):
        hermano = get_object_or_404(User, pk=pk)
        serializer = HermanoAdminUpdateSerializer(hermano)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def put(self, request, pk):
        """
        Actualización completa (requiere enviar todos los campos obligatorios).
        """
        hermano = get_object_or_404(User, pk=pk)

        serializer = HermanoAdminUpdateSerializer(hermano, data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            hermano_actualizado = update_hermano_por_admin_service(
                usuario_solicitante=request.user,
                hermano_id=pk,
                data_validada=serializer.validated_data
            )
            return Response(HermanoAdminUpdateSerializer(hermano_actualizado).data, status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        

    def patch(self, request, pk):
        """
        Actualización parcial (solo los campos enviados).
        """
        hermano = get_object_or_404(User, pk=pk)

        serializer = HermanoAdminUpdateSerializer(hermano, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            hermano_actualizado = update_hermano_por_admin_service(
                usuario_solicitante=request.user,
                hermano_id=pk,
                data_validada=serializer.validated_data
            )
            return Response(HermanoAdminUpdateSerializer(hermano_actualizado).data, status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)