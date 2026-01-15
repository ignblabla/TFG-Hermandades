from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Max
from ..models import Hermano
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

# -----------------------------------------------------------------------------
# SERVICES: GESTIÓN DE HERMANOS (USUARIOS)
# -----------------------------------------------------------------------------

@transaction.atomic
def create_hermano_solicitud_service(data_validada):
    password = data_validada.pop('password')
    areas_interes = data_validada.pop('areas_interes', [])

    data_validada['estado_hermano'] = User.EstadoHermano.PENDIENTE_INGRESO
    data_validada['estado_pago'] = User.EstadoPago.PENDIENTE
    data_validada['numero_registro'] = None
    data_validada['esAdmin'] = False
    data_validada['fecha_ingreso_corporacion'] = None
    data_validada['fecha_baja_corporacion'] = None

    hermano = User(**data_validada)
    hermano.set_password(password)
    hermano.save()

    if areas_interes:
        hermano.areas_interes.set(areas_interes)

    return hermano


@transaction.atomic
def activar_hermano_service(admin_user, hermano_id):
    if not getattr(admin_user, 'esAdmin', False):
        raise PermissionDenied("Solo los administradores pueden dar de alta a un hermano.")
    
    hermano = get_object_or_404(User, pk=hermano_id)

    if hermano.estado_hermano == User.EstadoHermano.ALTA:
        raise ValidationError({"estado_hermano": "El hermano ya está de alta."})
    
    max_num = User.objects.aggregate(models.Max('numero_registro'))['numero_registro__max']
    siguiente_numero = 1 if max_num is None else max_num + 1

    hermano.estado_hermano = User.EstadoHermano.ALTA
    hermano.numero_registro = siguiente_numero

    hermano.fecha_ingreso_corporacion = timezone.now().date()

    hermano.fecha_baja_corporacion = None

    hermano.estado_pago = User.EstadoPago.PAGADO

    hermano.save()
    return hermano