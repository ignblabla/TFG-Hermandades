from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Note

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "dni", "nombre", "primer_apellido", "segundo_apellido", "telefono", "fecha_nacimiento", "genero", "estado_civil", "password", "direccion", "codigo_postal", "localidad", "provincia", "comunidad_autonoma"]
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
            "comunidad_autonoma": {"required": True}
        }

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