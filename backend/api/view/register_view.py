from django.db import DatabaseError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from api.serializers import UserSerializer
from api.service.register_service import create_hermano_solicitud_service, activar_hermano_service

# -----------------------------------------------------------------------------
# VIEWS: GESTIÓN DE HERMANOS
# -----------------------------------------------------------------------------

class HermanoCreateView(APIView):
    """
    Vista pública para la solicitud de alta de nuevos hermanos.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. CAPA DE VALIDACIÓN (Serializer)
        # El serializer verifica que el DNI sea único, que el IBAN tenga formato, etc.
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 2. CAPA DE NEGOCIO (Service)
            # Pasamos una copia de los datos validados para no mutar el objeto original del serializer
            # El servicio se encarga de la transacción atómica (Hermano + Banco)
            nuevo_hermano = create_hermano_solicitud_service(
                data_validada=serializer.validated_data.copy() 
            )

            # 3. RESPUESTA
            # Serializamos el objeto creado para devolverlo al Frontend
            # Usamos el mismo serializer para mantener coherencia en el formato
            response_serializer = UserSerializer(nuevo_hermano)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Errores de lógica de negocio (ej. "Ya existe una solicitud pendiente")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except DatabaseError:
            # Errores de infraestructura
            return Response(
                {"detail": "Error temporal en el servidor de base de datos. Inténtelo más tarde."}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except Exception as e:
            # Fallback para errores no controlados
            # En producción, aquí deberías loguear el error (print(e) o usar logger)
            return Response(
                {"detail": "Ocurrió un error inesperado procesando su solicitud."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class AprobarAltaHermanoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            hermano_activado = activar_hermano_service(admin_user=request.user, hermano_id=pk)
            return Response(UserSerializer(hermano_activado).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)