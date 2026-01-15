from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Max
from ..models import Cuota, DatosBancarios, Hermano
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

    datos_bancarios_data = data_validada.pop('datos_bancarios', None)

    data_validada['estado_hermano'] = User.EstadoHermano.PENDIENTE_INGRESO
    data_validada['numero_registro'] = None
    data_validada['esAdmin'] = False
    data_validada['fecha_ingreso_corporacion'] = None
    data_validada['fecha_baja_corporacion'] = None

    hermano = User(**data_validada)
    hermano.set_password(password)
    hermano.save()

    if areas_interes:
        hermano.areas_interes.set(areas_interes)

    if datos_bancarios_data:
        # Creamos la instancia vinculada usando el hermano recién creado
        DatosBancarios.objects.create(hermano=hermano, **datos_bancarios_data)

    anio_actual = timezone.now().year
    Cuota.objects.create(
        hermano=hermano,
        anio=anio_actual,
        tipo=Cuota.TipoCuota.INGRESO,
        descripcion=f"Cuota de Ingreso - Solicitud {anio_actual}",
        importe=30.00,  # Importe fijo según lógica de negocio
        estado=Cuota.EstadoCuota.PENDIENTE,
        metodo_pago=Cuota.MetodoPago.DOMICILIACION # Asumimos domiciliación por defecto al alta
    )

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