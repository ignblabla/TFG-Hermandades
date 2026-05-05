from django.contrib.auth import get_user_model
from rest_framework import status

from api.serializadores.puesto.puesto_serializer import PuestoSerializer, PuestoUpdateSerializer
from api.models import Puesto

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from api.servicios.puesto.puesto_service import delete_puesto_service, update_puesto_service

User = get_user_model()


class PuestoDetalleView(APIView):
    """
    Endpoint para ver, editar o eliminar un puesto específico.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        puesto = get_object_or_404(Puesto, pk=pk)
        serializer = PuestoSerializer(puesto)
        return Response(serializer.data, status = status.HTTP_200_OK)


    def put(self, request, pk):
        """Actualización completa"""
        puesto = get_object_or_404(Puesto, pk=pk)
        serializer = PuestoUpdateSerializer(puesto, data=request.data)
        serializer.is_valid(raise_exception=True)

        puesto_actualizado = update_puesto_service(
            usuario = request.user,
            puesto_id = pk,
            data_validada=serializer.validated_data
        )

        return Response(PuestoSerializer(puesto_actualizado).data, status=status.HTTP_200_OK)


    def patch(self, request, pk):
        """Actualización parcial"""
        puesto = get_object_or_404(Puesto, pk=pk)
        serializer = PuestoUpdateSerializer(puesto, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        puesto_actualizado = update_puesto_service(
            usuario=request.user, 
            puesto_id=pk, 
            data_validada=serializer.validated_data
        )

        return Response(PuestoSerializer(puesto_actualizado).data, status=status.HTTP_200_OK)



    def delete(self, request, pk):
        """Eliminación de un puesto"""

        delete_puesto_service(
            usuario=request.user,
            puesto_id=pk
        )

        return Response(status=status.HTTP_204_NO_CONTENT)