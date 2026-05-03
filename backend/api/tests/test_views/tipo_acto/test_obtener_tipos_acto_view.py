import unittest
from unittest.mock import MagicMock, PropertyMock, patch
from rest_framework.test import APIRequestFactory

from django.contrib.auth.models import AnonymousUser

from api.vistas.tipo_acto.tipo_acto_view import TipoActoListView


class TestTipoActoListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/tipos-acto/'
        self.user = MagicMock()
        self.user.is_authenticated = True



    @patch("api.vistas.tipo_acto.tipo_acto_view.TipoActoSerializer")
    @patch("api.vistas.tipo_acto.tipo_acto_view.get_tipos_acto_service")
    def test_flujo_feliz_y_llamadas_correctas(self, mock_service, mock_serializer_class):
        """
        Test: Flujo feliz
            Se llama al service
            Serializer se llama con many=True
        
        Given: Una petición GET a la vista de tipos de acto.
        When: El servicio recupera los datos y el serializador los procesa.
        Then: La vista devuelve un 200 OK con la data correcta, habiendo llamado 
            al servicio una vez y configurado el serializador para múltiples objetos.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        datos_mock = ["tipo1", "tipo2"]
        mock_service.return_value = datos_mock
        
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [{"id": 1, "nombre": "Misa"}]
        mock_serializer_class.return_value = mock_serializer_instance

        vista = TipoActoListView()

        respuesta = vista.get(request)

        mock_service.assert_called_once()

        mock_serializer_class.assert_called_once_with(datos_mock, many=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [{"id": 1, "nombre": "Misa"}])



    @patch("api.vistas.tipo_acto.tipo_acto_view.get_tipos_acto_service")
    def test_service_lanza_excepcion_propaga_error(self, mock_service):
        """
        Test: Service lanza excepción
        
        Given: Un fallo en la capa de servicio (ej. error de base de datos).
        When: Se invoca get_tipos_acto_service().
        Then: La excepción sube sin ser capturada para que el framework 
            gestione el error 500 genérico.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.side_effect = Exception("error service")

        vista = TipoActoListView()

        with self.assertRaisesRegex(Exception, "error service"):
            vista.get(request)



    @patch("api.vistas.tipo_acto.tipo_acto_view.TipoActoSerializer")
    @patch("api.vistas.tipo_acto.tipo_acto_view.get_tipos_acto_service")
    def test_serializer_falla_propaga_error(self, mock_service, mock_serializer_class):
        """
        Test: Serializer falla
        
        Given: Un error inesperado al instanciar el serializador.
        When: Se procesan los datos del servicio.
        Then: La excepción se propaga hacia arriba para que DRF lance un 500.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = ["tipo1"]

        mock_serializer_class.side_effect = Exception("serializer error")

        vista = TipoActoListView()

        with self.assertRaisesRegex(Exception, "serializer error"):
            vista.get(request)



    @patch("api.vistas.tipo_acto.tipo_acto_view.TipoActoSerializer")
    @patch("api.vistas.tipo_acto.tipo_acto_view.get_tipos_acto_service")
    def test_acceso_a_data_rompe_propaga_error(self, mock_service, mock_serializer_class):
        """
        Test: .data rompe
        
        Given: Un problema interno durante la evaluación de los campos del serializador.
        When: La vista accede a la propiedad serializer.data.
        Then: El error se propaga limpiamente.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = ["tipo1"]

        mock_instance = MagicMock()
        type(mock_instance).data = PropertyMock(side_effect=Exception("data error"))
        mock_serializer_class.return_value = mock_instance

        vista = TipoActoListView()

        with self.assertRaisesRegex(Exception, "data error"):
            vista.get(request)



    @patch("api.vistas.tipo_acto.tipo_acto_view.TipoActoSerializer")
    @patch("api.vistas.tipo_acto.tipo_acto_view.get_tipos_acto_service")
    def test_service_devuelve_lista_vacia(self, mock_service, mock_serializer_class):
        """
        Test: Service devuelve lista vacía
        
        Given: Una base de datos sin tipos de acto registrados.
        When: Se invoca la vista.
        Then: Se devuelve un HTTP 200 OK con un array vacío.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = []
        
        mock_instance = MagicMock()
        mock_instance.data = []
        mock_serializer_class.return_value = mock_instance

        vista = TipoActoListView()
        
        respuesta = vista.get(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [])



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado (teórico)
        
        Given: Una petición HTTP GET de un usuario anónimo (sin sesión activa).
        When: Se procesa mediante el pipeline real de DRF (as_view).
        Then: La clase IsAuthenticated rechaza la petición devolviendo 401.
        """
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        vista_ejecutable = TipoActoListView.as_view()
        
        respuesta = vista_ejecutable(request)

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.data["detail"].code, "not_authenticated")



    @patch("api.vistas.tipo_acto.tipo_acto_view.TipoActoSerializer")
    @patch("api.vistas.tipo_acto.tipo_acto_view.get_tipos_acto_service")
    def test_response_status_y_contexto_serializer(self, mock_service, mock_serializer_class):
        """
        Test: Response status correcto
            No se pasa contexto al serializer
        
        Given: Una petición exitosa a la vista.
        When: Se instancia el serializador y se retorna la respuesta.
        Then: El status de la respuesta debe ser estrictamente 200 y 
            se debe garantizar que la vista no inyecta el 'context' 
            (request, view) al serializador, manteniéndolo ligero.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = ["tipo_acto_1"]
        mock_instance = MagicMock()
        mock_instance.data = [{"id": 1}]
        mock_serializer_class.return_value = mock_instance

        vista = TipoActoListView()
        
        respuesta = vista.get(request)

        self.assertEqual(respuesta.status_code, 200)

        kwargs_del_serializador = mock_serializer_class.call_args[1]
        
        self.assertNotIn("context", kwargs_del_serializador)