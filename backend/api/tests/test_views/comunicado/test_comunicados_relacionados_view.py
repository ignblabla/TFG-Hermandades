import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.comunicado.comunicados_relacionados_view import ComunicadosRelacionadosView


class TestComunicadosRelacionadosView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ComunicadosRelacionadosView.as_view()
        self.exclude_id_prueba = 1
        self.path = f"/api/comunicados/{self.exclude_id_prueba}/relacionados/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_get_devuelve_relacionados_correctamente(self, mock_service, mock_serializer):
        """
        Test: Flujo feliz de comunicados relacionados
        
        Given: Un usuario autenticado y un ID de comunicado a excluir.
        When: Se realiza una petición GET a la vista.
        Then: Se llama al servicio con el usuario y el ID correctos, se serializa 
            el resultado con el contexto del request y se retorna status 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock(name="QuerySetRelacionados")
        mock_service.obtener_comunicados_relacionados_usuario.return_value = mock_queryset

        datos_esperados = [{'id': 2, 'titulo': 'Relacionado'}]
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = datos_esperados
        mock_serializer.return_value = mock_serializer_instance

        response = self.view(request, exclude_id=self.exclude_id_prueba)

        mock_service.obtener_comunicados_relacionados_usuario.assert_called_once_with(
            self.mock_user, 
            self.exclude_id_prueba
        )

        mock_serializer.assert_called_once_with(
            mock_queryset, 
            many=True, 
            context={'request': ANY}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    def test_get_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales.
        When: Se intenta acceder al endpoint de relacionados.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso (401/403).
        """
        request = self.factory.get(self.path)

        response = self.view(request, exclude_id=self.exclude_id_prueba)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])