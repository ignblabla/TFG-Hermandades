from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from .models import Acto, Puesto, TipoActo, TipoPuesto
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import F

User = get_user_model()

# -----------------------------------------------------------------------------
# SERVICES: ACTO
# -----------------------------------------------------------------------------

def _validar_integridad_fechas_acto(fecha_acto):
    """
    Método auxiliar (privado) para reutilizar la lógica de validación temporal.
    Valida:
    1. Que la fecha sea futura (fecha y hora > ahora).
    2. Que la fecha esté dentro del año actual.
    """

    ahora = timezone.now()

    if fecha_acto.year != ahora.year:
        raise ValidationError({
            "fecha": f"Solo se permite programar actos para el año en curso ({ahora.year})."
        })
    
    if fecha_acto <= ahora:
        raise ValidationError({
            "fecha": "La fecha y hora del acto deben ser posteriores al momento actual."
        })
    

def _procesar_fechas_solicitud_papeleta(tipo_acto, fecha_acto, inicio_solicitud, fin_solicitud):
    """
    Aplica la lógica de negocio estricta para las fechas de solicitud de papeleta.
    Retorna una tupla (inicio_procesado, fin_procesado).
    """

    if not tipo_acto.requiere_papeleta:
        return None, None
    
    else:
        if not inicio_solicitud:
            raise ValidationError({"inicio_solicitud": "Este tipo de acto requiere especificar fecha de inicio de solicitud."})
        if not fin_solicitud:
            raise ValidationError({"fin_solicitud": "Este tipo de acto requiere especificar fecha de fin de solicitud."})
        
        if inicio_solicitud >= fin_solicitud:
            raise ValidationError({"fin_solicitud": "La fecha de fin de solicitud debe ser posterior a la fecha de inicio."})
        
        if fecha_acto and fin_solicitud >= fecha_acto:
            raise ValidationError({"fin_solicitud": "El periodo de solicitud debe finalizar antes de la fecha de celebración del acto."})
        
        return inicio_solicitud, fin_solicitud


@transaction.atomic
def create_acto_service(usuario, data_validada):
    """
    Crea un acto aplicando toda la lógica de negocio.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para crear actos. Contacta con Secretaría.")
    
    nombre = data_validada.get('nombre')
    fecha_acto = data_validada.get('fecha')
    tipo_acto = data_validada.get('tipo_acto')

    raw_inicio = data_validada.get('inicio_solicitud')
    raw_fin = data_validada.get('fin_solicitud')

    _validar_integridad_fechas_acto(fecha_acto)

    if Acto.objects.filter(nombre=nombre, fecha__date=fecha_acto.date()).exists():
        raise ValidationError({"non_field_errors": [f"Ya existe un acto con el nombre '{nombre}' para el día {fecha_acto.date().strftime('%d/%m/%Y')}."]})
    

    inicio_final, fin_final = _procesar_fechas_solicitud_papeleta(tipo_acto, fecha_acto, raw_inicio, raw_fin)

    data_validada['inicio_solicitud'] = inicio_final
    data_validada['fin_solicitud'] = fin_final

    acto = Acto.objects.create(**data_validada)
    return acto


@transaction.atomic
def update_acto_service(usuario, acto_id, data_validada):
    """
    Actualiza un acto, asegurando la coherencia del estado final.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar actos. Contacta con Secretaría.")
    
    acto = get_object_or_404(Acto, pk=acto_id)

    nuevo_tipo = data_validada.get('tipo_acto', acto.tipo_acto)

    if nuevo_tipo != acto.tipo_acto:
        if acto.puestos_disponibles.exists():
            raise ValidationError({"tipo_acto": "No se puede cambiar el tipo de acto porque ya tiene puestos asignados. Elimínelos primero."})
        
    nueva_fecha = data_validada.get('fecha', acto.fecha)
    nuevo_nombre = data_validada.get('nombre', acto.nombre)

    if 'fecha' in data_validada:
        _validar_integridad_fechas_acto(nueva_fecha)

    existe_duplicado = Acto.objects.filter(
        nombre = nuevo_nombre,
        fecha__date = nueva_fecha.date()
    ).exclude(pk=acto_id).exists()

    if existe_duplicado:
        raise ValidationError({"non_field_errors": [f"Ya existe otro acto con ese nombre en la fecha indicada."]})
    
    inicio_input = data_validada.get('inicio_solicitud', acto.inicio_solicitud)
    fin_input = data_validada.get('fin_solicitud', acto.fin_solicitud)

    inicio_final, fin_final = _procesar_fechas_solicitud_papeleta(
        nuevo_tipo, nueva_fecha, inicio_input, fin_input
    )

    data_validada['inicio_solicitud'] = inicio_final
    data_validada['fin_solicitud'] = fin_final

    for attr, value in data_validada.items():
        setattr(acto, attr, value)

    acto.save()
    return acto

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
# SERVICES DEL PANEL DE ADMINISTRACIÓN
# -----------------------------------------------------------------------------
def get_todos_hermanos_service(usuario_solicitante):
    if not getattr(usuario_solicitante, 'esAdmin', False):
        raise PermissionDenied("Acceso denegado. Se requieren permisos de Administrador para consultar el censo.")
    
    return User.objects.all().order_by(F('numero_registro').asc(nulls_last=True))