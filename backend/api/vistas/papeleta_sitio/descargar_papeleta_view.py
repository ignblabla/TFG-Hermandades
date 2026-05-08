from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from api.models import PapeletaSitio
from api.service.GenerarQRPapeletaService import generar_pdf_papeleta


class DescargarPapeletaPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        papeleta = get_object_or_404(PapeletaSitio, pk=pk, hermano=request.user)

        if papeleta.estado_papeleta not in ['EMITIDA', 'RECOGIDA', 'LEIDA']:
            return FileResponse(b"La papeleta aun no esta disponible para descarga", status=403)

        pdf_buffer = generar_pdf_papeleta(papeleta)

        filename = f"Papeleta_{papeleta.anio}_{papeleta.hermano.dni}.pdf"
        return FileResponse(
            pdf_buffer, 
            as_attachment=True, 
            filename=filename,
            content_type='application/pdf'
        )