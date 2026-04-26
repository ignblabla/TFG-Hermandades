import base64

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService
from api.models import Acto, PapeletaSitio, Puesto
from api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service import RepartoService


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