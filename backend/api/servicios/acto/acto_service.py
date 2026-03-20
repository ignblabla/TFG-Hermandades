from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import QueryDict
from django.utils import timezone

from api.models import Acto, TipoActo

# -----------------------------------------------------------------------------
# SERVICES: CREAR ACTO
# -----------------------------------------------------------------------------
@transaction.atomic
def crear_acto_service(usuario_solicitante, data_validada):
    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para crear actos. Se requiere ser Administrador.")

    nombre = data_validada.get("nombre")
    fecha = data_validada.get("fecha")

    if isinstance(nombre, str):
        nombre = nombre.strip()
        data_validada["nombre"] = nombre

    if nombre and fecha:
        if Acto.objects.filter(nombre=nombre, fecha__date=fecha.date()).exists():
            raise ValidationError({
                "non_field_errors": [f"Ya existe un acto llamado '{nombre}' para la fecha {fecha.strftime('%d/%m/%Y')}."]
            })

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

    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para editar actos. Se requiere ser Administrador.")

    try:
        acto = Acto.objects.select_related("tipo_acto").get(pk=acto_id)
    except Acto.DoesNotExist:
        raise ValidationError({"detail": "El acto solicitado no existe."})

    campos_permitidos = {
        "nombre", "descripcion", "fecha", "modalidad", "lugar",
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

    campos_update = {
        "nombre", "descripcion", "fecha", "modalidad",
        "tipo_acto", "lugar",
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



# -----------------------------------------------------------------------------
# SERVICES: LISTAR ACTOS
# -----------------------------------------------------------------------------
class ActoService:
    @staticmethod
    def get_todos_los_actos():
        """
        Devuelve el queryset con todos los actos, ordenados por fecha
        para garantizar una paginación predecible y consistente.
        """
        return Acto.objects.all().order_by('-fecha')