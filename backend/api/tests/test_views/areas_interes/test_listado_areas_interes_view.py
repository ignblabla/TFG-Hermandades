import unittest
from unittest.mock import MagicMock, PropertyMock, patch, ANY

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



    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresListView.get_queryset")
    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresSerializer")
    def test_serializer_llamado_con_many_true(self, mock_serializer, mock_get_queryset):
        """
        Test: Se llama a objects.all() (vía get_queryset en DRF)
            Serializer se llama con many=True
        
        Given: Una petición válida a la vista.
        When: La vista procesa el listado.
        Then: El queryset es procesado por el serializador asegurando 
            que el flag many=True esté activo para manejar la lista.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_queryset = [MagicMock()]
        mock_get_queryset.return_value = mock_queryset
        mock_serializer.return_value.data = [{"id": 1}]

        vista = AreaInteresListView()
        vista.request = request
        vista.format_kwarg = None
        vista.kwargs = {}
        vista.serializer_class = mock_serializer

        vista.list(request)

        mock_get_queryset.assert_called_once()

        mock_serializer.assert_called_once_with(mock_queryset, many=True, context=ANY)



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición HTTP GET de un usuario anónimo (sin token/sesión).
        When: La petición pasa por el flujo completo de la vista (as_view).
        Then: La clase IsAuthenticated bloquea el acceso y retorna HTTP 401 Unauthorized.
        """
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        vista_ejecutable = AreaInteresListView.as_view()

        respuesta = vista_ejecutable(request)

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.data["detail"].code, "not_authenticated")



    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresListView.get_queryset")
    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresSerializer")
    def test_queryset_vacio_retorna_lista_vacia(self, mock_serializer, mock_get_queryset):
        """
        Test: queryset vacío
        
        Given: Una base de datos que aún no tiene áreas de interés creadas.
        When: La vista intenta recuperar la lista.
        Then: Retorna un HTTP 200 OK pero con un array vacío.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_get_queryset.return_value = []
        mock_serializer.return_value.data = []

        vista = AreaInteresListView()
        vista.request = request
        vista.format_kwarg = None
        vista.kwargs = {}
        vista.serializer_class = mock_serializer

        respuesta = vista.list(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, [])



    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresListView.get_queryset")
    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresSerializer")
    def test_serializer_falla_propaga_error(self, mock_serializer, mock_get_queryset):
        """
        Test: Serializer falla
        
        Given: Un error interno al inicializar el serializador.
        When: Se llama a la vista.
        Then: La excepción debe subir hasta la capa superior para que DRF lance un 500.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_get_queryset.return_value = [MagicMock()]

        mock_serializer.side_effect = Exception("serializer error")

        vista = AreaInteresListView()
        vista.request = request
        vista.format_kwarg = None
        vista.kwargs = {}
        vista.serializer_class = mock_serializer

        with self.assertRaisesRegex(Exception, "serializer error"):
            vista.list(request)



    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresListView.get_queryset")
    @patch("api.vistas.areas_de_interes.areas_de_interes_view.AreaInteresSerializer")
    def test_acceso_a_data_rompe_propaga_error(self, mock_serializer, mock_get_queryset):
        """
        Test: .data rompe
        
        Given: Un fallo durante el proceso de serialización al acceder a la propiedad .data.
        When: La vista intenta acceder a serializer.data para construir la respuesta.
        Then: La excepción de la propiedad se propaga sin ser enmascarada.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_get_queryset.return_value = [MagicMock()]

        mock_instance = MagicMock()
        type(mock_instance).data = PropertyMock(side_effect=Exception("data error"))
        mock_serializer.return_value = mock_instance

        vista = AreaInteresListView()
        vista.request = request
        vista.format_kwarg = None
        vista.kwargs = {}
        vista.serializer_class = mock_serializer

        with self.assertRaisesRegex(Exception, "data error"):
            vista.list(request)



    def test_configuracion_metadatos_vista(self):
        """
        Test: Se usa queryset definido en clase
            Permiso correcto configurado
            Serializer correcto configurado

        Given: La definición de la clase AreaInteresListView.
        When: Se inspeccionan sus atributos estáticos.
        Then: Debe tener configurado el queryset, el serializador correcto y 
            la protección IsAuthenticated.
        """
        vista = AreaInteresListView()

        self.assertIsNotNone(vista.queryset)

        self.assertIn(IsAuthenticated, AreaInteresListView.permission_classes)

        self.assertEqual(AreaInteresListView.serializer_class, AreaInteresSerializer)