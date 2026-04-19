from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import QueryDict
from django.utils import timezone
from django.shortcuts import get_object_or_404

from api.models import Acto

# -----------------------------------------------------------------------------
# SERVICES: CREAR ACTO
# -----------------------------------------------------------------------------
@transaction.atomic
def crear_acto_service(usuario_solicitante, data_validada):
    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para crear actos. Se requiere ser Administrador.")

    nombre = data_validada.get("nombre")
    fecha = data_validada.get("fecha")

    if isinstance(nombre, str):
        nombre = nombre.strip()
        data_validada["nombre"] = nombre

    if nombre and fecha:
        if Acto.objects.filter(nombre=nombre, fecha__date=fecha.date()).exists():
            raise ValidationError({
                "non_field_errors": [f"Ya existe un acto llamado '{nombre}' para la fecha {fecha.strftime('%d/%m/%Y')}."]
            })

    nuevo_acto = Acto.objects.create(**data_validada)

    return nuevo_acto


# -----------------------------------------------------------------------------
# SERVICES: ACTUALIZAR ACTO
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