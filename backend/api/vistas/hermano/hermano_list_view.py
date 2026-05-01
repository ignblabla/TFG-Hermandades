from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from api.pagination import PaginacionDiezElementos
from api.serializadores.hermano.hermano_serializer import HermanoListadoSerializer
from api.servicios.hermano.hermano_service import get_listado_hermanos_service

from django.contrib.auth import get_user_model

User = get_user_model()


class HermanoListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PaginacionDiezElementos

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