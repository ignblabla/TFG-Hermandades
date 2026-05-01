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
    def test_orden_correcto_por_fecha_ascendente(self, mock_acto_model):
        """
        Test: Orden correcto por fecha ascendente
        
        Given: Una consulta de actos para el dashboard.
        When: Se construye el queryset.
        Then: Se verifica que se aplica .order_by('fecha') para garantizar que los 
            actos más cercanos en el tiempo aparezcan primero.
        """
        mock_only_qs = MagicMock()
        mock_acto_model.objects.filter.return_value.only.return_value = mock_only_qs

        obtener_proximos_actos_dashboard()

        mock_only_qs.order_by.assert_called_once_with('fecha')



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



    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_filtrado_correcto_por_fecha_futura(self, mock_timezone, mock_acto_model):
        """
        Test: Filtrado correcto por fecha futura
        
        Given: Un momento determinado en el tiempo.
        When: Se filtran los actos.
        Then: Se verifica que solo se incluyen actos cuya fecha sea mayor o igual 
            al momento actual (fecha__gte=ahora).
        """
        mock_ahora = MagicMock(name="MomentoActual")
        mock_timezone.now.return_value = mock_ahora

        obtener_proximos_actos_dashboard()

        _, kwargs = mock_acto_model.objects.filter.call_args
        
        self.assertEqual(kwargs['fecha__gte'], mock_ahora)
        self.assertIn('fecha__gte', kwargs)



    @patch('api.servicios.acto.acto_service.timezone')
    def test_error_en_timezone_now_propaga_excepcion(self, mock_timezone):
        """
        Test: Error en timezone.now
        
        Given: Un fallo en la obtención de la hora del sistema.
        When: Se invoca al servicio.
        Then: La excepción se propaga al llamador.
        """
        mock_timezone.now.side_effect = RuntimeError("Reloj del sistema no disponible")

        with self.assertRaises(RuntimeError) as cm:
            obtener_proximos_actos_dashboard()
        
        self.assertEqual(str(cm.exception), "Reloj del sistema no disponible")



    @patch('api.servicios.acto.acto_service.Acto')
    def test_error_en_filter_propaga_excepcion(self, mock_acto_model):
        """
        Test: Error en filter
        
        Given: Un error de comunicación con el motor de base de datos.
        When: Se intenta iniciar el filtrado de actos.
        Then: La excepción se propaga inmediatamente.
        """
        mock_acto_model.objects.filter.side_effect = Exception("Fallo crítico en base de datos")

        with self.assertRaises(Exception):
            obtener_proximos_actos_dashboard()



    @patch('api.servicios.acto.acto_service.Acto')
    def test_error_en_only_lanza_excepcion_en_queryset_chain(self, mock_acto_model):
        """
        Test: Error en .only()
        
        Given: Un error al intentar aplicar la optimización de campos.
        When: Se construye la cadena del queryset.
        Then: El error se propaga en el punto de la cadena donde ocurre (.only).
        """
        mock_filter_qs = MagicMock()
        mock_acto_model.objects.filter.return_value = mock_filter_qs

        mock_filter_qs.only.side_effect = ValueError("Campos de optimización inválidos")

        with self.assertRaises(ValueError):
            obtener_proximos_actos_dashboard()



    @patch('api.servicios.acto.acto_service.Acto')
    def test_error_en_order_by_propaga_excepcion(self, mock_acto_model):
        """
        Test: Error en .order_by()
        
        Given: Una cadena de consulta que falla al intentar ordenar.
        When: Se invoca order_by.
        Then: La excepción se propaga.
        """
        mock_only_qs = MagicMock()
        mock_acto_model.objects.filter.return_value.only.return_value = mock_only_qs
        
        mock_only_qs.order_by.side_effect = AttributeError("Campo de ordenación no existe")

        with self.assertRaises(AttributeError):
            obtener_proximos_actos_dashboard()



    @patch('api.servicios.acto.acto_service.Acto')
    def test_error_en_slicing_propaga_excepcion(self, mock_acto_model):
        """
        Test: Error en slicing ([:limite])
        
        Given: Una cadena de consulta válida.
        When: Se intenta aplicar el recorte de resultados (slicing).
        Then: Si ocurre un error inesperado en esta fase, la excepción se propaga.
        """
        mock_order_by_qs = MagicMock()
        mock_acto_model.objects.filter.return_value.only.return_value.order_by.return_value = mock_order_by_qs

        mock_order_by_qs.__getitem__.side_effect = IndexError("Error de índice en el motor de BD")

        with self.assertRaises(IndexError):
            obtener_proximos_actos_dashboard()



    @patch('api.servicios.acto.acto_service.Acto')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_no_hay_actos_futuros_devuelve_lista_vacia(self, mock_timezone, mock_acto_model):
        """
        Test: No hay actos futuros → devuelve lista vacía
        
        Given: Una base de datos que no contiene registros futuros.
        When: Se ejecuta la consulta con los filtros de fecha actuales.
        Then: El servicio retorna una lista vacía [] sin lanzar excepciones.
        """
        mock_order_by_qs = MagicMock()
        mock_acto_model.objects.filter.return_value.only.return_value.order_by.return_value = mock_order_by_qs

        mock_order_by_qs.__getitem__.return_value = []

        resultado = obtener_proximos_actos_dashboard()

        self.assertEqual(resultado, [])
        self.assertEqual(len(resultado), 0)



    @patch('api.servicios.acto.acto_service.Acto')
    def test_limite_igual_a_cero_devuelve_lista_vacia(self, mock_acto_model):
        """
        Test: limite = 0 → devuelve lista vacía
        
        Given: Una petición al servicio solicitando 0 elementos.
        When: Se aplica el slicing [:0].
        Then: El servicio no devuelve elementos, retornando una lista vacía.
        """
        mock_order_by_qs = MagicMock()
        mock_acto_model.objects.filter.return_value.only.return_value.order_by.return_value = mock_order_by_qs

        mock_order_by_qs.__getitem__.return_value = []

        resultado = obtener_proximos_actos_dashboard(limite=0)

        mock_order_by_qs.__getitem__.assert_called_once_with(slice(None, 0, None))
        self.assertEqual(resultado, [])



    @patch('api.servicios.acto.acto_service.Acto')
    def test_transversal_se_invoca_exactamente_una_vez_al_queryset(self, mock_acto_model):
        """
        Test: Se llama exactamente una vez al queryset
        
        Given: Una ejecución estándar del servicio.
        When: Se procesa la solicitud de actos para el dashboard.
        Then: Se verifica que no hay duplicación de consultas a la base de datos, 
            asegurando que el punto de entrada (.filter) se llama una única vez.
        """
        mock_acto_model.objects.filter.return_value.only.return_value \
            .order_by.return_value.__getitem__.return_value = []

        obtener_proximos_actos_dashboard()

        self.assertEqual(mock_acto_model.objects.filter.call_count, 1)



    @patch('api.servicios.acto.acto_service.Acto')
    def test_transversal_se_usa_correctamente_el_valor_de_limite(self, mock_acto_model):
        """
        Test: Se usa correctamente el valor de limite
        
        Given: Un valor de límite específico (ej. 10).
        When: Se invoca al servicio con dicho argumento.
        Then: Se valida que el slicing del queryset utiliza el parámetro recibido 
            para restringir los resultados en la base de datos.
        """
        limite_deseado = 10
        mock_order_by_qs = MagicMock()
        mock_acto_model.objects.filter.return_value.only.return_value.order_by.return_value = mock_order_by_qs

        obtener_proximos_actos_dashboard(limite=limite_deseado)

        mock_order_by_qs.__getitem__.assert_called_once_with(slice(None, limite_deseado, None))



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