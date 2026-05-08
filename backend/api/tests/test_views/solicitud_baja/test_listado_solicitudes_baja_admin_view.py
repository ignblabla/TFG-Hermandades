import unittest
from unittest.mock import patch, MagicMock
from django.core.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.solicitud_baja.listado_solicitudes_baja_admin_view import AdminListadoSolicitudesBajaAPIView


class TestAdminListadoSolicitudesBajaAPIView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/admin/solicitudes-baja/'
        self.vista_callable = AdminListadoSolicitudesBajaAPIView.as_view()

        self.admin_user = MagicMock()
        self.admin_user.is_authenticated = True
        self.admin_user.esAdmin = True



    @patch('api.vistas.solicitud_baja.listado_solicitudes_baja_admin_view.ListadoSolicitudesBajaSerializer')
    @patch('api.vistas.solicitud_baja.listado_solicitudes_baja_admin_view.obtener_solicitudes_baja_admin')
    def test_get_lista_solicitudes_correctamente_200(self, mock_service, mock_serializer_class):
        """
        Test: Lista solicitudes correctamente (200)
        
        Given: Un usuario administrador autenticado que hace una petición GET.
        When: El servicio recupera las solicitudes sin errores.
        Then: La vista serializa los datos y devuelve un status 200 OK.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.admin_user)
        
        solicitudes_mock = MagicMock()
        mock_service.return_value = solicitudes_mock
        
        datos_esperados = [{'id': 1, 'estado': 'PENDIENTE'}]
        mock_serializer_class.return_value.data = datos_esperados

        response = self.vista_callable(request)

        mock_service.assert_called_once_with(usuario=self.admin_user)
        mock_serializer_class.assert_called_once_with(solicitudes_mock, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.solicitud_baja.listado_solicitudes_baja_admin_view.obtener_solicitudes_baja_admin')
    def test_get_servicio_lanza_permission_denied_403(self, mock_service):
        """
        Test: Servicio lanza PermissionDenied (403)
        
        Given: Un usuario administrador que realiza la petición.
        When: La lógica interna del servicio lanza un PermissionDenied de Django.
        Then: El except captura el error específico y devuelve un status 403 Forbidden con el mensaje.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.admin_user)
        
        mensaje_error = "Permisos insuficientes en lógica de negocio."
        mock_service.side_effect = PermissionDenied(mensaje_error)

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], mensaje_error)



    @patch('api.vistas.solicitud_baja.listado_solicitudes_baja_admin_view.obtener_solicitudes_baja_admin')
    def test_get_excepcion_inesperada_500(self, mock_service):
        """
        Test: Excepción inesperada (500)
        
        Given: Una petición GET válida de un administrador.
        When: Ocurre un fallo crítico (Exception general) dentro del servicio.
        Then: El except genérico lo captura y devuelve un status 500 Internal Server Error seguro.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.admin_user)
        
        mock_service.side_effect = Exception("Fallo de conexión a la base de datos")

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], "Ocurrió un error inesperado al procesar la solicitud.")



    def test_get_seguridad_bloquea_accesos_no_permitidos(self):
        """
        Test: Seguridad bloquea accesos no permitidos
        
        Given: Peticiones realizadas por un usuario no autenticado y un hermano estándar.
        When: Intentan acceder al listado de administrador.
        Then: La clase de permiso EsAdministrador interviene bloqueando el acceso (401 o 403).
        """
        req_anon = self.factory.get(self.url)
        res_anon = self.vista_callable(req_anon)
        self.assertIn(res_anon.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        req_hermano = self.factory.get(self.url)
        hermano_normal = MagicMock(is_authenticated=True, esAdmin=False)
        force_authenticate(req_hermano, user=hermano_normal)
        
        res_hermano = self.vista_callable(req_hermano)
        self.assertEqual(res_hermano.status_code, status.HTTP_403_FORBIDDEN)