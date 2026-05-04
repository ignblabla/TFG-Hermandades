from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from api.servicios.acto.acto_service import ActoService

class ActoServiceGetTodosTests(TestCase):

    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_get_todos_los_actos_devuelve_queryset_filtrado_y_ordenado(self, mock_timezone, mock_objects):
        """
        Test: Devuelve queryset ordenado por fecha y filtrado por actos futuros

        Given: El servicio ActoService y una fecha actual fija.
        When: Se llama al método get_todos_los_actos.
        Then: Se debe invocar a Acto.objects.filter con fecha mayor o igual a la actual.
                Se debe encadenar el método order_by con el argumento 'fecha'.
                El método debe retornar el queryset final mockeado.
        """
        ahora = timezone.now()
        mock_timezone.now.return_value = ahora

        mock_queryset_filtrado = MagicMock()
        mock_queryset_ordenado = MagicMock()

        mock_objects.filter.return_value = mock_queryset_filtrado
        mock_queryset_filtrado.order_by.return_value = mock_queryset_ordenado

        resultado = ActoService.get_todos_los_actos()

        mock_objects.filter.assert_called_once_with(fecha__gte=ahora)
        mock_queryset_filtrado.order_by.assert_called_once_with('fecha')
        self.assertEqual(resultado, mock_queryset_ordenado)



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_encadenamiento_correcto_del_queryset(self, mock_timezone, mock_objects):
        """
        Test: Encadenamiento correcto de queryset

        Given: El servicio ActoService y una fecha mockeada.
        When: Se llama al método get_todos_los_actos.
        Then: Se debe verificar que 'order_by' se invoca específicamente sobre 
                el objeto devuelto por 'filter()', y no sobre el manager 'objects'.
                Esto garantiza que se sigue el patrón de QuerySet de Django.
        """
        ahora = timezone.now()
        mock_timezone.now.return_value = ahora
        
        mock_queryset_filter = MagicMock()
        mock_queryset_final = MagicMock()

        mock_objects.filter.return_value = mock_queryset_filter
        mock_queryset_filter.order_by.return_value = mock_queryset_final

        resultado = ActoService.get_todos_los_actos()

        mock_objects.order_by.assert_not_called()

        mock_objects.filter.assert_called_once_with(fecha__gte=ahora)

        mock_queryset_filter.order_by.assert_called_once_with('fecha')

        self.assertEqual(resultado, mock_queryset_final)



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_retorna_exactamente_el_resultado_de_order_by(self, mock_timezone, mock_objects):
        """
        Test: Retorna exactamente el resultado de order_by

        Given: El servicio ActoService y una fecha mockeada.
        When: Se llama al método get_todos_los_actos.
        Then: El valor de retorno de la función debe ser el mismo objeto 
                que devuelve el método order_by() del QuerySet.
                Garantiza que el servicio no aplica transformaciones (como list())
                que podrían romper el lazy loading de Django.
        """
        mock_timezone.now.return_value = timezone.now()
        
        mock_final_result = MagicMock(name="QuerySet_Final")
        mock_queryset_filter = MagicMock(name="QuerySet_Filter")

        mock_objects.filter.return_value = mock_queryset_filter
        mock_queryset_filter.order_by.return_value = mock_final_result

        resultado = ActoService.get_todos_los_actos()

        self.assertIs(resultado, mock_final_result)



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_soporta_queryset_vacio_sin_alterar_el_resultado(self, mock_timezone, mock_objects):
        """
        Test: Soporta queryset vacío

        Given: El servicio ActoService y una fecha mockeada.
                El ORM devuelve un QuerySet que representa una lista vacía tras filtrar y ordenar.
        When: Se llama al método get_todos_los_actos.
        Then: El servicio debe retornar el QuerySet vacío sin intentar 
                validar su contenido ni lanzar excepciones.
                Se garantiza que el servicio solo delega en el ORM.
        """
        mock_timezone.now.return_value = timezone.now()
        
        mock_queryset_filter = MagicMock(name="QuerySet_Filter")
        mock_queryset_vacio = MagicMock(name="QuerySet_Vacio")

        mock_objects.filter.return_value = mock_queryset_filter
        mock_queryset_filter.order_by.return_value = mock_queryset_vacio

        resultado = ActoService.get_todos_los_actos()

        self.assertEqual(resultado, mock_queryset_vacio)

        mock_queryset_vacio.assert_not_called()



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_filter_lanza_excepcion_y_el_servicio_la_propaga(self, mock_timezone, mock_objects):
        """
        Test: Acto.objects.filter() lanza excepción

        Given: El servicio ActoService y un fallo crítico en el ORM.
        When: Se llama al método get_todos_los_actos.
        Then: La excepción lanzada por Acto.objects.filter() debe propagarse 
                sin ser capturada por el servicio.
                Se garantiza que no hay bloques try-except que oculten fallos.
        """
        mock_timezone.now.return_value = timezone.now()
        mensaje_error = "Error crítico: Base de datos no operacional"
        mock_objects.filter.side_effect = Exception(mensaje_error)

        with self.assertRaises(Exception) as context:
                ActoService.get_todos_los_actos()

        self.assertEqual(str(context.exception), mensaje_error)
        mock_objects.filter.assert_called_once()



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_order_by_lanza_excepcion_y_el_servicio_la_propaga(self, mock_timezone, mock_objects):
        """
        Test: .order_by() lanza excepción

        Given: El servicio ActoService.
                El método filter() funciona correctamente y devuelve un queryset.
                El método order_by() lanza una excepción inesperada.
        When: Se llama al método get_todos_los_actos.
        Then: La excepción debe propagarse hacia el llamador.
                Se garantiza que el servicio no intercepta errores del ORM 
                en ninguna parte de la cadena.
        """
        ahora = timezone.now()
        mock_timezone.now.return_value = ahora
        
        mock_queryset_filter = MagicMock(name="QuerySet_Filter")
        mock_objects.filter.return_value = mock_queryset_filter

        mensaje_error = "Error de ordenamiento en la base de datos"
        mock_queryset_filter.order_by.side_effect = Exception(mensaje_error)

        with self.assertRaises(Exception) as context:
                ActoService.get_todos_los_actos()

        self.assertEqual(str(context.exception), mensaje_error)

        mock_objects.filter.assert_called_once_with(fecha__gte=ahora)
        mock_queryset_filter.order_by.assert_called_once_with('fecha')



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_get_todos_los_actos_llama_a_order_by_con_argumento_especifico(self, mock_timezone, mock_objects):
        """
        Test: order_by recibe argumento específico (test de contrato)

        Given: El servicio ActoService y una fecha mockeada.
        When: Se llama al método get_todos_los_actos.
        Then: Se debe verificar que el argumento pasado a order_by es exactamente 'fecha'.
                Esto garantiza que cualquier cambio accidental en el criterio de ordenación 
                en el código fuente sea detectado por la suite de pruebas.
        """
        mock_timezone.now.return_value = timezone.now()
        mock_queryset_filter = MagicMock(name="QuerySet_Filter")
        mock_objects.filter.return_value = mock_queryset_filter

        ActoService.get_todos_los_actos()

        mock_queryset_filter.order_by.assert_called_once_with('fecha')

        args, _ = mock_queryset_filter.order_by.call_args
        self.assertIn('fecha', args)
        self.assertNotIn('-fecha', args)
        self.assertNotIn('id', args)



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_filter_retorna_objeto_inesperado_lanza_attribute_error(self, mock_timezone, mock_objects):
        """
        Test: filter() no devuelve queryset (retorno inesperado)

        Given: El servicio ActoService.
                El método filter() devuelve un objeto inesperado (None) que no 
                posee el método 'order_by'.
        When: Se llama al método get_todos_los_actos.
        Then: El servicio debe lanzar un AttributeError al intentar ejecutar 
                .order_by() sobre un objeto que no lo soporta.
                Esto confirma que el servicio no intenta sanear fallos del ORM.
        """
        mock_timezone.now.return_value = timezone.now()
        mock_objects.filter.return_value = None

        with self.assertRaises(AttributeError):
                ActoService.get_todos_los_actos()

        mock_objects.filter.assert_called_once()



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_order_by_devuelve_instancia_distinta_y_el_servicio_la_respeta(self, mock_timezone, mock_objects):
        """
        Test: order_by devuelve objeto distinto

        Given: El servicio ActoService y una fecha mockeada.
                El método filter() devuelve un objeto QuerySet A.
                El método order_by() devuelve un objeto QuerySet B (diferente al A).
        When: Se llama al método get_todos_los_actos.
        Then: El servicio debe retornar el objeto B.
                Se asegura que no se devuelve accidentalmente el resultado de filter() 
                y que se respeta la cadena de transformación del ORM.
        """
        mock_timezone.now.return_value = timezone.now()
        mock_queryset_filter = MagicMock(name="Instancia_A_Filtrada")
        mock_queryset_ordenado = MagicMock(name="Instancia_B_Ordenada")

        mock_objects.filter.return_value = mock_queryset_filter
        mock_queryset_filter.order_by.return_value = mock_queryset_ordenado

        resultado = ActoService.get_todos_los_actos()

        self.assertIs(resultado, mock_queryset_ordenado)
        self.assertIsNot(resultado, mock_queryset_filter)
        self.assertEqual(resultado._extract_mock_name(), "Instancia_B_Ordenada")



    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_servicio_es_un_passthrough_puro_sin_logica_adicional(self, mock_timezone, mock_objects):
        """
        Test: Verificar que no hay lógica adicional de inspección

        Given: El servicio ActoService.
        When: Se llama al método get_todos_los_actos.
        Then: Se verifica que NO se han llamado a métodos de inspección 
                o transformación adicionales (como .count(), .exists() o list()).
                Garantiza que el servicio es un passthrough puro hacia el ORM 
                y mantiene el comportamiento lazy del QuerySet.
        """
        mock_timezone.now.return_value = timezone.now()
        mock_queryset_filter = MagicMock(name="QS_Filter")
        mock_queryset_final = MagicMock(name="QS_Final")
        
        mock_objects.filter.return_value = mock_queryset_filter
        mock_queryset_filter.order_by.return_value = mock_queryset_final

        resultado = ActoService.get_todos_los_actos()

        self.assertEqual(mock_objects.filter.call_count, 1)
        self.assertEqual(mock_queryset_filter.order_by.call_count, 1)

        mock_queryset_final.__iter__.assert_not_called()
        mock_queryset_final.count.assert_not_called()
        mock_queryset_final.exists.assert_not_called()

        self.assertIs(resultado, mock_queryset_final)