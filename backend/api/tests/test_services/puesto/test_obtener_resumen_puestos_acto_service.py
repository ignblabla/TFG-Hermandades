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
    def test_usa_correctamente_filter_acto_id_y_disponible(self, mock_puesto):
        """
        Test: Usa correctamente filter(acto_id, disponible=True)
        
        Given: Un identificador de acto específico.
        When: Se inicia la consulta.
        Then: Se verifica que el filtro de Django se aplica exclusivamente sobre el acto_id proporcionado y solo para puestos cuya marca 'disponible' sea True.
        """
        obtener_resumen_puestos_acto(123)

        mock_puesto.objects.filter.assert_called_once_with(acto_id=123, disponible=True)



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