import os
import bleach
from PIL import Image
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
        required=True,
        label="IDs de Áreas de Interés"
    )

    titulo = serializers.CharField(trim_whitespace=False, allow_blank=True)
    contenido = serializers.CharField(trim_whitespace=False, allow_blank=True)
    imagen_portada = serializers.FileField(required=False, allow_null=True)

    generar_podcast = serializers.BooleanField(required=False, default=False, label="Generar Podcast")


    class Meta:
        model = Comunicado
        fields = [
            'id', 'titulo', 'contenido', 'imagen_portada',
            'tipo_comunicacion', 'areas_interes', 'generar_podcast'
        ]

        extra_kwargs = {
            'id': {'read_only': True},
        }


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

        Aplica una doble capa de seguridad:
        1. Filtro estricto (Blacklist): Detecta y rechaza intentos evidentes de XSS.
        2. Saneamiento (Allowlist): Utiliza Bleach para limpiar el HTML entrante.

        Args:
            value (str): El texto original del contenido enviado en la petición HTTP.

        Returns:
            str: El contenido HTML saneado, seguro para renderizar y almacenar.

        Raises:
            serializers.ValidationError: Si está vacío o contiene código malicioso.
        """
        clean_value = value.strip()
        
        if not clean_value:
            raise serializers.ValidationError("El contenido no puede estar vacío.")

        etiquetas_prohibidas = ['<script', '<iframe', '<object', '<embed', '<style', 'onload=', 'onerror=']
        value_lower = clean_value.lower()
        if any(prohibida in value_lower for prohibida in etiquetas_prohibidas):
            raise serializers.ValidationError(
                "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
            )

        etiquetas_permitidas = [
            'p', 'b', 'i', 'u', 'em', 'strong', 
            'a', 'ul', 'ol', 'li', 'br', 'h1', 'h2', 'h3'
        ]

        atributos_permitidas = {
            'a': ['href', 'title', 'target'],
        }

        clean_value = bleach.clean(
            clean_value,
            tags=etiquetas_permitidas,
            attributes=atributos_permitidas,
            strip=True
        )

        if not clean_value.strip():
            raise serializers.ValidationError(
                "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
            )

        return clean_value


    def validate_imagen_portada(self, value):
        """
        Valida el tamaño, el formato real y las dimensiones del archivo de imagen.

        Garantiza que el archivo no solo cumpla con los límites de peso y extensión,
        sino que su contenido binario sea genuinamente una imagen válida (previniendo 
        archivos maliciosos renombrados) y que sus dimensiones sean razonables para
        su procesamiento y envío por Telegram.

        Args:
            value (django.core.files.uploadedfile.UploadedFile o None): El archivo.

        Returns:
            django.core.files.uploadedfile.UploadedFile o None: El archivo validado.

        Raises:
            serializers.ValidationError: Si falla cualquier control de seguridad o tamaño.
        """
        if not value:
            return value

        max_size_mb = 5
        if value.size > (max_size_mb * 1024 * 1024):
            raise serializers.ValidationError(
                f"La imagen es demasiado grande. El máximo permitido es de {max_size_mb}MB."
            )

        extension = os.path.splitext(value.name)[1].lower()
        extensiones_permitidas = ['.jpg', '.jpeg', '.png']
        
        if extension not in extensiones_permitidas:
            raise serializers.ValidationError(
                f"Formato de archivo no permitido ({extension}). "
                "Solo se admiten imágenes JPG, JPEG o PNG."
            )

        try:
            value.seek(0)

            img = Image.open(value)

            formato_real = img.format.lower()
            if formato_real not in ['jpeg', 'png']:
                raise serializers.ValidationError(
                    "El archivo parece tener una extensión falsa o está corrupto. "
                    "Asegúrese de subir una imagen real."
                )

            max_width, max_height = 4000, 4000
            if img.width > max_width or img.height > max_height:
                raise serializers.ValidationError(
                    f"Las dimensiones de la imagen son demasiado grandes ({img.width}x{img.height}). "
                    f"El máximo permitido es {max_width}x{max_height} píxeles."
                )

        except Exception as e:
            if isinstance(e, serializers.ValidationError):
                raise e
            raise serializers.ValidationError("El archivo subido no es una imagen válida o está dañado.")
            
        finally:
            value.seek(0)

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


    def to_internal_value(self, data):
        """
        Valida la integridad del esquema y transforma los datos de entrada.

        Actúa como un guardián de esquema estricto al interceptar el payload 
        antes del procesamiento de campos. Sobrescribe el comportamiento por 
        defecto de DRF para prohibir explícitamente el envío de parámetros 
        no definidos en el serializador, mitigando riesgos de 'Mass Assignment' 
        y garantizando la predictibilidad del contrato de la API.

        Args:
            data (dict): Diccionario de datos brutos provenientes de la petición (JSON/Multipart).

        Returns:
            dict: Diccionario de datos saneados listos para las validaciones de campo específicas.

        Raises:
            serializers.ValidationError: Si se detectan claves en el payload que no 
                                        están permitidas en la definición del serializador.
        """
        campos_permitidos = set(self.fields.keys())

        campos_recibidos = set(data.keys())

        campos_extra = campos_recibidos - campos_permitidos
        
        if campos_extra:
            raise serializers.ValidationError({
                "error": f"Campos no permitidos detectados: {', '.join(campos_extra)}. "
                        "La API opera en modo estricto y no acepta datos fuera de esquema."
            })
            
        return super().to_internal_value(data)