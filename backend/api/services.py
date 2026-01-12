from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from .models import Acto, Puesto, TipoPuesto

# -----------------------------------------------------------------------------
# SERVICES: ACTO
# -----------------------------------------------------------------------------

def _validar_fecha_futura_anio_actual(fecha_acto):
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

def create_acto_service(usuario, data_validada):
    """
    Servicio para la gestión de creación de actos.
    
    Args:
        usuario (User): El usuario que realiza la petición (request.user).
        data_validada (dict): Diccionario con datos limpios provenientes del serializer.
        
    Returns:
        Acto: La instancia del objeto Acto creado.
    
    Raises:
        PermissionDenied: Si el usuario no es admin.
        ValidationError: Si la fecha no corresponde al año actual.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para crear actos. Contacta con Secretaría.")
    
    nombre = data_validada.get('nombre')
    fecha_acto = data_validada.get('fecha')


    _validar_fecha_futura_anio_actual(fecha_acto)
    
    if Acto.objects.filter(nombre=nombre, fecha__date=fecha_acto.date()).exists():
        raise ValidationError({
            "non_field_errors": [f"Ya existe un acto con el nombre '{nombre}' para el día {fecha_acto.date().strftime('%d/%m/%Y')}."]
        })
    
    acto = Acto.objects.create(**data_validada)
    return acto


def update_acto_service(usuario, acto_id, data_validada):
    """
    Servicio para la actualización de un acto existente.
    
    Args:
        usuario (User): Usuario que realiza la petición.
        acto_id (int): ID del acto a actualizar.
        data_validada (dict): Datos limpios del serializer.
        
    Returns:
        Acto: La instancia actualizada.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar actos. Contacta con Secretaría.")
    
    acto = get_object_or_404(Acto, pk=acto_id)

    if 'tipo_acto' in data_validada:
        nuevo_tipo = data_validada['tipo_acto']

        if nuevo_tipo != acto.tipo_acto:
            if acto.puestos_disponibles.exists():
                raise ValidationError({
                    "tipo_acto": "No se puede cambiar el 'Tipo de Acto' porque ya existen puestos configurados para este evento. Elimine los puestos primero si desea cambiar el tipo."
                })

    nueva_fecha_entera = data_validada.get('fecha', acto.fecha)
    nuevo_nombre = data_validada.get('nombre', acto.nombre)

    _validar_fecha_futura_anio_actual(nueva_fecha_entera)

    nueva_fecha_dia = nueva_fecha_entera.date()

    existe_duplicado = Acto.objects.filter(
        nombre = nuevo_nombre,
        fecha__date = nueva_fecha_dia
    ).exclude(pk=acto_id).exists()

    if existe_duplicado:
        raise ValidationError({"non_field_errors": [f"Ya existe otro acto con el nombre '{nuevo_nombre}' para el día {nueva_fecha_dia.strftime('%d/%m/%Y')}."]})
        
    for attr, value in data_validada.items():
        setattr(acto, attr, value)

    acto.save()
    return acto

# -----------------------------------------------------------------------------
# SERVICES: PUESTO
# -----------------------------------------------------------------------------
def create_puesto_service(usuario, data_validada):
    """
    Servicio para la creación de puestos en un acto.
    
    Args:
        usuario (User): Usuario que realiza la petición.
        data_validada (dict): Datos limpios del serializer.
        
    Returns:
        Puesto: Instancia del puesto creado.
        
    Raises:
        PermissionDenied: Si el usuario no es administrador.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para crear puestos. Acción reservada a administradores.")
    
    acto = data_validada.get('acto')

    if acto and not acto.tipo_acto.requiere_papeleta:
        raise ValidationError({
            "acto": f"El acto '{acto.nombre}' es de tipo '{acto.tipo_acto.get_tipo_display()}' y no admite la creación de puestos ni papeletas de sitio."
        })
    
    puesto = Puesto.objects.create(**data_validada)

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