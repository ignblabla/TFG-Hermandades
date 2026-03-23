from rest_framework import serializers
from api.models import Acto, PapeletaSitio, Puesto
from django.utils import timezone
from api.serializers import PuestoSerializer


class PuestoInsigniaResumenSerializer(serializers.ModelSerializer):
    """
    Serializador ultra-ligero para listar las insignias a solicitar.
    """
    tipo_puesto = serializers.SlugRelatedField(
        slug_field='nombre_tipo',
        read_only=True
    )
    
    es_insignia = serializers.BooleanField(
        source='tipo_puesto.es_insignia', 
        read_only=True
    )

    class Meta:
        model = Puesto
        fields = [
            'id', 
            'nombre', 
            'disponible', 
            'acto', 
            'es_insignia', 
            'cortejo_cristo', 
            'tipo_puesto'
        ]


class ActoInsigniaResumenSerializer(serializers.ModelSerializer):
    """
    Serializador ligero optimizado para la pantalla de solicitud de insignias.
    """
    en_plazo_insignias = serializers.SerializerMethodField()
    puestos_disponibles = serializers.SerializerMethodField()

    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        read_only=True
    )
    requiere_papeleta = serializers.BooleanField(
        source='tipo_acto.requiere_papeleta', 
        read_only=True
    )

    class Meta:
        model = Acto
        fields = [
            'id', 
            'nombre',
            'fecha',
            'descripcion',
            'tipo_acto',
            'modalidad',
            'requiere_papeleta',
            'inicio_solicitud', 
            'fin_solicitud',    
            'en_plazo_insignias', 
            'puestos_disponibles'
        ]

    def get_en_plazo_insignias(self, obj):
        ahora = timezone.now()
        if obj.inicio_solicitud and obj.fin_solicitud:
            return obj.inicio_solicitud <= ahora <= obj.fin_solicitud
        return False
        
    def get_puestos_disponibles(self, obj):
        puestos = obj.puestos_disponibles.filter(
            disponible=True, 
            tipo_puesto__es_insignia=True
        )
        return PuestoInsigniaResumenSerializer(puestos, many=True).data


class PreferenciaInputSerializer(serializers.Serializer):
    """
    Serializador auxiliar solo para recibir los datos de entrada de las preferencias.
    Al usar PrimaryKeyRelatedField, Django convierte automáticamente el ID 
    que envía React en el objeto Puesto real.
    """
    puesto_solicitado = serializers.PrimaryKeyRelatedField(queryset=Puesto.objects.all())
    orden_prioridad = serializers.IntegerField(min_value=1)


class SolicitudInsigniaSerializer(serializers.ModelSerializer):
    """
    Serializador Transaccional: Recibe la intención de sacar papeleta y
    una lista de preferencias de puestos/insignias.
    """
    preferencias = PreferenciaInputSerializer(many=True, write_only=True)
    
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    
    acto_id = serializers.PrimaryKeyRelatedField(
        queryset=Acto.objects.all(), 
        source='acto', 
        write_only=True
    )

    class Meta:
        model = PapeletaSitio
        fields = [
            'id', 'acto_id', 'fecha_solicitud', 'nombre_acto', 'anio', 
            'fecha_emision', 'estado_papeleta', 'es_solicitud_insignia',
            'preferencias'
        ]
        read_only_fields = ['id', 'anio', 'fecha_emision', 'estado_papeleta', 'fecha_solicitud', 'es_solicitud_insignia']

    def validate_preferencias(self, value):
        """
        Validaciones de lógica de negocio sobre la lista de preferencias.
        """
        if not value:
            raise serializers.ValidationError("Debe indicar al menos una preferencia de sitio.")

        puestos_vistos = set()
        ordenes_vistos = []

        for item in value:
            puesto = item['puesto_solicitado'] 
            orden = item['orden_prioridad']

            if not getattr(puesto.tipo_puesto, 'es_insignia', False):
                raise serializers.ValidationError(
                    f"El puesto '{puesto.nombre}' no es una insignia válida."
                )

            if puesto.id in puestos_vistos:
                raise serializers.ValidationError(f"El puesto '{puesto.nombre}' está repetido.")
            puestos_vistos.add(puesto.id)
            
            ordenes_vistos.append(orden)

        ordenes_vistos.sort()
        expected_sequence = list(range(1, len(ordenes_vistos) + 1))
        if ordenes_vistos != expected_sequence:
            raise serializers.ValidationError("El orden de prioridad debe ser consecutivo (1, 2, 3...).")

        return value

    def validate(self, data):
        """
        Validación cruzada: Asegurar que los puestos pertenecen al Acto seleccionado.
        """
        acto = data.get('acto')
        preferencias = data.get('preferencias')

        if acto and preferencias:
            for item in preferencias:
                puesto = item['puesto_solicitado']
                
                if getattr(puesto, 'acto_id', None) != acto.id:
                    raise serializers.ValidationError({
                        "preferencias": f"El puesto '{puesto.nombre}' no pertenece al acto '{acto.nombre}'."
                    })
            
        return data