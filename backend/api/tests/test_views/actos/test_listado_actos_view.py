from unittest.mock import ANY, PropertyMock, call, patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.response import Response

from api.vistas.acto.listado_actos_view import ActoListAPIView


class TestActoListAPIViewPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ActoListAPIView.as_view()
        self.path = "/api/actos/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.pagination_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_get_lista_actos_flujo_correcto(self, mock_get_todos, mock_pagination_class, mock_serializer_class):
        """
        Test: Flujo correcto de listado de actos (Happy Path Consolidado)
        
        Given: Una petición GET al endpoint de listado de actos.
        When: Se ejecuta la vista genérica ListAPIView.
        Then: La vista delega la obtención del queryset al servicio personalizado, 
            DRF aplica su paginación y serialización internas, y retorna 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock(name="QuerySetCompleto")
        mock_get_todos.return_value = mock_queryset

        mock_paginator_instance = MagicMock()
        mock_paginator_instance.paginate_queryset.return_value = [MagicMock()]
        mock_datos_serializados = [{'id': 1, 'nombre': 'Acto Paginado'}]

        mock_paginator_instance.get_paginated_response.return_value = Response(
            {'results': mock_datos_serializados},
            status=status.HTTP_200_OK
        )
        mock_pagination_class.return_value = mock_paginator_instance

        mock_serializer_instancia = MagicMock()
        mock_serializer_instancia.data = mock_datos_serializados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_get_todos.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], mock_datos_serializados)