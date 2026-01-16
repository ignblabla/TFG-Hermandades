import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..models import Acto, CuerpoPertenencia, Hermano, PapeletaSitio, Puesto

def solicitar_papeleta_cirio(hermano: Hermano, acto: Acto, puesto: Puesto) -> PapeletaSitio:
    ahora = timezone.now()

    # -------------------------------------------------------------------------
    # REGLA 1: Validar Fechas (Inicio y Fin de solicitud de Cirios)
    # -------------------------------------------------------------------------
    if not acto.inicio_solicitud_cirios or not acto.fin_solicitud_cirios:
        raise ValidationError("Este acto no tiene habilitado el plazo de solicitud de cirios.")
    
    if ahora < acto.inicio_solicitud_cirios:
        raise ValidationError(f"El plazo para cirios aún no ha comenzado. Empieza el {acto.inicio_solicitud_cirios.strftime('%d/%m/%Y %H:%M')}.")
    
    if ahora > acto.fin_solicitud_cirios:
        raise ValidationError("El plazo de solicitud de cirios ha finalizado.")
    
    # -------------------------------------------------------------------------
    # REGLA 2: Validar Cuerpos de Pertenencia
    # "Solo NAZARENOS, PRIOSTIA, CARIDAD, JUVENTUD o Hermanos SIN cuerpo"
    # -------------------------------------------------------------------------
    cuerpos_permitidos = [
        CuerpoPertenencia.NombreCuerpo.NAZARENOS,
        CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL,
        CuerpoPertenencia.NombreCuerpo.JUVENTUD,
        CuerpoPertenencia.NombreCuerpo.PRIOSTÍA
    ]

    mis_cuerpos = hermano.cuerpos.all()
    numero_cuerpos = mis_cuerpos.count()

    es_apto_por_cuerpo = False

    if numero_cuerpos == 0:
        es_apto_por_cuerpo = True
    else:
        if mis_cuerpos.filter(nombre_cuerpo__in=cuerpos_permitidos).exists():
            es_apto_por_cuerpo = True

    if not es_apto_por_cuerpo:
        raise ValidationError("Tu cuerpo de pertenencia actual no permite solicitar cirio en este plazo."
            "Solo disponible para Nazarenos, Priostía, Caridad, Juventud o hermanos sin cuerpos asignados.")
    
    # -------------------------------------------------------------------------
    # REGLA 3: Incompatibilidad con Insignias EMITIDAS
    # "Si ya tienes una insignia concedida (EMITIDA), no puedes pedir cirio"
    # -------------------------------------------------------------------------
    tiene_insignia_concedida = PapeletaSitio.objects.filter(
        hermano = hermano,
        acto = acto,
        es_solicitud_insignia = True,
        estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
    ).exists()

    if tiene_insignia_concedida:
        raise ValidationError("No puedes solicitar cirio porque ya tienes asignada y emitida una papeleta de Insignia para este acto.")
    
    # -------------------------------------------------------------------------
    # REGLA 4: Evitar duplicados de solicitud de cirio
    # -------------------------------------------------------------------------
    ya_solicito_cirio = PapeletaSitio.objects.filter(
        hermano = hermano,
        acto = acto,
        es_solicitud_insignia = False,
    ).exists()

    if ya_solicito_cirio:
        raise ValidationError("Ya tienes una solicitud de sitio registrada para este acto.")
    
    # -------------------------------------------------------------------------
    # CREACIÓN DE LA PAPELETA
    # -------------------------------------------------------------------------
    nueva_papeleta = PapeletaSitio.objects.create(
        hermano = hermano,
        acto = acto,
        anio = acto.fecha.year,
        estado_papeleta = PapeletaSitio.EstadoPapeleta.SOLICITADA,
        es_solicitud_insignia = False,
        puesto = puesto,
        fecha_solicitud = ahora,
    )

    return nueva_papeleta