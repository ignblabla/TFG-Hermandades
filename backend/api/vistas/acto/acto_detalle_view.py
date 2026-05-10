from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch

from api.models import Acto, PapeletaSitio, PreferenciaSolicitud
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

        queryset_optimizado = Acto.objects.select_related(
            'tipo_acto'
        ).prefetch_related(
            'tramos',
            'puestos_disponibles__tipo_puesto'
        )

        acto = get_object_or_404(queryset_optimizado, pk=pk)

        estados_inactivos = ['ANULADA']
        
        acto.db_total_solicitantes_insignia = acto.papeletas.filter(
            es_solicitud_insignia=True
        ).exclude(estado_papeleta__in=estados_inactivos).count()

        acto.db_total_solicitudes_insignias = PreferenciaSolicitud.objects.filter(
            papeleta__acto=acto,
            papeleta__estado_papeleta__in=['SOLICITADA', 'EMITIDA', 'RECOGIDA', 'LEIDA', 'NO_ASIGNADA'],
            papeleta__es_solicitud_insignia=True
        ).count()

        acto.db_total_insignias = sum(
            p.numero_maximo_asignaciones for p in acto.puestos_disponibles.all() if p.tipo_puesto.es_insignia
        )

        acto.db_total_puestos_cirios = sum(
            1 for p in acto.puestos_disponibles.all() if not p.tipo_puesto.es_insignia
        )

        if acto.fecha_ejecucion_reparto:
            acto.db_total_asignados = acto.papeletas.filter(
                es_solicitud_insignia=True, 
                puesto__isnull=False
            ).exclude(estado_papeleta__in=['ANULADA', 'NO_ASIGNADA']).count()
            
            acto.db_total_no_asignados = max(0, acto.db_total_insignias - acto.db_total_asignados)
        else:
            acto.db_total_asignados = None
            acto.db_total_no_asignados = None

        acto.db_total_solicitantes_cirio = acto.papeletas.filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True)
        ).exclude(estado_papeleta__in=estados_inactivos).count()

        acto.db_total_cirios_cristo = acto.papeletas.filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True),
            puesto__isnull=False,
            puesto__cortejo_cristo=True,
            puesto__tipo_puesto__es_insignia=False
        ).exclude(estado_papeleta__in=estados_inactivos).count()

        acto.db_total_cirios_virgen = acto.papeletas.filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True),
            puesto__isnull=False,
            puesto__cortejo_cristo=False,
            puesto__tipo_puesto__es_insignia=False
        ).exclude(estado_papeleta__in=estados_inactivos).count()

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