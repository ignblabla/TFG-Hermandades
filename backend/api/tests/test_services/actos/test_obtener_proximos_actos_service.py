from unittest.mock import call, patch, MagicMock
from django.test import TestCase

from api.servicios.acto.acto_service import obtener_proximos_actos_dashboard


class TestObtenerProximosActosDashboard(TestCase):

    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_devuelve_proximos_actos_correctamente_limite_por_defecto(self, mock_timezone, mock_acto_model):
        """
        Test: Devuelve los próximos actos correctamente con límite por defecto
        
        Given: Un momento actual y una llamada al servicio sin parámetros.
        When: Se ejecuta la función obtener_proximos_actos_dashboard().
        Then: Se usa timezone.now(), se filtra por fecha, se optimizan campos con .only(), 
            se ordena por fecha y se aplica un slicing de 3 elementos por defecto.
        """
        mock_ahora = MagicMock(name="Ahora")
        mock_timezone.now.return_value = mock_ahora

        mock_filter_qs = MagicMock(name="FilterQS")
        mock_only_qs = MagicMock(name="OnlyQS")
        mock_order_by_qs = MagicMock(name="OrderByQS")
        
        mock_acto_model.objects.filter.return_value = mock_filter_qs
        mock_filter_qs.only.return_value = mock_only_qs
        mock_only_qs.order_by.return_value = mock_order_by_qs

        mock_resultado = [MagicMock(), MagicMock(), MagicMock()]
        mock_order_by_qs.__getitem__.return_value = mock_resultado

        resultado = obtener_proximos_actos_dashboard()

        mock_timezone.now.assert_called_once()

        mock_acto_model.objects.filter.assert_called_once_with(fecha__gte=mock_ahora)
        mock_filter_qs.only.assert_called_once_with('id', 'nombre', 'fecha', 'lugar')
        mock_only_qs.order_by.assert_called_once_with('fecha')

        mock_order_by_qs.__getitem__.assert_called_once_with(slice(None, 3, None))

        self.assertEqual(resultado, mock_resultado)



    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_respeta_parametro_limite_personalizado(self, mock_timezone, mock_acto_model):
        """
        Test: Respeta el parámetro limite personalizado
        
        Given: Una necesidad de mostrar más elementos en el dashboard (ej. limite=5).
        When: Se llama al servicio pasándole el parámetro limite personalizado.
        Then: La consulta se construye igual, pero el slicing dinámico recorta 
            exactamente la cantidad de elementos solicitada.
        """
        limite_personalizado = 5
        mock_timezone.now.return_value = MagicMock()

        mock_filter_qs = MagicMock()
        mock_only_qs = MagicMock()
        mock_order_by_qs = MagicMock()
        
        mock_acto_model.objects.filter.return_value = mock_filter_qs
        mock_filter_qs.only.return_value = mock_only_qs
        mock_only_qs.order_by.return_value = mock_order_by_qs

        obtener_proximos_actos_dashboard(limite=limite_personalizado)

        mock_order_by_qs.__getitem__.assert_called_once_with(slice(None, limite_personalizado, None))



    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_transversal_flujo_completo_del_orm(self, mock_timezone, mock_acto_model):
        """
        Test: Flujo completo del ORM
        
        Given: Una llamada al servicio de actos del dashboard.
        When: Se ejecuta la lógica interna.
        Then: Se verifica mediante tracking el orden estricto de ejecución:
            1. Obtención de tiempo actual.
            2. Filtrado inicial.
            3. Aplicación de optimización (only).
            4. Ordenamiento por fecha.
            5. Aplicación de slicing final.
        """
        mock_ahora = MagicMock(name="Ahora")
        mock_timezone.now.return_value = mock_ahora
        
        mock_filter = MagicMock(name="FilterQS")
        mock_only = MagicMock(name="OnlyQS")
        mock_order = MagicMock(name="OrderByQS")
        
        mock_acto_model.objects.filter.return_value = mock_filter
        mock_filter.only.return_value = mock_only
        mock_only.order_by.return_value = mock_order

        manager = MagicMock()
        manager.attach_mock(mock_timezone.now, 'get_time')
        manager.attach_mock(mock_acto_model.objects.filter, 'filter')
        manager.attach_mock(mock_filter.only, 'only')
        manager.attach_mock(mock_only.order_by, 'order_by')
        manager.attach_mock(mock_order.__getitem__, 'slice')

        obtener_proximos_actos_dashboard(limite=3)

        expected_calls = [
            call.get_time(),
            call.filter(fecha__gte=mock_ahora),
            call.only('id', 'nombre', 'fecha', 'lugar'),
            call.order_by('fecha'),
            call.slice(slice(None, 3, None))
        ]
        manager.assert_has_calls(expected_calls, any_order=False)



    @patch('api.servicios.acto.acto_service.Acto')
    def test_optimizacion_correcta_con_only(self, mock_acto_model):
        """
        Test: Optimización correcta con .only()
        
        Given: El requerimiento de ligereza para las tarjetas del Dashboard.
        When: Se ejecuta la consulta.
        Then: Se valida que se seleccionan únicamente los campos 'id', 'nombre', 
            'fecha' y 'lugar', evitando cargar datos pesados innecesarios.
        """
        mock_filter_qs = MagicMock()
        mock_acto_model.objects.filter.return_value = mock_filter_qs

        obtener_proximos_actos_dashboard()

        campos_esperados = ('id', 'nombre', 'fecha', 'lugar')
        mock_filter_qs.only.assert_called_once_with(*campos_esperados)