from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Comunicado
from api.serializadores.comunicado.comunicado_form_serializer import ComunicadoFormSerializer
from api.servicios.comunicado.creacion_comunicado_service import ComunicadoService
from api.serializadores.comunicado.comunicado_list_serializer import ComunicadoListSerializer


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