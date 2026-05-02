from api.models import Acto, PapeletaSitio
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.core.exceptions import ValidationError


def get_ultima_papeleta_hermano_service(usuario):
    """
    Recupera únicamente la papeleta más reciente de un hermano.
    """
    if not usuario or not usuario.is_authenticated:
        raise PermissionDenied("Usuario no identificado")
    
    ultima_papeleta = PapeletaSitio.objects.filter(
        hermano=usuario
    ).select_related(
        'acto', 'puesto', 'puesto__tipo_puesto', 'tramo'
    ).order_by('-anio', '-acto__fecha').first()

    return ultima_papeleta



# -----------------------------------------------------------------------------
# SERVICES: CONSULTA EL HISTÓRICO DE PAPELETAS DE SITIO (NO ADMIN)
# -----------------------------------------------------------------------------
def get_historial_papeletas_hermano_service(usuario):
    """
    Recupera el histórico de papeletas de un hermano específico.
    """
    if not usuario or not usuario.is_authenticated:
        raise PermissionDenied("Usuario no identificado")
    
    queryset = PapeletaSitio.objects.filter(
        hermano=usuario
    ).select_related('acto', 'puesto', 'puesto__tipo_puesto', 'tramo').order_by('-anio', '-acto__fecha')

    return queryset



def obtener_asistentes_leidos_por_acto(acto_id: int):
    """
    Recupera únicamente las papeletas en estado LEIDA de un acto,
    optimizando la carga del hermano, puesto y tramo,
    y ordenando por Cortejo (Cristo -> Virgen) y luego por Tramo.
    """
    return PapeletaSitio.objects.filter(
        acto_id=acto_id,
        estado_papeleta=PapeletaSitio.EstadoPapeleta.LEIDA
    ).select_related(
        'hermano',
        'puesto',
        'tramo'
    ).order_by(
        'tramo__paso',
        'tramo__numero_orden',
        'orden_en_tramo'
    )



def obtener_estadisticas_asistencia(acto_id: int):
    """
    Calcula de forma eficiente los totales de papeletas de un acto 
    usando una única consulta a la base de datos con aggregate.
    """
    if not Acto.objects.filter(id=acto_id).exists():
        raise ValidationError("El acto especificado no existe.")

    estados_validos = [
        PapeletaSitio.EstadoPapeleta.EMITIDA,
        PapeletaSitio.EstadoPapeleta.RECOGIDA,
        PapeletaSitio.EstadoPapeleta.LEIDA
    ]

    estadisticas = PapeletaSitio.objects.filter(
        acto_id=acto_id,
        estado_papeleta__in=estados_validos
    ).aggregate(
        total=Count('id'),
        leidas=Count('id', filter=Q(estado_papeleta=PapeletaSitio.EstadoPapeleta.LEIDA))
    )

    total = estadisticas['total'] or 0
    leidas = estadisticas['leidas'] or 0
    pendientes = total - leidas

    return {
        "total_papeletas": total,
        "papeletas_leidas": leidas,
        "papeletas_pendientes": pendientes
    }