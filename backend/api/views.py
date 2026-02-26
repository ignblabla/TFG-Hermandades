from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from rest_framework import generics, status
from django.db.models import Q

from api.servicios.comunicado.creacion_comunicado_service import ComunicadoService
from api.servicios.papeleta_telegram import TelegramWebhookService
from api.servicios.hermano.edicion_datos_hermano_service import update_mi_perfil_service
from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService

from .serializers import ActoCreateSerializer, AreaInteresSerializer, ComunicadoFormSerializer, ComunicadoListSerializer, DetalleVinculacionSerializer, HermanoAdminUpdateSerializer, HermanoListadoSerializer, HistorialPapeletaSerializer, PuestoUpdateSerializer, SolicitudUnificadaSerializer, TipoActoSerializer, UserSerializer, UserUpdateSerializer, ActoSerializer, PuestoSerializer, TipoPuestoSerializer, VincularPapeletaSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Acto, AreaInteres, Comunicado, Puesto
from django.utils import timezone
from .pagination import StandardResultsSetPagination
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError 
from django.core.exceptions import ValidationError as DjangoValidationError

from .services import actualizar_acto_service, crear_acto_service, create_acto_service, get_historial_papeletas_hermano_service, get_listado_hermanos_service, update_acto_service, create_puesto_service, get_tipos_puesto_service, update_hermano_por_admin_service, update_puesto_service, get_tipos_acto_service

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
# VIEWS: TIPOS DE ACTO
# -----------------------------------------------------------------------------
class TipoActoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipos = get_tipos_acto_service()
        serializer = TipoActoSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
# VIEWS: PANEL PARA ADMINISTRADORES
# -----------------------------------------------------------------------------
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
        
# -----------------------------------------------------------------------------
# VIEWS: CONSULTA EL HISTÓRICO DE PAPELETAS DE SITIO (NO ADMIN)
# -----------------------------------------------------------------------------
class MisPapeletasListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        try:
            queryset = get_historial_papeletas_hermano_service(usuario=request.user)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)

            if page is not None:
                serializer = HistorialPapeletaSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = HistorialPapeletaSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error en MisPapeletasListView: {str(e)}")
            return Response(
                {"detail": "Error al recuperar el historial de papeletas."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# -----------------------------------------------------------------------------
# VIEWS: CREAR ACTO
# -----------------------------------------------------------------------------
class CrearActoView(APIView):
    def post(self, request):
        serializer = ActoCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                acto = crear_acto_service(request.user, serializer.validated_data)
                return Response(
                    ActoCreateSerializer(acto).data,
                    status=status.HTTP_201_CREATED
                )
            except DjangoValidationError as e:
                if hasattr(e, 'message_dict'):
                    return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            except PermissionDenied as e:
                return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------------------------------------------------------
# VIEWS: ACTUALIZAR ACTO
# -----------------------------------------------------------------------------
class ActoUpdateView(APIView):
    """
    Vista para editar un acto existente.
    Soporta PUT (actualización total) y PATCH (actualización parcial).
    Delega la validación de negocio al Service.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        """Actualización completa del recurso."""
        return self._handle_update(request, pk, partial=False)

    def patch(self, request, pk):
        """Actualización parcial del recurso."""
        return self._handle_update(request, pk, partial=True)

    def _handle_update(self, request, pk, partial):
        """
        Método auxiliar para evitar duplicar código entre PUT y PATCH.
        """
        serializer = ActoCreateSerializer(data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                acto_actualizado = actualizar_acto_service(
                    usuario_solicitante=request.user,
                    acto_id=pk,
                    data_validada=serializer.validated_data
                )

                response_serializer = ActoCreateSerializer(acto_actualizado)
                return Response(response_serializer.data, status=status.HTTP_200_OK)

            except DjangoValidationError as e:
                if hasattr(e, 'message_dict'):
                    return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
                return Response(e.messages, status=status.HTTP_400_BAD_REQUEST)
            
            except DRFValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

            except PermissionDenied as e:
                return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
            except Exception as e:
                return Response(
                    {"detail": "Ocurrió un error inesperado al actualizar el acto."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------------------------------------
# VIEWS: CREAR COMUNICADO
# -----------------------------------------------------------------------------
class ComunicadoListCreateView(APIView):
    """
    GET: Lista todos los comunicados ordenados por fecha.
    POST: Crea un nuevo comunicado usando el Servicio de dominio.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        comunicados = Comunicado.objects.all().order_by('-fecha_emision')
        serializer = ComunicadoListSerializer(comunicados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
        serializer = ComunicadoFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            servicio = ComunicadoService()
            
            nuevo_comunicado = servicio.create_comunicado(
                usuario=request.user,
                data_validada=serializer.validated_data
            )

            response_serializer = ComunicadoListSerializer(nuevo_comunicado)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ComunicadoDetailView(APIView):
    """
    Gestiona operaciones sobre un comunicado específico.
    GET: Ver detalle
    PUT: Actualizar (Reemplazo total)
    PATCH: Actualizar parcialmente (Solo campos enviados)
    DELETE: Eliminar
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        comunicado = get_object_or_404(Comunicado, pk=pk)
        serializer = ComunicadoListSerializer(comunicado, context={'request': request})
        return Response(serializer.data)


    def put(self, request, pk):
        """Actualización total (espera todos los campos)"""
        comunicado = get_object_or_404(Comunicado, pk=pk)
        
        serializer = ComunicadoFormSerializer(comunicado, data=request.data) 
        serializer.is_valid(raise_exception=True)

        try:
            servicio = ComunicadoService()
            actualizado = servicio.update_comunicado(
                usuario=request.user,
                comunicado_instance=comunicado,
                data_validada=serializer.validated_data
            )
            return Response(ComunicadoListSerializer(actualizado).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, pk):
        """Actualización parcial (solo modifica los campos enviados)"""
        comunicado = get_object_or_404(Comunicado, pk=pk)
        serializer = ComunicadoFormSerializer(comunicado, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            servicio = ComunicadoService()
            actualizado = servicio.update_comunicado(
                usuario=request.user,
                comunicado_instance=comunicado,
                data_validada=serializer.validated_data
            )
            return Response(ComunicadoListSerializer(actualizado).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        comunicado = get_object_or_404(Comunicado, pk=pk)
        
        try:
            servicio = ComunicadoService()
            servicio.delete_comunicado(usuario=request.user, comunicado_instance=comunicado)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
# VISTA: LISTA DE ÁREAS DE INTERÉS (Para el Select del Frontend)
# -----------------------------------------------------------------------------
class AreaInteresListView(generics.ListAPIView):
    """
    Devuelve la lista de áreas disponibles para poblar los selectores en React.
    """
    queryset = AreaInteres.objects.all()
    serializer_class = AreaInteresSerializer
    permission_classes = [IsAuthenticated]



# -----------------------------------------------------------------------------
# VISTA: PAPELETA TELEGRAM
# -----------------------------------------------------------------------------
class TelegramWebhookView(APIView):
    """
    Endpoint público para recibir notificaciones (Webhooks) directamente desde los servidores de Telegram.
    """
    permission_classes = [AllowAny] # IMPORTANTE: Debe ser público para Telegram

    def post(self, request, *args, **kwargs):
        # Le pasamos la información a nuestro servicio
        TelegramWebhookService.procesar_actualizacion(request.data)
        
        # SIEMPRE debemos responder 200 OK a Telegram rápido. 
        # Si no lo hacemos, Telegram pensará que nuestro servidor está caído y reenviará el mensaje repetidas veces.
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