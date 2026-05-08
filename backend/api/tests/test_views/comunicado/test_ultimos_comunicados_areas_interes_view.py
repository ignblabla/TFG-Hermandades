import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.comunicado.ultimos_comunicados_areas_interes_view import UltimosComunicadosAreaInteresView


class TestUltimosComunicadosAreaInteresView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UltimosComunicadosAreaInteresView.as_view()
        self.path = "/api/comunicados/ultimos-area-interes/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_get_hay_comunicados_devuelve_200(self, mock_service, mock_serializer):
        """
        Test: Flujo feliz cuando existen comunicados (Rama 1)
        
        Given: Un usuario autenticado y el servicio encuentra resultados.
        When: Se realiza una petición GET.
        Then: Se verifica la llamada al servicio, se confirma existencia, 
            se serializa con el contexto adecuado y retorna 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_queryset

        datos_esperados = [{'id': 1, 'titulo': 'Test'}]
        mock_serializer.return_value.data = datos_esperados

        response = self.view(request)

        mock_service.obtener_ultimos_comunicados_areas_usuario.assert_called_once_with(self.mock_user)
        mock_serializer.assert_called_once_with(
            mock_queryset, 
            many=True, 
            context={'request': ANY}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_get_no_hay_comunicados_devuelve_404(self, mock_service, mock_serializer):
        """
        Test: Flujo cuando no hay resultados (Rama 2)
        
        Given: El servicio devuelve un queryset vacío.
        When: Se realiza la petición GET y .exists() es False.
        Then: No se debe llamar al serializador y se retorna status 404 con el detalle.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_queryset

        response = self.view(request)

        mock_serializer.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No hay comunicados recientes en sus áreas de interés.')



    def test_get_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales.
        When: Se intenta acceder a la vista.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso (401/403).
        """
        request = self.factory.get(self.path)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])