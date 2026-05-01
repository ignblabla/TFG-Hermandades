from unittest.mock import PropertyMock, call, patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.vistas.acto.actos_proximos_view import ProximosActosView


class TestProximosActosViewGetPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ProximosActosView.as_view()
        self.path = "/api/actos/proximos/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    @patch('api.vistas.acto.actos_proximos_view.ActoCultoCardSerializer')
    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_devuelve_3_proximos_actos_correctamente(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Devuelve los 3 próximos actos correctamente
        
        Given: Un usuario autenticado solicitando los próximos actos.
        When: Se realiza una petición GET a la vista.
        Then: La vista llama al servicio con limite=3, instancia el serializador 
            con many=True y retorna status 200 con los datos serializados.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_actos_lista = [MagicMock(), MagicMock(), MagicMock()]
        mock_obtener_actos.return_value = mock_actos_lista

        mock_serializer_instancia = MagicMock()
        datos_esperados = [{'id': 1}, {'id': 2}, {'id': 3}]
        mock_serializer_instancia.data = datos_esperados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_obtener_actos.assert_called_once_with(limite=3)

        mock_serializer_class.assert_called_once_with(mock_actos_lista, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_servicio_recibe_limite_correcto(self, mock_obtener_actos):
        """
        Test: El servicio recibe el límite correcto
        
        Given: Una petición GET a la vista del dashboard.
        When: La vista invoca la función de servicio.
        Then: Se verifica que se pasa exactamente el argumento limite=3.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        self.view(request)

        mock_obtener_actos.assert_called_once_with(limite=3)



    @patch('api.vistas.acto.actos_proximos_view.ActoCultoCardSerializer')
    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_serializacion_correcta_de_lista_de_actos(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Serialización correcta de lista de actos
        
        Given: Una lista de actos devuelta por el servicio.
        When: Se prepara la respuesta.
        Then: Se garantiza que el serializador se instancia con el parámetro many=True.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_lista = [MagicMock(), MagicMock()]
        mock_obtener_actos.return_value = mock_lista

        self.view(request)

        _, kwargs = mock_serializer_class.call_args
        self.assertTrue(kwargs.get('many'))
        self.assertEqual(mock_serializer_class.call_args[0][0], mock_lista)



    @patch('api.vistas.acto.actos_proximos_view.ActoCultoCardSerializer')
    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_flujo_completo_correcto(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Flujo completo correcto
        
        Given: Una petición válida.
        When: Se ejecuta la vista.
        Then: Se verifica mediante tracking que el orden de ejecución es:
            1. Llamada al servicio.
            2. Instanciación del serializador con el resultado del servicio.
            3. Retorno de la respuesta.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_resultado_servicio = MagicMock(name="ResultadoServicio")
        mock_obtener_actos.return_value = mock_resultado_servicio
        
        mock_ser_instancia = MagicMock(name="SerializerInstancia")
        mock_ser_instancia.data = []
        mock_serializer_class.return_value = mock_ser_instancia

        manager = MagicMock()
        manager.attach_mock(mock_obtener_actos, 'servicio')
        manager.attach_mock(mock_serializer_class, 'serializer')

        self.view(request)

        expected_calls = [
            call.servicio(limite=3),
            call.serializer(mock_resultado_servicio, many=True)
        ]
        manager.assert_has_calls(expected_calls, any_order=False)



    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_servicio_lanza_excepcion_propaga_error(self, mock_obtener_actos):
        """
        Test: Servicio lanza excepción → error no controlado
        
        Given: Un fallo inesperado en la lógica del servicio (ej. error de BD).
        When: La vista llama al servicio.
        Then: La excepción se propaga (ya que la vista no tiene try/except), 
            permitiendo que el manejador global de excepciones de Django la capture.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_obtener_actos.side_effect = RuntimeError("Error crítico en el servicio")

        with self.assertRaises(RuntimeError) as cm:
            self.view(request)
        
        self.assertEqual(str(cm.exception), "Error crítico en el servicio")



    @patch('api.vistas.acto.actos_proximos_view.ActoCultoCardSerializer')
    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_servicio_devuelve_lista_vacia_retorna_200(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Servicio devuelve lista vacía
        
        Given: El servicio no encuentra actos futuros.
        When: Se recibe una lista vacía [].
        Then: El serializador la procesa y se retorna una lista vacía con status 200.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_obtener_actos.return_value = []
        
        mock_ser_instancia = MagicMock()
        mock_ser_instancia.data = []
        mock_serializer_class.return_value = mock_ser_instancia

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        mock_serializer_class.assert_called_once_with([], many=True)



    @patch('api.vistas.acto.actos_proximos_view.ActoCultoCardSerializer')
    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_error_en_serializer_propaga_excepcion(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Error en serializer
        
        Given: El servicio funciona correctamente.
        When: El serializador lanza un error al instanciarse o acceder a .data.
        Then: La excepción se propaga.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_obtener_actos.return_value = [MagicMock()]

        mock_ser_instancia = MagicMock()
        type(mock_ser_instancia).data = PropertyMock(side_effect=ValueError("Campos de serialización inválidos"))
        mock_serializer_class.return_value = mock_ser_instancia

        with self.assertRaises(ValueError):
            self.view(request)



    @patch('api.vistas.acto.actos_proximos_view.ActoCultoCardSerializer')
    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_get_servicio_devuelve_none_manejado_por_serializer(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Servicio devuelve None
        
        Given: El servicio devuelve None (caso no ideal pero posible).
        When: La vista pasa el resultado al serializador.
        Then: El serializador recibe None y el comportamiento dependerá de su implementación 
            (usualmente resulta en error o respuesta vacía).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_obtener_actos.return_value = None
        
        self.view(request)

        mock_serializer_class.assert_called_once_with(None, many=True)



    def test_transversal_usuario_no_autenticado_bloqueado(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición GET al endpoint de próximos actos.
        When: No se proporciona autenticación.
        Then: Las permission_classes de DRF (IsAuthenticated) bloquean el acceso.
        """
        request = self.factory.get(self.path)

        response = self.view(request)
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_transversal_servicio_llamado_exactamente_una_vez(self, mock_obtener_actos):
        """
        Test: Servicio llamado exactamente una vez
        
        Given: Una petición válida procesada por la vista.
        When: Se ejecuta el método GET.
        Then: Se garantiza que el servicio de obtención de datos no se llama múltiples veces, 
            evitando duplicidad de lógica o carga innecesaria.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        self.view(request)

        mock_obtener_actos.assert_called_once()



    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_transversal_se_respeta_limite_fijo_de_3(self, mock_obtener_actos):
        """
        Test: Se respeta el límite fijo de 3
        
        Given: Una petición al Dashboard.
        When: La vista delega la obtención al servicio.
        Then: El límite pasado debe ser estrictamente 3, cumpliendo con el requisito 
            de diseño de las tarjetas de la interfaz.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        self.view(request)

        args, kwargs = mock_obtener_actos.call_args
        self.assertEqual(kwargs.get('limite'), 3)



    @patch('api.vistas.acto.actos_proximos_view.ActoCultoCardSerializer')
    @patch('api.vistas.acto.actos_proximos_view.obtener_proximos_actos_dashboard')
    def test_transversal_serializer_recibe_input_correcto_del_servicio(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Serializer recibe queryset/list correcto
        
        Given: El servicio devuelve una estructura de datos específica.
        When: Se llega a la fase de serialización.
        Then: El input del serializador debe ser exactamente el objeto devuelto por el servicio, 
            garantizando la integridad del pipeline de datos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_data_from_service = MagicMock(name="QuerySetResult")
        mock_obtener_actos.return_value = mock_data_from_service

        self.view(request)

        mock_serializer_class.assert_called_once_with(mock_data_from_service, many=True)