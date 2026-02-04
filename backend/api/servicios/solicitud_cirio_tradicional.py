import uuid
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

from api.models import Acto, CuerpoPertenencia, Cuota, Hermano, PapeletaSitio, Puesto


class SolicitudCirioTradicionalService:
    ESTADOS_NO_ACTIVOS = (
        PapeletaSitio.EstadoPapeleta.ANULADA,
        PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
    )

    def _qs_papeletas_activas(self):
        return PapeletaSitio.objects.exclude(estado_papeleta__in=self.ESTADOS_NO_ACTIVOS)

    @transaction.atomic
    def procesar_solicitud_cirio_tradicional(self, hermano: Hermano, acto: Acto, puesto: Puesto, numero_registro_vinculado: int = None):

        Hermano.objects.select_for_update().only("id").get(pk=hermano.pk)

        ahora = timezone.now()

        self._validar_configuracion_acto_tradicional(acto)
        self._validar_plazo_vigente(ahora, acto.inicio_solicitud_cirios, acto.fin_solicitud_cirios, "cirios")

        cuerpos_hermano_set = set(hermano.cuerpos.values_list('nombre_cuerpo', flat=True))
        self._validar_hermano_apto_para_solicitar(hermano, cuerpos_hermano_set, ahora)

        self._validar_item_puesto_cirio(cuerpos_hermano_set, acto, puesto)

        solicitud_insignia_a_anular = self._gestionar_conflicto_insignia_y_unicidad(hermano, acto, puesto)

        if solicitud_insignia_a_anular:
            anulado = (
                PapeletaSitio.objects
                .select_for_update()
                .filter(
                    pk=solicitud_insignia_a_anular.pk,
                    estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
                    es_solicitud_insignia=True,
                    hermano=hermano,
                    acto=acto,
                )
                .update(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA)
            )

            if anulado == 0:
                raise ValidationError(
                    "Tu solicitud de insignia cambió de estado durante el proceso. "
                    "Vuelve a intentarlo o contacta con secretaría."
                )

        try:
            papeleta = self._crear_papeleta_base(hermano, acto, ahora)
            papeleta.puesto = puesto
            papeleta.save(update_fields=['puesto'])

        except IntegrityError:
            raise ValidationError(
                "Ya existe una papeleta activa para este acto. "
                "Si has pulsado dos veces, espera unos segundos y recarga."
            )

        if numero_registro_vinculado:
            self._procesar_vinculacion(hermano, acto, papeleta, puesto, numero_registro_vinculado)

        return papeleta
    


    def _validar_configuracion_acto_tradicional(self, acto: Acto):
        """
        Verifica que el acto sea del tipo correcto para este endpoint.
        """
        if acto is None or acto.tipo_acto_id is None:
            raise ValidationError({"tipo_acto": "El tipo de acto es obligatorio."})

        if not acto.tipo_acto.requiere_papeleta:
            raise ValidationError(f"El acto '{acto.nombre}' no admite solicitudes de papeleta.")

        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            raise ValidationError("Este proceso es exclusivo para actos de modalidad TRADICIONAL.")
        


    def _validar_plazo_vigente(self, ahora, inicio, fin, nombre_plazo: str):
        """
        Valida que el momento actual esté dentro del rango definido.
        """
        if not inicio or not fin:
            raise ValidationError(f"El plazo de {nombre_plazo} no está configurado en el acto.")
            
        if ahora < inicio:
            raise ValidationError(f"El plazo de solicitud de {nombre_plazo} aún no ha comenzado.")
        
        if ahora > fin:
            raise ValidationError(f"El plazo de solicitud de {nombre_plazo} ha finalizado.")
        


    def _validar_hermano_apto_para_solicitar(self, hermano: Hermano, cuerpos_hermano_set: set, ahora):
        """Agrupa las validaciones de estado del hermano."""
        self._validar_hermano_en_alta(hermano)
        self._validar_hermano_al_corriente_hasta_anio_anterior(hermano, ahora)
        self._validar_pertenencia_cuerpos(cuerpos_hermano_set)



    def _validar_hermano_en_alta(self, hermano):
        if hermano.estado_hermano != Hermano.EstadoHermano.ALTA:
            raise ValidationError("Solo los hermanos en estado ALTA pueden solicitar papeleta.")
        


    def _validar_hermano_al_corriente_hasta_anio_anterior(self, hermano: Hermano, ahora):
        anio_actual = ahora.date().year
        anio_limite = anio_actual - 1

        estados_deuda = [
            Cuota.EstadoCuota.PENDIENTE, 
            Cuota.EstadoCuota.DEVUELTA
        ]

        deuda = hermano.cuotas.filter(
            anio__lte=anio_limite,
            estado__in=estados_deuda
        ).values('anio').order_by('anio').first()

        if deuda:
            raise ValidationError(
                f"Consta una cuota pendiente o devuelta del año {deuda['anio']}. "
                f"Por favor, contacte con mayordomía para regularizar su situación."
            )

        existe_historial = hermano.cuotas.filter(anio__lte=anio_limite).exists()
        
        if not existe_historial:
            raise ValidationError(
                f"No constan cuotas registradas hasta el año {anio_limite}. "
                "Contacte con secretaría para verificar su ficha."
            )
        


    def _validar_pertenencia_cuerpos(self, cuerpos_hermano_set: set):
        cuerpos_permitidos = {
            CuerpoPertenencia.NombreCuerpo.NAZARENOS.value,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA.value,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD.value,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL.value,
            CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value,
        }

        if not cuerpos_hermano_set:
            return

        cuerpos_no_aptos = set(cuerpos_hermano_set) - cuerpos_permitidos

        if cuerpos_no_aptos:
            raise ValidationError(
                "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: "
                + ", ".join(sorted(cuerpos_no_aptos))
            )
        


    def _validar_item_puesto_cirio(self, cuerpos_hermano_set: set, acto: Acto, puesto: Puesto):
        """Validaciones específicas para un puesto único de Cirio"""
        if not puesto:
            raise ValidationError("Debe seleccionar un puesto válido.")
        
        if puesto.acto_id != acto.id:
            raise ValidationError("El puesto no pertenece a este acto.")
        
        if puesto.tipo_puesto.es_insignia:
            raise ValidationError(f"El puesto '{puesto.nombre}' es una Insignia. No puede solicitarse en este formulario.")

        if not puesto.disponible:
            raise ValidationError(f"El puesto '{puesto.nombre}' no está marcado como disponible.")
            
        if (puesto.tipo_puesto.solo_junta_gobierno and CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value not in cuerpos_hermano_set):
            raise ValidationError(f"El puesto '{puesto.nombre}' es exclusivo para la Junta de Gobierno.")
        


    def _gestionar_conflicto_insignia_y_unicidad(self, hermano: Hermano, acto: Acto, puesto_nuevo: Puesto):
        """
        Maneja la lógica compleja de interacción entre Insignias y Cirios.
        Retorna: La instancia de Papeleta (Insignia) PENDIENTE si debe anularse.
        Lanza ValidationError si hay bloqueo insalvable.
        """
        papeletas_activas = (
            self._qs_papeletas_activas()
            .select_for_update()
            .filter(hermano=hermano, acto=acto)
        )

        insignia_a_anular = None

        for p in papeletas_activas:
            if p.es_solicitud_insignia and p.estado_papeleta in [PapeletaSitio.EstadoPapeleta.EMITIDA, PapeletaSitio.EstadoPapeleta.RECOGIDA, PapeletaSitio.EstadoPapeleta.LEIDA]:
                raise ValidationError("Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente.")

            elif p.es_solicitud_insignia and p.estado_papeleta == PapeletaSitio.EstadoPapeleta.SOLICITADA:
                insignia_a_anular = p
                continue

            elif not p.es_solicitud_insignia:
                tipo_existente = p.puesto.tipo_puesto if p.puesto else None
                tipo_nuevo = puesto_nuevo.tipo_puesto
                
                if tipo_existente and tipo_existente.id == tipo_nuevo.id:
                    raise ValidationError(f"Ya tienes una solicitud activa para '{tipo_nuevo.nombre_tipo}'.")
                else:
                    raise ValidationError("Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez).")

        return insignia_a_anular
    


    def _crear_papeleta_base(self, hermano, acto, fecha_solicitud, vinculado_a=None):
        return PapeletaSitio.objects.create(
            hermano=hermano,
            acto=acto,
            anio=acto.fecha.year,
            fecha_solicitud=fecha_solicitud,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            vinculado_a=vinculado_a,
            es_solicitud_insignia=False,
            codigo_verificacion=uuid.uuid4().hex[:8].upper()
        )
    


    def _procesar_vinculacion(self, hermano, acto, mi_papeleta, mi_puesto, numero_objetivo):
        """Lógica compleja de vinculación entre hermanos para tramos"""

        if not numero_objetivo:
            raise ValidationError("Debe indicar un número de registro válido para vincularse.")
        
        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            raise ValidationError("La vinculación solo está disponible en modalidad TRADICIONAL.")

        try:
            hermano_objetivo = Hermano.objects.get(numero_registro=numero_objetivo)
        except Hermano.DoesNotExist:
            raise ValidationError(f"No existe hermano con Nº {numero_objetivo}.")

        if hermano_objetivo.id == hermano.id:
            raise ValidationError("No puedes vincularte contigo mismo.")
        
        if hermano.numero_registro is None or hermano_objetivo.numero_registro is None:
            raise ValidationError("Ambos hermanos deben tener número de registro para poder vincularse.")
        
        if hermano.numero_registro > hermano_objetivo.numero_registro:
            raise ValidationError(
                f"Tú (Nº {hermano.numero_registro}) eres más nuevo que el Nº {hermano_objetivo.numero_registro}. "
                "Solo el hermano antiguo puede vincularse al nuevo (perdiendo antigüedad)."
            )

        qs_obj = (
            self._qs_papeletas_activas()
            .select_for_update()
            .filter(hermano=hermano_objetivo, acto=acto)
            .order_by("-fecha_solicitud", "-id")
        )

        count = qs_obj.count()
        if count == 0:
            raise ValidationError(f"El hermano Nº {numero_objetivo} no tiene solicitud activa.")
        if count > 1:
            raise ValidationError(
                f"El hermano Nº {numero_objetivo} tiene múltiples solicitudes activas para este acto. "
                "Contacte con secretaría."
            )

        papeleta_objetivo = qs_obj.get()

        tengo_dependientes = (
            self._qs_papeletas_activas()
            .filter(acto=acto, vinculado_a=hermano)
            .exists()
        )

        if tengo_dependientes:
            raise ValidationError(
                "No puedes vincularte a otro hermano porque ya tienes a otros hermanos vinculados a ti. "
                "No se permiten cadenas de vinculación (A->B->C). Diles que se vinculen directamente al hermano objetivo."
            )

        es_insignia_obj = papeleta_objetivo.es_solicitud_insignia or (
            papeleta_objetivo.puesto and papeleta_objetivo.puesto.tipo_puesto.es_insignia
        )
        if es_insignia_obj:
            raise ValidationError("No puedes vincularte a un hermano que solicita Insignia.")

        puesto_objetivo = papeleta_objetivo.puesto
        if not puesto_objetivo:
            raise ValidationError(f"El hermano Nº {numero_objetivo} no tiene puesto seleccionado.")

        if mi_puesto.tipo_puesto_id != puesto_objetivo.tipo_puesto_id:
            raise ValidationError("Ambos deben solicitar el mismo tipo de puesto (ej: ambos Cirio).")

        if mi_puesto.cortejo_cristo != puesto_objetivo.cortejo_cristo:
            raise ValidationError("Conflicto de sección: Uno va en Cristo y otro en Virgen.")

        mi_papeleta.vinculado_a = hermano_objetivo
        mi_papeleta.save(update_fields=['vinculado_a'])