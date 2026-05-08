from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.serializadores.papeleta_sitio.papeleta_sitio_serializer import PapeletaSitioSerializer
from api.servicios.papeleta_sitio.papeleta_sitio_service import validar_acceso_papeleta


class ValidarAccesoQRView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        papeleta_id = request.data.get('id')
        codigo = request.data.get('codigo')

        try:
            resultado = validar_acceso_papeleta(papeleta_id, codigo, request.user)

            data_papeleta = PapeletaSitioSerializer(resultado['papeleta']).data
            
            return Response({
                "resultado": resultado['status'],
                "mensaje": resultado['mensaje'],
                "datos": data_papeleta
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)