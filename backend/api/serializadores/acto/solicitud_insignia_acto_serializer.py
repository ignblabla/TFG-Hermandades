from rest_framework import serializers
from api.models import Acto, Puesto
from django.utils import timezone
from api.serializers import PuestoSerializer


class PuestoInsigniaResumenSerializer(serializers.ModelSerializer):
    """
    Serializador ultra-ligero para listar las insignias a solicitar.
    """
    tipo_puesto = serializers.SlugRelatedField(
        slug_field='nombre_tipo',
        read_only=True
    )
    
    es_insignia = serializers.BooleanField(
        source='tipo_puesto.es_insignia', 
        read_only=True
    )

    class Meta:
        model = Puesto
        fields = [
            'id', 
            'nombre', 
            'disponible', 
            'acto', 
            'es_insignia', 
            'cortejo_cristo', 
            'tipo_puesto'
        ]


class ActoInsigniaResumenSerializer(serializers.ModelSerializer):
    """
    Serializador ligero optimizado para la pantalla de solicitud de insignias.
    """
    en_plazo_insignias = serializers.SerializerMethodField()
    puestos_disponibles = serializers.SerializerMethodField()

    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        read_only=True
    )
    requiere_papeleta = serializers.BooleanField(
        source='tipo_acto.requiere_papeleta', 
        read_only=True
    )

    class Meta:
        model = Acto
        fields = [
            'id', 
            'nombre',
            'tipo_acto',
            'modalidad',
            'requiere_papeleta',
            'inicio_solicitud', 
            'fin_solicitud',    
            'en_plazo_insignias', 
            'puestos_disponibles'
        ]

    def get_en_plazo_insignias(self, obj):
        ahora = timezone.now()
        if obj.inicio_solicitud and obj.fin_solicitud:
            return obj.inicio_solicitud <= ahora <= obj.fin_solicitud
        return False
        
    def get_puestos_disponibles(self, obj):
        puestos = obj.puestos_disponibles.filter(
            disponible=True, 
            tipo_puesto__es_insignia=True
        )
        return PuestoInsigniaResumenSerializer(puestos, many=True).data