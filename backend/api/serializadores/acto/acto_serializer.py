import os

from PIL import Image
from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q

from api.models import Acto, PreferenciaSolicitud, TipoActo
from api.serializadores.puesto.puesto_serializer import PuestoSerializer
from api.serializadores.tramo.tramo_serializer import TramoSerializer


class ActoCultoCardSerializer(serializers.ModelSerializer):
    """
    Serializador súper ligero diseñado específicamente para alimentar 
    el componente CultoCard del dashboard. Evita cargar relaciones anidadas.
    """
    class Meta:
        model = Acto
        fields = ['id', 'nombre', 'fecha', 'lugar']



class ActoSerializer(serializers.ModelSerializer):
    total_insignias = serializers.ReadOnlyField(source='db_total_insignias')
    total_asignados = serializers.ReadOnlyField(source='db_total_asignados')
    total_no_asignados = serializers.ReadOnlyField(source='db_total_no_asignados')
    
    total_solicitantes_cirio = serializers.ReadOnlyField(source='db_total_solicitantes_cirio')
    total_cirios_cristo = serializers.ReadOnlyField(source='db_total_cirios_cristo')
    total_cirios_virgen = serializers.ReadOnlyField(source='db_total_cirios_virgen')
    total_puestos_cirios = serializers.ReadOnlyField(source='db_total_puestos_cirios')
    
    total_solicitantes_insignia = serializers.ReadOnlyField(source='db_total_solicitantes_insignia')
    total_solicitudes_insignias = serializers.ReadOnlyField(source='db_total_solicitudes_insignias')

    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        queryset=TipoActo.objects.all()
    )
    puestos_disponibles = PuestoSerializer(many=True, read_only=True)
    tramos = TramoSerializer(many=True, read_only=True)
    requiere_papeleta = serializers.BooleanField(source='tipo_acto.requiere_papeleta', read_only=True)

    # Estos los dejamos como MethodField porque hacer cuentas con fechas es rápido y no gasta SQL
    en_plazo_insignias = serializers.SerializerMethodField()
    en_plazo_cirios = serializers.SerializerMethodField()
    reparto_ejecutado = serializers.SerializerMethodField()

    class Meta:
        model = Acto
        fields = ['id', 'nombre', 'lugar', 'descripcion', 'fecha', 'tipo_acto', 'modalidad', 'inicio_solicitud', 'fin_solicitud', 'en_plazo_insignias', 'puestos_disponibles', 'tramos', 'inicio_solicitud_cirios', 'fin_solicitud_cirios', 'en_plazo_cirios', 'requiere_papeleta', 'fecha_ejecucion_reparto', 'reparto_ejecutado', 'imagen_portada', 'total_solicitantes_insignia', 'total_solicitudes_insignias', 'total_insignias', 'total_asignados', 'total_no_asignados', 'fecha_ejecucion_cirios', 'total_solicitantes_cirio', 'total_cirios_cristo', 'total_cirios_virgen', 'total_puestos_cirios']
        read_only_fields = ['fecha_ejecucion_reparto', 'reparto_ejecutado']

    def get_en_plazo_insignias(self, obj):
        ahora = timezone.now()
        if obj.inicio_solicitud and obj.fin_solicitud:
            return obj.inicio_solicitud <= ahora <= obj.fin_solicitud
        return False
    
    def get_en_plazo_cirios(self, obj):
        ahora = timezone.now()
        if obj.inicio_solicitud_cirios and obj.fin_solicitud_cirios:
            return obj.inicio_solicitud_cirios <= ahora <= obj.fin_solicitud_cirios
        return False
    
    def get_reparto_ejecutado(self, obj):
        return obj.fecha_ejecucion_reparto is not None



class ActoCreateSerializer(serializers.ModelSerializer):
    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        queryset=TipoActo.objects.all()
    )

    requiere_papeleta = serializers.BooleanField(source='tipo_acto.requiere_papeleta', read_only=True)

    imagen_portada = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Acto
        fields = [
            'id',
            'nombre',
            'lugar',
            'descripcion',
            'fecha',
            'modalidad',
            'tipo_acto',
            'requiere_papeleta',
            'inicio_solicitud',
            'fin_solicitud',
            'inicio_solicitud_cirios',
            'fin_solicitud_cirios',
            'imagen_portada'
        ]

    def validate_imagen_portada(self, value):
        """
        Valida el tamaño, el formato real y las dimensiones del archivo de imagen del acto.
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
    
    def validate_fecha(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("La fecha del acto no puede ser anterior a la actual.")
        return value


class ActoListSerializer(serializers.ModelSerializer):
    requiere_papeleta = serializers.BooleanField(
        source='tipo_acto.requiere_papeleta', 
        read_only=True
    )

    class Meta:
        model = Acto
        fields = [
            'id',
            'nombre', 
            'descripcion', 
            'fecha', 
            'lugar', 
            'requiere_papeleta', 
            'imagen_portada',
            'inicio_solicitud'
        ]