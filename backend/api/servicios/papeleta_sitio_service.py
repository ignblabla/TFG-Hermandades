from datetime import datetime, time
import uuid
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Acto, CuerpoPertenencia, Cuota, Hermano, PapeletaSitio, Puesto, PreferenciaSolicitud

class PapeletaSitioService:
    """
    Servicio para la gestión de solicitudes en Modalidad UNIFICADA (Express).
    
    Lógica de Negocio:
    - Permite solicitar Insignias (Lista de Preferencias) Y/O Puesto General (Cirio/Diputado/Etc) en el mismo acto.
    - Si se solicitan insignias, el Puesto General actúa como 'Puesto de Reserva' en caso de no obtener la insignia.
    - No permite vinculación (acompañantes).
    """
    MAX_PREFERENCIAS_PERMITIDAS = 20
    ESTADOS_NO_ACTIVOS = (
        PapeletaSitio.EstadoPapeleta.ANULADA,
        PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
    )

    @transaction.atomic
    def procesar_solicitud_unificada(self, hermano: Hermano, acto: Acto, datos_solicitud: dict):
        # ----------------------------------------------------------------------------------
        Hermano.objects.select_for_update().only("id").get(pk=hermano.pk)

        ahora = timezone.now()

        self._validar_configuracion_acto_unificado(acto)
        self._validar_plazo_vigente(ahora, acto.inicio_solicitud, acto.fin_solicitud, nombre_plazo="solicitud de papeletas")

        cuerpos_hermano_set = set(hermano.cuerpos.values_list('nombre_cuerpo', flat=True))
        self._validar_hermano_apto_para_solicitar(hermano, cuerpos_hermano_set, ahora)
        # ----------------------------------------------------------------------------------

        self._validar_unicidad(hermano, acto)

        preferencias_data = datos_solicitud.get('preferencias', [])
        puesto_general_id = datos_solicitud.get('puesto_general_id')

        if not preferencias_data and not puesto_general_id:
            raise ValidationError("La solicitud está vacía. Debe seleccionar al menos un puesto general o una insignia.")
        
        if preferencias_data:
            self._validar_edad_minima_insignia(hermano, acto)
            self._validar_limites_preferencias(preferencias_data)
            self._validar_preferencias_insignia(hermano, acto, preferencias_data, cuerpos_hermano_set)

        puesto_general_obj = None
        if puesto_general_id:
            try:
                puesto_general_obj = Puesto.objects.select_related('tipo_puesto').get(pk=puesto_general_id)
            except Puesto.DoesNotExist:
                raise ValidationError("El puesto general seleccionado no existe.")
            
            self._validar_item_puesto_general(cuerpos_hermano_set, acto, puesto_general_obj)

        try:
            papeleta = self._crear_papeleta(
                hermano, 
                acto, 
                ahora, 
                puesto_general=puesto_general_obj, 
                tiene_insignias=bool(preferencias_data)
            )

            if preferencias_data:
                self._guardar_preferencias(papeleta, preferencias_data)

            return papeleta

        except IntegrityError:
            raise ValidationError("Error de integridad. Es posible que ya exista una solicitud procesándose.")
        
    # =========================================================================
    # VALIDACIONES DE ACTO Y HERMANO
    # =========================================================================

    def _validar_configuracion_acto_unificado(self, acto: Acto):
        if acto is None or acto.tipo_acto_id is None:
            raise ValidationError({"tipo_acto": "El tipo de acto es obligatorio."})
        
        if not acto.tipo_acto.requiere_papeleta:
            raise ValidationError(f"Este acto '{acto.nombre}' no admite solicitudes de papeleta.")
        
        if acto.modalidad != Acto.ModalidadReparto.UNIFICADO:
            raise ValidationError(f"Este proceso es exclusivo para actos de modalidad UNIFICADO.")
        

        
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
        

    # =========================================================================
    # LÓGICA DE PUESTO GENERAL (CIRIO/NO INSIGNIA)
    # =========================================================================

    def _validar_item_puesto_general(self, cuerpos_hermano_set: set, acto: Acto, puesto: Puesto):
        """
        Validaciones específicas para un puesto único general (no insignia).
        """
        if not puesto:
            raise ValidationError("Debe seleccionar un puesto válido.")

        if puesto.acto_id != acto.id:
            raise ValidationError("El puesto general no pertenece a este acto.")

        if puesto.tipo_puesto.es_insignia:
            raise ValidationError(
                f"El puesto '{puesto.nombre}' es una Insignia. "
                "Las insignias deben añadirse a la lista de preferencias, no como puesto general."
            )

        if not puesto.disponible:
            raise ValidationError(f"El puesto general '{puesto.nombre}' no está disponible.")

        if (puesto.tipo_puesto.solo_junta_gobierno and 
            CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value not in cuerpos_hermano_set):
            raise ValidationError(f"El puesto '{puesto.nombre}' es exclusivo para Junta de Gobierno.")
    

    # =========================================================================
    # LÓGICA DE PREFERENCIAS (INSIGNIAS)
    # =========================================================================

    def _validar_limites_preferencias(self, preferencias_data: list):
        if len(preferencias_data) > self.MAX_PREFERENCIAS_PERMITIDAS:
            raise ValidationError(f"No puede solicitar más de {self.MAX_PREFERENCIAS_PERMITIDAS} puestos.")
        

    def _validar_preferencias_insignia(self, hermano: Hermano, acto: Acto, preferencias_data: list, cuerpos_hermano_set: set):
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



    # =========================================================================
    # PERSISTENCIA
    # =========================================================================

    def _crear_papeleta(self, hermano, acto, fecha, puesto_general=None, tiene_insignias=False):
        """
        Crea la papeleta.
        - puesto: Se rellena con el puesto_general (cirio/diputado).
        - es_solicitud_insignia: True si hay preferencias.
        
        Interpretación: Si es_solicitud_insignia=True y puesto!=None, 
        el puesto es el "fallback" si no consigue insignia.
        """
        return PapeletaSitio.objects.create(
            hermano=hermano,
            acto=acto,
            anio=acto.fecha.year,
            fecha_solicitud=fecha,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,

            puesto=puesto_general, 
            
            es_solicitud_insignia=tiene_insignias,
            
            vinculado_a=None,
            codigo_verificacion=uuid.uuid4().hex[:8].upper()
        )

    def _guardar_preferencias(self, papeleta, preferencias_data):
        objs = [
            PreferenciaSolicitud(
                papeleta=papeleta,
                puesto_solicitado=item['puesto_solicitado'],
                orden_prioridad=item['orden_prioridad']
            ) for item in preferencias_data
        ]
        PreferenciaSolicitud.objects.bulk_create(objs)