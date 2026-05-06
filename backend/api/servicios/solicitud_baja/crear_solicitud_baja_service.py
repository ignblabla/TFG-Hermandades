from django.core.exceptions import ValidationError

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