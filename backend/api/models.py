from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class Note(models.Model):
    title = models.CharField(max_length=100, verbose_name="Título")
    content = models.TextField(verbose_name="Contenido")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="notes",
        verbose_name="Autor"
    )

    def __str__(self):
        return self.title
    

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

    first_name = None
    last_name = None

    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['nombre', 'primer_apellido', 'segundo_apellido', 'email']

    def __str__(self):
        return f"{self.dni} - {self.nombre} {self.primer_apellido}"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.dni
        super().save(*args, **kwargs)