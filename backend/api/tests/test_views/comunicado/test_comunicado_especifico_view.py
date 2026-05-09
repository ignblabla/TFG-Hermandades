import unittest
from unittest.mock import ANY, MagicMock, patch
from django.http import Http404
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.vistas.comunicado.comunicado_view import ComunicadoDetailView
from api.models import Comunicado


class TestComunicadoDetailView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ComunicadoDetailView.as_view()
        self.pk = 1
        self.path = f"/api/comunicados/{self.pk}/"

        self.mock_normal = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_normal.is_authenticated = True
        self.mock_normal.esAdmin = False

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True



    # ---------------------------------------------------------------------------
    # TESTS GET (Requiere IsAuthenticated)
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_get_flujo_feliz_detalle_correcto(self, mock_get_object, mock_serializer):
        """
        Test: Flujo feliz consolidado (detalle correcto)
        
        Given: Un ID de comunicado existente y un usuario autenticado (normal o admin).
        When: Se solicita el detalle mediante GET.
        Then: Se obtiene el objeto de BD, se pasa el request en el contexto 
            del serializador y retorna status 200.
        """
        request = self.factory.get(self.path)

        force_authenticate(request, user=self.mock_normal)

        mock_comunicado = MagicMock(name="ComunicadoInstance")
        mock_get_object.return_value = mock_comunicado

        datos_esperados = {"id": self.pk, "titulo": "Comunicado Test"}
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = datos_esperados
        mock_serializer.return_value = mock_serializer_instance

        response = self.view(request, pk=self.pk)

        mock_get_object.assert_called_once_with(ANY, pk=self.pk)
        mock_serializer.assert_called_once_with(mock_comunicado, context={'request': ANY})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_get_comunicado_no_existe_lanza_404(self, mock_get_object):
        """
        Test: Comunicado no existe o ID inválido
        
        Given: Un ID de comunicado que no existe o tiene formato incorrecto.
        When: La vista intenta obtenerlo a través del shortcut.
        Then: get_object_or_404 lanza Http404 y DRF retorna status 404 NOT FOUND.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_normal)

        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_get_request_sin_autenticacion_falla_401(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición HTTP GET sin credenciales.
        When: Se intenta acceder al detalle del comunicado.
        Then: Las permission_classes interceptan la petición devolviendo 401/403.
        """
        request = self.factory.get(self.path)

        response = self.view(request, pk=self.pk)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    # ---------------------------------------------------------------------------
    # TESTS PUT (Requiere EsAdministrador)
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_put_actualizacion_total_exitosa(self, mock_get_object, mock_form_serializer, mock_service, mock_list_serializer):
        """
        Test: Flujo feliz consolidado (actualización correcta)
        
        Given: Un comunicado existente y datos de actualización válidos enviados por un admin.
        When: Se realiza una petición PUT al endpoint.
        Then: Se valida el formulario, el servicio actualiza el objeto 
            y se devuelve el objeto serializado con status 200.
        """
        datos_input = {"titulo": "Nuevo Título"}
        request = self.factory.put(self.path, data=datos_input, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_comunicado_original = MagicMock()
        mock_get_object.return_value = mock_comunicado_original

        mock_form_instance = MagicMock()
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.validated_data = datos_input
        mock_form_serializer.return_value = mock_form_instance

        mock_obj_actualizado = MagicMock()
        mock_service.return_value.update_comunicado.return_value = mock_obj_actualizado

        datos_respuesta = {"id": self.pk, "titulo": "Nuevo Título"}
        mock_list_serializer.return_value.data = datos_respuesta

        response = self.view(request, pk=self.pk)

        mock_get_object.assert_called_once_with(ANY, pk=self.pk)
        mock_form_serializer.assert_called_once_with(mock_comunicado_original, data=datos_input)
        mock_form_instance.is_valid.assert_called_once_with(raise_exception=True)
        
        mock_service.return_value.update_comunicado.assert_called_once_with(
            usuario=self.mock_admin,
            comunicado_instance=mock_comunicado_original,
            data_validada=datos_input
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_respuesta)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_put_usuario_no_admin_falla_403(self, mock_get_object):
        """
        Test: Seguridad - Usuario sin permisos de administrador (PUT)
        
        Given: Un usuario autenticado pero que no tiene el atributo esAdmin a True.
        When: Se intenta hacer una petición PUT.
        Then: La permission_class EsAdministrador intercepta la petición y retorna 403 Forbidden.
        """
        request = self.factory.put(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_normal)

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_get_object.assert_not_called()



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_put_validacion_falla_retorna_400(self, mock_get_object, mock_form_serializer):
        """
        Test: Validación del serializer falla
        
        Given: Datos que no cumplen con los requisitos del serializador.
        When: is_valid(raise_exception=True) es invocado.
        Then: DRF lanza ValidationError y la vista retorna status 400.
        """
        request = self.factory.put(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_get_object.return_value = MagicMock()
        mock_form_serializer.return_value.is_valid.side_effect = ValidationError({"error": "campo requerido"})

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_put_excepcion_capturada_en_bloque_try_retorna_400(self, mock_get_object, mock_form_serializer, mock_service):
        """
        Test: Excepción genérica capturada en bloque try/except
        
        Given: Un flujo de validación correcto de un administrador.
        When: Cualquier elemento dentro del try lanza una excepción genérica.
        Then: La vista captura la excepción y retorna 400 con el detalle del error.
        """
        request = self.factory.put(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_get_object.return_value = MagicMock()
        mock_form_serializer.return_value.is_valid.return_value = True

        mensaje_error = "Error interno simulado"
        mock_service.return_value.update_comunicado.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": mensaje_error})



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_put_comunicado_no_existe_lanza_404(self, mock_get_object):
        """
        Test: pk inválido o no existente
        
        Given: Un PK que no corresponde a ningún registro consultado por un admin.
        When: La vista llama a get_object_or_404.
        Then: DRF maneja la excepción Http404 y retorna status 404.
        """
        request = self.factory.put(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS PATCH (Requiere EsAdministrador)
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_patch_actualizacion_parcial_exitosa(self, mock_get_object, mock_form_serializer, mock_service, mock_list_serializer):
        """
        Test: Flujo feliz consolidado (PATCH correcto)
        
        Given: Un comunicado existente y datos parciales enviados por un admin.
        When: Se realiza una petición PATCH al endpoint.
        Then: El serializador se instancia con partial=True, el servicio actualiza 
            el objeto y se retorna status 200 con los datos.
        """
        datos_parciales = {"titulo": "Título modificado"}
        request = self.factory.patch(self.path, data=datos_parciales, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_obj = MagicMock(name="ComunicadoOriginal")
        mock_get_object.return_value = mock_obj

        mock_form_instance = MagicMock()
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.validated_data = datos_parciales
        mock_form_serializer.return_value = mock_form_instance

        obj_actualizado = MagicMock(name="ComunicadoActualizado")
        mock_service.return_value.update_comunicado.return_value = obj_actualizado

        datos_finales = {"id": self.pk, "titulo": "Título modificado", "contenido": "Original"}
        mock_list_serializer.return_value.data = datos_finales

        response = self.view(request, pk=self.pk)

        mock_get_object.assert_called_once_with(ANY, pk=self.pk)
        
        mock_form_serializer.assert_called_once_with(
            mock_obj, 
            data=datos_parciales, 
            partial=True
        )
        mock_form_instance.is_valid.assert_called_once_with(raise_exception=True)

        mock_service.return_value.update_comunicado.assert_called_once_with(
            usuario=self.mock_admin,
            comunicado_instance=mock_obj,
            data_validada=datos_parciales
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_finales)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_patch_usuario_no_admin_falla_403(self, mock_get_object):
        """
        Test: Seguridad - Usuario sin permisos de administrador (PATCH)
        
        Given: Un usuario normal sin permisos de administrador.
        When: Se intenta realizar una petición PATCH.
        Then: DRF bloquea la petición con 403 Forbidden antes de entrar al método.
        """
        request = self.factory.patch(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_normal)

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_get_object.assert_not_called()



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_patch_validacion_falla_retorna_400(self, mock_get_object, mock_form_serializer):
        """
        Test: Validación del serializer falla
        
        Given: Datos que no cumplen las reglas de negocio enviados por admin.
        When: Se llama a is_valid(raise_exception=True).
        Then: DRF lanza ValidationError y retorna status 400.
        """
        request = self.factory.patch(self.path, data={"campo_invalido": "valor"}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_get_object.return_value = MagicMock()
        mock_form_serializer.return_value.is_valid.side_effect = ValidationError({"error": "dato invalido"})

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_patch_excepcion_capturada_en_bloque_try_retorna_400(self, mock_get_object, mock_form_serializer, mock_service):
        """
        Test: Excepción genérica capturada en bloque try/except
        
        Given: Un formulario parcial válido y recuperado con éxito.
        When: Cualquier elemento dentro del try lanza una excepción genérica.
        Then: La vista captura la excepción y retorna 400 con el detalle del error.
        """
        request = self.factory.patch(self.path, data={"titulo": "error"}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_get_object.return_value = MagicMock()
        mock_form_serializer.return_value.is_valid.return_value = True

        mensaje_error = "Error interno simulado"
        mock_service.return_value.update_comunicado.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], mensaje_error)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_patch_comunicado_no_existe_lanza_404(self, mock_get_object):
        """
        Test: pk inválido o no existente
        
        Given: Un ID de comunicado que no figura en la base de datos consultado por admin.
        When: Se llama a get_object_or_404.
        Then: Se lanza Http404 y DRF responde con status 404.
        """
        request = self.factory.patch(self.path, data={"titulo": "cambio"}, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    # ---------------------------------------------------------------------------
    # TESTS DELETE (Requiere EsAdministrador)
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_flujo_feliz_consolidado(self, mock_get_object, mock_service):
        """
        Test: Flujo feliz (DELETE correcto)
        
        Given: Un ID de comunicado válido, existente, y un administrador.
        When: Se realiza una petición DELETE.
        Then: Se obtiene el objeto, se pasa al servicio, y se retorna status 204.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_obj = MagicMock(name="ComunicadoAEliminar")
        mock_get_object.return_value = mock_obj

        response = self.view(request, pk=self.pk)

        mock_get_object.assert_called_once_with(ANY, pk=self.pk)
        
        mock_service.return_value.delete_comunicado.assert_called_once_with(
            usuario=self.mock_admin,
            comunicado_instance=mock_obj
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_usuario_no_admin_falla_403(self, mock_get_object):
        """
        Test: Seguridad - Usuario sin permisos de administrador (DELETE)
        
        Given: Un usuario autenticado pero sin rol de administrador.
        When: Se realiza una petición DELETE.
        Then: EsAdministrador bloquea la operación retornando 403 Forbidden.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_normal)

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_get_object.assert_not_called()



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_servicio_lanza_excepcion_retorna_400(self, mock_get_object, mock_service):
        """
        Test: Excepción capturada en bloque try/except
        
        Given: Un comunicado existente y una solicitud enviada por un administrador.
        When: El servicio delete_comunicado lanza una excepción.
        Then: La vista captura la excepción y retorna 400 con el detalle del error.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_get_object.return_value = MagicMock()

        mensaje_error = "Restricción de integridad referencial"
        mock_service.return_value.delete_comunicado.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": mensaje_error})



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_comunicado_no_existe_lanza_404(self, mock_get_object):
        """
        Test: pk inválido o no existente
        
        Given: Un ID de comunicado inexistente y una solicitud DELETE de un admin.
        When: La vista llama a get_object_or_404.
        Then: Se lanza Http404 y DRF responde con status 404.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_delete_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición DELETE sin credenciales válidas.
        When: Se intenta acceder al endpoint.
        Then: Las permission_classes de DRF bloquean el acceso con 401/403.
        """
        request = self.factory.delete(self.path)

        response = self.view(request, pk=self.pk)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])