import unittest
from unittest.mock import MagicMock, PropertyMock, patch, ANY

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIRequestFactory

from django.contrib.auth.models import AnonymousUser

from api.vistas.areas_de_interes.areas_de_interes_view import AreaInteresListView
from api.serializadores.areas_de_interes.areas_de_interes_serializer import AreaInteresSerializer


class TestAreaInteresListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/areas-interes/'
        self.user = MagicMock()
        self.user.is_authenticated = True



    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresListView.get_queryset")
    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresSerializer")
    def test_flujo_feliz_lista_devuelta_correctamente(self, mock_serializer, mock_get_queryset):
        """
        Test: Flujo feliz (lista devuelta correctamente)
        
        Given: Una petición GET de un usuario a la lista de áreas.
        When: Se invoca la vista generica ListAPIView.
        Then: Se obtienen los datos del queryset, se pasan 
            por el serializador y retorna la data pura con status 200.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_queryset = [MagicMock(), MagicMock()]
        mock_get_queryset.return_value = mock_queryset

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [{"id": 1, "nombre": "Caridad"}, {"id": 2, "nombre": "Costaleros"}]
        mock_serializer.return_value = mock_serializer_instance

        vista = AreaInteresListView()
        vista.request = request
        vista.format_kwarg = None
        vista.kwargs = {}

        vista.serializer_class = mock_serializer

        respuesta = vista.list(request)

        mock_get_queryset.assert_called_once()

        mock_serializer.assert_called_once_with(mock_queryset, many=True, context=ANY)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [{"id": 1, "nombre": "Caridad"}, {"id": 2, "nombre": "Costaleros"}])



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado bloqueado
        
        Given: Una petición HTTP GET sin credenciales.
        When: La petición intenta acceder a la vista.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso.
        """
        request = self.factory.get(self.url)

        response = AreaInteresListView.as_view()(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])