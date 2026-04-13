import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from api.servicios.solicitud_cirio.solicitud_cirio_service import ReportesCiriosService
from api.models import Acto

class EjecutarRepartoCiriosView(APIView):
    """
    Endpoint administrativo para disparar el algoritmo de asignación de cirios
    y retornar el PDF con las posiciones resultantes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, acto_id):
        acto = get_object_or_404(Acto, pk=acto_id)

        try:
            cantidad_asignadas = ReportesCiriosService.ejecutar_asignacion_automatica_cirios(acto_id)

            pdf_buffer = ReportesCiriosService.generar_pdf_cirios_asignados(acto)
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            return Response({
                "mensaje": f"El reparto se ha ejecutado con éxito. Se han asignado {cantidad_asignadas} papeletas de sitio en los tramos.",
                "acto_id": acto_id,
                "asignadas": cantidad_asignadas,
                "pdf_base64": pdf_base64,
                "filename": f"asignacion_cirios_tramos_{acto.id}.pdf"
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Error interno del servidor durante el reparto.", "detalle": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )