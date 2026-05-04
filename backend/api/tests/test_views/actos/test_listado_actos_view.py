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
    def test_lista_de_actos_con_paginacion(self, mock_get_todos, mock_pagination_class, mock_serializer_class):
        """
        Test: Lista de actos con paginación
        
        Given: Una petición GET a la lista de actos con resultados suficientes para paginar.
        When: Se ejecuta la vista ActoListAPIView.
        Then: Se llama a ActoService.get_todos_los_actos, se aplica paginate_queryset, 
            se serializa la página resultante (many=True) y se retorna get_paginated_response.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock(name="QuerySetCompleto")
        mock_get_todos.return_value = mock_queryset

        mock_paginator_instance = MagicMock()
        mock_pagina = [MagicMock(name="Acto1")]
        mock_paginator_instance.paginate_queryset.return_value = mock_pagina

        mock_datos_serializados = [{'id': 1, 'nombre': 'Acto Paginado'}]
        mock_paginator_instance.get_paginated_response.return_value = Response(
            {'results': mock_datos_serializados}, status=status.HTTP_200_OK
        )
        mock_pagination_class.return_value = mock_paginator_instance

        mock_serializer_instancia = MagicMock()
        mock_serializer_instancia.data = mock_datos_serializados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_get_todos.assert_called_once()

        mock_serializer_class.assert_called_once_with(mock_pagina, many=True, context=ANY)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], mock_datos_serializados)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.pagination_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_lista_sin_paginacion(self, mock_get_todos, mock_pagination_class, mock_serializer_class):
        """
        Test: Lista sin paginación (page = None)
        
        Given: Una petición GET donde la paginación no se aplica (paginate_queryset retorna None).
        When: Se ejecuta la vista ActoListAPIView.
        Then: El serializador se instancia directamente sobre el queryset completo 
            y se retorna 200 con serializer.data puro.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = [MagicMock(), MagicMock()]
        mock_get_todos.return_value = mock_queryset

        mock_paginator_instance = MagicMock()
        mock_paginator_instance.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator_instance

        mock_serializer_instancia = MagicMock()
        mock_datos_serializados = [{'id': 1}, {'id': 2}]
        mock_serializer_instancia.data = mock_datos_serializados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_get_todos.assert_called_once()

        mock_serializer_class.assert_called_once_with(mock_queryset, many=True, context=ANY)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_datos_serializados)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_uso_correcto_del_serializer_con_many_true(self, mock_get_todos, mock_serializer_class):
        """
        Test: Uso correcto del serializer
        
        Given: Una lista de actos obtenida del servicio.
        When: La vista procesa los datos para la respuesta.
        Then: Se valida que el serializador se instancia con many=True, 
            garantizando que pueda procesar múltiples objetos Acto.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_lista_actos = [MagicMock(), MagicMock()]
        mock_get_todos.return_value = mock_lista_actos

        with patch('api.vistas.acto.listado_actos_view.PaginacionDoceElementos.paginate_queryset', return_value=None):
            self.view(request)

        mock_serializer_class.assert_called_once_with(
            mock_lista_actos, 
            many=True, 
            context=ANY
        )



    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_servicio_llamado_correctamente_para_obtener_actos(self, mock_get_todos):
        """
        Test: Servicio llamado correctamente
        
        Given: Una petición GET al listado de actos.
        When: Se ejecuta la lógica de la vista.
        Then: Se verifica que se invoca exactamente una vez al método 
            ActoService.get_todos_los_actos() para recuperar la información.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_get_todos.return_value = MagicMock()

        self.view(request)

        mock_get_todos.assert_called_once()



    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_get_error_en_servicio_propaga_excepcion(self, mock_get_todos):
        """
        Test: Error en ActoService.get_todos_los_actos
        
        Given: Un fallo en la capa de servicios (ej. error de base de datos).
        When: La vista intenta obtener el queryset.
        Then: La excepción se propaga, permitiendo que DRF la maneje.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_todos.side_effect = Exception("Error de conexión con el servicio")

        with self.assertRaises(Exception) as cm:
            self.view(request)
        
        self.assertEqual(str(cm.exception), "Error de conexión con el servicio")



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_get_error_en_serializer_propaga_excepcion(self, mock_get_todos, mock_serializer_class):
        """
        Test: Error en serializer
        
        Given: Un queryset válido devuelto por el servicio.
        When: El serializador falla al instanciarse o al acceder a la propiedad .data.
        Then: La excepción se propaga correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_todos.return_value = [MagicMock()]

        mock_serializer_instancia = MagicMock()
        type(mock_serializer_instancia).data = PropertyMock(side_effect=TypeError("Error de tipos en serialización"))
        mock_serializer_class.return_value = mock_serializer_instancia

        with self.assertRaises(TypeError):
            self.view(request)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.pagination_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_get_error_en_paginacion_paginate_queryset_propaga_excepcion(self, mock_get_todos, mock_pagination_class):
        """
        Test: Error en paginación (paginate_queryset)
        
        Given: Una petición para listar actos.
        When: El método paginate_queryset del paginador lanza un error.
        Then: La vista no captura el error y lo propaga.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_todos.return_value = MagicMock()
        
        mock_paginator_instance = MagicMock()
        mock_paginator_instance.paginate_queryset.side_effect = ValueError("Parámetros de paginación inválidos")
        mock_pagination_class.return_value = mock_paginator_instance

        with self.assertRaises(ValueError):
            self.view(request)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.pagination_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_get_error_en_get_paginated_response_propaga_excepcion(self, mock_get_todos, mock_pagination_class, mock_serializer_class):
        """
        Test: Error en get_paginated_response
        
        Given: Datos serializados correctamente.
        When: El paginador falla al construir la respuesta estructurada (count, next, previous).
        Then: Se propaga la excepción.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_todos.return_value = MagicMock()
        
        mock_paginator_instance = MagicMock()
        mock_paginator_instance.paginate_queryset.return_value = [MagicMock()]
        mock_paginator_instance.get_paginated_response.side_effect = RuntimeError("Fallo al generar respuesta paginada")
        mock_pagination_class.return_value = mock_paginator_instance

        with self.assertRaises(RuntimeError):
            self.view(request)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_get_servicio_devuelve_lista_vacia_retorna_lista_vacia_serializada(self, mock_get_todos, mock_serializer_class):
        """
        Test: Servicio devuelve lista vacía
        
        Given: El servicio ActoService retorna una lista vacía o QuerySet vacío.
        When: La vista procesa la petición sin paginación (para simplificar el flujo).
        Then: El serializador recibe la lista vacía y la vista retorna [] con status 200.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_get_todos.return_value = []

        mock_serializer_instancia = MagicMock()
        mock_serializer_instancia.data = []
        mock_serializer_class.return_value = mock_serializer_instancia

        with patch('api.vistas.acto.listado_actos_view.PaginacionDoceElementos.paginate_queryset', return_value=None):
            response = self.view(request)

        mock_serializer_class.assert_called_once_with([], many=True, context=ANY)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_get_servicio_devuelve_none_pasa_valor_al_serializer(self, mock_get_todos, mock_serializer_class):
        """
        Test: Servicio devuelve None
        
        Given: El servicio devuelve None (valor inesperado para un queryset).
        When: La vista intenta procesar los datos.
        Then: El valor None se propaga al serializador (si no hay paginación), 
            lo cual suele resultar en un error de serialización o respuesta vacía.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_get_todos.return_value = None
        
        with patch('api.vistas.acto.listado_actos_view.PaginacionDoceElementos.paginate_queryset', return_value=None):
            self.view(request)

        mock_serializer_class.assert_called_once_with(None, many=True, context=ANY)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.pagination_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_transversal_flujo_con_paginacion_activa(self, mock_get_todos, mock_pagination_class, mock_serializer_class):
        """
        Test: Flujo con paginación activa
        
        Given: Una petición exitosa con datos suficientes.
        When: Se ejecuta la vista.
        Then: Se verifica el orden estricto de llamadas y que la vista retorne una Response válida.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_qs = MagicMock(name="QS")
        mock_get_todos.return_value = mock_qs

        mock_paginator = MagicMock(name="Paginator")
        mock_pagina = [MagicMock(name="Acto1")]
        mock_paginator.paginate_queryset.return_value = mock_pagina
        
        mock_datos_finales = {'results': [{'id': 1}]}
        mock_paginator.get_paginated_response.return_value = Response(mock_datos_finales)
        mock_pagination_class.return_value = mock_paginator

        mock_serializer_instancia = MagicMock(name="SerializerInstance")
        mock_serializer_instancia.data = mock_datos_finales
        mock_serializer_class.return_value = mock_serializer_instancia

        manager = MagicMock()
        manager.attach_mock(mock_get_todos, 'servicio')
        manager.attach_mock(mock_paginator.paginate_queryset, 'paginar')
        manager.attach_mock(mock_serializer_class, 'clase_serializer')
        manager.attach_mock(mock_paginator.get_paginated_response, 'respuesta_paginada')

        response = self.view(request)

        expected_calls = [
            call.servicio(),
            call.paginar(mock_qs, ANY, view=ANY),
            call.clase_serializer(mock_pagina, many=True, context=ANY),
            call.respuesta_paginada(mock_serializer_instancia.data)
        ]
        
        manager.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(response.status_code, 200)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.pagination_class')
    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_transversal_flujo_sin_paginacion(self, mock_get_todos, mock_pagination_class, mock_serializer_class):
        """
        Test: Flujo sin paginación
        
        Given: Una petición donde el paginador devuelve None (ej: desactivado).
        When: Se ejecuta la vista.
        Then: El flujo salta la respuesta paginada y el serializador recibe el queryset original.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_qs = MagicMock(name="QS")
        mock_get_todos.return_value = mock_qs
        
        mock_paginator = MagicMock(name="Paginator")
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator

        self.view(request)

        mock_serializer_class.assert_called_once_with(mock_qs, many=True, context=ANY)
        mock_paginator.get_paginated_response.assert_not_called()



    @patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos')
    def test_transversal_servicio_llamado_exactamente_una_vez(self, mock_get_todos):
        """
        Test: Servicio llamado exactamente una vez
        
        Given: Una petición GET estándar.
        When: Se procesa la vista.
        Then: No hay llamadas redundantes a ActoService.get_todos_los_actos, 
            optimizando el acceso a datos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get_todos.return_value = MagicMock()

        self.view(request)

        self.assertEqual(mock_get_todos.call_count, 1)



    @patch('api.vistas.acto.listado_actos_view.ActoListAPIView.serializer_class')
    def test_transversal_uso_correcto_de_many_true(self, mock_serializer_class):
        """
        Test: Uso correcto de many=True
        
        Given: Datos devueltos por la capa de servicio/paginación.
        When: Se instancia el serializador.
        Then: Se garantiza que many=True está presente para evitar errores de 
            mapeo de tipos en listas o querysets.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        with patch('api.vistas.acto.listado_actos_view.ActoService.get_todos_los_actos', return_value=[]):
            self.view(request)

        _, kwargs = mock_serializer_class.call_args
        self.assertTrue(kwargs.get('many'))