from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from api.servicios.papeleta_sitio.papeleta_sitio_service import obtener_datos_tabla_insignias_acto
from api.serializadores.papeleta_sitio.papeleta_sitio_serializer import FilaTablaInsigniaSerializer

class TablaInsigniasActoView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, acto_id):
        if not getattr(request.user, 'esAdmin', False):
            raise PermissionDenied("Acceso denegado: Se requieren privilegios de administrador.")

        datos_aplanados = obtener_datos_tabla_insignias_acto(acto_id)
        
        serializer = FilaTablaInsigniaSerializer(datos_aplanados, many=True)
        return Response(serializer.data)