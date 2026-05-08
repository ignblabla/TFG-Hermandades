from unittest.mock import ANY, call, patch, MagicMock
from django.http import Http404
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError

from api.vistas.acto.acto_detalle_view import ActoDetalleView


class TestActoDetalleViewGetPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ActoDetalleView.as_view()
        self.pk_prueba = 1
        self.path = f"/api/actos/{self.pk_prueba}/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_get_recupera_acto_correctamente_y_valida_contexto(self, mock_get_object, mock_serializer_class):
        """
        Test: Recupera acto correctamente y verifica contexto
        
        Given: Un usuario autenticado y un ID (pk) de un acto existente.
        When: Se realiza una petición GET a la vista de detalle de acto.
        Then: Se busca el acto, se instancia el serializador con el request en su 'context',
            y se retorna status 200 con los datos serializados.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_acto_instancia = MagicMock()
        mock_get_object.return_value = mock_acto_instancia

        mock_serializer_instancia = MagicMock()
        datos_esperados = {'id': self.pk_prueba, 'titulo': 'Acto de Prueba'}
        mock_serializer_instancia.data = datos_esperados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request, pk=self.pk_prueba)

        mock_get_object.assert_called_once_with(ANY, pk=self.pk_prueba)

        mock_serializer_class.assert_called_once_with(mock_acto_instancia, context={'request': ANY})
        drf_request_passed = mock_serializer_class.call_args[1]['context']['request']
        self.assertEqual(drf_request_passed._request, request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_get_acto_no_encontrado_retorna_404(self, mock_get_object):
        """
        Test: Acto no encontrado → respuesta 404
        
        Given: Un identificador pk que no corresponde a ningún registro.
        When: Se invoca get_object_or_404 y este lanza Http404.
        Then: DRF captura la excepción y retorna un status 404 NOT FOUND.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_object.side_effect = Http404("No Acto matches the given query.")

        response = self.view(request, pk=self.pk_prueba)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS PUT
    # ---------------------------------------------------------------------------

    @patch('api.vistas.acto.acto_detalle_view.Acto')
    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_put_actualizacion_completa_correcta(self, mock_get_object, mock_serializer_class, mock_service, mock_acto_model):
        """
        Test: Actualización completa correcta
        
        Given: Un usuario autenticado y un payload con datos para actualizar un acto.
        When: Se realiza una petición PUT.
        Then: Se valida la existencia del acto, se valida el serializador, 
            se invoca el servicio y se retorna status 200 con los datos nuevos.
        """
        payload = {'titulo': 'Acto Actualizado', 'descripcion': 'Nueva descripción'}
        request = self.factory.put(self.path, payload, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_acto_instancia = MagicMock()
        mock_get_object.return_value = mock_acto_instancia

        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True
        mock_ser_entrada.validated_data = payload
        
        mock_ser_salida = MagicMock()
        mock_ser_salida.data = {**payload, 'id': self.pk_prueba}
        
        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]

        mock_acto_actualizado = MagicMock()
        mock_service.return_value = mock_acto_actualizado

        response = self.view(request, pk=self.pk_prueba)

        mock_get_object.assert_called_once_with(mock_acto_model, pk=self.pk_prueba)
        mock_serializer_class.assert_any_call(mock_acto_instancia, data=payload)
        mock_ser_entrada.is_valid.assert_called_once_with(raise_exception=True)

        mock_service.assert_called_once_with(
            usuario=self.mock_user, 
            acto_id=self.pk_prueba, 
            data_validada=payload
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_ser_salida.data)



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_put_serializer_invalido_no_llama_servicio(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido → excepción
        
        Given: Un payload con datos incorrectos.
        When: is_valid(raise_exception=True) detecta errores.
        Then: DRF captura la ValidationError, retorna 400 y NO se llega a llamar al servicio.
        """
        request = self.factory.put(self.path, {'titulo': ''}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()

        mock_ser = MagicMock()
        mock_ser.is_valid.side_effect = ValidationError({'titulo': 'Este campo es requerido'})
        mock_serializer_class.return_value = mock_ser

        response = self.view(request, pk=self.pk_prueba)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_service.assert_not_called()



    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_put_error_en_get_object_or_404_propaga_404(self, mock_get_object):
        """
        # Comentario requerido por [2026-03-04]
        Test: Error en get_object_or_404 → 404 Not Found
        
        Given: Un ID de acto inexistente.
        When: get_object_or_404 lanza Http404.
        Then: DRF captura la excepción y retorna un 404 Not Found.
        """
        request = self.factory.put(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=self.pk_prueba)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS PATCH
    # ---------------------------------------------------------------------------

    @patch('api.vistas.acto.acto_detalle_view.Acto')
    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_patch_actualizacion_parcial_correcta(self, mock_get_object, mock_serializer_class, mock_service, mock_acto_model):
        """
        Test: Actualización parcial correcta
        
        Given: Un usuario autenticado y un ID de acto existente.
        When: Se realiza una petición PATCH con datos parciales.
        Then: El serializador se instancia con partial=True, el servicio se invoca correctamente 
            y se retorna status 200.
        """
        payload = {'titulo': 'Nuevo Titulo Parcial'}
        request = self.factory.patch(self.path, payload, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_acto_instancia = MagicMock()
        mock_get_object.return_value = mock_acto_instancia

        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True
        mock_ser_entrada.validated_data = payload

        mock_ser_salida = MagicMock()
        mock_ser_salida.data = {**payload, 'descripcion': 'Descripción previa'}
        
        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]
        mock_service.return_value = MagicMock()

        response = self.view(request, pk=self.pk_prueba)

        mock_serializer_class.assert_any_call(mock_acto_instancia, data=payload, partial=True)

        mock_service.assert_called_once_with(
            usuario=self.mock_user,
            acto_id=self.pk_prueba,
            data_validada=payload
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_ser_salida.data)



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_patch_serializer_invalido_no_llama_servicio(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido → respuesta 400
        
        Given: Un payload con datos parciales inválidos.
        When: is_valid(raise_exception=True) detecta el error.
        Then: DRF captura la ValidationError, retorna 400 y el servicio NO es invocado.
        """
        request = self.factory.patch(self.path, {'campo_invalido': 'error'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()
        
        mock_ser = MagicMock()
        mock_ser.is_valid.side_effect = ValidationError({'error': 'dato no válido'})
        mock_serializer_class.return_value = mock_ser

        response = self.view(request, pk=self.pk_prueba)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_service.assert_not_called()



    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_patch_error_en_get_object_or_404_retorna_404(self, mock_get_object):
        """
        Test: Error en get_object_or_404
        
        Given: Un ID de acto que no existe.
        When: Se intenta realizar un PATCH.
        Then: get_object_or_404 lanza Http404 y DRF retorna status 404.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=self.pk_prueba)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS TRANSVERSALES
    # ---------------------------------------------------------------------------

    def test_transversal_usuario_no_autenticado_bloqueado_en_todos_los_metodos(self):
        """
        Test: Usuario no autenticado bloqueado transversalmente
        
        Given: Peticiones HTTP sin credenciales de autenticación.
        When: Se intenta acceder al detalle del acto mediante GET, PUT o PATCH.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso con 401/403.
        """
        metodos = ['get', 'put', 'patch']
        
        for metodo in metodos:
            with self.subTest(metodo=metodo):
                request_method = getattr(self.factory, metodo)
                request = request_method(self.path, {}, format='json')

                response = self.view(request, pk=self.pk_prueba)

                self.assertIn(
                    response.status_code, 
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
                    msg=f"La seguridad falló para el método {metodo.upper()}"
                )