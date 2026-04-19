from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied

from api.pagination import StandardResultsSetPagination
from api.serializadores.hermano.hermano_serializer import HermanoAdminUpdateSerializer, HermanoListadoSerializer, UserSerializer, UserUpdateSerializer
from api.servicios.hermano.hermano_service import get_listado_hermanos_service, update_hermano_por_admin_service, update_mi_perfil_service

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()

class HermanoListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        try:
            queryset_hermanos = get_listado_hermanos_service(usuario_solicitante=request.user)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset_hermanos, request)
            if page is not None:
                serializer = HermanoListadoSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = HermanoListadoSerializer(queryset_hermanos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response(
                {"detail": "Error al recuperar el listado.", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


class HermanoAdminDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not getattr(request.user, 'esAdmin', False):
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        
        hermano = get_object_or_404(User, pk=pk)
        serializer = HermanoAdminUpdateSerializer(hermano)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def put(self, request, pk):
        """
        Actualización completa (requiere enviar todos los campos obligatorios).
        """
        hermano = get_object_or_404(User, pk=pk)

        serializer = HermanoAdminUpdateSerializer(hermano, data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            hermano_actualizado = update_hermano_por_admin_service(
                usuario_solicitante=request.user,
                hermano_id=pk,
                data_validada=serializer.validated_data
            )
            return Response(HermanoAdminUpdateSerializer(hermano_actualizado).data, status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        

    def patch(self, request, pk):
        """
        Actualización parcial (solo los campos enviados).
        """
        hermano = get_object_or_404(User, pk=pk)

        serializer = HermanoAdminUpdateSerializer(hermano, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            hermano_actualizado = update_hermano_por_admin_service(
                usuario_solicitante=request.user,
                hermano_id=pk,
                data_validada=serializer.validated_data
            )
            return Response(HermanoAdminUpdateSerializer(hermano_actualizado).data, status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        


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



class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]