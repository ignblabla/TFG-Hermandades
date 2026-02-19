from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint, Q

# -----------------------------------------------------------------------------
# ENTIDAD: AREA DE INTERÉS
# -----------------------------------------------------------------------------
class AreaInteres(models.Model):
    class NombreArea(models.TextChoices):
        CARIDAD = 'CARIDAD', 'Caridad'
        CULTOS_FORMACION = 'CULTOS_FORMACION', 'Cultos y Formación'
        JUVENTUD = 'JUVENTUD', 'Juventud'
        PATRIMONIO = 'PATRIMONIO', 'Patrimonio'
        PRIOSTIA = 'PRIOSTIA', 'Priostía'
        DIPUTACION_MAYOR_GOBIERNO = 'DIPUTACION_MAYOR_GOBIERNO', 'Diputación Mayor de Gobierno'
        COSTALEROS = 'COSTALEROS', 'Costaleros'
        ACOLITOS = 'ACOLITOS', 'Acólitos'

    nombre_area = models.CharField(max_length=50, choices=NombreArea.choices, unique=True, verbose_name="Nombre del área")

    telegram_channel_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Canal Telegram", help_text="Ej: -100123456789. Deja vacío si esta área no tiene canal propio.")
    telegram_invite_link = models.URLField(max_length=255, blank=True, null=True, verbose_name="Enlace de invitación de Telegram", help_text="Ej: https://t.me/+AbCdEfGhIjK. Enlace para que el hermano se una al canal desde la app.")

    def __str__(self):
        return self.get_nombre_area_display()
    
# -----------------------------------------------------------------------------
# ENTIDAD: CUERPO DE PERTENENCIA
# -----------------------------------------------------------------------------
class CuerpoPertenencia(models.Model):
    class NombreCuerpo(models.TextChoices):
        COSTALEROS = 'COSTALEROS', 'Costaleros'
        NAZARENOS = 'NAZARENOS', 'Nazarenos'
        DIPUTADOS = 'DIPUTADOS', 'Diputados de tramo'
        BRAZALETES = 'BRAZALETES', 'Brazaletes'
        ACOLITOS = 'ACOLITOS', 'Acólitos'
        CAPATACES = 'CAPATACES', 'Capataces'
        SANITARIOS = 'SANITARIOS', 'Sanitarios'
        PRIOSTÍA = 'PRIOSTIA', 'Priostía'
        CARIDAD_ACCION_SOCIAL = 'CARIDAD_ACCION_SOCIAL', 'Caridad y Acción Social'
        JUVENTUD = 'JUVENTUD', 'Juventud'
        JUNTA_GOBIERNO = 'JUNTA_GOBIERNO', 'Junta de Gobierno'

    nombre_cuerpo = models.CharField(max_length=50, choices=NombreCuerpo.choices, unique=True, verbose_name="Nombre del cuerpo")

    def __str__(self):
        return self.get_nombre_cuerpo_display()

# -----------------------------------------------------------------------------
# ENTIDAD: HERMANO - CUERPO
# -----------------------------------------------------------------------------    
class HermanoCuerpo(models.Model):
    hermano = models.ForeignKey('Hermano', on_delete=models.CASCADE, related_name='pertenencias_cuerpos',verbose_name="Hermano")

    cuerpo = models.ForeignKey(
        CuerpoPertenencia, 
        on_delete=models.PROTECT, 
        related_name='integrantes',
        verbose_name="Cuerpo de pertenencia"
    )

    anio_ingreso = models.PositiveIntegerField(verbose_name="Año de ingreso", help_text="Año en el que el hermano ingresó en este cuerpo específico")

    def __str__(self):
        return f"{self.hermano} en {self.cuerpo} desde {self.anio_ingreso}"
    
# -----------------------------------------------------------------------------
# ENTIDAD: DATOS BANCARIOS
# -----------------------------------------------------------------------------
class DatosBancarios(models.Model):
    iban_validator = RegexValidator(
        regex=r'^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$',
        message="El IBAN debe tener un formato válido (ej: ES00...). Debe comenzar por 2 letras y 2 números."
    )

    class Periodicidad(models.TextChoices):
        TRIMESTRAL = 'TRIMESTRAL', 'Trimestral'
        SEMESTRAL = 'SEMESTRAL', 'Semestral'
        ANUAL = 'ANUAL', 'Anual'

    hermano = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='datos_bancarios', verbose_name="Hermano titular")

    iban = models.CharField(max_length=34, validators=[iban_validator], verbose_name="IBAN")
    es_titular = models.BooleanField(default=True, verbose_name="¿Es titular?")
    titular_cuenta = models.CharField(max_length=150, verbose_name="Nombre del titular", blank=True, null=True, help_text="Rellenar solo si el hermano no es el titular")

    periodicidad = models.CharField(max_length=20, choices=Periodicidad.choices, default=Periodicidad.ANUAL, verbose_name="Periodicidad de cobro")

    def __str__(self):
        return f"Datos bancarios de {self.hermano}"
    
# -----------------------------------------------------------------------------
# ENTIDAD: CUOTA
# -----------------------------------------------------------------------------
class Cuota(models.Model):
    class TipoCuota(models.TextChoices):
        ORDINARIA = 'ORDINARIA', 'Cuota de Hermano'
        INGRESO = 'INGRESO', 'Cuota de Ingreso/Alta'
        EXTRAORDINARIA = 'EXTRAORDINARIA', 'Cuota Extraordinaria'

    class EstadoCuota(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de pago'
        EN_REMESA = 'EN_REMESA', 'Enviada al banco (Remesa)'
        PAGADA = 'PAGADA', 'Pagada'
        DEVUELTA = 'DEVUELTA', 'Devuelta por el banco'
        EXENTO = 'EXENTO', 'Exento de pago'

    class MetodoPago(models.TextChoices):
        DOMICILIACION = 'DOMICILIACION', 'Domiciliación Bancaria'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'

    hermano = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cuotas', verbose_name="Hermano")

    anio = models.PositiveIntegerField(verbose_name="Ejercicio / Año")
    tipo = models.CharField(max_length=20, choices=TipoCuota.choices, default=TipoCuota.ORDINARIA)
    descripcion = models.CharField(max_length=100, help_text="Ej: Cuota 2024")

    fecha_emision = models.DateField(auto_now_add=True, verbose_name="Fecha de emisión")
    fecha_pago = models.DateField(null=True, blank=True, verbose_name="Fecha de pago")

    importe = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Importe (€)")

    estado = models.CharField(max_length=20, choices=EstadoCuota.choices, default=EstadoCuota.PENDIENTE)
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.DOMICILIACION)

    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.anio} - {self.tipo} - {self.hermano}"
    
    class Meta:
        indexes = [models.Index(fields=['hermano', 'estado', 'anio'], name='idx_cuota_deuda_hermano'),]

# -----------------------------------------------------------------------------
# ENTIDAD: HERMANO
# -----------------------------------------------------------------------------
class Hermano(AbstractUser):
    class Genero(models.TextChoices):
        MASCULINO = 'MASCULINO', 'Masculino'
        FEMENINO = 'FEMENINO', 'Femenino'

    class EstadoCivil(models.TextChoices):
        SOLTERO = 'SOLTERO', 'Soltero'
        SEPARADO = 'SEPARADO', 'Separado'
        CASADO = 'CASADO', 'Casado'
        VIUDO = 'VIUDO', 'Viudo'

    class EstadoHermano(models.TextChoices):
        ALTA = 'ALTA', 'Alta'
        BAJA = 'BAJA', 'Baja'
        PENDIENTE_INGRESO = 'PENDIENTE_INGRESO', 'Pendiente de ingreso'

    telefono_validator = RegexValidator(
        regex=r'^\d{9}$',
        message="El número de teléfono debe tener exactamente 9 dígitos numéricos."
    )

    cp_validator = RegexValidator(
        regex=r'^\d{5}$',
        message="El código postal debe tener exactamente 5 dígitos numéricos."
    )

    username = models.CharField(max_length=150, unique=True, blank=False, null=False)
    nombre = models.CharField(max_length=100, verbose_name = "Nombre")
    primer_apellido = models.CharField(max_length=100, verbose_name = "Primer apellido")
    segundo_apellido = models.CharField(max_length=100, verbose_name = "Segundo apellido")
    dni = models.CharField(max_length=9, unique=True, verbose_name = "DNI")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name = "Fecha de nacimiento")

    telefono = models.CharField(validators=[telefono_validator], max_length=9, verbose_name="Teléfono")
    genero = models.CharField(max_length=10, choices=Genero.choices, default=Genero.MASCULINO, verbose_name="Género")
    estado_civil = models.CharField(max_length=10, choices=EstadoCivil.choices, verbose_name="Estado Civil")

    direccion = models.CharField(max_length=255, verbose_name="Dirección postal", null=True, blank=True)
    codigo_postal = models.CharField(max_length=5, validators=[cp_validator], verbose_name="Código postal", null=True, blank=True)
    localidad = models.CharField(max_length=100, verbose_name="Localidad", null=True, blank=True)
    provincia = models.CharField(max_length=100, verbose_name="Provincia", null=True, blank=True)
    comunidad_autonoma = models.CharField(max_length=100, verbose_name="Comunidad Autónoma", null=True, blank=True)

    lugar_bautismo = models.CharField(max_length=100, verbose_name="Bautizado en", null=True, blank=True, help_text="Localidad o ciudad donde recibió el bautismo")
    fecha_bautismo = models.DateField(null=True, blank=True, verbose_name="Fecha de bautismo")
    parroquia_bautismo = models.CharField(max_length=150, verbose_name="Parroquia de bautismo", null=True, blank=True)

    numero_registro = models.PositiveIntegerField(unique=True, verbose_name="Número de registro", help_text="Número de registro en la hermandad", null=True, blank=True)
    estado_hermano = models.CharField(max_length=20, choices=EstadoHermano.choices, default=EstadoHermano.PENDIENTE_INGRESO, verbose_name="Estado del hermano")
    fecha_ingreso_corporacion = models.DateField(null=True, blank=True, verbose_name="Fecha de ingreso", help_text="Fecha oficial de admisión en la nómina de la Hermandad.")
    fecha_baja_corporacion = models.DateField(null=True, blank=True, verbose_name="Fecha de baja",help_text="Fecha en la que se hizo efectiva la baja (si procede).")

    esAdmin = models.BooleanField(default=False, verbose_name="Es Administrador")

    areas_interes = models.ManyToManyField(
        AreaInteres,
        verbose_name="Áreas de interés",
        blank=True,
        related_name="hermanos"
    )

    cuerpos = models.ManyToManyField(CuerpoPertenencia,
        through='HermanoCuerpo',
        verbose_name="Cuerpos de pertenencia",
        related_name="hermanos_miembros",
        blank=True,
        help_text="Colectivos a los que pertenece el hermano"
    )

    first_name = None
    last_name = None

    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['nombre', 'primer_apellido', 'segundo_apellido', 'email', 'telefono', 'estado_civil']

    @property
    def esta_al_corriente(self):
        """Retorna True si el hermano NO tiene ninguna cuota pendiente o devuelta."""
        estados_deuda = ['PENDIENTE', 'DEVUELTA']
        tiene_deuda = self.cuotas.filter(estado__in=estados_deuda).exists()
        return not tiene_deuda
    
    @property
    def antiguedad_anios(self):
        """Calcula la antigüedad en años para listados simples."""
        if not self.fecha_ingreso_corporacion:
            return 0
        today = timezone.now().date()
        return today.year - self.fecha_ingreso_corporacion.year - (
            (today.month, today.day) < (self.fecha_ingreso_corporacion.month, self.fecha_ingreso_corporacion.day)
        )

    def __str__(self):
        return f"{self.dni} - {self.nombre} {self.primer_apellido}"
    
    def clean(self):
        super().clean()
        if self.fecha_nacimiento and self.fecha_bautismo:
            if self.fecha_bautismo < self.fecha_nacimiento:
                raise ValidationError({
                    'fecha_bautismo': 'La fecha de bautismo no puede ser anterior a la fecha de nacimiento'
                })
        
        # Validación extra opcional: Si está de ALTA, debería tener número de hermano (depende de tu lógica de negocio)
        if self.estado_hermano == self.EstadoHermano.ALTA and not self.numero_registro:
            raise ValidationError({'numero_registro': 'Un hermano de Alta debe tener un número de registro asignado.'})
            pass

        if self.fecha_ingreso_corporacion and self.fecha_baja_corporacion:
            if self.fecha_baja_corporacion < self.fecha_ingreso_corporacion:
                raise ValidationError({
                    'fecha_baja_corporacion': 'La fecha de baja no puede ser anterior a la fecha de ingreso.'
                })

        if self.estado_hermano == self.EstadoHermano.BAJA and not self.fecha_baja_corporacion:
            raise ValidationError({
                'fecha_baja_corporacion': 'Si el estado es BAJA, debe indicar la fecha de la misma.'
            })
        
        if self.dni:
            self.username = self.dni
    
    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.username:
            self.username = self.dni
        super().save(*args, **kwargs)

# -----------------------------------------------------------------------------
# ENTIDAD: COMUNICADO
# -----------------------------------------------------------------------------
class Comunicado(models.Model):
    class TipoComunicacion(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        INFORMATIVO = 'INFORMATIVO', 'Informativo'
        CULTOS = 'CULTOS', 'Cultos'
        SECRETARIA = 'SECRETARIA', 'Secretaría'
        URGENTE = 'URGENTE', 'Urgente'
        EVENTOS = 'EVENTOS', 'Eventos y Caridad'

    titulo = models.CharField(max_length=200, verbose_name="Título")
    contenido = models.TextField(verbose_name="Contenido", help_text="Contenido del comunicado. Soporta texto enriquecido si el frontend lo implementa.")
    imagen_portada = models.ImageField(upload_to='comunicados/portadas/', null=True, blank=True, verbose_name="Imagen de Portada", help_text="Imagen principal de la noticia o comunicado")
    fecha_emision = models.DateTimeField(default=timezone.now, verbose_name="Fecha de emisión")
    tipo_comunicacion = models.CharField(max_length=20, choices=TipoComunicacion.choices, default=TipoComunicacion.GENERAL, verbose_name="Tipo de comunicación")

    autor = models.ForeignKey(Hermano, on_delete=models.PROTECT, related_name='comunicados_emitidos', verbose_name="Autor (Emisor)")
    areas_interes = models.ManyToManyField(AreaInteres, related_name='comunicados', verbose_name="Áreas destinatarias", blank=True, help_text="Seleccione las áreas a las que va dirigido este comunicado.")

    def __str__(self):
        return f"{self.fecha_emision.strftime('%d/%m/%Y')} - {self.titulo} ({self.get_tipo_comunicacion_display()})"

# -----------------------------------------------------------------------------
# ENTIDAD: TIPO DE ACTO
# -----------------------------------------------------------------------------
class TipoActo(models.Model):
    class OpcionesTipo(models.TextChoices):
        ESTACION_PENITENCIA = 'ESTACION_PENITENCIA', 'Estación de Penitencia'
        CABILDO_GENERAL = 'CABILDO_GENERAL', 'Cabildo General'
        CABILDO_EXTRAORDINARIO = 'CABILDO_EXTRAORDINARIO', 'Cabildo Extraordinario'
        VIA_CRUCIS = 'VIA_CRUCIS', 'Vía Crucis'
        QUINARIO = 'QUINARIO', 'Quinario'
        TRIDUO = 'TRIDUO', 'Triduo'
        ROSARIO_AURORA = 'ROSARIO_AURORA', 'Rosario de la Aurora'
        CONVIVENCIA = 'CONVIVENCIA', 'Convivencia'
        PROCESION_EUCARISTICA = 'PROCESION_EUCARISTICA', 'Procesión Eucarística'
        PROCESION_EXTRAORDINARIA = 'PROCESION_EXTRAORDINARIA', 'Procesión Extraordinaria'
        

    tipo = models.CharField(max_length=50, choices=OpcionesTipo.choices, unique=True, verbose_name="Tipo de Acto")
    requiere_papeleta = models.BooleanField(default=False, verbose_name='¿Requiere papeleta?', help_text="Marcar si este tipo de acto implica reparto de papeletas de sitio")
    
# -----------------------------------------------------------------------------
# ENTIDAD: ACTO
# -----------------------------------------------------------------------------
class Acto(models.Model):
    class ModalidadReparto(models.TextChoices):
        TRADICIONAL = 'TRADICIONAL', 'Tradicional (Fases separadas: Insignias luego Cirios)'
        UNIFICADO = 'UNIFICADO', 'Unificado / Express (Todo en un plazo)'

    nombre = models.CharField(max_length=100, verbose_name="Nombre del acto")
    descripcion = models.TextField(verbose_name="Descripción", blank=True, null=True)
    fecha = models.DateTimeField(verbose_name="Fecha y hora")
    modalidad = models.CharField(max_length=20, choices=ModalidadReparto.choices, verbose_name="Modalidad de reparto", blank=True, null=True)

    tipo_acto = models.ForeignKey(TipoActo, on_delete=models.PROTECT, verbose_name="Tipo de acto", related_name="actos")

    inicio_solicitud = models.DateTimeField(verbose_name="Inicio solicitud papeletas", blank=True, null=True, help_text="Fecha y hora de apertura de solicitudes (solo si requiere papeleta)")
    fin_solicitud = models.DateTimeField(verbose_name="Fin solicitud papeletas", blank=True, null=True, help_text="Fecha y hora de cierre de solicitudes (solo si requiere papeleta)")

    inicio_solicitud_cirios = models.DateTimeField(verbose_name="Inicio solicitud papeletas generales", blank=True, null=True, help_text="Fecha y hora de apertura de solicitudes de papeletas de sitio generales")
    fin_solicitud_cirios = models.DateTimeField(verbose_name="Fin solicitud papeletas generales", blank=True, null=True, help_text="Fecha y hora de cierre de solicitudes de papeletas de sitio generales")

    fecha_ejecucion_reparto = models.DateTimeField(null=True, blank=True, verbose_name="Fecha ejecución reparto", help_text="Si tiene valor, indica que el reparto automático ya se ha ejecutado.")

    def clean(self):
        super().clean()
        errors = {}

        if self.nombre is not None and not self.nombre.strip():
            errors["nombre"] = "El nombre del acto no puede estar vacío."

        if self.tipo_acto_id is None:
            raise ValidationError({"tipo_acto": "El tipo de acto es obligatorio."})

        if self.tipo_acto and not self.tipo_acto.requiere_papeleta:
            if self.modalidad:
                errors["modalidad"] = "Un acto que no requiere papeleta no puede tener modalidad."
            for f in ("inicio_solicitud", "fin_solicitud", "inicio_solicitud_cirios", "fin_solicitud_cirios"):
                if getattr(self, f) is not None:
                    errors[f] = "Un acto que no requiere papeleta no puede tener fechas de solicitud."
            if errors:
                raise ValidationError(errors)
            return

        if self.tipo_acto and self.tipo_acto.requiere_papeleta:
            if not self.modalidad:
                errors["modalidad"] = "La modalidad es obligatoria para actos con papeleta."

            if not self.inicio_solicitud:
                errors["inicio_solicitud"] = "El inicio de solicitud es obligatorio."
            if not self.fin_solicitud:
                errors["fin_solicitud"] = "El fin de solicitud es obligatorio."

            if self.inicio_solicitud and self.fin_solicitud:
                if self.inicio_solicitud >= self.fin_solicitud:
                    errors["fin_solicitud"] = "El fin de solicitud debe ser posterior al inicio."

            if self.fecha and self.inicio_solicitud and self.inicio_solicitud >= self.fecha:
                errors["inicio_solicitud"] = "El inicio de solicitud no puede ser igual o posterior a la fecha del acto."

            if self.fecha and self.fin_solicitud and self.fin_solicitud > self.fecha:
                errors["fin_solicitud"] = "El fin de solicitud no puede ser posterior a la fecha del acto."

            if self.modalidad == self.ModalidadReparto.TRADICIONAL:
                if not self.inicio_solicitud_cirios:
                    errors["inicio_solicitud_cirios"] = "El inicio de cirios es obligatorio en modalidad tradicional."
                if not self.fin_solicitud_cirios:
                    errors["fin_solicitud_cirios"] = "El fin de cirios es obligatorio en modalidad tradicional."

                if self.inicio_solicitud_cirios and self.fin_solicitud_cirios:
                    if self.inicio_solicitud_cirios >= self.fin_solicitud_cirios:
                        errors["fin_solicitud_cirios"] = "El fin de cirios debe ser posterior al inicio."

                if self.fecha and self.inicio_solicitud_cirios and self.inicio_solicitud_cirios >= self.fecha:
                    errors["inicio_solicitud_cirios"] = "El inicio de cirios no puede ser igual o posterior a la fecha del acto."

                if self.fecha and self.fin_solicitud_cirios and self.fin_solicitud_cirios > self.fecha:
                    errors["fin_solicitud_cirios"] = "El fin de cirios no puede ser posterior a la fecha del acto."

                if (
                    self.inicio_solicitud and self.fin_solicitud and
                    self.inicio_solicitud_cirios and self.fin_solicitud_cirios
                ):
                    if not (self.inicio_solicitud < self.fin_solicitud < self.inicio_solicitud_cirios < self.fin_solicitud_cirios):
                        if self.fin_solicitud >= self.inicio_solicitud_cirios:
                            errors.setdefault(
                                "inicio_solicitud_cirios",
                                "El período de cirios debe comenzar después de finalizar el de insignias."
                            )
                        else:
                            errors.setdefault(
                                "fin_solicitud_cirios",
                                "Orden de fases incorrecto: cirios debe ir completamente después de insignias."
                            )

            elif self.modalidad == self.ModalidadReparto.UNIFICADO:
                if self.inicio_solicitud_cirios is not None or self.fin_solicitud_cirios is not None:
                    errors["modalidad"] = "En modalidad UNIFICADO no se deben definir fechas de cirios."

        if errors:
            raise ValidationError(errors)
            
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.fecha.year})"

# -----------------------------------------------------------------------------
# ENTIDAD: TIPO DE PUESTO
# -----------------------------------------------------------------------------
class TipoPuesto(models.Model):
    """
    Representa la categoría o tipología del puesto.
    """
    nombre_tipo = models.CharField(max_length=75, unique=True, verbose_name="Nombre del tipo de puesto")
    solo_junta_gobierno = models.BooleanField(
        default=False,
        verbose_name="Solo para Junta de Gobierno",
        help_text="Si se marca, este tipo de puesto estará restringido a miembros de la Junta de Gobierno."
    )
    es_insignia = models.BooleanField(
        default=False, 
        verbose_name="¿Es insignia?", 
        help_text="Marcar si este puesto se considera una insignia o vara."
    )

    def __str__(self):
        return self.nombre_tipo

# -----------------------------------------------------------------------------
# ENTIDAD: PUESTO
# -----------------------------------------------------------------------------
class Puesto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del puesto")
    numero_maximo_asignaciones = models.PositiveIntegerField(verbose_name="Número máximo de asignaciones (Cupo total)", default=1)
    disponible = models.BooleanField(default=True, verbose_name="¿Está disponible?")
    lugar_citacion = models.CharField(max_length=150, verbose_name="Lugar de citación", blank=True, null=True)
    hora_citacion = models.TimeField(verbose_name="Hora de citación", blank=True, null=True)
    cortejo_cristo = models.BooleanField(default=True, verbose_name="¿Es cortejo de Cristo?", help_text="Marcar si este puesto pertenece al cortejo del Cristo. Desmarcar para Virgen/Palio.")

    acto = models.ForeignKey(Acto, on_delete=models.CASCADE, related_name='puestos_disponibles', verbose_name="Acto al que pertenece")

    tipo_puesto = models.ForeignKey(TipoPuesto, on_delete=models.PROTECT, verbose_name="Tipo de puesto")

    def __str__(self):
        return f"{self.nombre} ({self.tipo_puesto.nombre_tipo}) - {self.acto.nombre}"
    
    @property
    def cantidad_ocupada(self):
        """
        Calcula dinámicamente cuántas papeletas tienen asignado este puesto.
        Filtramos para contar solo las que están realmente asignadas (EMITIDA, RECOGIDA, LEIDA).
        """
        estados_ocupados = ['EMITIDA', 'RECOGIDA', 'LEIDA']
        
        return self.papeletas_asignadas.filter(
            estado_papeleta__in=estados_ocupados
        ).count()

    @property
    def plazas_disponibles(self):
        """
        Retorna el número de huecos libres.
        """
        calculo = self.numero_maximo_asignaciones - self.cantidad_ocupada
        return max(0, calculo)

    @property
    def porcentaje_ocupacion(self):
        """
        Útil para barras de progreso en el Frontend (React)
        """
        if self.numero_maximo_asignaciones == 0:
            return 100
        return int((self.cantidad_ocupada / self.numero_maximo_asignaciones) * 100)
    
# -----------------------------------------------------------------------------
# ENTIDAD: TRAMO
# -----------------------------------------------------------------------------
class Tramo(models.Model):
    class PasoCortejo(models.TextChoices):
        CRISTO = 'CRISTO', 'Paso de Cristo / Misterio'
        VIRGEN = 'VIRGEN', 'Paso de Virgen / Palio'

    nombre = models.CharField(max_length=100, verbose_name="Nombre identificativo", help_text="Ej: Tramo 3 - Senatus")
    numero_orden = models.PositiveIntegerField(verbose_name="Número de orden", help_text="Orden posición en la calle (1, 2, 3...)")

    paso = models.CharField(max_length=20, choices=PasoCortejo.choices, default=PasoCortejo.CRISTO, verbose_name="Cortejo")
    numero_maximo_cirios = models.PositiveIntegerField(verbose_name="Aforo Máximo (Cirios)", default=0, help_text="Número máximo de nazarenos (cirios) que caben en este tramo por inventario o logística.")

    acto = models.ForeignKey(Acto, on_delete=models.CASCADE, related_name='tramos', verbose_name="Acto")

    def __str__(self):
        return f"{self.numero_orden}º Tramo {self.get_paso_display()} - {self.nombre}"

# -----------------------------------------------------------------------------
# ENTIDAD: PAPELETA DE SITIO
# -----------------------------------------------------------------------------
class PapeletaSitio(models.Model):
    class EstadoPapeleta(models.TextChoices):
        NO_SOLICITADA = 'NO_SOLICITADA', 'No solicitada'
        SOLICITADA = 'SOLICITADA', 'Solicitada'
        EMITIDA = 'EMITIDA', 'Emitida'
        RECOGIDA = 'RECOGIDA', 'Recogida'
        LEIDA = 'LEIDA', 'Leída'
        ANULADA = 'ANULADA', 'Anulada'
        NO_ASIGNADA = 'NO_ASIGNADA', 'No asignada'

    class LadoTramo(models.TextChoices):
        IZQUIERDA = 'IZQUIERDA', 'Izquierda'
        DERECHA = 'DERECHA', 'Derecha'
        CENTRO = 'CENTRO', 'Centro (Diputado/Enlace)'

    estado_papeleta = models.CharField(max_length=20, choices=EstadoPapeleta.choices, default=EstadoPapeleta.NO_SOLICITADA, verbose_name="Estado")
    fecha_solicitud = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de solicitud", help_text="Fecha y hora exacta en la que el Hermano realizó la solicitud")
    fecha_emision = models.DateField(null=True, blank=True, verbose_name="Fecha de emisión")
    codigo_verificacion = models.CharField(null=True, blank=True, max_length=100, verbose_name="Código de verificación", help_text="Código único para validad la autenticidad")
    anio = models.PositiveIntegerField(verbose_name="Año")

    hermano = models.ForeignKey(Hermano, on_delete=models.CASCADE, related_name='papeletas', verbose_name="Hermano solicitante")
    acto = models.ForeignKey(Acto, on_delete=models.CASCADE, related_name='papeletas', verbose_name="Acto")
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, related_name="papeletas_asignadas", verbose_name="Puesto asignado", null=True, blank=True)
    tramo = models.ForeignKey(Tramo, on_delete=models.SET_NULL, related_name="nazarenos", verbose_name="Tramo asignado", null=True, blank=True)
    vinculado_a = models.ForeignKey(Hermano, on_delete=models.SET_NULL, null=True, blank=True, related_name='papeletas_vinculadas_origen', verbose_name="Vinculado a (Acompañante)", help_text="Hermano con el que se desea procesionar (perdiendo antigüedad)")

    numero_papeleta = models.PositiveIntegerField(verbose_name="Número de Papeleta/Tramo", null=True, blank=True, help_text="Número asignado tras el reparto de sitios")
    es_solicitud_insignia = models.BooleanField(default=False, null=True, blank=True, verbose_name="¿Es solicitud de insignia?")
    
    orden_en_tramo = models.PositiveIntegerField(
        verbose_name="Orden en el tramo", 
        null=True, 
        blank=True, 
        help_text="Posición relativa dentro del tramo (ej: Pareja 1, Pareja 2...)"
    )
    
    lado = models.CharField(
        max_length=15, 
        choices=LadoTramo.choices, 
        null=True, 
        blank=True, 
        verbose_name="Lado en el tramo"
    )
    
    def __str__(self):
        return f"Papeleta {self.numero_papeleta} - {self.anio})"

    def clean(self):
        """
        Validación personalizada para evitar duplicados activos en MariaDB.
        """
        super().clean()

        estados_inactivos = [
            self.EstadoPapeleta.ANULADA,
            self.EstadoPapeleta.NO_ASIGNADA
        ]

        if self.estado_papeleta not in estados_inactivos:
            papeletas_existentes = PapeletaSitio.objects.filter(
                hermano=self.hermano,
                acto=self.acto
            ).exclude(
                estado_papeleta__in=estados_inactivos
            )

            if self.pk:
                papeletas_existentes = papeletas_existentes.exclude(pk=self.pk)

            if papeletas_existentes.exists():
                raise ValidationError({
                    'hermano': 'Este hermano ya tiene una papeleta activa para este acto. Debe anular la anterior antes de crear una nueva.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Papeleta de Sitio"
        verbose_name_plural = "Papeletas de Sitio"
    
# -----------------------------------------------------------------------------
# ENTIDAD: PREFERENCIA SOLICITUD
# -----------------------------------------------------------------------------
class PreferenciaSolicitud(models.Model):
    papeleta = models.ForeignKey(PapeletaSitio, on_delete=models.CASCADE, related_name="preferencias", verbose_name="Papeleta asociada")
    puesto_solicitado = models.ForeignKey(Puesto, on_delete=models.CASCADE, related_name="solicitudes_preferencia", verbose_name="Puesto solicitado")
    orden_prioridad = models.PositiveIntegerField(verbose_name="Orden de prioridad", help_text="1 para la primera opción, 2 para la segunda, etc.")

    def __str__(self):
        return f"{self.papeleta} - Puesto: {self.puesto_solicitado.nombre} (Prioridad: {self.orden_prioridad})"
    