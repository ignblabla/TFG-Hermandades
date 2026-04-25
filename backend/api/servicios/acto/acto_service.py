from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import QueryDict
from django.utils import timezone
from django.shortcuts import get_object_or_404

from api.models import Acto

# -----------------------------------------------------------------------------
# SERVICES: CREAR ACTO
# -----------------------------------------------------------------------------
def crear_acto_service(usuario_solicitante, data_validada: dict) -> Acto:
    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para crear actos. Se requiere ser Administrador.")

    nuevo_acto = Acto.objects.create(**data_validada)

    return nuevo_acto

# -----------------------------------------------------------------------------
# SERVICES: ACTUALIZAR ACTO
# -----------------------------------------------------------------------------
@transaction.atomic
def update_acto_service(usuario, acto_id, data_validada):
    """
    Actualiza un acto delegando la integridad al modelo.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar actos.")
    
    acto = get_object_or_404(Acto, pk=acto_id)

    nuevo_tipo = data_validada.get('tipo_acto')
    if nuevo_tipo and nuevo_tipo != acto.tipo_acto:
        if acto.puestos_disponibles.exists():
            raise ValidationError({
                "tipo_acto": "No se puede cambiar el tipo de acto porque ya tiene puestos asignados."
            })

    for attr, value in data_validada.items():
        setattr(acto, attr, value)

    acto.save()
    
    return acto

# -----------------------------------------------------------------------------
# SERVICES: LISTAR ACTOS
# -----------------------------------------------------------------------------
class ActoService:
    @staticmethod
    def get_todos_los_actos():
        """
        Devuelve el queryset con todos los actos, ordenados por fecha
        para garantizar una paginación predecible y consistente.
        """
        return Acto.objects.all().order_by('-fecha')