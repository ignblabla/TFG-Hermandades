from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.serializers import MisPapeletasSerializer
from api.service.ConsultaPapeletasService import get_papeletas_usuario_service

class MisPapeletasListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            papeletas = get_papeletas_usuario_service(request.user)
            serializer = MisPapeletasSerializer(papeletas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": "Error al recuperar las papeletas.", "detalle": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )