from datetime import datetime, time
import uuid
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Acto, CuerpoPertenencia, Cuota, Hermano, PapeletaSitio, Puesto, PreferenciaSolicitud

class PapeletaSitioService:
    """
    Servicio centralizado para la gestión de solicitudes de papeleta de sitio.
    Maneja tanto la modalidad UNIFICADA como la TRADICIONAL (Insignias y Cirios por separado).
    """

    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS (ENTRADA)
    # -------------------------------------------------------------------------

    @transaction.atomic
    def procesar_solicitud_unificada(self, hermano: Hermano, acto: Acto, preferencias_data: list):
        """
        [MODALIDAD UNIFICADA]
        Permite solicitar insignias y/o cirio en una sola petición.
        """
        ahora = timezone.now()

        self._validar_plazos_acto_coherentes(acto)

        if acto.modalidad != Acto.ModalidadReparto.UNIFICADO:
            raise ValidationError(f"La solicitud unificada no está disponible. Modalidad actual: {acto.get_modalidad_display()}.")

        if not acto.inicio_solicitud or not acto.fin_solicitud:
            raise ValidationError("El plazo de solicitud no está configurado correctamente.")
        
        if ahora < acto.inicio_solicitud:
            raise ValidationError(f"El plazo aún no ha comenzado. Empieza el {acto.inicio_solicitud}.")
        
        if ahora > acto.fin_solicitud:
            raise ValidationError(f"El plazo finalizó el {acto.fin_solicitud}.")

        # 3. Validaciones Comunes
        self._validar_requiere_papeleta(acto)
        self._validar_pertenencia_cuerpos(hermano)
        self._validar_unicidad(hermano, acto)

        self._validar_mix_puestos_unificado(preferencias_data)

        papeleta = self._crear_papeleta_base(hermano, acto, ahora)

        es_insignia_global = False
        if preferencias_data:
            for item in preferencias_data:
                puesto = item['puesto_solicitado']
                orden = item['orden_prioridad']

                self._validar_puesto_solo_junta_gobierno(hermano, puesto)
                
                if puesto.tipo_puesto.es_insignia:
                    es_insignia_global = True

                PreferenciaSolicitud.objects.create(
                    papeleta=papeleta,
                    puesto_solicitado=puesto,
                    orden_prioridad=orden
                )
        
        if es_insignia_global:
            papeleta.es_solicitud_insignia = True
            papeleta.save(update_fields=['es_solicitud_insignia'])

        return papeleta

    @transaction.atomic
    def procesar_solicitud_insignia_tradicional(self, hermano: Hermano, acto: Acto, preferencias_data: list):
        """
        [MODALIDAD TRADICIONAL - FASE 1]
        Solo permite solicitar puestos marcados como insignia.
        """
        ahora = timezone.now()

        self._validar_plazos_acto_coherentes(acto)
                
        self._validar_requiere_papeleta(acto)

        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            raise ValidationError("Este endpoint es solo para actos de modalidad TRADICIONAL.")

        self._validar_hermano_en_alta(hermano)
        self._validar_hermano_al_corriente_hasta_anio_anterior(hermano)
        self._validar_pertenencia_cuerpos(hermano)
        self._validar_unicidad(hermano, acto)

        if not acto.inicio_solicitud or not acto.fin_solicitud:
            raise ValidationError("Plazo de insignias no configurado.")
        
        if ahora < acto.inicio_solicitud or ahora > acto.fin_solicitud:
            raise ValidationError("Fuera del plazo de solicitud de insignias.")
        
        if not preferencias_data:
            raise ValidationError("Debe indicar al menos una preferencia.")
        
        prioridades = [item["orden_prioridad"] for item in preferencias_data]
        if len(prioridades) != len(set(prioridades)):
            raise ValidationError("No puede haber orden de prioridad duplicado.")
        
        puestos_ids = [item["puesto_solicitado"].id for item in preferencias_data]
        if len(puestos_ids) != len(set(puestos_ids)):
            raise ValidationError("No puede haber un puesto duplicado en las preferencias.")

        for item in preferencias_data:
            puesto = item['puesto_solicitado']
            prioridad = item['orden_prioridad']

            self._validar_puesto_solo_junta_gobierno(hermano, puesto)

            if not isinstance(prioridad, int) or prioridad < 1:
                raise ValidationError("El orden de prioridad debe ser mayor que cero.")
            
            if puesto.acto_id != acto.id:
                raise ValidationError("No puede seleccionar un puesto de otro acto.")

            if not puesto.tipo_puesto.es_insignia:
                raise ValidationError(f"El puesto '{puesto.nombre}' no es una insignia. En plazo tradicional, los cirios se piden aparte.")
            
            if not puesto.disponible:
                raise ValidationError(
                    f"El puesto '{puesto.nombre}' no está disponible para su solicitud en este acto."
                )

        papeleta = self._crear_papeleta_base(hermano, acto, ahora)
        papeleta.es_solicitud_insignia = True
        papeleta.save(update_fields=['es_solicitud_insignia'])

        for item in preferencias_data:
            PreferenciaSolicitud.objects.create(
                papeleta=papeleta,
                puesto_solicitado=item['puesto_solicitado'],
                orden_prioridad=item['orden_prioridad']
            )

        return papeleta

    @transaction.atomic
    def procesar_solicitud_cirio_tradicional(self, hermano: Hermano, acto: Acto, puesto: Puesto, numero_registro_vinculado: int = None):
        ahora = timezone.now()

        self._validar_plazos_acto_coherentes(acto)

        self._validar_requiere_papeleta(acto)
        self._validar_puesto_no_nulo(puesto)

        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            raise ValidationError("Este endpoint es solo para actos de modalidad TRADICIONAL.")

        self._validar_hermano_en_alta(hermano)
        self._validar_hermano_al_corriente_hasta_anio_anterior(hermano)
        self._validar_pertenencia_cuerpos(hermano)

        tiene_insignia_emitida = PapeletaSitio.objects.filter(
            hermano=hermano, acto=acto, es_solicitud_insignia=True,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA
        ).exists()
        if tiene_insignia_emitida:
            raise ValidationError("Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio.")

        solicitud_insignia_pendiente = PapeletaSitio.objects.select_for_update().filter(
            hermano=hermano, acto=acto, es_solicitud_insignia=True,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        ).first()

        papeleta_cirio_activa = PapeletaSitio.objects.filter(
            hermano=hermano, acto=acto, es_solicitud_insignia=False
        ).exclude(
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
        ).select_related("puesto__tipo_puesto").first()

        if papeleta_cirio_activa:
            tipo_existente_id = papeleta_cirio_activa.puesto.tipo_puesto_id if papeleta_cirio_activa.puesto else None
            tipo_nuevo_id = puesto.tipo_puesto_id

            if tipo_existente_id == tipo_nuevo_id:
                raise ValidationError(
                    f"Ya tienes una solicitud activa para el tipo '{puesto.tipo_puesto.nombre_tipo}'. "
                    "Solo puedes solicitar un puesto de ese tipo."
                )

            raise ValidationError(
                "Solo puedes solicitar un único tipo de puesto en este acto (por ejemplo, CIRIO o CRUZ PENITENTE, pero no ambos)."
            )

        qs_unicidad = PapeletaSitio.objects.select_for_update().filter(
            hermano=hermano, acto=acto
        ).exclude(
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
        )
        if solicitud_insignia_pendiente:
            qs_unicidad = qs_unicidad.exclude(id=solicitud_insignia_pendiente.id)

        if qs_unicidad.exists():
            raise ValidationError("Ya existe una solicitud activa para este acto.")

        if ahora < acto.inicio_solicitud_cirios:
            raise ValidationError(f"El plazo de cirios comienza el {acto.inicio_solicitud_cirios}.")

        if ahora > acto.fin_solicitud_cirios:
            raise ValidationError("El plazo de solicitud de cirios ha finalizado.")

        if puesto.acto_id != acto.id:
            raise ValidationError("No puede seleccionar un puesto de otro acto.")

        if puesto.tipo_puesto.es_insignia:
            raise ValidationError(f"El puesto '{puesto.nombre}' es una insignia y no puede solicitarse como cirio.")
        
        self._validar_puesto_solo_junta_gobierno(hermano, puesto)

        if not puesto.disponible:
            raise ValidationError(f"El puesto '{puesto.nombre}' no está disponible para su solicitud en este acto.")

        if solicitud_insignia_pendiente:
            solicitud_insignia_pendiente.estado_papeleta = PapeletaSitio.EstadoPapeleta.ANULADA
            solicitud_insignia_pendiente.save(update_fields=["estado_papeleta"])

        papeleta = PapeletaSitio.objects.create(
            hermano=hermano,
            acto=acto,
            anio=acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=puesto,
            fecha_solicitud=ahora,
            codigo_verificacion=uuid.uuid4().hex[:8].upper()
        )

        if numero_registro_vinculado:
            self._procesar_vinculacion(hermano, acto, papeleta, puesto, numero_registro_vinculado)

        return papeleta

    # -------------------------------------------------------------------------
    # MÉTODOS PRIVADOS (HELPER & VALIDATORS)
    # -------------------------------------------------------------------------

    def _crear_papeleta_base(self, hermano, acto, fecha_solicitud):
        return PapeletaSitio.objects.create(
            hermano=hermano,
            acto=acto,
            anio=acto.fecha.year,
            fecha_solicitud=fecha_solicitud,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            numero_papeleta=None,
            codigo_verificacion=uuid.uuid4().hex[:8].upper()
        )
    
    def _validar_puesto_no_nulo(self, puesto: Puesto):
        if not puesto:
            raise ValidationError("Debe seleccionar un puesto válido.")

    def _validar_requiere_papeleta(self, acto):
        if not acto.tipo_acto.requiere_papeleta:
            raise ValidationError(f"El acto '{acto.nombre}' no admite solicitudes.")

    def _validar_pertenencia_cuerpos(self, hermano):
        cuerpos_permitidos = {
            CuerpoPertenencia.NombreCuerpo.NAZARENOS,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL,
            CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO,
        }

        mis_cuerpos_ids = list(
            hermano.cuerpos.values_list('nombre_cuerpo', flat=True)
        )

        if not mis_cuerpos_ids:
            return

        cuerpos_no_permitidos = [c for c in mis_cuerpos_ids if c not in cuerpos_permitidos]
        if cuerpos_no_permitidos:
            raise ValidationError("Tu cuerpo de pertenencia actual no permite solicitar papeleta.")

    def _validar_unicidad(self, hermano, acto):
        existe = PapeletaSitio.objects.select_for_update().filter(
            hermano=hermano, 
            acto=acto
        ).exclude(
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
        ).exists()
        
        if existe:
            raise ValidationError("Ya existe una solicitud activa para este acto.")
        
    def _validar_hermano_en_alta(self, hermano: Hermano):
        if hermano.estado_hermano != Hermano.EstadoHermano.ALTA:
            raise ValidationError("Solo los hermanos en estado ALTA pueden solicitar papeleta.")
        
    def _validar_hermano_al_corriente_hasta_anio_anterior(self, hermano: Hermano):
        """
        Requiere que TODAS las cuotas hasta el año anterior estén PAGADAS.
        """
        anio_actual = timezone.now().date().year
        anio_limite = anio_actual - 1
        existe_deuda = hermano.cuotas.filter(
            anio__lte=anio_limite
        ).exclude(
            estado=Cuota.EstadoCuota.PAGADA
        ).exists()

        if existe_deuda:
            raise ValidationError(
                f"No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}."
            )

    def _validar_mix_puestos_unificado(self, preferencias_data):
        """Valida que no se pidan dos puestos genéricos (ej: Cirio Cristo y Cirio Virgen)"""
        tipos_no_insignia_vistos = set()
        if preferencias_data:
            for item in preferencias_data:
                puesto = item['puesto_solicitado']
                tipo = puesto.tipo_puesto
                if not tipo.es_insignia:
                    if tipo.id in tipos_no_insignia_vistos:
                        raise ValidationError(f"No puedes solicitar más de un puesto tipo '{tipo.nombre_tipo}' en la misma solicitud.")
                    tipos_no_insignia_vistos.add(tipo.id)

    def _procesar_vinculacion(self, hermano, acto, mi_papeleta, mi_puesto, numero_objetivo):
        """Lógica compleja de vinculación entre hermanos para tramos"""
        
        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            raise ValidationError("La vinculación solo está disponible en modalidad TRADICIONAL.")

        try:
            hermano_objetivo = Hermano.objects.get(numero_registro=numero_objetivo)
        except Hermano.DoesNotExist:
            raise ValidationError(f"No existe hermano con Nº {numero_objetivo}.")

        if hermano_objetivo.id == hermano.id:
            raise ValidationError("No puedes vincularte contigo mismo.")

        papeleta_objetivo = PapeletaSitio.objects.select_for_update().filter(
            hermano=hermano_objetivo,
            acto=acto
        ).exclude(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).first()

        if not papeleta_objetivo:
            raise ValidationError(f"El hermano Nº {numero_objetivo} no tiene solicitud activa.")

        es_insignia_obj = papeleta_objetivo.es_solicitud_insignia or (
            papeleta_objetivo.puesto and papeleta_objetivo.puesto.tipo_puesto.es_insignia
        )
        if es_insignia_obj:
            raise ValidationError("No puedes vincularte a un hermano que solicita Insignia.")

        puesto_objetivo = papeleta_objetivo.puesto
        if not puesto_objetivo:
            raise ValidationError(f"El hermano Nº {numero_objetivo} no tiene puesto seleccionado.")

        if mi_puesto.tipo_puesto.nombre_tipo != puesto_objetivo.tipo_puesto.nombre_tipo:
            raise ValidationError("Ambos deben solicitar el mismo tipo de puesto (ej: ambos Cirio).")

        if mi_puesto.cortejo_cristo != puesto_objetivo.cortejo_cristo:
            raise ValidationError("Conflicto de sección: Uno va en Cristo y otro en Virgen.")

        if hermano.numero_registro > hermano_objetivo.numero_registro:
            raise ValidationError(
                f"Tú (Nº {hermano.numero_registro}) eres más nuevo que el Nº {hermano_objetivo.numero_registro}. "
                "Solo el hermano antiguo puede vincularse al nuevo (perdiendo antigüedad)."
            )

        mi_papeleta.vinculado_a = hermano_objetivo
        mi_papeleta.save(update_fields=['vinculado_a'])


    def _validar_puesto_solo_junta_gobierno(self, hermano: Hermano, puesto: Puesto):
        """
        Si el tipo de puesto es exclusivo de Junta de Gobierno, exige pertenecer al cuerpo JUNTA_GOBIERNO.
        """
        if puesto.tipo_puesto.solo_junta_gobierno:
            pertenece = hermano.cuerpos.filter(
                nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()

            if not pertenece:
                raise ValidationError(
                    f"El puesto '{puesto.nombre}' es exclusivo para Junta de Gobierno."
                )
            
    def _acto_fecha_como_datetime_fin_dia(self, acto: Acto):
        """
        Devuelve la fecha del acto como datetime aware para poder comparar con plazos datetime.
        - Si acto.fecha ya es datetime -> se usa tal cual
        - Si acto.fecha es date -> se convierte a fin de día (23:59:59.999999)
        """
        if not acto.fecha:
            return None

        if hasattr(acto.fecha, "date"):
            return acto.fecha

        dt = datetime.combine(acto.fecha, time.max)
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt

    def _validar_rango_inicio_fin(self, inicio, fin, mensaje_base: str):
        if not inicio or not fin:
            raise ValidationError(f"{mensaje_base} no configurado.")
        if inicio >= fin:
            raise ValidationError(
                f"{mensaje_base} mal configurado: la fecha de inicio debe ser anterior a la de fin."
            )

    def _validar_plazos_acto_coherentes(self, acto: Acto):
        """
        Restricciones pedidas:
        - Si requiere papeleta y TRADICIONAL:
            inicio_solicitud < fin_solicitud
            inicio_solicitud_cirios < fin_solicitud_cirios
            fin_solicitud_cirios <= acto.fecha
        - Si requiere papeleta y UNIFICADO:
            inicio_solicitud < fin_solicitud
            fin_solicitud <= acto.fecha
        """
        if not acto.tipo_acto.requiere_papeleta:
            return

        acto_dt = self._acto_fecha_como_datetime_fin_dia(acto)

        if acto.modalidad == Acto.ModalidadReparto.TRADICIONAL:
            self._validar_rango_inicio_fin(
                acto.inicio_solicitud,
                acto.fin_solicitud,
                "Plazo de insignias"
            )

            self._validar_rango_inicio_fin(
                acto.inicio_solicitud_cirios,
                acto.fin_solicitud_cirios,
                "Plazo de cirios"
            )

            if acto_dt and acto.fin_solicitud_cirios > acto_dt:
                raise ValidationError(
                    "Plazo de cirios mal configurado: no puede finalizar después de la fecha del acto."
                )

        elif acto.modalidad == Acto.ModalidadReparto.UNIFICADO:
            self._validar_rango_inicio_fin(
                acto.inicio_solicitud,
                acto.fin_solicitud,
                "Plazo de solicitud"
            )

            if acto_dt and acto.fin_solicitud > acto_dt:
                raise ValidationError(
                    "Plazo de solicitud mal configurado: no puede finalizar después de la fecha del acto."
                )