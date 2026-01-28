from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import PermissionDenied, ValidationError
from unittest.mock import patch
import datetime
from django.db import transaction

from ....services import actualizar_acto_service
from ....models import Acto, TipoActo, TipoPuesto, Puesto
from api.tests.factories import HermanoFactory


class ActualizarActoServiceTest(TestCase):

    def setUp(self):
        """
        Configuración inicial común para las pruebas de actualización.
        Creamos usuarios, un tipo de acto y un ACTO YA EXISTENTE para intentar modificarlo.
        """
        self.usuario_no_admin = HermanoFactory(esAdmin=False)
        self.usuario_admin = HermanoFactory(esAdmin=True)

        self.tipo_acto = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        self.fecha_original = timezone.now() + timedelta(days=30)
        self.nombre_original = "Acto Original"
        
        self.acto_existente = Acto.objects.create(
            nombre=self.nombre_original,
            fecha=self.fecha_original,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            descripcion="Descripción original",
            inicio_solicitud=self.fecha_original - timedelta(days=20),
            fin_solicitud=self.fecha_original - timedelta(days=10),
            inicio_solicitud_cirios=self.fecha_original - timedelta(days=9),
            fin_solicitud_cirios=self.fecha_original - timedelta(days=5),
        )



    def test_actualizar_acto_cambio_nombre_simple(self):
        """
        [Positivo] Actualización simple de campos básicos (solo nombre).
        
        Input:
            - Usuario: Admin.
            - Acto: Existente (self.acto_existente).
            - Data: Solo contiene {'nombre': 'Nuevo Nombre'}.
        Resultado:
            - El nombre del acto se actualiza en BBDD.
            - El resto de datos (fecha, descripción, tipo) permanecen intactos.
        """
        nuevo_nombre = "Acto Renombrado 2025"
        data_parcial = {
            'nombre': nuevo_nombre
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.usuario_admin,
            acto_id=self.acto_existente.id,
            data_validada=data_parcial
        )

        self.assertEqual(acto_actualizado.nombre, nuevo_nombre)

        self.acto_existente.refresh_from_db()

        self.assertEqual(self.acto_existente.nombre, nuevo_nombre)

        self.assertEqual(self.acto_existente.descripcion, "Descripción original")
        self.assertEqual(self.acto_existente.fecha, self.fecha_original)
        self.assertEqual(self.acto_existente.modalidad, Acto.ModalidadReparto.TRADICIONAL)



    def test_actualizar_acto_cambio_tipo_sin_dependencias(self):
        """
        [Positivo] Cambio de Tipo de Acto cuando NO hay dependencias (puestos creados).
        
        Input:
            - Acto existente: "Estación de Penitencia" (Requiere papeleta).
            - Nuevo tipo: "Convivencia" (NO requiere papeleta).
            - Condición: El acto NO tiene puestos asignados.
        Resultado:
            - Se actualiza el tipo_acto correctamente.
            - Efecto colateral esperado: La modalidad y las fechas se limpian (None)
                automáticamente porque el nuevo tipo no usa papeletas.
        """
        tipo_nuevo = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        self.assertEqual(self.acto_existente.puestos_disponibles.count(), 0)

        data_parcial = {
            'tipo_acto': tipo_nuevo
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.usuario_admin,
            acto_id=self.acto_existente.id,
            data_validada=data_parcial
        )

        self.assertEqual(acto_actualizado.tipo_acto, tipo_nuevo)

        self.assertIsNone(
            acto_actualizado.modalidad, 
            "La modalidad debería haberse reseteado a None al cambiar a un tipo sin papeleta."
        )
        self.assertIsNone(acto_actualizado.inicio_solicitud)
        self.assertIsNone(acto_actualizado.fin_solicitud)



    def test_actualizar_acto_cambio_fecha_valido(self):
        """
        [Positivo] Cambio de fecha del acto válido (Moviendo el acto más al futuro).
        
        Input:
            - Acto existente con solicitud que empieza dentro de 10 días.
            - Cambio: Movemos la fecha del acto 1 mes más adelante.
            - Condición: Los plazos de solicitud existentes (inicio/fin) siguen quedando
                anteriores a la nueva fecha del acto.
        Resultado:
            - Se actualiza la fecha del acto correctamente.
        """

        nueva_fecha = timezone.now() + timedelta(days=60)
        
        data_parcial = {
            'fecha': nueva_fecha
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.usuario_admin,
            acto_id=self.acto_existente.id,
            data_validada=data_parcial
        )

        self.assertEqual(acto_actualizado.fecha, nueva_fecha)

        self.acto_existente.refresh_from_db()
        self.assertEqual(self.acto_existente.fecha, nueva_fecha)

        self.assertLess(
            self.acto_existente.fin_solicitud, 
            self.acto_existente.fecha,
            "La fecha de fin de solicitud debe seguir siendo anterior a la nueva fecha del acto."
        )



    def test_actualizar_acto_fallo_seguridad_no_admin(self):
        """
        [Negativo] Fallo de Seguridad: Intento de actualización por usuario NO Admin.
        
        Input:
            - usuario.esAdmin = False (usuario_no_admin).
            - Acto existente.
            - Data válida (nombre nuevo).
        Resultado:
            - PermissionDenied.
            - El acto NO debe sufrir modificaciones en la BBDD.
        """
        nuevo_nombre = "Nombre Hackeado"
        data_parcial = {
            'nombre': nuevo_nombre
        }

        with self.assertRaises(PermissionDenied) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_no_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_parcial
            )

        mensaje_esperado = "No tienes permisos para editar actos."
        self.assertIn("No tienes permisos", str(contexto.exception))

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(self.acto_existente.nombre, nuevo_nombre)
        self.assertEqual(
            self.acto_existente.nombre, 
            self.nombre_original,
            "El nombre del acto no debería haber cambiado tras un intento no autorizado."
        )



    def test_actualizar_acto_inexistente_error(self):
        """
        [Negativo] Intento de actualizar un Acto cuyo ID no existe en la BBDD.
        
        Input:
            - Usuario: Admin.
            - acto_id: 99999 (Inexistente).
        Resultado:
            - ValidationError con mensaje específico.
        """
        id_inexistente = 99999
        
        data_parcial = {
            'nombre': 'Intento Fantasma'
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=id_inexistente,
                data_validada=data_parcial
            )

        exception = contexto.exception

        mensaje_esperado = "El acto solicitado no existe"
        if hasattr(exception, 'detail'):
            self.assertIn(mensaje_esperado, str(exception.detail))
        else:
            self.assertIn(mensaje_esperado, str(exception))



    def test_actualizar_acto_duplicidad_nombre_fecha_con_otro_acto_error(self):
        """
        [Negativo] Intento de actualizar un acto para que tenga el mismo nombre y fecha 
        que OTRO acto diferente ya existente en la BBDD.
        
        Input:
            - Acto A (Editando): self.acto_existente.
            - Acto B (Obstáculo): "Acto Bloqueante" en Fecha B.
            - Cambio solicitado en A: nombre="Acto Bloqueante", fecha=Fecha B.
        Resultado:
            - ValidationError ("Ya existe otro acto...").
            - El Acto A conserva sus datos originales.
        """
        fecha_conflicto = timezone.now() + timedelta(days=100)
        nombre_conflicto = "Acto Bloqueante"
        
        Acto.objects.create(
            nombre=nombre_conflicto,
            fecha=fecha_conflicto,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=fecha_conflicto - timedelta(days=10),
            fin_solicitud=fecha_conflicto - timedelta(days=5)
        )

        data_duplicada = {
            'nombre': nombre_conflicto,
            'fecha': fecha_conflicto
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_duplicada
            )

        exception = contexto.exception

        mensaje_esperado = f"Ya existe otro acto llamado '{nombre_conflicto}' en esa fecha."
        
        if hasattr(exception, 'detail'):
            self.assertIn(mensaje_esperado, str(exception.detail))
        else:
            self.assertIn(mensaje_esperado, str(exception))

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(self.acto_existente.nombre, nombre_conflicto)
        self.assertEqual(self.acto_existente.nombre, self.nombre_original)



    def test_actualizar_acto_mismo_nombre_fecha_falso_positivo_exito(self):
        """
        [Positivo] Caso de "Falso Positivo" en Duplicidad (Idempotencia parcial).
        Se intenta actualizar el acto enviando SU propio nombre y fecha actuales.
        
        Input:
            - Acto existente (ID X).
            - Data: nombre = "Nombre X", fecha = "Fecha X" (Mismos valores que ya tiene).
        Resultado:
            - Éxito (No lanza ValidationError).
            - El sistema debe excluir el propio ID del acto al comprobar duplicados.
        """
        data_identica = {
            'nombre': self.nombre_original,
            'fecha': self.fecha_original,
            'descripcion': 'Solo cambio la descripción, lo demás sigue igual'
        }

        try:
            acto_actualizado = actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_identica
            )
        except ValidationError as e:
            self.fail(f"El servicio falló incorrectamente detectando duplicidad consigo mismo: {e}")

        self.assertIsNotNone(acto_actualizado)

        self.acto_existente.refresh_from_db()

        self.assertEqual(self.acto_existente.nombre, self.nombre_original)
        self.assertEqual(self.acto_existente.fecha, self.fecha_original)

        self.assertEqual(
            self.acto_existente.descripcion, 
            'Solo cambio la descripción, lo demás sigue igual'
        )



    def test_actualizar_acto_bloqueo_cambio_tipo_con_puestos_error(self):
        """
        [Negativo] Intento de cambiar el 'Tipo de Acto' cuando ya existen puestos asociados.
        
        Input:
            - Acto existente con al menos 1 Puesto creado (dependencia).
            - Se intenta cambiar 'tipo_acto' a otro diferente.
        Resultado:
            - ValidationError.
            - Mensaje: "No se puede cambiar el Tipo de Acto porque ya existen puestos..."
            - El tipo de acto original no cambia.
        """
        nuevo_tipo = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        tipo_puesto_test = TipoPuesto.objects.create(
            nombre_tipo="Vara Genérica", 
            es_insignia=True
        )

        Puesto.objects.create(
            acto=self.acto_existente,
            tipo_puesto=tipo_puesto_test,
            nombre="Vara de prueba",
            numero_maximo_asignaciones=1,
            disponible=True
        )

        self.assertTrue(self.acto_existente.puestos_disponibles.exists())

        data_cambio_prohibido = {
            'tipo_acto': nuevo_tipo
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_cambio_prohibido
            )

        exception = contexto.exception

        mensaje_esperado_parte = "No se puede cambiar el Tipo de Acto porque ya existen puestos"
        
        if hasattr(exception, 'detail'):
            self.assertIn(mensaje_esperado_parte, str(exception.detail))
        else:
            self.assertIn(mensaje_esperado_parte, str(exception))

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(self.acto_existente.tipo_acto, nuevo_tipo)
        self.assertEqual(
            self.acto_existente.tipo_acto, 
            self.tipo_acto, 
            "El tipo de acto no debió cambiar debido al bloqueo por dependencias."
        )



    def test_actualizar_acto_cambio_fecha_antes_inicio_plazo_exito(self):
        """
        [Positivo] Cambio de fecha del acto cuando el plazo de solicitud AÚN NO ha comenzado.
        
        Input:
            - timezone.now() < inicio_solicitud (El plazo es futuro).
            - Se cambia la fecha del acto (respetando que sea posterior al fin de solicitud).
        Resultado:
            - Permitido. La actualización se guarda correctamente.
        """
        base_time = timezone.now()

        inicio_futuro = base_time + timedelta(days=5)
        fin_futuro = base_time + timedelta(days=10)
        fecha_acto_original = base_time + timedelta(days=20)
        
        acto_futuro = Acto.objects.create(
            nombre="Acto Aún No Iniciado",
            fecha=fecha_acto_original,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=inicio_futuro,
            fin_solicitud=fin_futuro,
            inicio_solicitud_cirios=None, 
            fin_solicitud_cirios=None
        )

        self.assertGreater(acto_futuro.inicio_solicitud, timezone.now())

        nueva_fecha_acto = base_time + timedelta(days=15)
        
        data_cambio = {
            'fecha': nueva_fecha_acto
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.usuario_admin,
            acto_id=acto_futuro.id,
            data_validada=data_cambio
        )

        self.assertEqual(acto_actualizado.fecha, nueva_fecha_acto)
        
        acto_futuro.refresh_from_db()
        self.assertEqual(acto_futuro.fecha, nueva_fecha_acto)



    def test_actualizar_acto_error_cambio_fecha_plazo_iniciado(self):
        """
        [Negativo] Intento de cambiar la fecha del Acto cuando el plazo de solicitud YA ha comenzado.
        
        Input:
            - inicio_solicitud < timezone.now() (Plazo abierto o ya pasado).
            - Se intenta cambiar el campo 'fecha'.
        Resultado:
            - ValidationError.
            - Mensaje: "No se puede modificar la fecha... el plazo de solicitud ya ha comenzado".
            - La fecha original no cambia.
        """
        base_time = timezone.now()

        inicio_pasado = base_time - timedelta(days=1)
        fin_futuro = base_time + timedelta(days=5)
        fecha_acto_original = base_time + timedelta(days=20)
        
        acto_en_curso = Acto.objects.create(
            nombre="Acto Ya Iniciado",
            fecha=fecha_acto_original,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=inicio_pasado,
            fin_solicitud=fin_futuro,
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None
        )

        self.assertLess(acto_en_curso.inicio_solicitud, timezone.now())

        data_cambio = {
            'fecha': fecha_acto_original + timedelta(days=5)
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=acto_en_curso.id,
                data_validada=data_cambio
            )
            
        exception = contexto.exception

        mensaje_esperado_parte = "el plazo de solicitud ya ha comenzado"
        
        if hasattr(exception, 'detail'):
            self.assertIn(mensaje_esperado_parte, str(exception.detail))
        else:
            self.assertIn(mensaje_esperado_parte, str(exception))

        acto_en_curso.refresh_from_db()
        self.assertEqual(
            acto_en_curso.fecha, 
            fecha_acto_original,
            "La fecha del acto no debió cambiar porque el proceso de solicitud ya está en marcha."
        )



    def test_actualizar_acto_cambio_a_no_requiere_papeleta_limpieza_automatica(self):
        """
        [Positivo] Cambio de Tipo de Acto a uno que NO requiere papeleta.
        
        Input:
            - Acto original: TRADICIONAL, con todas las fechas de solicitud rellenas.
            - Cambio: tipo_acto = 'CONVIVENCIA' (requiere_papeleta=False).
        Resultado:
            - El tipo de acto cambia.
            - Los campos de configuración de reparto (modalidad, fechas solicitud) 
                se eliminan (None) automáticamente para mantener la coherencia.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        self.assertEqual(self.acto_existente.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        self.assertIsNotNone(self.acto_existente.inicio_solicitud)
        self.assertIsNotNone(self.acto_existente.inicio_solicitud_cirios)

        data_cambio = {
            'tipo_acto': tipo_sin_papeleta
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.usuario_admin,
            acto_id=self.acto_existente.id,
            data_validada=data_cambio
        )

        self.assertEqual(acto_actualizado.tipo_acto, tipo_sin_papeleta)

        self.acto_existente.refresh_from_db()

        self.assertIsNone(
            self.acto_existente.modalidad, 
            "La modalidad debería haberse limpiado al cambiar a un acto sin papeleta."
        )
        
        self.assertIsNone(self.acto_existente.inicio_solicitud, "Inicio solicitud debe ser None")
        self.assertIsNone(self.acto_existente.fin_solicitud, "Fin solicitud debe ser None")
        self.assertIsNone(self.acto_existente.inicio_solicitud_cirios, "Inicio cirios debe ser None")
        self.assertIsNone(self.acto_existente.fin_solicitud_cirios, "Fin cirios debe ser None")



    def test_actualizar_acto_cambio_modalidad_tradicional_a_unificado_limpieza(self):
        """
        [Positivo] Cambio de Modalidad de TRADICIONAL a UNIFICADO.
        
        Input:
            - Acto original: TRADICIONAL (Tiene 4 fechas: inicio/fin solicitud + inicio/fin cirios).
            - Cambio: modalidad = 'UNIFICADO'.
        Resultado:
            - La modalidad cambia.
            - Las fechas específicas de 'Cirios' (Fase 2) se eliminan (None) automáticamente.
            - Las fechas de solicitud general (Fase 1) se mantienen intactas.
        """
        self.assertEqual(self.acto_existente.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        self.assertIsNotNone(self.acto_existente.inicio_solicitud_cirios)
        self.assertIsNotNone(self.acto_existente.fin_solicitud_cirios)

        fecha_inicio_original = self.acto_existente.inicio_solicitud

        data_cambio = {
            'modalidad': Acto.ModalidadReparto.UNIFICADO
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.usuario_admin,
            acto_id=self.acto_existente.id,
            data_validada=data_cambio
        )

        self.assertEqual(acto_actualizado.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.acto_existente.refresh_from_db()

        self.assertIsNone(
            self.acto_existente.inicio_solicitud_cirios, 
            "La fecha de inicio de cirios debe limpiarse al pasar a Unificado."
        )
        self.assertIsNone(
            self.acto_existente.fin_solicitud_cirios,
            "La fecha de fin de cirios debe limpiarse al pasar a Unificado."
        )

        self.assertEqual(
            self.acto_existente.inicio_solicitud, 
            fecha_inicio_original,
            "Las fechas de solicitud principales no deben perderse al cambiar la modalidad."
        )



    def test_actualizar_acto_cambio_unificado_a_tradicional_datos_incompletos_error(self):
        """
        [Negativo] Cambio de UNIFICADO a TRADICIONAL sin aportar las fechas nuevas requeridas.
        
        Contexto:
            - Un acto UNIFICADO tiene 'inicio_solicitud_cirios' y 'fin_solicitud_cirios' a NULL.
        Input:
            - Cambio: modalidad = 'TRADICIONAL'.
            - Datos extra: Se actualiza 'inicio_solicitud' (insignias), pero NO se envían las fechas de cirios.
        Resultado:
            - ValidationError. 
            - El servicio devuelve el error en el campo 'modalidad' indicando que faltan los plazos.
        """
        fecha_acto = timezone.now() + timedelta(days=50)
        
        acto_unificado = Acto.objects.create(
            nombre="Acto Unificado Test",
            fecha=fecha_acto,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=fecha_acto - timedelta(days=20),
            fin_solicitud=fecha_acto - timedelta(days=10),
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None
        )

        data_incompleta = {
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(days=25) 
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=acto_unificado.id,
                data_validada=data_incompleta
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn('modalidad', errores, "El error debe reportarse en el campo 'modalidad'")
        
        mensaje_esperado = "En modalidad TRADICIONAL deben definirse los plazos de insignias y de cirios."
        self.assertIn(mensaje_esperado, str(errores['modalidad']))

        acto_unificado.refresh_from_db()
        self.assertEqual(acto_unificado.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_actualizar_acto_solapamiento_fases_tradicional_error(self):
        """
        [Negativo] Intento de actualizar fechas provocando un solapamiento de fases 
        en modalidad TRADICIONAL.
        
        Input:
            - Modalidad: TRADICIONAL.
            - fin_solicitud (Insignias): Día X a las 12:00.
            - inicio_solicitud_cirios (Cirios): Día X a las 11:00.
        Resultado:
            - ValidationError.
            - El sistema detecta que el inicio de la fase 2 es anterior al fin de la fase 1.
        """
        dia_conflicto = timezone.now() + timedelta(days=15)

        fin_insignias_nuevo = dia_conflicto.replace(hour=12, minute=0, second=0)

        inicio_cirios_nuevo = dia_conflicto.replace(hour=11, minute=0, second=0)
        
        data_solapada = {
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'fin_solicitud': fin_insignias_nuevo,
            'inicio_solicitud_cirios': inicio_cirios_nuevo,
            'inicio_solicitud': dia_conflicto - timedelta(days=2),
            'fin_solicitud_cirios': dia_conflicto + timedelta(days=2)
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_solapada
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn('inicio_solicitud_cirios', errores, "El error debe estar en el inicio de cirios")

        mensaje_error = str(errores['inicio_solicitud_cirios'])
        self.assertIn("debe empezar tras el de insignias", mensaje_error)

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(self.acto_existente.fin_solicitud, fin_insignias_nuevo)
        self.assertNotEqual(self.acto_existente.inicio_solicitud_cirios, inicio_cirios_nuevo)



    def test_actualizar_acto_fin_solicitud_posterior_acto_error(self):
        """
        [Negativo] Intento de actualizar 'fin_solicitud' para que sea posterior a la fecha del acto.
        
        Input:
            - Fecha Acto: Día X (self.fecha_original).
            - Nuevo fin_solicitud: Día X + 1 (Posterior al acto).
        Resultado:
            - ValidationError en el campo 'fin_solicitud'.
            - Mensaje: "El fin de insignias debe ser anterior al acto."
        """
        fecha_invalida = self.fecha_original + timedelta(days=1)
        
        data_invalida = {
            'fin_solicitud': fecha_invalida
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_invalida
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn('fin_solicitud', errores, "El error debe estar asociado al campo 'fin_solicitud'")

        mensaje_esperado = "El fin de insignias debe ser anterior al acto."
        
        self.assertIn(mensaje_esperado, str(errores['fin_solicitud']))

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(self.acto_existente.fin_solicitud, fecha_invalida)



    def test_actualizar_acto_frontera_exacta_inicio_plazo_bloqueo(self):
        """
        [Negativo] Caso Frontera: Modificación en el SEGUNDO EXACTO de inicio.
        
        Contexto:
            - Validar que el bloqueo de cambio de fecha incluye el límite exacto.
        Input:
            - inicio_solicitud = T.
            - timezone.now() simulado = T.
        Código evaluado:
            - if now >= acto.inicio_solicitud: raise ValidationError
        Resultado:
            - ValidationError. (El plazo se considera iniciado en el segundo 0).
        """
        instante_frontera = timezone.now() + timedelta(days=10)
        
        acto_frontera = Acto.objects.create(
            nombre="Acto Frontera Exacta",
            fecha=instante_frontera + timedelta(days=20),
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=instante_frontera,
            fin_solicitud=instante_frontera + timedelta(days=5),
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None
        )

        data_cambio = {
            'fecha': instante_frontera + timedelta(days=25)
        }

        with patch('django.utils.timezone.now', return_value=instante_frontera):
            
            with self.assertRaises(ValidationError) as contexto:
                actualizar_acto_service(
                    usuario_solicitante=self.usuario_admin,
                    acto_id=acto_frontera.id,
                    data_validada=data_cambio
                )

        exception = contexto.exception

        mensaje_esperado_parte = "el plazo de solicitud ya ha comenzado"
        
        if hasattr(exception, 'detail'):
            self.assertIn(mensaje_esperado_parte, str(exception.detail))
        else:
            self.assertIn(mensaje_esperado_parte, str(exception))

        acto_frontera.refresh_from_db()
        self.assertNotEqual(acto_frontera.fecha, instante_frontera + timedelta(days=25))



    def test_actualizar_acto_frontera_fin_insignias_igual_inicio_cirios_error(self):
        """
        [Negativo] Caso Frontera TRADICIONAL: Fin de insignias == Inicio de cirios.
        
        Contexto:
            - Validación de coherencia de fechas en actualización.
        Input:
            - fin_solicitud (Insignias) = T.
            - inicio_solicitud_cirios (Cirios) = T.
        Código evaluado:
            - if inicio_cirios <= fin_insignias: Error.
        Resultado:
            - ValidationError. (Requiere inicio_cirios > fin_insignias).
        """
        dia_base = timezone.now() + timedelta(days=20)
        instante_frontera = dia_base.replace(hour=10, minute=0, second=0, microsecond=0)
        
        data_frontera = {
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': instante_frontera - timedelta(hours=5),
            'fin_solicitud_cirios': instante_frontera + timedelta(hours=5),
            'fin_solicitud': instante_frontera,
            'inicio_solicitud_cirios': instante_frontera
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_frontera
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn('inicio_solicitud_cirios', errores, "El error debe estar en 'inicio_solicitud_cirios'")

        mensaje_error = str(errores['inicio_solicitud_cirios'])
        self.assertIn("debe empezar tras", mensaje_error)

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(self.acto_existente.fin_solicitud, instante_frontera)



    def test_actualizar_acto_cambio_fecha_sin_inicio_solicitud_previo_exito(self):
        """
        [Positivo] Valor Crítico: Cambio de fecha en Acto sin configuración de plazos previa.
        
        Contexto:
            - El acto existe pero 'inicio_solicitud' es None (ej: no requería papeleta).
        Input:
            - Se cambia la fecha del acto.
        Código evaluado:
            - if acto.inicio_solicitud and ... (La condición de bloqueo debe saltarse).
        Resultado:
            - Éxito. La fecha se actualiza sin restricciones de plazo iniciado.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )
        
        fecha_original = timezone.now() + timedelta(days=10)
        
        acto_sin_plazos = Acto.objects.create(
            nombre="Acto Sin Plazos",
            fecha=fecha_original,
            tipo_acto=tipo_sin_papeleta,
            modalidad=None,
            inicio_solicitud=None,
            fin_solicitud=None,
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None
        )

        nueva_fecha = fecha_original + timedelta(days=5)
        
        data_cambio = {
            'fecha': nueva_fecha
        }

        try:
            acto_actualizado = actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=acto_sin_plazos.id,
                data_validada=data_cambio
            )
        except ValidationError as e:
            self.fail(f"No debió validarse el plazo iniciado porque inicio_solicitud es None: {e}")

        self.assertEqual(acto_actualizado.fecha, nueva_fecha)
        
        acto_sin_plazos.refresh_from_db()
        self.assertEqual(acto_sin_plazos.fecha, nueva_fecha)



    def test_actualizar_acto_partial_update_incoherencia_mezcla_datos_error(self):
        """
        [Negativo] Incoherencia temporal en Actualización Parcial (Mixing Data).
        
        Contexto:
            - El servicio debe validar combinando los datos nuevos con los existentes.
        Input:
            - BBDD: inicio_solicitud = Día 10.
            - Request: fin_solicitud = Día 9. (No se envía inicio).
        Resultado:
            - ValidationError.
            - El sistema detecta que el nuevo fin (9) es anterior al inicio existente (10).
        """
        base_time = timezone.now()

        dia_9 = base_time + timedelta(days=9)
        dia_10 = base_time + timedelta(days=10)
        dia_20 = base_time + timedelta(days=20)
        dia_30 = base_time + timedelta(days=30)
        
        acto_mix = Acto.objects.create(
            nombre="Acto Mix Datos",
            fecha=dia_30,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=dia_10,
            fin_solicitud=dia_20,
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None
        )

        data_parcial = {
            'fin_solicitud': dia_9
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=acto_mix.id,
                data_validada=data_parcial
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn('fin_solicitud', errores, "El error debe estar en fin_solicitud")

        mensaje = str(errores['fin_solicitud'])
        self.assertIn("posterior a su inicio", mensaje)

        acto_mix.refresh_from_db()
        self.assertNotEqual(acto_mix.fin_solicitud, dia_9)
        self.assertEqual(acto_mix.fin_solicitud, dia_20)



    def test_actualizar_acto_inicio_solicitud_posterior_acto_error(self):
        """
        [Negativo] Validación de coherencia: Inicio de solicitud posterior a la fecha del acto.
        
        Código testado:
            if inicio_insignias >= fecha_acto:
                errores['inicio_solicitud'] = "El inicio de insignias debe ser anterior al acto."
        
        Input:
            - Fecha Acto: Día X.
            - Nuevo inicio_solicitud: Día X + 1 hora (Posterior al acto).
        Resultado:
            - ValidationError en el campo 'inicio_solicitud'.
        """
        fecha_acto = self.fecha_original

        fecha_inicio_invalida = fecha_acto + timedelta(hours=1)
        
        data_invalida = {
            'inicio_solicitud': fecha_inicio_invalida
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_invalida
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn(
            'inicio_solicitud', 
            errores, 
            "El error debería estar en la clave 'inicio_solicitud' según tu código."
        )

        mensaje_esperado = "El inicio de insignias debe ser anterior al acto."
        self.assertIn(mensaje_esperado, str(errores['inicio_solicitud']))

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(self.acto_existente.inicio_solicitud, fecha_inicio_invalida)



    def test_actualizar_acto_inicio_cirios_posterior_acto_error(self):
        """
        [Negativo] Validación de coherencia: Inicio de cirios posterior a la fecha del acto.
        
        Código testado:
            if inicio_cirios and inicio_cirios >= fecha_acto:
                errores['inicio_solicitud_cirios'] = "El inicio de cirios debe ser anterior al acto."
        
        Input:
            - Modalidad: TRADICIONAL (para que aplique la lógica de cirios).
            - Fecha Acto: Día X.
            - Nuevo inicio_solicitud_cirios: Día X + 1 hora (Posterior al acto).
        Resultado:
            - ValidationError en el campo 'inicio_solicitud_cirios'.
            - Mensaje: "El inicio de cirios debe ser anterior al acto."
        """
        fecha_acto = self.fecha_original

        inicio_cirios_invalido = fecha_acto + timedelta(hours=1)
        
        data_invalida = {
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud_cirios': inicio_cirios_invalido
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_invalida
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn(
            'inicio_solicitud_cirios', 
            errores, 
            "El error debe estar en la clave 'inicio_solicitud_cirios'."
        )

        mensaje_esperado = "El inicio de cirios debe ser anterior al acto."

        mensaje_recibido = str(errores['inicio_solicitud_cirios'])
        
        self.assertIn(mensaje_esperado, mensaje_recibido)

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(
            self.acto_existente.inicio_solicitud_cirios, 
            inicio_cirios_invalido
        )



    def test_actualizar_acto_fin_cirios_posterior_acto_error(self):
        """
        [Negativo] Validación de coherencia: Fin de cirios posterior a la fecha del acto.
        
        Código testado:
            if fin_cirios and fin_cirios >= fecha_acto:
                errores['fin_solicitud_cirios'] = "El fin de cirios debe ser anterior al acto."
        
        Input:
            - Modalidad: TRADICIONAL (para habilitar el uso de fechas de cirios).
            - Fecha Acto: Día X.
            - Nuevo fin_solicitud_cirios: Día X + 1 minuto (Posterior al acto).
        Resultado:
            - ValidationError en el campo 'fin_solicitud_cirios'.
            - Mensaje exacto: "El fin de cirios debe ser anterior al acto."
        """
        fecha_acto = self.fecha_original

        fin_cirios_invalido = fecha_acto + timedelta(minutes=1)
        
        data_invalida = {
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'fin_solicitud_cirios': fin_cirios_invalido
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                usuario_solicitante=self.usuario_admin,
                acto_id=self.acto_existente.id,
                data_validada=data_invalida
            )

        exception = contexto.exception
        errores = exception.detail if hasattr(exception, 'detail') else {}

        self.assertIn(
            'fin_solicitud_cirios', 
            errores, 
            "El error debe estar asignado a la clave 'fin_solicitud_cirios'."
        )

        mensaje_esperado = "El fin de cirios debe ser anterior al acto."

        mensaje_recibido = str(errores['fin_solicitud_cirios'])
        
        self.assertIn(mensaje_esperado, mensaje_recibido)

        self.acto_existente.refresh_from_db()
        self.assertNotEqual(
            self.acto_existente.fin_solicitud_cirios, 
            fin_cirios_invalido
        )