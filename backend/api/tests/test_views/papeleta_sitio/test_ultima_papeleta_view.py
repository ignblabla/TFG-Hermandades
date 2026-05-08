from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from unittest.mock import patch, MagicMock

from api.vistas.papeleta_sitio.ultima_papeleta_view import UltimaPapeletaView


class TestUltimaPapeletaViewPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UltimaPapeletaView.as_view()
        self.path = "/api/papeletas/ultima/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    def test_usuario_no_autenticado_permiso(self):
        """
        Test: Usuario no autenticado (permiso)
        
        Given: Una petición realizada por un usuario anónimo (is_authenticated = False).
        When: DRF evalúa las permission_classes (IsAuthenticated).
        Then: La vista deniega el acceso con un status 403 Forbidden.
        """
        request = self.factory.get(self.path)

        anon_user = MagicMock()
        anon_user.is_authenticated = False
        force_authenticate(request, user=anon_user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_devuelve_200_con_datos_cuando_hay_papeleta(self, mock_service, mock_serializer_class):
        """
        Test: Devuelve 200 con datos cuando hay papeleta
        
        Given: Un usuario autenticado que tiene al menos una papeleta de sitio y solicita verla.
        When: Se realiza una petición GET a la vista.
        Then: La vista invoca al servicio, serializa la papeleta obtenida y retorna un status 200 con los datos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        datos_mockeados_del_servicio = MagicMock()
        mock_service.return_value = datos_mockeados_del_servicio

        mock_serializer_instancia = MagicMock()
        datos_serializados = {'id': 1, 'acto': 'Salida Procesional', 'puesto': 'Nazareno'}
        mock_serializer_instancia.data = datos_serializados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_service.assert_called_once_with(usuario=self.mock_user)
        mock_serializer_class.assert_called_once_with(datos_mockeados_del_servicio)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_serializados)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_no_hay_papeleta_devuelve_404(self, mock_service):
        """
        Test: No hay papeleta (devuelve 404)
        
        Given: Un usuario autenticado que no tiene ninguna papeleta registrada.
        When: Se llama al servicio y este retorna None.
        Then: La vista retorna un status 404 y un mensaje de detalle informativo.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = None
        
        response = self.view(request)
        
        mock_service.assert_called_once_with(usuario=self.mock_user)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "No se han encontrado papeletas para este hermano.")