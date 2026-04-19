from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q

from api.models import Acto, PreferenciaSolicitud, TipoActo
from api.serializers import TramoSerializer
from api.serializadores.puesto.puesto_serializer import PuestoSerializer


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