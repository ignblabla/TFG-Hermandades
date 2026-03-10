from rest_framework import serializers
from api.models import Comunicado

class ComunicadoSerializer(serializers.ModelSerializer):
    tipo_comunicacion_display = serializers.CharField(source='get_tipo_comunicacion_display', read_only=True)

    class Meta:
        model = Comunicado
        fields = [
            'id', 
            'titulo', 
            'contenido', 
            'imagen_portada', 
            'fecha_emision', 
            'tipo_comunicacion', 
            'tipo_comunicacion_display'
        ]