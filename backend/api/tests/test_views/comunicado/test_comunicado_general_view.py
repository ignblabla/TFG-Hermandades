import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from api.vistas.comunicado.comunicados_general_view import ComunicadoListCreateView


class TestComunicadoListCreateView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ComunicadoListCreateView.as_view()
        self.path = "/api/comunicados/"

        self.mock_normal = MagicMock(spec=['is_authenticated', 'esAdmin', 'areas_interes'])
        self.mock_normal.is_authenticated = True
        self.mock_normal.esAdmin = False

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin', 'areas_interes'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.PaginacionDoceElementos")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_get_flujo_feliz_con_paginacion(self, mock_comunicado, mock_paginacion, mock_serializer):
        """
        Test: Flujo feliz CON paginación (Rama 1)
        
        Given: Un usuario autenticado (normal) solicitando comunicados.
        When: El paginador segmenta exitosamente el queryset devuelto por el ORM.
        Then: Se instancia el serializador con la página de resultados y 
            se retorna get_paginated_response.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_normal)
        request.user = self.mock_normal

        mock_qs_final = MagicMock(name="QuerySetFinal")
        mock_comunicado.objects.select_related.return_value.prefetch_related.return_value.\
            filter.return_value.distinct.return_value.order_by.return_value = mock_qs_final

        mock_paginator_instance = mock_paginacion.return_value
        mock_page = ["comunicado_1", "comunicado_2"]
        mock_paginator_instance.paginate_queryset.return_value = mock_page

        mock_respuesta_paginada = Response({"count": 2, "results": []})
        mock_paginator_instance.get_paginated_response.return_value = mock_respuesta_paginada

        response = self.view(request)

        mock_paginator_instance.paginate_queryset.assert_called_once_with(mock_qs_final, ANY)
        mock_serializer.assert_called_once_with(mock_page, many=True, context={'request': ANY})
        mock_paginator_instance.get_paginated_response.assert_called_once()
        
        self.assertEqual(response, mock_respuesta_paginada)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.PaginacionDoceElementos")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_get_flujo_feliz_sin_paginacion(self, mock_comunicado, mock_paginacion, mock_serializer):
        """
        Test: Flujo feliz SIN paginación (Rama 2)
        
        Given: Un usuario autenticado (normal) solicitando comunicados.
        When: El paginador devuelve None (no aplica paginación).
        Then: La vista serializa el queryset completo y retorna status 200.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_normal)
        request.user = self.mock_normal

        mock_qs_final = MagicMock(name="QuerySetFinal")
        mock_comunicado.objects.select_related.return_value.prefetch_related.return_value.\
            filter.return_value.distinct.return_value.order_by.return_value = mock_qs_final

        mock_paginator_instance = mock_paginacion.return_value
        mock_paginator_instance.paginate_queryset.return_value = None

        datos_esperados = [{"id": 1, "titulo": "General"}]
        mock_serializer.return_value.data = datos_esperados

        response = self.view(request)

        mock_serializer.assert_called_once_with(mock_qs_final, many=True, context={'request': ANY})
        mock_paginator_instance.get_paginated_response.assert_not_called()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    def test_get_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales válidas.
        When: Se intenta acceder al listado de comunicados.
        Then: Las permission_classes interceptan la petición (401/403).
        """
        request = self.factory.get(self.path)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_post_creacion_comunicado_exitoso(self, mock_form, mock_service, mock_list_serializer):
        """
        Test: Flujo feliz consolidado (CREACIÓN OK)
        
        Given: Un usuario administrador autenticado y datos de entrada válidos.
        When: Se realiza una petición POST.
        Then: Se valida el formulario, se invoca al servicio con los datos correctos,
            se serializa el objeto creado y se retorna status 201.
        """
        datos_post = {"titulo": "Nuevo Comunicado"}
        request = self.factory.post(self.path, data=datos_post, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        datos_validados = {"titulo": "test"}
        mock_form_instance.validated_data = datos_validados

        objeto_creado = MagicMock(name="NuevoComunicado")
        mock_service_instance = mock_service.return_value
        mock_service_instance.create_comunicado.return_value = objeto_creado

        datos_respuesta = {"id": 1, "titulo": "test"}
        mock_list_serializer.return_value.data = datos_respuesta

        response = self.view(request)

        mock_form_instance.is_valid.assert_called_once_with(raise_exception=True)
        mock_service_instance.create_comunicado.assert_called_once_with(
            usuario=self.mock_admin,
            data_validada=datos_validados
        )
        mock_list_serializer.assert_called_once_with(objeto_creado)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, datos_respuesta)



    def test_post_usuario_no_admin_falla_403(self):
        """
        Test: Seguridad - Usuario sin permisos de administrador
        
        Given: Un usuario autenticado pero sin rol de administrador (esAdmin=False).
        When: Se intenta realizar una petición POST para crear un comunicado.
        Then: La permission_class EsAdministrador intercepta y bloquea la petición con 403.
        """
        request = self.factory.post(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_normal)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_post_validacion_falla_retorna_400(self, mock_form):
        """
        Test: El serializador de entrada detecta datos inválidos
        
        Given: Un payload que viola las reglas del serializador enviado por un admin.
        When: Se invoca is_valid(raise_exception=True).
        Then: DRF lanza ValidationError y la vista retorna status 400.
        """
        request = self.factory.post(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_form.return_value.is_valid.side_effect = ValidationError({"titulo": "Requerido"})

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_post_error_en_bloque_try_retorna_400(self, mock_form, mock_service):
        """
        Test: Captura de excepciones en el bloque try/except (Servicio o Serialización)
        
        Given: Un formulario válido enviado por un administrador.
        When: Cualquier paso dentro del bloque try lanza una excepción genérica.
        Then: La vista captura el error y retorna status 400 con el detalle.
        """
        request = self.factory.post(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_admin)
        
        mock_form.return_value.is_valid.return_value = True
        
        error_msg = "Error crítico en lógica de negocio"
        mock_service.return_value.create_comunicado.side_effect = Exception(error_msg)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": error_msg})



    def test_post_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición POST sin credenciales.
        When: Se intenta acceder al endpoint.
        Then: Las permission_classes bloquean el acceso (401/403).
        """
        request = self.factory.post(self.path, data={"titulo": "Hola"}, format='json')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])