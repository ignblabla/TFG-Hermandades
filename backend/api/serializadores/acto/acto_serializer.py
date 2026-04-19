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
    total_insignias = serializers.SerializerMethodField()
    total_asignados = serializers.SerializerMethodField()
    total_no_asignados = serializers.SerializerMethodField()

    total_solicitantes_cirio = serializers.SerializerMethodField()
    total_cirios_cristo = serializers.SerializerMethodField()
    total_cirios_virgen = serializers.SerializerMethodField()

    total_puestos_cirios = serializers.SerializerMethodField()

    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        queryset=TipoActo.objects.all()
    )
    puestos_disponibles = PuestoSerializer(many=True, read_only=True)

    tramos = TramoSerializer(many=True, read_only=True)

    requiere_papeleta = serializers.BooleanField(source='tipo_acto.requiere_papeleta', read_only=True)

    en_plazo_insignias = serializers.SerializerMethodField()
    en_plazo_cirios = serializers.SerializerMethodField()

    reparto_ejecutado = serializers.SerializerMethodField()

    total_solicitantes_insignia = serializers.SerializerMethodField()
    total_solicitudes_insignias = serializers.SerializerMethodField()

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
    
    def get_total_solicitantes_insignia(self, obj):
        estados_inactivos = ['ANULADA']

        return obj.papeletas.filter(
            es_solicitud_insignia=True
        ).exclude(
            estado_papeleta__in=estados_inactivos
        ).count()
    
    def get_total_solicitudes_insignias(self, obj):
        estados_validos = ['SOLICITADA', 'EMITIDA', 'RECOGIDA', 'LEIDA', 'NO_ASIGNADA']

        total = PreferenciaSolicitud.objects.filter(
            papeleta__acto_id=obj.id,
            papeleta__estado_papeleta__in=estados_validos,
            papeleta__es_solicitud_insignia=True
        ).count()

        return total

    def get_total_insignias(self, obj):
        """Calcula el cupo máximo de insignias para este acto"""
        puestos = obj.puestos_disponibles.filter(tipo_puesto__es_insignia=True)
        return sum(p.numero_maximo_asignaciones for p in puestos)

    def get_total_asignados(self, obj):
        if not obj.fecha_ejecucion_reparto:
            return None
            
        estados_inactivos = ['ANULADA', 'NO_ASIGNADA']
        
        return obj.papeletas.filter(
            es_solicitud_insignia=True, 
            puesto__isnull=False
        ).exclude(
            estado_papeleta__in=estados_inactivos
        ).count()

    def get_total_no_asignados(self, obj):
        if not obj.fecha_ejecucion_reparto:
            return None
            
        total = self.get_total_insignias(obj)
        asignados = self.get_total_asignados(obj)
        return max(0, total - asignados)
    
    def get_total_solicitantes_cirio(self, obj):
        estados_inactivos = ['ANULADA']
        return obj.papeletas.filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True)
        ).exclude(
            estado_papeleta__in=estados_inactivos
        ).count()

    def get_total_cirios_cristo(self, obj):
        estados_inactivos = ['ANULADA']
        return obj.papeletas.filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True),
            puesto__isnull=False,
            puesto__cortejo_cristo=True,
            puesto__tipo_puesto__es_insignia=False
        ).exclude(
            estado_papeleta__in=estados_inactivos
        ).count()

    def get_total_cirios_virgen(self, obj):
        estados_inactivos = ['ANULADA']
        return obj.papeletas.filter(
            Q(es_solicitud_insignia=False) | Q(es_solicitud_insignia__isnull=True),
            puesto__isnull=False,
            puesto__cortejo_cristo=False,
            puesto__tipo_puesto__es_insignia=False
        ).exclude(
            estado_papeleta__in=estados_inactivos
        ).count()

    def get_total_puestos_cirios(self, obj):
        """Cuenta el número de registros de Puesto que NO son insignias"""
        return obj.puestos_disponibles.filter(tipo_puesto__es_insignia=False).count()



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