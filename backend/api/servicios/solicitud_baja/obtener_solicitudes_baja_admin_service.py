from django.core.exceptions import PermissionDenied

from api.models import SolicitudBaja



def obtener_solicitudes_baja_admin(usuario):
    """
    Servicio para obtener el listado de solicitudes de baja.
    Solo accesible para administradores.
    """
    if getattr(usuario, 'esAdmin', False) is False:
        raise PermissionDenied("No tiene permisos de administrador para visualizar las solicitudes de baja.")

    return SolicitudBaja.objects.select_related('hermano').all().order_by('-fecha_solicitud')