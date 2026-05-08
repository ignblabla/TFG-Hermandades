from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from django.core.exceptions import ValidationError as DjangoValidationError

from api.servicios.acto.acto_service import crear_acto_service
from api.serializadores.acto.acto_serializer import ActoCreateSerializer
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador


class ActoCreateView(APIView):
    permission_classes = [EsAdministrador]
    
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