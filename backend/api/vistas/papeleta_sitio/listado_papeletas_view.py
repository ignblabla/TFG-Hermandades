from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.servicios.papeleta_sitio.papeleta_sitio_service import get_historial_papeletas_hermano_service
from api.serializadores.papeleta_sitio.papeleta_sitio_serializer import HistorialPapeletaSerializer
from api.pagination import StandardResultsSetPagination


class MisPapeletasListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        try:
            queryset = get_historial_papeletas_hermano_service(usuario=request.user)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)

            if page is not None:
                serializer = HistorialPapeletaSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = HistorialPapeletaSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error en MisPapeletasListView: {str(e)}")
            return Response(
                {"detail": "Error al recuperar el historial de papeletas."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )