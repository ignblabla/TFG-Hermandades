import os

from django.http import FileResponse
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService


class ChatComunicadosView(APIView):
    """
    Endpoint para que los hermanos puedan hacer preguntas a la IA 
    sobre los comunicados oficiales de la hermandad o descargar el programa.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pregunta = request.data.get('pregunta')
        
        if not pregunta or not str(pregunta).strip():
            return Response({"detail": "Debes enviar una pregunta válida en el campo 'pregunta'."}, status=status.HTTP_400_BAD_REQUEST)

        pregunta_lower = str(pregunta).lower()

        if "llamador" in pregunta_lower or "programa" in pregunta_lower:
            ruta_pdf = os.path.join(settings.MEDIA_ROOT, 'documentos', 'horarios.pdf')

            print("BUSCANDO PDF EN:", ruta_pdf)
            
            if os.path.exists(ruta_pdf):
                archivo = open(ruta_pdf, 'rb')
                return FileResponse(archivo, as_attachment=True, filename='horarios.pdf')
            else:
                return Response(
                    {"detail": "El programa de mano aún no está disponible para su descarga en el servidor."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
        try:
            servicio_rag = ComunicadoRAGService()
            respuesta_ia = servicio_rag.preguntar_a_comunicados(pregunta)
            
            return Response({"respuesta": respuesta_ia}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": "Ocurrió un error interno procesando la consulta con la IA.", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )