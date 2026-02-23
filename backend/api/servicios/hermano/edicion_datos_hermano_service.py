from django.db import transaction
from api.models import DatosBancarios
# -----------------------------------------------------------------------------
# SERVICES: PERFIL DEL HERMANO (ÁREA PERSONAL)
# -----------------------------------------------------------------------------
@transaction.atomic
def update_mi_perfil_service(usuario, data_validada):
    """
    Servicio para que el usuario logueado actualice sus propios datos.
    No requiere chequeo de permisos admin porque opera estrictamente 
    sobre el 'usuario' autenticado que hace la petición.
    """
    password = data_validada.pop('password', None)
    areas_data = data_validada.pop('areas_interes', None)
    # datos_bancarios_data = data_validada.pop('datos_bancarios', None)

    for attr, value in data_validada.items():
        setattr(usuario, attr, value)
    
    if password:
        usuario.set_password(password)
        
    usuario.save()

    if areas_data is not None:
        usuario.areas_interes.set(areas_data)

    # 5. Tratamiento para la relación One-to-One (Datos Bancarios)
    # if datos_bancarios_data is not None:
    #     DatosBancarios.objects.update_or_create(
    #         hermano=usuario,
    #         defaults=datos_bancarios_data
    #     )

    return usuario