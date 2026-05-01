from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.servicios.hermano.hermano_service import get_estadisticas_hermanos_service

class TestEstadisticasHermanosService(TestCase):

    @patch('api.servicios.hermano.hermano_service.timezone')
    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_calculo_correcto(self, mock_user, mock_timezone):
        """
        Test: Cálculo correcto de estadísticas con datos válidos
        
        Given: Un año actual y simulaciones de conteos para altas, bajas e ingresos.
        When: Se llama al servicio de estadísticas de hermanos.
        Then: Retorna un diccionario con las claves correctas y los valores que coinciden con los conteos.
        """
        mock_now = MagicMock()
        mock_now.year = 2026
        mock_timezone.now.return_value = mock_now

        mock_user.EstadoHermano.ALTA = 'ALTA'
        mock_user.EstadoHermano.BAJA = 'BAJA'

        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset

        mock_queryset.count.side_effect = [150, 20, 15]

        resultado = get_estadisticas_hermanos_service()

        self.assertEqual(resultado, {
            'total_alta': 150,
            'total_baja': 20,
            'ingresos_anio_actual': 15
        })

        self.assertEqual(mock_user.objects.filter.call_count, 3)
        mock_timezone.now.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.timezone')
    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_conteos_cero(self, mock_user, mock_timezone):
        """
        Test: Conteos en cero
        
        Given: Una base de datos vacía donde todas las consultas retornan cero.
        When: Se ejecuta el cálculo de estadísticas.
        Then: Retorna los valores en 0 correctamente.
        """
        mock_now = MagicMock()
        mock_now.year = 2026
        mock_timezone.now.return_value = mock_now

        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset

        mock_queryset.count.return_value = 0

        resultado = get_estadisticas_hermanos_service()

        self.assertEqual(resultado, {
            'total_alta': 0,
            'total_baja': 0,
            'ingresos_anio_actual': 0
        })
        
        self.assertEqual(mock_user.objects.filter.call_count, 3)



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_verificacion_filtros_estado(self, mock_user):
        """
        Test: Verificación de filtros por estado (ALTA y BAJA)
        
        Given: El servicio de estadísticas.
        When: Se ejecuta el servicio.
        Then: Se debe llamar a filter con estado_hermano=ALTA y luego con estado_hermano=BAJA.
        """
        mock_user.EstadoHermano.ALTA = 'A'
        mock_user.EstadoHermano.BAJA = 'B'
        
        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 0

        get_estadisticas_hermanos_service()

        mock_user.objects.filter.assert_any_call(estado_hermano='A')
        mock_user.objects.filter.assert_any_call(estado_hermano='B')



    @patch('api.servicios.hermano.hermano_service.timezone')
    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_verificacion_filtro_anio(self, mock_user, mock_timezone):
        """
        Test: Verificación de filtro por año actual
        
        Given: Una fecha específica retornada por timezone.now().
        When: Se ejecuta el cálculo de ingresos del año.
        Then: El filtro del queryset debe usar la clave fecha_ingreso_corporacion__year con el año actual.
        """
        anio_test = 2026
        mock_now = MagicMock()
        mock_now.year = anio_test
        mock_timezone.now.return_value = mock_now

        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 0

        get_estadisticas_hermanos_service()

        mock_user.objects.filter.assert_any_call(
            fecha_ingreso_corporacion__year=anio_test
        )



    @patch('api.servicios.hermano.hermano_service.timezone')
    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_anio_mockeado(self, mock_user, mock_timezone):
        """
        Test: Correcto uso del año obtenido de timezone.now()
        
        Given: Un mock de timezone.now() configurado para retornar el año 2026.
        When: Se calculan las estadísticas de ingresos.
        Then: El año utilizado en el filtro de fecha_ingreso_corporacion__year coincide exactamente con el mockeado.
        """
        anio_objetivo = 2026
        mock_fecha = MagicMock()
        mock_fecha.year = anio_objetivo
        mock_timezone.now.return_value = mock_fecha

        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 5

        resultado = get_estadisticas_hermanos_service()

        mock_user.objects.filter.assert_any_call(fecha_ingreso_corporacion__year=anio_objetivo)
        self.assertEqual(resultado['ingresos_anio_actual'], 5)



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_llamadas_independientes(self, mock_user):
        """
        Test: Múltiples llamadas a filter independientes
        
        Given: El servicio de estadísticas.
        When: Se ejecuta el cálculo completo.
        Then: Se realizan exactamente 3 llamadas independientes al método filter para obtener altas, bajas e ingresos.
        """
        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 0

        get_estadisticas_hermanos_service()

        self.assertEqual(mock_user.objects.filter.call_count, 3)



    @patch('api.servicios.hermano.hermano_service.timezone')
    def test_get_estadisticas_hermanos_service_error_timezone(self, mock_timezone):
        """
        Test: Error en timezone.now()
        
        Given: Un fallo inesperado al intentar obtener la fecha del sistema.
        When: timezone.now() lanza una excepción.
        Then: La excepción se propaga y el servicio interrumpe su ejecución inmediatamente.
        """
        mock_timezone.now.side_effect = RuntimeError("Reloj del sistema no disponible")

        with self.assertRaises(RuntimeError) as cm:
            get_estadisticas_hermanos_service()
        
        self.assertEqual(str(cm.exception), "Reloj del sistema no disponible")



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_error_filter(self, mock_user):
        """
        Test: Error en filter
        
        Given: Un problema en la construcción de la consulta o en la conexión con la base de datos.
        When: User.objects.filter() lanza una excepción.
        Then: La excepción se propaga correctamente hacia el llamador.
        """
        mock_user.objects.filter.side_effect = Exception("Error en la sintaxis de la consulta")

        with self.assertRaises(Exception) as cm:
            get_estadisticas_hermanos_service()
            
        self.assertEqual(str(cm.exception), "Error en la sintaxis de la consulta")



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_error_count(self, mock_user):
        """
        Test: Error en count
        
        Given: Un queryset válido retornado por filter.
        When: El método .count() lanza una excepción (ej. timeout de base de datos).
        Then: La excepción se propaga y detiene el cálculo de estadísticas.
        """
        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset

        mock_queryset.count.side_effect = Exception("Timeout al contar registros")

        with self.assertRaises(Exception) as cm:
            get_estadisticas_hermanos_service()
        
        self.assertEqual(str(cm.exception), "Timeout al contar registros")



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_filter_returns_none(self, mock_user):
        """
        Test: filter devuelve None
        
        Given: Un escenario donde, por un error de mockeo o configuración, filter no retorna un queryset.
        When: El servicio intenta encadenar la llamada .count().
        Then: Se lanza un AttributeError (comportamiento esperado al llamar .count() sobre None).
        """
        mock_user.objects.filter.return_value = None

        with self.assertRaises(AttributeError):
            get_estadisticas_hermanos_service()



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_valores_inconsistentes(self, mock_user):
        """
        Test: Valores inconsistentes en conteos (tipos no numéricos)
        
        Given: Un escenario donde el método .count() devuelve tipos inesperados (strings o None).
        When: Se ejecuta el servicio de estadísticas.
        Then: El servicio devuelve los valores tal cual los recibe del ORM, sin realizar validaciones numéricas internas.
        """
        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset

        mock_queryset.count.side_effect = ["10", None, "Muchos"]

        resultado = get_estadisticas_hermanos_service()

        self.assertEqual(resultado['total_alta'], "10")
        self.assertIsNone(resultado['total_baja'])
        self.assertEqual(resultado['ingresos_anio_actual'], "Muchos")



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_verificacion_estructura(self, mock_user):
        """
        Test: Verificación de estructura del resultado
        
        Given: Una ejecución normal del servicio.
        When: Se obtiene el diccionario de resultados.
        Then: El diccionario contiene exactamente las claves esperadas y ninguna otra.
        """
        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 1

        resultado = get_estadisticas_hermanos_service()

        claves_esperadas = {'total_alta', 'total_baja', 'ingresos_anio_actual'}
        self.assertEqual(set(resultado.keys()), claves_esperadas)
        self.assertEqual(len(resultado), 3)