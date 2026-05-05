import unittest
from unittest.mock import patch, MagicMock
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.exceptions import ValidationError

from django.contrib.auth.models import AnonymousUser
from django.http import Http404

from api.vistas.puesto.puesto_detalle_view import PuestoDetalleView


@pytest.mark.django_db
class TestPuestoDetalleViewPermisos(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.pk = 1
        self.url = f'/puestos/{self.pk}/'
        
        self.user = MagicMock()
        self.user.is_authenticated = True 

        self.vista_callable = PuestoDetalleView.as_view()
        self.data_update = {"nombre": "Costalero Editado"}



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_usuario_autenticado_acceso_permitido(self, mock_get_404, mock_serializer_class):
        """
        Test: Usuario autenticado -> acceso permitido
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_puesto = MagicMock()
        mock_get_404.return_value = mock_puesto
        mock_serializer_class.return_value.data = {"id": self.pk, "nombre": "Puesto Prueba"}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    def test_usuario_no_autenticado_acceso_denegado(self):
        """
        Test: Usuario no autenticado -> acceso denegado
        """
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        response = self.vista_callable(request, pk=self.pk)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_get_devuelve_puesto_correctamente_200(self, mock_get_404, mock_serializer_class):
        """
        Test: Devuelve puesto correctamente (200)
        
        Given: Un identificador (pk) de un puesto que existe en la base de datos.
        When: Se realiza una petición GET a la vista de detalle.
        Then: Se retorna una respuesta con los datos serializados y un código de estado 200 OK.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        puesto_mock = MagicMock()
        mock_get_404.return_value = puesto_mock
        
        mock_serializer_instancia = mock_serializer_class.return_value
        mock_serializer_instancia.data = {"id": self.pk, "nombre": "Puesto de Prueba"}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"id": self.pk, "nombre": "Puesto de Prueba"})



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_serializa_correctamente_el_objeto_puesto(self, mock_get_404, mock_serializer_class):
        """
        Test: Serializa correctamente el objeto puesto
        
        Given: Un objeto de modelo Puesto obtenido mediante el atajo get_object_or_404.
        When: La vista procede a preparar la respuesta.
        Then: Se verifica que el PuestoSerializer es instanciado pasando exactamente el objeto recuperado.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        puesto_db_mock = MagicMock()
        mock_get_404.return_value = puesto_db_mock

        self.vista_callable(request, pk=self.pk)

        mock_serializer_class.assert_called_once_with(puesto_db_mock)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    @patch('api.vistas.puesto.puesto_detalle_view.Puesto')
    def test_usa_correctamente_pk_en_la_consulta(self, mock_puesto_model, mock_get_404, mock_serializer_class):
        """
        Test: Usa correctamente pk en la consulta
        
        Given: Un valor de pk recibido por la URL.
        When: Se invoca al método GET.
        Then: Se llama a get_object_or_404 utilizando el modelo Puesto y el pk correspondiente como filtro.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        self.vista_callable(request, pk=self.pk)

        mock_get_404.assert_called_once_with(mock_puesto_model, pk=self.pk)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_get_devuelve_status_200(self, mock_get_404, mock_serializer_class):
        """
        Test: Devuelve status 200
        
        Given: Un flujo de consulta de detalle exitoso.
        When: La vista procesa la petición GET y genera la respuesta.
        Then: Se verifica que el objeto Response resultante contiene el código de estado HTTP 200 OK.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_get_404.return_value = MagicMock()
        mock_serializer_class.return_value.data = {"id": self.pk}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_puesto_no_existe_lanza_404(self, mock_get_404):
        """
        Test: Puesto no existe
        
        Given: Un ID de puesto (pk) que no se encuentra en la base de datos.
        When: Se invoca al atajo get_object_or_404.
        Then: DRF captura la excepción Http404 y devuelve una respuesta con status 404.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_get_404.side_effect = Http404("No Puesto matches the given query.")

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_error_en_serializer_lanza_excepcion(self, mock_get_404, mock_serializer_class):
        """
        Test: Error en serializer
        
        Given: Un objeto puesto recuperado con éxito.
        When: Ocurre un fallo inesperado durante la fase de serialización de los datos.
        Then: La excepción se propaga correctamente sin ser capturada por la lógica de la vista.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_get_404.return_value = MagicMock()

        mock_serializer_class.side_effect = Exception("Fallo crítico en serialización")

        with self.assertRaises(Exception) as context:
            self.vista_callable(request, pk=self.pk)
            
        self.assertEqual(str(context.exception), "Fallo crítico en serialización")



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_serializer_devuelve_data_vacia(self, mock_get_404, mock_serializer_class):
        """
        Test: Serializer devuelve data vacía
        
        Given: Un puesto existente cuya representación serializada resulta ser un diccionario vacío.
        When: La vista construye la respuesta.
        Then: Se retorna un status 200 OK y el cuerpo de la respuesta es un diccionario vacío {}.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()

        mock_serializer_class.return_value.data = {}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_verificar_que_no_se_llama_serializer_si_falla_get_object_or_404(self, mock_get_404, mock_serializer_class):
        """
        Test: Verificar que no se llama serializer si falla get_object_or_404
        
        Given: Una petición para un puesto que no existe.
        When: El atajo get_object_or_404 lanza una excepción Http404.
        Then: El flujo se interrumpe inmediatamente y nunca se llega a instanciar la clase PuestoSerializer.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        mock_get_404.side_effect = Http404()

        self.vista_callable(request, pk=self.pk)

        mock_serializer_class.assert_not_called()



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_verificar_que_se_construye_response_con_serializer_data(self, mock_get_404, mock_serializer_class):
        """
        Test: Verificar que se construye Response con serializer.data
        
        Given: Un diccionario de datos específicos generado por el serializador.
        When: La vista finaliza el método GET.
        Then: La respuesta devuelta por la vista debe contener exactamente los mismos datos que el atributo .data del serializador.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        datos_esperados = {"campo1": "valor1", "campo2": 123}
        mock_serializer_class.return_value.data = datos_esperados

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.data, datos_esperados)



    # ---------------------------------------------------------------------------
    # TESTS PUT
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_actualiza_puesto_correctamente_200(self, mock_get_404, mock_upd_serializer_class, mock_service, mock_serializer_class):
        """
        Test: Actualiza puesto correctamente (200)
        
        Given: Un ID de puesto existente y datos válidos en el cuerpo de la petición.
        When: Se ejecuta el método PUT.
        Then: Se valida la entrada, se procesa la actualización mediante el servicio y se devuelve el objeto final serializado con status 200 OK.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)

        puesto_inicial = MagicMock()
        mock_get_404.return_value = puesto_inicial

        mock_upd_ser = mock_upd_serializer_class.return_value
        mock_upd_ser.is_valid.return_value = True
        mock_upd_ser.validated_data = self.data_update

        puesto_final = MagicMock()
        mock_service.return_value = puesto_final
        mock_serializer_class.return_value.data = {"id": self.pk, "nombre": "Costalero Editado"}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Costalero Editado")

        mock_upd_serializer_class.assert_called_once_with(puesto_inicial, data=self.data_update)
        mock_serializer_class.assert_called_once_with(puesto_final)



    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_llama_al_servicio_con_parametros_correctos(self, mock_get_404, mock_upd_serializer_class, mock_service):
        """
        Test: Llama al servicio con parámetros correctos
        
        Given: Una petición PUT con un usuario autenticado y datos validados.
        When: La vista invoca a update_puesto_service.
        Then: Se verifica que el servicio recibe exactamente el usuario de la request, el pk de la URL y el diccionario de datos validados.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser = mock_upd_serializer_class.return_value
        mock_upd_ser.validated_data = self.data_update

        self.vista_callable(request, pk=self.pk)

        mock_service.assert_called_once_with(
            usuario=self.user,
            puesto_id=self.pk,
            data_validada=self.data_update
        )



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_serializer_entrada_se_llama_con_data_request_data(self, mock_get_404, mock_upd_serializer_class):
        """
        Test: Serializer de entrada se llama con data=request.data
        
        Given: Una petición PUT con un cuerpo JSON específico.
        When: La vista instancia el PuestoUpdateSerializer para validar la entrada.
        Then: Se verifica que el serializador recibe el objeto recuperado de la BD y el diccionario 'data' extraído directamente de la petición.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)
        
        puesto_mock = MagicMock()
        mock_get_404.return_value = puesto_mock

        self.vista_callable(request, pk=self.pk)

        mock_upd_serializer_class.assert_called_once_with(
            puesto_mock, 
            data=self.data_update
        )



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_devuelve_datos_serializados_del_objeto_actualizado(self, mock_get_404, mock_upd_ser, mock_service, mock_serializer_class):
        """
        Test: Devuelve datos serializados del objeto actualizado
        
        Given: Un objeto devuelto por el servicio tras una actualización exitosa.
        When: La vista genera la respuesta final.
        Then: Se comprueba que los datos en el cuerpo de la respuesta coinciden exactamente con el atributo .data del PuestoSerializer (salida).
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()

        puesto_actualizado = MagicMock()
        mock_service.return_value = puesto_actualizado

        datos_finales = {"id": 1, "nombre": "Nombre Final", "extra": "data"}
        mock_serializer_class.return_value.data = datos_finales

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.data, datos_finales)
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_serializer_invalido_devuelve_400(self, mock_get_404, mock_upd_serializer_class):
        """
        Test: Serializer inválido
        
        Given: Datos de entrada que no cumplen con las reglas de validación.
        When: Se llama a serializer.is_valid(raise_exception=True).
        Then: DRF captura la excepción ValidationError y devuelve una respuesta 400 Bad Request.
        """
        request = self.factory.put(self.url, data={"nombre": ""}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()

        mock_upd_ser = mock_upd_serializer_class.return_value
        mock_upd_ser.is_valid.side_effect = ValidationError({"nombre": "Este campo es requerido."})

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("nombre", response.data)



    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_error_en_update_puesto_service_lanza_excepcion(self, mock_get_404, mock_upd_ser, mock_service):
        """
        Test: Error en update_puesto_service
        
        Given: Una petición válida que supera la serialización.
        When: El servicio de actualización encuentra un error de negocio o de base de datos.
        Then: La excepción lanzada por el servicio se propaga hacia arriba sin ser interceptada por la vista.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser.return_value.is_valid.return_value = True

        mock_service.side_effect = Exception("Error de consistencia en el servicio")

        with self.assertRaises(Exception) as context:
            self.vista_callable(request, pk=self.pk)
            
        self.assertEqual(str(context.exception), "Error de consistencia en el servicio")



    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_puesto_no_existe_en_put_devuelve_404(self, mock_get_404):
        """
        Test: Puesto no existe (PUT)
        
        Given: Un intento de actualización sobre un recurso inexistente.
        When: get_object_or_404 no encuentra el puesto.
        Then: DRF maneja la excepción Http404 y devuelve una respuesta con código de estado 404.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)

        mock_get_404.side_effect = Http404()

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_validated_data_vacio(self, mock_get_404, mock_upd_ser_class, mock_service, mock_serializer_class):
        """
        Test: validated_data vacío
        
        Given: Una petición PUT donde el serializador valida con éxito pero no devuelve campos (diccionario vacío).
        When: Se invoca al servicio de actualización.
        Then: La vista debe pasar ese diccionario vacío al servicio y devolver un status 200 OK.
        """
        request = self.factory.put(self.url, data={}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        
        mock_upd_ser = mock_upd_ser_class.return_value
        mock_upd_ser.is_valid.return_value = True
        mock_upd_ser.validated_data = {}
        
        mock_service.return_value = MagicMock()
        mock_serializer_class.return_value.data = {"detalle": "actualizado"}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once_with(
            usuario=self.user,
            puesto_id=self.pk,
            data_validada={}
        )



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_verificar_que_is_valid_se_llama_con_raise_exception_true(self, mock_get_404, mock_upd_ser_class):
        """
        Test: Verificar que is_valid se llama con raise_exception=True
        
        Given: Una petición PUT con datos para validar.
        When: La vista ejecuta la validación del serializador.
        Then: Se verifica que se utiliza el parámetro raise_exception=True para delegar el manejo de errores a DRF.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser = mock_upd_ser_class.return_value

        self.vista_callable(request, pk=self.pk)

        mock_upd_ser.is_valid.assert_called_once_with(raise_exception=True)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_verificar_status_200_en_respuesta(self, mock_get_404, mock_upd_ser, mock_service, mock_serializer_class):
        """
        Test: Verificar status 200 en respuesta
        
        Given: Un flujo de actualización completo y exitoso.
        When: La vista genera la Response final.
        Then: El código de estado HTTP de la respuesta debe ser exactamente 200 OK.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()

        mock_upd_ser.return_value.is_valid.return_value = True
        mock_upd_ser.return_value.validated_data = self.data_update
        
        mock_service.return_value = MagicMock()
        mock_serializer_class.return_value.data = {"id": self.pk}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    # ---------------------------------------------------------------------------
    # TESTS PATCH
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_actualiza_parcialmente_correctamente_200(self, mock_get_404, mock_upd_ser_class, mock_service, mock_serializer_class):
        """
        Test: Actualiza parcialmente correctamente (200)
        
        Given: Un ID de puesto existente y un subconjunto de datos para actualizar.
        When: Se procesa la petición PATCH.
        Then: El serializador se instancia con partial=True, se ejecuta el servicio y se devuelve un 200 OK.
        """
        data_parcial = {"nombre": "Nuevo Nombre Parcial"}
        request = self.factory.patch(self.url, data=data_parcial, format='json')
        force_authenticate(request, user=self.user)
        
        puesto_mock = MagicMock()
        mock_get_404.return_value = puesto_mock

        mock_upd_ser = mock_upd_ser_class.return_value
        mock_upd_ser.is_valid.return_value = True
        mock_upd_ser.validated_data = data_parcial

        puesto_actualizado = MagicMock()
        mock_service.return_value = puesto_actualizado
        mock_serializer_class.return_value.data = {"id": self.pk, **data_parcial}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_upd_ser_class.assert_called_once_with(puesto_mock, data=data_parcial, partial=True)
        self.assertEqual(response.data["nombre"], "Nuevo Nombre Parcial")



    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_llama_al_servicio_con_parametros_correctos(self, mock_get_404, mock_upd_ser_class, mock_service):
        """
        Test: Llama al servicio con parámetros correctos
        
        Given: Una petición PATCH con datos validados.
        When: La vista invoca al servicio de actualización.
        Then: Se verifica que se pasan el usuario de la request, el pk de la URL y los datos validados del serializador.
        """
        data_parcial = {"nombre": "Solo Nombre"}
        request = self.factory.patch(self.url, data=data_parcial, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser = mock_upd_ser_class.return_value
        mock_upd_ser.validated_data = data_parcial

        self.vista_callable(request, pk=self.pk)

        mock_service.assert_called_once_with(
            usuario=self.user,
            puesto_id=self.pk,
            data_validada=data_parcial
        )



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_serializer_se_instancia_con_partial_true(self, mock_get_404, mock_upd_ser_class):
        """
        Test: Serializer se instancia con partial=True
        
        Given: Una petición de tipo PATCH con datos parciales.
        When: La vista prepara la validación de los datos recibidos.
        Then: Se verifica que el PuestoUpdateSerializer se instancia explícitamente con el argumento partial=True.
        """
        data_parcial = {"nombre": "Nombre Editado"}
        request = self.factory.patch(self.url, data=data_parcial, format='json')
        force_authenticate(request, user=self.user)
        
        puesto_mock = MagicMock()
        mock_get_404.return_value = puesto_mock

        self.vista_callable(request, pk=self.pk)

        mock_upd_ser_class.assert_called_once_with(
            puesto_mock, 
            data=data_parcial, 
            partial=True
        )



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_devuelve_datos_serializados_del_objeto_actualizado(self, mock_get_404, mock_upd_ser, mock_service, mock_serializer_class):
        """
        Test: Devuelve datos serializados del objeto actualizado
        
        Given: Un proceso de actualización parcial exitoso.
        When: El servicio devuelve el objeto modificado y la vista genera la respuesta.
        Then: La respuesta debe contener los datos devueltos por el PuestoSerializer (salida) con un status 200 OK.
        """
        request = self.factory.patch(self.url, data={"nombre": "Cambio"}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser.return_value.is_valid.return_value = True

        puesto_modificado = MagicMock()
        mock_service.return_value = puesto_modificado

        mock_serializer_class.return_value.data = {"id": self.pk, "nombre": "Cambio", "otros": "datos"}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"id": self.pk, "nombre": "Cambio", "otros": "datos"})



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_serializer_invalido_devuelve_400(self, mock_get_404, mock_upd_ser_class):
        """
        Test: Serializer inválido
        
        Given: Datos parciales que no cumplen con las reglas de validación del serializador.
        When: Se llama a serializer.is_valid(raise_exception=True).
        Then: DRF captura la excepción ValidationError y retorna una respuesta con status 400 Bad Request.
        """
        request = self.factory.patch(self.url, data={"nombre": ""}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()

        mock_upd_ser = mock_upd_ser_class.return_value
        mock_upd_ser.is_valid.side_effect = ValidationError({"nombre": "Error de validación parcial"})

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_error_en_update_puesto_service_lanza_excepcion(self, mock_get_404, mock_upd_ser, mock_service):
        """
        Test: Error en update_puesto_service
        
        Given: Una petición PATCH válida.
        When: El servicio de actualización lanza una excepción inesperada.
        Then: La excepción se propaga fuera de la vista para ser manejada por el sistema de logs o excepciones globales.
        """
        request = self.factory.patch(self.url, data={"nombre": "Nuevo"}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser.return_value.is_valid.return_value = True

        mock_service.side_effect = Exception("Fallo en la lógica de actualización parcial")

        with self.assertRaises(Exception) as context:
            self.vista_callable(request, pk=self.pk)
            
        self.assertEqual(str(context.exception), "Fallo en la lógica de actualización parcial")



    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_puesto_no_existe_devuelve_404(self, mock_get_404):
        """
        Test: Puesto no existe
        
        Given: Un intento de PATCH sobre un puesto que no se encuentra.
        When: get_object_or_404 falla al buscar el registro.
        Then: DRF captura el Http404 y devuelve una respuesta con status 404 Not Found.
        """
        request = self.factory.patch(self.url, data={"nombre": "Nuevo"}, format='json')
        force_authenticate(request, user=self.user)

        mock_get_404.side_effect = Http404()

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_validated_data_vacio_update_parcial_sin_cambios(self, mock_get_404, mock_upd_ser_class, mock_service, mock_serializer_class):
        """
        Test: validated_data vacío (update parcial sin cambios)
        
        Given: Una petición PATCH con un cuerpo vacío o datos que no generan cambios validados.
        When: El serializador devuelve un diccionario validated_data vacío.
        Then: La vista llama al servicio con ese diccionario vacío y retorna un status 200 OK.
        """
        request = self.factory.patch(self.url, data={}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()

        mock_upd_ser = mock_upd_ser_class.return_value
        mock_upd_ser.is_valid.return_value = True
        mock_upd_ser.validated_data = {}
        
        mock_service.return_value = MagicMock()
        mock_serializer_class.return_value.data = {"id": self.pk, "info": "sin cambios"}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once_with(
            usuario=self.user,
            puesto_id=self.pk,
            data_validada={}
        )



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_verificar_que_is_valid_usa_raise_exception_true(self, mock_get_404, mock_upd_ser_class):
        """
        Test: Verificar que is_valid usa raise_exception=True
        
        Given: Una petición PATCH estándar.
        When: La vista ejecuta la validación del serializador de actualización.
        Then: Se comprueba que se llama a is_valid con raise_exception=True para delegar la gestión del error a DRF.
        """
        request = self.factory.patch(self.url, data={"nombre": "Prueba"}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser = mock_upd_ser_class.return_value

        self.vista_callable(request, pk=self.pk)

        mock_upd_ser.is_valid.assert_called_once_with(raise_exception=True)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_verificar_status_200_en_respuesta(self, mock_get_404, mock_upd_ser_class, mock_service, mock_serializer_class):
        """
        Test: Verificar status 200 en respuesta
        
        Given: Un flujo de actualización parcial exitoso.
        When: La vista termina de procesar la petición y genera la Response.
        Then: El código de estado de la respuesta debe ser 200 OK.
        """
        request = self.factory.patch(self.url, data={"nombre": "Nuevo"}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()
        mock_upd_ser_class.return_value.is_valid.return_value = True
        mock_service.return_value = MagicMock()
        mock_serializer_class.return_value.data = {"id": self.pk}

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    # ---------------------------------------------------------------------------
    # TESTS DELETE
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.delete_puesto_service')
    def test_elimina_correctamente_204(self, mock_delete_service):
        """
        Test: Elimina correctamente (204)
        
        Given: Un ID de puesto válido y un usuario autenticado.
        When: Se realiza una petición DELETE a la vista.
        Then: El servicio procesa la eliminación y la vista responde con un status 204 No Content.
        """
        request = self.factory.delete(self.url)
        force_authenticate(request, user=self.user)

        mock_delete_service.return_value = None

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)



    @patch('api.vistas.puesto.puesto_detalle_view.delete_puesto_service')
    def test_llama_al_servicio_con_parametros_correctos(self, mock_delete_service):
        """
        Test: Llama al servicio con parámetros correctos
        
        Given: Una petición DELETE con un usuario autenticado y un pk específico.
        When: La vista procesa la solicitud.
        Then: Se verifica que el servicio de eliminación es invocado con el objeto usuario de la request y el pk recibido por URL.
        """
        request = self.factory.delete(self.url)
        force_authenticate(request, user=self.user)

        self.vista_callable(request, pk=self.pk)

        mock_delete_service.assert_called_once_with(
            usuario=self.user,
            puesto_id=self.pk
        )



    @patch('api.vistas.puesto.puesto_detalle_view.delete_puesto_service')
    def test_devuelve_status_204_sin_contenido(self, mock_delete_service):
        """
        Test: Devuelve status 204 sin contenido
        
        Given: Una ejecución exitosa del servicio de borrado.
        When: La vista genera la respuesta final.
        Then: La respuesta no debe contener datos en el cuerpo (None o vacío) y el status debe ser 204.
        """
        request = self.factory.delete(self.url)
        force_authenticate(request, user=self.user)

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)



    @patch('api.vistas.puesto.puesto_detalle_view.delete_puesto_service')
    def test_error_en_delete_puesto_service_lanza_excepcion(self, mock_delete_service):
        """
        Test: Error en el servicio
        
        Given: Una petición DELETE válida.
        When: El servicio de eliminación lanza una excepción (ej. error de permisos internos o fallo de BD).
        Then: La excepción se propaga fuera de la vista para ser gestionada por el framework.
        """
        request = self.factory.delete(self.url)
        force_authenticate(request, user=self.user)

        mock_delete_service.side_effect = Exception("No se pudo eliminar el puesto por restricciones de integridad")

        with self.assertRaises(Exception) as context:
            self.vista_callable(request, pk=self.pk)

        self.assertEqual(str(context.exception), "No se pudo eliminar el puesto por restricciones de integridad")



    @patch('api.vistas.puesto.puesto_detalle_view.delete_puesto_service')
    def test_verificar_que_el_servicio_se_llama_una_sola_vez(self, mock_delete_service):
        """
        Test: Verificar que el servicio se llama una sola vez
        
        Given: Una petición DELETE válida hacia un puesto específico.
        When: La vista procesa la solicitud de eliminación.
        Then: Se asegura que la comunicación con el servicio de borrado ocurra exactamente una vez para evitar ejecuciones duplicadas.
        """
        request = self.factory.delete(self.url)
        force_authenticate(request, user=self.user)

        self.vista_callable(request, pk=self.pk)

        mock_delete_service.assert_called_once()



    @patch('api.vistas.puesto.puesto_detalle_view.delete_puesto_service')
    def test_verificar_que_no_se_devuelve_body_en_la_respuesta(self, mock_delete_service):
        """
        Test: Verificar que no se devuelve body en la respuesta
        
        Given: Una petición de borrado exitosa.
        When: La vista construye la Response con status 204.
        Then: El cuerpo de la respuesta (data) debe ser nulo, cumpliendo con el estándar de HTTP 204 No Content.
        """
        request = self.factory.delete(self.url)
        force_authenticate(request, user=self.user)

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIsNone(response.data)

        self.assertEqual(len(response.rendered_content), 0)