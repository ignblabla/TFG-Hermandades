from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from rest_framework import generics, status
from .serializers import UserSerializer, UserUpdateSerializer, ActoSerializer, PuestoSerializer, TipoPuestoSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Acto
from django.utils import timezone

from .services import create_acto_service, update_acto_service, create_puesto_service, get_tipos_puesto_service


# Create your views here.

User = get_user_model()

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UsuarioLogueadoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        user = request.user
        serializer = UserUpdateSerializer(user, data = request.data, partial = True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# -----------------------------------------------------------------------------
# VIEWS: ACTO
# -----------------------------------------------------------------------------

class ActoListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        anio_actual = timezone.now().year
        actos = Acto.objects.filter(fecha__year = anio_actual).order_by('fecha')
        serializer = ActoSerializer(actos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ActoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nuevo_acto = create_acto_service(
            usuario=request.user,
            data_validada=serializer.validated_data                   
        )

        response_serializer = ActoSerializer(nuevo_acto)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    

class ActoDetalleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Recuperar un acto específico por su ID.
        """
        acto = get_object_or_404(Acto, pk=pk)
        serializer = ActoSerializer(acto)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """
        Actualización completa de un acto.
        """
        acto = get_object_or_404(Acto, pk=pk)
        serializer = ActoSerializer(acto, data=request.data)
        serializer.is_valid(raise_exception=True)

        acto_actualizado = update_acto_service(usuario=request.user, acto_id=pk, data_validada=serializer.validated_data)

        response_serializer = ActoSerializer(acto_actualizado)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        """
        Actualización parcial de un acto (solo algunos campos).
        """
        acto = get_object_or_404(Acto, pk=pk)

        serializer = ActoSerializer(acto, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        acto_actualizado = update_acto_service(
            usuario=request.user,
            acto_id=pk,
            data_validada=serializer.validated_data
        )

        response_serializer = ActoSerializer(acto_actualizado)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    

# -----------------------------------------------------------------------------
# VIEWS: PUESTO
# -----------------------------------------------------------------------------

class CrearPuestoView(APIView):
    """
    Endpoint para crear un nuevo Puesto asociado a un Acto.
    Requiere autenticación y permisos de administrador (gestionados en el servicio).
    """
    permission_classes = [IsAuthenticated]

    def post(Self, request):
        serializer = PuestoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nuevo_puesto = create_puesto_service(
            usuario=request.user,
            data_validada=serializer.validated_data
        )

        response_serializer = PuestoSerializer(nuevo_puesto)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    

# -----------------------------------------------------------------------------
# VIEWS: TIPO DE PUESTO
# -----------------------------------------------------------------------------
class TipoPuestoListView(APIView):
    """
    Endpoint para listar los tipos de puestos disponibles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipos = get_tipos_puesto_service()
        serializer = TipoPuestoSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
