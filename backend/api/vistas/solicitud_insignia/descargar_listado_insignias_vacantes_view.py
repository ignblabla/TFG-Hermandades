from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService
from api.models import Acto


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