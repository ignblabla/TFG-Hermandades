from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from unittest.mock import patch, MagicMock

from api.vistas.papeleta_sitio.validar_acceso_qr_papeleta_view import ValidarAccesoQRView


class TestValidarAccesoQRView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ValidarAccesoQRView.as_view()
        self.path = "/api/control-acceso/validar/"

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True

        self.mock_user_normal = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_user_normal.is_authenticated = True
        self.mock_user_normal.esAdmin = False



    @patch('api.vistas.papeleta_sitio.validar_acceso_qr_papeleta_view.PapeletaSitioSerializer')
    @patch('api.vistas.papeleta_sitio.validar_acceso_qr_papeleta_view.validar_acceso_papeleta')
    def test_post_validacion_qr_correcta(self, mock_servicio_validar, mock_serializer):
        """
        Test: Validación de acceso QR correcta
        
        Given: Un usuario administrador que envía un id de papeleta y código válidos.
        When: El servicio de validación procesa los datos con éxito y devuelve la papeleta.
        Then: La vista serializa la papeleta y devuelve un status 200 OK con el resultado.
        """
        data = {"id": 1, "codigo": "QR_SECRETO_123"}
        request = self.factory.post(self.path, data, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_papeleta = MagicMock()
        mock_resultado_servicio = {
            'status': 'OK',
            'mensaje': 'Acceso permitido',
            'papeleta': mock_papeleta
        }
        mock_servicio_validar.return_value = mock_resultado_servicio

        datos_serializados = {"id": 1, "hermano": "Juan Pérez", "estado": "LEIDA"}
        mock_serializer.return_value = MagicMock(data=datos_serializados)

        response = self.view(request)

        mock_servicio_validar.assert_called_once_with(1, "QR_SECRETO_123", self.mock_admin)
        mock_serializer.assert_called_once_with(mock_papeleta)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "resultado": "OK",
            "mensaje": "Acceso permitido",
            "datos": datos_serializados
        })



    @patch('api.vistas.papeleta_sitio.validar_acceso_qr_papeleta_view.validar_acceso_papeleta')
    def test_post_error_validacion_devuelve_400(self, mock_servicio_validar):
        """
        Test: Error en la validación devuelve 400 Bad Request
        
        Given: Un usuario administrador que envía datos que el servicio considera inválidos (ej. QR usado o erróneo).
        When: El servicio de validación lanza una excepción.
        Then: El except captura el error y devuelve un status 400 con el detalle de la excepción.
        """
        data = {"id": 1, "codigo": "QR_INVALIDO"}
        request = self.factory.post(self.path, data, format='json')
        force_authenticate(request, user=self.mock_admin)

        mensaje_error = "El código QR ya ha sido validado anteriormente"
        mock_servicio_validar.side_effect = Exception(mensaje_error)

        response = self.view(request)

        mock_servicio_validar.assert_called_once_with(1, "QR_INVALIDO", self.mock_admin)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": mensaje_error})



    @patch('api.vistas.papeleta_sitio.validar_acceso_qr_papeleta_view.validar_acceso_papeleta')
    def test_acceso_denegado_usuarios_sin_permisos(self, mock_servicio_validar):
        """
        Test: Acceso denegado a usuarios sin permisos de administrador
        
        Given: Peticiones de un usuario no autenticado o de un usuario autenticado sin privilegios.
        When: Intentan enviar datos a la vista de validación.
        Then: La clase de permiso EsAdministrador rechaza las peticiones (401/403) y el servicio no se ejecuta.
        """
        data = {"id": 1, "codigo": "QR_123"}

        request_anon = self.factory.post(self.path, data, format='json')
        response_anon = self.view(request_anon)
        self.assertIn(response_anon.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        request_user = self.factory.post(self.path, data, format='json')
        force_authenticate(request_user, user=self.mock_user_normal)
        
        response_user = self.view(request_user)
        self.assertEqual(response_user.status_code, status.HTTP_403_FORBIDDEN)

        mock_servicio_validar.assert_not_called()