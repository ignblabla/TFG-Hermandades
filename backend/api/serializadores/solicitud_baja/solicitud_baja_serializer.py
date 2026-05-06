from rest_framework import serializers

from api.models import SolicitudBaja


class SolicitudBajaSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudBaja
        fields = [
            'id', 
            'hermano',
            'nombre_completo',
            'motivo', 
            'fecha_solicitud', 
            'estado', 
            'estado_display',
            'fecha_resolucion', 
        ]

        read_only_fields = [
            'id', 
            'hermano', 
            'fecha_solicitud', 
            'estado', 
            'fecha_resolucion', 
        ]

    def get_nombre_completo(self, obj):
        hermano = obj.hermano
        apellidos = f"{hermano.primer_apellido} {hermano.segundo_apellido}".strip()
        return f"{hermano.nombre} {apellidos}"



class ListadoSolicitudesBajaSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    numero_registro = serializers.IntegerField(source='hermano.numero_registro', read_only=True)
    fecha_ingreso_corporacion = serializers.DateField(source='hermano.fecha_ingreso_corporacion', read_only=True)

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = SolicitudBaja
        fields = [
            'id', 
            'nombre_completo',
            'numero_registro',
            'fecha_ingreso_corporacion',
            'motivo', 
            'fecha_solicitud', 
            'estado', 
            'estado_display',
            'fecha_resolucion'
        ]

    def get_nombre_completo(self, obj):
        """Construlle el nombre completo del hermano"""
        hermano = obj.hermano
        apellidos = f"{hermano.primer_apellido} {hermano.segundo_apellido}".strip()
        return f"{hermano.nombre} {apellidos}"