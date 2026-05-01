from unittest.mock import patch, MagicMock
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from api.vistas.hermano.hermano_list_view import HermanoListView


class TestHermanoListView(TestCase):

    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_respuesta_paginada_correcta(
        self, 
        mock_get_listado_service, 
        mock_paginacion_class, 
        mock_serializer_class
    ):
        """
        Test: Respuesta paginada correcta
        
        Given: Un usuario autenticado que realiza una petición GET a la vista.
        When: El servicio devuelve el queryset de hermanos y el paginador genera una página con datos.
        Then: Se pagina el resultado, se serializa con many=True y se retorna la respuesta paginada.
        """
        vista = HermanoListView()

        vista.pagination_class = mock_paginacion_class

        mock_request = MagicMock()
        mock_user = MagicMock()
        mock_request.user = mock_user

        mock_queryset = MagicMock()
        mock_get_listado_service.return_value = mock_queryset

        mock_paginador_instancia = MagicMock()
        mock_paginacion_class.return_value = mock_paginador_instancia
        
        mock_pagina = ['hermano1', 'hermano2']
        mock_paginador_instancia.paginate_queryset.return_value = mock_pagina
        
        mock_respuesta_paginada = MagicMock(spec=Response)
        mock_paginador_instancia.get_paginated_response.return_value = mock_respuesta_paginada

        mock_serializer_instancia = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instancia
        mock_serializer_instancia.data = [{'id': 1, 'nombre': 'Hermano 1'}]

        response = vista.get(mock_request)

        mock_get_listado_service.assert_called_once_with(usuario_solicitante=mock_user)

        mock_paginador_instancia.paginate_queryset.assert_called_once_with(mock_queryset, mock_request)

        mock_serializer_class.assert_called_once_with(mock_pagina, many=True)

        mock_paginador_instancia.get_paginated_response.assert_called_once_with(mock_serializer_instancia.data)

        self.assertEqual(response, mock_respuesta_paginada)



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_respuesta_sin_paginacion(
        self, 
        mock_get_listado_service, 
        mock_paginacion_class, 
        mock_serializer_class
    ):
        """
        Test: Respuesta sin paginación (page = None)
        
        Given: Un queryset de hermanos válido.
        When: El paginador devuelve None al intentar paginar el queryset.
        Then: No se usa get_paginated_response y se retorna una Response estándar con status 200.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_paginacion_class

        mock_request = MagicMock()
        mock_user = MagicMock()
        mock_request.user = mock_user

        mock_queryset = MagicMock()
        mock_get_listado_service.return_value = mock_queryset
        
        mock_paginador_instancia = MagicMock()
        mock_paginacion_class.return_value = mock_paginador_instancia
        mock_paginador_instancia.paginate_queryset.return_value = None

        mock_serializer_instancia = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instancia
        mock_serializer_instancia.data = [{'id': 1, 'nombre': 'Hermano Solo'}]

        response = vista.get(mock_request)

        mock_paginador_instancia.paginate_queryset.assert_called_once_with(mock_queryset, mock_request)
        mock_paginador_instancia.get_paginated_response.assert_not_called()

        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_serializer_instancia.data)



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_serializer_recibe_many_true(
        self, 
        mock_get_listado_service, 
        mock_paginacion_class, 
        mock_serializer_class
    ):
        """
        Test: Serializer recibe correctamente many=True
        
        Given: Un queryset obtenido del servicio.
        When: Se instancia el serializador para procesar los datos (con o sin paginación).
        Then: El serializador se instancia siempre con el argumento many=True para manejar múltiples objetos.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_paginacion_class
        
        mock_request = MagicMock()
        mock_queryset = MagicMock()
        mock_get_listado_service.return_value = mock_queryset

        mock_paginador_instancia = MagicMock()
        mock_paginacion_class.return_value = mock_paginador_instancia
        mock_paginador_instancia.paginate_queryset.return_value = None

        vista.get(mock_request)

        args, kwargs = mock_serializer_class.call_args
        self.assertTrue(kwargs.get('many') or (len(args) > 1 and args[1] is True))



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_datos_serializer_usados_en_respuesta(
        self, 
        mock_get_listado_service, 
        mock_paginacion_class, 
        mock_serializer_class
    ):
        """
        Test: Datos del serializer usados en la respuesta
        
        Given: Un conjunto de datos serializados.
        When: La vista genera la respuesta HTTP.
        Then: El cuerpo de la respuesta (response.data) contiene exactamente lo que el serializador procesó.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_paginacion_class
        
        mock_request = MagicMock()
        mock_get_listado_service.return_value = MagicMock()

        mock_paginador_instancia = MagicMock()
        mock_paginacion_class.return_value = mock_paginador_instancia
        mock_paginador_instancia.paginate_queryset.return_value = None

        datos_esperados = [
            {'id': 101, 'alias': 'Hermano Test'},
            {'id': 102, 'alias': 'Hermano Mock'}
        ]
        mock_serializer_instancia = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instancia
        mock_serializer_instancia.data = datos_esperados

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_invoca_servicio_con_usuario_correcto(
        self, 
        mock_get_listado_service, 
        mock_paginacion_class
    ):
        """
        Test: El servicio se invoca con el usuario correcto
        
        Given: Una petición realizada por un usuario específico (request.user).
        When: La vista procesa la solicitud GET.
        Then: Se llama al servicio get_listado_hermanos_service pasando exactamente 
            ese usuario en el argumento 'usuario_solicitante'.
        """
        vista = HermanoListView()

        vista.pagination_class = mock_paginacion_class

        mock_usuario_especifico = MagicMock()
        mock_usuario_especifico.id = 99
        mock_usuario_especifico.email = "test@example.com"
        
        mock_request = MagicMock()
        mock_request.user = mock_usuario_especifico

        mock_get_listado_service.return_value = MagicMock()

        vista.get(mock_request)

        mock_get_listado_service.assert_called_once_with(
            usuario_solicitante=mock_usuario_especifico
        )



    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_permiso_denegado_retorna_403(self, mock_get_listado_service):
        """
        Test: El servicio lanza PermissionDenied → respuesta 403
        
        Given: Un usuario que no tiene permisos suficientes según la lógica del servicio.
        When: get_listado_hermanos_service lanza una excepción PermissionDenied.
        Then: La vista captura la excepción y retorna una respuesta con status 403 
            y el mensaje de error en el campo 'detail'.
        """
        vista = HermanoListView()
        mock_request = MagicMock()
        
        mensaje_error = "No tienes permiso para ver este listado."
        mock_get_listado_service.side_effect = PermissionDenied(mensaje_error)

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], mensaje_error)



    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_error_generico_retorna_500(self, mock_get_listado_service):
        """
        Test: El servicio lanza excepción genérica → respuesta 500
        
        Given: Un fallo inesperado en el servicio (ej. error de base de datos o bug).
        When: El servicio lanza una excepción de tipo Exception.
        Then: La vista captura el error y retorna un status 500 con un mensaje amigable 
            y el detalle técnico del error.
        """
        vista = HermanoListView()
        mock_request = MagicMock()
        
        error_tecnico = "Database connection lost"
        mock_get_listado_service.side_effect = Exception(error_tecnico)

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el listado.")
        self.assertEqual(response.data['error'], error_tecnico)



    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_error_en_paginacion_retorna_500(self, mock_get_listado_service, mock_pag_class):
        """
        Test: Error en paginate_queryset → respuesta 500
        
        Given: Un servicio que devuelve datos correctamente.
        When: El método paginate_queryset del paginador lanza una excepción inesperada.
        Then: La vista captura el error, no rompe la ejecución y retorna un status 500.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_pag_class
        mock_request = MagicMock()

        mock_get_listado_service.return_value = MagicMock()

        mock_pag_instancia = MagicMock()
        mock_pag_class.return_value = mock_pag_instancia

        mock_pag_instancia.paginate_queryset.side_effect = Exception("Error interno del paginador")

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el listado.")
        self.assertIn("Error interno del paginador", response.data['error'])



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_error_en_serializer_retorna_500(self, mock_get_listado_service, mock_serializer_class):
        """
        Test: Error en serializer → respuesta 500
        
        Given: Un queryset válido obtenido del servicio.
        When: La instanciación o el acceso a .data del serializador lanza una excepción.
        Then: La vista captura la excepción y retorna una respuesta con status 500.
        """
        vista = HermanoListView()
        mock_request = MagicMock()
        
        mock_get_listado_service.return_value = MagicMock()

        mock_serializer_class.side_effect = Exception("Atributo de modelo no encontrado en serialización")

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el listado.")
        self.assertIn("Atributo de modelo no encontrado en serialización", response.data['error'])



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_error_en_get_paginated_response_retorna_500(
        self, 
        mock_get_listado_service, 
        mock_pag_class, 
        mock_serializer_class
    ):
        """
        Test: Error en get_paginated_response → respuesta 500
        
        Given: Un flujo de paginación que ha funcionado correctamente hasta el paso final.
        When: El método get_paginated_response lanza una excepción.
        Then: La vista captura la excepción y retorna un status 500.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_pag_class
        mock_request = MagicMock()
        
        mock_get_listado_service.return_value = MagicMock()
        
        mock_pag_instancia = MagicMock()
        mock_pag_class.return_value = mock_pag_instancia

        mock_pag_instancia.paginate_queryset.return_value = ['item']

        mock_pag_instancia.get_paginated_response.side_effect = Exception("Error al construir JSON paginado")

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al recuperar el listado.")
        self.assertIn("Error al construir JSON paginado", response.data['error'])



    def setUp(self):
        self.factory = RequestFactory()
        self.vista = HermanoListView.as_view()



    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_usuario_no_autenticado_bloqueado(self, mock_service):
        """
        Test: Usuario no autenticado (control de permisos de la vista)
        
        Given: Una petición de un usuario anónimo (sin sesión).
        When: Se intenta acceder al endpoint GET de la vista.
        Then: DRF bloquea el acceso con status 401 o 403 y el servicio de negocio no se llama.
        """

        request = self.factory.get('/api/hermanos/')

        request.user = AnonymousUser()

        response = self.vista(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        mock_service.assert_not_called()



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_get_servicio_devuelve_queryset_vacio(self, mock_service, mock_pag_class, mock_serializer):
        """
        Test: El servicio devuelve queryset vacío
        
        Given: Un servicio que no encuentra hermanos (queryset vacío).
        When: Se realiza la petición GET.
        Then: La respuesta es válida, status 200, y contiene una lista vacía (ya sea paginada o directa).
        """
        vista = HermanoListView()
        vista.pagination_class = mock_pag_class
        mock_request = MagicMock()

        mock_service.return_value = []

        mock_pag_instancia = MagicMock()
        mock_pag_class.return_value = mock_pag_instancia
        mock_pag_instancia.paginate_queryset.return_value = []

        mock_serializer_instancia = MagicMock()
        mock_serializer.return_value = mock_serializer_instancia
        mock_serializer_instancia.data = []

        mock_pag_instancia.get_paginated_response.return_value = Response([])

        response = vista.get(mock_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_verificacion_flujo_completo_con_paginacion(self, mock_service, mock_pag_class, mock_ser_class):
        """
        Test: Verificación de flujo completo con paginación
        
        Given: Un entorno mockeado con un manager para rastrear el orden.
        When: Se realiza una petición y el queryset se pagina correctamente.
        Then: La vista ejecuta el servicio, instancia el paginador, pagina los resultados, serializa la página y retorna la respuesta en el orden exacto.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_pag_class
        mock_request = MagicMock()

        manager = MagicMock()
        manager.attach_mock(mock_service, 'servicio')
        manager.attach_mock(mock_pag_class, 'paginador_init')
        manager.attach_mock(mock_ser_class, 'serializer')

        mock_pag_instancia = mock_pag_class.return_value
        mock_pag_instancia.paginate_queryset.return_value = ['pagina']

        vista.get(mock_request)

        nombres_llamadas = [call[0] for call in manager.mock_calls]
        
        self.assertEqual(nombres_llamadas[0], 'servicio')
        self.assertEqual(nombres_llamadas[1], 'paginador_init')
        self.assertEqual(nombres_llamadas[2], 'paginador_init().paginate_queryset')
        self.assertEqual(nombres_llamadas[3], 'serializer')
        self.assertEqual(nombres_llamadas[4], 'paginador_init().get_paginated_response')



    @patch('api.vistas.hermano.hermano_list_view.HermanoListadoSerializer')
    @patch('api.vistas.hermano.hermano_list_view.PaginacionDiezElementos')
    @patch('api.vistas.hermano.hermano_list_view.get_listado_hermanos_service')
    def test_verificacion_flujo_completo_sin_paginacion(self, mock_service, mock_pag_class, mock_ser_class):
        """
        Test: Verificación de flujo completo sin paginación
        
        Given: Un entorno mockeado con un manager para rastrear el orden.
        When: Se realiza una petición y paginate_queryset retorna None.
        Then: La vista ejecuta el servicio, intenta paginar sin éxito y serializa directamente el queryset original en el orden exacto.
        """
        vista = HermanoListView()
        vista.pagination_class = mock_pag_class
        mock_request = MagicMock()
        
        manager = MagicMock()
        manager.attach_mock(mock_service, 'servicio')
        manager.attach_mock(mock_pag_class.return_value.paginate_queryset, 'paginador_exec')
        manager.attach_mock(mock_ser_class, 'serializer')

        mock_pag_class.return_value.paginate_queryset.return_value = None

        vista.get(mock_request)

        nombres_llamadas = [call[0] for call in manager.mock_calls]

        self.assertEqual(nombres_llamadas[0], 'servicio')
        self.assertEqual(nombres_llamadas[1], 'paginador_exec')
        self.assertEqual(nombres_llamadas[2], 'serializer')