from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.shortcuts import get_object_or_404


from api.serializadores.comunicado.comunicado_form_serializer import ComunicadoFormSerializer
from api.servicios.comunicado.creacion_comunicado_service import ComunicadoService
from api.models import Comunicado
from api.serializadores.comunicado.comunicado_list_serializer import ComunicadoListSerializer


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