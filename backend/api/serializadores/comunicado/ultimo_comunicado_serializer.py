from rest_framework import serializers
from api.models import Comunicado

class ComunicadoSerializer(serializers.ModelSerializer):
    tipo_comunicacion_display = serializers.CharField(source='get_tipo_comunicacion_display', read_only=True)

    areas_interes = serializers.SerializerMethodField()

    class Meta:
        model = Comunicado
        fields = [
            'id', 
            'titulo', 
            'contenido', 
            'imagen_portada', 
            'fecha_emision', 
            'tipo_comunicacion', 
            'tipo_comunicacion_display',
            'areas_interes'
        ]

    def get_areas_interes(self, obj):
        nombres_areas = []
        for area in obj.areas_interes.all():
            try:
                nombres_areas.append(str(area))
            except Exception:
                nombres_areas.append(f"Área (ID: {area.id})")
        return nombres_areas