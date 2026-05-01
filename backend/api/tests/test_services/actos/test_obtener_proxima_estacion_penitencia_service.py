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



    @patch('api.servicios.acto.acto_service.TipoActo')
    @patch('api.servicios.acto.acto_service.Acto')
    def test_devuelve_primer_resultado_ordenado_por_fecha(self, mock_acto_model, mock_tipo_acto_model):
        """
        Test: Devuelve el primer resultado ordenado por fecha
        
        Given: Una consulta para buscar la próxima estación de penitencia.
        When: Se ejecuta el servicio.
        Then: Se verifica que se respeta el orden ascendente (.order_by('fecha')) 
            y se extrae el primer elemento (.first()).
        """
        mock_filter_qs = MagicMock()
        mock_select_related_qs = MagicMock()
        mock_order_by_qs = MagicMock()
        
        mock_acto_model.objects.filter.return_value = mock_filter_qs
        mock_filter_qs.select_related.return_value = mock_select_related_qs
        mock_select_related_qs.order_by.return_value = mock_order_by_qs

        obtener_proxima_estacion_penitencia()

        mock_select_related_qs.order_by.assert_called_once_with('fecha')

        mock_order_by_qs.first.assert_called_once()



    @patch('api.servicios.acto.acto_service.timezone')
    @patch('api.servicios.acto.acto_service.TipoActo')
    @patch('api.servicios.acto.acto_service.Acto')
    def test_aplica_correctamente_filtro_por_tipo_de_acto(self, mock_acto_model, mock_tipo_acto_model, mock_timezone):
        """
        Test: Aplica correctamente filtro por tipo de acto
        
        Given: El enum de opciones de tipo de acto.
        When: El servicio construye el QuerySet.
        Then: Se asegura de usar exactamente 'tipo_acto__tipo=ESTACION_PENITENCIA'.
        """
        mock_ahora = MagicMock()
        mock_timezone.now.return_value = mock_ahora

        mock_estacion_penitencia = MagicMock()
        mock_tipo_acto_model.OpcionesTipo.ESTACION_PENITENCIA = mock_estacion_penitencia

        obtener_proxima_estacion_penitencia()

        args, kwargs = mock_acto_model.objects.filter.call_args

        self.assertIn('tipo_acto__tipo', kwargs)
        self.assertEqual(kwargs['tipo_acto__tipo'], mock_estacion_penitencia)



    @patch('api.servicios.acto.acto_service.TipoActo')
    @patch('api.servicios.acto.acto_service.Acto')
    def test_uso_correcto_de_select_related_para_optimizacion(self, mock_acto_model, mock_tipo_acto_model):
        """
        Test: Uso correcto de select_related para optimización
        
        Given: Una consulta de base de datos que cruza relaciones (Acto -> TipoActo).
        When: Se invoca la cadena del QuerySet.
        Then: Se verifica que se incluye la relación 'tipo_acto' para evitar 
            el problema de N+1 queries al acceder a los datos del tipo posteriormente.
        """
        mock_filter_qs = MagicMock()
        mock_acto_model.objects.filter.return_value = mock_filter_qs

        obtener_proxima_estacion_penitencia()

        mock_filter_qs.select_related.assert_called_once_with('tipo_acto')



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



    @patch('api.servicios.acto.acto_service.timezone')
    def test_error_en_timezone_now_propaga_excepcion(self, mock_timezone):
        """
        Test: Error en timezone.now
        
        Given: Un fallo en el sistema operativo o en el módulo timezone.
        When: Se intenta obtener la fecha actual.
        Then: La excepción se propaga al llamador.
        """
        mock_timezone.now.side_effect = RuntimeError("Error en el reloj del sistema")

        with self.assertRaises(RuntimeError) as cm:
            obtener_proxima_estacion_penitencia()
        
        self.assertEqual(str(cm.exception), "Error en el reloj del sistema")



    @patch('api.servicios.acto.acto_service.Acto')
    def test_error_en_filter_propaga_excepcion(self, mock_acto_model):
        """
        Test: Error en filter
        
        Given: Un error de conexión con la base de datos.
        When: Se llama al método .filter().
        Then: La excepción se propaga inmediatamente.
        """
        mock_acto_model.objects.filter.side_effect = Exception("Fallo de conexión a la base de datos")

        with self.assertRaises(Exception):
            obtener_proxima_estacion_penitencia()



    @patch('api.servicios.acto.acto_service.Acto')
    def test_error_en_chain_propaga_excepcion(self, mock_acto_model):
        """
        Test: Error en chain (select_related / order_by / first)
        
        Given: Una consulta que falla en la fase de ordenamiento o selección de relación.
        When: Se ejecuta la cadena del QuerySet.
        Then: Se lanza la excepción en el punto exacto de la cadena.
        """
        mock_filter_qs = MagicMock()
        mock_select_related_qs = MagicMock()
        
        mock_acto_model.objects.filter.return_value = mock_filter_qs
        mock_filter_qs.select_related.return_value = mock_select_related_qs

        mock_select_related_qs.order_by.side_effect = AttributeError("Campo inexistente")

        with self.assertRaises(AttributeError):
            obtener_proxima_estacion_penitencia()



    @patch('api.servicios.acto.acto_service.Acto')
    def test_error_en_first_propaga_excepcion(self, mock_acto_model):
        """
        Test: Error en .first()
        
        Given: Una consulta válida que falla al intentar extraer el primer registro.
        When: Se ejecuta .first().
        Then: La excepción se propaga.
        """
        mock_chain = mock_acto_model.objects.filter.return_value \
                                        .select_related.return_value \
                                        .order_by.return_value
        
        mock_chain.first.side_effect = Exception("Error al ejecutar la query final")

        with self.assertRaises(Exception):
            obtener_proxima_estacion_penitencia()



    @patch('api.servicios.acto.acto_service.Acto')
    def test_transversal_se_invoca_exactamente_una_vez_el_queryset(self, mock_acto_model):
        """
        Test: Se invoca exactamente una vez el queryset
        
        Given: Una llamada al servicio.
        When: Se ejecuta la lógica de obtención.
        Then: Se garantiza que no hay llamadas duplicadas a la base de datos, 
            verificando que .objects.filter solo se ejecuta una vez.
        """
        mock_acto_model.objects.filter.return_value.select_related.return_value \
            .order_by.return_value.first.return_value = MagicMock()

        obtener_proxima_estacion_penitencia()

        self.assertEqual(mock_acto_model.objects.filter.call_count, 1)



    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_transversal_uso_correcto_del_filtro_temporal(self, mock_timezone, mock_acto_model):
        """
        Test: Uso correcto del filtro temporal
        
        Given: Un objeto datetime devuelto por timezone.now().
        When: Se construye el filtro de la consulta.
        Then: Se verifica que se utiliza el operador __gte (Greater Than or Equal) 
            con el valor exacto de 'ahora'.
        """
        mock_ahora = MagicMock(name="MomentoActual")
        mock_timezone.now.return_value = mock_ahora
        
        obtener_proxima_estacion_penitencia()

        args, kwargs = mock_acto_model.objects.filter.call_args
        self.assertEqual(kwargs['fecha__gte'], mock_ahora)



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