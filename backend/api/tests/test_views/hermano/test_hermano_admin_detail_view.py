from unittest.mock import PropertyMock, call, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from api.vistas.hermano.hermano_admin_detail_view import HermanoAdminDetailView

User = get_user_model()


class TestHermanoAdminDetailViewGetUnitario(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = HermanoAdminDetailView.as_view()
        self.path = "/api/hermanos/1/gestion/"

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch('api.vistas.hermano.hermano_admin_detail_view.HermanoAdminUpdateSerializer')
    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_get_usuario_admin_obtiene_detalle_correctamente(self, mock_get_object, mock_serializer_class):
        """
        Test: Usuario admin → obtiene detalle correctamente
        
        Given: Una petición GET realizada por un usuario con esAdmin=True.
        When: El hermano existe en la base de datos.
        Then: Se recupera el objeto, se serializa y se retorna status 200 con los datos.
        """
        pk_test = 1
        request = self.factory.get(self.path)

        mock_admin = MagicMock()
        mock_admin.esAdmin = True

        force_authenticate(request, user=mock_admin)

        mock_hermano = MagicMock()
        mock_get_object.return_value = mock_hermano
        
        datos_esperados = {'id': pk_test, 'nombre': 'Test Admin'}
        mock_serializer_instancia = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instancia
        mock_serializer_instancia.data = datos_esperados

        response = self.view(request, pk=pk_test)

        mock_get_object.assert_called_once_with(User, pk=pk_test)
        mock_serializer_class.assert_called_once_with(mock_hermano)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_get_usuario_no_admin_retorna_403(self, mock_get_object):
        """
        Test: Usuario no admin → 403
        
        Given: Un usuario autenticado cuyo atributo 'esAdmin' es False.
        When: Se realiza una petición GET al detalle de gestión.
        Then: La vista retorna un status 403 con el mensaje "No autorizado" y no llega a llamar a get_object_or_404.
        """
        request = self.factory.get(self.path)

        mock_user = MagicMock()
        mock_user.esAdmin = False

        force_authenticate(request, user=mock_user)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.data['detail'], "No autorizado")

        mock_get_object.assert_not_called()



    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_get_error_en_get_object_or_404_propaga_404(self, mock_get_object):
        """
        Test: Error en get_object_or_404 → propagación (404)
        
        Given: Un usuario administrador.
        When: get_object_or_404 lanza una excepción Http404.
        Then: La excepción se propaga y DRF la convierte en una respuesta 404.
        """
        request = self.factory.get(self.path)
        mock_admin = MagicMock()
        mock_admin.esAdmin = True
        force_authenticate(request, user=mock_admin)
        
        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS PUT
    # ---------------------------------------------------------------------------

    @patch('api.vistas.hermano.hermano_admin_detail_view.update_hermano_por_admin_service')
    @patch('api.vistas.hermano.hermano_admin_detail_view.HermanoAdminUpdateSerializer')
    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_put_actualizacion_completa_correcta(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Actualización completa correcta
        
        Given: Un payload válido enviado por un administrador en una petición PUT.
        When: La vista procesa la actualización completa.
        Then: Se valida el payload, se invoca al servicio y se retorna status 200 con los nuevos datos.
        """
        pk_test = 1
        payload = {'nombre': 'Nombre Actualizado', 'email': 'nuevo@test.com'}
        request = self.factory.put(self.path, payload, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_hermano_original = MagicMock()
        mock_get_object.return_value = mock_hermano_original

        mock_serializer_validacion = MagicMock()
        mock_serializer_validacion.validated_data = {'nombre': 'Nombre Actualizado', 'email': 'nuevo@test.com'}

        mock_serializer_respuesta = MagicMock()
        mock_serializer_respuesta.data = {'id': pk_test, 'nombre': 'Nombre Actualizado', 'email': 'nuevo@test.com'}

        mock_serializer_class.side_effect = [mock_serializer_validacion, mock_serializer_respuesta]

        mock_hermano_actualizado = MagicMock()
        mock_service.return_value = mock_hermano_actualizado

        response = self.view(request, pk=pk_test)

        mock_get_object.assert_called_once_with(User, pk=pk_test)

        mock_serializer_class.assert_has_calls([
            call(mock_hermano_original, data=payload),
            call(mock_hermano_actualizado)
        ])

        mock_serializer_validacion.is_valid.assert_called_once_with(raise_exception=True)

        mock_service.assert_called_once_with(
            usuario_solicitante=request.user,
            hermano_id=pk_test,
            data_validada=mock_serializer_validacion.validated_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_serializer_respuesta.data)



    @patch('api.vistas.hermano.hermano_admin_detail_view.update_hermano_por_admin_service')
    @patch('api.vistas.hermano.hermano_admin_detail_view.HermanoAdminUpdateSerializer')
    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_put_usuario_sin_permisos_en_servicio_retorna_403(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Usuario sin permisos → servicio lanza PermissionDenied
        
        Given: Un administrador que intenta una acción no permitida por el servicio.
        When: update_hermano_por_admin_service lanza una excepción PermissionDenied.
        Then: La vista captura la excepción y retorna un status 403 con el mensaje de error.
        """
        request = self.factory.put(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_get_object.return_value = MagicMock()

        mock_serializer = MagicMock()
        mock_serializer_class.return_value = mock_serializer

        mensaje_error = "El administrador no tiene rango suficiente para esta acción."
        mock_service.side_effect = PermissionDenied(mensaje_error)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], mensaje_error)



    @patch('api.vistas.hermano.hermano_admin_detail_view.update_hermano_por_admin_service')
    @patch('api.vistas.hermano.hermano_admin_detail_view.HermanoAdminUpdateSerializer')
    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_put_serializer_invalido_lanza_excepcion(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido → lanza excepción
        
        Given: Datos de entrada que no cumplen con las reglas del serializador.
        When: Se llama a is_valid(raise_exception=True).
        Then: Se lanza una ValidationError de DRF y NO se llega a llamar al servicio de actualización.
        """
        request = self.factory.put(self.path, {'campo_invalido': 'error'}, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_get_object.return_value = MagicMock()

        mock_serializer = MagicMock()
        mock_serializer_class.return_value = mock_serializer

        mock_serializer.is_valid.side_effect = ValidationError({'email': ['Formato inválido']})

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        mock_service.assert_not_called()



    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_put_error_en_get_object_or_404_propaga_excepcion(self, mock_get_object):
        """
        Test: Error en get_object_or_404
        
        Given: Un usuario administrador intentando actualizar un PK que no existe.
        When: get_object_or_404 lanza una excepción Http404.
        Then: DRF captura la excepción y retorna una respuesta con status 404 Not Found.
        """
        request = self.factory.put(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_get_object.side_effect = Http404("No encontrado")

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_get_object.assert_called_once()



    # ---------------------------------------------------------------------------
    # TESTS PATCH
    # ---------------------------------------------------------------------------

    @patch('api.vistas.hermano.hermano_admin_detail_view.update_hermano_por_admin_service')
    @patch('api.vistas.hermano.hermano_admin_detail_view.HermanoAdminUpdateSerializer')
    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_patch_actualizacion_parcial_correcta(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Actualización parcial correcta
        
        Given: Un payload parcial (solo algunos campos) enviado en una petición PATCH.
        When: La vista procesa la petición.
        Then: El serializador se instancia con partial=True, se llama al servicio y se retorna status 200.
        """
        pk_test = 1
        payload_parcial = {'nombre': 'Nuevo Nombre'}
        request = self.factory.patch(self.path, payload_parcial, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_hermano_original = MagicMock()
        mock_get_object.return_value = mock_hermano_original

        mock_serializer_validacion = MagicMock()
        mock_serializer_validacion.validated_data = payload_parcial

        mock_serializer_respuesta = MagicMock()
        mock_serializer_respuesta.data = {'id': pk_test, 'nombre': 'Nuevo Nombre', 'email': 'existente@test.com'}

        mock_serializer_class.side_effect = [mock_serializer_validacion, mock_serializer_respuesta]

        mock_hermano_actualizado = MagicMock()
        mock_service.return_value = mock_hermano_actualizado

        response = self.view(request, pk=pk_test)

        mock_get_object.assert_called_once_with(User, pk=pk_test)
        mock_serializer_class.assert_any_call(mock_hermano_original, data=payload_parcial, partial=True)
        mock_serializer_validacion.is_valid.assert_called_once_with(raise_exception=True)
        
        mock_service.assert_called_once_with(
            usuario_solicitante=request.user,
            hermano_id=pk_test,
            data_validada=payload_parcial
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_serializer_respuesta.data)



    @patch('api.vistas.hermano.hermano_admin_detail_view.update_hermano_por_admin_service')
    @patch('api.vistas.hermano.hermano_admin_detail_view.HermanoAdminUpdateSerializer')
    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_patch_servicio_lanza_permission_denied_retorna_403(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Servicio lanza PermissionDenied → 403
        
        Given: Una petición PATCH válida a nivel de serializador.
        When: El servicio de negocio lanza PermissionDenied (ej. faltan permisos específicos).
        Then: La vista captura la excepción y retorna un status 403.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_get_object.return_value = MagicMock()
        mock_serializer_class.return_value = MagicMock()
        
        mensaje_error = "Permisos insuficientes en el servicio."
        mock_service.side_effect = PermissionDenied(mensaje_error)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], mensaje_error)



    @patch('api.vistas.hermano.hermano_admin_detail_view.HermanoAdminUpdateSerializer')
    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_patch_serializer_invalido_lanza_excepcion(self, mock_get_object, mock_serializer_class):
        """
        Test: Serializer inválido → excepción (400)
        
        Given: Datos parciales enviados que fallan la validación.
        When: is_valid(raise_exception=True) detecta errores.
        Then: Se propaga la ValidationError de DRF (Status 400).
        """
        request = self.factory.patch(self.path, {'email': 'invalido'}, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_get_object.return_value = MagicMock()
        
        mock_serializer = MagicMock()
        mock_serializer_class.return_value = mock_serializer
        mock_serializer.is_valid.side_effect = ValidationError({'email': ['Email incorrecto']})

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_patch_error_en_get_object_or_404_propaga_excepcion(self, mock_get_object):
        """
        Test: Error en get_object_or_404 → propagación (404)
        
        Given: Un PK que no corresponde a ningún usuario.
        When: Se invoca get_object_or_404.
        Then: La excepción Http404 se propaga y DRF la convierte en status 404.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_get_object.side_effect = Http404("No encontrado")

        response = self.view(request, pk=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS TRANSVERSALES
    # ---------------------------------------------------------------------------

    @patch('api.vistas.hermano.hermano_admin_detail_view.get_object_or_404')
    def test_usuario_no_autenticado_bloqueado_en_todos_los_metodos(self, mock_get_object):
        """
        Test: Usuario no autenticado
        
        Given: Una petición (GET, PUT, PATCH) sin credenciales de autenticación.
        When: Se intenta acceder a la vista.
        Then: DRF bloquea el acceso con 401 o 403 y no se ejecuta ninguna lógica (get_object_or_404 no se llama).
        """
        metodos = ['get', 'put', 'patch']
        
        for metodo in metodos:
            request = getattr(self.factory, metodo)("/api/hermanos/1/gestion/")

            response = self.view(request, pk=1)

            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
            mock_get_object.assert_not_called()