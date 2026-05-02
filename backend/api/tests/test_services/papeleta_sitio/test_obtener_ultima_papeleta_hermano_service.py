from unittest import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import PermissionDenied

from api.servicios.papeleta_sitio.papeleta_sitio_service import get_ultima_papeleta_hermano_service


class TestObtenerUltimaPapeletaHermanoService(TestCase):

    def setUp(self):
        self.mock_usuario = MagicMock()
        self.mock_usuario.is_authenticated = True



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_ultima_papeleta(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve la última papeleta

        Given: Un usuario debidamente autenticado en la llamada.
        When: Se procesa la solicitud de obtener la última papeleta exitosamente.
        Then: Se debe devolver el objeto de la papeleta tras realizar la consulta encadenada a base de datos.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True

        mock_papeleta_esperada = MagicMock()
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value \
            .first.return_value = mock_papeleta_esperada

        resultado = get_ultima_papeleta_hermano_service(mock_usuario)

        self.assertEqual(resultado, mock_papeleta_esperada)

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            hermano=mock_usuario
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.assert_called_once_with(
            'acto', 'puesto', 'puesto__tipo_puesto', 'tramo'
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value.order_by.assert_called_once_with(
            '-anio', '-acto__fecha'
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value.order_by.return_value.first.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_none_si_no_hay_papeletas(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve None si no hay papeletas

        Given: Un usuario sin historial de papeletas en la base de datos.
        When: Se consulta la última papeleta del hermano.
        Then: El método .first() debe retornar None y el servicio debe devolver None.
        """
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value \
            .first.return_value = None

        resultado = get_ultima_papeleta_hermano_service(self.mock_usuario)

        self.assertIsNone(resultado)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_se_filtra_por_usuario_correctamente(self, mock_papeleta_sitio_model):
        """
        Test: Se filtra por el usuario correctamente

        Given: Un usuario específico realizando la consulta.
        When: Se ejecuta el servicio.
        Then: Se debe llamar al método filter del ORM usando el objeto usuario proporcionado.
        """
        mock_qs = mock_papeleta_sitio_model.objects.filter.return_value
        mock_qs.select_related.return_value.order_by.return_value.first.return_value = MagicMock()

        get_ultima_papeleta_hermano_service(self.mock_usuario)

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(hermano=self.mock_usuario)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_se_usan_correctamente_los_select_related(self, mock_papeleta_sitio_model):
        """
        Test: Se usan correctamente los select_related

        Given: Una solicitud de optimización de consulta (select_related).
        When: El servicio recupera la papeleta.
        Then: Se deben incluir las relaciones 'acto', 'puesto', 'puesto__tipo_puesto' y 'tramo' para evitar N+1.
        """
        mock_filter = mock_papeleta_sitio_model.objects.filter.return_value
        mock_select = mock_filter.select_related

        get_ultima_papeleta_hermano_service(self.mock_usuario)

        mock_select.assert_called_once_with(
            'acto', 'puesto', 'puesto__tipo_puesto', 'tramo'
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_ordenacion_correcta(self, mock_papeleta_sitio_model):
        """
        Test: Ordenación correcta (-anio, -acto__fecha)

        Given: Una consulta a la base de datos de papeletas.
        When: Se procesa la solicitud para obtener la más reciente.
        Then: Se debe invocar el método order_by con los campos '-anio' y '-acto__fecha' para asegurar la prioridad temporal.
        """
        mock_select = mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value
        mock_order = mock_select.order_by
        
        get_ultima_papeleta_hermano_service(self.mock_usuario)

        mock_order.assert_called_once_with('-anio', '-acto__fecha')



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_se_ejecuta_first_una_unica_vez(self, mock_papeleta_sitio_model):
        """
        Test: Se ejecuta .first() una única vez

        Given: Un queryset configurado con filtros y ordenación.
        When: Se solicita el resultado final del servicio.
        Then: Se debe invocar el método .first() exactamente una vez para recuperar el registro individual.
        """
        mock_first = (mock_papeleta_sitio_model.objects.filter.return_value
                    .select_related.return_value
                    .order_by.return_value
                    .first)

        get_ultima_papeleta_hermano_service(self.mock_usuario)

        self.assertEqual(mock_first.call_count, 1)



    def test_usuario_es_none(self):
        """
        Test: Usuario es None

        Given: Un valor None en lugar de un objeto usuario.
        When: Se intenta recuperar la última papeleta.
        Then: El servicio debe lanzar una excepción PermissionDenied por falta de identificación.
        """
        with self.assertRaises(PermissionDenied) as context:
            get_ultima_papeleta_hermano_service(None)
        
        self.assertEqual(str(context.exception), "Usuario no identificado")



    def test_usuario_no_autenticado(self):
        """
        Test: Usuario no autenticado (is_authenticated=False)

        Given: Un objeto usuario con el atributo is_authenticated establecido en False.
        When: Se procesa la solicitud del servicio.
        Then: Se debe denegar el acceso lanzando PermissionDenied.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = False

        with self.assertRaises(PermissionDenied) as context:
            get_ultima_papeleta_hermano_service(mock_usuario)
            
        self.assertEqual(str(context.exception), "Usuario no identificado")



    def test_usuario_sin_atributo_is_authenticated(self):
        """
        Test: Usuario sin atributo is_authenticated

        Given: Un objeto que no tiene definida la autenticación (evalúa a False).
        When: Se valida la identidad del usuario en el servicio.
        Then: El servicio debe tratarlo como no identificado y lanzar PermissionDenied.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = False 

        with self.assertRaises(PermissionDenied) as context:
            get_ultima_papeleta_hermano_service(mock_usuario)
            
        self.assertIn("Usuario no identificado", str(context.exception))



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_filter(self, mock_papeleta_sitio_model):
        """
        Test: Error en filter()

        Given: Un problema inesperado en la base de datos durante la ejecución del filtro.
        When: Se invoca al método filter() del ORM.
        Then: La excepción lanzada por la base de datos debe propagarse correctamente hacia arriba.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True

        mock_papeleta_sitio_model.objects.filter.side_effect = Exception("Error de conexión a BD")

        with self.assertRaises(Exception) as context:
            get_ultima_papeleta_hermano_service(mock_usuario)
            
        self.assertEqual(str(context.exception), "Error de conexión a BD")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_select_related(self, mock_papeleta_sitio_model):
        """
        Test: Error en select_related()

        Given: Un fallo en la carga de relaciones relacionadas (select_related).
        When: Se intenta procesar la consulta.
        Then: La excepción lanzada por el ORM debe propagarse hacia el llamador.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.side_effect = Exception("Error en select_related")

        with self.assertRaises(Exception) as context:
            get_ultima_papeleta_hermano_service(self.mock_usuario)
        
        self.assertEqual(str(context.exception), "Error en select_related")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_order_by(self, mock_papeleta_sitio_model):
        """
        Test: Error en order_by()

        Given: Un error en los criterios de ordenación de la consulta.
        When: Se ejecuta la lógica del servicio.
        Then: El servicio debe fallar permitiendo que la excepción del ORM suba en la pila de ejecución.
        """
        mock_qs = mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value
        mock_qs.order_by.side_effect = Exception("Error en order_by")

        with self.assertRaises(Exception) as context:
            get_ultima_papeleta_hermano_service(self.mock_usuario)
        
        self.assertEqual(str(context.exception), "Error en order_by")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_first(self, mock_papeleta_sitio_model):
        """
        Test: Error en first()

        Given: Una base de datos que falla al intentar recuperar el primer registro del conjunto.
        When: Se finaliza la ejecución de la consulta.
        Then: Se debe capturar la excepción específica lanzada por el método first.
        """
        mock_qs = (mock_papeleta_sitio_model.objects.filter.return_value
                .select_related.return_value
                .order_by.return_value)
        mock_qs.first.side_effect = Exception("Error en first")

        with self.assertRaises(Exception) as context:
            get_ultima_papeleta_hermano_service(self.mock_usuario)
        
        self.assertEqual(str(context.exception), "Error en first")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_cadena_queryset_rota(self, mock_papeleta_sitio_model):
        """
        Test: Cadena de queryset rota (algún método devuelve None)

        Given: Una respuesta inesperada (None) en mitad de la cadena del ORM.
        When: Se intenta acceder al siguiente método de la cadena (.select_related()).
        Then: El servicio debe lanzar un AttributeError al intentar ejecutar un método sobre un objeto None.
        """
        mock_papeleta_sitio_model.objects.filter.return_value = None

        with self.assertRaises(AttributeError):
            get_ultima_papeleta_hermano_service(self.mock_usuario)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_usuario_valido_pero_sin_resultados(self, mock_papeleta_sitio_model):
        """
        Test: Usuario válido pero sin resultados

        Given: Un usuario que existe y está autenticado pero no tiene papeletas registradas.
        When: Se ejecuta la consulta completa en la base de datos.
        Then: El método .first() devuelve None y el servicio retorna None sin lanzar excepciones.
        """
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value \
            .first.return_value = None

        resultado = get_ultima_papeleta_hermano_service(self.mock_usuario)

        self.assertIsNone(resultado)