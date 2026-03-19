from django.utils import timezone
from api.models import Acto

class ActoService:
    
    @staticmethod
    def obtener_acto_activo_insignias() -> Acto:
        """
        Busca y retorna el acto que actualmente tiene abierto 
        el plazo de solicitud de papeletas de sitio (insignias).
        Incluye optimización de consultas para las relaciones.
        """
        ahora = timezone.now()
        
        acto_activo = Acto.objects.select_related(
            'tipo_acto'
        ).prefetch_related(
            'puestos_disponibles',
            'puestos_disponibles__tipo_puesto'
        ).filter(
            tipo_acto__requiere_papeleta=True,
            inicio_solicitud__lte=ahora,
            fin_solicitud__gte=ahora
        ).first()
        
        return acto_activo