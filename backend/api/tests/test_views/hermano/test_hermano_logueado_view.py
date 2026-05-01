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



    @patch('api.vistas.hermano.hermano_logueado_view.UserSerializer')
    def test_get_error_en_serializer_propaga_excepcion(self, mock_serializer_class):
        """
        Test: Error en serializer → excepción no controlada
        
        Given: Un usuario autenticado.
        When: El UserSerializer lanza una excepción inesperada durante la instanciación.
        Then: La vista no captura el error y la excepción se propaga.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_serializer_class.side_effect = Exception("Fallo crítico de mapeo")

        with self.assertRaises(Exception) as cm:
            self.view(request)
        
        self.assertEqual(str(cm.exception), "Fallo crítico de mapeo")



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
        Then: El serializer se instancia con partial=True, es válido, se llama al servicio y retorna 200.
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
    def test_patch_serializer_valido_uso_correcto_de_validated_data(self, mock_serializer_class, mock_service):
        """
        Test: Serializer válido → uso correcto de validated_data
        
        Given: Un payload con datos válidos.
        When: El serializer procesa la información.
        Then: Los datos limpios (validated_data) se pasan íntegramente al servicio de actualización.
        """
        request = self.factory.patch(self.path, {'email': 'nuevo@test.com'}, format='json')
        force_authenticate(request, user=self.mock_user)

        datos_validados = {'email': 'nuevo@test.com'}
        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = datos_validados
        mock_serializer_class.return_value = mock_ser

        self.view(request)

        mock_service.assert_called_once_with(usuario=self.mock_user, data_validada=datos_validados)



    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_respuesta_usa_serializer_de_salida(self, mock_serializer_class, mock_service):
        """
        Test: Respuesta usa serializer de salida
        
        Given: Una actualización exitosa en el servicio.
        When: Se genera la respuesta.
        Then: Se instancia un nuevo serializer con el objeto devuelto por el servicio y se usa su atributo .data.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_usuario_actualizado = MagicMock()
        mock_service.return_value = mock_usuario_actualizado

        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True
        
        mock_ser_salida = MagicMock()
        mock_ser_salida.data = {"status": "success"}
        
        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]

        response = self.view(request)

        mock_serializer_class.assert_has_calls([
            call(self.mock_user, data={}, partial=True),
            call(mock_usuario_actualizado)
        ])
        self.assertEqual(response.data, mock_ser_salida.data)



    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_serializer_invalido_retorna_400_con_errores(self, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido → retorna 400 con errores
        
        Given: Un payload con datos que no pasan la validación (ej. email mal formado).
        When: is_valid() devuelve False.
        Then: La vista retorna un status 400, incluye los errores del serializador y NO llama al servicio.
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
    def test_patch_error_en_servicio_retorna_400(self, mock_serializer_class, mock_service):
        """
        Test: Error en servicio → retorna 400
        
        Given: Un serializador válido.
        When: El servicio update_mi_perfil_service lanza una excepción (ej. error de integridad).
        Then: La vista captura la excepción en el bloque try-except y retorna status 400 con el detalle del error.
        """
        request = self.factory.patch(self.path, {'nombre': 'Test'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = {'nombre': 'Test'}
        mock_serializer_class.return_value = mock_ser

        mock_service.side_effect = Exception("El nombre ya está en uso")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "El nombre ya está en uso")



    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_error_en_serializer_entrada_propaga_excepcion(self, mock_serializer_class):
        """
        Test: Error en serializer de entrada (is_valid lanza excepción)
        
        Given: Una petición PATCH.
        When: El método is_valid() del serializador lanza una excepción no controlada.
        Then: La vista no tiene un try-except externo que cubra is_valid, por lo que la excepción se propaga.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.side_effect = RuntimeError("Fallo interno del motor de validación")
        mock_serializer_class.return_value = mock_ser

        with self.assertRaises(RuntimeError) as cm:
            self.view(request)
        
        self.assertEqual(str(cm.exception), "Fallo interno del motor de validación")



    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_error_en_serializer_de_salida_capturado_por_view(self, mock_serializer_class, mock_service):
        """
        Test: Error en serializer de salida
        
        Given: Un servicio que actualiza el perfil correctamente.
        When: La segunda instancia del serializador (respuesta) falla al acceder a .data.
        Then: La vista captura la excepción en su bloque try-except y retorna status 400.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True

        mock_ser_salida = MagicMock()
        type(mock_ser_salida).data = PropertyMock(side_effect=Exception("Error serializando usuario actualizado"))
        
        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]
        mock_service.return_value = MagicMock()

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Error serializando usuario actualizado")



    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_patch_validated_data_vacio_llama_servicio(self, mock_serializer_class, mock_service):
        """
        Test: validated_data vacío
        
        Given: Una petición PATCH con un body vacío o datos que no afectan al modelo.
        When: El serializador es válido pero su validated_data es un diccionario vacío {}.
        Then: Se llama al servicio con el diccionario vacío y se retorna status 200.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = {}
        mock_serializer_class.side_effect = [mock_ser, MagicMock()]

        response = self.view(request)

        mock_service.assert_called_once_with(usuario=self.mock_user, data_validada={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    def test_patch_usuario_no_autenticado_bloqueado(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición PATCH sin autenticación.
        When: Se intenta acceder al endpoint.
        Then: DRF bloquea el acceso antes de ejecutar el método de la vista (401/403).
        """
        request = self.factory.patch(self.path, {}, format='json')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    # ---------------------------------------------------------------------------
    # TESTS TRANSVERSALES
    # ---------------------------------------------------------------------------

    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_verificacion_flujo_correcto_patch(self, mock_serializer_class, mock_service):
        """
        Test: Verificación de flujo correcto en PATCH
        
        Given: Un usuario autenticado enviando una petición válida.
        When: Se ejecuta el método PATCH de la vista.
        Then: El orden de operaciones es: 1. Instanciar serializer entrada, 2. Validar, 
            3. Llamar servicio, 4. Instanciar serializer salida, 5. Retornar respuesta.
        """
        payload = {'nombre': 'Test'}
        request = self.factory.patch(self.path, payload, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True
        mock_ser_entrada.validated_data = payload
        
        mock_ser_salida = MagicMock()
        mock_ser_salida.data = payload

        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]
        
        mock_usuario_upd = MagicMock()
        mock_service.return_value = mock_usuario_upd

        manager = MagicMock()
        manager.attach_mock(mock_serializer_class, 'serializer_class')
        manager.attach_mock(mock_service, 'servicio')
        manager.attach_mock(mock_ser_entrada, 'serializer_instancia')

        self.view(request)

        expected_calls = [
            call.serializer_class(self.mock_user, data=payload, partial=True),
            call.serializer_instancia.is_valid(),
            call.servicio(usuario=self.mock_user, data_validada=payload),
            call.serializer_class(mock_usuario_upd)
        ]
        
        manager.assert_has_calls(expected_calls, any_order=False)



    @patch('api.vistas.hermano.hermano_logueado_view.update_mi_perfil_service')
    @patch('api.vistas.hermano.hermano_logueado_view.UserUpdateSerializer')
    def test_verificacion_uso_de_request_user(self, mock_serializer_class, mock_service):
        """
        Test: Verificación de uso de request.user
        
        Given: Una instancia de usuario en la request.
        When: Se procesa la actualización.
        Then: Se garantiza que es EXACTAMENTE ese objeto usuario el que se pasa al serializer y al servicio.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.side_effect = [mock_ser, MagicMock()]

        self.view(request)

        args_ser, kwargs_ser = mock_serializer_class.call_args_list[0]
        self.assertEqual(args_ser[0], self.mock_user)

        _, kwargs_serv = mock_service.call_args
        self.assertEqual(kwargs_serv['usuario'], self.mock_user)