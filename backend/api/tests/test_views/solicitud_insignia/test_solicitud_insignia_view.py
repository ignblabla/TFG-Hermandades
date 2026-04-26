from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status

from django.core.exceptions import ValidationError as DjangoValidationError

from api.vistas.solicitud_insignia.solicitud_insignia_view import SolicitarInsigniaView


class TestSolicitarInsigniaView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = SolicitarInsigniaView.as_view()
        self.url = "/papeletas/solicitar-insignia/"

    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_request_valido_retorna_201_created(self, mock_serializer_class, mock_service_class):
        """
        Test: Request válido → 201 CREATED

        Given: Un request POST válido de un usuario autenticado solicitando una insignia.
        When: La vista SolicitarInsigniaView procesa la petición.
        Then: Se invoca al servicio con los datos validados y se retorna la papeleta serializada con status 201.
        """
        request = self.factory.post(self.url, data={'acto': 1, 'preferencias': []}, format='json')
        mock_user = MagicMock()
        force_authenticate(request, user=mock_user)

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = True

        mock_acto = MagicMock()
        mock_serializer_instance.validated_data = {
            'acto': mock_acto,
            'preferencias': []
        }

        datos_respuesta_esperada = {"id": 100, "estado": "SOLICITADA"}
        mock_serializer_instance.data = datos_respuesta_esperada

        mock_service_instance = mock_service_class.return_value
        mock_papeleta = MagicMock()
        mock_service_instance.procesar_solicitud_insignia_tradicional.return_value = mock_papeleta

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data, datos_respuesta_esperada)

        mock_service_instance.procesar_solicitud_insignia_tradicional.assert_called_once_with(
            hermano=mock_user,
            acto=mock_acto,
            preferencias_data=[]
        )



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_se_llama_al_servicio_con_parametros_correctos(self, mock_serializer_class, mock_service_class):
        """
        Test: Se llama al servicio con parámetros correctos

        Given: Un serializer que valida correctamente un acto y una lista de preferencias.
        When: Se ejecuta la acción POST de la vista.
        Then: El método procesar_solicitud_insignia_tradicional del servicio debe recibir exactamente el usuario, el acto y las preferencias.
        """
        mock_user = MagicMock()
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=mock_user)

        mock_acto = MagicMock()
        mock_preferencias = [{'puesto': 1, 'prioridad': 1}]
        
        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = {
            'acto': mock_acto,
            'preferencias': mock_preferencias
        }

        mock_service_instance = mock_service_class.return_value

        self.view(request)

        mock_service_instance.procesar_solicitud_insignia_tradicional.assert_called_once_with(
            hermano=mock_user,
            acto=mock_acto,
            preferencias_data=mock_preferencias
        )



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_serializer_recibe_context_correctamente(self, mock_serializer_class):
        """
        Test: Serializer recibe context correctamente

        Given: Una petición POST hacia la vista.
        When: Se instancia el serializer para validar la entrada.
        Then: Se debe pasar el objeto enriquecido por DRF (Request) dentro del context.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())
        
        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = False 

        response = self.view(request)

        args, kwargs = mock_serializer_class.call_args
        
        self.assertIn('context', kwargs)

        request_en_serializer = kwargs['context']['request']

        from rest_framework.request import Request
        self.assertIsInstance(request_en_serializer, Request)

        self.assertEqual(request_en_serializer.path, self.url)



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_serializer_invalido_retorna_400_bad_request(self, mock_serializer_class):
        """
        Test: Serializer inválido → 400

        Given: Un request con datos que no cumplen las reglas del serializer.
        When: Se llama a serializer.is_valid().
        Then: La vista debe retornar un status 400 y el diccionario de errores del serializer.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = False
        
        errores_esperados = {'acto': ['Este campo es requerido.']}
        mock_serializer_instance.errors = errores_esperados

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, errores_esperados)



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_error_de_validacion_del_servicio_retorna_400(self, mock_serializer_class, mock_service_class):
        """
        Test: Error de validación del servicio (DjangoValidationError)

        Given: Un serializer válido pero una lógica de negocio que lanza DjangoValidationError.
        When: El servicio procesa la solicitud.
        Then: La vista debe capturar la excepción y retornar un status 400 con el detalle del error.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = {'acto': MagicMock(), 'preferencias': []}

        mock_service_instance = mock_service_class.return_value
        mock_service_instance.procesar_solicitud_insignia_tradicional.side_effect = DjangoValidationError(
            "Ya existe una solicitud para este acto."
        )

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Ya existe una solicitud para este acto."})



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_django_validation_error_sin_message_usa_fallback_str(self, mock_serializer_class, mock_service_class):
        """
        Test: DjangoValidationError sin .message

        Given: Un error de validación de Django que solo contiene una cadena (sin atributo .message).
        When: El servicio lanza la excepción.
        Then: La vista debe usar str(e) como fallback y retornar status 400.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True

        error_msg = "Error de formato de lista."
        mock_service_instance = mock_service_class.return_value
        mock_service_instance.procesar_solicitud_insignia_tradicional.side_effect = DjangoValidationError(error_msg)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn(error_msg, str(response.data["detail"]))



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_excepcion_generica_retorna_500_error_interno(self, mock_serializer_class, mock_service_class):
        """
        Test: Excepción genérica → 500

        Given: Un error inesperado en el servidor (base de datos caída, error de código, etc.).
        When: El servicio lanza una Exception genérica.
        Then: La vista debe capturarlo y retornar un mensaje genérico de error interno con status 500.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True

        mock_service_instance = mock_service_class.return_value
        mock_service_instance.procesar_solicitud_insignia_tradicional.side_effect = Exception("Database crash")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"detail": "Error interno al procesar la solicitud."})

        self.assertNotEqual(response.data["detail"], "Database crash")



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_validacion_parcial_del_serializer_no_llama_al_servicio(self, mock_serializer_class, mock_service_class):
        """
        Test: Validación parcial del serializer

        Given: Un serializer que determina que los datos de entrada son inválidos.
        When: Se ejecuta la lógica de la vista.
        Then: La vista debe retornar un error 400 y el método procesar_solicitud_insignia_tradicional del servicio NUNCA debe ser invocado.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = False
        
        mock_service_instance = mock_service_class.return_value

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        mock_service_instance.procesar_solicitud_insignia_tradicional.assert_not_called()



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_usuario_en_request_se_pasa_correctamente(self, mock_serializer_class, mock_service_class):
        """
        Test: Usuario en request

        Given: Un usuario autenticado en la sesión.
        When: Se procesa la solicitud exitosamente.
        Then: El objeto user extraído de request.user debe ser el mismo que se pase al parámetro 'hermano' del servicio.
        """
        mock_user = MagicMock()
        request = self.factory.post(self.url, data={}, format='json')

        force_authenticate(request, user=mock_user)

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = {
            'acto': MagicMock(),
            'preferencias': []
        }

        mock_service_instance = mock_service_class.return_value

        self.view(request)

        args, kwargs = mock_service_instance.procesar_solicitud_insignia_tradicional.call_args
        self.assertEqual(kwargs['hermano'], mock_user)



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_datos_minimos_validos_flujo_basico_completo(self, mock_serializer_class, mock_service_class):
        """
        Test: Datos mínimos válidos

        Given: Un payload con los campos mínimos requeridos por el serializer.
        When: Se procesa la petición POST.
        Then: La vista debe coordinar correctamente al serializer y al servicio para culminar en un 201 CREATED.
        """
        request = self.factory.post(self.url, data={'acto': 1, 'preferencias': []}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_in = mock_serializer_class.return_value
        mock_serializer_in.is_valid.return_value = True
        mock_serializer_in.validated_data = {'acto': MagicMock(), 'preferencias': []}

        mock_papeleta = MagicMock()
        mock_service_class.return_value.procesar_solicitud_insignia_tradicional.return_value = mock_papeleta

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_service_class.return_value.procesar_solicitud_insignia_tradicional.assert_called_once()



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    def test_serializer_de_respuesta_se_instancia_con_papeleta(self, mock_service_class, mock_serializer_class):
        """
        Test: Serializer de respuesta

        Given: Una solicitud procesada con éxito por el servicio.
        When: Se prepara la respuesta para el cliente.
        Then: Se debe instanciar el serializer pasando el objeto papeleta devuelto por el servicio para su transformación a JSON.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True
        mock_serializer_class.return_value.validated_data = {'acto': MagicMock(), 'preferencias': []}

        papeleta_creada = MagicMock(id=999)
        mock_service_class.return_value.procesar_solicitud_insignia_tradicional.return_value = papeleta_creada

        self.view(request)

        llamada_respuesta = mock_serializer_class.call_args_list[1]

        self.assertEqual(llamada_respuesta.args[0], papeleta_creada)