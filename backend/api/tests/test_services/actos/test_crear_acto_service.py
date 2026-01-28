from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from rest_framework.exceptions import PermissionDenied, ValidationError

from ....models import Acto, TipoActo
from ....services import crear_acto_service
from api.tests.factories import HermanoFactory

User = get_user_model()

class CrearActoServiceTest(TestCase):

    def setUp(self):
        """
        Configuración inicial común para todos los tests de esta clase.
        """
        self.usuario_no_admin = HermanoFactory(esAdmin=False)

        self.usuario_admin = HermanoFactory(esAdmin=True)

        self.tipo_acto = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

    def test_crear_acto_sin_papeleta_valido(self):
        """
        [Positivo] Caso de éxito: Creación de un Acto que NO requiere papeleta.
        
        Input: 
            - tipo_acto.requiere_papeleta = False.
            - data contiene campos básicos.
            - Campos de gestión de papeletas (modalidad, fechas solicitud) son None.
        Resultado: 
            - El servicio crea el acto correctamente sin levantar ValidationError.
            - Los campos de fechas de solicitud se guardan como NULL en BBDD.
        """

        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        fecha_acto = timezone.now() + timedelta(days=15)

        data_validada = {
            'nombre': 'Misa de Hermandad',
            'descripcion': 'Misa mensual',
            'fecha': fecha_acto,
            'tipo_acto': tipo_sin_papeleta,

            'modalidad': None,
            'inicio_solicitud': None,
            'fin_solicitud': None,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        acto_creado = crear_acto_service(self.usuario_admin, data_validada)

        self.assertIsNotNone(acto_creado.id, "El acto debería tener un ID asignado")
        self.assertEqual(Acto.objects.count(), 1, "Debería haber 1 acto en la base de datos")

        self.assertEqual(acto_creado.nombre, 'Misa de Hermandad')
        self.assertEqual(acto_creado.tipo_acto, tipo_sin_papeleta)

        self.assertIsNone(acto_creado.modalidad)
        self.assertIsNone(acto_creado.inicio_solicitud)
        self.assertIsNone(acto_creado.fin_solicitud_cirios)



    def test_crear_acto_sin_papeleta_con_datos_prohibidos_error(self):
        """
        [Negativo] Intento de creación de Acto que NO requiere papeleta, 
        pero enviando datos de gestión de papeletas (fechas/modalidad).
        
        Input:
            - tipo_acto.requiere_papeleta = False.
            - data contiene campos prohibidos (ej. inicio_solicitud).
        Resultado:
            - El servicio lanza ValidationError.
            - El mensaje de error es específico sobre la incompatibilidad.
            - No se guarda nada en la base de datos.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        fecha_acto = timezone.now() + timedelta(days=10)

        data_invalida = {
            'nombre': 'Misa de Difuntos',
            'descripcion': 'Misa solemne',
            'fecha': fecha_acto,
            'tipo_acto': tipo_sin_papeleta,

            'inicio_solicitud': fecha_acto - timedelta(days=5),

            'modalidad': None, 
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        mensaje_error = str(contexto.exception)
        self.assertIn(
            "Un acto que no requiere papeleta no puede tener modalidad ni fechas de solicitud", 
            mensaje_error
        )

        self.assertEqual(
            Acto.objects.filter(nombre='Misa de Difuntos').count(), 
            0, 
            "El acto no debió persistirse en la BBDD"
        )



    def test_crear_acto_unificado_valido(self):
        """
        [Positivo] Caso de éxito: Creación de Acto con papeleta en modalidad UNIFICADA.
        
        Input:
            - requiere_papeleta = True.
            - modalidad = 'UNIFICADO'.
            - Fechas: inicio_solicitud < fin_solicitud < fecha_acto.
            - Fechas de cirios = None (Condición obligatoria para UNIFICADO).
        Resultado:
            - El servicio crea el acto.
            - Se ignoran/permiten nulos en las fechas de cirios.
        """
        fecha_acto = timezone.now() + timedelta(days=60)
        inicio_solicitud = timezone.now() + timedelta(days=10)
        fin_solicitud = timezone.now() + timedelta(days=30)

        data_validada = {
            'nombre': 'Salida Extraordinaria Unificada',
            'descripcion': 'Procesión Magna',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,

            'modalidad': Acto.ModalidadReparto.UNIFICADO,

            'inicio_solicitud': inicio_solicitud,
            'fin_solicitud': fin_solicitud,

            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        acto_creado = crear_acto_service(self.usuario_admin, data_validada)

        self.assertEqual(Acto.objects.count(), 1)
        self.assertEqual(acto_creado.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertEqual(acto_creado.inicio_solicitud, inicio_solicitud)
        self.assertEqual(acto_creado.fin_solicitud, fin_solicitud)

        self.assertIsNone(acto_creado.inicio_solicitud_cirios)
        self.assertIsNone(acto_creado.fin_solicitud_cirios)



    def test_crear_acto_tradicional_valido(self):
        """
        [Positivo] Caso de éxito: Creación de Acto con papeleta en modalidad TRADICIONAL.
        
        Input:
            - requiere_papeleta = True.
            - modalidad = 'TRADICIONAL'.
            - Secuencia temporal estricta:
                Inicio Insignias < Fin Insignias < Inicio Cirios < Fin Cirios < Fecha Acto
        Resultado:
            - El servicio crea el acto.
            - Se validan correctamente los huecos entre fases (sin solapamientos).
        """
        base_time = timezone.now()

        inicio_insignias = base_time + timedelta(days=10)
        fin_insignias    = base_time + timedelta(days=15)
        inicio_cirios    = base_time + timedelta(days=20) 
        fin_cirios       = base_time + timedelta(days=25)
        
        fecha_acto       = base_time + timedelta(days=60)

        data_validada = {
            'nombre': 'Estación de Penitencia 2024',
            'descripcion': 'Salida procesional Jueves Santo',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL, 
            'inicio_solicitud': inicio_insignias,
            'fin_solicitud': fin_insignias,
            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': fin_cirios,
        }

        acto_creado = crear_acto_service(self.usuario_admin, data_validada)

        self.assertEqual(Acto.objects.count(), 1)
        self.assertEqual(acto_creado.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(acto_creado.inicio_solicitud, inicio_insignias)
        self.assertEqual(acto_creado.fin_solicitud, fin_insignias)
        self.assertEqual(acto_creado.inicio_solicitud_cirios, inicio_cirios)
        self.assertEqual(acto_creado.fin_solicitud_cirios, fin_cirios)



    def test_crear_acto_sin_papeleta_con_datos_prohibidos(self):
        """
        [Negativo] Intento de creación de Acto que NO requiere papeleta, 
        pero enviando datos prohibidos (modalidad o fechas).
        
        Input:
            - tipo_acto.requiere_papeleta = False.
            - data incluye 'modalidad' = 'UNIFICADO' (o fechas).
        Resultado:
            - ValidationError con el mensaje específico de bloqueo.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ROSARIO_AURORA,
            requiere_papeleta=False
        )

        fecha_acto = timezone.now() + timedelta(days=15)

        data_invalida = {
            'nombre': 'Rosario de la Aurora 2025',
            'descripcion': 'Rezo del Santo Rosario',
            'fecha': fecha_acto,
            'tipo_acto': tipo_sin_papeleta,

            'modalidad': Acto.ModalidadReparto.UNIFICADO, 
            'inicio_solicitud': fecha_acto - timedelta(days=5)
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        mensaje_esperado = "Un acto que no requiere papeleta no puede tener modalidad ni fechas de solicitud."

        self.assertIn(mensaje_esperado, str(contexto.exception))

        self.assertEqual(Acto.objects.filter(nombre='Rosario de la Aurora 2025').count(), 0)



    def test_crear_acto_con_papeleta_sin_modalidad_error(self):
        """
        [Negativo] Intento de crear un Acto con papeleta (requiere_papeleta=True)
        sin especificar la modalidad de reparto (modalidad=None).
        
        Input:
            - tipo_acto.requiere_papeleta = True.
            - modalidad = None.
        Resultado:
            - ValidationError (DRF) indicando que el campo 'modalidad' es obligatorio.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Vía Crucis Sin Modalidad',
            'descripcion': 'Acto de culto externo',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': None,
            'inicio_solicitud': fecha_acto - timedelta(days=10),
            'fin_solicitud': fecha_acto - timedelta(days=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail' (propio de DRF)")
        
        errores = exception.detail

        self.assertIn('modalidad', errores, "El error debe estar asociado al campo 'modalidad'")

        mensaje_esperado = "La modalidad es obligatoria para actos con papeleta."

        self.assertIn(mensaje_esperado, str(errores['modalidad']))
        self.assertEqual(Acto.objects.filter(nombre='Vía Crucis Sin Modalidad').count(), 0)



    def test_crear_acto_fechas_obligatorias_faltantes_error(self):
        """
        [Negativo] Intento de crear un Acto con papeleta donde falta una de las fechas obligatorias
        (inicio_solicitud o fin_solicitud).
        
        Input:
            - requiere_papeleta = True.
            - modalidad = 'UNIFICADO' (válida).
            - inicio_solicitud = None (FALTANTE).
        Resultado:
            - ValidationError (DRF) indicando que el campo 'inicio_solicitud' es obligatorio.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Acto Sin Fecha Inicio',
            'descripcion': 'Falta la fecha de apertura',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': None,
            'fin_solicitud': fecha_acto - timedelta(days=5),
            
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('inicio_solicitud', errores, "El error debe estar en 'inicio_solicitud'")
        
        mensaje_esperado = "La fecha de inicio de solicitud es obligatoria."
        
        self.assertIn(mensaje_esperado, str(errores['inicio_solicitud']))
        self.assertEqual(Acto.objects.filter(nombre='Acto Sin Fecha Inicio').count(), 0)



    def test_crear_acto_tradicional_fechas_cirios_faltantes_error(self):
        """
        [Negativo] Intento de crear un Acto TRADICIONAL donde faltan las fechas específicas de cirios.
        
        Input:
            - modalidad = 'TRADICIONAL'.
            - inicio_solicitud_cirios = None (FALTANTE).
            - Las fechas de insignias (generales) sí están presentes.
        Resultado:
            - ValidationError (DRF) indicando que 'inicio_solicitud_cirios' es obligatorio en tradicional.
        """
        fecha_acto = timezone.now() + timedelta(days=40)
        
        data_invalida = {
            'nombre': 'Tradicional Incompleto',
            'descripcion': 'Faltan plazos de cirios',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(days=20),
            'fin_solicitud': fecha_acto - timedelta(days=15),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': fecha_acto - timedelta(days=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail
        self.assertIn('inicio_solicitud_cirios', errores, "El error debe estar en 'inicio_solicitud_cirios'")
        
        mensaje_esperado = "El inicio de cirios es obligatorio en modalidad tradicional."
        
        self.assertIn(mensaje_esperado, str(errores['inicio_solicitud_cirios']))
        self.assertEqual(Acto.objects.filter(nombre='Tradicional Incompleto').count(), 0)



    def test_crear_acto_unificado_con_fechas_cirios_error(self):
        """
        [Negativo] Intento de crear un Acto UNIFICADO enviando fechas de cirios.
        
        Input:
            - modalidad = 'UNIFICADO'.
            - inicio_solicitud_cirios = fecha (INVALIDO para esta modalidad).
        Resultado:
            - ValidationError (DRF) indicando que en unificado no debe haber fechas de cirios.
            - El error debe estar asociado al campo 'modalidad'.
        """
        fecha_acto = timezone.now() + timedelta(days=50)
        
        data_invalida = {
            'nombre': 'Unificado Incoherente',
            'descripcion': 'Intento mezclar modalidades',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': fecha_acto - timedelta(days=20),
            'fin_solicitud': fecha_acto - timedelta(days=10),
            'inicio_solicitud_cirios': fecha_acto - timedelta(days=15),
            'fin_solicitud_cirios': fecha_acto - timedelta(days=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail
        self.assertIn('modalidad', errores, "El error debe estar asociado al campo 'modalidad'")
        
        mensaje_esperado = "En modalidad Unificada no se deben definir fechas de cirios independientes."
        
        self.assertIn(mensaje_esperado, str(errores['modalidad']))
        self.assertEqual(Acto.objects.filter(nombre='Unificado Incoherente').count(), 0)



    def test_crear_acto_incoherencia_fechas_insignias_error(self):
        """
        [Negativo] Intento de crear un Acto donde la fecha de inicio de solicitud 
        es posterior a la fecha de fin (Incoherencia temporal).
        
        Input:
            - inicio_solicitud > fin_solicitud.
        Resultado:
            - ValidationError (DRF) asociado al campo 'fin_solicitud'.
        """
        base_time = timezone.now()
        fecha_acto = base_time + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Acto Fechas Cruzadas',
            'descripcion': 'Error cronológico',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,

            'inicio_solicitud': base_time + timedelta(days=10),
            'fin_solicitud': base_time + timedelta(days=5),

            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('fin_solicitud', errores, "El error debe estar en 'fin_solicitud'")
        
        mensaje_esperado = "La fecha de fin debe ser posterior al inicio."
        
        self.assertIn(mensaje_esperado, str(errores['fin_solicitud']))
        self.assertEqual(Acto.objects.filter(nombre='Acto Fechas Cruzadas').count(), 0)



    def test_crear_acto_incoherencia_fechas_cirios_error(self):
        """
        [Negativo] Intento de crear un Acto TRADICIONAL donde la fecha de inicio de cirios 
        es posterior a la fecha de fin de cirios.
        
        Input:
            - modalidad = 'TRADICIONAL'.
            - inicio_solicitud_cirios > fin_solicitud_cirios.
        Resultado:
            - ValidationError (DRF) asociado al campo 'fin_solicitud_cirios'.
        """
        base_time = timezone.now()
        fecha_acto = base_time + timedelta(days=60)
        
        data_invalida = {
            'nombre': 'Cirios Incoherentes',
            'descripcion': 'Error en fechas de papeletas de sitio generales',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': base_time + timedelta(days=5),
            'fin_solicitud': base_time + timedelta(days=10),
            'inicio_solicitud_cirios': base_time + timedelta(days=20),
            'fin_solicitud_cirios': base_time + timedelta(days=15),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('fin_solicitud_cirios', errores, "El error debe estar en 'fin_solicitud_cirios'")
        
        mensaje_esperado = "La fecha de fin de cirios debe ser posterior al inicio."
        
        self.assertIn(mensaje_esperado, str(errores['fin_solicitud_cirios']))
        self.assertEqual(Acto.objects.filter(nombre='Cirios Incoherentes').count(), 0)



    def test_crear_acto_tradicional_solapamiento_insignias_cirios_error(self):
        """
        [Negativo] Intento de crear un Acto TRADICIONAL donde el plazo de cirios 
        comienza antes de que termine el de insignias (Solapamiento).
        
        Input:
            - modalidad = 'TRADICIONAL'.
            - inicio_solicitud_cirios <= fin_solicitud (insignias).
        Resultado:
            - ValidationError (DRF) asociado a 'inicio_solicitud_cirios'.
        """
        base_time = timezone.now()
        fecha_acto = base_time + timedelta(days=60)
        
        data_invalida = {
            'nombre': 'Solapamiento Tradicional',
            'descripcion': 'Conflicto de fechas entre fases',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': base_time + timedelta(days=10),
            'fin_solicitud': base_time + timedelta(days=20),
            'inicio_solicitud_cirios': base_time + timedelta(days=15),
            'fin_solicitud_cirios': base_time + timedelta(days=25),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('inicio_solicitud_cirios', errores, "El error debe estar en 'inicio_solicitud_cirios'")
        
        mensaje_esperado = "El reparto de cirios debe empezar después de que terminen las insignias."
        
        self.assertIn(mensaje_esperado, str(errores['inicio_solicitud_cirios']))
        self.assertEqual(Acto.objects.filter(nombre='Solapamiento Tradicional').count(), 0)



    def test_crear_acto_fechas_solicitud_posterior_al_acto_error(self):
        """
        [Negativo] Intento de crear un Acto donde una de las fechas de solicitud
        (ej. fin_solicitud) es posterior a la propia fecha de celebración del acto.
        
        Input:
            - fecha_acto = Día X.
            - fin_solicitud = Día X + 1 (Posterior al acto).
        Resultado:
            - ValidationError (DRF) asociado al campo 'fin_solicitud'.
            - Mensaje: "Debe ser anterior a la fecha del acto..."
        """
        base_time = timezone.now()

        fecha_acto = base_time + timedelta(days=10)
        
        data_invalida = {
            'nombre': 'Acto Pasado de Fecha',
            'descripcion': 'Error: solicitud termina después del acto',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': base_time + timedelta(days=1),
            'fin_solicitud': fecha_acto + timedelta(days=1),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('fin_solicitud', errores, "El error debe estar asociado a 'fin_solicitud'")
        
        mensaje_esperado_parte = "Debe ser anterior a la fecha del acto"
        
        self.assertIn(mensaje_esperado_parte, str(errores['fin_solicitud']))
        self.assertEqual(Acto.objects.filter(nombre='Acto Pasado de Fecha').count(), 0)



    def test_crear_acto_exito_admin(self):
        """
        [Positivo] Creación exitosa de un Acto por parte de un Administrador.
        
        Input:
            - usuario.esAdmin = True.
            - nombre único.
            - fechas válidas (lógica temporal correcta).
        Resultado:
            - El servicio no lanza excepciones.
            - El objeto Acto se crea en BBDD.
            - El servicio retorna la instancia creada correctamente poblada.
        """
        fecha_acto = timezone.now() + timedelta(days=60)
        inicio_solicitud = timezone.now() + timedelta(days=10)
        fin_solicitud = timezone.now() + timedelta(days=30)

        data_validada = {
            'nombre': 'Procesión Magna 2025',
            'descripcion': 'Salida extraordinaria por aniversario.',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': inicio_solicitud,
            'fin_solicitud': fin_solicitud,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        acto_creado = crear_acto_service(self.usuario_admin, data_validada)
        self.assertIsNotNone(acto_creado, "El servicio debe retornar el objeto creado.")
        self.assertIsNotNone(acto_creado.id, "El objeto retornado debe tener un ID asignado (persistido).")
        self.assertEqual(acto_creado.nombre, 'Procesión Magna 2025')

        acto_db = Acto.objects.get(id=acto_creado.id)
        self.assertEqual(acto_db.descripcion, 'Salida extraordinaria por aniversario.')
        self.assertEqual(acto_db.fecha, fecha_acto)
        self.assertEqual(acto_db.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertTrue(Acto.objects.filter(nombre='Procesión Magna 2025').exists())



    def test_crear_acto_fallo_seguridad_no_admin(self):
        """
        [Negativo] Fallo de Seguridad: Intento de creación por usuario NO Admin.
        
        Input:
            - usuario.esAdmin = False (usuario_no_admin del setUp).
            - data válida (para asegurar que el fallo es por permisos y no por validación).
        Resultado:
            - PermissionDenied levantado por el servicio.
            - No se crea nada en la BBDD.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_validada = {
            'nombre': 'Intento Hackeo',
            'descripcion': 'Usuario normal intentando crear acto',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': fecha_acto - timedelta(days=10),
            'fin_solicitud': fecha_acto - timedelta(days=5),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(PermissionDenied) as contexto:
            crear_acto_service(self.usuario_no_admin, data_validada)

        mensaje_esperado = "No tienes permisos para crear actos. Se requiere ser Administrador."
        self.assertIn(mensaje_esperado, str(contexto.exception))
        self.assertEqual(Acto.objects.count(), 0, "No se debería haber persistido ningún Acto")



    def test_crear_acto_duplicado_nombre_y_fecha_error(self):
        """
        [Negativo] Intento de crear un Acto con el mismo nombre y fecha (día)
        que uno ya existente.
        
        Input:
            - Ya existe en BBDD: Acto(nombre="Procesión", fecha="Día X 10:00")
            - Se intenta crear: Acto(nombre="Procesión", fecha="Día X 18:00")
        Resultado:
            - ValidationError indicando que "Ya existe el acto...".
            - No se crea el segundo acto.
        """
        fecha_dia = timezone.now() + timedelta(days=90)
        fecha_original = fecha_dia.replace(hour=10, minute=0, second=0)

        Acto.objects.create(
            nombre="Procesión Magna",
            descripcion="Original",
            fecha=fecha_original,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=fecha_original - timedelta(days=20),
            fin_solicitud=fecha_original - timedelta(days=10)
        )

        fecha_intento = fecha_dia.replace(hour=18, minute=0, second=0)

        data_duplicada = {
            'nombre': "Procesión Magna",
            'descripcion': "Intento de duplicado",
            'fecha': fecha_intento,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': fecha_intento - timedelta(days=20),
            'fin_solicitud': fecha_intento - timedelta(days=10),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_duplicada)

        exception = contexto.exception

        mensaje_esperado = "Ya existe el acto 'Procesión Magna' en esa fecha."
        
        if hasattr(exception, 'detail'):
            self.assertIn(mensaje_esperado, str(exception.detail))
        else:
            self.assertIn(mensaje_esperado, str(exception))

        self.assertEqual(Acto.objects.filter(nombre="Procesión Magna").count(), 1)



    def test_crear_acto_rollback_validacion_fallida(self):
        """
        [Negativo] Verificación de Atomicidad/Rollback.
        
        Input:
            - Usuario: Admin (Pasa el check de permisos).
            - Nombre/Fecha: Únicos (Pasa el check de duplicados).
            - Datos: Contienen una incoherencia de fechas que hace fallar a '_validar_fechas_acto'.
        Resultado:
            - Se lanza ValidationError.
            - El decorador @transaction.atomic asegura que no se haga commit.
            - No se crea el registro en BBDD.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Acto Rollback Test',
            'descripcion': 'Probando atomicidad',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': fecha_acto - timedelta(days=5),
            'fin_solicitud': fecha_acto - timedelta(days=10),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError):
            crear_acto_service(self.usuario_admin, data_invalida)

        self.assertEqual(
            Acto.objects.filter(nombre='Acto Rollback Test').count(), 
            0,
            "La transacción debió revertirse o cancelarse; el objeto no debe existir."
        )



    def test_crear_acto_frontera_inicio_igual_fin_error(self):
        """
        [Negativo] Caso Frontera: Inicio de solicitud es EXACTAMENTE igual al Fin.
        
        Input:
            - inicio_solicitud == fin_solicitud.
        Resultado:
            - ValidationError. El código utiliza la condición '>=', por lo que
                la igualdad también se considera inválida (se requiere duración > 0).
        """
        instante_reparto = timezone.now() + timedelta(days=10)
        fecha_acto = timezone.now() + timedelta(days=60)
        
        data_invalida = {
            'nombre': 'Acto Tiempo Nulo',
            'descripcion': 'Intervalo de 0 minutos',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': instante_reparto,
            'fin_solicitud': instante_reparto,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('fin_solicitud', errores, "El error debe estar en 'fin_solicitud'")
        
        mensaje_esperado = "La fecha de fin debe ser posterior al inicio."
        self.assertIn(mensaje_esperado, str(errores['fin_solicitud']))

        self.assertEqual(Acto.objects.filter(nombre='Acto Tiempo Nulo').count(), 0)



    def test_crear_acto_frontera_fin_solicitud_igual_fecha_acto_error(self):
        """
        [Negativo] Caso Frontera: La fecha de fin de solicitud es EXACTAMENTE igual 
        a la fecha de celebración del Acto.
        
        Input:
            - fin_solicitud == fecha_acto.
        Resultado:
            - ValidationError. El sistema exige 'valor < fecha_acto'.
            - Al ser iguales (>=), debe bloquearse.
        """
        momento_acto = timezone.now() + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Acto Frontera Límite',
            'descripcion': 'Prueba de concurrencia de fechas',
            'fecha': momento_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': momento_acto - timedelta(days=1),
            'fin_solicitud': momento_acto,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('fin_solicitud', errores, "El error debe estar en 'fin_solicitud'")

        fecha_formateada = momento_acto.strftime('%d/%m/%Y %H:%M')
        mensaje_esperado = f"Debe ser anterior a la fecha del acto ({fecha_formateada})."
        
        self.assertIn(mensaje_esperado, str(errores['fin_solicitud']))
        self.assertEqual(Acto.objects.filter(nombre='Acto Frontera Límite').count(), 0)



    def test_crear_acto_frontera_fin_insignias_igual_inicio_cirios_error(self):
        """
        [Negativo] Caso Frontera TRADICIONAL: El fin de solicitud de insignias es 
        EXACTAMENTE igual al inicio de solicitud de cirios.
        
        Input:
            - modalidad = 'TRADICIONAL'.
            - fin_solicitud == inicio_solicitud_cirios.
        Resultado:
            - ValidationError. La lógica 'inicio_cirios <= fin_insignias' 
                detecta el solapamiento incluso en la igualdad estricta.
        """
        base_time = timezone.now()
        momento_cambio_fase = base_time + timedelta(days=10)
        fecha_acto = base_time + timedelta(days=60)
        
        data_invalida = {
            'nombre': 'Acto Frontera Fases',
            'descripcion': 'Prueba de continuidad inmediata',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': momento_cambio_fase - timedelta(days=5),
            'fin_solicitud': momento_cambio_fase,
            'inicio_solicitud_cirios': momento_cambio_fase,
            'fin_solicitud_cirios': momento_cambio_fase + timedelta(days=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('inicio_solicitud_cirios', errores, "El error debe estar en 'inicio_solicitud_cirios'")
        
        mensaje_esperado = "El reparto de cirios debe empezar después de que terminen las insignias."
        
        self.assertIn(mensaje_esperado, str(errores['inicio_solicitud_cirios']))
        self.assertEqual(Acto.objects.filter(nombre='Acto Frontera Fases').count(), 0)



    def test_crear_acto_frontera_unicidad_mismo_dia_diferente_hora_error(self):
        """
        [Negativo] Caso Frontera de Unicidad: Mismo nombre, mismo día, diferente hora.
        
        Input:
            - Existe: Acto("Misa", 20/03/2024 10:00).
            - Intento: Acto("Misa", 20/03/2024 20:00).
        Código: 
            - filter(nombre=..., fecha__date=fecha.date()).
        Resultado:
            - ValidationError. El sistema considera que 'ya existe' porque coincide el día.
        """
        dia_conflicto = timezone.now() + timedelta(days=20)
        fecha_manana = dia_conflicto.replace(hour=10, minute=0, second=0)
        
        Acto.objects.create(
            nombre="Misa de Hermandad",
            descripcion="Misa matutina",
            fecha=fecha_manana,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=fecha_manana - timedelta(days=5),
            fin_solicitud=fecha_manana - timedelta(days=1)
        )

        fecha_tarde = dia_conflicto.replace(hour=20, minute=0, second=0)

        data_duplicada = {
            'nombre': "Misa de Hermandad",
            'descripcion': "Misa vespertina (Intento)",
            'fecha': fecha_tarde,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': fecha_tarde - timedelta(days=5),
            'fin_solicitud': fecha_tarde - timedelta(days=1),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_duplicada)

        exception = contexto.exception

        mensaje_esperado = "Ya existe el acto 'Misa de Hermandad' en esa fecha."

        if hasattr(exception, 'detail'):
            self.assertIn(mensaje_esperado, str(exception.detail))
        else:
            self.assertIn(mensaje_esperado, str(exception))

        self.assertEqual(Acto.objects.filter(nombre="Misa de Hermandad").count(), 1)

        acto_existente = Acto.objects.get(nombre="Misa de Hermandad")
        self.assertEqual(acto_existente.fecha, fecha_manana)



    def test_crear_acto_modalidad_string_vacio_error(self):
        """
        [Negativo] Caso de Valor Crítico: Modalidad enviada como string vacío ("").
        
        Input:
            - tipo_acto.requiere_papeleta = True.
            - modalidad = "" (String vacío).
        Código:
            - if not modalidad: (Python evalúa "" como False).
        Resultado:
            - ValidationError indicando que la modalidad es obligatoria.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Acto Modalidad Vacía',
            'descripcion': 'Test de valor Falsey',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': "", 
            'inicio_solicitud': fecha_acto - timedelta(days=10),
            'fin_solicitud': fecha_acto - timedelta(days=5),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail
        self.assertIn('modalidad', errores, "El error debe estar en 'modalidad'")
        
        mensaje_esperado = "La modalidad es obligatoria para actos con papeleta."
        
        self.assertIn(mensaje_esperado, str(errores['modalidad']))
        self.assertEqual(Acto.objects.filter(nombre='Acto Modalidad Vacía').count(), 0)



    def test_crear_acto_tradicional_ambas_fechas_cirios_faltantes_error(self):
        """
        [Negativo] Intento de crear un Acto TRADICIONAL donde faltan AMBAS fechas de cirios.
        
        Input:
            - modalidad = 'TRADICIONAL'.
            - inicio_solicitud_cirios = None.
            - fin_solicitud_cirios = None.
        Resultado:
            - ValidationError (DRF) que contiene DOS errores simultáneos:
                1. Clave 'inicio_solicitud_cirios'.
                2. Clave 'fin_solicitud_cirios'.
        """
        fecha_acto = timezone.now() + timedelta(days=40)
        
        data_invalida = {
            'nombre': 'Tradicional Sin Fechas Cirios',
            'descripcion': 'Faltan inicio y fin de la fase 2',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(days=20),
            'fin_solicitud': fecha_acto - timedelta(days=15),
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('inicio_solicitud_cirios', errores, "Debe reportar error en inicio")
        self.assertIn(
            "El inicio de cirios es obligatorio en modalidad tradicional.", 
            str(errores['inicio_solicitud_cirios'])
        )

        self.assertIn('fin_solicitud_cirios', errores, "Debe reportar error en fin")
        self.assertIn(
            "El fin de cirios es obligatorio en modalidad tradicional.", 
            str(errores['fin_solicitud_cirios'])
        )

        self.assertEqual(Acto.objects.filter(nombre='Tradicional Sin Fechas Cirios').count(), 0)



    def test_crear_acto_datos_basicos_obligatorios_faltantes_error(self):
        """
        [Negativo] Intento de crear un Acto con papeleta donde faltan TODOS 
        los datos obligatorios de configuración (Modalidad y Fechas Generales).
        
        Input:
            - requiere_papeleta = True.
            - modalidad = None.
            - inicio_solicitud = None.
            - fin_solicitud = None.
        Resultado:
            - ValidationError (DRF) conteniendo 3 errores simultáneos:
                'modalidad', 'inicio_solicitud' y 'fin_solicitud'.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Acto Sin Configuración',
            'descripcion': 'Faltan los pilares básicos',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': None,
            'inicio_solicitud': None,
            'fin_solicitud': None,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('modalidad', errores, "Debe faltar la modalidad")
        self.assertIn(
            "La modalidad es obligatoria para actos con papeleta.", 
            str(errores['modalidad'])
        )

        self.assertIn('inicio_solicitud', errores, "Debe faltar el inicio")
        self.assertIn(
            "La fecha de inicio de solicitud es obligatoria.", 
            str(errores['inicio_solicitud'])
        )

        self.assertIn('fin_solicitud', errores, "Debe faltar el fin")
        self.assertIn(
            "La fecha de fin de solicitud es obligatoria.", 
            str(errores['fin_solicitud'])
        )

        self.assertEqual(Acto.objects.filter(nombre='Acto Sin Configuración').count(), 0)



    def test_crear_acto_fin_solicitud_faltante_error(self):
        """
        [Negativo] Intento de crear un Acto con papeleta donde falta SOLO 
        la fecha de fin de solicitud.
        
        Input:
            - requiere_papeleta = True.
            - modalidad = 'UNIFICADO' (Correcto).
            - inicio_solicitud = Fecha válida (Correcto).
            - fin_solicitud = None (FALTANTE).
        Resultado:
            - ValidationError (DRF) asociado exclusivamente al campo 'fin_solicitud'.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_invalida = {
            'nombre': 'Acto Sin Fecha Fin',
            'descripcion': 'Falta el cierre de plazo',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            'inicio_solicitud': fecha_acto - timedelta(days=10),
            'fin_solicitud': None,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('fin_solicitud', errores, "El error debe estar en 'fin_solicitud'")
        
        mensaje_esperado = "La fecha de fin de solicitud es obligatoria."
        self.assertIn(mensaje_esperado, str(errores['fin_solicitud']))

        self.assertNotIn('inicio_solicitud', errores)
        self.assertNotIn('modalidad', errores)

        self.assertEqual(Acto.objects.filter(nombre='Acto Sin Fecha Fin').count(), 0)



    def test_crear_acto_tradicional_fin_cirios_faltante_error(self):
        """
        [Negativo] Intento de crear un Acto TRADICIONAL donde falta SOLO 
        la fecha de fin de solicitud de cirios.
        
        Input:
            - modalidad = 'TRADICIONAL'.
            - inicio_solicitud_cirios = Fecha válida (Correcto).
            - fin_solicitud_cirios = None (FALTANTE).
        Resultado:
            - ValidationError (DRF) asociado exclusivamente al campo 'fin_solicitud_cirios'.
        """
        fecha_acto = timezone.now() + timedelta(days=40)
        
        data_invalida = {
            'nombre': 'Tradicional Sin Fin Cirios',
            'descripcion': 'Falta el cierre de la fase 2',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(days=20),
            'fin_solicitud': fecha_acto - timedelta(days=15),
            'inicio_solicitud_cirios': fecha_acto - timedelta(days=10),
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        exception = contexto.exception

        self.assertTrue(hasattr(exception, 'detail'), "La excepción debe tener el atributo '.detail'")
        
        errores = exception.detail

        self.assertIn('fin_solicitud_cirios', errores, "El error debe estar en 'fin_solicitud_cirios'")
        
        mensaje_esperado = "El fin de cirios es obligatorio en modalidad tradicional."
        self.assertIn(mensaje_esperado, str(errores['fin_solicitud_cirios']))

        self.assertNotIn('inicio_solicitud_cirios', errores)
        self.assertEqual(Acto.objects.filter(nombre='Tradicional Sin Fin Cirios').count(), 0)