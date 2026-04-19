from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from api.models import Acto, TipoActo
from api.servicios.acto.acto_service import ActoService, crear_acto_service, update_acto_service
from api.serializadores.acto.acto_serializer import ActoCreateSerializer, ActoCultoCardSerializer, ActoListSerializer, ActoSerializer
from api.pagination import PaginacionDiezElementos


class ActoDetalleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Recuperar un acto específico por su ID.
        """
        acto = get_object_or_404(Acto, pk=pk)
        serializer = ActoSerializer(acto, context={'request': request})
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



class ProximosActosView(APIView):
    """
    Devuelve los 3 actos más próximos a partir de la fecha y hora actual,
    optimizados para las tarjetas del Dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ahora = timezone.now()

        proximos_actos = Acto.objects.filter(
            fecha__gte=ahora
        ).only(
            'id', 'nombre', 'fecha', 'lugar'
        ).order_by('fecha')[:3]

        serializer = ActoCultoCardSerializer(proximos_actos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ProximaEstacionPenitenciaView(APIView):
    """
    Devuelve el próximo acto que sea 'Estación de Penitencia'
    y que aún no haya ocurrido, diseñado para la cuenta regresiva.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ahora = timezone.now()

        proxima_estacion = Acto.objects.filter(
            tipo_acto__tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            fecha__gte=ahora
        ).select_related('tipo_acto').order_by('fecha').first()

        if proxima_estacion:
            serializer = ActoCultoCardSerializer(proxima_estacion)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "No hay ninguna Estación de Penitencia futura programada."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        


class ActoCreateView(APIView):
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



class ActoListAPIView(generics.ListAPIView):
    """
    Vista para listar todos los Actos.
    Utiliza PaginacionDiezElementos para devolver 10 resultados por página.
    """
    serializer_class = ActoListSerializer
    pagination_class = PaginacionDiezElementos

    def get_queryset(self):
        return ActoService.get_todos_los_actos()