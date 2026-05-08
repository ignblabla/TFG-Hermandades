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
    def test_get_devuelve_proximos_actos_correctamente(self, mock_obtener_actos, mock_serializer_class):
        """
        Test: Flujo completo y correcto de obtención de actos (Happy Path Consolidado)
        
        Given: Un usuario autenticado.
        When: Se realiza una petición GET a la vista.
        Then: La vista llama al servicio con limite=3, instancia el serializador 
            con many=True utilizando los datos del servicio, y retorna status 200.
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



    def test_get_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales.
        When: Se intenta acceder al endpoint.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso con 401/403.
        """
        request = self.factory.get(self.path)

        response = self.view(request)
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])