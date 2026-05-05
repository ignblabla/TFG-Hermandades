import unittest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory

from api.vistas.puesto.listado_puesto_view import PuestosPorActoListView


class TestPuestosPorActoListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.acto_id = 1
        self.url = f'/actos/{self.acto_id}/puestos/'
        self.user = MagicMock()

        self.request = self.factory.get(self.url)
        self.request.user = self.user

        self.vista = PuestosPorActoListView()



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_devuelve_respuesta_paginada_correctamente(self, mock_obtener_puestos, mock_paginator_class, mock_serializer_class):
        """
        Test: Devuelve respuesta paginada correctamente
        
        Given: Una solicitud GET válida para listar los puestos de un acto específico.
        When: Se procesa la petición a través del método get de la vista PuestosPorActoListView.
        Then: El servicio recupera el queryset, el paginador recorta los resultados, el serializador los transforma y se retorna la respuesta paginada formateada.
        """
        mock_queryset = MagicMock()
        mock_obtener_puestos.return_value = mock_queryset

        mock_paginator_instance = MagicMock()
        mock_paginator_class.return_value = mock_paginator_instance

        puestos_paginados_mock = [MagicMock(), MagicMock()]
        mock_paginator_instance.paginate_queryset.return_value = puestos_paginados_mock

        mock_serializer_instance = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instance

        mock_serializer_instance.data = [{'id': 1, 'nombre': 'Puesto 1'}, {'id': 2, 'nombre': 'Puesto 2'}]

        mock_response = MagicMock()
        mock_paginator_instance.get_paginated_response.return_value = mock_response

        resultado = self.vista.get(self.request, acto_id=self.acto_id)

        mock_obtener_puestos.assert_called_once_with(acto_id=self.acto_id)

        mock_paginator_class.assert_called_once()
        mock_paginator_instance.paginate_queryset.assert_called_once_with(mock_queryset, self.request, view=self.vista)

        mock_serializer_class.assert_called_once_with(puestos_paginados_mock, many=True)

        mock_paginator_instance.get_paginated_response.assert_called_once_with(mock_serializer_instance.data)

        self.assertEqual(resultado, mock_response)



    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    def test_llama_al_servicio_con_acto_id_correcto(self, mock_paginador, mock_obtener_puestos):
        """
        Test: Llama al servicio con acto_id correcto
        
        Given: Un acto_id extraído de los parámetros de la URL.
        When: Se ejecuta el método GET de la vista.
        Then: El servicio obtener_puestos_por_acto debe ser invocado exactamente con ese acto_id.
        """
        mock_obtener_puestos.return_value = MagicMock()

        self.vista.get(self.request, acto_id=self.acto_id)

        mock_obtener_puestos.assert_called_once_with(acto_id=self.acto_id)



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_serializer_se_llama_con_many_true(self, mock_puestos, mock_paginador, mock_serializer):
        """
        Test: Serializer se llama con many=True
        
        Given: Una lista de puestos obtenida tras la paginación.
        When: Se instancie el serializador.
        Then: Se debe pasar el argumento many=True para asegurar el procesamiento correcto de múltiples instancias del modelo Puesto.
        """
        lista_paginada = [MagicMock(), MagicMock()]
        mock_paginador.return_value.paginate_queryset.return_value = lista_paginada

        self.vista.get(self.request, acto_id=self.acto_id)

        mock_serializer.assert_called_once_with(lista_paginada, many=True)



    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_usa_correctamente_paginate_queryset(self, mock_puestos, mock_paginador_class):
        """
        Test: Usa correctamente paginate_queryset
        
        Given: Un queryset de puestos y el objeto de la petición (request).
        When: Se inicia el proceso de paginación.
        Then: Se debe llamar a paginate_queryset pasando el queryset original, el objeto request y la instancia de la vista actual.
        """
        mock_qs = MagicMock()
        mock_puestos.return_value = mock_qs
        mock_paginador_instancia = mock_paginador_class.return_value

        self.vista.get(self.request, acto_id=self.acto_id)

        mock_paginador_instancia.paginate_queryset.assert_called_once_with(
            mock_qs, self.request, view=self.vista
        )



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_devuelve_exactamente_get_paginated_response_con_data(self, mock_puestos, mock_paginador, mock_serializer):
        """
        Test: Devuelve exactamente get_paginated_response(serializer.data)
        
        Given: Los datos transformados por el serializador.
        When: Se construye la respuesta final.
        Then: La vista debe retornar el objeto Response que genera el método get_paginated_response del paginador, usando los datos serializados.
        """
        datos_serializados = [{'test': 'data'}]
        mock_serializer.return_value.data = datos_serializados
        
        mock_paginador_instancia = mock_paginador.return_value
        mock_response_final = MagicMock()
        mock_paginador_instancia.get_paginated_response.return_value = mock_response_final

        resultado = self.vista.get(self.request, acto_id=self.acto_id)

        mock_paginador_instancia.get_paginated_response.assert_called_once_with(datos_serializados)
        self.assertIs(resultado, mock_response_final)



    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_error_en_el_servicio_lanza_excepcion(self, mock_servicio):
        """
        Test: Error en el servicio
        
        Given: Un fallo inesperado en la lógica del servicio obtener_puestos_por_acto.
        When: La vista intenta recuperar los puestos del acto.
        Then: La excepción se propaga, interrumpiendo la ejecución de la vista.
        """
        mock_servicio.side_effect = Exception("Error de base de datos en el servicio")

        with self.assertRaises(Exception) as context:
            self.vista.get(self.request, acto_id=self.acto_id)
        self.assertEqual(str(context.exception), "Error de base de datos en el servicio")



    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination.paginate_queryset')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_error_en_paginate_queryset_lanza_excepcion(self, mock_servicio, mock_paginate):
        """
        Test: Error en paginate_queryset
        
        Given: Un queryset válido retornado por el servicio.
        When: El paginador falla al intentar segmentar los resultados (ej. parámetros de query inválidos).
        Then: La excepción lanzada por el paginador es capturada por el test.
        """
        mock_servicio.return_value = MagicMock()
        mock_paginate.side_effect = Exception("Fallo en la lógica de paginación")

        with self.assertRaises(Exception) as context:
            self.vista.get(self.request, acto_id=self.acto_id)
        self.assertEqual(str(context.exception), "Fallo en la lógica de paginación")



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination.paginate_queryset')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_error_en_serializer_lanza_excepcion(self, mock_servicio, mock_paginate, mock_serializer):
        """
        Test: Error en serializer
        
        Given: Resultados paginados listos para procesar.
        When: El serializador encuentra un error de integridad o de mapeo en los datos.
        Then: Se propaga la excepción generada durante la instanciación o acceso a .data.
        """
        mock_servicio.return_value = MagicMock()
        mock_paginate.return_value = [MagicMock()]
        mock_serializer.side_effect = Exception("Error de mapeo en el serializador")

        with self.assertRaises(Exception) as context:
            self.vista.get(self.request, acto_id=self.acto_id)
        self.assertEqual(str(context.exception), "Error de mapeo en el serializador")



    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination.get_paginated_response')
    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination.paginate_queryset')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_error_en_get_paginated_response_lanza_excepcion(self, mock_servicio, mock_paginate, mock_serializer, mock_get_response):
        """
        Test: Error en get_paginated_response
        
        Given: Datos serializados correctamente.
        When: El paginador falla al construir el objeto Response final (ej. error en headers o metadatos).
        Then: La vista no devuelve una respuesta y propaga el error.
        """
        mock_servicio.return_value = MagicMock()
        mock_paginate.return_value = []
        mock_serializer.return_value.data = []
        mock_get_response.side_effect = Exception("Fallo al construir respuesta paginada")

        with self.assertRaises(Exception) as context:
            self.vista.get(self.request, acto_id=self.acto_id)
        self.assertEqual(str(context.exception), "Fallo al construir respuesta paginada")



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_paginate_queryset_devuelve_none(self, mock_servicio, mock_paginador_class, mock_serializer):
        """
        Test: paginate_queryset devuelve None
        
        Given: Un paginador que decide no paginar (devuelve None).
        When: Se procesa la petición en la vista.
        Then: El serializador se instancia con None (o la respuesta del paginador) y se llama a get_paginated_response, 
            verificando que la vista no se rompe ante este comportamiento del paginador.
        """
        mock_servicio.return_value = MagicMock()
        mock_paginador_instancia = mock_paginador_class.return_value
        mock_paginador_instancia.paginate_queryset.return_value = None

        self.vista.get(self.request, acto_id=self.acto_id)

        mock_serializer.assert_called_once_with(None, many=True)
        mock_paginador_instancia.get_paginated_response.assert_called_once()



    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_queryset_vacio(self, mock_servicio, mock_paginador_class):
        """
        Test: Queryset vacío
        
        Given: El servicio devuelve una lista vacía (sin puestos).
        When: Se intenta paginar.
        Then: El paginador recibe la lista vacía y la vista continúa su flujo normal hacia la respuesta paginada vacía.
        """
        mock_servicio.return_value = []
        mock_paginador_instancia = mock_paginador_class.return_value

        self.vista.get(self.request, acto_id=self.acto_id)

        mock_paginador_instancia.paginate_queryset.assert_called_once_with(
            [], self.request, view=self.vista
        )



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_verificar_que_el_serializer_recibe_exactamente_puestos_paginados(self, mock_servicio, mock_paginador_class, mock_serializer):
        """
        Test: Verificar que el serializer recibe exactamente puestos_paginados
        
        Given: Un conjunto de resultados recortado por el paginador.
        When: Se llega al paso de serialización.
        Then: Se asegura que el serializador no recibe el queryset original, sino específicamente el objeto devuelto por paginate_queryset.
        """
        queryset_original = MagicMock(name="QS_Original")
        puestos_paginados = [MagicMock(name="Puesto_Pagina_1")]
        
        mock_servicio.return_value = queryset_original
        mock_paginador_class.return_value.paginate_queryset.return_value = puestos_paginados

        self.vista.get(self.request, acto_id=self.acto_id)

        args, kwargs = mock_serializer.call_args
        self.assertIs(args[0], puestos_paginados)
        self.assertIsNot(args[0], queryset_original)



    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    def test_verificar_que_se_instancia_el_paginador_correctamente(self, mock_paginador_class):
        """
        Test: Verificar que se instancia el paginador correctamente
        
        Given: Una petición GET a la vista.
        When: Se ejecuta el método get.
        Then: Se debe crear una nueva instancia de la clase de paginación StandardResultsSetPagination.
        """
        with patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto'):
            self.vista.get(self.request, acto_id=self.acto_id)

        mock_paginador_class.assert_called_once()