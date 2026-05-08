from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from api.models import Acto, PapeletaSitio
from api.servicios.acto.acto_service import delete_acto_service, update_acto_service
from api.serializadores.acto.acto_serializer import ActoSerializer
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador


class ActoDetalleView(APIView):

    def get_permissions(self):
        """
        Instancia y devuelve la lista de permisos requeridos dependiendo del método HTTP.
        """
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [EsAdministrador()]



    def get(self, request, pk):
        """
        Recuperar un acto específico por su ID optimizando las consultas SQL.
        """
        queryset_optimizado = Acto.objects.select_related(
            'tipo_acto'
        ).prefetch_related(
            'tramos',
            'puestos_disponibles__tipo_puesto',
            Prefetch(
                'papeletas',
                queryset=PapeletaSitio.objects.select_related('puesto__tipo_puesto')
            )
        )

        acto = get_object_or_404(queryset_optimizado, pk=pk)
        serializer = ActoSerializer(acto, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)



    def put(self, request, pk):
        """
        Actualización completa de un acto.
        """
        acto = get_object_or_404(Acto, pk=pk)
        serializer = ActoSerializer(acto, data=request.data)
        serializer.is_valid(raise_exception=True)

        acto_actualizado = update_acto_service(usuario=request.user, acto_id=pk, data_validada=serializer.validated_data)

        response_serializer = ActoSerializer(acto_actualizado)
        return Response(response_serializer.data, status=status.HTTP_200_OK)



    def patch(self, request, pk):
        """
        Actualización parcial de un acto (solo algunos campos).
        """
        acto = get_object_or_404(Acto, pk=pk)

        serializer = ActoSerializer(acto, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        acto_actualizado = update_acto_service(
            usuario=request.user,
            acto_id=pk,
            data_validada=serializer.validated_data
        )

        response_serializer = ActoSerializer(acto_actualizado)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    


    def delete(self, request, pk):
        """
        Eliminar un acto.
        """
        delete_acto_service(usuario=request.user, acto_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)