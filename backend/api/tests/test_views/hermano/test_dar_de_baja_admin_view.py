from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory, force_authenticate

from api.vistas.hermano.baja_hermano_admin_view import BajaHermanoAdminView


class TestBajaHermanoAdminView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = BajaHermanoAdminView.as_view()

        self.path = reverse('admin-dar-de-baja-hermano', kwargs={'pk': 1})

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True

        self.mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_user.is_authenticated = True
        self.mock_user.esAdmin = False



    @patch('api.vistas.hermano.baja_hermano_admin_view.dar_de_baja_hermano_service')
    def test_post_baja_correcta_retorna_200(self, mock_service):
        """
        Test: Administrador da de baja correctamente -> 200 OK
        
        Given: Un usuario administrador autenticado que hace una petición POST a la URL de baja.
        When: El servicio `dar_de_baja_hermano_service` se ejecuta sin errores.
        Then: Retorna un status 200 con el detalle de la operación y los nuevos datos del hermano.
        """
        pk_test = 1
        request = self.factory.post(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_hermano_dado_de_baja = MagicMock()
        mock_hermano_dado_de_baja.nombre = "Juan"
        mock_hermano_dado_de_baja.primer_apellido = "Pérez"
        mock_hermano_dado_de_baja.estado_hermano = "BAJA"
        mock_hermano_dado_de_baja.fecha_baja_corporacion = "2026-05-08"
        mock_hermano_dado_de_baja.is_active = False

        mock_service.return_value = mock_hermano_dado_de_baja

        response = self.view(request, pk=pk_test)

        mock_service.assert_called_once_with(
            usuario_solicitante=request.user,
            hermano_id=pk_test
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['detail'], 
            "El hermano Juan Pérez ha sido dado de baja correctamente."
        )
        self.assertEqual(response.data['estado_hermano'], "BAJA")
        self.assertEqual(response.data['fecha_baja_corporacion'], "2026-05-08")
        self.assertFalse(response.data['is_active'])



    @patch('api.vistas.hermano.baja_hermano_admin_view.dar_de_baja_hermano_service')
    def test_post_servicio_lanza_permission_denied_retorna_403(self, mock_service):
        """
        Test: Error de negocio en el servicio -> 403 Forbidden
        
        Given: Un usuario administrador autenticado que hace una petición POST.
        When: El servicio lanza una excepción `PermissionDenied` (ej. intentar dar de baja a otro admin).
        Then: La vista captura la excepción y retorna un status 403 con el mensaje del error.
        """
        pk_test = 1
        request = self.factory.post(self.path)
        force_authenticate(request, user=self.mock_admin)

        mensaje_error = "Un administrador no puede dar de baja a otro administrador."
        mock_service.side_effect = PermissionDenied(mensaje_error)

        response = self.view(request, pk=pk_test)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], mensaje_error)



    @patch('api.vistas.hermano.baja_hermano_admin_view.dar_de_baja_hermano_service')
    def test_post_servicio_lanza_http404_propaga_404(self, mock_service):
        """
        Test: Hermano no encontrado -> 404 Not Found
        
        Given: Un usuario administrador autenticado que hace una petición POST.
        When: El servicio lanza una excepción `Http404` (al no encontrar al hermano por ID).
        Then: La excepción se propaga y DRF devuelve automáticamente un status 404.
        """
        pk_test = 999
        request = self.factory.post(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_service.side_effect = Http404()

        response = self.view(request, pk=pk_test)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.hermano.baja_hermano_admin_view.dar_de_baja_hermano_service')
    def test_post_usuario_no_autenticado_bloqueado(self, mock_service):
        """
        Test: Usuario no autenticado -> 401/403 (Bloqueo DRF)
        
        Given: Una petición POST a la URL de baja sin credenciales de autenticación.
        When: Se intenta acceder a la vista.
        Then: DRF rechaza la petición por la configuración de permisos antes de ejecutar la lógica interna.
        """
        request = self.factory.post(self.path)

        response = self.view(request, pk=1)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        mock_service.assert_not_called()



    @patch('api.vistas.hermano.baja_hermano_admin_view.dar_de_baja_hermano_service')
    def test_post_usuario_no_admin_bloqueado(self, mock_service):
        """
        Test: Usuario sin permisos de admin -> 403 Forbidden
        
        Given: Un usuario autenticado pero cuyo atributo `esAdmin` es False.
        When: Hace una petición POST a la vista.
        Then: La clase de permiso `EsAdministrador` bloquea la petición, impidiendo la ejecución del servicio.
        """
        request = self.factory.post(self.path)
        force_authenticate(request, user=self.mock_user)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_service.assert_not_called()