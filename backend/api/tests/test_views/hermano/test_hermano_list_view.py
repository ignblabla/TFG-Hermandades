from unittest.mock import ANY, patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from api.vistas.hermano.hermano_list_view import HermanoListView
from api.vistas.solicitud_baja.resolver_solicitud_baja_view import EsAdministrador


class TestHermanoListView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.vista_callable = HermanoListView.as_view()
        self.path = "/api/hermanos/listado/" 
        self.user = MagicMock()
        self.user.is_authenticated = True



    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch.object(EsAdministrador, 'has_permission', return_value=True)
    def test_get_listado_paginado_exitoso_200(self, mock_permiso, mock_serializer, mock_service):
        """
        Test: Listado paginado exitoso (200)
        
        Given: Un usuario administrador autenticado.
        When: Se solicita el listado de hermanos.
        Then: La vista debe instanciar el paginador, paginar el queryset y retornar 200.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.user)

        mock_queryset = MagicMock()
        mock_service.return_value = mock_queryset

        mock_paginador = MagicMock()
        mock_paginador.paginate_queryset.return_value = ['hermano1']
        mock_paginador.get_paginated_response.return_value = Response({'results': []}, status=200)

        with patch('api.vistas.hermano.hermano_list_view.HermanoListView.pagination_class', return_value=mock_paginador):
            response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once_with(usuario_solicitante=self.user)
        mock_paginador.paginate_queryset.assert_called_once_with(mock_queryset, ANY)



    @patch.object(EsAdministrador, 'has_permission', return_value=True)
    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_listado_sin_paginacion_retorna_200_directo(self, mock_service, mock_serializer_class, mock_permiso):
        """
        Test: Listado sin paginación (page is None) -> 200 OK
        
        Given: Un usuario administrador autenticado.
        When: El paginador devuelve None (por ejemplo, porque la paginación está desactivada por parámetros).
        Then: La vista serializa el queryset completo y retorna una Response estándar (status 200).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.user)

        mock_queryset = MagicMock()
        mock_service.return_value = mock_queryset

        mock_paginador = MagicMock()
        mock_paginador.paginate_queryset.return_value = None

        mock_serializer_instancia = mock_serializer_class.return_value
        datos_esperados = [{'id': 1, 'nombre': 'Hermano Completo'}]
        mock_serializer_instancia.data = datos_esperados

        with patch('api.vistas.hermano.hermano_list_view.HermanoListView.pagination_class', return_value=mock_paginador):
            response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)

        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)

        mock_paginador.get_paginated_response.assert_not_called()



    @patch.object(EsAdministrador, 'has_permission', return_value=True)
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_permiso_denegado_en_servicio_retorna_403(self, mock_service, mock_permiso):
        """
        Test: PermissionDenied en servicio -> 403
        
        Given: Un usuario que supera el permiso de la vista pero no la lógica del servicio.
        When: El servicio lanza una excepción PermissionDenied.
        Then: La vista captura el error y retorna status 403 con el detalle.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.user)
        
        mensaje_error = "No tienes permiso para ver este listado."
        mock_service.side_effect = PermissionDenied(mensaje_error)

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], mensaje_error)



    @patch.object(EsAdministrador, 'has_permission', return_value=True)
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_error_generico_retorna_500(self, mock_service, mock_permiso):
        """
        Test: Error genérico -> 500
        
        Given: Un fallo inesperado en el servidor.
        When: El servicio lanza una excepción de tipo Exception.
        Then: La vista retorna un status 500 con el mensaje de error técnico.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.user)
        mock_service.side_effect = Exception("Database error")

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el listado.")



    @patch.object(EsAdministrador, 'has_permission', return_value=False)
    def test_usuario_autenticado_no_admin_denegado_403(self, mock_permiso):
        """
        Test: Usuario autenticado no admin -> 403
        
        Given: Un usuario autenticado que no es administrador.
        When: Intenta acceder al listado de hermanos.
        Then: El permiso EsAdministrador bloquea la petición antes de ejecutar la vista.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.user)

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    def test_usuario_no_autenticado_denegado_401(self):
        """
        Test: Usuario anónimo -> 401
        
        Given: Un usuario no autenticado.
        When: Intenta acceder al listado.
        Then: DRF bloquea el acceso devolviendo 401 Unauthorized.
        """
        request = self.factory.get(self.path)
        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)