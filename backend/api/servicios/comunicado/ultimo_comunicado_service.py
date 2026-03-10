from api.models import Comunicado, AreaInteres


def obtener_ultimo_comunicado_areas_usuario(usuario):
    """
    Obtiene el último comunicado publicado que pertenezca a alguna 
    de las áreas de interés a las que está suscrito el usuario.
    Si no tiene áreas asignadas, devuelve el último de TODOS_HERMANOS.
    """
    areas_usuario = usuario.areas_interes.all()

    if not areas_usuario.exists():
        return Comunicado.objects.filter(
            areas_interes__nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS
        ).order_by('-fecha_emision').first()

    ultimo_comunicado = Comunicado.objects.filter(
        areas_interes__in=areas_usuario
    ).order_by('-fecha_emision').first()

    return ultimo_comunicado