import unittest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.vistas.puesto.crear_puesto_view import CrearPuestoView
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador


class TestCrearPuestoViewPermisos(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/puestos/'
        self.user = MagicMock()
        self.user.is_authenticated = True 

        self.vista_callable = CrearPuestoView.as_view()
        self.data_post = {"nombre": "Costalero", "acto": 1}



    @patch.object(EsAdministrador, 'has_permission', return_value=True)
    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_post_crea_puesto_correctamente_201(self, mock_serializer_class, mock_service, mock_permiso):
        """
        Test: Crea puesto correctamente (201)
        
        Given: Datos de entrada válidos y un usuario autenticado con permisos de administrador.
        When: Se realiza una petición POST.
        Then: La vista valida, ejecuta el servicio y devuelve HTTP 201 con los datos serializados.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)

        mock_ser_in = MagicMock()
        mock_ser_in.validated_data = self.data_post

        mock_ser_out = MagicMock()
        mock_ser_out.data = {"id": 1, "nombre": "Costalero", "acto": 1}

        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]

        puesto_creado_mock = MagicMock()
        mock_service.return_value = puesto_creado_mock

        response = self.vista_callable(request)

        mock_ser_in.is_valid.assert_called_once_with(raise_exception=True)
        mock_service.assert_called_once_with(usuario=self.user, data_validada=self.data_post)
        mock_serializer_class.assert_called_with(puesto_creado_mock)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, mock_ser_out.data)



    @patch.object(EsAdministrador, 'has_permission', return_value=True)
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_post_serializer_invalido_retorna_400_bad_request(self, mock_serializer_class, mock_permiso):
        """
        Test: Serializer inválido -> 400 Bad Request
        
        Given: Datos de entrada inválidos y un usuario administrador.
        When: La vista invoca is_valid(raise_exception=True).
        Then: DRF captura la ValidationError y retorna una respuesta 400 con los errores.
        """
        request = self.factory.post(self.url, data={"nombre": ""}, format='json')
        force_authenticate(request, user=self.user)

        mock_ser_in = MagicMock()
        errores_esperados = {"nombre": ["Este campo no puede estar vacío."]}

        mock_ser_in.is_valid.side_effect = ValidationError(errores_esperados)
        mock_serializer_class.return_value = mock_ser_in

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, errores_esperados)



    @patch.object(EsAdministrador, 'has_permission', return_value=False)
    def test_usuario_autenticado_no_administrador_acceso_denegado_403(self, mock_permiso):
        """
        Test: Usuario autenticado sin rol admin -> 403 Forbidden
        
        Given: Una petición POST de un usuario autenticado pero sin privilegios de administrador.
        When: La petición entra en la vista y se evalúa EsAdministrador.
        Then: DRF deniega el acceso devolviendo un 403.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    def test_usuario_no_autenticado_acceso_denegado_401(self):
        """
        Test: Usuario no autenticado -> 401 Unauthorized
        
        Given: Una petición POST enviada por un usuario anónimo.
        When: Se evalúan los permisos de la vista.
        Then: DRF rechaza inmediatamente la petición con un error HTTP 401.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)