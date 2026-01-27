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
def _validar_fechas_acto(data):
    tipo_acto = data.get('tipo_acto')
    modalidad = data.get('modalidad')
    fecha_acto = data.get('fecha')
    
    if not tipo_acto.requiere_papeleta:
        campos_prohibidos = ['modalidad', 'inicio_solicitud', 'fin_solicitud', 'inicio_solicitud_cirios', 'fin_solicitud_cirios']
        if any(data.get(campo) is not None for campo in campos_prohibidos):
            raise ValidationError("Un acto que no requiere papeleta no puede tener modalidad ni fechas de solicitud.")
        return data

    errors = {}

    if not modalidad:
        errors['modalidad'] = "La modalidad es obligatoria para actos con papeleta."
    if not data.get('inicio_solicitud'):
        errors['inicio_solicitud'] = "La fecha de inicio de solicitud es obligatoria."
    if not data.get('fin_solicitud'):
        errors['fin_solicitud'] = "La fecha de fin de solicitud es obligatoria."

    if modalidad == Acto.ModalidadReparto.TRADICIONAL:
        if not data.get('inicio_solicitud_cirios'):
            errors['inicio_solicitud_cirios'] = "El inicio de cirios es obligatorio en modalidad tradicional."
        if not data.get('fin_solicitud_cirios'):
            errors['fin_solicitud_cirios'] = "El fin de cirios es obligatorio en modalidad tradicional."
            
    elif modalidad == Acto.ModalidadReparto.UNIFICADO:
        if data.get('inicio_solicitud_cirios') or data.get('fin_solicitud_cirios'):
            errors['modalidad'] = "En modalidad Unificada no se deben definir fechas de cirios independientes."

    if errors:
        raise ValidationError(errors)

    inicio_insignias = data.get('inicio_solicitud')
    fin_insignias = data.get('fin_solicitud')
    inicio_cirios = data.get('inicio_solicitud_cirios')
    fin_cirios = data.get('fin_solicitud_cirios')

    fechas = {
        'inicio_solicitud': inicio_insignias,
        'fin_solicitud': fin_insignias,
        'inicio_solicitud_cirios': inicio_cirios,
        'fin_solicitud_cirios': fin_cirios
    }

    for campo, valor in fechas.items():
        if valor and fecha_acto and valor >= fecha_acto:
            errors[campo] = f"Debe ser anterior a la fecha del acto ({fecha_acto.strftime('%d/%m/%Y %H:%M')})."

    if inicio_insignias and fin_insignias and inicio_insignias >= fin_insignias:
        errors['fin_solicitud'] = "La fecha de fin debe ser posterior al inicio."
    
    if inicio_cirios and fin_cirios and inicio_cirios >= fin_cirios:
        errors['fin_solicitud_cirios'] = "La fecha de fin de cirios debe ser posterior al inicio."

    if modalidad == Acto.ModalidadReparto.TRADICIONAL:
        if fin_insignias and inicio_cirios and inicio_cirios <= fin_insignias:
            errors['inicio_solicitud_cirios'] = "El reparto de cirios debe empezar después de que terminen las insignias."

    if errors:
        raise ValidationError(errors)
    
    return data

@transaction.atomic
def crear_acto_service(usuario_solicitante, data_validada):
    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para crear actos. Se requiere ser Administrador.")
    
    nombre = data_validada.get('nombre')
    fecha = data_validada.get('fecha')
    if Acto.objects.filter(nombre=nombre, fecha__date=fecha.date()).exists():
        raise ValidationError(f"Ya existe el acto '{nombre}' en esa fecha.")
    
    data_limpia = _validar_fechas_acto(data_validada)

    nuevo_acto = Acto.objects.create(**data_limpia)
    return nuevo_acto

# -----------------------------------------------------------------------------
# SERVICES: ACTUALIZAR ACTO
# -----------------------------------------------------------------------------
def _validar_cambio_fecha(acto: Acto, nueva_fecha):
    if acto.fecha == nueva_fecha:
        return

    now = timezone.now()
    fecha_limite = acto.inicio_solicitud

    if fecha_limite and now >= fecha_limite:
        raise ValidationError({
            'fecha': (
                f"No se puede modificar la fecha del acto porque el plazo de solicitud ya ha comenzado "
                f"({fecha_limite.strftime('%d/%m/%Y %H:%M')})."
            )
        })
        
def _validar_coherencia_fechas(acto, data):
    fecha_acto = data.get('fecha', acto.fecha)
    modalidad = data.get('modalidad', acto.modalidad)
    tipo_acto = data.get('tipo_acto', acto.tipo_acto)
    
    data_final = data.copy()

    if not tipo_acto.requiere_papeleta:
        data_final.update({
            'modalidad': None,
            'inicio_solicitud': None,
            'fin_solicitud': None,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None
        })
        return data_final

    if modalidad == Acto.ModalidadReparto.UNIFICADO:
        data_final.update({
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None
        })

    inicio_insignias = data_final.get('inicio_solicitud', acto.inicio_solicitud)
    fin_insignias = data_final.get('fin_solicitud', acto.fin_solicitud)
    inicio_cirios = data_final.get('inicio_solicitud_cirios', acto.inicio_solicitud_cirios)
    fin_cirios = data_final.get('fin_solicitud_cirios', acto.fin_solicitud_cirios)

    errores = {}

    if modalidad == Acto.ModalidadReparto.TRADICIONAL:
        if not all([inicio_insignias, fin_insignias, inicio_cirios, fin_cirios]):
            raise ValidationError({
                'modalidad': "En modalidad TRADICIONAL deben definirse los plazos de insignias y de cirios."
            })

    if fecha_acto:
        if inicio_insignias and inicio_insignias >= fecha_acto:
            errores['inicio_solicitud'] = f"El inicio de insignias debe ser anterior al acto."
        if fin_insignias and fin_insignias >= fecha_acto:
            errores['fin_solicitud'] = "El fin de insignias debe ser anterior al acto."
        if inicio_cirios and inicio_cirios >= fecha_acto:
            errores['inicio_solicitud_cirios'] = "El inicio de cirios debe ser anterior al acto."
        if fin_cirios and fin_cirios >= fecha_acto:
            errores['fin_solicitud_cirios'] = "El fin de cirios debe ser anterior al acto."

    if inicio_insignias and fin_insignias and inicio_insignias >= fin_insignias:
        errores['fin_solicitud'] = "La fecha fin de insignias debe ser posterior a su inicio."
    
    if inicio_cirios and fin_cirios and inicio_cirios >= fin_cirios:
        errores['fin_solicitud_cirios'] = "La fecha fin de cirios debe ser posterior a su inicio."

    if modalidad == Acto.ModalidadReparto.TRADICIONAL:
        if fin_insignias and inicio_cirios and inicio_cirios <= fin_insignias:
            errores['inicio_solicitud_cirios'] = (
                f"El plazo de cirios debe empezar tras el de insignias ({fin_insignias.strftime('%d/%m/%Y %H:%M')})."
            )

    if errores:
        raise ValidationError(errores)
    
    return data_final
    

@transaction.atomic
def actualizar_acto_service(usuario_solicitante, acto_id, data_validada):
    if not getattr(usuario_solicitante, "esAdmin", False):
        raise PermissionDenied("No tienes permisos para editar actos. Se requiere ser Administrador.")
    
    try:
        acto = Acto.objects.select_related('tipo_acto').get(pk=acto_id)
    except Acto.DoesNotExist:
        raise ValidationError({"detail": "El acto solicitado no existe."})
    
    nuevo_nombre = data_validada.get('nombre', acto.nombre)
    nueva_fecha = data_validada.get('fecha', acto.fecha)
    nuevo_tipo = data_validada.get('tipo_acto', acto.tipo_acto)

    if Acto.objects.filter(nombre=nuevo_nombre, fecha__date=nueva_fecha.date()).exclude(pk=acto.id).exists():
        raise ValidationError(f"Ya existe otro acto llamado '{nuevo_nombre}' en esa fecha.")
    
    if nuevo_tipo != acto.tipo_acto:
        if acto.puestos_disponibles.exists():
            raise ValidationError({
                'tipo_acto': "No se puede cambiar el Tipo de Acto porque ya existen puestos generados. Elimine los puestos primero."
            })
        
    _validar_cambio_fecha(acto, nueva_fecha)

    data_limpia = _validar_coherencia_fechas(acto, data_validada)

    for campo, valor in data_limpia.items():
        setattr(acto, campo, valor)
    
    acto.save()
    return acto