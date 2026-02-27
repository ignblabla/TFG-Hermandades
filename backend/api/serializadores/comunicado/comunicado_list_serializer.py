from rest_framework import serializers

from api.models import Comunicado



class ComunicadoListSerializer(serializers.ModelSerializer):
    """
    Optimizado para mostrar datos. 
    Las relaciones M2M se muestran como Strings (nombres).
    """
    tipo_display = serializers.CharField(source='get_tipo_comunicacion_display', read_only=True)
    areas_interes = serializers.StringRelatedField(many=True, read_only=True)
    autor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Comunicado
        fields = [
            'id', 'titulo', 'contenido', 'fecha_emision', 'imagen_portada',
            'tipo_comunicacion', 'tipo_display', 'autor_nombre', 
            'areas_interes'
        ]

    def get_autor_nombre(self, obj):
        if obj.autor:
            nombre = getattr(obj.autor, 'nombre', obj.autor.username)
            ap1 = getattr(obj.autor, 'primer_apellido', '')
            return f"{nombre} {ap1}".strip()
        return "Secretaría"