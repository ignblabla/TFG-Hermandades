from rest_framework import serializers

from api.models import Tramo


class TramoSerializer(serializers.ModelSerializer):
    """
    Serializa la estructura de un tramo dentro de la cofradía.
    """
    paso_display = serializers.CharField(source='get_paso_display', read_only=True)
    
    class Meta:
        model = Tramo
        fields = ['id', 'nombre', 'numero_orden', 'paso', 'paso_display', 'acto', 'numero_maximo_cirios']