import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta

from rest_framework.exceptions import PermissionDenied, ValidationError

from api.servicios.puesto.puesto_service import create_puesto_service


class TestPuestoService(unittest.TestCase):

    def setUp(self):
        self.usuario_admin = MagicMock()
        self.usuario_admin.esAdmin = True



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_crea_puesto_correctamente(self, mock_timezone, mock_puesto):
        """
        Test: Crea puesto correctamente (caso válido)
        
        Given: Un usuario administrador, datos validados de un puesto para un acto futuro que requiere papeleta, y garantizando que el puesto no existe previamente.
        When: Se llama al servicio de creación de puesto.
        Then: Se verifica que se comprueba la inexistencia del puesto, se llama a Puesto.objects.create con los datos exactos y se retorna la instancia creada.
        """
        usuario = MagicMock()
        usuario.esAdmin = True

        fecha_hoy = date(2026, 5, 5)
        mock_now = MagicMock()
        mock_now.date.return_value = fecha_hoy
        mock_timezone.now.return_value = mock_now

        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = fecha_hoy + timedelta(days=5)

        data_validada = {
            'acto': acto,
            'nombre': 'Diputado de Cruz',
            'descripcion': 'Descripción del puesto'
        }

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_puesto.objects.filter.return_value = mock_queryset

        mock_instancia_puesto = MagicMock()
        mock_puesto.objects.create.return_value = mock_instancia_puesto

        resultado = create_puesto_service(usuario, data_validada)

        mock_puesto.objects.filter.assert_called_once_with(acto=acto, nombre='Diputado de Cruz')
        mock_queryset.exists.assert_called_once()

        mock_puesto.objects.create.assert_called_once_with(**data_validada)

        self.assertEqual(resultado, mock_instancia_puesto)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_devuelve_el_puesto_creado(self, mock_timezone, mock_puesto):
        """
        Test: Devuelve el puesto creado
        
        Given: Un flujo de creación de puesto válido.
        When: Se completa la ejecución de create_puesto_service.
        Then: El servicio debe retornar exactamente el objeto que fue devuelto por el método Puesto.objects.create.
        """
        usuario = MagicMock(esAdmin=True)

        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = hoy + timedelta(days=1)
        
        data = {'acto': acto, 'nombre': 'Puesto Test'}

        puesto_mock = MagicMock(spec=['id', 'nombre'])
        mock_puesto.objects.filter.return_value.exists.return_value = False
        mock_puesto.objects.create.return_value = puesto_mock

        resultado = create_puesto_service(usuario, data)

        self.assertEqual(resultado, puesto_mock)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_usa_correctamente_create_con_data_validada(self, mock_timezone, mock_puesto):
        """
        Test: Usa correctamente create(**data_validada)
        
        Given: Un diccionario de datos validados.
        When: Se procede a la persistencia en base de datos.
        Then: Se verifica que se utiliza el operador de desempaquetado (**) para pasar todos los argumentos al método create de Django.
        """
        usuario = MagicMock(esAdmin=True)
        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = hoy + timedelta(days=1)
        
        data_validada = {
            'acto': acto,
            'nombre': 'Fiscal',
            'seccion': 'Cristo',
            'prioridad': 1
        }
        mock_puesto.objects.filter.return_value.exists.return_value = False

        create_puesto_service(usuario, data_validada)

        mock_puesto.objects.create.assert_called_once_with(**data_validada)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_convierte_correctamente_inicio_solicitud_con_date(self, mock_timezone, mock_puesto):
        """
        Test: Convierte correctamente inicio_solicitud con .date()
        
        Given: Un objeto acto cuyo inicio_solicitud es un datetime (con hora).
        When: Se evalúa si el periodo de solicitud ha comenzado.
        Then: El servicio debe llamar al método .date() del campo para realizar una comparación de fechas pura contra timezone.now().date().
        """
        usuario = MagicMock(esAdmin=True)

        fecha_actual_dt = datetime(2026, 5, 5, 10, 0, 0)
        mock_timezone.now.return_value = fecha_actual_dt

        inicio_solicitud_dt = MagicMock(spec=datetime)
        inicio_solicitud_dt.date.return_value = date(2026, 5, 6)
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = inicio_solicitud_dt
        
        data = {'acto': acto, 'nombre': 'Test Date'}
        mock_puesto.objects.filter.return_value.exists.return_value = False

        create_puesto_service(usuario, data)

        inicio_solicitud_dt.date.assert_called_once()



    def test_usuario_no_admin_lanza_permisos_denegados(self):
        """
        Test: Usuario no admin
        
        Given: Un usuario que no tiene el atributo esAdmin o es False.
        When: Se intenta crear un puesto.
        Then: Se lanza una excepción PermissionDenied con el mensaje "No tienes permisos para crear puestos."
        """
        usuario = MagicMock(esAdmin=False)
        data = {}

        with self.assertRaises(PermissionDenied) as context:
            create_puesto_service(usuario, data)
        self.assertEqual(str(context.exception), "No tienes permisos para crear puestos.")



    def test_acto_no_requiere_papeleta_lanza_error(self):
        """
        Test: Acto no requiere papeleta
        
        Given: Un usuario administrador y un acto cuyo tipo no requiere papeleta.
        When: Se intenta crear el puesto.
        Then: Se lanza una ValidationError indicando que el tipo de acto no admite puestos.
        """
        usuario = MagicMock(esAdmin=True)
        acto = MagicMock()
        acto.nombre = "Misa de Hermandad"
        acto.tipo_acto.requiere_papeleta = False
        acto.tipo_acto.get_tipo_display.return_value = "Culto"
        
        data = {'acto': acto, 'nombre': 'Acólito'}

        with self.assertRaises(ValidationError) as context:
            create_puesto_service(usuario, data)
        self.assertIn("no admite puestos", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_pasada_lanza_error(self, mock_timezone):
        """
        Test: Fecha inicio ya pasada
        
        Given: Un acto cuyo periodo de solicitud comenzó en el pasado.
        When: Se intenta crear un nuevo puesto para dicho acto.
        Then: Se lanza una ValidationError indicando que no se pueden crear puestos si el periodo ya comenzó.
        """
        usuario = MagicMock(esAdmin=True)
        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = hoy - timedelta(days=10) # Hace 10 días
        
        data = {'acto': acto, 'nombre': 'Puesto Tarde'}

        with self.assertRaises(ValidationError) as context:
            create_puesto_service(usuario, data)
        self.assertIn("el pasado, o no tienen fecha definida", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_es_hoy_lanza_error(self, mock_timezone):
        """
        Test: Fecha inicio es hoy
        
        Given: Un acto donde el periodo de solicitud comienza el mismo día actual.
        When: Se intenta añadir un puesto.
        Then: Se lanza una ValidationError ya que los puestos deben definirse antes de que comience el periodo.
        """
        usuario = MagicMock(esAdmin=True)
        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = hoy # Hoy mismo
        
        data = {'acto': acto, 'nombre': 'Puesto Hoy'}

        with self.assertRaises(ValidationError) as context:
            create_puesto_service(usuario, data)
        self.assertIn("periodo de solicitud ya ha comenzado", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_solicitud_es_none(self, mock_timezone):
        """
        Test: Fecha inicio es None
        
        Given: Un acto que requiere papeleta pero cuyo campo 'inicio_solicitud' es None.
        When: Se intenta crear un puesto para dicho acto.
        Then: Se lanza una ValidationError indicando que no se pueden crear puestos para actos sin fecha definida.
        """
        mock_timezone.now.return_value.date.return_value = date(2026, 5, 5)
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = None
        
        data = {'acto': acto, 'nombre': 'Diputado'}

        with self.assertRaises(ValidationError) as context:
            create_puesto_service(self.usuario_admin, data)
        
        self.assertIn("no tienen fecha definida", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_ya_existe_puesto_con_mismo_nombre_en_acto(self, mock_timezone, mock_puesto):
        """
        Test: Ya existe puesto con mismo nombre en el acto
        
        Given: Un acto válido y futuro, pero un nombre de puesto que ya ha sido registrado previamente para ese mismo acto.
        When: El servicio verifica la existencia antes de crear.
        Then: Se lanza una ValidationError informando de la duplicidad en el campo 'nombre'.
        """
        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True
        acto.inicio_solicitud = date(2026, 5, 20)
        
        nombre_duplicado = "Fiscal de Paso"
        data = {'acto': acto, 'nombre': nombre_duplicado}

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_puesto.objects.filter.return_value = mock_queryset

        with self.assertRaises(ValidationError) as context:
            create_puesto_service(self.usuario_admin, data)

        self.assertIn(f"Ya existe un puesto con el nombre '{nombre_duplicado}'", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_inicio_solicitud_ya_es_date_sin_metodo_date(self, mock_timezone, mock_puesto):
        """
        Test: inicio_solicitud sin método .date() (ya es date)
        
        Given: Un acto cuyo campo 'inicio_solicitud' ya es un objeto de tipo date (no datetime).
        When: El servicio verifica la fecha de inicio.
        Then: El código debe usar el objeto directamente sin intentar llamar a .date(), permitiendo que la validación de fecha futura funcione correctamente.
        """
        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy

        fecha_futura = hoy + timedelta(days=1)
        
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = True

        del acto.inicio_solicitud.date 
        acto.inicio_solicitud = fecha_futura
        
        data = {'acto': acto, 'nombre': 'Puesto Date Puro'}
        mock_puesto.objects.filter.return_value.exists.return_value = False

        create_puesto_service(self.usuario_admin, data)

        mock_puesto.objects.create.assert_called_once()



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_no_se_llama_a_create_si_hay_error_previo(self, mock_timezone, mock_puesto):
        """
        Test: Verificar que no se llama a create si hay error previo
        
        Given: Un acto con una configuración inválida (ej. no requiere papeleta).
        When: Se intenta ejecutar el servicio.
        Then: Se debe lanzar la ValidationError y se verifica que el método Puesto.objects.create nunca llega a ejecutarse.
        """
        acto = MagicMock()
        acto.tipo_acto.requiere_papeleta = False
        
        data = {'acto': acto, 'nombre': 'Puesto Fantasma'}

        with self.assertRaises(ValidationError):
            create_puesto_service(self.usuario_admin, data)

        mock_puesto.objects.create.assert_not_called()