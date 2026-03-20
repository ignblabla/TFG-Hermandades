from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied

from django.core.exceptions import ValidationError as DjangoValidationError

from api.serializers import ActoCreateSerializer, ActoSerializer
from api.servicios.acto.acto_service import ActoService, crear_acto_service
from api.pagination import PaginacionDiezElementos


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
    serializer_class = ActoSerializer
    pagination_class = PaginacionDiezElementos

    def get_queryset(self):
        return ActoService.get_todos_los_actos()