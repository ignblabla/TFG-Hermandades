import os

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.serializadores.datos_bancarios.datos_bancarios_serializer import DatosBancariosSerializer
from api.serializadores.cuota.cuota_serializer import CuotaSerializer
from .models import (AreaInteres, CuerpoPertenencia, HermanoCuerpo, PreferenciaSolicitud, TipoActo, Acto, Puesto, PapeletaSitio, TipoPuesto, Tramo)
from django.core.signing import Signer
import base64

User = get_user_model()

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
        fields = ['id', 'nombre_tipo', 'solo_junta_gobierno', 'es_insignia']

class PuestoSerializer(serializers.ModelSerializer):
    tipo_puesto = serializers.SlugRelatedField(
        slug_field='nombre_tipo',
        queryset=TipoPuesto.objects.all()
    )

    es_insignia = serializers.BooleanField(source='tipo_puesto.es_insignia', read_only=True)

    class Meta:
        model = Puesto
        fields = [
            'id', 'nombre', 'numero_maximo_asignaciones', 
            'disponible', 'lugar_citacion', 'hora_citacion', 'acto',
            'tipo_puesto', 'es_insignia', 'cortejo_cristo', 'cantidad_ocupada', 'plazas_disponibles', 'porcentaje_ocupacion'
        ]
        
        read_only_fields = ['cantidad_ocupada', 'plazas_disponibles', 'porcentaje_ocupacion']

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
        read_only_fields = ['acto', 'cantidad_ocupada', 'plazas_disponibles', 'porcentaje_ocupacion']


class TramoSerializer(serializers.ModelSerializer):
    """
    Serializa la estructura de un tramo dentro de la cofradía.
    """
    paso_display = serializers.CharField(source='get_paso_display', read_only=True)
    
    class Meta:
        model = Tramo
        fields = ['id', 'nombre', 'numero_orden', 'paso', 'paso_display', 'acto', 'numero_maximo_cirios']

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

    tramo_display = serializers.CharField(source='tramo.__str__', read_only=True)
    nombre_vinculado = serializers.SerializerMethodField()

    lado_display = serializers.CharField(source='get_lado_display', read_only=True)
    
    tramo_id = serializers.PrimaryKeyRelatedField(
        queryset=Tramo.objects.all(), 
        source='tramo', 
        write_only=True, 
        required=False,
        allow_null=True
    )

    class Meta:
        model = PapeletaSitio
        fields = [
            'id', 'estado_papeleta', 'es_solicitud_insignia',
            'fecha_solicitud', 'fecha_emision', 'codigo_verificacion', 
            'anio', 'hermano', 'nombre_hermano', 'apellidos_hermano',
            'acto', 'nombre_acto', 
            'puesto', 'nombre_puesto', 'tramo_display', 'tramo_id',
            'vinculado_a', 'nombre_vinculado',
            'orden_en_tramo', 
            'lado', 
            'lado_display'
        ]
        read_only_fields = ['fecha_emision', 'codigo_verificacion', 'anio', 'tramo_display', 'nombre_vinculado', 'orden_en_tramo', 'lado', 'lado_display']

    def get_apellidos_hermano(self, obj):
        return f"{obj.hermano.primer_apellido} {obj.hermano.segundo_apellido}"
    
    def get_nombre_vinculado(self, obj):
        if obj.vinculado_a:
            return f"{obj.vinculado_a.nombre} {obj.vinculado_a.primer_apellido} {obj.vinculado_a.segundo_apellido} (Nº {obj.vinculado_a.numero_registro})"
        return None

    def validate(self, data):
        """
        Validación de integridad de datos (Data Integrity).
        La lógica de negocio compleja (ej. cálculo de antigüedad) va al Service,
        pero la coherencia básica de los datos va aquí.
        """
        puesto = data.get('puesto')
        acto = data.get('acto')
        hermano = data.get('hermano')
        tramo = data.get('tramo')
        
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
            es_miembro_junta = hermano.pertenencias_cuerpos.filter(
                cuerpo__nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()

            if not es_miembro_junta:
                raise serializers.ValidationError({
                    "puesto": f"El puesto '{puesto.nombre}' ({puesto.tipo_puesto.nombre_tipo}) está reservado exclusivamente para miembros de la Junta de Gobierno."
                })
            
        if tramo and acto:
            if tramo.acto != acto:
                raise serializers.ValidationError({
                    "tramo_id": f"El tramo {tramo} no pertenece al acto {acto.nombre}."
                })

        return data
    
# -----------------------------------------------------------------------------
# SERIALIZERS PARA SOLICITUD DE INSIGNIAS Y PAPELETAS
# -----------------------------------------------------------------------------

class PreferenciaSolicitudSerializer(serializers.ModelSerializer):
    puesto_id = serializers.PrimaryKeyRelatedField(
        queryset=Puesto.objects.all(), 
        source='puesto_solicitado', 
        write_only=True
    )

    orden_prioridad = serializers.IntegerField() 

    class Meta:
        model = PreferenciaSolicitud
        fields = ['puesto_id', 'orden_prioridad']


class SolicitudCirioSerializer(serializers.Serializer):
    acto = serializers.PrimaryKeyRelatedField(
        queryset = Acto.objects.all(),
        write_only=True,
        required=True
    )

    puesto = serializers.PrimaryKeyRelatedField(
        queryset=Puesto.objects.filter(disponible=True),
        write_only=True,
        required=True
    )

    id_papeleta = serializers.IntegerField(read_only=True, source='id')
    fecha_solicitud = serializers.DateTimeField(read_only=True)
    mensaje = serializers.CharField(read_only=True, default="Solicitud registrada correctamente.")
    numero_registro_vinculado = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        """
        Validación cruzada Acto - Puesto
        """
        acto = data.get('acto')
        puesto = data.get('puesto')

        if not acto.tipo_acto.requiere_papeleta:
            raise serializers.ValidationError({"acto_id": "Este acto no requiere solicitud de papeleta de sitio."})

        if puesto.acto.id != acto.id:
            raise serializers.ValidationError({"puesto_id": f"El puesto {puesto.nombre} no pertenece al acto {acto.nombre}."})

        if "CIRIO" not in puesto.tipo_puesto.nombre_tipo.upper():
            raise serializers.ValidationError({"puesto_id": "El puesto seleccionado no es de tipo CIRIO."})

        return data
    

# -----------------------------------------------------------------------------
# SERIALIZERS PARA PANEL DE ADMINISTRADOR
# -----------------------------------------------------------------------------
class HermanoListadoSerializer(serializers.ModelSerializer):
    """
    Serializador ligero exclusivo para el listado de administración.
    Solo devuelve los campos solicitados para la tabla de gestión.
    """
    class Meta:
        model = User
        fields = [
            'id',
            'numero_registro',
            'dni',
            'nombre',
            'primer_apellido',
            'segundo_apellido',
            'estado_hermano',
            'telefono',
            'email',
            'direccion',
            'fecha_ingreso_corporacion',
            'fecha_nacimiento',
            'esAdmin'
        ]

class HermanoAdminUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador independiente para la edición completa por parte del Administrador.
    """
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'password',
            'dni', 
            'nombre', 
            'primer_apellido', 
            'segundo_apellido', 
            'email',
            'telefono', 
            'fecha_nacimiento', 
            'genero', 
            'estado_civil', 
            'direccion', 
            'codigo_postal', 
            'localidad', 
            'provincia', 
            'comunidad_autonoma', 
            'lugar_bautismo', 
            'fecha_bautismo', 
            'parroquia_bautismo',
            'numero_registro', 
            'estado_hermano', 
            'fecha_ingreso_corporacion', 
            'fecha_baja_corporacion', 
            'esAdmin'
        ]

        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def validate(self, data):
        """
        Validaciones necesarias antes de pasar al servicio.
        """
        if 'fecha_ingreso_corporacion' in data and 'fecha_baja_corporacion' in data:
            ingreso = data['fecha_ingreso_corporacion']
            baja = data['fecha_baja_corporacion']
            if ingreso and baja and baja < ingreso:
                raise serializers.ValidationError("La fecha de baja no puede ser anterior a la de ingreso.")
        return data



# -----------------------------------------------------------------------------
# SERIALIZERS PARA LA CREACIÓN DE ACTOS
# -----------------------------------------------------------------------------
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



class ActoUpdateSerializer(serializers.ModelSerializer):
    requiere_papeleta = serializers.BooleanField(source='tipo_acto.requiere_papeleta', read_only=True)

    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        queryset=TipoActo.objects.all()
    )

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
            'fin_solicitud_cirios'
        ]

# -----------------------------------------------------------------------------
# SERIALIZERS PARA LA SOLICITUD DE PAPELETA DE SITIO
# -----------------------------------------------------------------------------
class PreferenciaSolicitudDTO(serializers.Serializer):
    puesto_id = serializers.PrimaryKeyRelatedField(queryset=Puesto.objects.all(), source='puesto_solicitado')
    orden = serializers.IntegerField(source='orden_prioridad')


class SolicitudUnificadaSerializer(serializers.ModelSerializer):
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    modalidad_acto = serializers.CharField(source='acto.modalidad', read_only=True)

    acto_id = serializers.PrimaryKeyRelatedField(
        queryset=Acto.objects.all(), 
        source='acto', 
        write_only=True
    )

    puesto_general_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    preferencias_solicitadas = PreferenciaSolicitudDTO(many=True, write_only=True, required=False)
    preferencias = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = PapeletaSitio
        fields = [
            'id',
            'acto_id',
            'nombre_acto',
            'modalidad_acto',
            'anio',
            'estado_papeleta',
            'es_solicitud_insignia',
            'puesto_general_id',
            'preferencias_solicitadas',
            'preferencias',
            'fecha_solicitud'
        ]

        read_only_fields = ['id', 'anio', 'estado_papeleta', 'fecha_solicitud']


# -----------------------------------------------------------------------------
# SERIALIZERS PARA LA VINCULACIÓN DE PAPELETAS DE SITIO
# -----------------------------------------------------------------------------
class VincularPapeletaSerializer(serializers.Serializer):
    """
    Serializer simple para recibir el número de registro del hermano objetivo.
    """
    numero_registro_objetivo = serializers.IntegerField(
        required=True, 
        min_value=1,
        help_text="Número de registro del hermano con el que quieres ir."
    )

class DetalleVinculacionSerializer(serializers.ModelSerializer):
    """
    Para devolver la respuesta con los datos del hermano vinculado.
    """
    nombre_vinculado = serializers.SerializerMethodField()
    
    class Meta:
        model = PapeletaSitio
        fields = ['id', 'vinculado_a', 'nombre_vinculado']

    def get_nombre_vinculado(self, obj):
        if obj.vinculado_a:
            return f"{obj.vinculado_a.nombre} {obj.vinculado_a.primer_apellido}"
        return None
