from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db import transaction

from rest_framework.exceptions import ValidationError

from api.models import Hermano, SolicitudBaja


def crear_solicitud_baja(usuario, motivo=None):
    """
    Servicio para crear una solicitud de baja validando las reglas de negocio.
    """
    if not usuario or not usuario.is_authenticated:
        raise ValidationError("El usuario debe estar autenticado para realizar esta acción.")

    if usuario.estado_hermano != Hermano.EstadoHermano.ALTA:
        raise ValidationError("Solo los hermanos en estado de ALTA pueden solicitar la baja.")

    tiene_solicitud_pendiente = SolicitudBaja.objects.filter(
        hermano=usuario, 
        estado=SolicitudBaja.EstadoSolicitud.PENDIENTE
    ).exists()
    
    if tiene_solicitud_pendiente:
        raise ValidationError("Ya tienes una solicitud de baja en curso pendiente de revisión.")

    solicitud = SolicitudBaja(
        hermano=usuario,
        motivo=motivo
    )
    solicitud.save()
    
    return solicitud


def obtener_solicitudes_baja_admin(usuario):
    """
    Servicio para obtener el listado de solicitudes de baja.
    Solo accesible para administradores.
    """
    if getattr(usuario, 'esAdmin', False) is False:
        raise PermissionDenied("No tiene permisos de administrador para visualizar las solicitudes de baja.")

    return SolicitudBaja.objects.select_related('hermano').all().order_by('-fecha_solicitud')



@staticmethod
@transaction.atomic
def resolver_solicitud(solicitud: SolicitudBaja, accion: str, usuario: Hermano) -> SolicitudBaja:
    """
    Resuelve una solicitud de baja (ACEPTAR o DENEGAR).
    """
    if getattr(usuario, 'esAdmin', False) is False:
        raise PermissionDenied("No tiene permisos de administrador para resolver las solicitudes de baja.")

    if solicitud.estado != SolicitudBaja.EstadoSolicitud.PENDIENTE:
        raise ValidationError("Solo se pueden resolver solicitudes que estén pendientes.")

    if accion == 'ACEPTAR':
        solicitud.estado = SolicitudBaja.EstadoSolicitud.APROBADA
        solicitud.fecha_resolucion = timezone.now()

        hermano = solicitud.hermano
        hermano.is_active = False
        hermano.estado_hermano = Hermano.EstadoHermano.BAJA
        hermano.fecha_baja_corporacion = timezone.now().date()
        hermano.save()
        
    elif accion == 'DENEGAR':
        solicitud.estado = SolicitudBaja.EstadoSolicitud.DENEGADA
        solicitud.fecha_resolucion = timezone.now()
        
    else:
        raise ValidationError("Acción no válida. Las opciones permitidas son 'ACEPTAR' o 'DENEGAR'.")

    solicitud.save()
    return solicitud