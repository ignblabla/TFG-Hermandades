from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.servicios.papeleta_sitio.papeleta_sitio_service import obtener_estadisticas_asistencia
from api.vistas.papeleta_sitio.lista_asistentes_leidos_view import EsAdminHermano


class EstadisticasAsistenciaView(APIView):
    permission_classes = [EsAdminHermano]

    def get(self, request, acto_id):
        try:
            stats = obtener_estadisticas_asistencia(acto_id)
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)