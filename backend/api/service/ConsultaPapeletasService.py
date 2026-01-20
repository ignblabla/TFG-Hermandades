


from api.models import PapeletaSitio


def get_papeletas_usuario_service(usuario):
    """
    Recupera todas las papeletas de sitio asociadas al usuario logueado.
    
    Optimizaciones:
    - select_related: Trae datos de FK directas (Acto, Puesto, Tramo) en la misma query.
    - prefetch_related: Trae datos de relaciones inversas (Preferencias) eficientemente.
    - Orden: Las más recientes primero (por año y fecha de solicitud).
    """

    return PapeletaSitio.objects.filter(hermano=usuario).select_related(
        'acto',
        'acto__tipo_acto',
        'puesto',
        'puesto__tipo_puesto',
        'tramo'
    ).prefetch_related('preferencias', 'preferencias__puesto_solicitado')\
    .order_by('-anio', '-fecha_solicitud')