from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission

from api.serializadores.papeleta_sitio.papeleta_sitio_serializer import AsistenteActoSimplificadoSerializer
from api.servicios.papeleta_sitio.papeleta_sitio_service import obtener_asistentes_leidos_por_acto
from api.pagination import PaginacionVeinteElementos


class EsAdminHermano(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'esAdmin', False))



class ListarAsistentesLeidosActoView(APIView):
    """
    Devuelve la información esencial de los asistentes (Papeleta LEIDA) a un acto,
    paginada de 20 en 20.
    """
    permission_classes = [EsAdminHermano]
    pagination_class = PaginacionVeinteElementos

    def get(self, request, acto_id):
        try:
            papeletas = obtener_asistentes_leidos_por_acto(acto_id)

            paginator = self.pagination_class()

            page = paginator.paginate_queryset(papeletas, request, view=self)
            
            if page is not None:
                serializer = AsistenteActoSimplificadoSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = AsistenteActoSimplificadoSerializer(papeletas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Ocurrió un error al recuperar los asistentes."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )