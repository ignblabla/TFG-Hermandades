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
        fields = ['id', 'nombre', 'descripcion', 'fecha', 'tipo_acto', 'inicio_solicitud', 'fin_solicitud', 'en_plazo_insignias', 'puestos_disponibles', 'tramos', 'inicio_solicitud_cirios', 'fin_solicitud_cirios', 'en_plazo_cirios', 'requiere_papeleta']

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
            'puesto', 'nombre_puesto', 'tramo_display', 'tramo_id'
        ]
        read_only_fields = ['fecha_emision', 'codigo_verificacion', 'anio', 'tramo_display']

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
    nombre_puesto = serializers.CharField(source='puesto.nombre', read_only=True)
    tipo_puesto_nombre = serializers.CharField(source='puesto.tipo_puesto.nombre_tipo', read_only=True)
    es_insignia = serializers.BooleanField(source='puesto.tipo_puesto.es_insignia', read_only=True)

    puesto_id = serializers.PrimaryKeyRelatedField(
        queryset=Puesto.objects.filter(disponible=True),
        source='puesto',
        write_only=True
    )

    class Meta:
        model = PreferenciaSolicitud
        fields = ['id', 'puesto_id', 'nombre_puesto', 'tipo_puesto_nombre', 'orden_prioridad', 'es_insignia']

        def validate(self, data):
            puesto = data.get('puesto')
            
            if puesto and not puesto.disponible:
                raise serializers.ValidationError(f"El puesto {puesto.nombre} ya no está disponible.")
                
            return data
        

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
    # Nested Serializer para recibir la lista de opciones (Ej: [Vara, Cirio, Manigueta])
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
        Validación de lógica de conjunto (Set Logic):
        1. No puede haber puestos repetidos.
        2. El orden de prioridad debe ser secuencial (1, 2, 3...).
        """
        if not value:
            raise serializers.ValidationError("Debe indicar al menos una preferencia de sitio.")

        puestos_vistos = set()
        ordenes_vistos = []

        for item in value:
            puesto = item['puesto']
            orden = item['orden_prioridad']

            if not puesto.tipo_puesto.es_insignia:
                raise serializers.ValidationError(
                    f"El puesto '{puesto.nombre}' no es una insignia válida para esta solicitud."
                )

            # 1. Chequeo de duplicados
            if puesto.id in puestos_vistos:
                raise serializers.ValidationError(f"El puesto '{puesto.nombre}' está repetido en sus preferencias.")
            puestos_vistos.add(puesto.id)
            
            ordenes_vistos.append(orden)

        # 2. Chequeo de secuencia (opcional, pero recomendado para UI limpia)
        ordenes_vistos.sort()
        expected_sequence = list(range(1, len(ordenes_vistos) + 1))
        if ordenes_vistos != expected_sequence:
            raise serializers.ValidationError("El orden de prioridad debe ser consecutivo (1, 2, 3...) sin saltos.")

        return value

    def validate(self, data):
        """
        Validación cruzada Acto vs Puestos solicitados.
        """
        acto = data.get('acto')
        preferencias = data.get('preferencias')
        
        # Validar que todos los puestos solicitados pertenecen al acto indicado
        for item in preferencias:
            puesto = item['puesto']
            if puesto.acto.id != acto.id:
                raise serializers.ValidationError({
                    "preferencias": f"El puesto '{puesto.nombre}' no pertenece al acto '{acto.nombre}'."
                })
            
        return data
    

    def create(self, validated_data):
        """
        Sobrescribimos create para manejar la escritura de campos anidados (preferencias).
        """
        # 1. Extraemos los datos anidados de la lista 'preferencias'
        preferencias_data = validated_data.pop('preferencias')

        # 2. Usamos una transacción atómica: O se guarda todo, o no se guarda nada.
        with transaction.atomic():
            # 3. Creamos la instancia del Padre (PapeletaSitio)
            # validated_data ya contiene el resto de datos limpios y el 'hermano' (si lo pasas en el save del servicio)
            papeleta = PapeletaSitio.objects.create(**validated_data)

            for preferencia_item in preferencias_data:
                PreferenciaSolicitud.objects.create(
                    papeleta=papeleta,
                    puesto_solicitado=preferencia_item['puesto'],
                    orden_prioridad=preferencia_item['orden_prioridad']
                )

        return papeleta
    




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
            'hora_citacion'
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

    def validate(self, data):
        tipo_acto_seleccionado = data.get('tipo_acto')
        modalidad = data.get('modalidad')

        if not tipo_acto_seleccionado:
            return data
        
        necesita_papeleta = tipo_acto_seleccionado.requiere_papeleta

        # --- ESCENARIO A: NO REQUIERE PAPELETA ---
        if not necesita_papeleta:
            data['inicio_solicitud'] = None
            data['fin_solicitud'] = None
            data['inicio_solicitud_cirios'] = None
            data['fin_solicitud_cirios'] = None
            return data
        
        # --- ESCENARIO B: SÍ REQUIERE PAPELETA ---
        inicio_insignias = data.get('inicio_solicitud')
        fin_insignias = data.get('fin_solicitud')
        inicio_cirios = data.get('inicio_solicitud_cirios')
        fin_cirios = data.get('fin_solicitud_cirios')

        if inicio_insignias and fin_insignias and inicio_insignias >= fin_insignias:
            raise serializers.ValidationError({"fin_solicitud": "La fecha de fin de insignias debe ser posterior al inicio."})
        
        if inicio_cirios and fin_cirios and inicio_cirios >= fin_cirios:
            raise serializers.ValidationError({"fin_solicitud_cirios": "La fecha de fin de cirios debe ser posterior al inicio."})
        
        if modalidad == Acto.ModalidadReparto.TRADICIONAL:
            if fin_insignias and inicio_cirios:
                if inicio_cirios <= fin_insignias:
                    raise serializers.ValidationError({
                        'inicio_solicitud_cirios': (
                            f'La solicitud de cirios no puede solaparse con insignias. '
                            f'Insignias termina el {fin_insignias.strftime("%d/%m/%Y %H:%M")}.'
                        )
                    })
                
            if inicio_insignias and inicio_cirios and inicio_insignias >= inicio_cirios:
                raise serializers.ValidationError({'inicio_solicitud': 'El reparto de insignias debe comenzar antes que el de cirios.'})
        
        return data