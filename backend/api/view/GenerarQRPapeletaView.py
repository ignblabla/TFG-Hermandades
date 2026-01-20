from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status

from api.models import PapeletaSitio
from api.service.GenerarQRPapeletaService import generar_pdf_papeleta, validar_acceso_papeleta
from api.serializers import PapeletaSitioSerializer

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
    

class ValidarAccesoQRView(APIView):
    permission_classes = [IsAuthenticated] # Requiere que el Diputado esté logueado en el móvil

    def post(self, request):
        papeleta_id = request.data.get('id')
        codigo = request.data.get('codigo')

        try:
            resultado = validar_acceso_papeleta(papeleta_id, codigo, request.user)
            
            # Serializamos la papeleta para mostrar datos del hermano en pantalla
            data_papeleta = PapeletaSitioSerializer(resultado['papeleta']).data
            
            return Response({
                "resultado": resultado['status'],
                "mensaje": resultado['mensaje'],
                "datos": data_papeleta
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)