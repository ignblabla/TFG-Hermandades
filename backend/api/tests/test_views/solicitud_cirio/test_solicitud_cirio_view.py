from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from api.vistas.solicitud_cirio.solicitud_cirio_view import SolicitarCirioView

from django.core.exceptions import ValidationError as DjangoValidationError


class TestSolicitarInsigniaView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = "/api/papeletas/solicitar-cirio/"
        self.vista_callable = SolicitarCirioView.as_view()
        
        self.user = MagicMock(name="User_Hermano")
        self.user.is_authenticated = True



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    def test_post_solicitud_exitosa_sin_vinculacion_201(self, mock_service_method, mock_serializer_class):
        """
        Test: Solicitud correcta sin vinculación (201)

        Given: Una petición POST válida sin datos de vinculación.
        When: El serializador valida y el servicio procesa la solicitud con éxito.
        Then: La vista retorna 201 CREATED con un mensaje de éxito simple.
        """
        request = self.factory.post(self.url, data={})
        force_authenticate(request, user=self.user)

        mock_acto = MagicMock()
        mock_puesto = MagicMock(nombre="Cirio")
        
        mock_serializer = mock_serializer_class.return_value
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            'acto': mock_acto,
            'puesto': mock_puesto,
            'numero_registro_vinculado': None
        }

        mock_service_method.return_value = MagicMock(id=123, numero_papeleta=50, fecha_solicitud="2026-03-20")

        response = self.vista_callable(request)

        mock_service_method.assert_called_once_with(
            hermano=self.user, acto=mock_acto, puesto=mock_puesto, numero_registro_vinculado=None
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["mensaje"], "Solicitud para Cirio realizada correctamente.")
        self.assertEqual(response.data["id"], 123)



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    def test_post_solicitud_exitosa_con_vinculacion_201(self, mock_service_method, mock_serializer_class):
        """
        Test: Solicitud correcta con vinculación (201)

        Given: Una petición válida que incluye un número de registro vinculado.
        When: La lógica de la vista detecta que numero_vinculado tiene un valor verdadero.
        Then: La respuesta incluye un mensaje de éxito concatenado con la información del hermano.
        """
        request = self.factory.post(self.url, data={"numero_registro_vinculado": 456})
        force_authenticate(request, user=self.user)

        mock_serializer = mock_serializer_class.return_value
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            'acto': MagicMock(),
            'puesto': MagicMock(nombre="Diputado"),
            'numero_registro_vinculado': 456
        }

        mock_service_method.return_value = MagicMock(id=1, numero_papeleta=10, fecha_solicitud="2026-03-20")

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["mensaje"], "Solicitud para Diputado realizada correctamente. Vinculada al hermano Nº 456.")



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    def test_post_serializer_invalido_400(self, mock_serializer_class):
        """
        Test: Serializer inválido (400)

        Given: Una petición con datos que no superan las validaciones.
        When: serializer.is_valid() retorna False.
        Then: La vista salta el bloque try y retorna 400 BAD REQUEST con los errores.
        """
        request = self.factory.post(self.url, data={})
        force_authenticate(request, user=self.user)

        mock_serializer = mock_serializer_class.return_value
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {"acto": ["Este campo es obligatorio."]}

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"acto": ["Este campo es obligatorio."]})



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    def test_post_django_validation_error_400(self, mock_service_method, mock_serializer_class):
        """
        Test: DjangoValidationError capturado (400)

        Given: Datos válidos pero el servicio detecta una inconsistencia de negocio.
        When: El servicio lanza una DjangoValidationError.
        Then: La vista captura la excepción y retorna un 400 con el detalle del mensaje.
        """
        request = self.factory.post(self.url, data={})
        force_authenticate(request, user=self.user)

        mock_serializer = mock_serializer_class.return_value
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'acto': MagicMock(), 'puesto': MagicMock(), 'numero_registro_vinculado': None}

        mensaje_error = "Ya existe una solicitud activa."
        mock_service_method.side_effect = DjangoValidationError(mensaje_error)

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(mensaje_error, str(response.data["detail"]))



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    def test_post_excepcion_inesperada_500(self, mock_service_method, mock_serializer_class, mock_print):
        """
        Test: Exception genérica y llamada a print (500)

        Given: Una excepción inesperada en el servicio.
        When: La vista captura la excepción en el bloque genérico.
        Then: Ejecuta un print para loguear el fallo y retorna 500 INTERNAL SERVER ERROR.
        """
        request = self.factory.post(self.url, data={})
        force_authenticate(request, user=self.user)

        mock_serializer_class.return_value.is_valid.return_value = True
        mock_service_method.side_effect = Exception("Caída de Base de Datos")

        response = self.vista_callable(request)

        mock_print.assert_called()
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detail"], "Error interno del servidor.")



    def test_post_usuario_no_autenticado_403(self):
        """
        Test: Usuario no autenticado -> acceso denegado
        
        Given: Una petición POST sin credenciales.
        When: Intenta acceder al endpoint protegido.
        Then: La vista bloquea el acceso en la capa de permisos (401/403).
        """
        request = self.factory.post(self.url, data={})
        
        response = self.vista_callable(request)
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])