from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.servicios.comunicado.comunicado_service import ComunicadoService
from api.serializadores.comunicado.comunicado_serializer import ComunicadoListSerializer
from api.pagination import PaginacionDoceElementos
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador


class ComunicadoAdminListView(APIView):
    """
    Vista que delega la validación de administrador al servicio.
    """
    permission_classes = [EsAdministrador]
    pagination_class = PaginacionDoceElementos

    def get(self, request):
        comunicados = ComunicadoService.obtener_todos_los_comunicados(request.user)

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(comunicados, request, view=self)
        
        if page is not None:
            serializer = ComunicadoListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = ComunicadoListSerializer(comunicados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)