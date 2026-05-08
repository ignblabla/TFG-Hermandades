from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.response import Response
from unittest.mock import patch, MagicMock

from api.vistas.papeleta_sitio.listado_papeletas_view import MisPapeletasListView


class TestMisPapeletasListViewPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = MisPapeletasListView.as_view()
        self.path = "/api/papeletas/mis-papeletas/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    def test_usuario_no_autenticado_deniega_acceso(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición realizada sin credenciales de usuario.
        When: Se evalúa el permiso IsAuthenticated.
        Then: La vista deniega la ejecución y retorna un status 403 Forbidden.
        """
        request = self.factory.get(self.path)

        anon_user = MagicMock()
        anon_user.is_authenticated = False
        force_authenticate(request, user=anon_user)
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_devuelve_respuesta_paginada_correctamente(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Devuelve respuesta paginada correctamente

        Given: Un usuario autenticado con un historial de papeletas que excede el tamaño de la página.
        When: Se realiza una petición GET al listado de sus papeletas.
        Then: La vista obtiene el queryset, extrae la página, la serializa y devuelve la respuesta final construida por el paginador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_service.return_value = MagicMock()
        mock_paginator = MagicMock()
        mock_pagination_class.return_value = mock_paginator
        mock_paginator.paginate_queryset.return_value = ["papeleta_1"]
        
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1}]
        mock_serializer_class.return_value = mock_serializer

        respuesta_esperada = Response({"results": mock_serializer.data}, status=status.HTTP_200_OK)
        mock_paginator.get_paginated_response.return_value = respuesta_esperada

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, respuesta_esperada.data)
        mock_service.assert_called_once_with(usuario=self.mock_user)
        mock_paginator.get_paginated_response.assert_called_once_with(mock_serializer.data)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_devuelve_respuesta_sin_paginacion_cuando_page_es_none(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Devuelve respuesta sin paginación cuando page es None
        
        Given: El paginador determina que no es necesaria la paginación (ej: pocos resultados).
        When: paginate_queryset devuelve None.
        Then: La vista serializa el queryset completo y devuelve una Response estándar 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_queryset = MagicMock()
        mock_service.return_value = mock_queryset

        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1}]
        mock_serializer_class.return_value = mock_serializer
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_serializer.data)
        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)



    @patch('builtins.print')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_error_en_el_servicio_devuelve_500(self, mock_service, mock_print):
        """
        Test: Error general en la vista devuelve 500
        
        Given: Un error inesperado en cualquier dependencia (ej: el servicio de base de datos).
        When: Se lanza una excepción durante el procesamiento de la vista.
        Then: La vista captura la excepción, imprime el error en consola y retorna un status 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        error_msg = "Database connection lost"
        mock_service.side_effect = Exception(error_msg)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el historial de papeletas.")
        mock_print.assert_called_once_with(f"Error en MisPapeletasListView: {error_msg}")