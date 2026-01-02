from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Note

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "dni", "nombre", "primer_apellido", "segundo_apellido", "password"]
        extra_kwargs = {
            "password": {"write_only": True},
            "dni": {"required": True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['dni'],
            **validated_data
        )
        return user
    
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}