from django.db import transaction
from django.core.exceptions import PermissionDenied
from api.models import Comunicado, CuerpoPertenencia


class CreacionComunicadoService:

    @transaction.atomic
    def create_comunicado_service(self, usuario, data_validada):
        """
        Servicio para crear un comunicado aplicando reglas de negocio y permisos.
        
        Reglas:
        1. Solo Admins o miembros de Junta de Gobierno pueden crear comunicados.
        2. El autor es el usuario logueado.
        3. Se deben gestionar las áreas de interés (M2M). Si no se asignan,
        se asume estado 'borrador' (sin destinatarios).
        """
        es_admin = getattr(usuario, 'esAdmin', False)
        es_junta = usuario.cuerpos.filter(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        ).exists()

        if not (es_admin or es_junta):
            raise PermissionDenied(
                "No tienes permisos para emitir comunicados. "
                "Solo disponible para Administradores o Junta de Gobierno."
            )
        
        areas = data_validada.pop('areas_interes', [])

        comunicado = Comunicado.objects.create(
            autor=usuario,
            **data_validada
        )

        if areas:
            comunicado.areas_interes.set(areas)
        else:
            pass

        return comunicado