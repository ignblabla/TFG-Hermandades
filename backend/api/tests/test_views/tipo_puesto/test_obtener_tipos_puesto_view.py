import unittest
from unittest.mock import MagicMock, PropertyMock, patch
from rest_framework.test import APIRequestFactory

from django.contrib.auth.models import AnonymousUser

from api.vistas.tipo_puesto.tipo_puesto_view import TipoPuestoListView


class TestTipoPuestoListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/tipos-puesto/'
        self.user = MagicMock()
        self.user.is_authenticated = True



    @patch("api.vistas.tipo_puesto.tipo_puesto_view.TipoPuestoSerializer")
    @patch("api.vistas.tipo_puesto.tipo_puesto_view.get_tipos_puesto_service")
    def test_flujo_feliz_y_llamadas_correctas(self, mock_service, mock_serializer_class):
        """
        Test: Flujo feliz
            Se llama al service
            Serializer recibe many=True
        
        Given: Una petición GET válida a la vista de tipos de puesto.
        When: El servicio recupera los datos y el serializador los procesa.
        Then: La vista devuelve un 200 OK con la data correcta, garantizando 
            las llamadas al servicio y al serializador con el parámetro many=True.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        datos_mock = ["tipo1", "tipo2"]
        mock_service.return_value = datos_mock
        
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [{"id": 1, "nombre": "Costalero"}]
        mock_serializer_class.return_value = mock_serializer_instance

        vista = TipoPuestoListView()

        respuesta = vista.get(request)

        mock_service.assert_called_once()

        mock_serializer_class.assert_called_once_with(datos_mock, many=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [{"id": 1, "nombre": "Costalero"}])



    @patch("api.vistas.tipo_puesto.tipo_puesto_view.get_tipos_puesto_service")
    def test_service_lanza_excepcion_propaga_error(self, mock_service):
        """
        Test: Service lanza excepción
        
        Given: Un fallo crítico en la capa de servicio al consultar la base de datos.
        When: Se invoca get_tipos_puesto_service().
        Then: La excepción debe subir sin ser interceptada para que DRF maneje el HTTP 500.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.side_effect = Exception("service error")

        vista = TipoPuestoListView()

        with self.assertRaisesRegex(Exception, "service error"):
            vista.get(request)



    @patch("api.vistas.tipo_puesto.tipo_puesto_view.TipoPuestoSerializer")
    @patch("api.vistas.tipo_puesto.tipo_puesto_view.get_tipos_puesto_service")
    def test_serializer_falla_al_instanciar(self, mock_service, mock_serializer_class):
        """
        Test: Serializer falla al instanciar
        
        Given: Un error imprevisto al iniciar la clase del serializador.
        When: La vista intenta instanciar TipoPuestoSerializer con los datos del servicio.
        Then: El error de instanciación se propaga hacia el bloque superior.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = ["tipo1"]

        mock_serializer_class.side_effect = Exception("serializer error")

        vista = TipoPuestoListView()

        with self.assertRaisesRegex(Exception, "serializer error"):
            vista.get(request)



    @patch("api.vistas.tipo_puesto.tipo_puesto_view.TipoPuestoSerializer")
    @patch("api.vistas.tipo_puesto.tipo_puesto_view.get_tipos_puesto_service")
    def test_error_accediendo_a_data_propaga_error(self, mock_service, mock_serializer_class):
        """
        Test: 6. ❌ Error accediendo a .data
        
        Given: Un fallo interno al serializar los objetos devueltos por el servicio.
        When: La vista intenta acceder a la propiedad .data del serializador.
        Then: La excepción se propaga correctamente sin ser enmascarada.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = ["tipo1"]

        mock_instance = MagicMock()
        type(mock_instance).data = PropertyMock(side_effect=Exception("data error"))
        mock_serializer_class.return_value = mock_instance

        vista = TipoPuestoListView()

        with self.assertRaisesRegex(Exception, "data error"):
            vista.get(request)



    @patch("api.vistas.tipo_puesto.tipo_puesto_view.TipoPuestoSerializer")
    @patch("api.vistas.tipo_puesto.tipo_puesto_view.get_tipos_puesto_service")
    def test_service_devuelve_lista_vacia(self, mock_service, mock_serializer_class):
        """
        Test: Service devuelve lista vacía
        
        Given: Una consulta donde no existen tipos de puesto en el sistema.
        When: Se procesa la petición GET.
        Then: La vista devuelve un HTTP 200 OK y la data es un array vacío.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = []
        
        mock_instance = MagicMock()
        mock_instance.data = []
        mock_serializer_class.return_value = mock_instance

        vista = TipoPuestoListView()
        
        respuesta = vista.get(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [])



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado (si ejecutas permisos)
        
        Given: Una petición HTTP GET sin credenciales válidas.
        When: Pasa por el as_view() de DRF.
        Then: Retorna HTTP 401 Unauthorized.
        """
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        vista_ejecutable = TipoPuestoListView.as_view()
        
        respuesta = vista_ejecutable(request)

        self.assertEqual(respuesta.status_code, 401)



    @patch("api.vistas.tipo_puesto.tipo_puesto_view.TipoPuestoSerializer")
    @patch("api.vistas.tipo_puesto.tipo_puesto_view.get_tipos_puesto_service")
    def test_status_correcto_y_sin_contexto_serializer(self, mock_service, mock_serializer_class):
        """
        Test: Status HTTP correcto
            No se pasa context al serializer

        Given: Una petición exitosa que obtiene datos.
        When: Se construye la respuesta.
        Then: El status debe ser exactamente 200 y el serializador no debe 
            recibir la inyección del kwargs 'context'.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = ["tipo1"]
        mock_instance = MagicMock()
        mock_instance.data = [{"id": 1}]
        mock_serializer_class.return_value = mock_instance

        vista = TipoPuestoListView()
        
        respuesta = vista.get(request)

        self.assertEqual(respuesta.status_code, 200)

        kwargs_del_serializador = mock_serializer_class.call_args[1]
        self.assertNotIn("context", kwargs_del_serializador)
