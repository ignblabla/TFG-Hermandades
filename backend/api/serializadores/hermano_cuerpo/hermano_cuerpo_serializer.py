from rest_framework import serializers

from api.models import CuerpoPertenencia, HermanoCuerpo


class HermanoCuerpoSerializer(serializers.ModelSerializer):
    """
    Gestiona la pertenencia de un hermano a un cuerpo (ej. Costaleros, Nazarenos).
    """
    nombre_cuerpo = serializers.CharField(source='cuerpo.get_nombre_cuerpo_display', read_only=True)
    cuerpo_slug = serializers.SlugRelatedField(
        slug_field='nombre_cuerpo',
        queryset=CuerpoPertenencia.objects.all(),
        source='cuerpo',
        write_only=True
    )

    class Meta:
        model = HermanoCuerpo
        fields = ['id', 'hermano', 'cuerpo_slug', 'nombre_cuerpo', 'anio_ingreso']
        extra_kwargs = {
            'hermano': {'read_only': True} 
        }
    
    def validate_anio_ingreso(self, value):
        from django.utils import timezone
        anio_actual = timezone.now().year
        if value > anio_actual:
            raise serializers.ValidationError("El año de ingreso no puede ser futuro.")
        if value < 1900:
            raise serializers.ValidationError("El año de ingreso no es válido.")
        return value