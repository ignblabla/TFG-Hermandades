from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from api.models import PapeletaSitio
from api.service.GenerarQRPapeletaService import generar_pdf_papeleta

class DescargarPapeletaPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # 1. Obtener la papeleta y verificar seguridad (que sea del usuario)
        papeleta = get_object_or_404(PapeletaSitio, pk=pk, hermano=request.user)

        # 2. Validar lógica de negocio (opcional: solo si está emitida o pagada)
        if papeleta.estado_papeleta not in ['EMITIDA', 'RECOGIDA', 'LEIDA']:
            return FileResponse(b"La papeleta aun no esta disponible para descarga", status=403)

        # 3. Llamar al servicio para generar el binario
        pdf_buffer = generar_pdf_papeleta(papeleta)

        # 4. Retornar FileResponse
        filename = f"Papeleta_{papeleta.anio}_{papeleta.hermano.dni}.pdf"
        return FileResponse(
            pdf_buffer, 
            as_attachment=True, 
            filename=filename,
            content_type='application/pdf'
        )