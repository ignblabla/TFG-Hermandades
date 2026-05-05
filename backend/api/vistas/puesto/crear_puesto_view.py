from django.contrib.auth import get_user_model
from rest_framework import status

from api.serializadores.puesto.puesto_serializer import PuestoSerializer

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from api.servicios.puesto.puesto_service import create_puesto_service

User = get_user_model()


class CrearPuestoView(APIView):
    """
    Endpoint para crear un nuevo Puesto asociado a un Acto.
    Requiere autenticación y permisos de administrador (gestionados en el servicio).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PuestoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nuevo_puesto = create_puesto_service(
            usuario=request.user,
            data_validada=serializer.validated_data
        )

        response_serializer = PuestoSerializer(nuevo_puesto)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)