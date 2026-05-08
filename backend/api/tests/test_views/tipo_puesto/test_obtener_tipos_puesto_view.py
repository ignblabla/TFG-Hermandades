import unittest
from unittest.mock import MagicMock, PropertyMock, patch
from rest_framework import status
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
    def test_flujo_feliz_y_llamadas_correctas_200(self, mock_service, mock_serializer_class):
        """
        Test: Flujo feliz (200 OK)
        
        Given: Una petición GET autenticada a la vista de tipos de puesto.
        When: El servicio recupera los datos y el serializador los procesa.
        Then: La vista devuelve un 200 OK con la data correcta, habiendo llamado 
            al servicio y configurado el serializador para múltiples objetos (many=True).
        """
        request = self.factory.get(self.url)
        request.user = self.user

        datos_mock = ["tipo1", "tipo2"]
        mock_service.return_value = datos_mock
        
        mock_serializer_instance = MagicMock()
        datos_respuesta = [{"id": 1, "nombre": "Costalero"}]
        mock_serializer_instance.data = datos_respuesta
        mock_serializer_class.return_value = mock_serializer_instance

        vista = TipoPuestoListView()
        respuesta = vista.get(request)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data, datos_respuesta)
        mock_service.assert_called_once()
        mock_serializer_class.assert_called_once_with(datos_mock, many=True)



    @patch("api.vistas.tipo_puesto.tipo_puesto_view.TipoPuestoSerializer")
    @patch("api.vistas.tipo_puesto.tipo_puesto_view.get_tipos_puesto_service")
    def test_service_devuelve_lista_vacia_200(self, mock_service, mock_serializer_class):
        """
        Test: Service devuelve lista vacía (200 OK)
        
        Given: Una consulta donde no existen tipos de puesto en el sistema.
        When: Se procesa la petición GET.
        Then: La vista procesa correctamente la ausencia de datos y devuelve un HTTP 200 OK con un array vacío.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_service.return_value = []
        
        mock_instance = MagicMock()
        mock_instance.data = []
        mock_serializer_class.return_value = mock_instance

        vista = TipoPuestoListView()
        respuesta = vista.get(request)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data, [])



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado (401)
        
        Given: Una petición HTTP GET sin credenciales válidas (usuario anónimo).
        When: La petición pasa por el pipeline de as_view() de DRF.
        Then: La clase IsAuthenticated intercepta la petición y retorna HTTP 401 Unauthorized.
        """
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        vista_ejecutable = TipoPuestoListView.as_view()
        respuesta = vista_ejecutable(request)

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)