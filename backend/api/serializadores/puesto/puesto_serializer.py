from rest_framework import serializers

from api.models import Puesto, TipoPuesto


class PuestoSerializer(serializers.ModelSerializer):
    tipo_puesto = serializers.SlugRelatedField(
        slug_field='nombre_tipo',
        queryset=TipoPuesto.objects.all()
    )

    es_insignia = serializers.BooleanField(source='tipo_puesto.es_insignia', read_only=True)

    class Meta:
        model = Puesto
        fields = [
            'id', 'nombre', 'numero_maximo_asignaciones', 
            'disponible', 'lugar_citacion', 'hora_citacion', 'acto',
            'tipo_puesto', 'es_insignia', 'cortejo_cristo', 'cantidad_ocupada', 'plazas_disponibles', 'porcentaje_ocupacion'
        ]
        
        read_only_fields = ['cantidad_ocupada', 'plazas_disponibles', 'porcentaje_ocupacion']

        extra_kwargs = {
            'hora_citacion': {
                'error_messages': {
                    'invalid': 'El formato de hora es incorrecto. Por favor, use el formato HH:MM (ej. 20:30).'
                }
            }
        }

    def validate_numero_maximo_asignaciones(self, value):
        """
        Validación de campo: El número de asignaciones debe ser positivo.
        """
        if value < 1:
            raise serializers.ValidationError("El número máximo de asignaciones debe ser al menos 1.")
        return value



class PuestoUpdateSerializer(PuestoSerializer):
    """
    Serializador específico para actualizaciones.
    Hereda de PuestoSerializer para no repetir campos, pero
    marca 'acto' como read_only para asegurar que no se modifica.
    """
    class Meta(PuestoSerializer.Meta):
        read_only_fields = ['acto', 'cantidad_ocupada', 'plazas_disponibles', 'porcentaje_ocupacion']