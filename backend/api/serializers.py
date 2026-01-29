from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from .models import (AreaInteres, CuerpoPertenencia, Cuota, DatosBancarios, HermanoCuerpo, PreferenciaSolicitud, TipoActo, Acto, Puesto, PapeletaSitio, TipoPuesto, Tramo)
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


class ActoSerializer(serializers.ModelSerializer):
    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        queryset=TipoActo.objects.all()
    )
    puestos_disponibles = PuestoSerializer(many=True, read_only=True)

    tramos = TramoSerializer(many=True, read_only=True)

    requiere_papeleta = serializers.BooleanField(source='tipo_acto.requiere_papeleta', read_only=True)

    en_plazo_insignias = serializers.SerializerMethodField()
    en_plazo_cirios = serializers.SerializerMethodField()

    class Meta:
        model = Acto
        fields = ['id', 'nombre', 'descripcion', 'fecha', 'tipo_acto', 'modalidad', 'inicio_solicitud', 'fin_solicitud', 'en_plazo_insignias', 'puestos_disponibles', 'tramos', 'inicio_solicitud_cirios', 'fin_solicitud_cirios', 'en_plazo_cirios', 'requiere_papeleta']

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
        

class MisPapeletasSerializer(PapeletaSitioSerializer):
    """
    Serializer de lectura para que el hermano vea sus propias papeletas.
    Hereda de PapeletaSitioSerializer pero añade las preferencias solicitadas
    para que el usuario recuerde qué pidió (Vara, Manigueta, etc.).
    """
    preferencias = PreferenciaSolicitudSerializer(many=True, read_only=True)
    
    # Campos calculados extra para el frontend
    nombre_tipo_acto = serializers.CharField(source='acto.tipo_acto.nombre_tipo', read_only=True)
    fecha_acto = serializers.DateTimeField(source='acto.fecha', read_only=True)

    class Meta(PapeletaSitioSerializer.Meta):
        fields = PapeletaSitioSerializer.Meta.fields + ['preferencias', 'nombre_tipo_acto', 'fecha_acto']
        

class SolicitudInsigniaSerializer(serializers.ModelSerializer):
    """
    Serializador Transaccional: Recibe la intención de sacar papeleta y
    una lista de preferencias de puestos/insignias.
    """
    preferencias = PreferenciaSolicitudSerializer(many=True)
    
    # Campos informativos del hermano y acto
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    
    # Input field para el ID del acto (necesario al crear la solicitud)
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
            # --- AQUÍ FALLABA ANTES ---
            # Ahora, gracias al 'source' de arriba, item ya tiene la clave 'puesto_solicitado'
            # y contiene el OBJETO Puesto completo, no solo el ID.
            puesto = item['puesto_solicitado'] 
            orden = item['orden_prioridad']

            # 1. Validar que sea insignia
            if not puesto.tipo_puesto.es_insignia:
                raise serializers.ValidationError(
                    f"El puesto '{puesto.nombre}' no es una insignia válida."
                )

            # 2. Validar duplicados
            if puesto.id in puestos_vistos:
                raise serializers.ValidationError(f"El puesto '{puesto.nombre}' está repetido.")
            puestos_vistos.add(puesto.id)
            
            ordenes_vistos.append(orden)

        # 3. Validar secuencia numérica (1, 2, 3...)
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
        
        for item in preferencias:
            # Aquí también usamos la clave correcta
            puesto = item['puesto_solicitado']
            
            if puesto.acto.id != acto.id:
                raise serializers.ValidationError({
                    "preferencias": f"El puesto '{puesto.nombre}' no pertenece al acto '{acto.nombre}'."
                })
            
        return data

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
# SERIALIZERS PARA CONSULTAR EL HISTÓRICO DE PAPELETAS DE SITIO (NO ADMIN)
# -----------------------------------------------------------------------------
class HistorialPapeletaSerializer(serializers.ModelSerializer):
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    fecha_acto = serializers.DateTimeField(source='acto.fecha', read_only=True)

    nombre_puesto = serializers.CharField(source='puesto.nombre', read_only=True, allow_null=True)
    nombre_tramo = serializers.CharField(source='tramo.nombre', read_only=True, allow_null=True)
    numero_tramo = serializers.IntegerField(source='tramo.numero_orden', read_only=True, allow_null=True)

    es_insignia = serializers.BooleanField(source='puesto.tipo_puesto.es_insignia', read_only=True, default=False)

    lugar_citacion = serializers.CharField(source='puesto.lugar_citacion', read_only=True, allow_null=True)
    hora_citacion = serializers.TimeField(source='puesto.hora_citacion', read_only=True, allow_null=True)

    lado_display = serializers.CharField(source='get_lado_display', read_only=True)

    class Meta:
        model = PapeletaSitio
        fields = [
            'id', 
            'estado_papeleta', 
            'fecha_solicitud', 
            'fecha_emision', 
            'anio',
            'nombre_acto',
            'fecha_acto',
            'nombre_puesto',
            'nombre_tramo',
            'numero_tramo',
            'es_insignia',
            'lugar_citacion',
            'hora_citacion',
            'orden_en_tramo',
            'lado',
            'lado_display'
        ]

# -----------------------------------------------------------------------------
# SERIALIZERS PARA LA CREACIÓN DE ACTOS
# -----------------------------------------------------------------------------
class ActoCreateSerializer(serializers.ModelSerializer):
    tipo_acto = serializers.SlugRelatedField(
        slug_field='tipo',
        queryset=TipoActo.objects.all()
    )

    requiere_papeleta = serializers.BooleanField(source='tipo_acto.requiere_papeleta', read_only=True)

    class Meta:
        model = Acto
        fields = [
            'id',
            'nombre',
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