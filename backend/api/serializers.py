from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (AreaInteres, CuerpoPertenencia, Cuota, DatosBancarios, HermanoCuerpo, TipoActo, Acto, Puesto, PapeletaSitio, TipoPuesto)
from django.db import transaction

User = get_user_model()

# -----------------------------------------------------------------------------
# SERIALIZERS FINANCIEROS (NUEVOS)
# -----------------------------------------------------------------------------

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
    

class CuotaSerializer(serializers.ModelSerializer):
    """
    Historial de pagos. Generalmente es de solo lectura desde la API de perfil,
    ya que los pagos se generan por procesos (Service) o pasarelas.
    """
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Cuota
        fields = [
            'id', 'anio', 'tipo', 'tipo_display', 'descripcion', 
            'importe', 'estado', 'estado_display', 
            'fecha_emision', 'fecha_pago', 'metodo_pago'
        ]
        read_only_fields = fields


# -----------------------------------------------------------------------------
# SERIALIZERS DE USUARIO (HERMANO) - ACTUALIZADO
# -----------------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    antiguedad_anios = serializers.IntegerField(read_only=True)
    esta_al_corriente = serializers.BooleanField(read_only=True)

    datos_bancarios = DatosBancariosSerializer(required=False)

    historial_cuotas = CuotaSerializer(source='cuotas', many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "dni", "nombre", "primer_apellido", "segundo_apellido", 
            "telefono", "fecha_nacimiento", "genero", "estado_civil", 
            "password", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "lugar_bautismo", 
            "fecha_bautismo", "parroquia_bautismo", "areas_interes",
            # Nuevos campos anidados:
            "datos_bancarios", "historial_cuotas", "esta_al_corriente",
            # Campos de gestión:
            "numero_registro", "estado_hermano", "esAdmin",
            "fecha_ingreso_corporacion", "fecha_baja_corporacion", "antiguedad_anios"
        ]

        read_only_fields = [
            "estado_hermano", "numero_registro", "esAdmin", 
            "fecha_ingreso_corporacion", "fecha_baja_corporacion", 
            "antiguedad_anios", "esta_al_corriente", "historial_cuotas"
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
            "iban": {"required": True},
            "periodicidad": {"required": True},
            "es_titular": {"required": True},
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
    
    def validate_iban(self, value):
        """
        Sanitización del IBAN:
        El usuario puede escribir 'ES00 1234...' con espacios.
        Aquí lo limpiamos antes de que llegue al modelo para que el RegexValidator no falle.
        """
        if value:
            return value.replace(" ", "").upper()
        return value
    
    
class UserUpdateSerializer(serializers.ModelSerializer):
    areas_interes = serializers.SlugRelatedField(
        many=True,
        slug_field='nombre_area',
        queryset=AreaInteres.objects.all(),
        required=False
    )

    datos_bancarios = DatosBancariosSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "telefono", "direccion", "codigo_postal", "localidad", 
            "provincia", "comunidad_autonoma", "estado_civil", "areas_interes",
            "datos_bancarios"
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


class HermanoManagementSerializer(UserSerializer):
    """
    NUEVO: Serializador exclusivo para el rol ADMIN/SECRETARIA.
    Hereda de UserSerializer pero desbloquea los campos administrativos.
    Usar este serializador solo en vistas protegidas con IsAdminUser.
    """
    class Meta(UserSerializer.Meta):
        read_only_fields = ["antiguedad_anios"]


class AreaInteresSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaInteres
        fields = ['id', 'nombre_area']

class CuerpoPertenenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuerpoPertenencia
        fields = ['id', 'nombre_cuerpo']

class TipoActoSerializer(serializers.ModelSerializer):
    nombre_mostrar = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = TipoActo
        fields = ['id', 'tipo', 'nombre_mostrar', 'requiere_papeleta']


# -----------------------------------------------------------------------------
# SERIALIZERS DE RELACIONES (HERMANO - CUERPO)
# -----------------------------------------------------------------------------

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
        from django.utils import timezone
        anio_actual = timezone.now().year
        if value > anio_actual:
            raise serializers.ValidationError("El año de ingreso no puede ser futuro.")
        if value < 1900:
            raise serializers.ValidationError("El año de ingreso no es válido.")
        return value
    
# -----------------------------------------------------------------------------
# SERIALIZERS DE GESTIÓN DE ACTOS Y PUESTOS
# -----------------------------------------------------------------------------

class TipoPuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPuesto
        fields = ['id', 'nombre_tipo', 'solo_junta_gobierno']

class PuestoSerializer(serializers.ModelSerializer):
    tipo_puesto = serializers.SlugRelatedField(
        slug_field='nombre_tipo',
        queryset=TipoPuesto.objects.all()
    )

    class Meta:
        model = Puesto
        fields = [
            'id', 'nombre', 'numero_maximo_asignaciones', 
            'disponible', 'lugar_citacion', 'hora_citacion', 'acto',
            'tipo_puesto'
        ]

        extra_kwargs = {
            'hora_citacion': {
                'error_messages': {
                    'invalid': 'El formato de hora es incorrecto. Por favor, use el formato HH:MM (ej. 20:30).'
                }
            }
        }

    def validate_numero_maximo_asignaciones(self, value):
        """
        Validación de campo: El número de asignaciones debe ser positivo.
        """
        if value < 1:
            raise serializers.ValidationError("El número máximo de asignaciones debe ser al menos 1.")
        return value
    

class PuestoUpdateSerializer(PuestoSerializer):
    """
    Serializador específico para actualizaciones.
    Hereda de PuestoSerializer para no repetir campos, pero
    marca 'acto' como read_only para asegurar que no se modifica.
    """
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
        fields = ['id', 'nombre', 'descripcion', 'fecha', 'tipo_acto', 'inicio_solicitud', 'fin_solicitud', 'puestos_disponibles', 'requiere_papeleta']


# -----------------------------------------------------------------------------
# SERIALIZER TRANSACCIONAL: PAPELETA DE SITIO
# -----------------------------------------------------------------------------

class PapeletaSitioSerializer(serializers.ModelSerializer):
    """
    Este es un serializer crítico. Aquí validamos la integridad de la solicitud
    antes de que pase a la capa de servicio.
    """
    nombre_hermano = serializers.CharField(source='hermano.nombre', read_only=True)
    apellidos_hermano = serializers.SerializerMethodField()
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    nombre_puesto = serializers.CharField(source='puesto.nombre', read_only=True)

    class Meta:
        model = PapeletaSitio
        fields = [
            'id', 'estado_papeleta', 'fecha_emision', 'codigo_verificacion', 
            'anio', 'hermano', 'nombre_hermano', 'apellidos_hermano',
            'acto', 'nombre_acto', 
            'puesto', 'nombre_puesto'
        ]
        read_only_fields = ['fecha_emision', 'codigo_verificacion', 'anio']

    def get_apellidos_hermano(self, obj):
        return f"{obj.hermano.primer_apellido} {obj.hermano.segundo_apellido}"

    def validate(self, data):
        """
        Validación de integridad de datos (Data Integrity).
        La lógica de negocio compleja (ej. cálculo de antigüedad) va al Service,
        pero la coherencia básica de los datos va aquí.
        """
        puesto = data.get('puesto')
        acto = data.get('acto')
        hermano = data.get('hermano')
        
        if puesto and acto:
            if puesto.acto != acto:
                raise serializers.ValidationError({
                    "puesto": "El puesto seleccionado no pertenece al acto indicado."
                })

        if puesto and not puesto.disponible:
            raise serializers.ValidationError({
                "puesto": "El puesto seleccionado no está marcado como disponible."
            })
        
        if puesto and puesto.tipo_puesto.solo_junta_gobierno:
            # Comprobamos si el hermano pertenece al cuerpo 'JUNTA_GOBIERNO'
            # Usamos el related_name 'pertenencias_cuerpos' definido en HermanoCuerpo
            es_miembro_junta = hermano.pertenencias_cuerpos.filter(
                cuerpo__nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()

            if not es_miembro_junta:
                raise serializers.ValidationError({
                    "puesto": f"El puesto '{puesto.nombre}' ({puesto.tipo_puesto.nombre_tipo}) está reservado exclusivamente para miembros de la Junta de Gobierno."
                })

        return data