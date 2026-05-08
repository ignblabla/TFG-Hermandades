import unittest
from unittest.mock import ANY, MagicMock, patch

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.response import Response

from api.vistas.comunicado.comunicado_admin_list_view import ComunicadoAdminListView


class TestComunicadoAdminListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_class = ComunicadoAdminListView
        self.path = "/api/admin/comunicados/listado-total/"

        self.mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_user.is_authenticated = True
        self.mock_user.esAdmin = True



    def test_acceso_denegado_si_no_es_admin(self):
        """
        Test: El permiso EsAdministrador bloquea usuarios sin esAdmin=True.

        Given: Un usuario autenticado pero sin permisos de administrador.
        When: Se realiza GET a la vista.
        Then: La respuesta tiene status 403 Forbidden.
        """
        user_sin_permiso = MagicMock(spec=['is_authenticated', 'esAdmin'])
        user_sin_permiso.is_authenticated = True
        user_sin_permiso.esAdmin = False

        request = self.factory.get(self.path)
        force_authenticate(request, user=user_sin_permiso)

        view = self.view_class.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 403)



    def test_acceso_denegado_si_no_autenticado(self):
        """
        Test: El permiso EsAdministrador bloquea usuarios no autenticados.

        Given: Un usuario no autenticado.
        When: Se realiza GET a la vista.
        Then: La respuesta tiene status 403 Forbidden.
        """
        user_anonimo = MagicMock(spec=['is_authenticated', 'esAdmin'])
        user_anonimo.is_authenticated = False

        request = self.factory.get(self.path)
        force_authenticate(request, user=user_anonimo)

        view = self.view_class.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 403)



    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoService')
    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoListSerializer')
    def test_get_sin_paginacion_retorna_200(
        self, mock_serializer_cls, mock_service
    ):
        """
        Test: GET retorna 200 con todos los comunicados cuando no hay página.

        Given: Un usuario administrador autenticado y el servicio retorna una lista de comunicados.
        When: Se realiza GET y el paginador no produce página (retorna None).
        Then: La respuesta tiene status 200 y contiene los datos serializados.
        """
        mock_comunicados = [MagicMock(), MagicMock()]
        mock_service.obtener_todos_los_comunicados.return_value = mock_comunicados

        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None

        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1}, {'id': 2}]
        mock_serializer_cls.return_value = mock_serializer

        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        with patch.object(self.view_class, 'pagination_class', return_value=mock_paginator):
            view = self.view_class.as_view()
            response = view(request)

        self.assertEqual(response.status_code, 200)
        mock_service.obtener_todos_los_comunicados.assert_called_once_with(self.mock_user)

        mock_serializer_cls.assert_called_once_with(
            mock_comunicados, many=True, context={'request': ANY}
        )



    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoService')
    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoListSerializer')
    def test_get_delega_en_servicio_con_usuario_correcto(
        self, mock_serializer_cls, mock_service
    ):
        """
        Test: La vista pasa el usuario del request al servicio.

        Given: Un usuario administrador autenticado.
        When: Se realiza GET a la vista.
        Then: ComunicadoService.obtener_todos_los_comunicados se llama exactamente una vez
            con el usuario del request.
        """
        mock_service.obtener_todos_los_comunicados.return_value = []

        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None

        mock_serializer_cls.return_value = MagicMock(data=[])

        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        with patch.object(self.view_class, 'pagination_class', return_value=mock_paginator):
            view = self.view_class.as_view()
            view(request)

        mock_service.obtener_todos_los_comunicados.assert_called_once_with(self.mock_user)



    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoService')
    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoListSerializer')
    def test_get_con_paginacion_retorna_respuesta_paginada(
        self, mock_serializer_cls, mock_service
    ):
        """
        Test: Verifica que la vista retorna una respuesta paginada correctamente 
        cuando el paginador devuelve una página de resultados.

        Given: Un usuario administrador autenticado y un paginador que retorna una página válida de resultados.
        When: Se realiza GET a la vista.
        Then: La vista pagina el queryset, serializa solo la página, y retorna una respuesta con status 200 usando get_paginated_response.
        """
        mock_comunicados = [MagicMock(), MagicMock(), MagicMock()]
        mock_service.obtener_todos_los_comunicados.return_value = mock_comunicados

        mock_page = [MagicMock(), MagicMock()]
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = mock_page

        datos_serializados = [{'id': 1}, {'id': 2}]
        mock_paginator.get_paginated_response.return_value = Response({
            'count': 3,
            'results': datos_serializados
        })

        mock_serializer = MagicMock()
        mock_serializer.data = datos_serializados
        mock_serializer_cls.return_value = mock_serializer

        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        with patch.object(self.view_class, 'pagination_class', return_value=mock_paginator):
            view = self.view_class.as_view()
            response = view(request)

        self.assertEqual(response.status_code, 200)

        mock_service.obtener_todos_los_comunicados.assert_called_once_with(self.mock_user)

        mock_paginator.paginate_queryset.assert_called_once()
        args, kwargs = mock_paginator.paginate_queryset.call_args
        self.assertEqual(args[0], mock_comunicados)

        mock_serializer_cls.assert_called_once_with(
            mock_page, many=True, context={'request': ANY}
        )

        mock_paginator.get_paginated_response.assert_called_once_with(datos_serializados)



    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoService')
    @patch('api.vistas.comunicado.comunicado_admin_list_view.ComunicadoListSerializer')
    @patch('api.vistas.comunicado.comunicado_admin_list_view.PaginacionDoceElementos')
    def test_get_delega_en_servicio_con_usuario_correcto(
        self, mock_paginacion_cls, mock_serializer_cls, mock_service
    ):
        """
        Test: La vista pasa el usuario del request al servicio.

        Given: Un usuario administrador autenticado.
        When: Se realiza GET a la vista.
        Then: ComunicadoService.obtener_todos_los_comunicados se llama exactamente una vez
            con el usuario del request.
        """
        mock_service.obtener_todos_los_comunicados.return_value = []

        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_paginacion_cls.return_value = mock_paginator

        mock_serializer_cls.return_value = MagicMock(data=[])

        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        view = self.view_class.as_view()
        view(request)

        mock_service.obtener_todos_los_comunicados.assert_called_once_with(self.mock_user)