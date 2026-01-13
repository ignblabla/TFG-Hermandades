from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
    
class AreaInteres(models.Model):
    class NombreArea(models.TextChoices):
        CARIDAD = 'CARIDAD', 'Caridad'
        CULTOS_FORMACION = 'CULTOS_FORMACION', 'Cultos y Formación'
        JUVENTUD = 'JUVENTUD', 'Juventud'
        PATRIMONIO = 'PATRIMONIO', 'Patrimonio'
        PRIOSTIA = 'PRIOSTIA', 'Priostía'
        DIPUTACION_MAYOR_GOBIERNO = 'DIPUTACION_MAYOR_GOBIERNO', 'Diputación Mayor de Gobierno'
        COSTALEROS = 'COSTALEROS', 'Costaleros'
        ACOLITOS = 'ACÓLITOS', 'Acólitos'

    nombre_area = models.CharField(max_length=50, choices=NombreArea.choices, unique=True, verbose_name="Nombre del área")

    def __str__(self):
        return self.get_nombre_area_display()
    
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
    

class Hermano(AbstractUser):
    class Genero(models.TextChoices):
        MASCULINO = 'MASCULINO', 'Masculino'
        FEMENINO = 'FEMENINO', 'Femenino'

    class EstadoCivil(models.TextChoices):
        SOLTERO = 'SOLTERO', 'Soltero'
        SEPARADO = 'SEPARADO', 'Separado'
        CASADO = 'CASADO', 'Casado'
        VIUDO = 'VIUDO', 'Viudo'

    telefono_validator = RegexValidator(
        regex=r'^\d{9}$',
        message="El número de teléfono debe tener exactamente 9 dígitos numéricos."
    )

    cp_validator = RegexValidator(
        regex=r'^\d{5}$',
        message="El código postal debe tener exactamente 5 dígitos numéricos."
    )

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
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
    REQUIRED_FIELDS = ['nombre', 'primer_apellido', 'segundo_apellido', 'email', 'username', 'telefono', 'estado_civil']

    def __str__(self):
        return f"{self.dni} - {self.nombre} {self.primer_apellido}"
    
    def clean(self):
        super().clean()
        if self.fecha_nacimiento and self.fecha_bautismo:
            if self.fecha_bautismo < self.fecha_nacimiento:
                raise ValidationError({
                    'fecha_bautismo': 'La fecha de bautismo no puede ser anterior a la fecha de nacimiento'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.username:
            self.username = self.dni
        super().save(*args, **kwargs)


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
    

class Acto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del acto")
    descripcion = models.TextField(verbose_name="Descripción", blank=True, null=True)
    fecha = models.DateTimeField(verbose_name="Fecha y hora")

    tipo_acto = models.ForeignKey(TipoActo, on_delete=models.PROTECT, verbose_name="Tipo de acto", related_name="actos")

    inicio_solicitud = models.DateTimeField(verbose_name="Inicio solicitud papeletas", blank=True, null=True, help_text="Fecha y hora de apertura de solicitudes (solo si requiere papeleta)")
    fin_solicitud = models.DateTimeField(verbose_name="Fin solicitud papeletas", blank=True, null=True, help_text="Fecha y hora de cierre de solicitudes (solo si requiere papeleta)")


    def __str__(self):
        return f"{self.nombre} ({self.fecha.year})"


    
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
        verbose_name="¿Es Insignia?",
        help_text="Marcar si este tipo de puesto se considera una insignia, vara o enser que requiere asignación específica."
    )

    def __str__(self):
        return self.nombre_tipo


class Puesto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del puesto")
    numero_maximo_asignaciones = models.PositiveIntegerField(verbose_name="Número máximo de asignaciones", default=1)
    disponible = models.BooleanField(default=True, verbose_name="¿Está disponible?")
    lugar_citacion = models.CharField(max_length=150, verbose_name="Lugar de citación", blank=True, null=True)
    hora_citacion = models.TimeField(verbose_name="Hora de citación", blank=True, null=True)

    acto = models.ForeignKey(Acto, on_delete=models.CASCADE, related_name='puestos_disponibles', verbose_name="Acto al que pertenece")

    tipo_puesto = models.ForeignKey(TipoPuesto, on_delete=models.PROTECT, verbose_name="Tipo de puesto")

    def __str__(self):
        return f"{self.nombre} ({self.tipo_puesto.nombre_tipo}) - {self.acto.nombre}"
    

class PapeletaSitio(models.Model):
    class EstadoPapeleta(models.TextChoices):
        NO_SOLICITADA = 'NO_SOLICITADA', 'No solicitada'
        SOLICITADA = 'SOLICITADA', 'Solicitada'
        EMITIDA = 'EMITIDA', 'Emitida'
        RECOGIDA = 'RECOGIDA', 'Recogida'
        LEIDA = 'LEIDA', 'Leída'
        ANULADA = 'ANULADA', 'Anulada'

    estado_papeleta = models.CharField(max_length=20, choices=EstadoPapeleta.choices, default=EstadoPapeleta.NO_SOLICITADA, verbose_name="Estado")
    fecha_emision = models.DateField(auto_now_add=True, verbose_name="Fecha de emisión")
    codigo_verificacion = models.CharField(max_length=100, verbose_name="Código de verificación", help_text="Código único para validad la autenticidad")
    anio = models.PositiveIntegerField(verbose_name="Año")

    hermano = models.ForeignKey(Hermano, on_delete=models.CASCADE, related_name='papeletas', verbose_name="Hermano solicitante")
    acto = models.ForeignKey(Acto, on_delete=models.CASCADE, related_name='papeletas', verbose_name="Acto")
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, related_name="papeletas_asignadas", verbose_name="Puesto asignado", null=True, blank=True)

    numero_papeleta = models.PositiveIntegerField(verbose_name="Número de Papeleta/Tramo", null=True, blank=True, help_text="Número asignado tras el reparto de sitios")

    def __str__(self):
        return f"Papeleta {self.numero_papeleta} - {self.anio})"
    

class PreferenciaSolicitud(models.Model):
    papeleta = models.ForeignKey(PapeletaSitio, on_delete=models.CASCADE, related_name="preferencias", verbose_name="Papeleta asociada")
    puesto_solicitado = models.ForeignKey(Puesto, on_delete=models.CASCADE, related_name="solicitudes_preferencia", verbose_name="Puesto solicitado")
    orden_prioridad = models.PositiveIntegerField(verbose_name="Orden de prioridad", help_text="1 para la primera opción, 2 para la segunda, etc.")

    def __str__(self):
        return f"{self.papeleta} - Puesto: {self.puesto_solicitado.nombre} (Prioridad: {self.orden_prioridad})"