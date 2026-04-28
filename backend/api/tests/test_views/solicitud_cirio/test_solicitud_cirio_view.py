from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from api.vistas.solicitud_cirio.solicitud_cirio_view import SolicitarCirioView

from django.core.exceptions import ValidationError as DjangoValidationError


class TestSolicitarInsigniaView(APITestCase):

    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_solicitud_correcta_sin_vinculacion(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: Solicitud correcta sin vinculación

        Given: Una petición POST válida enviada por un usuario autenticado sin datos de vinculación.
        When: El serializador valida correctamente y el servicio procesa la solicitud con éxito.
        Then: La vista debe retornar un status 201 CREATED con la información de la papeleta y un mensaje de éxito simple.
        """
        factory = APIRequestFactory()
        user_fake = MagicMock(name="User_Hermano")
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=user_fake)

        mock_acto = MagicMock(name="Acto_Mock")
        mock_puesto = MagicMock(name="Puesto_Mock")
        mock_puesto.nombre = "Cirio"
        
        serializer_instance = mock_serializer_class.return_value
        serializer_instance.is_valid.return_value = True
        serializer_instance.validated_data = {
            'acto': mock_acto,
            'puesto': mock_puesto,
            'numero_registro_vinculado': None
        }

        mock_papeleta = MagicMock(name="Papeleta_Mock")
        mock_papeleta.id = 123
        mock_papeleta.numero_papeleta = None
        mock_papeleta.fecha_solicitud = "2026-03-20"
        mock_service_method.return_value = mock_papeleta

        view = SolicitarCirioView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["mensaje"], "Solicitud para Cirio realizada correctamente.")
        self.assertEqual(response.data["id"], 123)
        self.assertEqual(response.data["fecha"], "2026-03-20")

        mock_service_method.assert_called_once_with(
            hermano=user_fake,
            acto=mock_acto,
            puesto=mock_puesto,
            numero_registro_vinculado=None
        )



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_solicitud_correcta_con_vinculacion(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: Solicitud correcta con vinculación

        Given: Una petición válida que incluye el número de registro de un hermano vinculado (ej. 456).
        When: El serializador valida la vinculación y el servicio procesa la solicitud con éxito.
        Then: La respuesta debe incluir un mensaje de éxito que concatene correctamente el texto de vinculación al hermano indicado.
        """
        factory = APIRequestFactory()
        user_fake = MagicMock(name="User_Hermano")
        request = factory.post("/papeletas/solicitar-cirio/", data={"numero_registro_vinculado": 456})
        force_authenticate(request, user=user_fake)

        mock_puesto = MagicMock(name="Puesto_Mock")
        mock_puesto.nombre = "Diputado"
        
        serializer_instance = mock_serializer_class.return_value
        serializer_instance.is_valid.return_value = True
        serializer_instance.validated_data = {
            'acto': MagicMock(name="Acto_Mock"),
            'puesto': mock_puesto,
            'numero_registro_vinculado': 456
        }

        mock_papeleta = MagicMock(id=1, numero_papeleta=10, fecha_solicitud="2026-03-20")
        mock_service_method.return_value = mock_papeleta

        view = SolicitarCirioView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mensaje_esperado = "Solicitud para Diputado realizada correctamente. Vinculada al hermano Nº 456."
        self.assertEqual(response.data["mensaje"], mensaje_esperado)



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_llamada_correcta_al_servicio(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: Llamada correcta al servicio

        Given: Un conjunto de datos validados (acto, puesto, numero_registro_vinculado).
        When: La vista ejecuta el flujo tras la validación del serializador.
        Then: Se debe llamar al método procesar_solicitud_cirio_tradicional del servicio pasando exactamente los objetos extraídos y el usuario de la petición.
        """
        factory = APIRequestFactory()
        user_fake = MagicMock(name="User_Hermano")
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=user_fake)

        mock_acto_instancia = MagicMock(name="Acto_Instancia")
        mock_puesto_instancia = MagicMock(name="Puesto_Instancia")
        num_vinculado = 789
        
        serializer_instance = mock_serializer_class.return_value
        serializer_instance.is_valid.return_value = True
        serializer_instance.validated_data = {
            'acto': mock_acto_instancia,
            'puesto': mock_puesto_instancia,
            'numero_registro_vinculado': num_vinculado
        }

        mock_service_method.return_value = MagicMock(id=1, numero_papeleta=1, fecha_solicitud="2026-03-20")

        view = SolicitarCirioView.as_view()

        view(request)

        mock_service_method.assert_called_once_with(
            hermano=user_fake,
            acto=mock_acto_instancia,
            puesto=mock_puesto_instancia,
            numero_registro_vinculado=num_vinculado
        )



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_estructura_correcta_de_la_respuesta(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: Estructura correcta de la respuesta

        Given: Una solicitud procesada con éxito por el servicio.
        When: La vista genera la respuesta para el cliente.
        Then: El JSON de respuesta debe contener exactamente las llaves: status, mensaje, id, numero_papeleta y fecha.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True
        mock_serializer_class.return_value.validated_data = {
            'acto': MagicMock(), 'puesto': MagicMock(nombre="Test"), 'numero_registro_vinculado': None
        }

        mock_papeleta = MagicMock()
        mock_papeleta.id = 1
        mock_papeleta.numero_papeleta = 100
        mock_papeleta.fecha_solicitud = "2026-03-20"
        mock_service_method.return_value = mock_papeleta

        view = SolicitarCirioView.as_view()

        response = view(request)

        keys_esperadas = {"status", "mensaje", "id", "numero_papeleta", "fecha"}
        self.assertEqual(set(response.data.keys()), keys_esperadas)

        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["numero_papeleta"], 100)
        self.assertEqual(response.data["fecha"], "2026-03-20")



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_manejo_numero_registro_vinculado_none(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: Manejo correcto de numero_registro_vinculado=None

        Given: Una solicitud donde numero_registro_vinculado es None o no viene en el serializador.
        When: Se construye el mensaje de éxito.
        Then: El mensaje no debe incluir la coletilla "Vinculada al hermano Nº..." para evitar confusión.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        mock_puesto = MagicMock(nombre="Cirio")
        mock_serializer_class.return_value.is_valid.return_value = True
        mock_serializer_class.return_value.validated_data = {
            'acto': MagicMock(),
            'puesto': mock_puesto,
            'numero_registro_vinculado': None
        }

        mock_service_method.return_value = MagicMock(id=1, numero_papeleta=None, fecha_solicitud="2026-03-20")

        view = SolicitarCirioView.as_view()

        response = view(request)

        mensaje_esperado = "Solicitud para Cirio realizada correctamente."
        self.assertEqual(response.data["mensaje"], mensaje_esperado)
        self.assertNotIn("Vinculada al", response.data["mensaje"])



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_serializer_invalido_devuelve_400(self, mock_print, mock_serializer_class):
        """
        Test: Serializer inválido

        Given: Una petición con datos que no superan las validaciones del serializador.
        When: Se llama a serializer.is_valid().
        Then: La vista debe retornar un status 400 BAD REQUEST y el contenido de serializer.errors.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        serializer_instance = mock_serializer_class.return_value
        serializer_instance.is_valid.return_value = False
        serializer_instance.errors = {"acto": ["Este campo es obligatorio."]}

        view = SolicitarCirioView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, serializer_instance.errors)

        self.assertIn("acto", response.data)



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_serializer_invalido_con_multiples_errores(self, mock_print, mock_serializer_class):
        """
        Test: Serializer inválido con múltiples errores

        Given: Una petición con varios campos erróneos (ej. acto y puesto).
        When: Se procesa la validación del serializador.
        Then: La vista debe devolver todos los errores acumulados por el serializador en la respuesta.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        errores_esperados = {
            "acto": ["ID de acto no válido."],
            "puesto": ["Este hermano ya tiene este puesto asignado."],
            "numero_registro_vinculado": ["El número de registro debe ser positivo."]
        }
        
        serializer_instance = mock_serializer_class.return_value
        serializer_instance.is_valid.return_value = False
        serializer_instance.errors = errores_esperados

        view = SolicitarCirioView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data["puesto"], ["Este hermano ya tiene este puesto asignado."])



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_django_validation_error_con_message(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: DjangoValidationError con .message

        Given: Un serializador válido pero un servicio que lanza una DjangoValidationError con un mensaje específico.
        When: El servicio detecta un error de negocio (ej. el hermano ya tiene una solicitud).
        Then: La vista debe capturar la excepción y usar el atributo .message para devolver el detalle en la respuesta 400.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True
        mock_serializer_class.return_value.validated_data = {'acto': MagicMock(), 'puesto': MagicMock()}

        mensaje_error = "Ya existe una solicitud activa para este acto."
        error_negocio = DjangoValidationError(mensaje_error)
        mock_service_method.side_effect = error_negocio

        view = SolicitarCirioView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data["detail"], mensaje_error)



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_django_validation_error_sin_message(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: DjangoValidationError sin .message

        Given: Un servicio que lanza una excepción de validación que no posee el atributo .message (u otra excepción de Django).
        When: Se captura la excepción en el bloque try/except.
        Then: La vista debe convertir el objeto de la excepción a string mediante str(e) para informar al usuario con un status 400.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True
        mock_serializer_class.return_value.validated_data = {'acto': MagicMock(), 'puesto': MagicMock()}

        mock_service_method.side_effect = DjangoValidationError({"puesto": "Puesto no disponible."})

        view = SolicitarCirioView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("puesto", str(response.data["detail"]))



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_error_interno_servidor_devuelve_500(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: Exception genérica (Error 500)

        Given: Un flujo donde el servicio encuentra un error crítico e inesperado (Exception).
        When: Se ejecuta la lógica de la vista y el servicio lanza un crash no controlado.
        Then: La vista debe capturar la excepción genérica y retornar un status 500 con un mensaje de error interno.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True
        mock_serializer_class.return_value.validated_data = {'acto': MagicMock(), 'puesto': MagicMock()}

        mock_service_method.side_effect = Exception("Error crítico de base de datos")

        view = SolicitarCirioView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detail"], "Error interno del servidor.")



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_exception_ejecuta_print_de_error(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: Exception + verificación de print

        Given: Una excepción inesperada capturada por el bloque genérico.
        When: La vista procesa el error.
        Then: Se debe llamar a la función print() para registrar el detalle del error en los logs del servidor antes de enviar la respuesta.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={})
        force_authenticate(request, user=MagicMock())

        mock_serializer_class.return_value.is_valid.return_value = True

        error_mensaje = "Fallo en el sistema de archivos"
        mock_service_method.side_effect = Exception(error_mensaje)

        view = SolicitarCirioView.as_view()

        view(request)

        mock_print.assert_called()

        args, _ = mock_print.call_args
        self.assertIn(error_mensaje, args[0])
        self.assertIn("Error en SolicitarCirioView", args[0])



    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioSerializer")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.SolicitudCirioTradicionalService.procesar_solicitud_cirio_tradicional")
    @patch("api.vistas.solicitud_cirio.solicitud_cirio_view.print")
    def test_numero_registro_vinculado_cero_no_añade_texto(self, mock_print, mock_service_method, mock_serializer_class):
        """
        Test: numero_registro_vinculado = 0 (Edge Case)

        Given: Una solicitud donde el número de registro vinculado es 0.
        When: La vista construye el mensaje de éxito evaluando 'if numero_vinculado'.
        Then: El mensaje no debe incluir el texto de vinculación, ya que 0 se evalúa como Falsy en Python.
        """
        factory = APIRequestFactory()
        request = factory.post("/papeletas/solicitar-cirio/", data={"numero_registro_vinculado": 0})
        force_authenticate(request, user=MagicMock())

        mock_puesto = MagicMock(nombre="Cirio")
        mock_serializer_class.return_value.is_valid.return_value = True
        mock_serializer_class.return_value.validated_data = {
            'acto': MagicMock(),
            'puesto': mock_puesto,
            'numero_registro_vinculado': 0
        }

        mock_service_method.return_value = MagicMock(id=1, numero_papeleta=None, fecha_solicitud="2026-03-20")

        view = SolicitarCirioView.as_view()

        response = view(request)

        mensaje_esperado = "Solicitud para Cirio realizada correctamente."
        self.assertEqual(response.data["mensaje"], mensaje_esperado)

        self.assertNotIn("Vinculada", response.data["mensaje"])

        mock_service_method.assert_called_once()
        args, kwargs = mock_service_method.call_args
        self.assertEqual(kwargs['numero_registro_vinculado'], 0)