from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import AreaInteres
from django.db import transaction

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = [
            "id", "dni", "nombre", "primer_apellido", "segundo_apellido", 
            "telefono", "fecha_nacimiento", "genero", "estado_civil", 
            "password", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "lugar_bautismo", 
            "fecha_bautismo", "parroquia_bautismo", "areas_interes"
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
        }

    def validate(self, data):
        """
        Validación cruzada de campos.
        Al ser creación, validamos directamente los datos de entrada.
        """
        fecha_nacimiento = data.get('fecha_nacimiento')
        fecha_bautismo = data.get('fecha_bautismo')

        if fecha_nacimiento and fecha_bautismo:
            if fecha_bautismo < fecha_nacimiento:
                raise serializers.ValidationError({
                    "fecha_bautismo": "La fecha de bautismo no puede ser anterior a la fecha de nacimiento."
                })
        return data
    
    def create(self, validated_data):
        areas_data = validated_data.pop('areas_interes', [])
        
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['dni'],
                **validated_data
            )
            
            if areas_data:
                user.areas_interes.set(areas_data)
        
        return user
    
class UserUpdateSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = [
            "telefono", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "estado_civil", "areas_interes"
        ]

    def update(self, instance, validated_data):
        """
        Sobrescribimos update para asegurar una gestión limpia, 
        aunque el update por defecto de DRF suele manejar bien los M2M.
        """
        areas_data = validated_data.pop('areas_interes', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()

        if areas_data is not None:
            instance.areas_interes.set(areas_data)

        return instance
    