from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.servicios.papeleta_sitio.papeleta_sitio_service import get_ultima_papeleta_hermano_service
from api.serializadores.papeleta_sitio.papeleta_sitio_serializer import HistorialPapeletaSerializer


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