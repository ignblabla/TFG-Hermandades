from unittest.mock import ANY, call, patch, MagicMock
from django.test import TestCase

from api.servicios.acto.acto_service import obtener_proxima_estacion_penitencia


class TestObtenerProximaEstacionPenitenciaPositivos(TestCase):

    @patch('api.servicios.acto.acto_service.TipoActo')
    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_devuelve_proxima_estacion_penitencia_correctamente(self, mock_timezone, mock_acto_model, mock_tipo_acto_model):
        """
        Test: Devuelve la próxima estación de penitencia correctamente
        
        Given: Un momento actual y una base de datos con al menos una Estación de Penitencia futura.
        When: Se llama al servicio obtener_proxima_estacion_penitencia().
        Then: Se construye correctamente la cadena del QuerySet (filter, select_related, 
            order_by, first) y se retorna el objeto Acto esperado.
        """
        mock_ahora = MagicMock(name="Ahora")
        mock_timezone.now.return_value = mock_ahora

        mock_estacion_penitencia = MagicMock()
        mock_tipo_acto_model.OpcionesTipo.ESTACION_PENITENCIA = mock_estacion_penitencia

        mock_filter_qs = MagicMock(name="FilterQS")
        mock_select_related_qs = MagicMock(name="SelectRelatedQS")
        mock_order_by_qs = MagicMock(name="OrderByQS")
        mock_acto_esperado = MagicMock(name="Acto")

        mock_acto_model.objects.filter.return_value = mock_filter_qs
        mock_filter_qs.select_related.return_value = mock_select_related_qs
        mock_select_related_qs.order_by.return_value = mock_order_by_qs
        mock_order_by_qs.first.return_value = mock_acto_esperado

        resultado = obtener_proxima_estacion_penitencia()

        mock_timezone.now.assert_called_once()

        mock_acto_model.objects.filter.assert_called_once_with(
            tipo_acto__tipo=mock_estacion_penitencia,
            fecha__gte=mock_ahora
        )

        mock_filter_qs.select_related.assert_called_once_with('tipo_acto')

        mock_select_related_qs.order_by.assert_called_once_with('fecha')

        mock_order_by_qs.first.assert_called_once()

        self.assertEqual(resultado, mock_acto_esperado)



    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_no_existen_actos_futuros_retorna_none(self, mock_timezone, mock_acto_model):
        """
        Test: No existen actos futuros → retorna None
        
        Given: Una base de datos donde no hay actos que cumplan los criterios.
        When: Se ejecuta el servicio.
        Then: .first() devuelve None y el servicio retorna None correctamente.
        """
        mock_chain = mock_acto_model.objects.filter.return_value \
                                        .select_related.return_value \
                                        .order_by.return_value
        mock_chain.first.return_value = None

        resultado = obtener_proxima_estacion_penitencia()

        self.assertIsNone(resultado)
        mock_chain.first.assert_called_once()



    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_transversal_flujo_completo_del_orm(self, mock_timezone, mock_acto_model):
        """
        Test: Flujo completo del ORM
        
        Given: La necesidad de obtener un único registro optimizado y ordenado.
        When: Se ejecuta el servicio.
        Then: Se verifica mediante tracking que el orden de las operaciones de Django 
            es el esperado para garantizar eficiencia y resultado correcto.
        """
        mock_ahora = MagicMock(name="Ahora")
        mock_timezone.now.return_value = mock_ahora
        
        mock_filter = MagicMock(name="FilterQS")
        mock_select = MagicMock(name="SelectRelatedQS")
        mock_order = MagicMock(name="OrderByQS")
        
        mock_acto_model.objects.filter.return_value = mock_filter
        mock_filter.select_related.return_value = mock_select
        mock_select.order_by.return_value = mock_order

        manager = MagicMock()
        manager.attach_mock(mock_timezone.now, 'get_time')
        manager.attach_mock(mock_acto_model.objects.filter, 'filter')
        manager.attach_mock(mock_filter.select_related, 'select_related')
        manager.attach_mock(mock_select.order_by, 'order_by')
        manager.attach_mock(mock_order.first, 'first')

        obtener_proxima_estacion_penitencia()

        expected_calls = [
            call.get_time(),
            call.filter(tipo_acto__tipo=ANY, fecha__gte=mock_ahora),
            call.select_related('tipo_acto'),
            call.order_by('fecha'),
            call.first()
        ]
        manager.assert_has_calls(expected_calls, any_order=False)