import unittest
from unittest.mock import patch, MagicMock
from django.http import Http404
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.solicitud_baja.resolver_solicitud_baja_view import ResolverSolicitudBajaView


class TestResolverSolicitudBajaView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.pk = 1
        self.url = f'/api/solicitudes-baja/{self.pk}/resolver/'
        self.vista_callable = ResolverSolicitudBajaView.as_view()

        self.admin_user = MagicMock()
        self.admin_user.is_authenticated = True
        self.admin_user.esAdmin = True



    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.SolicitudBajaSerializer')
    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.resolver_solicitud')
    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.get_object_or_404')
    def test_post_accion_aceptar_resuelve_correctamente_200(self, mock_get_404, mock_service, mock_serializer_class):
        """
        Test: Acción ACEPTAR resuelve correctamente (200)
        
        Given: Un usuario administrador que envía la acción "ACEPTAR".
        When: La vista valida el parámetro, procesa el servicio y serializa el resultado.
        Then: Retorna status 200 OK y el mensaje confirmando la aprobación (rama True del ternario).
        """
        request = self.factory.post(self.url, data={'accion': 'ACEPTAR'}, format='json')
        force_authenticate(request, user=self.admin_user)
        
        solicitud_mock = MagicMock()
        mock_get_404.return_value = solicitud_mock
        
        solicitud_resuelta_mock = MagicMock()
        mock_service.return_value = solicitud_resuelta_mock
        
        datos_serializados = {'id': self.pk, 'estado': 'APROBADA'}
        mock_serializer_class.return_value.data = datos_serializados

        response = self.vista_callable(request, pk=self.pk)

        mock_service.assert_called_once_with(solicitud_mock, 'ACEPTAR', self.admin_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mensaje'], "Solicitud aprobada y hermano dado de baja correctamente.")
        self.assertEqual(response.data['solicitud'], datos_serializados)



    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.SolicitudBajaSerializer')
    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.resolver_solicitud')
    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.get_object_or_404')
    def test_post_accion_denegar_resuelve_correctamente_200(self, mock_get_404, mock_service, mock_serializer_class):
        """
        Test: Acción DENEGAR resuelve correctamente (200)
        
        Given: Un usuario administrador que envía la acción "DENEGAR".
        When: La vista procesa el servicio de resolución.
        Then: Retorna status 200 OK y el mensaje confirmando la denegación (rama False del ternario).
        """
        request = self.factory.post(self.url, data={'accion': 'DENEGAR'}, format='json')
        force_authenticate(request, user=self.admin_user)
        
        mock_get_404.return_value = MagicMock()
        mock_service.return_value = MagicMock()
        mock_serializer_class.return_value.data = {'id': self.pk, 'estado': 'DENEGADA'}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mensaje'], "Solicitud denegada correctamente.")



    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.get_object_or_404')
    def test_post_falta_parametro_accion_retorna_400(self, mock_get_404):
        """
        Test: Falta parámetro 'accion' retorna 400
        
        Given: Una petición sin el campo 'accion' en el body.
        When: La vista valida la presencia del dato.
        Then: Retorna inmediatamente un status 400 Bad Request indicando el campo faltante.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=self.admin_user)
        
        mock_get_404.return_value = MagicMock()

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Debe proporcionar el campo 'accion' en el cuerpo de la petición.")



    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.get_object_or_404')
    def test_post_solicitud_no_existe_lanza_404(self, mock_get_404):
        """
        Test: Solicitud no existe (404)
        
        Given: Un PK de solicitud que no existe en BD.
        When: Se ejecuta get_object_or_404.
        Then: Se lanza la excepción Http404 y el framework retorna 404 Not Found.
        """
        request = self.factory.post(self.url, data={'accion': 'ACEPTAR'}, format='json')
        force_authenticate(request, user=self.admin_user)
        
        mock_get_404.side_effect = Http404()

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.resolver_solicitud')
    @patch('api.vistas.solicitud_baja.resolver_solicitud_baja_view.get_object_or_404')
    def test_post_excepcion_en_servicio_retorna_400(self, mock_get_404, mock_service):
        """
        Test: Excepción en servicio retorna 400
        
        Given: Una petición válida donde el servicio de resolución falla (ej. estado inválido).
        When: resolver_solicitud lanza una Exception.
        Then: El bloque try/except captura el fallo y retorna 400 con el string del error.
        """
        request = self.factory.post(self.url, data={'accion': 'ACEPTAR'}, format='json')
        force_authenticate(request, user=self.admin_user)
        
        mock_get_404.return_value = MagicMock()
        
        mensaje_error = "La solicitud ya ha sido resuelta previamente."
        mock_service.side_effect = Exception(mensaje_error)

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], mensaje_error)



    def test_post_seguridad_bloquea_accesos_no_permitidos(self):
        """
        Test: Seguridad bloquea accesos no permitidos
        
        Given: Peticiones de un usuario no autenticado y un usuario normal (no admin).
        When: Intentan ejecutar el método POST.
        Then: El permiso EsAdministrador interviene y rechaza el acceso (401 o 403).
        """
        req_anon = self.factory.post(self.url, data={'accion': 'ACEPTAR'}, format='json')
        res_anon = self.vista_callable(req_anon, pk=self.pk)
        self.assertIn(res_anon.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        req_hermano = self.factory.post(self.url, data={'accion': 'ACEPTAR'}, format='json')
        hermano_normal = MagicMock(is_authenticated=True, esAdmin=False)
        force_authenticate(req_hermano, user=hermano_normal)
        
        res_hermano = self.vista_callable(req_hermano, pk=self.pk)
        self.assertEqual(res_hermano.status_code, status.HTTP_403_FORBIDDEN)