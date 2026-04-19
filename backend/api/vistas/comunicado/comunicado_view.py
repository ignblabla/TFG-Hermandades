from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializadores.comunicado.comunicado_list_serializer import ComunicadoListSerializer
from api.models import AreaInteres, Comunicado

from django.db.models import Q

from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService


class MisComunicadosListView(generics.ListAPIView):
    """
    Devuelve los comunicados filtrados por las áreas de interés del usuario logueado,
    INCLUYENDO siempre los comunicados dirigidos a 'Todos los Hermanos'.
    """
    serializer_class = ComunicadoListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        mis_areas = usuario.areas_interes.all()

        queryset = Comunicado.objects.filter(
            Q(areas_interes__in=mis_areas) | 
            Q(areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS)
        ).distinct().order_by('-fecha_emision')

        return queryset
    


class ChatComunicadosView(APIView):
    """
    Endpoint para que los hermanos puedan hacer preguntas a la IA 
    sobre los comunicados oficiales de la hermandad.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pregunta = request.data.get('pregunta')
        
        if not pregunta or not str(pregunta).strip():
            return Response({"detail": "Debes enviar una pregunta válida en el campo 'pregunta'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            servicio_rag = ComunicadoRAGService()
            respuesta_ia = servicio_rag.preguntar_a_comunicados(pregunta)
            
            return Response({"respuesta": respuesta_ia}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": "Ocurrió un error interno procesando la consulta con la IA.", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )