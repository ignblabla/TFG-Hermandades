import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError

from api.vistas.comunicado.comunicados_general_view import ComunicadoListCreateView


class TestComunicadoListCreateView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ComunicadoListCreateView.as_view()
        self.path = "/api/comunicados/"

        self.mock_user = MagicMock(spec=['is_authenticated', 'areas_interes'])
        self.mock_user.is_authenticated = True



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.PaginacionDoceElementos")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_flujo_feliz_sin_paginacion(self, mock_comunicado, mock_paginacion, mock_serializer):
        """
        Test: Flujo feliz SIN paginación
        
        Given: Un usuario autenticado que solicita el listado de comunicados.
        When: El paginador procesa el queryset pero devuelve None (indicando que no se aplica paginación).
        Then: La vista debe instanciar el serializador con el queryset completo (sin paginar) 
            y retornar un status 200 con los datos serializados.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user

        self.mock_user.areas_interes.all.return_value = []

        mock_qs_select = MagicMock()
        mock_qs_prefetch = MagicMock()
        mock_qs_filter = MagicMock()
        mock_qs_distinct = MagicMock()
        mock_qs_final = MagicMock()
        
        mock_comunicado.objects.select_related.return_value = mock_qs_select
        mock_qs_select.prefetch_related.return_value = mock_qs_prefetch
        mock_qs_prefetch.filter.return_value = mock_qs_filter
        mock_qs_filter.distinct.return_value = mock_qs_distinct
        mock_qs_distinct.order_by.return_value = mock_qs_final

        mock_paginator_instance = mock_paginacion.return_value
        mock_paginator_instance.paginate_queryset.return_value = None

        mock_serializer_instance = mock_serializer.return_value
        datos_simulados = [{"id": 1, "titulo": "Comunicado General"}]
        mock_serializer_instance.data = datos_simulados

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data, datos_simulados)

        mock_serializer.assert_called_once_with(
            mock_qs_final, 
            many=True, 
            context={'request': ANY}
        )

        mock_paginator_instance.get_paginated_response.assert_not_called()



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.PaginacionDoceElementos")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_flujo_feliz_con_paginacion(self, mock_comunicado, mock_paginacion, mock_serializer):
        """
        Test: Flujo feliz CON paginación
        
        Given: Un usuario autenticado y un listado de comunicados que supera el tamaño de página.
        When: El paginador devuelve una lista de elementos (página activa).
        Then: La vista debe delegar la creación de la respuesta al método get_paginated_response 
            del paginador, en lugar de retornar una Response manual.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user

        mock_comunicado.objects.select_related.return_value.prefetch_related.return_value.filter.return_value.distinct.return_value.order_by.return_value = MagicMock()

        mock_paginator_instance = mock_paginacion.return_value
        mock_paginator_instance.paginate_queryset.return_value = ["comunicado_paginado"]

        respuesta_paginada_esperada = Response({"count": 1, "results": [{"id": 1}]})
        mock_paginator_instance.get_paginated_response.return_value = respuesta_paginada_esperada

        response = self.view(request)

        mock_paginator_instance.get_paginated_response.assert_called_once()

        self.assertEqual(response, respuesta_paginada_esperada)

        mock_serializer.assert_called_once_with(["comunicado_paginado"], many=True, context={'request': ANY})



    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_llama_a_areas_interes_all(self, mock_comunicado):
        """
        Test: Se llama a areas_interes.all()
        
        Given: Un usuario autenticado accediendo al listado general.
        When: La vista construye el filtro Q para los comunicados.
        Then: Se verifica que se consulten las áreas de interés del usuario para 
            personalizar el filtrado de la consulta.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user

        self.mock_user.areas_interes.all.return_value = []

        try:
            self.view(request)
        except Exception:
            pass

        self.mock_user.areas_interes.all.assert_called_once()



    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_se_construye_el_queryset_completo(self, mock_comunicado):
        """
        Test: Se construye el queryset completo
        
        Given: Una petición al listado general de comunicados.
        When: La vista ejecuta la lógica de obtención de datos.
        Then: Se verifica que se llame a toda la cadena del ORM (select_related, 
            prefetch_related, filter, distinct y order_by) con los parámetros correctos
            para optimizar la consulta y filtrar por fecha.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        self.mock_user.areas_interes.all.return_value = []

        mock_qs_select = MagicMock()
        mock_qs_prefetch = MagicMock()
        mock_qs_filter = MagicMock()
        mock_qs_distinct = MagicMock()
        mock_qs_order = MagicMock()

        mock_comunicado.objects.select_related.return_value = mock_qs_select
        mock_qs_select.prefetch_related.return_value = mock_qs_prefetch
        mock_qs_prefetch.filter.return_value = mock_qs_filter
        mock_qs_filter.distinct.return_value = mock_qs_distinct
        mock_qs_distinct.order_by.return_value = mock_qs_order

        try:
            self.view(request)
        except Exception:
            pass

        mock_comunicado.objects.select_related.assert_called_once_with('autor')
        mock_qs_select.prefetch_related.assert_called_once_with('areas_interes')
        mock_qs_prefetch.filter.assert_called_once()
        mock_qs_filter.distinct.assert_called_once()
        mock_qs_distinct.order_by.assert_called_once_with('-fecha_emision')



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_se_pasa_correctamente_el_request_al_serializer(self, mock_comunicado, mock_serializer):
        """
        Test: Se pasa correctamente el request al serializer
        
        Given: Una petición GET válida de un usuario.
        When: La vista instancia el ComunicadoListSerializer.
        Then: Se valida que el objeto request (el wrapper de DRF) se incluya 
            en el contexto del serializador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        
        self.mock_user.areas_interes.all.return_value = []
        mock_comunicado.objects.select_related.return_value.prefetch_related.return_value.filter.return_value.distinct.return_value.order_by.return_value = MagicMock()

        response = self.view(request)

        args, kwargs = mock_serializer.call_args
        request_en_contexto = kwargs['context']['request']

        self.assertIsInstance(request_en_contexto, Request)

        self.assertEqual(request_en_contexto._request, request)



    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_usuario_sin_areas_funciona_sin_romper(self, mock_comunicado):
        """
        Test: Usuario sin áreas
        
        Given: Un usuario autenticado que no tiene áreas de interés vinculadas.
        When: Se construye el filtro Q de la consulta.
        Then: El sistema debe procesar la lista vacía de áreas sin lanzar excepciones
            y continuar con la ejecución normal del queryset.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user

        self.mock_user.areas_interes.all.return_value = []

        mock_comunicado.objects.select_related.return_value.prefetch_related.return_value.filter.return_value.distinct.return_value.order_by.return_value = MagicMock()

        response = self.view(request)

        self.assertEqual(response.status_code, 200)



    @patch("api.vistas.comunicado.comunicados_general_view.PaginacionDoceElementos")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_paginate_queryset_lanza_excepcion(self, mock_comunicado, mock_paginacion):
        """
        Test: paginate_queryset lanza excepción
        
        Given: Una consulta de comunicados válida.
        When: El componente de paginación falla internamente al intentar segmentar el queryset.
        Then: La excepción lanzada por el paginador debe propagarse correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        self.mock_user.areas_interes.all.return_value = []

        mock_paginator_instance = mock_paginacion.return_value
        mock_paginator_instance.paginate_queryset.side_effect = Exception("error_paginacion")

        with self.assertRaises(Exception) as context:
            self.view(request)
            
        self.assertEqual(str(context.exception), "error_paginacion")



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer") # Añadido
    @patch("api.vistas.comunicado.comunicados_general_view.PaginacionDoceElementos")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_get_paginated_response_falla(self, mock_comunicado, mock_paginacion, mock_serializer):
        """
        Test: get_paginated_response falla
        
        Given: Un queryset paginado correctamente.
        When: La vista intenta generar la respuesta envuelta en metadatos de paginación.
        Then: Si el método get_paginated_response falla, la excepción debe ser capturada por el test.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        self.mock_user.areas_interes.all.return_value = []

        mock_qs = MagicMock()
        mock_comunicado.objects.select_related.return_value \
            .prefetch_related.return_value \
            .filter.return_value \
            .distinct.return_value \
            .order_by.return_value = mock_qs

        mock_serializer.return_value.data = [{"id": 1}]

        mock_paginator_instance = mock_paginacion.return_value
        mock_paginator_instance.paginate_queryset.return_value = ["item"]

        mock_paginator_instance.get_paginated_response.side_effect = Exception("error_respuesta_paginada")

        with self.assertRaises(Exception) as context:
            self.view(request)

        self.assertIn("error_respuesta_paginada", str(context.exception))



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_serializer_lanza_excepcion(self, mock_comunicado, mock_serializer):
        """
        Test: Serializer falla
        
        Given: Un queryset obtenido correctamente del ORM.
        When: La vista intenta instanciar el ComunicadoListSerializer.
        Then: La excepción lanzada por el constructor del serializador se propaga, 
            permitiendo verificar la robustez del flujo.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        self.mock_user.areas_interes.all.return_value = []

        mock_comunicado.objects.select_related.return_value \
            .prefetch_related.return_value \
            .filter.return_value \
            .distinct.return_value \
            .order_by.return_value = MagicMock()

        mock_serializer.side_effect = Exception("serializer error")

        with self.assertRaises(Exception) as context:
            self.view(request)
            
        self.assertIn("serializer error", str(context.exception))



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_serializer_data_falla(self, mock_comunicado, mock_serializer):
        """
        Test: serializer.data falla
        
        Given: Un serializador instanciado correctamente.
        When: La vista accede a la propiedad calculada .data para construir la respuesta.
        Then: La excepción inyectada en la propiedad data se propaga correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        self.mock_user.areas_interes.all.return_value = []

        mock_comunicado.objects.select_related.return_value \
            .prefetch_related.return_value \
            .filter.return_value \
            .distinct.return_value \
            .order_by.return_value = MagicMock()

        mock_instance = mock_serializer.return_value
        type(mock_instance).data = property(
            lambda _: (_ for _ in ()).throw(Exception("data error"))
        )

        with self.assertRaises(Exception) as context:
            self.view(request)
            
        self.assertIn("data error", str(context.exception))



    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_falla_en_la_cadena_del_queryset(self, mock_comunicado):
        """
        Test: Falla en la cadena del queryset
        
        Given: Una petición al listado general.
        When: El ORM falla específicamente en el método .filter().
        Then: La excepción "query error" se propaga, validando que el error no sea 
            silenciado durante la construcción de la consulta.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user
        self.mock_user.areas_interes.all.return_value = []

        mock_qs_prefetch = mock_comunicado.objects.select_related.return_value.prefetch_related.return_value
        mock_qs_prefetch.filter.side_effect = Exception("query error")

        with self.assertRaises(Exception) as context:
            self.view(request)
            
        self.assertIn("query error", str(context.exception))



    @patch("api.vistas.comunicado.comunicados_general_view.Comunicado")
    def test_se_respeta_el_orden_fecha_emision_descendente(self, mock_comunicado):
        """
        Test: Se respeta el orden -fecha_emision
        
        Given: Una petición al listado general de comunicados.
        When: Se construye la consulta final al ORM.
        Then: Se verifica que el método .order_by() sea invocado exactamente con 
            el parámetro '-fecha_emision' para garantizar que los más recientes aparezcan primero.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        request.user = self.mock_user

        self.mock_user.areas_interes.all.return_value = []

        mock_qs_select = MagicMock()
        mock_qs_prefetch = MagicMock()
        mock_qs_filter = MagicMock()
        mock_qs_distinct = MagicMock()
        mock_qs_final = MagicMock()

        mock_comunicado.objects.select_related.return_value = mock_qs_select
        mock_qs_select.prefetch_related.return_value = mock_qs_prefetch
        mock_qs_prefetch.filter.return_value = mock_qs_filter
        mock_qs_filter.distinct.return_value = mock_qs_distinct
        mock_qs_distinct.order_by.return_value = mock_qs_final

        try:
            self.view(request)
        except Exception:
            pass

        mock_qs_distinct.order_by.assert_called_once_with('-fecha_emision')



    # ---------------------------------------------------------------------------
    # TESTS POST
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_creacion_comunicado_flujo_feliz(self, mock_form, mock_service, mock_response_serializer):
        """
        Test: Flujo feliz (CREACIÓN OK)
        
        Given: Un usuario autenticado y datos de entrada válidos para un comunicado.
        When: Se realiza una petición POST a la vista.
        Then: El formulario valida correctamente, el servicio crea el objeto y 
            la vista retorna un status 201 junto con los datos del nuevo comunicado.
        """
        datos_post = {"titulo": "Nuevo Comunicado", "contenido": "Texto de prueba"}
        request = self.factory.post(self.path, data=datos_post, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        datos_validados = {"titulo": "test"}
        mock_form_instance.validated_data = datos_validados

        mock_service_instance = mock_service.return_value
        objeto_creado = MagicMock()
        mock_service_instance.create_comunicado.return_value = objeto_creado

        mock_response_instance = mock_response_serializer.return_value
        datos_respuesta = {"id": 1, "titulo": "test"}
        mock_response_instance.data = datos_respuesta

        response = self.view(request)

        mock_form_instance.is_valid.assert_called_once_with(raise_exception=True)
        mock_service_instance.create_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            data_validada=datos_validados
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, datos_respuesta)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_verificar_llamadas_validacion_y_servicio(self, mock_form, mock_service, mock_response_serializer):
        """
        Test: Verificación de is_valid y llamada al servicio
        
        Given: Una petición POST con datos para un nuevo comunicado.
        When: La vista procesa la solicitud de creación.
        Then: Se debe invocar is_valid con el parámetro raise_exception=True 
            y posteriormente llamar al servicio con el usuario de la request 
            y los datos ya validados por el serializador.
        """
        datos_entrada = {"titulo": "Interacción Test"}
        request = self.factory.post(self.path, data=datos_entrada, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        
        datos_validados_simulados = {"titulo": "Interacción Test Validada"}
        mock_form_instance.validated_data = datos_validados_simulados
        
        mock_service_instance = mock_service.return_value

        self.view(request)

        mock_form_instance.is_valid.assert_called_once_with(raise_exception=True)

        mock_service_instance.create_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            data_validada=datos_validados_simulados
        )



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_se_llama_al_service_con_datos_correctos(self, mock_form, mock_service, mock_response_serializer):
        """
        Test: Se llama al service con datos correctos
        
        Given: Un usuario autenticado y un serializador que valida los datos de entrada.
        When: La vista procesa el método POST exitosamente.
        Then: Se debe invocar al método create_comunicado del servicio enviando 
            el objeto usuario de la request y el diccionario de validated_data 
            del serializador.
        """
        datos_entrada = {"titulo": "Comunicado de prueba", "contenido": "Contenido válido"}
        request = self.factory.post(self.path, data=datos_entrada, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True

        datos_validados_mock = {"titulo": "Comunicado de prueba", "contenido": "Contenido válido"}
        mock_form_instance.validated_data = datos_validados_mock
        
        mock_service_instance = mock_service.return_value

        self.view(request)

        mock_service_instance.create_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            data_validada=datos_validados_mock
        )



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_se_serializa_la_respuesta_correctamente(self, mock_form, mock_service, mock_response_serializer):
        """
        Test: Se serializa la respuesta correctamente
        
        Given: Un flujo donde el servicio crea exitosamente un comunicado.
        When: La vista recibe el nuevo objeto desde la capa de servicio.
        Then: Se debe instanciar el ComunicadoListSerializer pasando exactamente 
            el objeto devuelto por el servicio para generar la respuesta final.
        """
        request = self.factory.post(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form.return_value.is_valid.return_value = True

        objeto_creado_mock = MagicMock(name="objeto_creado")
        mock_service.return_value.create_comunicado.return_value = objeto_creado_mock

        self.view(request)

        mock_response_serializer.assert_called_once_with(objeto_creado_mock)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_form_serializer_falla_validation_error(self, mock_form):
        """
        Test: Form serializer falla (ValidationError)
        
        Given: Un payload con datos que no cumplen las reglas del serializador.
        When: Se llama a is_valid(raise_exception=True).
        Then: DRF lanza una ValidationError y el framework devuelve automáticamente 
            un status 400 antes de ejecutar el bloque try de la vista.
        """
        request = self.factory.post(self.path, data={"titulo": ""}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form.return_value.is_valid.side_effect = ValidationError("error")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_validated_data_vacio_o_invalido(self, mock_form, mock_service):
        """
        Test: validated_data vacío o inválido
        
        Given: Un serializador que se marca como válido pero no tiene datos procesados.
        When: La vista intenta llamar al servicio pasando None como data_validada.
        Then: El servicio o la lógica posterior lanza una excepción que es 
            capturada por el bloque except de la vista, devolviendo un status 400.
        """
        request = self.factory.post(self.path, data={"data": "test"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.validated_data = None

        mock_service.return_value.create_comunicado.side_effect = Exception("Datos no proporcionados")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Datos no proporcionados")



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_service_lanza_excepcion_devuelve_400(self, mock_form, mock_service):
        """
        Test: Service lanza excepción
        
        Given: Un formulario válido.
        When: El método create_comunicado del servicio lanza una excepción genérica.
        Then: La vista debe capturar el error y devolver un status 400 con el mensaje 
            de la excepción en el campo 'detail'.
        """
        request = self.factory.post(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_form.return_value.is_valid.return_value = True

        mock_service.return_value.create_comunicado.side_effect = Exception("service error")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "service error"})



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_serializer_de_salida_falla_devuelve_400(self, mock_form, mock_service, mock_response_serializer):
        """
        Test: Serializer de salida falla
        
        Given: Un comunicado creado correctamente por el servicio.
        When: El serializador de salida (ComunicadoListSerializer) lanza una excepción al instanciarse.
        Then: La vista debe capturar este error en su bloque try/except y retornar 
            un status 400 con el detalle del error.
        """
        request = self.factory.post(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_form.return_value.is_valid.return_value = True
        mock_service.return_value.create_comunicado.return_value = MagicMock()

        mock_response_serializer.side_effect = Exception("serializer error")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "serializer error")



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_serializer_data_rompe_devuelve_400(self, mock_form, mock_service, mock_response_serializer):
        """
        Test: serializer.data rompe
        
        Given: Un proceso de creación exitoso hasta la serialización de salida.
        When: Se accede a la propiedad .data del serializador pero esta lanza una excepción.
        Then: La vista debe capturar el error en el bloque try/except y retornar status 400.
        """
        request = self.factory.post(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_form.return_value.is_valid.return_value = True
        mock_service.return_value.create_comunicado.return_value = MagicMock()

        mock_instance = mock_response_serializer.return_value
        type(mock_instance).data = property(
            lambda _: (_ for _ in ()).throw(Exception("data error"))
        )

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "data error")



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_usuario_correcto_se_pasa_al_service(self, mock_form, mock_service):
        """
        Test: Usuario correcto se pasa al service
        
        Given: Una petición post de un usuario autenticado.
        When: La vista llama al servicio de creación.
        Then: Se verifica que el objeto usuario pasado al servicio sea exactamente 
            el mismo que el de la request (request.user).
        """
        request = self.factory.post(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_form.return_value.is_valid.return_value = True
        mock_service_instance = mock_service.return_value

        self.view(request)

        mock_service_instance.create_comunicado.assert_called_once()
        args, kwargs = mock_service_instance.create_comunicado.call_args
        self.assertEqual(kwargs["usuario"], self.mock_user)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_request_data_vacio_lanza_validation_error(self, mock_form):
        """
        Test: request.data vacío
        
        Given: Una petición POST sin cuerpo de datos (JSON vacío).
        When: El ComunicadoFormSerializer procesa los datos.
        Then: is_valid(raise_exception=True) lanza una ValidationError y 
            DRF responde automáticamente con un status 400.
        """
        request = self.factory.post(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form.return_value.is_valid.side_effect = ValidationError({"detail": "No data provided"})

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicados_general_view.ComunicadoFormSerializer")
    def test_exception_generica_en_flujo_servicio(self, mock_form, mock_service):
        """
        Test: Exception genérica en todo el flujo
        
        Given: Un formulario que pasa la validación inicial.
        When: El servicio lanza una excepción inesperada o fatal durante la creación.
        Then: La vista debe capturar dicha excepción en su bloque try/except genérico
            y retornar un status 400 con el mensaje exacto de la excepción en el campo 'detail'.
        """
        request = self.factory.post(self.path, data={"titulo": "Prueba Fatal"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_form.return_value.is_valid.return_value = True

        mock_service.return_value.create_comunicado.side_effect = Exception("fatal")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "fatal"})