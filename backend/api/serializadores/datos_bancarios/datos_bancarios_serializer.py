from rest_framework import serializers

from api.models import DatosBancarios


class DatosBancariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosBancarios
        fields = ['id', 'iban', 'es_titular', 'titular_cuenta', 'periodicidad']
        extra_kwargs = {
            "iban": {"required": True},
            "periodicidad": {"required": True}
        }

    def validate_iban(self, value):
        """
        Sanitización del IBAN: Eliminar espacios y pasar a mayúsculas
        antes de validar con el Regex del modelo.
        """
        if value:
            return value.replace(" ", "").upper()
        return value