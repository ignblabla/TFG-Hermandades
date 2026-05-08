from unittest.mock import patch, MagicMock
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from api.vistas.hermano.hermano_list_view import HermanoListView


class TestHermanoListView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.vista = HermanoListView.as_view()
        self.path = "/api/hermanos/listado/" 
        self.mock_user = MagicMock()



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_respuesta_paginada_correcta(
        self, 
        mock_get_listado_service, 
        mock_paginacion_class, 
        mock_serializer_class
    ):
        """
        Test: Respuesta paginada correcta
        
        Given: Un usuario autenticado que realiza una petición GET a la vista.
        When: El servicio devuelve el queryset de hermanos y el paginador genera una página con datos.
        Then: Se pagina el resultado, se serializa con many=True y se retorna la respuesta paginada.
        """
        vista = HermanoListView()

        vista.pagination_class = mock_paginacion_class

        mock_request = MagicMock()
        mock_user = MagicMock()
        mock_request.user = mock_user

        mock_queryset = MagicMock()
        mock_get_listado_service.return_value = mock_queryset

        mock_paginador_instancia = MagicMock()
        mock_paginacion_class.return_value = mock_paginador_instancia
        
        mock_pagina = ['hermano1', 'hermano2']
        mock_paginador_instancia.paginate_queryset.return_value = mock_pagina
        
        mock_respuesta_paginada = MagicMock(spec=Response)
        mock_paginador_instancia.get_paginated_response.return_value = mock_respuesta_paginada

        mock_serializer_instancia = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instancia
        mock_serializer_instancia.data = [{'id': 1, 'nombre': 'Hermano 1'}]

        response = vista.get(mock_request)

        mock_get_listado_service.assert_called_once_with(usuario_solicitante=mock_user)

        mock_paginador_instancia.paginate_queryset.assert_called_once_with(mock_queryset, mock_request)

        mock_serializer_class.assert_called_once_with(mock_pagina, many=True)

        mock_paginador_instancia.get_paginated_response.assert_called_once_with(mock_serializer_instancia.data)

        self.assertEqual(response, mock_respuesta_paginada)



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_respuesta_sin_paginacion(
        self, 
        mock_get_listado_service, 
        mock_paginacion_class, 
        mock_serializer_class
    ):
        """
        Test: Respuesta sin paginación (page = None)
        
        Given: Un queryset de hermanos válido.
        When: El paginador devuelve None al intentar paginar el queryset.
        Then: No se usa get_paginated_response y se retorna una Response estándar con status 200.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_paginacion_class

        mock_request = MagicMock()
        mock_user = MagicMock()
        mock_request.user = mock_user

        mock_queryset = MagicMock()
        mock_get_listado_service.return_value = mock_queryset
        
        mock_paginador_instancia = MagicMock()
        mock_paginacion_class.return_value = mock_paginador_instancia
        mock_paginador_instancia.paginate_queryset.return_value = None

        mock_serializer_instancia = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instancia
        mock_serializer_instancia.data = [{'id': 1, 'nombre': 'Hermano Solo'}]

        response = vista.get(mock_request)

        mock_paginador_instancia.paginate_queryset.assert_called_once_with(mock_queryset, mock_request)
        mock_paginador_instancia.get_paginated_response.assert_not_called()

        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_serializer_instancia.data)



    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_permiso_denegado_retorna_403(self, mock_get_listado_service):
        """
        Test: El servicio lanza PermissionDenied → respuesta 403
        
        Given: Un usuario que no tiene permisos suficientes según la lógica del servicio.
        When: get_listado_hermanos_service lanza una excepción PermissionDenied.
        Then: La vista captura la excepción y retorna una respuesta con status 403 
            y el mensaje de error en el campo 'detail'.
        """
        vista = HermanoListView()
        mock_request = MagicMock()
        
        mensaje_error = "No tienes permiso para ver este listado."
        mock_get_listado_service.side_effect = PermissionDenied(mensaje_error)

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], mensaje_error)



    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_error_generico_retorna_500(self, mock_get_listado_service):
        """
        Test: El servicio lanza excepción genérica → respuesta 500
        
        Given: Un fallo inesperado en el servicio (ej. error de base de datos o bug).
        When: El servicio lanza una excepción de tipo Exception.
        Then: La vista captura el error y retorna un status 500 con un mensaje amigable 
            y el detalle técnico del error.
        """
        vista = HermanoListView()
        mock_request = MagicMock()
        
        error_tecnico = "Database connection lost"
        mock_get_listado_service.side_effect = Exception(error_tecnico)

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el listado.")
        self.assertEqual(response.data['error'], error_tecnico)



    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_usuario_no_autenticado_bloqueado(self, mock_service):
        """
        Test: Usuario no autenticado (control de permisos)
        
        Given: Una petición sin credenciales de autenticación.
        When: Se intenta acceder a la vista.
        Then: DRF bloquea el acceso (401/403) gracias a IsAuthenticated y el servicio no se ejecuta.
        """
        request = self.factory.get(self.path)

        response = self.vista(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        mock_service.assert_not_called()