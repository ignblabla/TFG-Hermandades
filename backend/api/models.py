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

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=100, verbose_name = "Nombre")
    primer_apellido = models.CharField(max_length=100, verbose_name = "Primer apellido")
    segundo_apellido = models.CharField(max_length=100, verbose_name = "Segundo apellido")
    dni = models.CharField(max_length=9, unique=True, verbose_name = "DNI")
    # fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")

    telefono_validator = RegexValidator(
        regex=r'^\d{9}$',
        message="El número de teléfono debe tener exactamente 9 dígitos numéricos."
    )

    telefono = models.CharField(validators=[telefono_validator], max_length=9, verbose_name="Teléfono")
    genero = models.CharField(max_length=10, choices=Genero.choices, default=Genero.MASCULINO, verbose_name="Género")

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