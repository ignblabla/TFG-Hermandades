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
        ).order_by('-fecha_emision')[:2]

    return Comunicado.objects.filter(
        areas_interes__in=areas_usuario
    ).order_by('-fecha_emision')[:2]