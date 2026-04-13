import base64

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404

from api.serializadores.solicitud_insignia.solicitud_insignia_serializer import ActoInsigniaResumenSerializer, SolicitudInsigniaSerializer
from api.servicios.solicitud_insignia.solicitud_insignia_service import ActoService, SolicitudInsigniaService
from api.models import Acto, PapeletaSitio, Puesto
from api.service.reparto_service import RepartoService


class ActoActivoInsigniasView(APIView):
    """
    Endpoint para obtener el acto cuyo plazo de solicitud de insignias 
    se encuentra actualmente abierto.
    """
    
    def get(self, request, *args, **kwargs):
        acto = ActoService.obtener_acto_activo_insignias()
        
        if acto:
            serializer = ActoInsigniaResumenSerializer(acto)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "No hay ningún acto con el plazo de solicitud de insignias abierto actualmente."}, 
                status=status.HTTP_404_NOT_FOUND
            )



class SolicitarInsigniaView(APIView):
    """
    Endpoint para solicitar insignias cuando el acto es TRADICIONAL.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SolicitudInsigniaSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                service = SolicitudInsigniaService()

                papeleta = service.procesar_solicitud_insignia_tradicional(
                    hermano=request.user,
                    acto=serializer.validated_data['acto'],
                    preferencias_data=serializer.validated_data['preferencias']
                )

                return Response(
                    SolicitudInsigniaSerializer(papeleta).data, 
                    status=status.HTTP_201_CREATED
                )

            except DjangoValidationError as e:
                mensaje = e.message if hasattr(e, 'message') else str(e)
                return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                return Response({"detail": "Error interno al procesar la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class EjecutarRepartoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        acto = get_object_or_404(Acto, pk=pk)
        
        try:
            resultado_algoritmo = RepartoService.ejecutar_asignacion_automatica(acto_id=pk)

            puestos_insignia = Puesto.objects.filter(acto_id=pk, tipo_puesto__es_insignia=True)
            total_cupo_insignias = sum(p.numero_maximo_asignaciones for p in puestos_insignia)

            insignias_asignadas = PapeletaSitio.objects.filter(
                acto_id=pk,
                es_solicitud_insignia=True,
                puesto__isnull=False
            ).count()

            insignias_no_asignadas = total_cupo_insignias - insignias_asignadas

            stats = {
                "total_asignados": insignias_asignadas,
                "total_no_asignados": max(0, insignias_no_asignadas),
                "total_insignias": total_cupo_insignias
            }

            if isinstance(resultado_algoritmo, dict):
                resultado_algoritmo.update(stats)
            else:
                resultado_algoritmo = stats

            pdf_buffer = SolicitudInsigniaService.generar_pdf_asignados(acto)
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

            return Response({
                "mensaje": "Reparto ejecutado con éxito.",
                "detalle_algoritmo": resultado_algoritmo,
                "pdf_base64": pdf_base64,
                "filename": f"asignacion_insignias_{acto.id}.pdf"
            }, status=status.HTTP_200_OK)

        except DjangoValidationError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": "Error interno del servidor", "detalle": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class DescargarListadoInsigniasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        acto = get_object_or_404(Acto, pk=pk)
        
        try:
            pdf_buffer = SolicitudInsigniaService.generar_pdf_asignados(acto)

            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="asignacion_insignias_{acto.id}.pdf"'
            
            pdf_buffer.close()
            return response
            
        except Exception as e:
            return Response(
                {"error": "Error al generar el documento", "detalle": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class DescargarListadoVacantesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        acto = get_object_or_404(Acto, pk=pk)
        
        try:
            pdf_buffer = SolicitudInsigniaService.generar_pdf_vacantes(acto)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="insignias_vacantes_{acto.id}.pdf"'
            
            pdf_buffer.close()
            return response
            
        except Exception as e:
            return Response(
                {"error": "Error al generar el documento de vacantes", "detalle": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class DescargarListadoTodasInsigniasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        acto = get_object_or_404(Acto, pk=pk)
        
        try:
            pdf_buffer = SolicitudInsigniaService.generar_pdf_todas_insignias(acto)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="catalogo_insignias_{acto.id}.pdf"'
            
            pdf_buffer.close()
            return response
            
        except Exception as e:
            return Response(
                {"error": "Error al generar el catálogo de insignias", "detalle": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )