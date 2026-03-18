from api.models import Comunicado, AreaInteres


def obtener_ultimos_comunicados_areas_usuario(usuario):
    """
    Obtiene los 2 últimos comunicados publicados que pertenezcan a alguna 
    de las áreas de interés a las que está suscrito el usuario.
    Si no tiene áreas asignadas, devuelve los 2 últimos de TODOS_HERMANOS.
    """
    areas_usuario = usuario.areas_interes.all()

    if not areas_usuario.exists():
        return Comunicado.objects.filter(
            areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS
        ).distinct().order_by('-fecha_emision')[:2]

    return Comunicado.objects.filter(
        areas_interes__in=areas_usuario
    ).distinct().order_by('-fecha_emision')[:2]


def obtener_comunicados_relacionados_usuario(usuario, comunicado_actual_id):
    """
    Obtiene los 3 últimos comunicados publicados de las áreas de interés del usuario,
    excluyendo explícitamente el comunicado que se está leyendo.
    Si no tiene áreas asignadas, devuelve los 3 últimos de TODOS_HERMANOS.
    """
    areas_usuario = usuario.areas_interes.all()

    queryset_base = Comunicado.objects.exclude(id=comunicado_actual_id)

    if not areas_usuario.exists():
        return queryset_base.filter(
            areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS
        ).distinct().order_by('-fecha_emision')[:3]

    return queryset_base.filter(
        areas_interes__in=areas_usuario
    ).distinct().order_by('-fecha_emision')[:3]