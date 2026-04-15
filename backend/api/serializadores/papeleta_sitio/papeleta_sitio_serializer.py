from rest_framework import serializers

from api.models import PapeletaSitio

class FilaTablaInsigniaSerializer(serializers.Serializer):
    dni = serializers.CharField(max_length=9)
    estado = serializers.CharField(max_length=50)
    fecha_solicitud = serializers.DateTimeField(format="%d/%m/%Y %H:%M", allow_null=True)
    acto = serializers.CharField(max_length=100)
    es_solicitud_insignia = serializers.BooleanField()
    preferencia = serializers.CharField(max_length=200)



# -----------------------------------------------------------------------------
# SERIALIZERS PARA CONSULTAR EL HISTÓRICO DE PAPELETAS DE SITIO (NO ADMIN)
# -----------------------------------------------------------------------------
class HistorialPapeletaSerializer(serializers.ModelSerializer):
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    fecha_acto = serializers.DateTimeField(source='acto.fecha', read_only=True)

    nombre_puesto = serializers.CharField(source='puesto.nombre', read_only=True, allow_null=True)
    nombre_tramo = serializers.CharField(source='tramo.nombre', read_only=True, allow_null=True)
    numero_tramo = serializers.IntegerField(source='tramo.numero_orden', read_only=True, allow_null=True)

    es_insignia = serializers.BooleanField(source='puesto.tipo_puesto.es_insignia', read_only=True, default=False)
    tipo_acto = serializers.CharField(source='acto.tipo_acto.tipo', read_only=True)

    lugar_citacion = serializers.CharField(source='puesto.lugar_citacion', read_only=True, allow_null=True)
    hora_citacion = serializers.TimeField(source='puesto.hora_citacion', read_only=True, allow_null=True)

    lado_display = serializers.CharField(source='get_lado_display', read_only=True)

    class Meta:
        model = PapeletaSitio
        fields = [
            'id',
            'acto',
            'estado_papeleta', 
            'fecha_solicitud', 
            'fecha_emision', 
            'anio',
            'tipo_acto',
            'nombre_acto',
            'fecha_acto',
            'nombre_puesto',
            'nombre_tramo',
            'numero_tramo',
            'es_insignia',
            'lugar_citacion',
            'hora_citacion',
            'orden_en_tramo',
            'lado',
            'lado_display'
        ]