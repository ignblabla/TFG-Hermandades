from datetime import datetime, time
import uuid
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Acto, CuerpoPertenencia, Cuota, Hermano, PapeletaSitio, Puesto, PreferenciaSolicitud


class SolicitudInsigniaService:
    """
    Servicio centralizado para la gestión de solicitudes de papeleta de sitio.
    Maneja tanto la modalidad UNIFICADA como la TRADICIONAL (Insignias y Cirios por separado).
    """

    @transaction.atomic
    def procesar_solicitud_insignia_tradicional(self, hermano: Hermano, acto: Acto, preferencias_data: list):
        """
        [MODALIDAD TRADICIONAL - FASE 1]
        Solo permite solicitar puestos marcados como insignia.
        Asume que el objeto 'acto' es válido y coherente (garantizado por Acto.clean).
        """
        ahora = timezone.now()

        self._validar_configuracion_acto_tradicional(acto)

        self._validar_hermano_apto_para_solicitar(hermano)

        self._validar_unicidad(hermano, acto)

        self._validar_plazo_vigente(ahora, acto.inicio_solicitud, acto.fin_solicitud, "insignias")

        self._validar_preferencias_insignia_tradicional(hermano, acto, preferencias_data)

        papeleta = self._crear_papeleta_base(hermano, acto, ahora)
        papeleta.es_solicitud_insignia = True
        papeleta.save(update_fields=['es_solicitud_insignia'])

        self._guardar_preferencias(papeleta, preferencias_data)

        return papeleta

    # -------------------------------------------------------------------------
    # VALIDACIONES DE ACTO (Contexto)
    # -------------------------------------------------------------------------
    def _validar_configuracion_acto_tradicional(self, acto: Acto):
        """
        Verifica que el acto sea del tipo correcto para este endpoint.
        """
        if not (acto.tipo_acto and acto.tipo_acto.requiere_papeleta):
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

    # -------------------------------------------------------------------------
    # VALIDACIONES DE HERMANO
    # -------------------------------------------------------------------------
    def _validar_hermano_apto_para_solicitar(self, hermano: Hermano):
        """Agrupa las validaciones de estado del hermano."""
        self._validar_hermano_en_alta(hermano)
        self._validar_hermano_al_corriente_hasta_anio_anterior(hermano)
        self._validar_pertenencia_cuerpos(hermano)


    def _validar_hermano_en_alta(self, hermano: Hermano):
        if hermano.estado_hermano != Hermano.EstadoHermano.ALTA:
            raise ValidationError("Solo los hermanos en estado ALTA pueden solicitar papeleta.")
        

    def _validar_hermano_al_corriente_hasta_anio_anterior(self, hermano: Hermano):
        anio_actual = timezone.now().date().year
        anio_limite = anio_actual - 1

        qs = hermano.cuotas.filter(anio__lte=anio_limite)
        if not qs.exists():
            raise ValidationError(f"No constan cuotas registradas hasta el año {anio_limite}. Contacte con secretaría.")

        estados_ok = [Cuota.EstadoCuota.PAGADA, Cuota.EstadoCuota.EXENTO]
        cuota_pendiente = qs.exclude(estado__in=estados_ok).order_by('anio').first()

        if cuota_pendiente:
            raise ValidationError(
                f"Consta una cuota pendiente del año {cuota_pendiente.anio}. Contacte con tesorería."
            )
        

    def _validar_pertenencia_cuerpos(self, hermano):
        cuerpos_permitidos = {
            CuerpoPertenencia.NombreCuerpo.NAZARENOS,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL,
            CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO,
        }
        mis_cuerpos = set(hermano.cuerpos.values_list('nombre_cuerpo', flat=True))
        
        if not mis_cuerpos:
            return
        
        cuerpos_invalidos = mis_cuerpos - cuerpos_permitidos
        if cuerpos_invalidos:
            raise ValidationError("Tu cuerpo de pertenencia actual no permite solicitar papeleta.")
        

    def _validar_unicidad(self, hermano, acto):
        existe = PapeletaSitio.objects.filter(
            hermano=hermano, 
            acto=acto
        ).exclude(
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
        ).exists()
        
        if existe:
            raise ValidationError("Ya existe una solicitud activa para este acto.")

    # -------------------------------------------------------------------------
    # VALIDACIONES DE PREFERENCIAS (Inputs del usuario)
    # -------------------------------------------------------------------------
    def _validar_preferencias_insignia_tradicional(self, hermano: Hermano, acto: Acto, preferencias_data: list):
        if not preferencias_data:
            raise ValidationError("Debe indicar al menos una preferencia.")

        puestos = []
        prioridades = []
        
        for item in preferencias_data:
            puesto = item.get("puesto_solicitado")
            prioridad = item.get("orden_prioridad")
            
            if not puesto or prioridad is None:
                raise ValidationError("Datos de preferencia incompletos.")
            
            puestos.append(puesto)
            prioridades.append(prioridad)

        self._validar_prioridades_consecutivas(prioridades)
        self._validar_puestos_unicos(puestos)

        for puesto in puestos:
            self._validar_item_puesto(hermano, acto, puesto)


    def _validar_prioridades_consecutivas(self, prioridades: list):
        if len(prioridades) != len(set(prioridades)):
            raise ValidationError("No puede haber orden de prioridad duplicado.")
        
        if any(p < 1 for p in prioridades):
            raise ValidationError("El orden de prioridad debe ser mayor que cero.")

        if sorted(prioridades) != list(range(1, len(prioridades) + 1)):
            raise ValidationError("El orden de prioridad debe ser consecutivo empezando por 1.")
        

    def _validar_puestos_unicos(self, puestos: list):
        if len(puestos) != len(set(p for p in puestos if p)):
            raise ValidationError("No puede solicitar el mismo puesto varias veces.")
        

    def _validar_item_puesto(self, hermano: Hermano, acto: Acto, puesto: Puesto):
        if puesto.acto_id != acto.id:
            raise ValidationError(f"El puesto '{puesto.nombre}' no pertenece a este acto.")
        
        if not puesto.tipo_puesto.es_insignia:
            raise ValidationError(f"El puesto '{puesto.nombre}' no es una insignia. (Fase Tradicional).")

        if not puesto.disponible:
            raise ValidationError(f"El puesto '{puesto.nombre}' no está marcado como disponible.")

        if puesto.tipo_puesto.solo_junta_gobierno:
            es_junta = hermano.cuerpos.filter(
                nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()
            if not es_junta:
                raise ValidationError(f"El puesto '{puesto.nombre}' es exclusivo para Junta de Gobierno.")

    # -------------------------------------------------------------------------
    # CREACIÓN Y GUARDADO
    # -------------------------------------------------------------------------
    def _crear_papeleta_base(self, hermano, acto, fecha_solicitud):
        return PapeletaSitio.objects.create(
            hermano=hermano,
            acto=acto,
            anio=acto.fecha.year,
            fecha_solicitud=fecha_solicitud,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            codigo_verificacion=uuid.uuid4().hex[:8].upper()
        )
    

    def _guardar_preferencias(self, papeleta, preferencias_data):
        PreferenciaSolicitud.objects.bulk_create([
            PreferenciaSolicitud(
                papeleta=papeleta,
                puesto_solicitado=item["puesto_solicitado"],
                orden_prioridad=item["orden_prioridad"],
            )
            for item in preferencias_data
        ])