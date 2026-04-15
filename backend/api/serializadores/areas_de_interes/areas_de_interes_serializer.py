from rest_framework import serializers
from api.models import AreaInteres


class AreaInteresSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaInteres
        fields = ['id', 'nombre_area', 'get_nombre_area_display', 'telegram_invite_link']