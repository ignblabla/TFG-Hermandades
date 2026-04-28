from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404

from api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service import ReportesCiriosService
from api.models import Acto


class DescargarListadoCiriosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        acto = get_object_or_404(Acto, pk=pk)

        filtro_paso = request.query_params.get('paso', None)
        
        try:
            pdf_buffer = ReportesCiriosService.generar_pdf_cirios_asignados(acto, filtro_paso)

            nombre_archivo = f"asignacion_cirios_{acto.id}.pdf"
            if filtro_paso == 'CRISTO':
                nombre_archivo = f"asignacion_cirios_cristo_{acto.id}.pdf"
            elif filtro_paso == 'VIRGEN':
                nombre_archivo = f"asignacion_cirios_virgen_{acto.id}.pdf"

            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
            
            pdf_buffer.close()
            return response
            
        except Exception as e:
            return Response(
                {"error": "Error al generar el documento de cirios", "detalle": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )