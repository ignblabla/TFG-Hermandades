from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from rest_framework import generics, status
from django.db.models import Q

from api.servicios.papeleta_telegram import TelegramWebhookService
from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService
from api.serializadores.comunicado.comunicado_list_serializer import ComunicadoListSerializer
from api.serializadores.hermano.hermano_serializer import UserSerializer, UserUpdateSerializer
from api.serializadores.tipo_puesto.tipo_puesto_serializer import TipoPuestoSerializer
from api.serializadores.puesto.puesto_serializer import PuestoSerializer, PuestoUpdateSerializer

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from api.servicios.hermano.hermano_service import update_mi_perfil_service
from .models import AreaInteres, Comunicado, Puesto

from .services import create_puesto_service, get_tipos_puesto_service, update_puesto_service

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

# -----------------------------------------------------------------------------
# VIEWS: PUESTO
# -----------------------------------------------------------------------------

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
    
class PuestoDetalleView(APIView):
    """
    Endpoint para ver, editar o eliminar un puesto específico.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        puesto = get_object_or_404(Puesto, pk=pk)
        serializer = PuestoSerializer(puesto)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def put(self, request, pk):
        """Actualización completa"""
        puesto = get_object_or_404(Puesto, pk=pk)
        serializer = PuestoUpdateSerializer(puesto, data=request.data)
        serializer.is_valid(raise_exception=True)

        puesto_actualizado = update_puesto_service(
            usuario = request.user,
            puesto_id = pk,
            data_validada=serializer.validated_data
        )

        return Response(PuestoSerializer(puesto_actualizado).data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        """Actualización parcial"""
        puesto = get_object_or_404(Puesto, pk=pk)
        serializer = PuestoUpdateSerializer(puesto, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        puesto_actualizado = update_puesto_service(
            usuario=request.user, 
            puesto_id=pk, 
            data_validada=serializer.validated_data
        )

        return Response(PuestoSerializer(puesto_actualizado).data, status=status.HTTP_200_OK)

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

# -----------------------------------------------------------------------------
# VIEWS: CREAR COMUNICADO
# -----------------------------------------------------------------------------
class MisComunicadosListView(generics.ListAPIView):
    """
    Devuelve los comunicados filtrados por las áreas de interés del usuario logueado,
    INCLUYENDO siempre los comunicados dirigidos a 'Todos los Hermanos'.
    """
    serializer_class = ComunicadoListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        mis_areas = usuario.areas_interes.all()

        queryset = Comunicado.objects.filter(
            Q(areas_interes__in=mis_areas) | 
            Q(areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS)
        ).distinct().order_by('-fecha_emision')

        return queryset


# -----------------------------------------------------------------------------
# VISTA: PAPELETA TELEGRAM
# -----------------------------------------------------------------------------
class TelegramWebhookView(APIView):
    """
    Endpoint público para recibir notificaciones (Webhooks) directamente desde los servidores de Telegram.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        TelegramWebhookService.procesar_actualizacion(request.data)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)



class ChatComunicadosView(APIView):
    """
    Endpoint para que los hermanos puedan hacer preguntas a la IA 
    sobre los comunicados oficiales de la hermandad.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pregunta = request.data.get('pregunta')
        
        if not pregunta or not str(pregunta).strip():
            return Response({"detail": "Debes enviar una pregunta válida en el campo 'pregunta'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            servicio_rag = ComunicadoRAGService()
            respuesta_ia = servicio_rag.preguntar_a_comunicados(pregunta)
            
            return Response({"respuesta": respuesta_ia}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": "Ocurrió un error interno procesando la consulta con la IA.", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )