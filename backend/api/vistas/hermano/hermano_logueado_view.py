from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.serializadores.hermano.hermano_serializer import UserSerializer, UserUpdateSerializer
from api.servicios.hermano.hermano_service import update_mi_perfil_service

from django.contrib.auth import get_user_model

User = get_user_model()


class UsuarioLogueadoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            try:
                usuario_actualizado = update_mi_perfil_service(
                    usuario=user,
                    data_validada=serializer.validated_data
                )
                response_serializer = UserUpdateSerializer(usuario_actualizado)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)