from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.vistas.cuota.numero_cuotas_pendientes_view import NumeroCuotasPendientesView


class TestNumeroCuotasPendientesView(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.path = "/api/cuotas/mis-cuotas-pendientes/total/"
        self.view = NumeroCuotasPendientesView.as_view()

        self.mock_user = MagicMock()
        self.mock_user.is_authenticated = True



    @patch("api.vistas.cuota.numero_cuotas_pendientes_view.CuotaService.contar_cuotas_pendientes_hermano")
    def test_get_total_pendientes_exitoso(self, mock_service):
        """
        Test: Obtener número total de cuotas pendientes con éxito
        
        Given: Un usuario autenticado.
        When: Se realiza una petición GET a la vista.
        Then: Se invoca al servicio con el usuario de la petición y se retorna 
            un status 200 con el valor entero devuelto por el servicio.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_service.return_value = 5

        response = self.view(request)

        mock_service.assert_called_once_with(self.mock_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"total_pendientes": 5})



    def test_get_total_pendientes_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales.
        When: Se intenta acceder al endpoint.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso (401/403).
        """
        request = self.factory.get(self.path)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])