from unittest import TestCase
from unittest.mock import patch, MagicMock

from api.servicios.papeleta_sitio.papeleta_sitio_service import obtener_estadisticas_asistencia
from django.core.exceptions import ValidationError


class TestObtenerEstadisticasAsistencia(TestCase):

    def setUp(self):
        self.patcher_acto = patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
        self.mock_acto = self.patcher_acto.start()
        self.mock_acto.objects.filter.return_value.exists.return_value = True

    def tearDown(self):
        self.patcher_acto.stop()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_estadisticas_correctas(self, mock_papeleta_sitio_model, mock_acto_model):
        """
        Test: Devuelve estadísticas correctas (caso normal)

        Given: Un acto existente con papeletas procesadas en diferentes estados.
        When: Se solicitan las estadísticas de asistencia del acto.
        Then: Se debe calcular y devolver el total, las leídas y las pendientes correctamente.
        """
        acto_id = 1

        mock_acto_model.objects.filter.return_value.exists.return_value = True

        mock_papeleta_sitio_model.EstadoPapeleta.EMITIDA = 'EMITIDA'
        mock_papeleta_sitio_model.EstadoPapeleta.RECOGIDA = 'RECOGIDA'
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = 'LEIDA'

        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': 100,
            'leidas': 60
        }

        resultado = obtener_estadisticas_asistencia(acto_id)

        diccionario_esperado = {
            "total_papeletas": 100,
            "papeletas_leidas": 60,
            "papeletas_pendientes": 40
        }
        self.assertEqual(resultado, diccionario_esperado)

        mock_acto_model.objects.filter.assert_called_once_with(id=acto_id)
        mock_acto_model.objects.filter.return_value.exists.assert_called_once()

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            acto_id=acto_id,
            estado_papeleta__in=['EMITIDA', 'RECOGIDA', 'LEIDA']
        )

        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_calcula_correctamente_pendientes(self, mock_papeleta_sitio_model):
        """
        Test: Calcula correctamente pendientes = total - leidas

        Given: Un resultado de agregación con valores controlados (total=50, leidas=20).
        When: El servicio procesa los resultados del aggregate.
        Then: La resta debe realizarse correctamente devolviendo 30 en papeletas_pendientes.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': 50,
            'leidas': 20
        }

        resultado = obtener_estadisticas_asistencia(1)

        self.assertEqual(resultado["papeletas_pendientes"], 30)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_maneja_total_es_none(self, mock_papeleta_sitio_model):
        """
        Test: Maneja total = None

        Given: Un resultado de base de datos donde 'total' es None.
        When: Se procesan las estadísticas.
        Then: El servicio debe tratar el total como 0 y calcular las pendientes correctamente.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': None,
            'leidas': 0
        }

        resultado = obtener_estadisticas_asistencia(1)

        self.assertEqual(resultado["total_papeletas"], 0)
        self.assertEqual(resultado["papeletas_pendientes"], 0)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_maneja_leidas_es_none(self, mock_papeleta_sitio_model):
        """
        Test: Maneja leidas = None

        Given: Un resultado de base de datos donde 'leidas' es None y total es 10.
        When: Se calculan los resultados finales.
        Then: Se debe tratar leidas como 0, resultando en 10 papeletas pendientes.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': 10,
            'leidas': None
        }

        resultado = obtener_estadisticas_asistencia(1)

        self.assertEqual(resultado["papeletas_leidas"], 0)
        self.assertEqual(resultado["papeletas_pendientes"], 10)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_maneja_ambos_valores_none(self, mock_papeleta_sitio_model):
        """
        Test: Maneja ambos valores None

        Given: Una respuesta de aggregate donde tanto total como leidas son None.
        When: El servicio inicializa las variables.
        Then: Todos los campos de la respuesta deben ser 0 para evitar errores de tipo.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': None,
            'leidas': None
        }

        resultado = obtener_estadisticas_asistencia(1)

        self.assertEqual(resultado["total_papeletas"], 0)
        self.assertEqual(resultado["papeletas_leidas"], 0)
        self.assertEqual(resultado["papeletas_pendientes"], 0)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_filtra_correctamente_por_acto_y_estados_validos(self, mock_papeleta_sitio_model):
        """
        Test: Filtra correctamente por acto_id y estados válidos

        Given: Un ID de acto y las constantes de estado (EMITIDA, RECOGIDA, LEIDA).
        When: Se ejecuta la consulta principal del servicio.
        Then: El método filter debe recibir el acto_id y el operador estado_papeleta__in con la lista de estados correcta.
        """
        mock_papeleta_sitio_model.EstadoPapeleta.EMITIDA = "E"
        mock_papeleta_sitio_model.EstadoPapeleta.RECOGIDA = "R"
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = "L"

        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {'total': 0, 'leidas': 0}

        obtener_estadisticas_asistencia(123)

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            acto_id=123,
            estado_papeleta__in=["E", "R", "L"]
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Q')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Count')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_usa_correctamente_aggregate_con_count_y_q(self, mock_papeleta_sitio_model, mock_count, mock_q):
        """
        Test: Usa correctamente aggregate con Count y Q

        Given: La necesidad de contar el total de registros y filtrar condicionalmente los leídos.
        When: Se realiza la agregación en la base de datos.
        Then: Se debe llamar al método aggregate utilizando instancias de Count y un objeto Q para el filtro de leídas.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {'total': 10, 'leidas': 5}
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = "LEIDA"

        obtener_estadisticas_asistencia(1)

        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.assert_called_once()

        mock_q.assert_called_with(estado_papeleta="LEIDA")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_estructura_de_respuesta_correcta(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve estructura de respuesta correcta

        Given: Un resultado de agregación válido (total=10, leidas=4).
        When: El servicio finaliza su lógica.
        Then: La respuesta debe ser un diccionario con las tres claves estadísticas requeridas: total_papeletas, papeletas_leidas y papeletas_pendientes.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': 10,
            'leidas': 4
        }

        resultado = obtener_estadisticas_asistencia(1)

        self.assertIn("total_papeletas", resultado)
        self.assertIn("papeletas_leidas", resultado)
        self.assertIn("papeletas_pendientes", resultado)
        
        self.assertEqual(resultado["total_papeletas"], 10)
        self.assertEqual(resultado["papeletas_leidas"], 4)
        self.assertEqual(resultado["papeletas_pendientes"], 6)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
    def test_el_acto_no_existe(self, mock_acto_model):
        """
        Test: El acto no existe

        Given: Un identificador de acto que no se encuentra en la base de datos.
        When: Se valida la existencia del acto al inicio del servicio.
        Then: Se debe lanzar una excepción ValidationError con el mensaje "El acto especificado no existe.".
        """
        mock_acto_model.objects.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError) as context:
            obtener_estadisticas_asistencia(999)
        
        self.assertEqual(str(context.exception.message), "El acto especificado no existe.")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
    def test_error_en_exists(self, mock_acto_model):
        """
        Test: Error en exists()

        Given: Un fallo de conexión o error interno al consultar la existencia del acto.
        When: Se ejecuta el método .exists() del queryset.
        Then: La excepción lanzada por la base de datos debe propagarse hacia arriba.
        """
        mock_acto_model.objects.filter.return_value.exists.side_effect = Exception("Error de conexión")

        with self.assertRaises(Exception) as context:
            obtener_estadisticas_asistencia(1)
        
        self.assertEqual(str(context.exception), "Error de conexión")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_filter_de_papeletas(self, mock_papeleta_sitio_model, mock_acto_model):
        """
        Test: Error en filter() de papeletas

        Given: Un acto que sí existe pero un error al intentar filtrar sus papeletas.
        When: Se inicia la consulta de PapeletaSitio.
        Then: El servicio debe fallar permitiendo que la excepción de filter sea visible.
        """
        mock_acto_model.objects.filter.return_value.exists.return_value = True
        mock_papeleta_sitio_model.objects.filter.side_effect = Exception("Fallo en filtro de papeletas")

        with self.assertRaises(Exception) as context:
            obtener_estadisticas_asistencia(1)
            
        self.assertEqual(str(context.exception), "Fallo en filtro de papeletas")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_aggregate(self, mock_papeleta_sitio_model, mock_acto_model):
        """
        Test: Error en aggregate()

        Given: Un queryset de papeletas válido.
        When: Se intenta realizar el cálculo de agregación (Count/Q).
        Then: La excepción ocurrida durante el cálculo de agregados debe ser lanzada por el servicio.
        """
        mock_acto_model.objects.filter.return_value.exists.return_value = True
        mock_qs = mock_papeleta_sitio_model.objects.filter.return_value
        mock_qs.aggregate.side_effect = Exception("Error en el cálculo de agregados")

        with self.assertRaises(Exception) as context:
            obtener_estadisticas_asistencia(1)
            
        self.assertEqual(str(context.exception), "Error en el cálculo de agregados")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_resultado_aggregate_sin_claves_esperadas(self, mock_papeleta_sitio):
        """
        Test: Resultado de aggregate sin claves esperadas

        Given: Una respuesta de aggregate vacía por un comportamiento inesperado del ORM.
        When: El servicio intenta acceder a las claves 'total' y 'leidas'.
        Then: Python lanzará un KeyError al no encontrar las claves en el diccionario.
        """
        mock_papeleta_sitio.objects.filter.return_value.aggregate.return_value = {}

        with self.assertRaises(KeyError):
            obtener_estadisticas_asistencia(1)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_resultado_parcial_aggregate(self, mock_papeleta_sitio):
        """
        Test: Resultado parcial (solo total o solo leidas)

        Given: Un diccionario de agregación incompleto.
        When: Se procesan los valores.
        Then: El servicio debe fallar con KeyError al faltar uno de los componentes necesarios para el cálculo.
        """
        # Caso solo total
        mock_papeleta_sitio.objects.filter.return_value.aggregate.return_value = {"total": 10}
        with self.assertRaises(KeyError):
            obtener_estadisticas_asistencia(1)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_valores_inconsistentes_leidas_mayor_que_total(self, mock_papeleta_sitio):
        """
        Test: Valores inconsistentes (leidas > total)

        Given: Datos inconsistentes en BD donde las leídas superan al total.
        When: Se calcula el valor de pendientes.
        Then: El servicio devolverá un valor negativo en papeletas_pendientes, reflejando fielmente la inconsistencia de los datos.
        """
        mock_papeleta_sitio.objects.filter.return_value.aggregate.return_value = {
            "total": 10,
            "leidas": 15
        }

        resultado = obtener_estadisticas_asistencia(1)
        self.assertEqual(resultado["papeletas_pendientes"], -5)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_robustez_filtro_estados(self, mock_papeleta_sitio):
        """
        Test: Lista de estados vacía o alterada (robustez del filtro)

        Given: Constantes de estado con valores específicos.
        When: Se prepara la lista estados_validos.
        Then: El filtro __in debe contener exactamente los tres estados definidos en la lógica de negocio.
        """
        mock_papeleta_sitio.EstadoPapeleta.EMITIDA = "EMI"
        mock_papeleta_sitio.EstadoPapeleta.RECOGIDA = "REC"
        mock_papeleta_sitio.EstadoPapeleta.LEIDA = "LEI"
        mock_papeleta_sitio.objects.filter.return_value.aggregate.return_value = {"total": 0, "leidas": 0}

        obtener_estadisticas_asistencia(1)

        args, kwargs = mock_papeleta_sitio.objects.filter.call_args
        self.assertCountEqual(kwargs['estado_papeleta__in'], ["EMI", "REC", "LEI"])



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_verificar_que_exists_se_evalua_antes_del_aggregate(self, mock_papeleta_sitio):
        """
        Test: Verificar que exists() se evalúa antes del aggregate

        Given: Un acto que no existe en la base de datos.
        When: Se llama al servicio.
        Then: Se debe lanzar ValidationError y el mock de PapeletaSitio no debe haber sido llamado nunca.
        """
        self.mock_acto.objects.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError):
            obtener_estadisticas_asistencia(1)

        mock_papeleta_sitio.objects.filter.assert_not_called()