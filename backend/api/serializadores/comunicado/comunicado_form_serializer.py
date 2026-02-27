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
        """
        Valida y sanea el campo 'titulo' del comunicado.

        Aplica una limpieza de espacios en blanco al inicio y al final de la cadena,
        y verifica que el resultado cumpla con los requisitos mínimos de longitud
        para garantizar un título con contenido significativo.

        Args:
            value (str): El valor original del título enviado en la petición HTTP.

        Returns:
            str: El título saneado (sin espacios periféricos) y validado.

        Raises:
            serializers.ValidationError: Si la cadena resultante está completamente vacía,
                                        formada solo por espacios, o si tiene una longitud 
                                        inferior a 5 caracteres.
        """
        clean_value = value.strip()
        if not clean_value:
            raise serializers.ValidationError("El título no puede estar formado solo por espacios en blanco.")
        if len(clean_value) < 5:
            raise serializers.ValidationError("El título es demasiado corto. Debe tener al menos 5 caracteres.")
        return clean_value


    def validate_contenido(self, value):
        """
        Valida y sanea el campo 'contenido' del comunicado.

        Aplica una limpieza de espacios en blanco al inicio y al final del texto
        para asegurar que el cuerpo del mensaje tenga sustancia real y no esté 
        compuesto únicamente por caracteres en blanco o retornos de carro.

        Args:
            value (str): El texto original del contenido enviado en la petición HTTP.

        Returns:
            str: El contenido saneado, listo para ser almacenado en la base de datos.

        Raises:
            serializers.ValidationError: Si, tras la limpieza, la cadena de texto 
                                        resultante está completamente vacía.
        """
        clean_value = value.strip()
        if not clean_value:
            raise serializers.ValidationError("El contenido no puede estar vacío.")
        return clean_value


    def validate_imagen_portada(self, value):
        """
        Valida el tamaño y el formato del archivo de imagen subido como portada.

        Garantiza que el archivo cumpla con los límites de peso del servidor y con 
        los requisitos de compatibilidad multimedia de la API de Telegram para el envío 
        de notificaciones con adjuntos.

        Reglas aplicadas:
            - Límite máximo de tamaño: 5 MB.
            - Formatos permitidos: .jpg, .jpeg, .png.

        Args:
            value (django.core.files.uploadedfile.UploadedFile o None): El archivo 
                    de imagen recibido en la petición HTTP. Puede ser None si el campo es opcional.

        Returns:
            django.core.files.uploadedfile.UploadedFile o None: El mismo archivo original, 
                    inalterado, en caso de superar todas las validaciones exitosamente.

        Raises:
            serializers.ValidationError: Si el archivo supera el tamaño máximo permitido
                                        o si la extensión no está dentro de la lista blanca.
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
        Valida que el comunicado tenga asignado al menos un público objetivo.

        Esta regla de negocio es indispensable para evitar que el comunicado 
        quede "huérfano" en la base de datos. Garantiza que el motor de notificaciones 
        sepa a qué canales de Telegram enviar la alerta y en qué secciones del 
        feed de la aplicación debe mostrarse el contenido.

        Args:
            value (list): Lista de instancias de `AreaInteres` (resueltas por DRF 
                            a partir de los IDs enviados en la petición HTTP).

        Returns:
            list: La misma lista de áreas de interés, inalterada tras superar la validación.

        Raises:
            serializers.ValidationError: Si la lista de áreas proporcionada está vacía 
                                        o es nula, instruyendo al usuario a utilizar 
                                        la opción genérica ('Todos los Hermanos') si procede.
        """
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "Debe seleccionar al menos un área de interés. Si es para todos, elija 'Todos los Hermanos'."
            )
        return value