from unittest import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import PermissionDenied

from api.servicios.papeleta_sitio.papeleta_sitio_service import get_historial_papeletas_hermano_service



class TestObtenerHistorialPapeletasHermanoService(TestCase):

    def setUp(self):
        self.mock_usuario = MagicMock()
        self.mock_usuario.is_authenticated = True



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_el_queryset_correctamente(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve el queryset correctamente

        Given: Un usuario debidamente autenticado en la llamada.
        When: Se solicita el histórico de papeletas del hermano.
        Then: Se debe devolver el queryset resultante tras aplicar filter, select_related y order_by.
        """
        mock_queryset_esperado = MagicMock()

        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value = mock_queryset_esperado

        resultado = get_historial_papeletas_hermano_service(self.mock_usuario)

        self.assertEqual(resultado, mock_queryset_esperado)

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            hermano=self.mock_usuario
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.assert_called_once_with(
            'acto', 'puesto', 'puesto__tipo_puesto', 'tramo'
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value.order_by.assert_called_once_with(
            '-anio', '-acto__fecha'
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_se_filtra_por_usuario_correctamente(self, mock_papeleta_sitio_model):
        """
        Test: Se filtra por el usuario correctamente

        Given: Un usuario autenticado solicitando su información.
        When: Se ejecuta el servicio de historial.
        Then: El método filter debe ser llamado utilizando el objeto usuario recibido por parámetro.
        """
        get_historial_papeletas_hermano_service(self.mock_usuario)
        
        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(hermano=self.mock_usuario)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_se_usan_correctamente_los_select_related(self, mock_papeleta_sitio_model):
        """
        Test: Se usan correctamente los select_related

        Given: Una solicitud de historial que requiere optimización de base de datos.
        When: Se construye el queryset.
        Then: Se debe invocar select_related con los campos 'acto', 'puesto', 'puesto__tipo_puesto' y 'tramo'.
        """
        mock_filter = mock_papeleta_sitio_model.objects.filter.return_value
        
        get_historial_papeletas_hermano_service(self.mock_usuario)
        
        mock_filter.select_related.assert_called_once_with(
            'acto', 'puesto', 'puesto__tipo_puesto', 'tramo'
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_ordenacion_correcta(self, mock_papeleta_sitio_model):
        """
        Test: Ordenación correcta (-anio, -acto__fecha)

        Given: Un usuario consultando sus papeletas históricas.
        When: Se genera el queryset final.
        Then: El método order_by debe recibir los argumentos '-anio' y '-acto__fecha' para garantizar el orden cronológico inverso.
        """
        mock_select = mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value
        
        get_historial_papeletas_hermano_service(self.mock_usuario)
        
        mock_select.order_by.assert_called_once_with('-anio', '-acto__fecha')



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_se_encadena_correctamente_el_queryset(self, mock_papeleta_sitio_model):
        """
        Test: Se encadena correctamente el queryset

        Given: La definición de la lógica del servicio de historial.
        When: Se ejecuta el código del servicio.
        Then: Cada método del ORM debe devolver un mock que permita la llamada al siguiente método de la cadena.
        """
        mock_filter = MagicMock()
        mock_select = MagicMock()
        mock_order = MagicMock()

        mock_papeleta_sitio_model.objects.filter.return_value = mock_filter
        mock_filter.select_related.return_value = mock_select
        mock_select.order_by.return_value = mock_order

        resultado = get_historial_papeletas_hermano_service(self.mock_usuario)

        self.assertEqual(resultado, mock_order)
        mock_filter.select_related.assert_called_once()
        mock_select.order_by.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_exactamente_el_resultado_de_order_by(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve exactamente el resultado de order_by

        Given: El último eslabón de la cadena del queryset.
        When: El servicio finaliza su ejecución.
        Then: El objeto retornado debe ser idéntico al valor devuelto por el método .order_by().
        """
        queryset_final_mock = MagicMock()
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value = queryset_final_mock

        resultado = get_historial_papeletas_hermano_service(self.mock_usuario)

        self.assertIs(resultado, queryset_final_mock)



    def test_usuario_es_none(self):
        """
        Test: Usuario es None

        Given: Un valor None en lugar de un objeto usuario.
        When: Se intenta recuperar el historial de papeletas.
        Then: El servicio debe lanzar una excepción PermissionDenied de DRF.
        """
        with self.assertRaises(PermissionDenied) as context:
            get_historial_papeletas_hermano_service(None)
        
        self.assertIn("Usuario no identificado", str(context.exception))



    def test_usuario_no_autenticado(self):
        """
        Test: Usuario no autenticado (is_authenticated=False)

        Given: Un objeto usuario con is_authenticated en False.
        When: Se solicita el historial del hermano.
        Then: Se debe denegar el acceso lanzando PermissionDenied.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = False

        with self.assertRaises(PermissionDenied) as context:
            get_historial_papeletas_hermano_service(mock_usuario)
            
        self.assertIn("Usuario no identificado", str(context.exception))



    def test_usuario_sin_atributo_is_authenticated(self):
        """
        Test: Usuario sin atributo is_authenticated

        Given: Un objeto que no posee el atributo is_authenticated.
        When: El servicio intenta validar la identidad.
        Then: Python debe lanzar un AttributeError al intentar acceder a la propiedad inexistente.
        """
        mock_usuario = MagicMock()
        del mock_usuario.is_authenticated

        with self.assertRaises(AttributeError):
            get_historial_papeletas_hermano_service(mock_usuario)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_filter(self, mock_papeleta_sitio_model):
        """
        Test: Error en filter()

        Given: Un fallo crítico en la base de datos al iniciar el filtrado.
        When: Se ejecuta la consulta del historial.
        Then: La excepción lanzada por filter() debe propagarse íntegramente.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_papeleta_sitio_model.objects.filter.side_effect = Exception("Fallo en base de datos")

        with self.assertRaises(Exception) as context:
            get_historial_papeletas_hermano_service(mock_usuario)
            
        self.assertEqual(str(context.exception), "Fallo en base de datos")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_select_related(self, mock_papeleta_sitio_model):
        """
        Test: Error en select_related()

        Given: Un error al intentar realizar los joins de la consulta (select_related).
        When: Se construye el queryset.
        Then: Se debe capturar la excepción lanzada por el método select_related.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.side_effect = Exception("Error en select_related")

        with self.assertRaises(Exception) as context:
            get_historial_papeletas_hermano_service(mock_usuario)
            
        self.assertEqual(str(context.exception), "Error en select_related")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_order_by(self, mock_papeleta_sitio_model):
        """
        Test: Error en order_by()

        Given: Una excepción ocurrida durante la definición del orden del historial.
        When: Se finaliza la construcción del queryset.
        Then: El servicio debe fallar permitiendo que la excepción de order_by sea visible.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_select = mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value
        mock_select.order_by.side_effect = Exception("Error en order_by")

        with self.assertRaises(Exception) as context:
            get_historial_papeletas_hermano_service(mock_usuario)
            
        self.assertEqual(str(context.exception), "Error en order_by")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_cadena_queryset_rota(self, mock_papeleta_sitio_model):
        """
        Test: Cadena de queryset rota (algún método devuelve None)

        Given: Un fallo en la cadena donde .filter() devuelve None inesperadamente.
        When: El servicio intenta encadenar el siguiente método (.select_related()).
        Then: Se debe producir un AttributeError, ya que no se pueden ejecutar métodos del ORM sobre None.
        """
        mock_papeleta_sitio_model.objects.filter.return_value = None

        with self.assertRaises(AttributeError):
            get_historial_papeletas_hermano_service(self.mock_usuario)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_usuario_valido_pero_sin_resultados(self, mock_papeleta_sitio_model):
        """
        Test: Usuario válido pero sin resultados (queryset vacío)

        Given: Un usuario sin registros de papeletas en el sistema.
        When: Se solicita el historial completo.
        Then: El servicio debe devolver un queryset vacío (un iterable sin elementos) pero no None ni lanzar excepción.
        """
        mock_queryset_vacio = MagicMock()
        mock_queryset_vacio.__iter__.return_value = iter([])
        mock_queryset_vacio.__len__.return_value = 0

        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value = mock_queryset_vacio

        resultado = get_historial_papeletas_hermano_service(self.mock_usuario)

        self.assertEqual(len(list(resultado)), 0)
        self.assertIs(resultado, mock_queryset_vacio)