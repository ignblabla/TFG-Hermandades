from django.http import QueryDict
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from .models import Acto, PapeletaSitio, Puesto, TipoActo, TipoPuesto
from django.db import transaction
from django.contrib.auth import get_user_model
# from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()

# -----------------------------------------------------------------------------
# SERVICES: PUESTO
# -----------------------------------------------------------------------------
def create_puesto_service(usuario, data_validada):
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para crear puestos.")
    
    acto = data_validada.get('acto')
    nombre = data_validada.get('nombre')

    # Regla de Negocio: Solo actos que requieren papeleta pueden tener puestos
    if not acto.tipo_acto.requiere_papeleta:
        raise ValidationError({
            "acto": f"El acto '{acto.nombre}' es de tipo '{acto.tipo_acto.get_tipo_display()}' y no admite puestos."
        })
    
    if Puesto.objects.filter(acto=acto, nombre=nombre).exists():
        raise ValidationError({"nombre": [f"Ya existe un puesto con el nombre '{nombre}' en este acto."]})
    
    puesto = Puesto.objects.create(**data_validada)
    return puesto


def update_puesto_service(usuario, puesto_id, data_validada):
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar puestos.")

    puesto = get_object_or_404(Puesto, pk=puesto_id)
    acto = puesto.acto
    
    if not acto.tipo_acto.requiere_papeleta:
        raise ValidationError({"acto": "Este acto ya no admite la gestión de puestos."})
    
    nuevo_nombre = data_validada.get('nombre', puesto.nombre)

    if Puesto.objects.filter(acto=acto, nombre=nuevo_nombre).exclude(pk=puesto_id).exists():
        raise ValidationError({"nombre": [f"Ya existe un puesto con el nombre '{nuevo_nombre}' en este acto."]})
    
    for attr, value in data_validada.items():
        setattr(puesto, attr, value)

    puesto.save()
    return puesto

# -----------------------------------------------------------------------------
# SERVICES: TIPO DE PUESTO
# -----------------------------------------------------------------------------
def get_tipos_puesto_service():
    """
    Servicio para recuperar el catálogo completo de tipos de puestos.
    Puede incluir lógica de filtrado si fuera necesaria en el futuro.
    """
    return TipoPuesto.objects.all()


# -----------------------------------------------------------------------------
# SERVICES: TIPO DE ACTO
# -----------------------------------------------------------------------------
def get_tipos_acto_service():
    """Retorna todos los tipos de actos disponibles"""
    return TipoActo.objects.all()

# -----------------------------------------------------------------------------
# SERVICES: PANEL DE ADMINISTRADOR
# -----------------------------------------------------------------------------
def get_listado_hermanos_service(usuario_solicitante):
    """
    Retorna el listado completo de hermanos.
    Regla de Negocio: Solo accesible por administradores.
    """
    if not getattr(usuario_solicitante, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para visualizar el listado de hermanos.")
    
    hermanos = User.objects.all().order_by('numero_registro')
    return hermanos

@transaction.atomic
def update_hermano_por_admin_service(usuario_solicitante, hermano_id, data_validada):
    if not getattr(usuario_solicitante, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar los datos de otros hermanos.")
    
    hermano = get_object_or_404(User, pk=hermano_id)

    for attr, value in data_validada.items():
        if attr == 'password':
            if value:
                hermano.set_password(value)
        else:
            setattr(hermano, attr, value)
    
    hermano.save()
    return hermano