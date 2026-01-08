from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Note

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "dni", "nombre", "primer_apellido", "segundo_apellido", "telefono", "fecha_nacimiento", "genero", "estado_civil", "password", "direccion", "codigo_postal", "localidad", "provincia", "comunidad_autonoma", "lugar_bautismo", "fecha_bautismo", "parroquia_bautismo"]
        extra_kwargs = {
            "password": {"write_only": True},
            "dni": {"required": True},
            "fecha_nacimiento": {"required": True},
            "telefono": {"required": True},
            "genero": {"required": True},
            "estado_civil": {"required": True},
            "direccion": {"required": True},
            "codigo_postal": {"required": True},
            "localidad": {"required": True},
            "provincia": {"required": True},
            "comunidad_autonoma": {"required": True},
            "lugar_bautismo": {"read_only": True},
            "fecha_bautismo": {"read_only": True},
            "parroquia_bautismo": {"read_only": True},
        }

    def validate(self, data):
        fecha_nacimiento = data.get('fecha_nacimiento')
        fecha_bautismo = data.get('fecha_bautismo')

        if self.instance:
            fecha_nacimiento = fecha_nacimiento or self.instance.fecha_nacimiento
            fecha_bautismo = fecha_bautismo or self.instance.fecha_bautismo

        if fecha_nacimiento and fecha_bautismo:
            if fecha_bautismo < fecha_nacimiento:
                raise serializers.ValidationError({
                    "fecha_bautismo": "La fecha de bautismo no puede ser anterior a la fecha de nacimiento."
                })

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['dni'],
            **validated_data
        )
        return user
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["telefono", "direccion", "codigo_postal", "localidad", "provincia", "comunidad_autonoma", "estado_civil"]
    
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}