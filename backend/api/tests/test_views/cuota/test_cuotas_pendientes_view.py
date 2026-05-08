from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.vistas.cuota.cuotas_pendientes_view import MisCuotasPendientesView


class TestMisCuotasPendientesView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.path = "/api/cuotas/mis-cuotas-pendientes/"
        self.view = MisCuotasPendientesView.as_view()

        self.mock_user = MagicMock()
        self.mock_user.is_authenticated = True



    @patch("api.vistas.cuota.cuotas_pendientes_view.CuotaService.obtener_cuotas_pendientes_hermano")
    @patch("api.vistas.cuota.cuotas_pendientes_view.MisCuotasPendientesView.get_serializer")
    def test_get_cuotas_pendientes_flujo_exitoso(self, mock_get_serializer, mock_service):
        """
        Test: Listado de cuotas pendientes exitoso
        
        Given: Un usuario autenticado con cuotas pendientes.
        When: Se realiza una petición GET a la vista.
        Then: Se invoca al servicio con el usuario de la petición, se serializa 
            el resultado y se retorna status 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock(name="QuerySetPendiente")
        mock_service.return_value = mock_queryset

        mock_serializer = MagicMock()
        datos_esperados = [{"id": 1, "concepto": "Cuota 2026"}]
        mock_serializer.data = datos_esperados
        mock_get_serializer.return_value = mock_serializer

        response = self.view(request)

        mock_service.assert_called_once_with(self.mock_user)

        mock_get_serializer.assert_called_once_with(mock_queryset, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    def test_get_cuotas_pendientes_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales.
        When: Se intenta acceder al endpoint de cuotas pendientes.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso (401/403).
        """
        request = self.factory.get(self.path)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])