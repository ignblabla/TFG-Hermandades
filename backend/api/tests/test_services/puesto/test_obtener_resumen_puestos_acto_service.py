import unittest
from unittest.mock import MagicMock, patch

from api.servicios.puesto.puesto_service import obtener_resumen_puestos_acto


class TestObtenerResumenPuestosActo(unittest.TestCase):

    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_devuelve_resumen_correctamente_caso_normal(self, mock_puesto_model):
        """
        Test: Devuelve resumen correctamente (caso normal)
        
        Given: Un acto_id válido con puestos disponibles registrados.
        When: Se invoca la función obtener_resumen_puestos_acto.
        Then: La base de datos es consultada filtrando por acto y disponibilidad, y el diccionario devuelto contiene los valores exactos arrojados por el aggregate().
        """
        acto_id = 1

        mock_queryset_filter = mock_puesto_model.objects.filter.return_value

        mock_queryset_filter.aggregate.return_value = {
            'total_puestos': 15,
            'total_cristo': 10,
            'total_virgen': 5
        }

        resultado = obtener_resumen_puestos_acto(acto_id)

        mock_puesto_model.objects.filter.assert_called_once_with(
            acto_id=acto_id, 
            disponible=True
        )

        mock_queryset_filter.aggregate.assert_called_once()

        esperado = {
            "total_puestos": 15,
            "total_cristo": 10,
            "total_virgen": 5
        }
        self.assertEqual(resultado, esperado)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_calcula_correctamente_valores_cuando_todos_vienen_informados(self, mock_puesto):
        """
        Test: Calcula correctamente valores cuando todos vienen informados
        
        Given: Una respuesta de base de datos con valores positivos para todos los contadores.
        When: Se procesa el resultado del aggregate.
        Then: El servicio debe mapear cada clave del diccionario de agregación a la clave correspondiente del resumen final.
        """
        mock_puesto.objects.filter.return_value.aggregate.return_value = {
            'total_puestos': 50,
            'total_cristo': 30,
            'total_virgen': 20
        }

        resultado = obtener_resumen_puestos_acto(1)

        self.assertEqual(resultado['total_puestos'], 50)
        self.assertEqual(resultado['total_cristo'], 30)
        self.assertEqual(resultado['total_virgen'], 20)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_usa_correctamente_filter_acto_id_y_disponible(self, mock_puesto):
        """
        Test: Usa correctamente filter(acto_id, disponible=True)
        
        Given: Un identificador de acto específico.
        When: Se inicia la consulta.
        Then: Se verifica que el filtro de Django se aplica exclusivamente sobre el acto_id proporcionado y solo para puestos cuya marca 'disponible' sea True.
        """
        obtener_resumen_puestos_acto(123)

        mock_puesto.objects.filter.assert_called_once_with(acto_id=123, disponible=True)



    @patch('api.servicios.puesto.puesto_service.Count')
    @patch('api.servicios.puesto.puesto_service.Q')
    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_usa_correctamente_aggregate_con_count_y_q(self, mock_puesto, mock_q, mock_count):
        """
        Test: Usa correctamente aggregate con Count y Q
        
        Given: La necesidad de realizar un desglose por cortejo en una sola consulta.
        When: Se ejecuta el aggregate.
        Then: Se verifica que se llaman a las funciones Count de Django y que se aplican los filtros Q(cortejo_cristo=True/False) según corresponde a cada campo.
        """
        obtener_resumen_puestos_acto(1)

        args, kwargs = mock_puesto.objects.filter.return_value.aggregate.call_args
        self.assertIn('total_puestos', kwargs)
        self.assertIn('total_cristo', kwargs)
        self.assertIn('total_virgen', kwargs)

        mock_q.assert_any_call(cortejo_cristo=True)
        mock_q.assert_any_call(cortejo_cristo=False)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_devuelve_estructura_exacta_del_dict(self, mock_puesto):
        """
        Test: Devuelve estructura exacta del dict
        
        Given: Una ejecución del servicio.
        When: Se obtiene el valor de retorno.
        Then: El diccionario resultante debe tener exactamente las tres claves requeridas por la interfaz, sin campos adicionales ni faltantes.
        """
        mock_puesto.objects.filter.return_value.aggregate.return_value = {
            'total_puestos': 0, 'total_cristo': 0, 'total_virgen': 0
        }

        resultado = obtener_resumen_puestos_acto(1)

        claves_esperadas = {"total_puestos", "total_cristo", "total_virgen"}
        self.assertEqual(set(resultado.keys()), claves_esperadas)
        self.assertEqual(len(resultado), 3)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_error_en_filter_lanza_excepcion(self, mock_puesto):
        """
        Test: Error en filter
        
        Given: Un fallo en la base de datos o un error de conexión al intentar iniciar la consulta.
        When: Se invoca Puesto.objects.filter.
        Then: La excepción lanzada por el ORM debe propagarse íntegramente, permitiendo que el sistema de logs o el middleware de errores la capture.
        """
        mock_puesto.objects.filter.side_effect = Exception("Error de conexión a la base de datos")

        with self.assertRaises(Exception) as context:
            obtener_resumen_puestos_acto(1)
        self.assertEqual(str(context.exception), "Error de conexión a la base de datos")



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_error_en_aggregate_lanza_excepcion(self, mock_puesto):
        """
        Test: Error en aggregate
        
        Given: Un error durante el cálculo de la agregación (por ejemplo, un timeout en una consulta compleja o fallo en funciones SQL).
        When: Se ejecuta el método .aggregate() sobre el queryset filtrado.
        Then: Se debe lanzar la excepción sin que el servicio la capture internamente, asegurando la visibilidad del fallo.
        """
        mock_qs_filter = MagicMock()
        mock_puesto.objects.filter.return_value = mock_qs_filter
        mock_qs_filter.aggregate.side_effect = Exception("Fallo en la función de agregación Count")

        with self.assertRaises(Exception) as context:
            obtener_resumen_puestos_acto(1)
        self.assertEqual(str(context.exception), "Fallo en la función de agregación Count")



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_aggregate_devuelve_none_en_todos_los_campos(self, mock_puesto):
        """
        Test: aggregate devuelve None en todos los campos
        
        Given: Un acto sin puestos donde la base de datos retorna None para todos los contadores de agregación.
        When: Se procesan los datos con la lógica 'or 0'.
        Then: El diccionario resultante debe contener ceros en lugar de valores nulos para evitar errores en el frontend.
        """
        mock_puesto.objects.filter.return_value.aggregate.return_value = {
            'total_puestos': None,
            'total_cristo': None,
            'total_virgen': None
        }

        resultado = obtener_resumen_puestos_acto(1)

        self.assertEqual(resultado['total_puestos'], 0)
        self.assertEqual(resultado['total_cristo'], 0)
        self.assertEqual(resultado['total_virgen'], 0)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_aggregate_devuelve_parcialmente_none(self, mock_puesto):
        """
        Test: aggregate devuelve parcialmente None
        
        Given: Un resultado mixto donde algunos campos tienen valor y otros son nulos.
        When: Se construye el resumen.
        Then: Solo los campos nulos deben ser convertidos a 0, respetando los valores numéricos existentes.
        """
        mock_puesto.objects.filter.return_value.aggregate.return_value = {
            'total_puestos': 10,
            'total_cristo': None,
            'total_virgen': 10
        }

        resultado = obtener_resumen_puestos_acto(1)

        self.assertEqual(resultado['total_puestos'], 10)
        self.assertEqual(resultado['total_cristo'], 0)
        self.assertEqual(resultado['total_virgen'], 10)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_aggregate_devuelve_dict_vacio_o_sin_claves(self, mock_puesto):
        """
        Test: aggregate devuelve dict vacío o sin claves
        
        Given: Un escenario inesperado donde aggregate() no devuelve las claves esperadas.
        When: El código intenta acceder a las claves.
        Then: Se debe lanzar un KeyError, ya que el servicio asume que las claves de agregación siempre están presentes en el contrato del ORM.
        """
        mock_puesto.objects.filter.return_value.aggregate.return_value = {}

        with self.assertRaises(KeyError):
            obtener_resumen_puestos_acto(1)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_valores_inconsistentes_se_mantienen(self, mock_puesto):
        """
        Test: Valores inconsistentes (ej: cristo + virgen ≠ total)
        
        Given: Una respuesta de base de datos donde la suma de las partes no coincide con el total (por datos corruptos o lógica externa).
        When: El servicio procesa la información.
        Then: El servicio debe limitarse a reportar lo que devuelve la base de datos sin intentar corregir o validar la suma aritmética, actuando como un simple transmisor.
        """
        mock_puesto.objects.filter.return_value.aggregate.return_value = {
            'total_puestos': 100,
            'total_cristo': 10,
            'total_virgen': 10
        }

        resultado = obtener_resumen_puestos_acto(1)

        self.assertEqual(resultado['total_puestos'], 100)
        self.assertEqual(resultado['total_cristo'], 10)
        self.assertEqual(resultado['total_virgen'], 10)