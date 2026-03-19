from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializadores.acto.solicitud_insignia_acto_serializer import ActoInsigniaResumenSerializer
from api.servicios.acto.acto_con_solicitud_insignias_abierta import ActoService

class ActoActivoInsigniasView(APIView):
    """
    Endpoint para obtener el acto cuyo plazo de solicitud de insignias 
    se encuentra actualmente abierto.
    """
    
    def get(self, request, *args, **kwargs):
        acto = ActoService.obtener_acto_activo_insignias()
        
        if acto:
            serializer = ActoInsigniaResumenSerializer(acto)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "No hay ningún acto con el plazo de solicitud de insignias abierto actualmente."}, 
                status=status.HTTP_404_NOT_FOUND
            )