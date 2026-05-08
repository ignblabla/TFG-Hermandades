from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.vistas.hermano.estadisticas_hermano_view import EstadisticasHermanosView


class TestEstadisticasHermanosView(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EstadisticasHermanosView.as_view()
        self.path = "/api/hermanos/estadisticas/"

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True



    @patch('api.vistas.hermano.estadisticas_hermano_view.EstadisticasHermanosSerializer')
    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_get_estadisticas_admin_exitoso(self, mock_service, mock_serializer_class):
        """
        Test: Usuario admin obtiene estadísticas (Happy Path)
        
        Given: Un usuario administrador autenticado.
        When: Se realiza una petición GET a la vista.
        Then: Se invoca al servicio, se serializan los datos devueltos 
            y se retorna status 200 OK con la información.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        datos_servicio = {'total': 500}
        mock_service.return_value = datos_servicio
        
        mock_serializer_instancia = MagicMock()
        mock_serializer_instancia.data = datos_servicio
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_service.assert_called_once()
        mock_serializer_class.assert_called_once_with(datos_servicio)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_servicio)



    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_get_estadisticas_no_admin_denegado(self, mock_service):
        """
        Test: Denegación de acceso a no administradores
        
        Given: Un usuario autenticado que no tiene el flag 'esAdmin'.
        When: Intenta acceder a las estadísticas.
        Then: Se retorna status 403 FORBIDDEN y no se invoca la lógica del servicio.
        """
        request = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = False
        force_authenticate(request, user=mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "No tienes permisos para ver las estadísticas de la Hermandad.")
        mock_service.assert_not_called()



    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_get_estadisticas_error_ia_retorna_500(self, mock_service):
        """
        Test: Manejo de errores internos (bloque try/except)
        
        Given: Un administrador autenticado.
        When: El servicio (o el serializador) lanza una excepción genérica.
        Then: La vista captura el error y retorna status 500 controlado.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.side_effect = Exception("Fallo de cálculo")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al calcular las estadísticas.")
        self.assertEqual(response.data['error'], "Fallo de cálculo")



    def test_get_estadisticas_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales.
        When: Se intenta acceder al endpoint.
        Then: DRF bloquea el acceso con status 401 o 403.
        """
        request = self.factory.get(self.path)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])