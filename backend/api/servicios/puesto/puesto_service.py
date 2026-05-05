from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, QuerySet

from api.models import Puesto

User = get_user_model()

# -----------------------------------------------------------------------------
# SERVICES: PUESTO
# -----------------------------------------------------------------------------
def create_puesto_service(usuario, data_validada):
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para crear puestos.")
    
    acto = data_validada.get('acto')
    nombre = data_validada.get('nombre')

    if not acto.tipo_acto.requiere_papeleta:
        raise ValidationError({
            "acto": f"El acto '{acto.nombre}' es de tipo '{acto.tipo_acto.get_tipo_display()}' y no admite puestos."
        })

    hoy = timezone.now().date()
    fecha_inicio = acto.inicio_solicitud.date() if hasattr(acto.inicio_solicitud, 'date') else acto.inicio_solicitud

    if not fecha_inicio or fecha_inicio <= hoy:
        raise ValidationError({
            "acto": "No se pueden crear puestos para actos cuyo periodo de solicitud ya ha comenzado, es en el pasado, o no tienen fecha definida."
        })
    
    if Puesto.objects.filter(acto=acto, nombre=nombre).exists():
        raise ValidationError({"nombre": [f"Ya existe un puesto con el nombre '{nombre}' en este acto."]})
    
    puesto = Puesto.objects.create(**data_validada)
    return puesto



def update_puesto_service(usuario, puesto_id, data_validada):
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar puestos.")

    puesto = get_object_or_404(Puesto, pk=puesto_id)

    nuevo_acto = data_validada.get('acto')
    if nuevo_acto and nuevo_acto != puesto.acto:
        raise ValidationError({
            "acto": "No está permitido cambiar el acto asociado a un puesto una vez que ha sido creado."
        })

    acto = puesto.acto

    hoy = timezone.now().date()

    fecha_inicio = acto.inicio_solicitud 

    if not fecha_inicio or fecha_inicio.date() <= hoy:
        raise ValidationError({
            "acto": "No se pueden actualizar puestos para actos cuyo periodo de solicitud ya ha comenzado, es en el pasado, o no tienen fecha definida."
        })

    if not acto.tipo_acto.requiere_papeleta:
        raise ValidationError({"acto": "Este acto ya no admite la gestión de puestos."})
    
    nuevo_nombre = data_validada.get('nombre', puesto.nombre)

    if Puesto.objects.filter(acto=acto, nombre=nuevo_nombre).exclude(pk=puesto_id).exists():
        raise ValidationError({"nombre": [f"Ya existe un puesto con el nombre '{nuevo_nombre}' en este acto."]})

    data_validada.pop('acto', None)

    for attr, value in data_validada.items():
        setattr(puesto, attr, value)

    puesto.save()
    return puesto



def obtener_puestos_por_acto(acto_id: int) -> QuerySet[Puesto]:
    """
    Retorna un queryset con todos los puestos (tanto insignias como no insignias) 
    para un acto determinado.
    """
    return Puesto.objects.select_related(
        'tipo_puesto', 
        'acto', 
        'acto__tipo_acto'
    ).filter(
        acto_id=acto_id
    )



def obtener_resumen_puestos_acto(acto_id: int) -> dict:
    """
    Retorna el total de puestos distintos disponibles en un acto,
    desglosado también por cortejo de Cristo y Virgen.
    Realiza una sola consulta SQL agrupada para mayor eficiencia.
    """
    resumen = Puesto.objects.filter(acto_id=acto_id, disponible=True).aggregate(
        total_puestos=Count('id'),
        total_cristo=Count('id', filter=Q(cortejo_cristo=True)),
        total_virgen=Count('id', filter=Q(cortejo_cristo=False))
    )
    
    return {
        "total_puestos": resumen['total_puestos'] or 0,
        "total_cristo": resumen['total_cristo'] or 0,
        "total_virgen": resumen['total_virgen'] or 0,
    }



def delete_puesto_service(usuario, puesto_id):
    """
    Servicio para eliminar un puesto.
    Solo accesible para administradores y si la fecha de inicio de solicitud del acto no ha comenzado.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para eliminar puestos.")

    puesto = get_object_or_404(Puesto, pk=puesto_id)
    acto = puesto.acto

    hoy = timezone.now().date()
    fecha_inicio = acto.inicio_solicitud 

    if fecha_inicio and fecha_inicio.date() <= hoy:
        raise ValidationError({
            "acto": "No se puede eliminar el puesto porque el periodo de solicitud para este acto ya ha comenzado."
        })

    puesto.delete()
    
    return True