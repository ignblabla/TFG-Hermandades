from rest_framework import serializers

from api.models import AreaInteres
from api.serializadores.datos_bancarios.datos_bancarios_serializer import DatosBancariosSerializer
from api.serializadores.cuota.cuota_serializer import CuotaSerializer

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import Signer

import base64

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    telegram_chat_id = serializers.CharField(read_only=True)
    enlace_vinculacion_telegram = serializers.SerializerMethodField()

    antiguedad_anios = serializers.IntegerField(read_only=True)
    esta_al_corriente = serializers.BooleanField(read_only=True)

    total_papeletas_historicas = serializers.IntegerField(read_only=True)

    datos_bancarios = DatosBancariosSerializer(required=False)

    historial_cuotas = CuotaSerializer(source='cuotas', many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "dni", "nombre", "primer_apellido", "segundo_apellido", 
            "telefono", "fecha_nacimiento", "genero", "estado_civil", 
            "password", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "lugar_bautismo", 
            "fecha_bautismo", "parroquia_bautismo", "areas_interes",
            "email",
            "datos_bancarios", "historial_cuotas", "esta_al_corriente",
            "numero_registro", "estado_hermano", "esAdmin",
            "fecha_ingreso_corporacion", "fecha_baja_corporacion", "antiguedad_anios",
            "telegram_chat_id", "enlace_vinculacion_telegram",
            "total_papeletas_historicas"
        ]

        read_only_fields = [
            "estado_hermano", "numero_registro", "esAdmin", 
            "fecha_ingreso_corporacion", "fecha_baja_corporacion", 
            "antiguedad_anios", "esta_al_corriente", "historial_cuotas", "total_papeletas_historicas"
        ]

        extra_kwargs = {
            "password": {"write_only": True},
            "fecha_nacimiento": {"required": True},
            "direccion": {"required": True},
            "codigo_postal": {"required": True},
            "localidad": {"required": True},
            "provincia": {"required": True},
            "comunidad_autonoma": {"required": True},
            "lugar_bautismo": {"required": True}, 
            "fecha_bautismo": {"required": True},
            "parroquia_bautismo": {"required": True},
            "iban": {"required": True},
            "periodicidad": {"required": True},
            "es_titular": {"required": True},
        }

    def validate(self, data):
        """
        Validación cruzada de campos.
        """
        fecha_nacimiento = data.get('fecha_nacimiento')
        fecha_bautismo = data.get('fecha_bautismo')

        if fecha_nacimiento and fecha_bautismo:
            if fecha_bautismo < fecha_nacimiento:
                raise serializers.ValidationError({
                    "fecha_bautismo": "La fecha de bautismo no puede ser anterior a la fecha de nacimiento."
                })
        return data
    
    def validate_iban(self, value):
        """
        Sanitización del IBAN:
        El usuario puede escribir 'ES00 1234...' con espacios.
        Aquí lo limpiamos antes de que llegue al modelo para que el RegexValidator no falle.
        """
        if value:
            return value.replace(" ", "").upper()
        return value
    

    def get_enlace_vinculacion_telegram(self, obj):
        """
        Genera el enlace Deep Link firmado criptográficamente y 
        codificado en base64 para cumplir con las reglas de Telegram.
        """
        signer = Signer()
        token_seguro = signer.sign(str(obj.id)) 
        
        token_base64 = base64.urlsafe_b64encode(token_seguro.encode()).decode()
        token_limpio = token_base64.rstrip('=') 
        
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'TuBot_bot')
        
        return f"https://t.me/{bot_username}?start={token_limpio}"



class UserUpdateSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    datos_bancarios = DatosBancariosSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "telefono", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "estado_civil", "areas_interes",
            "datos_bancarios", "password", "email"
        ]

        extra_kwargs = {
                'password': {'write_only': True, 'required': False},
            }

    def update(self, instance, validated_data):
        areas_data = validated_data.pop('areas_interes', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)

        instance.save()

        if areas_data is not None:
            instance.areas_interes.set(areas_data)

        return instance