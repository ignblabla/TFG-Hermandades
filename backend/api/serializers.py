from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (TipoActo, Acto, Puesto, PapeletaSitio)

User = get_user_model()

# -----------------------------------------------------------------------------
# SERIALIZERS PARA SOLICITUD DE INSIGNIAS Y PAPELETAS
# -----------------------------------------------------------------------------

class SolicitudCirioSerializer(serializers.Serializer):
    acto = serializers.PrimaryKeyRelatedField(
        queryset = Acto.objects.all(),
        write_only=True,
        required=True
    )

    puesto = serializers.PrimaryKeyRelatedField(
        queryset=Puesto.objects.filter(disponible=True),
        write_only=True,
        required=True
    )

    id_papeleta = serializers.IntegerField(read_only=True, source='id')
    fecha_solicitud = serializers.DateTimeField(read_only=True)
    mensaje = serializers.CharField(read_only=True, default="Solicitud registrada correctamente.")
    numero_registro_vinculado = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        """
        Validación cruzada Acto - Puesto
        """
        acto = data.get('acto')
        puesto = data.get('puesto')

        if not acto.tipo_acto.requiere_papeleta:
            raise serializers.ValidationError({"acto_id": "Este acto no requiere solicitud de papeleta de sitio."})

        if puesto.acto.id != acto.id:
            raise serializers.ValidationError({"puesto_id": f"El puesto {puesto.nombre} no pertenece al acto {acto.nombre}."})

        if "CIRIO" not in puesto.tipo_puesto.nombre_tipo.upper():
            raise serializers.ValidationError({"puesto_id": "El puesto seleccionado no es de tipo CIRIO."})

        return data

# -----------------------------------------------------------------------------
# SERIALIZERS PARA LA SOLICITUD DE PAPELETA DE SITIO
# -----------------------------------------------------------------------------
class PreferenciaSolicitudDTO(serializers.Serializer):
    puesto_id = serializers.PrimaryKeyRelatedField(queryset=Puesto.objects.all(), source='puesto_solicitado')
    orden = serializers.IntegerField(source='orden_prioridad')


class SolicitudUnificadaSerializer(serializers.ModelSerializer):
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    modalidad_acto = serializers.CharField(source='acto.modalidad', read_only=True)

    acto_id = serializers.PrimaryKeyRelatedField(
        queryset=Acto.objects.all(), 
        source='acto', 
        write_only=True
    )

    puesto_general_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    preferencias_solicitadas = PreferenciaSolicitudDTO(many=True, write_only=True, required=False)
    preferencias = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = PapeletaSitio
        fields = [
            'id',
            'acto_id',
            'nombre_acto',
            'modalidad_acto',
            'anio',
            'estado_papeleta',
            'es_solicitud_insignia',
            'puesto_general_id',
            'preferencias_solicitadas',
            'preferencias',
            'fecha_solicitud'
        ]

        read_only_fields = ['id', 'anio', 'estado_papeleta', 'fecha_solicitud']


# -----------------------------------------------------------------------------
# SERIALIZERS PARA LA VINCULACIÓN DE PAPELETAS DE SITIO
# -----------------------------------------------------------------------------
class VincularPapeletaSerializer(serializers.Serializer):
    """
    Serializer simple para recibir el número de registro del hermano objetivo.
    """
    numero_registro_objetivo = serializers.IntegerField(
        required=True, 
        min_value=1,
        help_text="Número de registro del hermano con el que quieres ir."
    )

class DetalleVinculacionSerializer(serializers.ModelSerializer):
    """
    Para devolver la respuesta con los datos del hermano vinculado.
    """
    nombre_vinculado = serializers.SerializerMethodField()
    
    class Meta:
        model = PapeletaSitio
        fields = ['id', 'vinculado_a', 'nombre_vinculado']

    def get_nombre_vinculado(self, obj):
        if obj.vinculado_a:
            return f"{obj.vinculado_a.nombre} {obj.vinculado_a.primer_apellido}"
        return None
