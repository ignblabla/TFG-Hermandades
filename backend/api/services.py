from django.http import QueryDict
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from .models import Acto, PapeletaSitio, Puesto, TipoActo, TipoPuesto
from django.db import transaction
from django.contrib.auth import get_user_model
# from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()

# -----------------------------------------------------------------------------
# SERVICES: ACTO
# -----------------------------------------------------------------------------

def _validar_integridad_fechas_acto(fecha_acto):
    """
    Método auxiliar (privado) para reutilizar la lógica de validación temporal.
    Valida:
    1. Que la fecha sea futura (fecha y hora > ahora).
    2. Que la fecha esté dentro del año actual.
    """

    ahora = timezone.now()

    if fecha_acto.year != ahora.year:
        raise ValidationError({
            "fecha": f"Solo se permite programar actos para el año en curso ({ahora.year})."
        })
    
    if fecha_acto <= ahora:
        raise ValidationError({
            "fecha": "La fecha y hora del acto deben ser posteriores al momento actual."
        })
    

def _procesar_fechas_solicitud_papeleta(tipo_acto, fecha_acto, inicio_solicitud, fin_solicitud):
    """
    Aplica la lógica de negocio estricta para las fechas de solicitud de papeleta.
    Retorna una tupla (inicio_procesado, fin_procesado).
    """

    if not tipo_acto.requiere_papeleta:
        return None, None
    
    else:
        if not inicio_solicitud:
            raise ValidationError({"inicio_solicitud": "Este tipo de acto requiere especificar fecha de inicio de solicitud."})
        if not fin_solicitud:
            raise ValidationError({"fin_solicitud": "Este tipo de acto requiere especificar fecha de fin de solicitud."})
        
        if inicio_solicitud >= fin_solicitud:
            raise ValidationError({"fin_solicitud": "La fecha de fin de solicitud debe ser posterior a la fecha de inicio."})
        
        if fecha_acto and fin_solicitud >= fecha_acto:
            raise ValidationError({"fin_solicitud": "El periodo de solicitud debe finalizar antes de la fecha de celebración del acto."})
        
        return inicio_solicitud, fin_solicitud


@transaction.atomic
def create_acto_service(usuario, data_validada):
    """
    Crea un acto aplicando toda la lógica de negocio.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para crear actos. Contacta con Secretaría.")
    
    nombre = data_validada.get('nombre')
    fecha_acto = data_validada.get('fecha')
    tipo_acto = data_validada.get('tipo_acto')

    raw_inicio = data_validada.get('inicio_solicitud')
    raw_fin = data_validada.get('fin_solicitud')

    _validar_integridad_fechas_acto(fecha_acto)

    if Acto.objects.filter(nombre=nombre, fecha__date=fecha_acto.date()).exists():
        raise ValidationError({"non_field_errors": [f"Ya existe un acto con el nombre '{nombre}' para el día {fecha_acto.date().strftime('%d/%m/%Y')}."]})
    

    inicio_final, fin_final = _procesar_fechas_solicitud_papeleta(tipo_acto, fecha_acto, raw_inicio, raw_fin)

    data_validada['inicio_solicitud'] = inicio_final
    data_validada['fin_solicitud'] = fin_final

    acto = Acto.objects.create(**data_validada)
    return acto


@transaction.atomic
def update_acto_service(usuario, acto_id, data_validada):
    """
    Actualiza un acto, asegurando la coherencia del estado final.
    """
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar actos. Contacta con Secretaría.")
    
    acto = get_object_or_404(Acto, pk=acto_id)

    nuevo_tipo = data_validada.get('tipo_acto', acto.tipo_acto)

    if nuevo_tipo != acto.tipo_acto:
        if acto.puestos_disponibles.exists():
            raise ValidationError({"tipo_acto": "No se puede cambiar el tipo de acto porque ya tiene puestos asignados. Elimínelos primero."})
        
    nueva_fecha = data_validada.get('fecha', acto.fecha)
    nuevo_nombre = data_validada.get('nombre', acto.nombre)

    if 'fecha' in data_validada:
        _validar_integridad_fechas_acto(nueva_fecha)

    existe_duplicado = Acto.objects.filter(
        nombre = nuevo_nombre,
        fecha__date = nueva_fecha.date()
    ).exclude(pk=acto_id).exists()

    if existe_duplicado:
        raise ValidationError({"non_field_errors": [f"Ya existe otro acto con ese nombre en la fecha indicada."]})
    
    inicio_input = data_validada.get('inicio_solicitud', acto.inicio_solicitud)
    fin_input = data_validada.get('fin_solicitud', acto.fin_solicitud)

    inicio_final, fin_final = _procesar_fechas_solicitud_papeleta(
        nuevo_tipo, nueva_fecha, inicio_input, fin_input
    )

    data_validada['inicio_solicitud'] = inicio_final
    data_validada['fin_solicitud'] = fin_final

    for attr, value in data_validada.items():
        setattr(acto, attr, value)

    acto.save()
    return acto

# -----------------------------------------------------------------------------
# SERVICES: PUESTO
# -----------------------------------------------------------------------------
def create_puesto_service(usuario, data_validada):
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para crear puestos.")
    
    acto = data_validada.get('acto')
    nombre = data_validada.get('nombre')

    # Regla de Negocio: Solo actos que requieren papeleta pueden tener puestos
    if not acto.tipo_acto.requiere_papeleta:
        raise ValidationError({
            "acto": f"El acto '{acto.nombre}' es de tipo '{acto.tipo_acto.get_tipo_display()}' y no admite puestos."
        })
    
    if Puesto.objects.filter(acto=acto, nombre=nombre).exists():
        raise ValidationError({"nombre": [f"Ya existe un puesto con el nombre '{nombre}' en este acto."]})
    
    puesto = Puesto.objects.create(**data_validada)
    return puesto


def update_puesto_service(usuario, puesto_id, data_validada):
    if not getattr(usuario, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar puestos.")

    puesto = get_object_or_404(Puesto, pk=puesto_id)
    acto = puesto.acto
    
    if not acto.tipo_acto.requiere_papeleta:
        raise ValidationError({"acto": "Este acto ya no admite la gestión de puestos."})
    
    nuevo_nombre = data_validada.get('nombre', puesto.nombre)

    if Puesto.objects.filter(acto=acto, nombre=nuevo_nombre).exclude(pk=puesto_id).exists():
        raise ValidationError({"nombre": [f"Ya existe un puesto con el nombre '{nuevo_nombre}' en este acto."]})
    
    for attr, value in data_validada.items():
        setattr(puesto, attr, value)

    puesto.save()
    return puesto

# -----------------------------------------------------------------------------
# SERVICES: TIPO DE PUESTO
# -----------------------------------------------------------------------------
def get_tipos_puesto_service():
    """
    Servicio para recuperar el catálogo completo de tipos de puestos.
    Puede incluir lógica de filtrado si fuera necesaria en el futuro.
    """
    return TipoPuesto.objects.all()


# -----------------------------------------------------------------------------
# SERVICES: TIPO DE ACTO
# -----------------------------------------------------------------------------
def get_tipos_acto_service():
    """Retorna todos los tipos de actos disponibles"""
    return TipoActo.objects.all()

# -----------------------------------------------------------------------------
# SERVICES: PANEL DE ADMINISTRADOR
# -----------------------------------------------------------------------------
def get_listado_hermanos_service(usuario_solicitante):
    """
    Retorna el listado completo de hermanos.
    Regla de Negocio: Solo accesible por administradores.
    """
    if not getattr(usuario_solicitante, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para visualizar el listado de hermanos.")
    
    hermanos = User.objects.all().order_by('numero_registro')
    return hermanos

@transaction.atomic
def update_hermano_por_admin_service(usuario_solicitante, hermano_id, data_validada):
    if not getattr(usuario_solicitante, 'esAdmin', False):
        raise PermissionDenied("No tienes permisos para editar los datos de otros hermanos.")
    
    hermano = get_object_or_404(User, pk=hermano_id)

    for attr, value in data_validada.items():
        if attr == 'password':
            if value:
                hermano.set_password(value)
        else:
            setattr(hermano, attr, value)
    
    hermano.save()
    return hermano

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

# -----------------------------------------------------------------------------
# SERVICES: CREAR ACTO
# -----------------------------------------------------------------------------
@transaction.atomic
def crear_acto_service(usuario_solicitante, data_validada):
    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para crear actos. Se requiere ser Administrador.")

    nombre = data_validada.get("nombre")
    fecha = data_validada.get("fecha")
    if nombre and fecha and Acto.objects.filter(nombre=nombre, fecha__date=fecha.date()).exists():
        raise ValidationError(f"Ya existe el acto '{nombre}' en esa fecha.")

    nuevo_acto = Acto.objects.create(**data_validada)

    return nuevo_acto

# -----------------------------------------------------------------------------
# SERVICES: ACTUALIZAR ACTO
# -----------------------------------------------------------------------------
def _validar_cambio_fecha(acto: Acto, nueva_fecha, data_dict=None):
    """
    Política A (más segura):
    - Si YA ha comenzado el plazo de solicitud según el estado actual en BD (acto.inicio_solicitud),
        NO se permite cambiar la fecha del acto.
    - Aunque el payload intente modificar inicio_solicitud a la vez (anti-bypass).
    """
    if nueva_fecha is None or acto.fecha == nueva_fecha:
        return

    if not acto.tipo_acto.requiere_papeleta:
        return

    now = timezone.now()
    fecha_limite_actual = acto.inicio_solicitud

    if fecha_limite_actual and now >= fecha_limite_actual:
        intento_cambiar_inicio = data_dict is not None and "inicio_solicitud" in data_dict
        extra = " (y no se puede esquivar modificando inicio_solicitud en el mismo update)." if intento_cambiar_inicio else "."

        raise ValidationError({
            "fecha": (
                "No se puede modificar la fecha del acto porque el plazo de solicitud ya ha comenzado "
                f"({fecha_limite_actual.strftime('%d/%m/%Y %H:%M')}){extra}"
            )
        })
    


def _normalizar_campos_papeleta(acto):
    """
    Normaliza el estado final del acto (ya con cambios aplicados) para que:
    - Si NO requiere papeleta: limpia modalidad y todos los plazos.
    - Si modalidad UNIFICADO: limpia plazos de cirios.
    """
    if acto.tipo_acto and not acto.tipo_acto.requiere_papeleta:
        acto.modalidad = None
        acto.inicio_solicitud = None
        acto.fin_solicitud = None
        acto.inicio_solicitud_cirios = None
        acto.fin_solicitud_cirios = None
        return

    if acto.modalidad == Acto.ModalidadReparto.UNIFICADO:
        acto.inicio_solicitud_cirios = None
        acto.fin_solicitud_cirios = None



def _normalizar_payload_acto(data_validada):
    """
    Devuelve un dict seguro para servicios:
    - DRF serializer.validated_data (dict) → OK
    - QueryDict → valida que no haya multivalue y luego .dict()
    - Otros → ValidationError
    """

    if isinstance(data_validada, QueryDict):
        errores = {}
        for key in data_validada.keys():
            if len(data_validada.getlist(key)) > 1:
                errores[key] = "No se permiten múltiples valores para este campo."

        if errores:
            raise ValidationError(errores)

        data = data_validada.dict()

    elif isinstance(data_validada, dict):
        data = dict(data_validada)

        errores = {}
        for campo, valor in data.items():
            if isinstance(valor, (list, tuple)):
                errores[campo] = "No se permiten múltiples valores para este campo."

        if errores:
            raise ValidationError(errores)

    else:
        raise ValidationError({
            "non_field_errors": "Formato de datos inválido para actualizar el acto."
        })

    return data


@transaction.atomic
def actualizar_acto_service(usuario_solicitante, acto_id, data_validada):
    # -------------------------------------------------------------------------
    # Permisos
    # -------------------------------------------------------------------------
    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para editar actos. Se requiere ser Administrador.")

    # -------------------------------------------------------------------------
    # Cargar acto
    # -------------------------------------------------------------------------
    try:
        acto = Acto.objects.select_related("tipo_acto").get(pk=acto_id)
    except Acto.DoesNotExist:
        raise ValidationError({"detail": "El acto solicitado no existe."})

    # -------------------------------------------------------------------------
    # Lista blanca estricta + prohibir claves desconocidas
    # -------------------------------------------------------------------------
    campos_permitidos = {
        "nombre", "descripcion", "fecha", "modalidad",
        "tipo_acto", "tipo_acto_id",
        "inicio_solicitud", "fin_solicitud",
        "inicio_solicitud_cirios", "fin_solicitud_cirios",
    }

    data_dict = _normalizar_payload_acto(data_validada)

    claves_desconocidas = sorted(set(data_dict.keys()) - campos_permitidos)
    if claves_desconocidas:
        raise ValidationError({
            "non_field_errors": [
                "Payload inválido: contiene campos no permitidos: " + ", ".join(claves_desconocidas)
            ]
        })

    # -------------------------------------------------------------------------
    # Resolver tipo_acto si viene por ID (y validar existencia)
    # -------------------------------------------------------------------------
    tipo_acto_obj = data_dict.get("tipo_acto", None)
    tipo_acto_id = data_dict.get("tipo_acto_id", None)

    if tipo_acto_obj is not None and tipo_acto_id is not None:
        obj_id = getattr(tipo_acto_obj, "id", None)

        if obj_id is None:
            raise ValidationError({
                "tipo_acto": "tipo_acto debe ser una instancia de TipoActo cuando se envía junto a tipo_acto_id."
            })

        if obj_id != tipo_acto_id:
            raise ValidationError({
                "tipo_acto": "Ambigüedad: tipo_acto y tipo_acto_id no coinciden.",
                "tipo_acto_id": "Ambigüedad: tipo_acto_id no coincide con tipo_acto."
            })

    if tipo_acto_id is not None:
        try:
            data_dict["tipo_acto"] = TipoActo.objects.get(pk=tipo_acto_id)
        except TipoActo.DoesNotExist:
            raise ValidationError({"tipo_acto": "El tipo de acto indicado no existe."})

    # -------------------------------------------------------------------------
    # Calcular valores finales (para reglas de negocio)
    # -------------------------------------------------------------------------
    nuevo_nombre = data_dict.get("nombre", acto.nombre)
    nueva_fecha = data_dict.get("fecha", acto.fecha)
    nuevo_tipo = data_dict.get("tipo_acto", acto.tipo_acto)

    if nuevo_nombre and nueva_fecha:
        if Acto.objects.filter(
            nombre=nuevo_nombre,
            fecha__date=nueva_fecha.date()
        ).exclude(pk=acto.id).exists():
            raise ValidationError(f"Ya existe otro acto llamado '{nuevo_nombre}' en esa fecha.")

    if nuevo_tipo != acto.tipo_acto and acto.puestos_disponibles.exists():
        raise ValidationError({
            "tipo_acto": (
                "No se puede cambiar el Tipo de Acto porque ya existen puestos generados. "
                "Elimine los puestos primero."
            )
        })

    _validar_cambio_fecha(acto, nueva_fecha, data_dict=data_dict)

    # -------------------------------------------------------------------------
    # Aplicar cambios (estricto: solo campos de update real)
    # -------------------------------------------------------------------------
    campos_update = {
        "nombre", "descripcion", "fecha", "modalidad",
        "tipo_acto",
        "inicio_solicitud", "fin_solicitud",
        "inicio_solicitud_cirios", "fin_solicitud_cirios",
    }

    for campo in campos_update:
        if campo in data_dict:
            setattr(acto, campo, data_dict[campo])

    _normalizar_campos_papeleta(acto)

    acto.full_clean()
    acto.save()

    return acto