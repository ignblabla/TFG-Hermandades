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



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_usuario_autenticado_y_esadmin_true_acceso_permitido(self, mock_service):
        """
        Test: Usuario autenticado y esAdmin=True → acceso permitido
        
        Given: Un usuario que está autenticado y tiene el atributo esAdmin a True.
        When: Realiza una petición GET a la vista de asistentes leídos.
        Then: La clase de permisos (EsAdminHermano) permite el acceso y la vista retorna un status 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_service.return_value = []

        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once_with(self.acto_id)



    def test_usuario_autenticado_pero_no_es_admin_acceso_denegado(self):
        """
        Test: Usuario autenticado pero no es admin → acceso denegado
        
        Given: Un usuario autenticado cuyo atributo 'esAdmin' es False.
        When: Intenta acceder a la vista de asistentes leídos.
        Then: La clase de permiso retorna False y la respuesta es 403 Forbidden.
        """
        request = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = False
        force_authenticate(request, user=mock_user)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    def test_usuario_no_autenticado_acceso_denegado(self):
        """
        Test: Usuario no autenticado → acceso denegado
        
        Given: Un usuario que no ha iniciado sesión (is_authenticated = False).
        When: Intenta realizar la petición GET.
        Then: La vista deniega el acceso con status 403 Forbidden.
        """
        request = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated'])
        mock_user.is_authenticated = False
        force_authenticate(request, user=mock_user)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    def test_usuario_sin_atributo_esadmin_acceso_denegado(self):
        """
        Test: Usuario sin atributo esAdmin → acceso denegado
        
        Given: Un usuario autenticado que no posee el atributo 'esAdmin' en su modelo.
        When: Se evalúa el permiso mediante getattr(request.user, 'esAdmin', False).
        Then: Al no existir el atributo, se asume False y se retorna 403 Forbidden.
        """
        request = self.factory.get(self.path)

        mock_user = MagicMock(spec=['is_authenticated'])
        mock_user.is_authenticated = True

        if hasattr(mock_user, 'esAdmin'):
            del mock_user.esAdmin
            
        force_authenticate(request, user=mock_user)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_devuelve_respuesta_paginada_correctamente(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Devuelve respuesta paginada correctamente
        
        Given: Un acto con más de 20 asistentes.
        When: Se solicita la lista y el paginador genera una página.
        Then: La vista devuelve la respuesta estructurada del paginador (get_paginated_response).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        # Mocks
        mock_service.return_value = MagicMock() # Queryset original
        mock_paginator = MagicMock()
        mock_pagination_class.return_value = mock_paginator
        
        # Simulamos que hay página
        page_data = ["asistente1", "asistente2"]
        mock_paginator.paginate_queryset.return_value = page_data
        
        # Serializador
        datos_serializados = [{"nombre": "Hermano Test"}]
        mock_serializer = MagicMock()
        mock_serializer.data = datos_serializados
        mock_serializer_class.return_value = mock_serializer
        
        # Respuesta del paginador
        respuesta_final = Response({"count": 100, "results": datos_serializados})
        mock_paginator.get_paginated_response.return_value = respuesta_final
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, respuesta_final.data)
        mock_serializer_class.assert_called_once_with(page_data, many=True)



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_devuelve_respuesta_sin_paginacion_cuando_page_es_none(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Devuelve respuesta sin paginación (page = None)
        
        Given: Pocos resultados o paginador desactivado.
        When: paginate_queryset devuelve None.
        Then: La vista devuelve una Response estándar con los datos del serializador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        queryset = ["papeleta_unica"]
        mock_service.return_value = queryset
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        datos_directos = [{"nombre": "Unico"}]
        mock_serializer = MagicMock(data=datos_directos)
        mock_serializer_class.return_value = mock_serializer
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_directos)
        mock_serializer_class.assert_called_once_with(queryset, many=True)



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_llama_correctamente_al_servicio_con_acto_id(self, mock_service):
        """
        Test: Llama correctamente al servicio con acto_id
        
        Given: Un acto_id específico en la URL.
        When: Se procesa la petición GET.
        Then: El servicio de negocio recibe exactamente ese acto_id.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = []
        
        self.view(request, acto_id=self.acto_id)
        
        mock_service.assert_called_once_with(self.acto_id)



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_serializer_se_ejecuta_con_many_true_paginado(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Serializer se ejecuta con many=True (paginado)
        
        Given: El flujo donde el paginador devuelve una página de resultados.
        When: Se instancia el serializador para procesar esa página.
        Then: El serializador debe recibir el argumento many=True ya que la página es una lista.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["asistente_1"]
        mock_paginator.get_paginated_response.return_value = Response({})
        mock_pagination_class.return_value = mock_paginator
        
        self.view(request, acto_id=self.acto_id)

        _, kwargs = mock_serializer_class.call_args
        self.assertTrue(kwargs.get('many'))



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_serializer_se_ejecuta_con_many_true_sin_paginacion(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Serializer se ejecuta con many=True (sin paginación)
        
        Given: El flujo donde paginate_queryset devuelve None.
        When: Se serializa el queryset original directamente.
        Then: El serializador debe recibir many=True porque el servicio devuelve una colección.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = ["asistente_1"]
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        self.view(request, acto_id=self.acto_id)
        
        _, kwargs = mock_serializer_class.call_args
        self.assertTrue(kwargs.get('many'))



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_usa_correctamente_get_paginated_response(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Usa correctamente get_paginated_response
        
        Given: Un flujo con paginación exitosa.
        When: Se obtienen los datos serializados del serializador.
        Then: La vista debe llamar a get_paginated_response pasando específicamente serializer.data.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["item"]
        mock_pagination_class.return_value = mock_paginator

        datos_serializados = [{"id": 1, "nombre": "Prueba"}]
        mock_instancia_serializer = MagicMock()
        mock_instancia_serializer.data = datos_serializados
        mock_serializer_class.return_value = mock_instancia_serializer

        mock_paginator.get_paginated_response.return_value = Response(datos_serializados)
        
        self.view(request, acto_id=self.acto_id)

        mock_paginator.get_paginated_response.assert_called_once_with(datos_serializados)



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_error_en_el_servicio_devuelve_500(self, mock_service):
        """
        Test: Error en el servicio
        
        Given: El servicio de obtención de asistentes lanza una excepción (ej: fallo en DB).
        When: Se invoca la vista.
        Then: Se captura la excepción y se devuelve un status 500 con el mensaje de error definido.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.side_effect = Exception("Error de base de datos")
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], "Ocurrió un error al recuperar los asistentes.")



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_error_en_paginate_queryset_devuelve_500(self, mock_service, mock_pagination_class):
        """
        Test: Error en paginate_queryset
        
        Given: El servicio funciona pero el paginador falla al intentar segmentar el queryset.
        When: paginate_queryset lanza una excepción.
        Then: La vista retorna un status 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.side_effect = Exception("Fallo en paginación")
        mock_pagination_class.return_value = mock_paginator
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], "Ocurrió un error al recuperar los asistentes.")



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_error_en_serializer_devuelve_500(self, mock_service, mock_serializer_class):
        """
        Test: Error en serializer
        
        Given: Los datos se obtienen correctamente pero el serializador falla al procesarlos.
        When: Se instancia el serializador y lanza una excepción.
        Then: La vista captura el error y retorna status 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = MagicMock()
        mock_serializer_class.side_effect = Exception("Fallo en serialización")
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_error_en_get_paginated_response_devuelve_500(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Error en get_paginated_response
        
        Given: La página se crea y se serializa, pero falla la construcción de la respuesta paginada final.
        When: get_paginated_response lanza una excepción.
        Then: Se retorna un status 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = MagicMock()
        mock_serializer_class.return_value = MagicMock(data=[])
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["item"]
        mock_paginator.get_paginated_response.side_effect = Exception("Fallo en respuesta paginada")
        mock_pagination_class.return_value = mock_paginator
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], "Ocurrió un error al recuperar los asistentes.")



    def test_usuario_no_autorizado_devuelve_403(self):
        """
        Test: Usuario no autorizado (403)

        Given: Un usuario que no cumple los requisitos de administración (no admin o no autenticado).
        When: Intenta realizar una petición GET a la vista.
        Then: La respuesta debe tener un status 403 Forbidden debido a la restricción de permission_classes.
        """
        request = self.factory.get(self.path)

        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = False
        
        force_authenticate(request, user=mock_user)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_queryset_vacio_con_paginacion(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Queryset vacío con paginación
        
        Given: El servicio devuelve una lista vacía y el paginador está activo.
        When: paginate_queryset devuelve una lista vacía [].
        Then: Se debe llamar a get_paginated_response con los datos serializados vacíos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = []
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = []
        mock_paginator.get_paginated_response.return_value = Response({"results": []})
        mock_pagination_class.return_value = mock_paginator
        
        mock_serializer_class.return_value = MagicMock(data=[])
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_paginator.get_paginated_response.assert_called_once_with([])



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_queryset_vacio_sin_paginacion(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Queryset vacío sin paginación
        
        Given: El paginador decide no paginar (devuelve None) sobre un resultado vacío.
        When: Se procesa el flujo directo de la vista.
        Then: La vista devuelve una lista vacía [] directamente en el cuerpo de la Response.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = []
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator
        
        mock_serializer_class.return_value = MagicMock(data=[])
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_serializer_devuelve_lista_vacia(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Serializer devuelve lista vacía
        
        Given: Existen datos en el servicio y el paginador genera una página.
        When: El serializador procesa la página pero su atributo .data resulta ser una lista vacía.
        Then: Esa lista vacía se pasa al método get_paginated_response del paginador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = MagicMock()
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = ["item_no_valido"]
        mock_paginator.get_paginated_response.return_value = Response({"results": []})
        mock_pagination_class.return_value = mock_paginator

        mock_serializer_class.return_value = MagicMock(data=[])
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_paginator.get_paginated_response.assert_called_once_with([])



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_verificar_que_no_se_instancia_serializer_si_el_servicio_falla(self, mock_service, mock_serializer_class):
        """
        Test: Verificar que no se instancia serializer si el servicio falla
        
        Given: El servicio de obtención de asistentes lanza una excepción.
        When: La ejecución entra en el bloque 'except'.
        Then: El serializador no debe haber sido llamado nunca, optimizando recursos y evitando estados inconsistentes.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.side_effect = Exception("Fallo de servicio")
        
        self.view(request, acto_id=self.acto_id)
        
        mock_serializer_class.assert_not_called()



    @patch.object(ListarAsistentesLeidosActoView, 'pagination_class')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.AsistenteActoSimplificadoSerializer')
    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_verificar_status_200_en_flujo_sin_paginacion(self, mock_service, mock_serializer_class, mock_pagination_class):
        """
        Test: Verificar status 200 en flujo sin paginación
        
        Given: Resultados que no requieren paginación.
        When: paginate_queryset devuelve None.
        Then: La vista retorna status 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = ["dato"]
        
        mock_paginator = MagicMock()
        mock_paginator.paginate_queryset.return_value = None
        mock_pagination_class.return_value = mock_paginator

        mock_serializer_class.return_value = MagicMock(data=[])
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_verificar_status_500_en_excepcion_general(self, mock_service):
        """
        Test: Verificar status 500 en excepción general
        
        Given: Cualquier error inesperado durante la ejecución de la vista.
        When: Se lanza una excepción.
        Then: El bloque try/except debe garantizar una respuesta con código 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.side_effect = Exception("Fallo crítico")
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)



    @patch('api.vistas.papeleta_sitio.lista_asistentes_leidos_view.obtener_asistentes_leidos_por_acto')
    def test_verificar_que_acto_id_se_pasa_correctamente_al_servicio(self, mock_service):
        """
        Test: Verificar que acto_id se pasa correctamente al servicio
        
        Given: Un acto_id dinámico pasado por la URL.
        When: La vista llama al servicio de negocio.
        Then: El servicio recibe exactamente el mismo acto_id capturado por Django.
        """
        test_id = 999
        path = f"/api/actos/{test_id}/asistentes-leidos/"
        request = self.factory.get(path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = []
        
        self.view(request, acto_id=test_id)
        
        mock_service.assert_called_once_with(test_id)