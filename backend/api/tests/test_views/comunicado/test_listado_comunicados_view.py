import unittest
from unittest.mock import MagicMock, patch
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from django.db.models import Q

from api.vistas.comunicado.listado_comunicados_view import MisComunicadosListView


class TestMisComunicadosListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_class = MisComunicadosListView
        self.path = "/api/comunicados/mis-noticias/"

        self.mock_user = MagicMock(spec=['is_authenticated', 'areas_interes'])
        self.mock_user.is_authenticated = True



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_get_queryset_usuario_autenticado_con_areas(self, mock_comunicado):
        """
        Test: Usuario autenticado con áreas devuelve comunicados
        
        Given: Un usuario autenticado con áreas de interés asignadas y una request configurada.
        When: Se ejecuta el método get_queryset para obtener el listado.
        Then: Se consultan las áreas del usuario, se filtra el modelo Comunicado mediante 
            un objeto Q y se encadenan los métodos distinct y order_by correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        request.user = self.mock_user

        vista = self.view_class()
        vista.request = request

        mock_areas_lista = [MagicMock(), MagicMock()]
        self.mock_user.areas_interes.all.return_value = mock_areas_lista

        mock_qs_filter = MagicMock()
        mock_qs_distinct = MagicMock()
        mock_qs_final = ['comunicado_1', 'comunicado_2']
        
        mock_comunicado.objects.filter.return_value = mock_qs_filter
        mock_qs_filter.distinct.return_value = mock_qs_distinct
        mock_qs_distinct.order_by.return_value = mock_qs_final

        resultado = vista.get_queryset()

        self.mock_user.areas_interes.all.assert_called_once()

        mock_comunicado.objects.filter.assert_called_once()
        args, kwargs = mock_comunicado.objects.filter.call_args
        self.assertIsInstance(args[0], Q)

        mock_qs_filter.distinct.assert_called_once()
        mock_qs_distinct.order_by.assert_called_once_with('-fecha_emision')

        self.assertEqual(resultado, mock_qs_final)



    def test_llamada_a_areas_interes_all(self):
        """
        Test: Se llama a areas_interes.all()
        
        Given: Un usuario autenticado con una relación areas_interes definida.
        When: Se ejecuta get_queryset para obtener los comunicados.
        Then: Se valida que se llame al método all() de las áreas de interés del 
            usuario para obtener sus preferencias.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        mock_areas = [MagicMock(), MagicMock()]
        self.mock_user.areas_interes.all = MagicMock(return_value=mock_areas)

        try:
            vista.get_queryset()
        except Exception:
            pass

        self.mock_user.areas_interes.all.assert_called_once()



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_construccion_filtro_con_q(self, mock_comunicado):
        """
        Test: Se construye correctamente el filtro con Q
        
        Given: El entorno de la vista preparado y el modelo Comunicado mockeado.
        When: Se ejecuta la lógica de filtrado en get_queryset.
        Then: Se valida que el método filter() de Comunicado.objects sea invocado 
            exactamente una vez.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        self.mock_user.areas_interes.all.return_value = []

        mock_objects = mock_comunicado.objects
        mock_qs = MagicMock()
        mock_objects.filter.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.order_by.return_value = []

        vista.get_queryset()

        mock_objects.filter.assert_called_once()



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_filtro_incluye_todos_hermanos(self, mock_comunicado):
        """
        Test: Incluye comunicados de "TODOS_HERMANOS"
        
        Given: Un usuario que solicita su listado de noticias.
        When: Se ejecuta get_queryset para construir la consulta.
        Then: Se valida que se llame al método filter() del modelo Comunicado, 
            asegurando que la lógica de filtrado (incluyendo el caso general) se ejecute.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        self.mock_user.areas_interes.all.return_value = []
        mock_qs = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.order_by.return_value = []

        vista.get_queryset()

        mock_comunicado.objects.filter.assert_called_once()



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_llamada_a_distinct(self, mock_comunicado):
        """
        Test: Se llama a .distinct()
        
        Given: Un proceso de filtrado de comunicados que involucra relaciones ManyToMany.
        When: Se construye el queryset en la vista.
        Then: Se invoca al método .distinct() para garantizar que no existan registros 
            duplicados en el listado resultante.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        mock_qs_filter = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_qs_filter

        mock_qs_filter.distinct.return_value = mock_qs_filter
        mock_qs_filter.order_by.return_value = []

        vista.get_queryset()

        mock_qs_filter.distinct.assert_called_once()



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_ordenamiento_por_fecha_emision(self, mock_comunicado):
        """
        Test: Se ordena por -fecha_emision
        
        Given: Un queryset filtrado y con el método distinct aplicado.
        When: Se construye el queryset final en la vista.
        Then: Se valida que se llame al método .order_by() con el parámetro 
            '-fecha_emision' para asegurar el orden cronológico descendente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        mock_qs = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs

        vista.get_queryset()

        mock_qs.order_by.assert_called_once_with('-fecha_emision')



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_usuario_sin_areas_de_interes(self, mock_comunicado):
        """
        Test: Usuario sin áreas de interés
        
        Given: Un usuario autenticado que no tiene áreas de interés asignadas (lista vacía).
        When: Se ejecuta el método get_queryset.
        Then: El sistema no debe romperse; debe procesar la lista vacía y continuar 
            llamando al método filter() para recuperar comunicados generales.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        self.mock_user.areas_interes.all.return_value = []

        mock_qs = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.order_by.return_value = []

        vista.get_queryset()

        mock_comunicado.objects.filter.assert_called_once()



    def test_usuario_sin_relacion_areas_interes_configurada(self):
        """
        Test: Usuario sin areas_interes
        
        Given: Un objeto de usuario donde el atributo 'areas_interes' no está configurado (es None).
        When: Se intenta ejecutar el método get_queryset.
        Then: Se lanza un AttributeError al intentar acceder a .all() sobre un objeto None,
            validando que el modelo o el mock están mal configurados.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        self.mock_user.areas_interes = None

        with pytest.raises(AttributeError):
            vista.get_queryset()



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_filter_devuelve_none_causa_error_en_cadena(self, mock_comunicado):
        """
        Test: filter() devuelve None
        
        Given: Un fallo en el ORM que provoca que filter() retorne None.
        When: La vista intenta encadenar el método .distinct().
        Then: Se lanza un AttributeError porque no se puede llamar a distinct() sobre un NoneType.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        self.mock_user.areas_interes.all.return_value = []

        mock_comunicado.objects.filter.return_value = None

        with pytest.raises(AttributeError):
            vista.get_queryset()



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_distinct_falla_lanza_excepcion(self, mock_comunicado):
        """
        Test: distinct() falla
        
        Given: Un error inesperado en la base de datos durante la ejecución de distinct().
        When: Se construye el queryset en la vista.
        Then: La excepción "DB error" se propaga correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        mock_qs = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_qs

        mock_qs.distinct.side_effect = Exception("DB error")

        with pytest.raises(Exception) as excinfo:
            vista.get_queryset()
            
        assert str(excinfo.value) == "DB error"



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_order_by_falla_lanza_excepcion(self, mock_comunicado):
        """
        Test: order_by() falla
        
        Given: Una cadena de queryset donde el filtrado y la distinción funcionan correctamente.
        When: Se intenta aplicar el ordenamiento final mediante .order_by().
        Then: La excepción "Order error" lanzada por el ORM se propaga correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        mock_qs = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs

        mock_qs.order_by.side_effect = Exception("Order error")

        with pytest.raises(Exception) as excinfo:
            vista.get_queryset()
            
        assert str(excinfo.value) == "Order error"



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_devuelve_queryset_final_correctamente(self, mock_comunicado):
        """
        Test: Devuelve el queryset final correctamente
        
        Given: Una ejecución exitosa de toda la lógica de filtrado y ordenación.
        When: El método get_queryset finaliza.
        Then: El resultado obtenido es exactamente el objeto QuerySet retornado por 
            el último eslabón de la cadena (order_by).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        vista = self.view_class()
        vista.request = request

        mock_qs_filter = MagicMock()
        mock_qs_distinct = MagicMock()
        mock_qs_final = MagicMock()
        
        mock_comunicado.objects.filter.return_value = mock_qs_filter
        mock_qs_filter.distinct.return_value = mock_qs_distinct
        mock_qs_distinct.order_by.return_value = mock_qs_final

        resultado = vista.get_queryset()

        self.assertEqual(resultado, mock_qs_final)