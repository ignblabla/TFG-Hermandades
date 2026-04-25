from unittest.mock import MagicMock, patch
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from api.vistas.acto.acto_view import ActoCreateView


class ActoCreateViewTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ActoCreateView.as_view()
        self.url = reverse('crear_acto')

        self.user = MagicMock()
        self.user.esAdmin = True 
        self.user.is_authenticated = True

        self.data_valida = {
            'nombre': 'Ensayo de Costaleros',
            'lugar': 'Casa Hermandad',
            'fecha': '2026-10-10T10:00:00Z',
            'tipo_acto': 'CONVIVENCIA'
        }



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_request_valido_creacion_correcta(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Request válido -> creación correcta

        Given: Un payload con datos de acto válidos y un usuario administrador.
                El serializador valida correctamente los datos y el servicio devuelve un objeto acto.
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista devuelve el status HTTP 201 CREATED.
                La respuesta contiene los datos serializados del acto creado.
                El servicio crear_acto_service es invocado exactamente con el usuario de la request y los datos validados.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance

        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = self.data_valida

        datos_serializados_esperados = {
            'id': 1, 
            'nombre': 'Ensayo de Costaleros', 
            'lugar': 'Casa Hermandad',
            'fecha': '2026-10-10T10:00:00Z',
            'tipo_acto': 'CONVIVENCIA'
        }
        mock_serializer_instance.data = datos_serializados_esperados

        mock_acto_creado = MagicMock()
        mock_crear_acto_service.return_value = mock_acto_creado

        request = self.factory.post(self.url, self.data_valida, format='json')

        force_authenticate(request, user=self.user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, datos_serializados_esperados)
        mock_serializer_instance.is_valid.assert_called_once()
        mock_crear_acto_service.assert_called_once_with(self.user, self.data_valida)



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_validacion_correcta_con_distintos_datos_validos(self, MockSerializerClass, mock_crear_acto_service):
        # [2026-03-04]
        """
        Test: Validación correcta con distintos datos válidos

        Given: Diferentes conjuntos de datos (ej. un acto sin descripción o con distinta modalidad).
                El serializador valida estos datos y el servicio responde correctamente.
        When: Se realiza una petición POST a la vista con estas variantes.
        Then: La vista debe procesar cada petición correctamente, demostrando que no depende 
                de valores específicos de los campos sino del estado de validación.
        """
        variantes_datos = [
            {
                'nombre': 'Acto Mínimo',
                'lugar': 'Parroquia',
                'fecha': '2026-12-12T20:00:00Z',
                'tipo_acto': 'QUINARIO'
            },
            {
                'nombre': 'Acto Completo',
                'lugar': 'Sede',
                'descripcion': 'Una descripción larga...',
                'fecha': '2026-11-11T18:00:00Z',
                'modalidad': 'TRADICIONAL',
                'tipo_acto': 'ESTACION_PENITENCIA'
            }
        ]

        for data_mock in variantes_datos:
            mock_serializer_instance = MagicMock()
            MockSerializerClass.return_value = mock_serializer_instance
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.validated_data = data_mock
            mock_serializer_instance.data = data_mock
            
            mock_crear_acto_service.return_value = MagicMock()

            request = self.factory.post(self.url, data_mock, format='json')
            force_authenticate(request, user=self.user)
            response = self.view(request)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data, data_mock)

            mock_crear_acto_service.assert_called_with(self.user, data_mock)



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_serializer_invalido_no_crea_acto_y_devuelve_400(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Serializer inválido

        Given: Un payload con datos incompletos o erróneos.
                El serializador determina que los datos no son válidos (is_valid() -> False).
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista devuelve el status HTTP 400 BAD REQUEST.
                La respuesta contiene el diccionario de errores generado por el serializador.
                El servicio crear_acto_service NO es invocado en ningún momento.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance

        mock_serializer_instance.is_valid.return_value = False
        errores_esperados = {
            'nombre': ['Este campo es requerido.'],
            'fecha': ['Formato de fecha no válido.']
        }
        mock_serializer_instance.errors = errores_esperados

        request = self.factory.post(self.url, {}, format='json')
        force_authenticate(request, user=self.user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, errores_esperados)

        mock_crear_acto_service.assert_not_called()



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_servicio_lanza_django_validation_error_con_message_dict(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Errores del servicio -> DjangoValidationError con message_dict

        Given: El serializador es válido.
                El servicio crear_acto_service lanza una excepción DjangoValidationError 
                que contiene un atributo 'message_dict' (errores de validación de modelo).
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista captura la excepción y entra en la rama 'hasattr(e, "message_dict")'.
                Se responde con un status HTTP 400 BAD REQUEST.
                El cuerpo de la respuesta es exactamente el diccionario de errores del servicio.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = self.data_valida

        errores_modelo = {
            'fin_solicitud': ['El fin de solicitud debe ser posterior al inicio.'],
            'non_field_errors': ['Ya existe un acto similar para esta fecha.']
        }
        exception_mock = DjangoValidationError(errores_modelo)
        mock_crear_acto_service.side_effect = exception_mock

        request = self.factory.post(self.url, self.data_valida, format='json')
        force_authenticate(request, user=self.user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, errores_modelo)

        mock_crear_acto_service.assert_called_once()



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_servicio_lanza_django_validation_error_sin_message_dict(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: DjangoValidationError sin message_dict

        Given: El serializador es válido.
                El servicio lanza una DjangoValidationError con un mensaje simple (string),
                lo que implica que no posee el atributo 'message_dict'.
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista captura la excepción y entra en la rama alternativa (else del hasattr).
                Se responde con un status HTTP 400 BAD REQUEST.
                El cuerpo de la respuesta contiene el error bajo la clave 'detail' como un string.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = self.data_valida

        error_simple_texto = "El nombre del acto contiene palabras no permitidas."
        exception_mock = DjangoValidationError(error_simple_texto)

        mock_crear_acto_service.side_effect = exception_mock

        request = self.factory.post(self.url, self.data_valida, format='json')
        force_authenticate(request, user=self.user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        expected_response_detail = str(exception_mock)
        self.assertEqual(response.data, {'detail': expected_response_detail})

        mock_crear_acto_service.assert_called_once()



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_servicio_lanza_permission_denied_devuelve_403(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Errores del servicio -> PermissionDenied

        Given: El serializador valida los datos correctamente.
                El servicio crear_acto_service lanza una excepción PermissionDenied
                (ej. el usuario no tiene el rol de Administrador requerido).
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista captura la excepción en el bloque 'except PermissionDenied'.
                Se responde con un status HTTP 403 FORBIDDEN.
                El cuerpo de la respuesta contiene el mensaje de error bajo la clave 'detail'.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = self.data_valida

        mensaje_error_permisos = "No tienes permisos para crear actos. Se requiere ser Administrador."
        exception_mock = PermissionDenied(mensaje_error_permisos)
        mock_crear_acto_service.side_effect = exception_mock

        request = self.factory.post(self.url, self.data_valida, format='json')
        force_authenticate(request, user=self.user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.data, {'detail': mensaje_error_permisos})

        mock_crear_acto_service.assert_called_once_with(self.user, self.data_valida)



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_servicio_devuelve_objeto_inesperado_pero_la_vista_serializa_la_salida(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Casos límite -> crear_acto_service devuelve objeto inesperado

        Given: El serializador de entrada es válido.
                El servicio devuelve un objeto con una estructura inusual (ej. un mock genérico
                o un objeto con datos parciales).
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista debe instanciar el serializador de salida con ese objeto.
                Se devuelve el status HTTP 201 CREATED.
                La respuesta contiene lo que el serializador de salida dicte, demostrando 
                que la vista no manipula el objeto manualmente.
        """
        mock_input_serializer = MagicMock()
        mock_output_serializer = MagicMock()

        MockSerializerClass.side_effect = [mock_input_serializer, mock_output_serializer]
        
        mock_input_serializer.is_valid.return_value = True
        mock_input_serializer.validated_data = self.data_valida

        objeto_inesperado = {"dato_extraño": "valor_no_mapeado"}
        mock_crear_acto_service.return_value = objeto_inesperado

        data_final = {"id": 99, "nombre": "Nombre Normalizado"}
        mock_output_serializer.data = data_final

        request = self.factory.post(self.url, self.data_valida, format='json')
        force_authenticate(request, user=self.user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, data_final)

        MockSerializerClass.assert_any_call(objeto_inesperado)



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_serializer_validado_vacio_pero_valido_con_payload_minimo(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Casos límite -> serializer.validated_data vacío pero válido

        Given: El cliente envía un payload mínimo o vacío que el serializador acepta 
                como válido (is_valid() -> True), resultando en un validated_data vacío.
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista debe llamar al servicio con el diccionario vacío.
                Se devuelve el status HTTP 201 CREATED.
                La vista no debe romperse al manejar un conjunto de datos vacío.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance

        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = {}

        mock_acto = MagicMock()
        mock_crear_acto_service.return_value = mock_acto

        datos_minimos = {'id': 100}
        mock_serializer_instance.data = datos_minimos

        request = self.factory.post(self.url, {}, format='json')
        force_authenticate(request, user=self.user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, datos_minimos)

        mock_crear_acto_service.assert_called_once_with(self.user, {})



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    @patch('api.vistas.acto.acto_view.ActoCreateView.get_permissions')
    def test_usuario_en_request_es_anonymous_user(self, mock_get_permissions, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Usuario en request es AnonymousUser

        Given: El serializador es válido y el usuario es anónimo.
                Se desactivan los permisos de DRF para asegurar que llegamos al servicio.
                El servicio lanza una excepción de Permisos personalizada.
        When: Se realiza una petición POST.
        Then: La vista captura la excepción del SERVICIO y devuelve el mensaje en español.
        """
        mock_get_permissions.return_value = []

        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = self.data_valida

        usuario_anonimo = AnonymousUser()

        mensaje_error = "No tienes permisos para crear actos. Se requiere ser Administrador."
        mock_crear_acto_service.side_effect = PermissionDenied(mensaje_error)

        request = self.factory.post(self.url, self.data_valida, format='json')
        force_authenticate(request, user=usuario_anonimo)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(str(response.data['detail']), mensaje_error)

        mock_crear_acto_service.assert_called_once_with(usuario_anonimo, self.data_valida)



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_serializer_se_instancia_con_los_datos_de_la_request(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Verificar que el serializer se instancia correctamente

        Given: Un payload enviado por el cliente en la petición.
        When: Se realiza una petición POST a la vista ActoCreateView.
        Then: La vista debe instanciar el ActoCreateSerializer pasando los datos 
                recibidos en el argumento 'data'.
                Esto asegura que la validación se realice sobre la información correcta.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance

        mock_serializer_instance.is_valid.return_value = False 
        mock_serializer_instance.errors = {}

        payload_cliente = {'campo_prueba': 'valor_prueba'}

        request = self.factory.post(self.url, payload_cliente, format='json')
        force_authenticate(request, user=self.user)
        
        self.view(request)

        MockSerializerClass.assert_called_once_with(data=payload_cliente)



    @patch('api.vistas.acto.acto_view.crear_acto_service')
    @patch('api.vistas.acto.acto_view.ActoCreateSerializer')
    def test_vista_pasa_validated_data_al_servicio_en_lugar_de_data_cruda(self, MockSerializerClass, mock_crear_acto_service):
        """
        Test: Verificar que se usa validated_data (no data)

        Given: Un payload enviado por el cliente.
                El serializador transforma esos datos en un diccionario validado 
                (que puede ser diferente al original, ej. convirtiendo strings en objetos).
        When: Se realiza una petición POST a la vista.
        Then: La llamada al servicio crear_acto_service debe realizarse exclusivamente 
                con el contenido de serializer.validated_data, garantizando la integridad de los datos.
        """
        mock_serializer_instance = MagicMock()
        MockSerializerClass.return_value = mock_serializer_instance

        data_cruda = {'nombre': '  Ensayo con espacios  '}
        data_validada = {'nombre': 'Ensayo con espacios'}
        
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = data_validada

        mock_serializer_instance.data = {'id': 1}
        mock_crear_acto_service.return_value = MagicMock()

        request = self.factory.post(self.url, data_cruda, format='json')
        force_authenticate(request, user=self.user)
        
        self.view(request)

        self.assertNotEqual(mock_crear_acto_service.call_args[0][1], data_cruda)

        mock_crear_acto_service.assert_called_once_with(self.user, data_validada)