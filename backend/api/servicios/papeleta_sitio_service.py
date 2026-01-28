import uuid
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Acto, CuerpoPertenencia, Hermano, PapeletaSitio, Puesto, PreferenciaSolicitud

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
                
        self._validar_requiere_papeleta(acto)

        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            raise ValidationError("Este endpoint es solo para actos de modalidad TRADICIONAL.")

        self._validar_pertenencia_cuerpos(hermano)
        self._validar_unicidad(hermano, acto)

        if not acto.inicio_solicitud or not acto.fin_solicitud:
            raise ValidationError("Plazo de insignias no configurado.")
        
        if ahora < acto.inicio_solicitud or ahora > acto.fin_solicitud:
            raise ValidationError("Fuera del plazo de solicitud de insignias.")

        for item in preferencias_data:
            puesto = item['puesto_solicitado']
            if not puesto.tipo_puesto.es_insignia:
                raise ValidationError(f"El puesto '{puesto.nombre}' no es una insignia. En plazo tradicional, los cirios se piden aparte.")

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
        """
        [MODALIDAD TRADICIONAL - FASE 2]
        Solicitud directa de puesto (Cirio/Diputado) con lógica de VINCULACIÓN.
        """
        ahora = timezone.now()

        self._validar_requiere_papeleta(acto)

        if acto.modalidad != Acto.ModalidadReparto.TRADICIONAL:
            raise ValidationError("Este endpoint es solo para actos de modalidad TRADICIONAL.")
        
        self._validar_pertenencia_cuerpos(hermano)

        tiene_insignia_emitida = PapeletaSitio.objects.filter(
            hermano=hermano, acto=acto, es_solicitud_insignia=True, 
            estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA
        ).exists()

        if tiene_insignia_emitida:
            raise ValidationError("Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio.")
        
        solicitud_insignia_pendiente = PapeletaSitio.objects.filter(
            hermano=hermano, acto=acto, es_solicitud_insignia=True,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        ).first()

        if solicitud_insignia_pendiente:
            solicitud_insignia_pendiente.estado_papeleta = PapeletaSitio.EstadoPapeleta.ANULADA
            solicitud_insignia_pendiente.save(update_fields=['estado_papeleta'])

        self._validar_unicidad(hermano, acto)

        if not acto.inicio_solicitud_cirios or not acto.fin_solicitud_cirios:
            raise ValidationError("Plazo de cirios no configurado.")
        
        if ahora < acto.inicio_solicitud_cirios:
            raise ValidationError(f"El plazo de cirios comienza el {acto.inicio_solicitud_cirios}.")
        
        if ahora > acto.fin_solicitud_cirios:
            raise ValidationError("El plazo de solicitud de cirios ha finalizado.")

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

    def _validar_requiere_papeleta(self, acto):
        if not acto.tipo_acto.requiere_papeleta:
            raise ValidationError(f"El acto '{acto.nombre}' no admite solicitudes.")

    def _validar_pertenencia_cuerpos(self, hermano):
        cuerpos_permitidos = [
            CuerpoPertenencia.NombreCuerpo.NAZARENOS,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL
        ]
        mis_cuerpos = hermano.pertenencias_cuerpos.all() # Asumiendo related_name correcto
        
        mis_cuerpos_ids = hermano.cuerpos.values_list('nombre_cuerpo', flat=True)
        if mis_cuerpos_ids and not any(c in cuerpos_permitidos for c in mis_cuerpos_ids):
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