from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.response import Response
from unittest.mock import patch, MagicMock

from api.vistas.papeleta_sitio.lista_asistentes_leidos_view import ListarAsistentesLeidosActoView


class TestListarAsistentesLeidosActoViewPermisos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ListarAsistentesLeidosActoView.as_view()
        self.acto_id = 1
        self.path = f"/api/actos/{self.acto_id}/asistentes-leidos/"

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_get_respuesta_paginada_correctamente(self, mock_service, mock_paginador_class, mock_serializer_class):
        """
        Test: Devuelve respuesta paginada correctamente
        
        Given: Un usuario administrador que solicita la lista de asistentes.
        When: El servicio devuelve datos y el paginador determina que hay una página válida.
        Then: La vista devuelve la respuesta estructurada del paginador (status 200).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_queryset = MagicMock()
        mock_service.return_value = mock_queryset

        mock_paginador = MagicMock()
        mock_paginador_class.return_value = mock_paginador
        mock_page = ["asistente1", "asistente2"]
        mock_paginador.paginate_queryset.return_value = mock_page

        datos_esperados = [{"id": 1, "nombre": "Hermano Test"}]
        mock_serializer_class.return_value = MagicMock(data=datos_esperados)

        respuesta_mock = Response({"results": datos_esperados}, status=status.HTTP_200_OK)
        mock_paginador.get_paginated_response.return_value = respuesta_mock

        response = self.view(request, acto_id=self.acto_id)

        mock_service.assert_called_once_with(self.acto_id)
        mock_serializer_class.assert_called_once_with(mock_page, many=True)
        mock_paginador.get_paginated_response.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"results": datos_esperados})



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_get_respuesta_sin_paginacion(self, mock_service, mock_paginador_class, mock_serializer_class):
        """
        Test: Devuelve respuesta sin paginación (page = None)
        
        Given: Una petición GET donde los resultados no alcanzan el límite de paginación.
        When: El método paginate_queryset devuelve None.
        Then: La vista serializa todo el queryset y devuelve una Response plana (status 200).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_queryset = MagicMock()
        mock_service.return_value = mock_queryset

        mock_paginador = MagicMock()
        mock_paginador_class.return_value = mock_paginador
        mock_paginador.paginate_queryset.return_value = None

        datos_esperados = [{"id": 1, "nombre": "Hermano Test"}]
        mock_serializer_class.return_value = MagicMock(data=datos_esperados)

        response = self.view(request, acto_id=self.acto_id)

        mock_paginador.get_paginated_response.assert_not_called()
        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_get_error_interno_devuelve_500(self, mock_service):
        """
        Test: Error general en el servicio devuelve 500
        
        Given: Un usuario administrador válido.
        When: Se produce cualquier error inesperado dentro del bloque try (ej. base de datos).
        Then: El except captura el error y devuelve un status 500 con el mensaje genérico.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_service.side_effect = Exception("Fallo inesperado del sistema")

        response = self.view(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], "Ocurrió un error al recuperar los asistentes.")



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_acceso_denegado_usuarios_sin_permisos(self, mock_service):
        """
        Test: Acceso denegado a usuarios sin permisos
        
        Given: Una petición sin sesión activa, o de un usuario autenticado pero sin privilegios.
        When: Intentan acceder a la ruta de asistentes.
        Then: La clase de permiso EsAdminHermano rechaza la petición (401/403) y el servicio no se ejecuta.
        """
        request_anon = self.factory.get(self.path)
        response_anon = self.view(request_anon, acto_id=self.acto_id)
        self.assertIn(response_anon.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        request_user = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = False
        force_authenticate(request_user, user=mock_user)
        
        response_user = self.view(request_user, acto_id=self.acto_id)
        self.assertEqual(response_user.status_code, status.HTTP_403_FORBIDDEN)

        mock_service.assert_not_called()