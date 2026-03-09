from rest_framework import serializers

from api.models import Acto


class ActoCultoCardSerializer(serializers.ModelSerializer):
    """
    Serializador súper ligero diseñado específicamente para alimentar 
    el componente CultoCard del dashboard. Evita cargar relaciones anidadas.
    """
    class Meta:
        model = Acto
        fields = ['id', 'nombre', 'fecha', 'lugar']