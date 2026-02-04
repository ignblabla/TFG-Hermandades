from django.db import transaction
from django.core.exceptions import PermissionDenied
from api.models import Comunicado, CuerpoPertenencia


class ComunicadoService:

    def _verificar_permisos(self, usuario):
        """Helper interno para validar permisos de Admin o Junta."""
        es_admin = getattr(usuario, 'esAdmin', False)
        es_junta = usuario.cuerpos.filter(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        ).exists()

        if not (es_admin or es_junta):
            raise PermissionDenied("No tienes permisos para gestionar comunicados.")
        

    @transaction.atomic
    def create_comunicado(self, usuario, data_validada):
        self._verificar_permisos(usuario)
        
        areas = data_validada.pop('areas_interes', [])
        comunicado = Comunicado.objects.create(autor=usuario, **data_validada)
        
        if areas:
            comunicado.areas_interes.set(areas)
        return comunicado
    

    @transaction.atomic
    def update_comunicado(self, usuario, comunicado_instance, data_validada):
        """
        Actualiza un comunicado existente.
        """
        self._verificar_permisos(usuario)

        if 'areas_interes' in data_validada:
            areas = data_validada.pop('areas_interes')
            comunicado_instance.areas_interes.set(areas)

        for attr, value in data_validada.items():
            setattr(comunicado_instance, attr, value)

        comunicado_instance.save()
        return comunicado_instance

    @transaction.atomic
    def delete_comunicado(self, usuario, comunicado_instance):
        """
        Borra un comunicado.
        """
        self._verificar_permisos(usuario)
        comunicado_instance.delete()