from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.servicios.puesto.puesto_service import obtener_puestos_por_acto
from api.serializadores.puesto.puesto_serializer import PuestoListadoSerializer
from api.pagination import StandardResultsSetPagination


class PuestosPorActoListView(APIView):
    """
    API View para listar todos los puestos pertenecientes a un acto concreto.
    """
    
    def get(self, request, acto_id, *args, **kwargs):
        puestos = obtener_puestos_por_acto(acto_id=acto_id)
        paginador = StandardResultsSetPagination()
        puestos_paginados = paginador.paginate_queryset(puestos, request, view=self)
        serializer = PuestoListadoSerializer(puestos_paginados, many=True)
        return paginador.get_paginated_response(serializer.data)