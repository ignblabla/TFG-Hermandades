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

        mock_queryset = MagicMock()
        mock_service.return_value = mock_queryset

        mock_paginator_instancia = MagicMock()
        mock_pagination_class.return_value = mock_paginator_instancia

        pagina_simulada = ["papeleta_1", "papeleta_2"]
        mock_paginator_instancia.paginate_queryset.return_value = pagina_simulada

        mock_serializer_instancia = MagicMock()
        datos_serializados = [{'id': 1}, {'id': 2}]
        mock_serializer_instancia.data = datos_serializados
        mock_serializer_class.return_value = mock_serializer_instancia

        respuesta_paginada_esperada = Response(
            {"count": 2, "next": None, "previous": None, "results": datos_serializados},
            status=status.HTTP_200_OK
        )
        mock_paginator_instancia.get_paginated_response.return_value = respuesta_paginada_esperada

        response = self.view(request)

        mock_service.assert_called_once_with(usuario=self.mock_user)

        mock_serializer_class.assert_called_once_with(pagina_simulada, many=True)

        mock_paginator_instancia.get_paginated_response.assert_called_once_with(datos_serializados)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, respuesta_paginada_esperada.data)



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
        
        mock_serializer_instancia = MagicMock()
        mock_serializer_instancia.data = [{'id': 1}]
        mock_serializer_class.return_value = mock_serializer_instancia
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)



    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_el_servicio_se_llama_con_request_user(self, mock_service):
        """
        Test: El servicio se llama con request.user
        
        Given: Un usuario autenticado solicita su historial.
        When: La vista invoca la lógica de negocio.
        Then: Se valida que el servicio reciba el usuario de la petición como parámetro.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_service.return_value = []
        
        self.view(request)
        
        mock_service.assert_called_once_with(usuario=self.mock_user)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_serializer_se_llama_con_many_true_paginado(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Serializer se llama con many=True (paginado)
        
        Given: Existe una página de resultados.
        When: Se instancia el serializador.
        Then: Se debe incluir el argumento many=True ya que se está procesando una lista de objetos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_service.return_value = MagicMock()
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["item1"]

        mock_paginator.get_paginated_response.return_value = Response([])
        
        mock_pagination_class.return_value = mock_paginator
        
        self.view(request)

        args, kwargs = mock_serializer_class.call_args
        self.assertTrue(kwargs.get('many'))



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_serializer_se_llama_con_many_true_no_paginado(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Serializer se llama con many=True (no paginado)
        
        Given: No hay paginación activa.
        When: Se serializa el queryset directamente.
        Then: Al ser un listado, el serializador debe recibir el parámetro many=True.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_service.return_value = MagicMock()
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        self.view(request)
        
        args, kwargs = mock_serializer_class.call_args
        self.assertTrue(kwargs.get('many'))



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_se_usa_correctamente_get_paginated_response(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Se usa correctamente get_paginated_response
        
        Given: Un flujo donde la paginación está activa (page no es None).
        When: Se obtienen los datos serializados.
        Then: La vista debe llamar al método get_paginated_response del paginador pasando los datos del serializador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()

        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["papeleta1"]
        mock_paginator.get_paginated_response.return_value = Response({"results": []})
        mock_pagination_class.return_value = mock_paginator

        datos_test = [{"id": 1}]
        mock_serializer = MagicMock()
        mock_serializer.data = datos_test
        mock_serializer_class.return_value = mock_serializer
        
        self.view(request)

        mock_paginator.get_paginated_response.assert_called_once_with(datos_test)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_se_instancia_correctamente_el_paginador(self, mock_service, mock_pagination_class):
        """
        Test: Se instancia correctamente el paginador
        
        Given: Una petición GET a la vista.
        When: La vista comienza a procesar la lógica de paginación.
        Then: La clase de paginación configurada (pagination_class) debe ser instanciada (llamada).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()

        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        self.view(request)

        mock_pagination_class.assert_called_once()



    @patch('builtins.print')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_error_en_el_servicio_devuelve_500(self, mock_service, mock_print):
        """
        Test: Error en el servicio (devuelve 500)
        
        Given: El servicio de obtención del historial falla por un error de base de datos.
        When: Se lanza una excepción desde el servicio.
        Then: La vista captura la excepción, imprime el error en consola y retorna un status 500 con el mensaje de detalle configurado.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        error_msg = "Database connection lost"
        mock_service.side_effect = Exception(error_msg)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el historial de papeletas.")

        mock_print.assert_called_once_with(f"Error en MisPapeletasListView: {error_msg}")



    @patch('builtins.print')
    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_error_en_paginate_queryset_devuelve_500(self, mock_service, mock_pagination_class, mock_print):
        """
        Test: Error en paginate_queryset
        
        Given: El servicio funciona pero el motor de paginación falla al procesar el queryset.
        When: paginate_queryset lanza una excepción.
        Then: La vista maneja el error dentro de su bloque catch y retorna un error 500 al cliente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()

        error_msg = "Pagination error"
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.side_effect = Exception(error_msg)
        mock_pagination_class.return_value = mock_paginator
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el historial de papeletas.")

        mock_print.assert_called_once_with(f"Error en MisPapeletasListView: {error_msg}")



    @patch('builtins.print')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_error_en_el_serializer_devuelve_500(self, mock_service, mock_serializer_class, mock_print):
        """
        Test: Error en el serializer
        
        Given: El servicio y el paginador funcionan, pero el serializador falla al procesar los datos.
        When: Se instancia el serializador y este lanza una excepción.
        Then: La vista captura el error, lo imprime y retorna un status 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        error_msg = "Serializer error"
        mock_serializer_class.side_effect = Exception(error_msg)
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el historial de papeletas.")
        mock_print.assert_called_with(f"Error en MisPapeletasListView: {error_msg}")



    @patch('builtins.print')
    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_error_en_get_paginated_response_devuelve_500(self, mock_service, mock_serializer_class, mock_pagination_class, mock_print):
        """
        Test: Error en get_paginated_response
        
        Given: Un flujo de paginación activo donde falla la generación de la respuesta final del paginador.
        When: Se llama a get_paginated_response y se lanza una excepción.
        Then: La vista maneja el error y responde con un status 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()

        mock_serializer_instancia = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instancia
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["item"]
        error_msg = "Response generation failed"
        mock_paginator.get_paginated_response.side_effect = Exception(error_msg)
        mock_pagination_class.return_value = mock_paginator
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mock_print.assert_called_with(f"Error en MisPapeletasListView: {error_msg}")



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
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_queryset_vacio_con_paginacion(self, mock_service, mock_pagination_class):
        """
        Test: Queryset vacío con paginación
        
        Given: El servicio devuelve un queryset vacío pero el paginador está activo.
        When: paginate_queryset devuelve una lista vacía [].
        Then: La vista debe llamar a get_paginated_response con la lista vacía serializada y retornar la estructura de paginación estándar.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = []
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = []
        mock_paginator.get_paginated_response.return_value = Response({"results": []})
        mock_pagination_class.return_value = mock_paginator
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])
        mock_paginator.get_paginated_response.assert_called_once()



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_queryset_vacio_sin_paginacion(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Queryset vacío sin paginación
        
        Given: El paginador no se activa (devuelve None) y el servicio no tiene datos.
        When: Se procesa el flujo alternativo de la vista.
        Then: La vista debe devolver una lista vacía [] con un status 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_queryset_vacio = []
        mock_service.return_value = mock_queryset_vacio
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        mock_serializer_class.assert_called_once_with(mock_queryset_vacio, many=True)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_serializer_devuelve_lista_vacia(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Serializer devuelve lista vacía
        
        Given: Existen datos pero el serializador, por filtros internos o lógica, devuelve una lista vacía.
        When: Se accede a serializer.data.
        Then: La vista debe entregar dicha lista vacía al paginador o en la respuesta directa.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["dato_que_no_se_serializa"]
        mock_paginator.get_paginated_response.side_effect = lambda data: Response({"results": data})
        mock_pagination_class.return_value = mock_paginator
        
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer
        
        response = self.view(request)
        
        self.assertEqual(response.data["results"], [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_verificar_que_no_se_llama_serializer_dos_veces(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Verificar que no se llama serializer dos veces
        
        Given: Un flujo de ejecución estándar (paginado o no).
        When: La vista procesa los datos para devolver la respuesta.
        Then: El serializador debe instanciarse exactamente una vez para optimizar el rendimiento.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        self.view(request)
        
        self.assertEqual(mock_serializer_class.call_count, 1)



    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_verificar_mensaje_error_en_500(self, mock_service):
        """
        Test: Verificar mensaje de error en 500
        
        Given: Una excepción lanzada por cualquier dependencia (ej: el servicio).
        When: Se captura el error en el bloque try/except.
        Then: El cuerpo de la respuesta debe contener la clave 'detail' con el mensaje exacto: 
            "Error al recuperar el historial de papeletas."
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.side_effect = Exception("Fallo inesperado")
        
        response = self.view(request)
        
        mensaje_esperado = "Error al recuperar el historial de papeletas."
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data.get('detail'), mensaje_esperado)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_verificar_status_200_en_flujo_sin_paginacion(self, mock_service, mock_pagination_class):
        """
        Test: Verificar status 200 en flujo sin paginación
        
        Given: Un usuario con pocas papeletas donde el paginador decide no paginar.
        When: paginate_queryset retorna None.
        Then: La vista debe retornar un código de estado 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = [MagicMock()]
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_verificar_que_paginate_queryset_recibe_view_self(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Verificar que paginate_queryset recibe view=self
        
        Given: El proceso estándar de paginación de una APIView.
        When: Se invoca al método paginate_queryset del paginador.
        Then: Se debe pasar la propia instancia de la vista (self) a través del argumento 'view', 
            cumpliendo con el contrato de la clase base de paginación de DRF.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()

        mock_paginator = MagicMock()
        mock_pagination_class.return_value = mock_paginator

        mock_paginator.paginate_queryset.return_value = ["dato"]
        
        mock_serializer_class.return_value = MagicMock(data=[])
        mock_paginator.get_paginated_response.return_value = Response({})

        self.view(request)

        args, kwargs = mock_paginator.paginate_queryset.call_args

        self.assertIsInstance(kwargs.get('view'), MisPapeletasListView)



    @patch.object(MisPapeletasListView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.listado_papeletas_view.get_historial_papeletas_hermano_service')
    def test_verificar_que_el_flujo_paginado_no_usa_response_directamente(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Verificar que el flujo paginado no usa Response directamente
        
        Given: Un escenario donde existen resultados paginados (page no es None).
        When: La vista prepara la respuesta final.
        Then: La vista NO debe instanciar la clase Response manualmente, sino que debe delegar 
            totalmente esa responsabilidad en el método get_paginated_response del paginador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()

        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["pagina_con_datos"]

        respuesta_paginador = Response({"count": 1})
        mock_paginator.get_paginated_response.return_value = respuesta_paginador
        mock_pagination_class.return_value = mock_paginator
        
        with patch('api.vistas.papeleta_sitio.listado_papeletas_view.Response') as mock_response_class:
            response = self.view(request)

            mock_response_class.assert_not_called()
            self.assertEqual(response, respuesta_paginador)