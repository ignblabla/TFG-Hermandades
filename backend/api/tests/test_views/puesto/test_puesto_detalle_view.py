import unittest
from unittest.mock import patch, MagicMock
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.exceptions import ValidationError

from django.http import Http404

from api.vistas.puesto.puesto_detalle_view import PuestoDetalleView
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador


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



    def test_usuario_no_autenticado_acceso_denegado_401(self):
        """
        Test: Usuario anónimo -> 401
        
        Given: Una petición GET enviada por un usuario no autenticado (anónimo).
        When: La vista procesa la solicitud y evalúa la clase de permiso IsAuthenticated.
        Then: Se deniega el acceso devolviendo un status 401 Unauthorized.
        """
        request = self.factory.get(self.url)

        response = self.vista_callable(request, pk=self.pk)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    @patch.object(EsAdministrador, 'has_permission', return_value=False)
    def test_usuario_autenticado_no_admin_prohibido_escritura_403(self, mock_permiso):
        """
        Test: Usuario autenticado pero NO admin intentando PUT/PATCH/DELETE -> 403
        
        Given: Un usuario autenticado que no posee el rol de administrador.
        When: Se intenta realizar una operación de escritura (PUT, PATCH o DELETE).
        Then: El permiso EsAdministrador deniega la acción devolviendo un status 403 Forbidden.
        """
        for metodo in ['put', 'patch', 'delete']:
            request = getattr(self.factory, metodo)(self.url, data=self.data_update)
            force_authenticate(request, user=self.user)
            response = self.vista_callable(request, pk=self.pk)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, f"Falló en {metodo}")



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    @patch('api.vistas.puesto.puesto_detalle_view.Puesto')
    def test_get_devuelve_puesto_correctamente_200(self, mock_puesto_model, mock_get_404, mock_serializer_class):
        """
        Test: Devuelve puesto correctamente (200)
        
        Given: Un identificador (pk) de un puesto que existe en la base de datos.
        When: Se realiza una petición GET a la vista de detalle.
        Then: Se recupera el modelo, se serializa y se retorna un status 200 OK con los datos.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        puesto_mock = MagicMock()
        mock_get_404.return_value = puesto_mock
        
        datos_esperados = {"id": self.pk, "nombre": "Puesto de Prueba"}
        mock_serializer_instancia = mock_serializer_class.return_value
        mock_serializer_instancia.data = datos_esperados

        response = self.vista_callable(request, pk=self.pk)

        mock_get_404.assert_called_once_with(mock_puesto_model, pk=self.pk)
        mock_serializer_class.assert_called_once_with(puesto_mock)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_get_puesto_no_existe_lanza_404(self, mock_get_404):
        """
        Test: Puesto no existe -> 404
        
        Given: Un ID de puesto (pk) que no se encuentra en la base de datos.
        When: Se invoca al atajo get_object_or_404.
        Then: DRF captura la excepción Http404 y devuelve una respuesta con status 404.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_get_404.side_effect = Http404()

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS PUT
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_puesto_no_existe_devuelve_404(self, mock_get_404):
        """
        Test: Puesto no existe (devuelve 404)
        
        Given: Un intento de actualización sobre un recurso inexistente.
        When: get_object_or_404 no encuentra el puesto.
        Then: DRF maneja la excepción Http404 y devuelve una respuesta 404 Not Found.
        """
        request = self.factory.put(self.url, data=self.data_update, format='json')
        force_authenticate(request, user=self.user)

        mock_get_404.side_effect = Http404()

        response = self.vista_callable(request, pk=self.pk)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_serializer_invalido_devuelve_400(self, mock_get_404, mock_upd_serializer_class):
        """
        Test: Serializer inválido (devuelve 400)
        
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

        datos_finales = {"id": self.pk, "nombre": "Costalero Editado"}
        mock_serializer_class.return_value.data = datos_finales

        response = self.vista_callable(request, pk=self.pk)

        mock_upd_serializer_class.assert_called_once_with(puesto_inicial, data=self.data_update)
        mock_upd_ser.is_valid.assert_called_once_with(raise_exception=True)
        mock_service.assert_called_once_with(usuario=self.user, puesto_id=self.pk, data_validada=self.data_update)
        mock_serializer_class.assert_called_once_with(puesto_final)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_finales)



    # ---------------------------------------------------------------------------
    # TESTS PATCH
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.PuestoSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.update_puesto_service')
    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_actualiza_parcialmente_correctamente_200(self, mock_get_404, mock_upd_ser_class, mock_service, mock_serializer_class):
        """
        Test: Actualiza parcialmente correctamente (200)
        
        Given: Un ID de puesto existente y un subconjunto de datos válidos.
        When: Se procesa la petición PATCH.
        Then: La vista valida, actualiza mediante el servicio y retorna 200 OK con los datos actualizados.
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
        
        datos_esperados = {"id": self.pk, **data_parcial}
        mock_serializer_class.return_value.data = datos_esperados

        response = self.vista_callable(request, pk=self.pk)

        mock_upd_ser_class.assert_called_once_with(puesto_mock, data=data_parcial, partial=True)
        mock_upd_ser.is_valid.assert_called_once_with(raise_exception=True)
        mock_service.assert_called_once_with(usuario=self.user, puesto_id=self.pk, data_validada=data_parcial)
        mock_serializer_class.assert_called_once_with(puesto_actualizado)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_puesto_no_existe_devuelve_404(self, mock_get_404):
        """
        Test: Puesto no existe (devuelve 404)
        
        Given: Un intento de PATCH sobre un recurso inexistente.
        When: get_object_or_404 no encuentra el puesto y lanza Http404.
        Then: DRF maneja la excepción y devuelve una respuesta 404 Not Found.
        """
        request = self.factory.patch(self.url, data={"nombre": "Nuevo"}, format='json')
        force_authenticate(request, user=self.user)

        mock_get_404.side_effect = Http404()

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.puesto.puesto_detalle_view.PuestoUpdateSerializer')
    @patch('api.vistas.puesto.puesto_detalle_view.get_object_or_404')
    def test_patch_serializer_invalido_devuelve_400(self, mock_get_404, mock_upd_ser_class):
        """
        Test: Serializer inválido (devuelve 400)
        
        Given: Datos parciales que no cumplen con las reglas de validación del serializador.
        When: Se llama a serializer.is_valid(raise_exception=True).
        Then: DRF captura la excepción ValidationError y retorna status 400 Bad Request.
        """
        request = self.factory.patch(self.url, data={"nombre": ""}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_get_404.return_value = MagicMock()

        errores_esperados = {"nombre": ["Este campo no puede estar vacío."]}
        mock_upd_ser = mock_upd_ser_class.return_value
        mock_upd_ser.is_valid.side_effect = ValidationError(errores_esperados)

        response = self.vista_callable(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, errores_esperados)



    # ---------------------------------------------------------------------------
    # TESTS DELETE
    # ---------------------------------------------------------------------------

    @patch('api.vistas.puesto.puesto_detalle_view.delete_puesto_service')
    def test_delete_elimina_puesto_correctamente_204(self, mock_delete_service):
        """
        Test: Elimina puesto correctamente (204)
        
        Given: Una petición DELETE válida con un ID de puesto y un usuario autenticado.
        When: La vista procesa la solicitud de eliminación.
        Then: El servicio es invocado con los parámetros correctos y se retorna status 204 No Content.
        """
        request = self.factory.delete(self.url)
        force_authenticate(request, user=self.user)

        response = self.vista_callable(request, pk=self.pk)

        mock_delete_service.assert_called_once_with(
            usuario=self.user,
            puesto_id=self.pk
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)