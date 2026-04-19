from rest_framework import serializers

from api.models import PreferenciaSolicitud, Puesto


class PreferenciaSolicitudSerializer(serializers.ModelSerializer):
    puesto_id = serializers.PrimaryKeyRelatedField(
        queryset=Puesto.objects.all(), 
        source='puesto_solicitado', 
        write_only=True
    )

    orden_prioridad = serializers.IntegerField() 

    class Meta:
        model = PreferenciaSolicitud
        fields = ['puesto_id', 'orden_prioridad']