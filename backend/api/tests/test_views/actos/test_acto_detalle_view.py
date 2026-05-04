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

    @patch('api.vistas.acto.acto_detalle_view.Acto')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_get_recupera_acto_correctamente(self, mock_get_object, mock_serializer_class, mock_acto_model):
        """
        # Comentario requerido por [2026-03-04]
        Test: Recupera acto correctamente
        
        Given: Un usuario autenticado y un ID (pk) de un acto existente.
        When: Se realiza una petición GET a la vista de detalle de acto.
        Then: Se busca el acto con get_object_or_404, se serializa y retorna status 200 con serializer.data.
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.acto.acto_detalle_view.Acto')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_get_serializer_recibe_contexto_correcto(self, mock_get_object, mock_serializer_class, mock_acto_model):
        """
        Test: Serializer recibe contexto correcto
        
        Given: Una petición GET válida procesada por la vista.
        When: Se instancia el ActoSerializer para preparar la respuesta.
        Then: Se verifica estrictamente que el diccionario 'context' contenga la clave 'request' apuntando al objeto request actual.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_acto_instancia = MagicMock()
        mock_get_object.return_value = mock_acto_instancia
        mock_serializer_class.return_value = MagicMock()

        self.view(request, pk=self.pk_prueba)

        _, kwargs = mock_serializer_class.call_args
        
        self.assertIn('context', kwargs)
        self.assertIn('request', kwargs['context'])

        drf_request = kwargs['context']['request']

        self.assertEqual(drf_request._request, request)



    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_get_acto_no_encontrado_retorna_404(self, mock_get_object):
        """
        Test: Acto no encontrado → respuesta 404
        
        Given: Un identificador pk que no corresponde a ningún registro.
        When: Se invoca get_object_or_404 y lanza Http404.
        Then: DRF captura la excepción y retorna un status 404 NOT FOUND.
        """
        pk_invalido = 99
        path_invalido = f"/api/actos/{pk_invalido}/"
        
        request = self.factory.get(path_invalido)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_object.side_effect = Http404("No Acto matches the given query.")

        response = self.view(request, pk=pk_invalido)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_get_error_en_serializer_propaga_excepcion(self, mock_get_object, mock_serializer_class):
        """
        Test: Error en serializer → excepción
        
        Given: Un acto recuperado con éxito.
        When: El serializador lanza una excepción inesperada durante su inicialización.
        Then: La vista no captura el error y la excepción se propaga.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_object.return_value = MagicMock()
        mock_serializer_class.side_effect = Exception("Fallo interno del serializador")

        with self.assertRaises(Exception) as cm:
            self.view(request, pk=self.pk_prueba)
        
        self.assertEqual(str(cm.exception), "Fallo interno del serializador")



    def test_get_usuario_no_autenticado_bloqueado_401_403(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición GET sin credenciales de autenticación.
        When: Se intenta acceder al detalle del acto.
        Then: Las permission_classes de DRF bloquean el acceso con 401 o 403.
        """
        request = self.factory.get(self.path)

        response = self.view(request, pk=self.pk_prueba)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



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
    def test_put_uso_correcto_de_validated_data(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Uso correcto de validated_data
        
        Given: Un serializador que limpia los datos de entrada.
        When: El serializador es válido.
        Then: Se garantiza que al servicio se le pasan los datos provenientes de validated_data 
            y no el request.data crudo.
        """
        datos_crudos = {'titulo': 'Titulo Sucio ', 'extra': 'campo no permitido'}
        datos_limpios = {'titulo': 'Titulo Limpio'}
        request = self.factory.put(self.path, datos_crudos, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()
        
        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = datos_limpios
        mock_serializer_class.side_effect = [mock_ser, MagicMock()]

        self.view(request, pk=self.pk_prueba)

        mock_service.assert_called_once_with(
            usuario=self.mock_user, 
            acto_id=self.pk_prueba, 
            data_validada=datos_limpios
        )



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_put_respuesta_usa_serializer_de_salida_con_objeto_actualizado(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Serializer de respuesta usado correctamente
        
        Given: Un servicio que retorna un objeto 'acto_actualizado' tras procesar los cambios.
        When: La vista construye la respuesta final.
        Then: Se debe instanciar un nuevo ActoSerializer pasando el objeto actualizado 
            devuelto por el servicio para generar el .data de la respuesta.
        """
        request = self.factory.put(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_acto_original = MagicMock(name="ActoOriginal")
        mock_get_object.return_value = mock_acto_original

        mock_acto_actualizado = MagicMock(name="ActoActualizado")
        mock_service.return_value = mock_acto_actualizado

        mock_ser_entrada = MagicMock(name="SerializerEntrada")
        mock_ser_entrada.is_valid.return_value = True
        
        mock_ser_salida = MagicMock(name="SerializerSalida")
        mock_ser_salida.data = {"resultado": "datos_actualizados"}

        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]

        response = self.view(request, pk=self.pk_prueba)

        self.assertEqual(mock_serializer_class.call_count, 2)
        
        segunda_llamada = mock_serializer_class.call_args_list[1]
        args_salida, _ = segunda_llamada
        
        self.assertEqual(args_salida[0], mock_acto_actualizado)
        self.assertEqual(response.data, {"resultado": "datos_actualizados"})



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
    def test_put_error_en_get_object_or_404_propaga_excepcion(self, mock_get_object):
        """
        Test: Error en get_object_or_404
        
        Given: Un ID de acto inexistente.
        When: Se intenta realizar un PUT.
        Then: get_object_or_404 lanza Http404 y DRF retorna un 404 Not Found.
        """
        request = self.factory.put(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=self.pk_prueba)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_put_error_en_servicio_propaga_excepcion(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Error en servicio → excepción
        
        Given: Un serializador válido.
        When: El servicio update_acto_service lanza una excepción (ej. error de base de datos).
        Then: Como la vista no tiene un bloque try/except explícito, la excepción se propaga.
        """
        request = self.factory.put(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()
        
        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.return_value = mock_ser

        mock_service.side_effect = RuntimeError("Error inesperado en el servicio")

        with self.assertRaises(RuntimeError):
            self.view(request, pk=self.pk_prueba)



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_put_error_en_serializer_de_respuesta_falla(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Error en serializer de respuesta
        
        Given: El servicio actualiza el acto correctamente.
        When: El serializador de salida falla al procesar el objeto actualizado.
        Then: La excepción se propaga al final del flujo.
        """
        request = self.factory.put(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()
        mock_service.return_value = MagicMock()

        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True
        
        mock_serializer_class.side_effect = [mock_ser_entrada, Exception("Fallo en serialización de salida")]

        with self.assertRaises(Exception) as cm:
            self.view(request, pk=self.pk_prueba)
        
        self.assertEqual(str(cm.exception), "Fallo en serialización de salida")



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
    def test_patch_solo_campos_parciales_enviados(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Solo campos parciales enviados
        
        Given: Un payload que contiene solo un subconjunto de los campos del modelo.
        When: El serializador procesa la petición PATCH.
        Then: El validated_data pasado al servicio contiene exclusivamente los campos enviados,
            permitiendo la actualización parcial en la lógica de negocio.
        """
        payload_parcial = {'solo_un_campo': 'valor'}
        request = self.factory.patch(self.path, payload_parcial, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()
        
        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = payload_parcial

        mock_serializer_class.side_effect = [mock_ser, MagicMock()]

        self.view(request, pk=self.pk_prueba)

        args_servicio, kwargs_servicio = mock_service.call_args
        self.assertEqual(kwargs_servicio['data_validada'], payload_parcial)



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



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_patch_error_en_servicio_propaga_excepcion(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Error en servicio → excepción
        
        Given: Un serializador de entrada válido.
        When: El servicio update_acto_service falla (ej. error de permisos de negocio).
        Then: La excepción se propaga fuera de la vista.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()
        
        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.return_value = mock_ser

        mock_service.side_effect = RuntimeError("Error en la lógica de actualización")

        with self.assertRaises(RuntimeError):
            self.view(request, pk=self.pk_prueba)



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    def test_patch_error_en_serializer_de_respuesta_propaga_excepcion(self, mock_get_object, mock_serializer_class, mock_service):
        """
        Test: Error en serializer de respuesta
        
        Given: Una actualización exitosa por parte del servicio.
        When: El serializador encargado de la respuesta falla al acceder a .data.
        Then: La excepción se propaga.
        """
        request = self.factory.patch(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()
        mock_service.return_value = MagicMock()
        
        mock_ser_entrada = MagicMock()
        mock_ser_entrada.is_valid.return_value = True

        mock_serializer_class.side_effect = [mock_ser_entrada, Exception("Fallo de serialización final")]

        with self.assertRaises(Exception) as cm:
            self.view(request, pk=self.pk_prueba)
        
        self.assertEqual(str(cm.exception), "Fallo de serialización final")



    # ---------------------------------------------------------------------------
    # TESTS TRANSVERSALES
    # ---------------------------------------------------------------------------

    def test_transversal_usuario_no_autenticado_bloqueado_en_put_patch(self):
        """
        Test: Usuario no autenticado
        
        Given: Peticiones PUT y PATCH sin credenciales.
        When: Se intenta acceder al endpoint.
        Then: DRF bloquea el acceso (401/403) por las permission_classes.
        """
        for metodo in ['put', 'patch']:
            request = getattr(self.factory, metodo)(self.path, {}, format='json')

            response = self.view(request, pk=self.pk_prueba)
            
            self.assertIn(
                response.status_code, 
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
                msg=f"Fallo en método {metodo}"
            )



    @patch('api.vistas.acto.acto_detalle_view.Acto')
    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    def test_transversal_verificacion_uso_correcto_de_pk(self, mock_serializer_class, mock_get_object, mock_service, mock_acto_model):
        """
        Test: Verificación de uso correcto de pk
        
        Given: Un ID específico (pk) en la URL.
        When: Se ejecuta una actualización (PUT).
        Then: El pk se propaga correctamente tanto a get_object_or_404 para la búsqueda 
            como al servicio para la lógica de actualización.
        """
        pk_especifico = 555
        request = self.factory.put(f"/api/actos/{pk_especifico}/", {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.side_effect = [mock_ser, MagicMock()]

        self.view(request, pk=pk_especifico)

        mock_get_object.assert_called_once_with(mock_acto_model, pk=pk_especifico)

        mock_service.assert_called_once_with(
            usuario=self.mock_user,
            acto_id=pk_especifico,
            data_validada=ANY
        )



    @patch('api.vistas.acto.acto_detalle_view.update_acto_service')
    @patch('api.vistas.acto.acto_detalle_view.get_object_or_404')
    @patch('api.vistas.acto.acto_detalle_view.ActoSerializer')
    def test_transversal_verificacion_flujo_completo(self, mock_serializer_class, mock_get_object, mock_service):
        """
        Test: Verificación de flujo completo (PUT/PATCH)
        
        Given: Una petición de actualización válida.
        When: Se procesa en la vista.
        Then: Se respeta el orden lógico: 1. Obtener objeto, 2. Instanciar Serializer, 
            3. Validar, 4. Ejecutar Servicio, 5. Serializar Respuesta.
        """
        request = self.factory.put(self.path, {'data': 'test'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_acto_db = MagicMock(name="ActoDB")
        mock_acto_upd = MagicMock(name="ActoActualizado")
        mock_ser_entrada = MagicMock(name="SerEntrada")
        mock_ser_entrada.is_valid.return_value = True
        mock_ser_salida = MagicMock(name="SerSalida")
        mock_ser_salida.data = {}

        manager = MagicMock()
        manager.attach_mock(mock_get_object, 'get_obj')
        manager.attach_mock(mock_serializer_class, 'serializer_class')
        manager.attach_mock(mock_ser_entrada, 'ser_instancia')
        manager.attach_mock(mock_service, 'servicio')

        mock_get_object.return_value = mock_acto_db
        mock_serializer_class.side_effect = [mock_ser_entrada, mock_ser_salida]
        mock_service.return_value = mock_acto_upd

        self.view(request, pk=self.pk_prueba)

        expected_calls = [
            call.get_obj(ANY, pk=self.pk_prueba),
            call.serializer_class(mock_acto_db, data={'data': 'test'}),
            call.ser_instancia.is_valid(raise_exception=True),
            call.servicio(usuario=self.mock_user, acto_id=self.pk_prueba, data_validada=ANY),
            call.serializer_class(mock_acto_upd)
        ]
        manager.assert_has_calls(expected_calls, any_order=False)