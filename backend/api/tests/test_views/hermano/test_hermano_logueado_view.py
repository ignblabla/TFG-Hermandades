from unittest.mock import PropertyMock, call, patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.vistas.hermano.hermano_logueado_view import UsuarioLogueadoView


class TestUsuarioLogueadoViewGetPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UsuarioLogueadoView.as_view()
        self.path = "/api/me/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch('api.vistas.hermano.hermano_logueado_view.UserSerializer')
    def test_get_usuario_autenticado_devuelve_datos_correctamente(self, mock_serializer_class):
        """
        Test: Usuario autenticado → devuelve datos correctamente
        
        Given: Un usuario autenticado realizando una petición GET.
        When: La vista procesa la solicitud para obtener el perfil actual.
        Then: Se instancia UserSerializer con request.user y retorna un status 200 con los datos serializados.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_serializer_instancia = MagicMock()
        datos_esperados = {'id': 1, 'email': 'test@test.com', 'nombre': 'Usuario Test'}
        mock_serializer_instancia.data = datos_esperados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_serializer_class.assert_called_once_with(self.mock_user)

        self.assertEqual(response.data, datos_esperados)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    def test_get_usuario_no_autenticado_bloqueado(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición GET sin token ni sesión.
        When: Se intenta acceder al perfil propio.
        Then: DRF bloquea el acceso mediante IsAuthenticated (401 o 403).
        """
        request = self.factory.get(self.path)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    # ---------------------------------------------------------------------------
    # TESTS PATCH
    # ---------------------------------------------------------------------------

    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_actualizacion_parcial_correcta(self, mock_serializer_class, mock_service):
        """
        Test: Actualización parcial correcta
        
        Given: Un payload parcial enviado por el usuario autenticado.
        When: Se realiza una petición PATCH.
        Then: El serializer valida los datos, se llama al servicio y retorna 200 con el perfil actualizado.
        """
        payload = {'nombre': 'Nuevo Nombre'}
        request = self.factory.patch(self.path, payload, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True
        mock_ser_entrada.validated_data = payload

        mock_ser_salida = MagicMock()
        mock_ser_salida.data = {'id': 1, 'nombre': 'Nuevo Nombre'}
        
        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]
        
        mock_usuario_upd = MagicMock()
        mock_service.return_value = mock_usuario_upd

        response = self.view(request)

        mock_serializer_class.assert_any_call(self.mock_user, data=payload, partial=True)
        mock_service.assert_called_once_with(usuario=self.mock_user, data_validada=payload)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_ser_salida.data)



    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_serializer_invalido_retorna_400_con_errores(self, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido → retorna 400 con errores
        
        Given: Un payload con datos que no pasan la validación (ej. email mal formado).
        When: is_valid() evalúa a False.
        Then: La vista retorna status 400 con los errores del serializador y NO llama al servicio.
        """
        request = self.factory.patch(self.path, {'email': 'formato_incorrecto'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = False
        mock_ser.errors = {'email': ['Introduzca un email válido.']}
        mock_serializer_class.return_value = mock_ser

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, mock_ser.errors)
        mock_service.assert_not_called()



    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_error_en_try_except_retorna_400(self, mock_serializer_class, mock_service):
        """
        Test: Error interno (servicio o serialización) → retorna 400
        
        Given: Un serializador válido con datos correctos.
        When: Ocurre una excepción dentro del bloque try (ej. fallo del servicio).
        Then: La vista captura la excepción y retorna status 400 con el detalle del error.
        """
        request = self.factory.patch(self.path, {'nombre': 'Test'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = {'nombre': 'Test'}
        mock_serializer_class.return_value = mock_ser

        mensaje_error = "Error de integridad en base de datos"
        mock_service.side_effect = Exception(mensaje_error)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], mensaje_error)



    def test_patch_usuario_no_autenticado_bloqueado(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición PATCH sin credenciales (sesión/token).
        When: Se intenta acceder al endpoint de actualización.
        Then: DRF bloquea el acceso en la capa de permisos (401/403).
        """
        request = self.factory.patch(self.path, {}, format='json')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])