import uuid
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Acto, CuerpoPertenencia, Hermano, PapeletaSitio, Puesto

@transaction.atomic
def solicitar_papeleta_cirio(hermano: Hermano, acto: Acto, puesto: Puesto, numero_registro_vinculado: int = None) -> PapeletaSitio:
    ahora = timezone.now()

    # =========================================================================
    # FASE 1: VALIDACIONES DE LA SOLICITUD (El usuario puede pedir sitio)
    # =========================================================================

    # 1. Validar Fechas
    if not acto.inicio_solicitud_cirios or not acto.fin_solicitud_cirios:
        raise ValidationError("Este acto no tiene habilitado el plazo de solicitud de cirios.")
    
    if ahora < acto.inicio_solicitud_cirios:
        raise ValidationError(f"El plazo para cirios aún no ha comenzado. Empieza el {acto.inicio_solicitud_cirios.strftime('%d/%m/%Y %H:%M')}.")
    
    if ahora > acto.fin_solicitud_cirios:
        raise ValidationError("El plazo de solicitud de cirios ha finalizado.")
    
    # 2. Validar Cuerpos de Pertenencia
    cuerpos_permitidos = [
        CuerpoPertenencia.NombreCuerpo.NAZARENOS,
        CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL,
        CuerpoPertenencia.NombreCuerpo.JUVENTUD,
        CuerpoPertenencia.NombreCuerpo.PRIOSTÍA
    ]

    mis_cuerpos = hermano.cuerpos.all()
    if mis_cuerpos.exists() and not mis_cuerpos.filter(nombre_cuerpo__in=cuerpos_permitidos).exists():
        raise ValidationError("Tu cuerpo de pertenencia actual no permite solicitar cirio en este plazo.")
    
    # 3. Incompatibilidad con Insignias EMITIDAS
    tiene_insignia_concedida = PapeletaSitio.objects.filter(
        hermano=hermano,
        acto=acto,
        es_solicitud_insignia=True,
        estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA
    ).exists()

    if tiene_insignia_concedida:
        raise ValidationError("No puedes solicitar cirio porque ya tienes asignada y emitida una papeleta de Insignia para este acto.")
    
    # 4. Evitar duplicados
    # Usamos select_for_update para bloquear concurrencia en la validación de duplicados
    ya_solicito_cirio = PapeletaSitio.objects.select_for_update().filter(
        hermano=hermano,
        acto=acto,
        es_solicitud_insignia=False,
    ).exists()

    if ya_solicito_cirio:
        raise ValidationError("Ya tienes una solicitud de sitio registrada para este acto.")
    
    # =========================================================================
    # FASE 2: CREACIÓN DE LA PAPELETA
    # =========================================================================
    nueva_papeleta = PapeletaSitio.objects.create(
        hermano=hermano,
        acto=acto,
        anio=acto.fecha.year,
        estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
        es_solicitud_insignia=False,
        puesto=puesto,
        fecha_solicitud=ahora,
    )

    # =========================================================================
    # FASE 3: LÓGICA DE VINCULACIÓN (Opcional)
    # =========================================================================
    if numero_registro_vinculado:
        
        # A. Validar Modalidad
        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            # Nota: Al estar dentro de una transacción, esto hará rollback de la creación anterior
            raise ValidationError("La vinculación de sitios solo está disponible para actos de modalidad TRADICIONAL.")

        # B. Obtener Hermano Objetivo
        try:
            hermano_objetivo = Hermano.objects.get(numero_registro=numero_registro_vinculado)
        except Hermano.DoesNotExist:
            raise ValidationError(f"No existe ningún hermano con el número de registro {numero_registro_vinculado}.")

        if hermano_objetivo == hermano:
            raise ValidationError("No puedes vincularte contigo mismo.")

        # C. Obtener Papeleta Objetivo (Debe existir, ser del mismo acto y no anulada)
        papeleta_objetivo = PapeletaSitio.objects.select_for_update().filter(
            hermano=hermano_objetivo,
            acto=acto
        ).exclude(
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
        ).first()

        if not papeleta_objetivo:
            raise ValidationError(
                f"El hermano con Nº {numero_registro_vinculado} no ha solicitado papeleta de sitio para este acto (o está anulada)."
            )

        # D. Validar que la papeleta objetivo NO sea insignia (Regla de paridad)
        es_insignia_objetivo = False
        if papeleta_objetivo.es_solicitud_insignia:
            es_insignia_objetivo = True
        if papeleta_objetivo.puesto and papeleta_objetivo.puesto.tipo_puesto.es_insignia:
            es_insignia_objetivo = True
        
        if es_insignia_objetivo:
            raise ValidationError(
                f"El hermano con Nº {numero_registro_vinculado} ha solicitado una Insignia. "
                "Solo puedes vincularte a hermanos que también vayan de Cirio."
            )

        puesto_objetivo = papeleta_objetivo.puesto
        if not puesto_objetivo:
            raise ValidationError(f"El hermano Nº {numero_registro_vinculado} tiene solicitud pero no ha seleccionado puesto.")

        # E. Validar que coincidan los Tipos de Puesto (ej: Cirio vs Cirio)
        if puesto.tipo_puesto.nombre_tipo != puesto_objetivo.tipo_puesto.nombre_tipo:
            raise ValidationError(
                f"No puedes vincularte: Tú has pedido '{puesto.tipo_puesto.nombre_tipo}' "
                f"y el otro hermano ha pedido '{puesto_objetivo.tipo_puesto.nombre_tipo}'. Deben coincidir."
            )

        # F. Validar que coincida el Cortejo (Cristo vs Virgen)
        if puesto.cortejo_cristo != puesto_objetivo.cortejo_cristo:
            seccion_propia = "Cristo" if puesto.cortejo_cristo else "Virgen"
            seccion_objetivo = "Cristo" if puesto_objetivo.cortejo_cristo else "Virgen"
            raise ValidationError(
                f"Conflicto de sección: Tú vas en el cortejo de {seccion_propia} "
                f"y el hermano objetivo va en el de {seccion_objetivo}."
            )

        # G. Validar Antigüedad (Regla de Oro: solo el antiguo se vincula al nuevo)
        mi_numero = hermano.numero_registro
        su_numero = hermano_objetivo.numero_registro

        if not mi_numero or not su_numero:
            raise ValidationError("Ambos hermanos deben tener número de registro asignado para poder vincularse.")

        if mi_numero > su_numero:
            raise ValidationError(
                f"No puedes vincularte al hermano {su_numero}. "
                f"Tú tienes el número {mi_numero}. Solo puedes vincularte a hermanos con un número MAYOR al tuyo (perder antigüedad)."
            )

        # H. Aplicar Vinculación
        nueva_papeleta.vinculado_a = hermano_objetivo
        nueva_papeleta.save(update_fields=['vinculado_a'])

    return nueva_papeleta