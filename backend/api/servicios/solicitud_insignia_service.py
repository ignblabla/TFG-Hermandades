from datetime import datetime, time
import uuid
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Acto, CuerpoPertenencia, Cuota, Hermano, PapeletaSitio, Puesto, PreferenciaSolicitud


class SolicitudInsigniaService:
    """
    Servicio centralizado para la gestión de solicitudes de papeleta de sitio.
    Maneja tanto la modalidad UNIFICADA como la TRADICIONAL (Insignias y Cirios por separado).
    """

    MAX_PREFERENCIAS_PERMITIDAS = 20

    @transaction.atomic
    def procesar_solicitud_insignia_tradicional(self, hermano: Hermano, acto: Acto, preferencias_data: list, vinculado_a = None):
        """
        [MODALIDAD TRADICIONAL - FASE 1]
        """
        if vinculado_a is not None:
            raise ValidationError("Las solicitudes de insignia no permiten vincularse con otro hermano.")

        ahora = timezone.now()

        cuerpos_hermano_set = set(hermano.cuerpos.values_list('nombre_cuerpo', flat=True))

        self._validar_configuracion_acto_tradicional(acto)
        self._validar_plazo_vigente(ahora, acto.inicio_solicitud, acto.fin_solicitud, "insignias")

        self._validar_hermano_apto_para_solicitar(hermano, cuerpos_hermano_set)
        self._validar_edad_minima_insignia(hermano, acto)

        self._validar_unicidad(hermano, acto)

        self._validar_limites_preferencias(preferencias_data)
        self._validar_preferencias_insignia_tradicional(hermano, acto, preferencias_data, cuerpos_hermano_set)

        try:
            papeleta = self._crear_papeleta_base(hermano, acto, ahora)
            papeleta.es_solicitud_insignia = True
            papeleta.save(update_fields=['es_solicitud_insignia'])

        except IntegrityError:
            raise ValidationError(
                "Ya existe una solicitud activa tramitada para este hermano. "
                "Por favor, no haga doble clic en el botón de enviar."
            )

        self._guardar_preferencias(papeleta, preferencias_data)

        return papeleta
    

    # -------------------------------------------------------------------------
    # VALIDACIONES
    # -------------------------------------------------------------------------
    def _validar_unicidad(self, hermano, acto):
        """
        Verifica si existe alguna papeleta que BLOQUEE una nueva solicitud.
        Una papeleta bloquea si está 'viva'.
        Una papeleta NO bloquea si está 'muerta' (ANULADA o NO_ASIGNADA).
        """
        estados_ignorable = [
            PapeletaSitio.EstadoPapeleta.ANULADA,
            PapeletaSitio.EstadoPapeleta.NO_ASIGNADA
        ]
        
        existe_activa = PapeletaSitio.objects.filter(
            hermano=hermano, 
            acto=acto
        ).exclude(
            estado_papeleta__in=estados_ignorable
        ).exists()
        
        if existe_activa:
            raise ValidationError("Ya existe una solicitud activa (en proceso o asignada) para este acto.")
        


    def _validar_hermano_apto_para_solicitar(self, hermano: Hermano, cuerpos_hermano_set: set):
        """Agrupa las validaciones de estado del hermano."""
        self._validar_hermano_en_alta(hermano)
        self._validar_hermano_al_corriente_hasta_anio_anterior(hermano)
        self._validar_pertenencia_cuerpos(cuerpos_hermano_set)



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



    def _validar_preferencias_insignia_tradicional(self, hermano: Hermano, acto: Acto, preferencias_data: list, cuerpos_hermano_set: set):
        if not preferencias_data:
            raise ValidationError("Debe indicar al menos una preferencia.")

        self._resolver_y_validar_existencia_puestos(preferencias_data)

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
            self._validar_item_puesto(cuerpos_hermano_set, acto, puesto)



    def _validar_item_puesto(self, cuerpos_hermano_set: set, acto: Acto, puesto: Puesto):
        if puesto.acto_id != acto.id:
            raise ValidationError(f"El puesto '{puesto.nombre}' no pertenece a este acto.")
        
        if not puesto.tipo_puesto.es_insignia:
            raise ValidationError(f"El puesto '{puesto.nombre}' no es una insignia.")

        if not puesto.disponible:
            raise ValidationError(f"El puesto '{puesto.nombre}' no está marcado como disponible.")

        if puesto.tipo_puesto.solo_junta_gobierno:
            if CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO not in cuerpos_hermano_set:
                raise ValidationError(f"El puesto '{puesto.nombre}' es exclusivo para Junta de Gobierno.")



    def _validar_limites_preferencias(self, preferencias_data: list):
        if len(preferencias_data) > self.MAX_PREFERENCIAS_PERMITIDAS:
            raise ValidationError(f"No puede solicitar más de {self.MAX_PREFERENCIAS_PERMITIDAS} puestos.")
        


    def _validar_edad_minima_insignia(self, hermano: Hermano, acto: Acto):
        """
        Valida que el hermano tenga 18 años cumplidos antes de la fecha de inicio de solicitud.
        """
        if not hermano.fecha_nacimiento:
            raise ValidationError(
                "No consta su fecha de nacimiento en la base de datos. "
                "Contacte con secretaría para actualizar su ficha antes de solicitar insignia."
            )

        if not acto.inicio_solicitud:
            fecha_referencia = timezone.now().date()
        else:
            fecha_referencia = acto.inicio_solicitud.date()

        fecha_nacimiento = hermano.fecha_nacimiento

        edad = fecha_referencia.year - fecha_nacimiento.year - (
            (fecha_referencia.month, fecha_referencia.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )

        if edad < 18:
            raise ValidationError(
                f"Para solicitar insignia debe ser mayor de 18 años antes del inicio del plazo ({fecha_referencia.strftime('%d/%m/%Y')})."
            )



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



    def _validar_hermano_en_alta(self, hermano):
        if hermano.estado_hermano != Hermano.EstadoHermano.ALTA:
            raise ValidationError("Solo los hermanos en estado ALTA pueden solicitar papeleta.")
        


    def _validar_hermano_al_corriente_hasta_anio_anterior(self, hermano: Hermano):
        anio_actual = timezone.now().date().year
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
                f"Por favor, contacte con tesorería para regularizar su situación."
            )

        existe_historial = hermano.cuotas.filter(anio__lte=anio_limite).exists()
        
        if not existe_historial:
            raise ValidationError(
                f"No constan cuotas registradas hasta el año {anio_limite}. "
                "Contacte con secretaría para verificar su ficha."
            )



    def _resolver_y_validar_existencia_puestos(self, preferencias_data: list):
        """
        Recorre la lista de preferencias, detecta si 'puesto_solicitado' es un ID (int/str)
        y lo sustituye por la instancia de Puesto correspondiente.
        Realiza una carga masiva (Bulk Fetch) para evitar N+1 queries.
        """
        ids_a_buscar = set()

        for item in preferencias_data:
            val = item.get("puesto_solicitado")
            if isinstance(val, (int, str)) and str(val).isdigit():
                ids_a_buscar.add(int(val))
            elif isinstance(val, Puesto):
                continue
            elif val is None:
                continue
            else:
                raise ValidationError(f"Formato de puesto inválido: {val}")

        if not ids_a_buscar:
            return

        puestos_encontrados = Puesto.objects.filter(
            id__in=ids_a_buscar
        ).select_related('tipo_puesto')

        mapa_puestos = {p.id: p for p in puestos_encontrados}

        ids_encontrados = set(mapa_puestos.keys())
        ids_faltantes = ids_a_buscar - ids_encontrados
        
        if ids_faltantes:
            raise ValidationError(
                f"Los siguientes IDs de puesto no existen: {', '.join(map(str, ids_faltantes))}"
            )

        for item in preferencias_data:
            val = item.get("puesto_solicitado")
            if isinstance(val, (int, str)) and str(val).isdigit():
                item["puesto_solicitado"] = mapa_puestos[int(val)]



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



    def _guardar_preferencias(self, papeleta, preferencias_data):
        PreferenciaSolicitud.objects.bulk_create([
            PreferenciaSolicitud(
                papeleta=papeleta,
                puesto_solicitado=item["puesto_solicitado"],
                orden_prioridad=item["orden_prioridad"],
            )
            for item in preferencias_data
        ])