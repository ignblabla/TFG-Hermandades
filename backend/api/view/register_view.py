from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from api.serializers import UserSerializer
from api.service.register_service import create_hermano_solicitud_service, activar_hermano_service

# -----------------------------------------------------------------------------
# VIEWS: GESTIÓN DE HERMANOS
# -----------------------------------------------------------------------------

class HermanoCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)

        try:
            nuevo_hermano = create_hermano_solicitud_service(data_validada = serializer.validated_data)
            response_serializer = UserSerializer(nuevo_hermano)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"detail": f"Error procesando la solicitud: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        

class AprobarAltaHermanoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            hermano_activado = activar_hermano_service(admin_user=request.user, hermano_id=pk)
            return Response(UserSerializer(hermano_activado).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)