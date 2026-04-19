from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.serializadores.papeleta_sitio.papeleta_sitio_serializer import PreferenciaSolicitudDTO

from .models import (Acto, Puesto, PapeletaSitio)

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