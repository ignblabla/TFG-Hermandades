from unittest.mock import PropertyMock, call, patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError

from api.vistas.acto.crear_acto_view import ActoCreateView


class TestActoCreateView(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ActoCreateView.as_view()
        self.path = "/api/actos/crear/"
        self.mock_user = MagicMock()


    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_creacion_exitosa_de_acto(self, mock_serializer_class, mock_service):
        """
        Test: Creación exitosa de acto
        
        Given: Un usuario autenticado y datos válidos en la petición.
        When: Se procesa el POST.
        Then: Se valida el serializador, se llama al servicio y se retorna 201 
            con los datos del nuevo acto serializados.
        """
        data = {'nombre': 'Evento Test'}
        request = self.factory.post(self.path, data)
        force_authenticate(request, user=self.mock_user)

        mock_ser_in = MagicMock()
        mock_ser_in.is_valid.return_value = True
        mock_ser_in.validated_data = data

        mock_acto_instancia = MagicMock()
        mock_service.return_value = mock_acto_instancia

        mock_ser_out = MagicMock()
        mock_ser_out.data = {'id': 1, **data}

        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, mock_ser_out.data)
        mock_service.assert_called_once_with(self.mock_user, data)



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_servicio_devuelve_acto_correctamente_serializado(self, mock_serializer_class, mock_service):
        """
        Test: Service devuelve acto correctamente serializado
        
        Given: Una creación de acto exitosa en la capa de servicio.
        When: La vista prepara la respuesta final.
        Then: Se verifica que se instancia un segundo serializador (salida) con el acto 
            creado y se utiliza su propiedad .data para el cuerpo de la respuesta.
        """
        request = self.factory.post(self.path, {'nombre': 'Test'})
        force_authenticate(request, user=self.mock_user)

        mock_ser_in = MagicMock(name="SerializerEntrada")
        mock_ser_in.is_valid.return_value = True

        mock_acto_creado = MagicMock(name="InstanciaActo")
        mock_service.return_value = mock_acto_creado
        
        mock_ser_out = MagicMock(name="SerializerSalida")
        mock_ser_out.data = {'id': 99, 'nombre': 'Test'}

        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]

        response = self.view(request)

        from unittest.mock import call
        self.assertEqual(mock_serializer_class.call_args_list[1], call(mock_acto_creado))

        self.assertEqual(response.data, mock_ser_out.data)



    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_validacion_correcta_de_serializer_de_entrada(self, mock_serializer_class):
        """
        Test: Validación correcta de serializer de entrada
        
        Given: Una petición con datos en formato JSON.
        When: La vista recibe los datos y los pasa al serializador.
        Then: Se verifica que se instancia el serializador con los datos correctos 
            y se llama a .is_valid().
        """
        data_input = {'nombre': 'Validación Exitosa'}
        request = self.factory.post(self.path, data_input, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock(name="SerializerEntrada")
        mock_ser.is_valid.return_value = True

        mock_ser_out = MagicMock(name="SerializerSalida")
        mock_ser_out.data = {}
        
        mock_serializer_class.side_effect = [mock_ser, mock_ser_out]

        with patch('api.vistas.acto.crear_acto_view.crear_acto_service'):
            self.view(request)

        mock_serializer_class.assert_any_call(data=data_input)
        mock_ser.is_valid.assert_called_once()



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_serializer_invalido_retorna_400_con_errores(self, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido → 400 con errores
        
        Given: Una petición con datos que fallan la validación del serializador.
        When: serializer.is_valid() devuelve False.
        Then: Se retorna status 400, se devuelven los errores del serializador 
            y se garantiza que el servicio no es invocado.
        """
        request = self.factory.post(self.path, {'nombre': ''}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock(name="SerializerInvalido")
        mock_ser.is_valid.return_value = False
        mock_ser.errors = {'nombre': ['Este campo no puede estar en blanco.']}
        mock_serializer_class.return_value = mock_ser

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, mock_ser.errors)
        mock_service.assert_not_called()



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_django_validation_error_con_message_dict_retorna_diccionario(self, mock_serializer_class, mock_service):
        """
        Test: DjangoValidationError con message_dict → 400 con diccionario
        
        Given: El serializador es válido pero el servicio detecta un error de negocio complejo.
        When: El servicio lanza DjangoValidationError con un diccionario de mensajes.
        Then: La vista captura la excepción y retorna el message_dict con status 400.
        """
        request = self.factory.post(self.path, {'nombre': 'Test'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.return_value = mock_ser

        errores_negocio = {'cupo': ['No quedan plazas disponibles para este acto.']}
        mock_service.side_effect = DjangoValidationError(errores_negocio)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, errores_negocio)



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_django_validation_error_sin_message_dict_retorna_detail(self, mock_serializer_class, mock_service):
        """
        Test: DjangoValidationError sin message_dict → 400 con detail
        
        Given: El servicio detecta un error general de validación.
        When: Se lanza DjangoValidationError con un mensaje simple (string).
        Then: La vista retorna un diccionario con la clave 'detail' y status 400.
        """
        request = self.factory.post(self.path, {'nombre': 'Test'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.return_value = mock_ser

        mensaje_error = "Error general de validación en el servidor."
        mock_service.side_effect = DjangoValidationError(mensaje_error)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': f"['{mensaje_error}']"})



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_permission_denied_retorna_403(self, mock_serializer_class, mock_service):
        """
        Test: PermissionDenied → 403
        
        Given: Un usuario que no tiene permisos para realizar la acción.
        When: El servicio lanza una excepción PermissionDenied.
        Then: Se retorna un status 403 y el mensaje de error en la clave 'detail'.
        """
        request = self.factory.post(self.path, {'nombre': 'Privado'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.return_value = mock_ser

        mensaje_error = "No tienes permisos para crear actos."
        mock_service.side_effect = PermissionDenied(mensaje_error)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': mensaje_error})



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_error_inesperado_en_service_se_propaga(self, mock_serializer_class, mock_service):
        """
        Test: Error inesperado en service
        
        Given: Un fallo crítico no controlado en el servicio (ej. DatabaseError).
        When: Se ejecuta la lógica de creación.
        Then: La vista no captura la excepción (no hay bloque except genérico) 
            y se propaga al middleware de Django.
        """
        request = self.factory.post(self.path, {'nombre': 'Test'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.return_value = mock_ser
        
        mock_service.side_effect = RuntimeError("Fallo catastrófico")

        with self.assertRaises(RuntimeError):
            self.view(request)



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_usuario_en_request_correctamente_pasado_al_servicio(self, mock_serializer_class, mock_service):
        """
        Test: Usuario en request correctamente pasado al servicio
        
        Given: Una petición de un usuario autenticado.
        When: El serializador es válido.
        Then: Se verifica que el objeto request.user se pasa íntegro como primer 
            argumento a la función crear_acto_service.
        """
        request = self.factory.post(self.path, {'nombre': 'Test'}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = {'nombre': 'Test'}
        mock_serializer_class.return_value = mock_ser

        mock_service.return_value = MagicMock()

        self.view(request)

        args, _ = mock_service.call_args
        self.assertEqual(args[0], self.mock_user)



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_post_crear_acto_error_permisos_retorna_403(self, mock_serializer_class, mock_service):
        """
        Test: Captura de PermissionDenied en la vista
        
        Given: Un usuario autenticado que NO es administrador.
        When: El servicio crear_acto_service lanza PermissionDenied.
        Then: La vista captura la excepción y retorna status 403 con el mensaje 
            dentro de la clave 'detail'.
        """
        data_input = {'nombre': 'Acto Prohibido'}
        request = self.factory.post(self.path, data_input, format='json')

        self.mock_user.esAdmin = False
        force_authenticate(request, user=self.mock_user)

        mock_ser_in = MagicMock(name="SerializerEntrada")
        mock_ser_in.is_valid.return_value = True
        mock_ser_in.validated_data = data_input
        mock_serializer_class.return_value = mock_ser_in

        mensaje_esperado = "No tienes permisos para crear actos. Se requiere ser Administrador."
        mock_service.side_effect = PermissionDenied(mensaje_esperado)

        response = self.view(request)

        mock_service.assert_called_once_with(self.mock_user, data_input)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': mensaje_esperado})



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_transversal_flujo_correcto_completo_happy_path(self, mock_serializer_class, mock_service):
        """
        Test: Flujo correcto completo (happy path)
        
        Given: Una petición válida.
        When: Se procesa el POST.
        Then: Se verifica el orden: Serializer Input -> Service -> Serializer Output -> Response 201.
        """
        data_input = {'nombre': 'Acto Transversal'}
        request = self.factory.post(self.path, data_input, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser_in = MagicMock(name="SerIn")
        mock_ser_in.is_valid.return_value = True
        mock_ser_in.validated_data = data_input
        
        mock_acto_creado = MagicMock(name="InstanciaActo")
        mock_service.return_value = mock_acto_creado
        
        mock_ser_out = MagicMock(name="SerOut")
        mock_ser_out.data = {'id': 1, **data_input}
        
        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]

        manager = MagicMock()
        manager.attach_mock(mock_serializer_class, 'instanciar_serializer')
        manager.attach_mock(mock_ser_in.is_valid, 'validar')
        manager.attach_mock(mock_service, 'ejecutar_servicio')

        response = self.view(request)

        expected_calls = [
            call.instanciar_serializer(data=data_input),
            call.validar(),
            call.ejecutar_servicio(self.mock_user, data_input),
            call.instanciar_serializer(mock_acto_creado)
        ]
        manager.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_transversal_no_se_llama_al_service_si_serializer_no_es_valido(self, mock_serializer_class, mock_service):
        """
        Test: No se llama al service si serializer no es válido
        
        Validaciones: El flujo se interrumpe inmediatamente después de is_valid() False.
        """
        request = self.factory.post(self.path, {}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = False
        mock_serializer_class.return_value = mock_ser

        self.view(request)

        mock_service.assert_not_called()



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_transversal_validacion_de_payload_enviado_al_service(self, mock_serializer_class, mock_service):
        """
        Test: Validación de payload enviado al service
        
        Given: Un diccionario de datos validados por el serializador.
        When: Se invoca al servicio de creación.
        Then: Se garantiza que crear_acto_service recibe exactamente el atributo 
            validated_data del serializador, asegurando la limpieza de datos.
        """
        request = self.factory.post(self.path, {'nombre': 'Limpio'}, format='json')
        force_authenticate(request, user=self.mock_user)

        datos_limpios = {'nombre': 'Limpio', 'sistema': True}
        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = datos_limpios

        mock_serializer_class.side_effect = [mock_ser, MagicMock()]
        mock_service.return_value = MagicMock()

        self.view(request)

        mock_service.assert_called_once_with(self.mock_user, datos_limpios)