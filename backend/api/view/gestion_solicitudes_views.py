from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError

# Importamos el Servicio Unificado y los Serializers
from ..servicios.GestionSolicitudesService import GestionSolicitudesService
from ..serializers import (
    SolicitudInsigniaSerializer, 
    SolicitudCirioSerializer, 
    SolicitudUnificadaSerializer,
    PapeletaSitioSerializer # Opcional, para devolver la respuesta completa
)

# -----------------------------------------------------------------------------
# VISTA 1: SOLICITUD DE INSIGNIA (MODALIDAD TRADICIONAL - FASE 1)
# -----------------------------------------------------------------------------
class SolicitarInsigniaView(APIView):
    """
    Endpoint para solicitar insignias cuando el acto es TRADICIONAL.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Validación de formato de entrada (Serializer)
        serializer = SolicitudInsigniaSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                # 2. Instanciamos el servicio centralizado
                service = GestionSolicitudesService()

                # 3. Llamada al método específico de Insignias Tradicionales
                papeleta = service.procesar_solicitud_insignia_tradicional(
                    hermano=request.user,
                    acto=serializer.validated_data['acto'],
                    preferencias_data=serializer.validated_data['preferencias']
                )

                # 4. Respuesta exitosa
                # Reutilizamos el serializer para devolver la data formateada o uno de lectura
                return Response(
                    SolicitudInsigniaSerializer(papeleta).data, 
                    status=status.HTTP_201_CREATED
                )

            except DjangoValidationError as e:
                # Errores de negocio (fechas, permisos, lógica)
                mensaje = e.message if hasattr(e, 'message') else str(e)
                return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                # --- AGREGA ESTO PARA VER EL ERROR REAL ---
                import traceback
                print("¡¡¡ERROR INTERNO CAPTURADO!!!")
                print(str(e))
                print(traceback.format_exc())
                # ------------------------------------------
                return Response({"detail": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Errores de validación de campos (JSON mal formado, faltan campos, etc.)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------------------------------------
# VISTA 2: SOLICITUD DE CIRIO (MODALIDAD TRADICIONAL - FASE 2)
# -----------------------------------------------------------------------------
class SolicitarCirioView(APIView):
    """
    Endpoint para solicitar puesto directo (Cirio/Diputado) cuando el acto es TRADICIONAL.
    Permite vinculación de hermanos.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SolicitudCirioSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                service = GestionSolicitudesService()
                
                # Extraemos datos limpios del serializer
                acto = serializer.validated_data['acto']
                puesto = serializer.validated_data['puesto']
                numero_vinculado = serializer.validated_data.get('numero_registro_vinculado')

                # Llamada al método específico de Cirios Tradicionales
                papeleta = service.procesar_solicitud_cirio_tradicional(
                    hermano=request.user, 
                    acto=acto, 
                    puesto=puesto,
                    numero_registro_vinculado=numero_vinculado
                )
                
                # Construimos mensaje de éxito personalizado
                mensaje_exito = f"Solicitud para {puesto.nombre} realizada correctamente."
                if numero_vinculado:
                    mensaje_exito += f" Vinculada al hermano Nº {numero_vinculado}."

                return Response({
                    "status": "success",
                    "mensaje": mensaje_exito,
                    "id": papeleta.id,
                    "numero_papeleta": papeleta.numero_papeleta, # Será None hasta el reparto
                    "fecha": papeleta.fecha_solicitud
                }, status=status.HTTP_201_CREATED)
            
            except DjangoValidationError as e:
                mensaje = e.message if hasattr(e, 'message') else str(e)
                return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Error en SolicitarCirioView: {e}")
                return Response({"detail": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------------------------------------
# VISTA 3: SOLICITUD UNIFICADA (MODALIDAD UNIFICADA)
# -----------------------------------------------------------------------------
class CrearSolicitudUnificadaView(APIView):
    """
    Endpoint para solicitar Insignias y/o Cirios en una sola petición 
    cuando el acto es UNIFICADO.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SolicitudUnificadaSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                service = GestionSolicitudesService()

                acto = serializer.validated_data['acto']
                # En el serializer 'preferencias_solicitadas' es el campo de entrada
                preferencias = serializer.validated_data.get('preferencias_solicitadas', [])
                
                # Llamada al método específico Unificado
                papeleta = service.procesar_solicitud_unificada(
                    hermano=request.user,
                    acto=acto,
                    preferencias_data=preferencias
                )

                return Response(
                    SolicitudUnificadaSerializer(papeleta).data, 
                    status=status.HTTP_201_CREATED
                )

            except DjangoValidationError as e:
                mensaje_error = e.message if hasattr(e, 'message') else str(e)
                return Response({"detail": mensaje_error}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                print(f"Error en Unificada: {e}")
                return Response({"detail": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)