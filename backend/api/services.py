from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Acto

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
    
    fecha_acto = data_validada.get('fecha')

    anio_actual = timezone.now().year

    if fecha_acto.year != anio_actual:
        raise ValidationError({"fecha": f"Solo se permite crear actos para el año en curso ({anio_actual})."})
    
    acto = Acto.objects.create(**data_validada)

    return acto