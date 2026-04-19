from rest_framework import serializers

from api.models import Cuota


class CuotaSerializer(serializers.ModelSerializer):
    """
    Historial de pagos. Generalmente es de solo lectura desde la API de perfil,
    ya que los pagos se generan por procesos (Service) o pasarelas.
    """
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Cuota
        fields = [
            'id', 'anio', 'tipo', 'tipo_display', 'descripcion', 
            'importe', 'estado', 'estado_display', 
            'fecha_emision', 'fecha_pago', 'metodo_pago', 'observaciones'
        ]
        read_only_fields = fields