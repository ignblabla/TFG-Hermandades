import traceback

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from api.servicios.solicitud_baja.crear_solicitud_baja_service import crear_solicitud_baja
from api.serializadores.solicitud_baja.solicitud_baja_serializer import SolicitudBajaSerializer
from api.models import SolicitudBaja
from api.pagination import PaginacionDiezElementos



class SolicitudBajaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Método GET para listar las solicitudes.
        Si el usuario es administrador, ve todas. Si es un hermano normal, ve solo las suyas.
        """
        # 1. Obtenemos las solicitudes dependiendo de si es Admin o no
        if request.user.esAdmin:
            queryset = SolicitudBaja.objects.all().order_by('-fecha_solicitud')
        else:
            queryset = SolicitudBaja.objects.filter(hermano=request.user).order_by('-fecha_solicitud')

        # 2. Calculamos el resumen para las tarjetas del frontend
        total_pendientes = queryset.filter(estado=SolicitudBaja.EstadoSolicitud.PENDIENTE).count()
        total_aprobadas = queryset.filter(estado=SolicitudBaja.EstadoSolicitud.APROBADA).count()
        total_denegadas = queryset.filter(estado=SolicitudBaja.EstadoSolicitud.DENEGADA).count()

        # 3. Paginación
        paginator = PaginacionDiezElementos()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = SolicitudBajaSerializer(page, many=True)
            # Obtenemos la respuesta paginada estándar de DRF
            response_data = paginator.get_paginated_response(serializer.data).data
            
            # Le inyectamos nuestro "resumen" extra al JSON de respuesta
            response_data['resumen'] = {
                'total_pendientes': total_pendientes,
                'total_aprobadas': total_aprobadas,
                'total_denegadas': total_denegadas,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        # Fallback por si la paginación falla
        serializer = SolicitudBajaSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



    def post(self, request, *args, **kwargs):
        motivo = request.data.get('motivo', '')

        try:
            nueva_solicitud = crear_solicitud_baja(usuario=request.user, motivo=motivo)
            serializer = SolicitudBajaSerializer(nueva_solicitud)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": list(e.messages) if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("\n❌ ERROR GRAVE EN SOLICITUD DE BAJA:")
            traceback.print_exc() 
            print("----------------------------------\n")
            return Response({"error": "Ocurrió un error inesperado al procesar la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)