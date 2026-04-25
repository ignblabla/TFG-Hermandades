from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import AreaInteres, Comunicado

from django.db.models import Q
from django.shortcuts import get_object_or_404

from api.serializadores.comunicado.comunicado_serializer import ComunicadoFormSerializer, ComunicadoListSerializer, ComunicadoSerializer
from api.servicios.comunicado.comunicado_service import ComunicadoService
from api.pagination import PaginacionDoceElementos
from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService


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
        


class UltimosComunicadosAreaInteresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        comunicados = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(request.user)
        
        if comunicados.exists():
            serializer = ComunicadoSerializer(comunicados, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        return Response(
            {'detail': 'No hay comunicados recientes en sus áreas de interés.'}, 
            status=status.HTTP_404_NOT_FOUND
        )



class ComunicadosRelacionadosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exclude_id):
        comunicados = ComunicadoService.obtener_comunicados_relacionados_usuario(request.user, exclude_id)

        serializer = ComunicadoSerializer(comunicados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class ComunicadoListCreateView(APIView):
    """
    Punto de entrada de la API para la consulta y creación de la colección de comunicados.

    Vista HTTP autenticada que delega las validaciones a los serializadores y la lógica de negocio a la capa de servicios.

    Attributes:
        permission_classes (list): Lista de clases de permisos de DRF. 
                                    Aplica `IsAuthenticated` a nivel de clase.

    Methods:
        get(request):
            Recupera el listado completo de comunicados.
            Orden: Descendente por fecha de emisión (más recientes primero).
            Respuesta: Array de objetos serializados con `ComunicadoListSerializer`.
            Códigos HTTP: 200 OK.

        post(request):
            Procesa la creación de un nuevo comunicado.
            Flujo de trabajo:
                1. Validación de entrada mediante `ComunicadoFormSerializer`.
                2. Delegación de la lógica de creación a `ComunicadoService.create_comunicado()`.
                3. Formateo de la respuesta utilizando `ComunicadoListSerializer`.
            Códigos HTTP: 
                - 201 Created (Éxito).
                - 400 Bad Request (Error de validación o excepción en la capa de servicio).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        filtro_areas = Q(areas_interes__in=usuario.areas_interes.all()) | \
                    Q(areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS)

        comunicados = Comunicado.objects.select_related('autor') \
                                        .prefetch_related('areas_interes') \
                                        .filter(filtro_areas) \
                                        .distinct() \
                                        .order_by('-fecha_emision')

        paginator = PaginacionDoceElementos()
        page = paginator.paginate_queryset(comunicados, request)

        if page is not None:
            serializer = ComunicadoListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

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
    Punto de acceso de la API para consultar, actualizar o eliminar un comunicado específico.

    Continúa el patrón de separación de responsabilidades de la arquitectura: 
    gestiona el ciclo de vida de la petición/respuesta HTTP, delega la limpieza 
    y validación de datos a `ComunicadoFormSerializer`, y confía en `ComunicadoService` 
    para la ejecución de las operaciones de base de datos y validación de permisos.

    Requiere autenticación mediante token o sesión activa.

    Attributes:
        permission_classes (list): Aplica `IsAuthenticated` para proteger el acceso.

    Methods:
        get(request, pk):
            Recupera los detalles de un comunicado específico por su clave primaria.
            Respuesta: Objeto serializado con `ComunicadoListSerializer`.
            Códigos HTTP: 200 OK, 404 Not Found.

        put(request, pk):
            Procesa la actualización total del comunicado (requiere todos los campos obligatorios).
            Delega la lógica a `ComunicadoService.update_comunicado()`.
            Códigos HTTP: 200 OK (Éxito), 400 Bad Request (Error validación/servicio), 404 Not Found.

        patch(request, pk):
            Procesa la actualización parcial del comunicado (permite enviar solo los campos a cambiar).
            Delega la lógica a `ComunicadoService.update_comunicado()`.
            Códigos HTTP: 200 OK (Éxito), 400 Bad Request (Error validación/servicio), 404 Not Found.

        delete(request, pk):
            Procesa la eliminación del comunicado.
            Delega la validación de permisos y el borrado a `ComunicadoService.delete_comunicado()`.
            Códigos HTTP: 204 No Content (Éxito), 400 Bad Request (Error servicio), 404 Not Found.
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