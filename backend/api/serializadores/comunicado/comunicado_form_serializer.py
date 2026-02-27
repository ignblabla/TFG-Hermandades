import os
from rest_framework import serializers
from api.models import AreaInteres, Comunicado


class ComunicadoFormSerializer(serializers.ModelSerializer):
    """
    Serializador de entrada que valida y sanea los datos recibidos para crear o editar comunicados.

    Actúa como filtro de seguridad y reglas de negocio sobre el payload de la petición HTTP. 
    Espera identificadores (IDs) para las relaciones y garantiza que los datos y archivos 
    multimedia cumplan con los requisitos técnicos de la aplicación y de servicios externos (Telegram).

    Validaciones principales aplicadas:
        - Textos (título/contenido): Limpieza de espacios y validación de longitud mínima.
        - Archivos (imagen_portada): Límite de tamaño (5MB) y formatos específicos (JPG/PNG).
        - Relaciones (areas_interes): Obligatoriedad de seleccionar al menos un destinatario.
    """
    areas_interes = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=AreaInteres.objects.all(),
        required=False,
        label="IDs de Áreas de Interés"
    )


    class Meta:
        model = Comunicado
        fields = [
            'id', 'titulo', 'contenido', 'imagen_portada',
            'tipo_comunicacion', 'areas_interes'
        ]


    def validate_titulo(self, value):
        """Asegura que el título no esté vacío y quita espacios extra."""
        clean_value = value.strip()
        if not clean_value:
            raise serializers.ValidationError("El título no puede estar formado solo por espacios en blanco.")
        if len(clean_value) < 5:
            raise serializers.ValidationError("El título es demasiado corto. Debe tener al menos 5 caracteres.")
        return clean_value


    def validate_contenido(self, value):
        """Asegura que el contenido tenga sustancia."""
        clean_value = value.strip()
        if not clean_value:
            raise serializers.ValidationError("El contenido no puede estar vacío.")
        return clean_value


    def validate_imagen_portada(self, value):
        """
        Valida tamaño y formato de la imagen para asegurar compatibilidad 
        con el servidor y la API de Telegram.
        """
        if value:
            max_size_mb = 5
            if value.size > (max_size_mb * 1024 * 1024):
                raise serializers.ValidationError(f"La imagen es demasiado grande. El máximo permitido es de {max_size_mb}MB.")


            extension = os.path.splitext(value.name)[1].lower()
            extensiones_permitidas = ['.jpg', '.jpeg', '.png']
            
            if extension not in extensiones_permitidas:
                raise serializers.ValidationError(
                    f"Formato de archivo no permitido ({extension}). "
                    "Solo se admiten imágenes JPG, JPEG o PNG para asegurar el envío a Telegram."
                )
        return value


    def validate_areas_interes(self, value):
        """
        Asegura que el comunicado tenga al menos un destino para garantizar
        la difusión por Telegram y visibilidad en el feed.
        """
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "Debe seleccionar al menos un área de interés. Si es para todos, elija 'Todos los Hermanos'."
            )
        return value