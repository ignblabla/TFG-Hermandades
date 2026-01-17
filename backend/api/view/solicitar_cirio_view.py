from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from api.service.solicitar_papeleta_cirio_service import solicitar_papeleta_cirio

from ..serializers import SolicitudCirioSerializer

class SolicitarCirioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SolicitudCirioSerializer(data=request.data)
        if serializer.is_valid():
            acto = serializer.validated_data['acto']
            puesto = serializer.validated_data['puesto']
            hermano = request.user

            try:
                papeleta = solicitar_papeleta_cirio(hermano, acto, puesto)
                return Response({
                    "status": "success",
                    "mensaje": f"Solicitud para {puesto.nombre} realizada correctamente",
                    "id_papeleta": papeleta.id,
                    "fecha": papeleta.fecha_solicitud
                }, status=status.HTTP_201_CREATED)
            
            except ValidationError as e:
                return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"detail": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        