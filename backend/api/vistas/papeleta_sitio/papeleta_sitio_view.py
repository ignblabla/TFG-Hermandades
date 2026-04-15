from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from api.servicios.papeleta_sitio.papeleta_sitio_service import get_historial_papeletas_hermano_service, get_ultima_papeleta_hermano_service, obtener_datos_tabla_insignias_acto
from api.serializadores.papeleta_sitio.papeleta_sitio_serializer import FilaTablaInsigniaSerializer, HistorialPapeletaSerializer
from api.pagination import StandardResultsSetPagination

class TablaInsigniasActoView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, acto_id):
        if not getattr(request.user, 'esAdmin', False):
            raise PermissionDenied("Acceso denegado: Se requieren privilegios de administrador.")

        datos_aplanados = obtener_datos_tabla_insignias_acto(acto_id)
        
        serializer = FilaTablaInsigniaSerializer(datos_aplanados, many=True)
        return Response(serializer.data)



class UltimaPapeletaView(APIView):
    """
    Devuelve los detalles de la última papeleta de sitio del usuario logueado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        papeleta = get_ultima_papeleta_hermano_service(usuario=request.user)
        
        if not papeleta:
            return Response(
                {"detail": "No se han encontrado papeletas para este hermano."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = HistorialPapeletaSerializer(papeleta)
        return Response(serializer.data, status=status.HTTP_200_OK)



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