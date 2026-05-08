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
    def test_solicitud_valida_retorna_201_created(self, mock_serializer_class, mock_service_class):
        """
        Test: Request válido retorna 201 Created

        Given: Un request POST válido de un usuario autenticado solicitando una insignia.
        When: La vista procesa la petición exitosamente a través del serializer y el servicio.
        Then: Se invoca al servicio con los parámetros exactos y retorna status 201 con los datos.
        """
        mock_user = MagicMock()
        request = self.factory.post(self.url, data={'acto': 1, 'preferencias': []}, format='json')
        force_authenticate(request, user=mock_user)

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = True
        
        mock_acto = MagicMock()
        mock_serializer_instance.validated_data = {'acto': mock_acto, 'preferencias': []}
        
        datos_respuesta_esperada = {"id": 100, "estado": "SOLICITADA"}
        mock_serializer_instance.data = datos_respuesta_esperada

        mock_papeleta = MagicMock()
        mock_service_instance = mock_service_class.return_value
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
    def test_serializer_invalido_retorna_400_bad_request(self, mock_serializer_class, mock_service_class):
        """
        Test: Serializer inválido retorna 400 Bad Request

        Given: Un request con datos que fallan las reglas de validación del serializer.
        When: Se llama a serializer.is_valid() y falla.
        Then: La vista retorna status 400 con los errores y NUNCA invoca al servicio.
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
        mock_service_class.return_value.procesar_solicitud_insignia_tradicional.assert_not_called()



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_error_validacion_servicio_retorna_400(self, mock_serializer_class, mock_service_class):
        """
        Test: Error de validación del servicio retorna 400

        Given: Un serializer válido pero una lógica de negocio que lanza DjangoValidationError.
        When: El servicio procesa la solicitud y rechaza la operación.
        Then: La vista captura la excepción y retorna un status 400 con el detalle del error.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = {'acto': MagicMock(), 'preferencias': []}

        mock_service_instance = mock_service_class.return_value
        mensaje_error = "Ya existe una solicitud para este acto."
        mock_service_instance.procesar_solicitud_insignia_tradicional.side_effect = DjangoValidationError(mensaje_error)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(mensaje_error, str(response.data["detail"]))



    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.solicitud_insignia_view.SolicitudInsigniaSerializer')
    def test_excepcion_generica_retorna_500(self, mock_serializer_class, mock_service_class):
        """
        Test: Excepción genérica retorna 500

        Given: Una petición válida.
        When: El servicio lanza una Exception inesperada (ej. base de datos inaccesible).
        Then: La vista captura el error y retorna status 500 con un mensaje genérico.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True

        mock_service_instance = mock_service_class.return_value
        mock_service_instance.procesar_solicitud_insignia_tradicional.side_effect = Exception("Database crash")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"detail": "Error interno al procesar la solicitud."})



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado es rechazado

        Given: Un usuario anónimo (sin sesión/token de autenticación).
        When: Intenta acceder al endpoint POST.
        Then: La vista bloquea el acceso mediante IsAuthenticated y retorna 401/403.
        """
        request = self.factory.post(self.url, data={'acto': 1}, format='json')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])