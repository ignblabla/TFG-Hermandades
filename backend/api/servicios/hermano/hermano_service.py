from rest_framework.exceptions import PermissionDenied

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction

from api.models import DatosBancarios

User = get_user_model()

def get_listado_hermanos_service(usuario_solicitante):
    """
    Retorna el listado completo de hermanos.
    Regla de Negocio: Solo accesible por administradores.
    """
    if not getattr(usuario_solicitante, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para visualizar el listado de hermanos.")
    
    hermanos = User.objects.all().order_by('numero_registro')
    return hermanos



@transaction.atomic
def update_hermano_por_admin_service(usuario_solicitante, hermano_id, data_validada):
    if not getattr(usuario_solicitante, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar los datos de otros hermanos.")
    
    hermano = get_object_or_404(User, pk=hermano_id)

    for attr, value in data_validada.items():
        if attr == 'password':
            if value:
                hermano.set_password(value)
        else:
            setattr(hermano, attr, value)
    
    hermano.save()
    return hermano



@transaction.atomic
def update_mi_perfil_service(usuario, data_validada):
    """
    Servicio para que el usuario logueado actualice sus propios datos.
    No requiere chequeo de permisos admin porque opera estrictamente 
    sobre el 'usuario' autenticado que hace la petición.
    """
    password = data_validada.pop('password', None)
    areas_data = data_validada.pop('areas_interes', None)
    datos_bancarios_data = data_validada.pop('datos_bancarios', None)

    for attr, value in data_validada.items():
        setattr(usuario, attr, value)
    
    if password:
        usuario.set_password(password)
        
    usuario.save()

    if areas_data is not None:
        usuario.areas_interes.set(areas_data)

    if datos_bancarios_data is not None:
        DatosBancarios.objects.update_or_create(
            hermano=usuario,
            defaults=datos_bancarios_data
        )

    return usuario