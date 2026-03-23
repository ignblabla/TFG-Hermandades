from rest_framework import serializers

class FilaTablaInsigniaSerializer(serializers.Serializer):
    dni = serializers.CharField(max_length=9)
    estado = serializers.CharField(max_length=50)
    fecha_solicitud = serializers.DateTimeField(format="%d/%m/%Y %H:%M", allow_null=True)
    acto = serializers.CharField(max_length=100)
    es_solicitud_insignia = serializers.BooleanField()
    preferencia = serializers.CharField(max_length=200)