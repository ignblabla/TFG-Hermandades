from api.models import PapeletaSitio
from rest_framework.exceptions import PermissionDenied


def obtener_datos_tabla_insignias_acto(acto_id: int):
    papeletas = PapeletaSitio.objects.select_related(
        'hermano', 'acto', 'puesto', 'puesto__tipo_puesto'
    ).prefetch_related(
        'preferencias__puesto_solicitado'
    ).filter(
        acto_id=acto_id,
        es_solicitud_insignia=True
    ).exclude(
        estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
    ).order_by(
        'hermano__fecha_ingreso_corporacion'
    )

    filas_tabla = []

    for papeleta in papeletas:
        reparto_ejecutado = papeleta.acto.fecha_ejecucion_reparto is not None
        
        datos_base = {
            'dni': papeleta.hermano.dni,
            'fecha_solicitud': papeleta.fecha_solicitud,
            'acto': papeleta.acto.nombre,
            'es_solicitud_insignia': True,
        }

        if papeleta.preferencias.exists():
            for pref in papeleta.preferencias.all():
                fila = datos_base.copy()
                fila['preferencia'] = f"{pref.orden_prioridad}º - {pref.puesto_solicitado.nombre}"

                if reparto_ejecutado:
                    if papeleta.puesto_id == pref.puesto_solicitado_id:
                        fila['estado'] = papeleta.get_estado_papeleta_display()
                    else:
                        fila['estado'] = "No asignada"
                else:
                    fila['estado'] = papeleta.get_estado_papeleta_display()
                    
                filas_tabla.append(fila)
        else:
            fila = datos_base.copy()
            fila['preferencia'] = "Sin preferencias registradas"
            
            if reparto_ejecutado:
                if papeleta.puesto and papeleta.puesto.tipo_puesto.es_insignia:
                    fila['estado'] = papeleta.get_estado_papeleta_display()
                else:
                    fila['estado'] = "No asignada"
            else:
                fila['estado'] = papeleta.get_estado_papeleta_display()
                
            filas_tabla.append(fila)

    return filas_tabla



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