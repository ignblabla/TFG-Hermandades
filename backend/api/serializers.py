from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (AreaInteres, CuerpoPertenencia, HermanoCuerpo, PreferenciaSolicitud, TipoActo, Acto, Puesto, PapeletaSitio, TipoPuesto)
from django.db import transaction
from django.utils import timezone

User = get_user_model()

# -----------------------------------------------------------------------------
# 1. GESTIÓN DE USUARIOS (HERMANOS) Y PERTENENCIAS
# -----------------------------------------------------------------------------

class AreaInteresSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaInteres
        fields = ['id', 'nombre_area']


class CuerpoPertenenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuerpoPertenencia
        fields = ['id', 'nombre_cuerpo']


class HermanoCuerpoSerializer(serializers.ModelSerializer):
    """
    Gestiona la pertenencia de un hermano a un cuerpo (ej. Costaleros, Nazarenos).
    """
    nombre_cuerpo = serializers.CharField(source='cuerpo.get_nombre_cuerpo_display', read_only=True)
    cuerpo_slug = serializers.SlugRelatedField(
        slug_field='nombre_cuerpo',
        queryset=CuerpoPertenencia.objects.all(),
        source='cuerpo',
        write_only=True
    )

    class Meta:
        model = HermanoCuerpo
        fields = ['id', 'hermano', 'cuerpo_slug', 'nombre_cuerpo', 'anio_ingreso']
        extra_kwargs = {
            'hermano': {'read_only': True} 
        }
    
    def validate_anio_ingreso(self, value):
        anio_actual = timezone.now().year
        if value > anio_actual:
            raise serializers.ValidationError("El año de ingreso no puede ser futuro.")
        if value < 1900:
            raise serializers.ValidationError("El año de ingreso no es válido.")
        return value
    

class UserSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    pertenencias_cuerpos = HermanoCuerpoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "dni", "nombre", "primer_apellido", "segundo_apellido", 
            "telefono", "fecha_nacimiento", "genero", "estado_civil", 
            "password", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "lugar_bautismo", 
            "fecha_bautismo", "parroquia_bautismo", "areas_interes",
            "pertenencias_cuerpos", "esAdmin"
        ]

        extra_kwargs = {
            "password": {"write_only": True},
            "fecha_nacimiento": {"required": True},
            "direccion": {"required": True},
            "codigo_postal": {"required": True},
            "localidad": {"required": True},
            "provincia": {"required": True},
            "comunidad_autonoma": {"required": True},
            "lugar_bautismo": {"required": True}, 
            "fecha_bautismo": {"required": True},
            "parroquia_bautismo": {"required": True},
        }

    def validate(self, data):
        """
        Validación cruzada de campos.
        """
        fecha_nacimiento = data.get('fecha_nacimiento')
        fecha_bautismo = data.get('fecha_bautismo')

        if fecha_nacimiento and fecha_bautismo:
            if fecha_bautismo < fecha_nacimiento:
                raise serializers.ValidationError({
                    "fecha_bautismo": "La fecha de bautismo no puede ser anterior a la fecha de nacimiento."
                })
        return data
    
    
    
class UserUpdateSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = [
            "telefono", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "estado_civil", "areas_interes"
        ]

    def update(self, instance, validated_data):
        """
        Sobrescribimos update para asegurar una gestión limpia, 
        aunque el update por defecto de DRF suele manejar bien los M2M.
        """
        areas_data = validated_data.pop('areas_interes', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()

        if areas_data is not None:
            instance.areas_interes.set(areas_data)

        return instance


# -----------------------------------------------------------------------------
# 2. GESTIÓN DE ACTOS Y PUESTOS
# -----------------------------------------------------------------------------

class TipoActoSerializer(serializers.ModelSerializer):
    nombre_mostrar = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = TipoActo
        fields = ['id', 'tipo', 'nombre_mostrar', 'requiere_papeleta']


class TipoPuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPuesto
        fields = ['id', 'nombre_tipo', 'solo_junta_gobierno', 'es_insignia']


class PuestoSerializer(serializers.ModelSerializer):
    tipo_puesto_detalle = TipoPuestoSerializer(source='tipo_puesto', read_only=True)
    tipo_puesto_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoPuesto.objects.all(), source='tipo_puesto', write_only=True
    )

    class Meta:
        model = Puesto
        fields = [
            'id', 'nombre', 'numero_maximo_asignaciones', 
            'disponible', 'lugar_citacion', 'hora_citacion', 'acto',
            'tipo_puesto_id', 'tipo_puesto_detalle'
        ]
        extra_kwargs = {
            'hora_citacion': {'format': '%H:%M'}
        }

    def validate_numero_maximo_asignaciones(self, value):
        if value < 1:
            raise serializers.ValidationError("El número máximo de asignaciones debe ser al menos 1.")
        return value
    

class PuestoUpdateSerializer(PuestoSerializer):
    class Meta(PuestoSerializer.Meta):
        read_only_fields = ['acto']


class ActoSerializer(serializers.ModelSerializer):
    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        queryset=TipoActo.objects.all()
    )

    puestos_disponibles = PuestoSerializer(many=True, read_only=True)
    requiere_papeleta = serializers.BooleanField(source='tipo_acto.requiere_papeleta', read_only=True)

    class Meta:
        model = Acto
        fields = [
            'id', 'nombre', 'descripcion', 'fecha', 'tipo_acto', 
            'inicio_solicitud', 'fin_solicitud', 'puestos_disponibles', 
            'requiere_papeleta'
        ]

# -----------------------------------------------------------------------------
# 3. PROCESO DE SITIO (PAPELETAS Y PREFERENCIAS)
# -----------------------------------------------------------------------------

class PreferenciaSolicitudSerializer(serializers.ModelSerializer):
    """
    Gestiona las líneas de solicitud (ej: 1º Opción: Vara Dorada, 2º Opción: Manigueta).
    """
    nombre_puesto = serializers.CharField(source='puesto_solicitado.nombre', read_only=True)
    
    class Meta:
        model = PreferenciaSolicitud
        fields = ['id', 'papeleta', 'puesto_solicitado', 'nombre_puesto', 'orden_prioridad']
        read_only_fields = ['papeleta']

    def validate(self, data):
        if data['orden_prioridad'] < 1:
            raise serializers.ValidationError("El orden de prioridad debe ser 1 o superior.")
        return data

class PapeletaSitioSerializer(serializers.ModelSerializer):
    """
    Serializer principal para la gestión de Papeletas.
    Se usa tanto para la solicitud (creación) como para la visualización.
    """
    nombre_hermano = serializers.CharField(source='hermano.nombre', read_only=True)
    apellidos_hermano = serializers.SerializerMethodField()
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    
    # Campo para ver el puesto asignado finalmente (puede ser null si está en solicitud)
    nombre_puesto_asignado = serializers.CharField(source='puesto.nombre', read_only=True)
    
    # Nested Serializer para recibir/enviar las preferencias
    preferencias = PreferenciaSolicitudSerializer(many=True, required=False)

    class Meta:
        model = PapeletaSitio
        fields = [
            'id', 'estado_papeleta', 'fecha_emision', 'codigo_verificacion', 
            'anio', 'hermano', 'nombre_hermano', 'apellidos_hermano',
            'acto', 'nombre_acto', 
            'puesto', 'nombre_puesto_asignado', 'numero_papeleta',
            'es_solicitud_insignia', 'preferencias'
        ]
        read_only_fields = ['fecha_emision', 'codigo_verificacion', 'anio', 'numero_papeleta', 'estado_papeleta']
        
        # 'puesto' (asignado) debe ser read_only para el usuario normal, 
        # pero editable para el administrador. Se puede controlar en View/Service.
        # Aquí lo dejamos editable pero validaremos permisos en el Service.

    def get_apellidos_hermano(self, obj):
        return f"{obj.hermano.primer_apellido} {obj.hermano.segundo_apellido}"

    def validate(self, data):
        """
        Validación de integridad de datos.
        """
        puesto_asignado = data.get('puesto') # Puesto FINAL asignado
        acto = data.get('acto')
        hermano = data.get('hermano')
        es_insignia = data.get('es_solicitud_insignia', False)
        preferencias_data = data.get('preferencias', [])

        # 1. Validación de Puesto Asignado (si existe)
        if puesto_asignado:
            if puesto_asignado.acto != acto:
                raise serializers.ValidationError({
                    "puesto": "El puesto asignado no pertenece al acto indicado."
                })

            if not puesto_asignado.disponible:
                raise serializers.ValidationError({
                    "puesto": "El puesto seleccionado no está marcado como disponible."
                })
            
            # Validación de Junta de Gobierno
            if puesto_asignado.tipo_puesto.solo_junta_gobierno:
                es_miembro_junta = hermano.pertenencias_cuerpos.filter(
                    cuerpo__nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
                ).exists()

                if not es_miembro_junta:
                    raise serializers.ValidationError({
                        "puesto": f"El puesto '{puesto_asignado.nombre}' está reservado para Junta de Gobierno."
                    })

        # 2. Validación cruzada: Si es solicitud de insignia, debe tener preferencias
        # (Opcional, depende de tu regla de negocio)
        if es_insignia and self.instance is None: # Solo al crear
            # Si no hay preferencias en el payload, y marca insignia, warning.
            # Pero como las preferencias van nested, a veces se validan post-save en el service.
            pass

        return data
    
    def create(self, validated_data):
        """
        Sobrescribimos create para soportar la creación de Preferencias anidadas
        si decidimos no usar un Servicio para esto (aunque recomiendo usar Service).
        """
        preferencias_data = validated_data.pop('preferencias', [])
        papeleta = PapeletaSitio.objects.create(**validated_data)
        
        for pref_data in preferencias_data:
            PreferenciaSolicitud.objects.create(papeleta=papeleta, **pref_data)
            
        return papeleta