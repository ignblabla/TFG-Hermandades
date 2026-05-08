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

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True

        self.mock_normal = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_normal.is_authenticated = True
        self.mock_normal.esAdmin = False



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_creacion_exitosa_de_acto(self, mock_serializer_class, mock_service):
        """
        Test: Creación exitosa de acto
        
        Given: Un usuario administrador autenticado y datos válidos en la petición.
        When: Se procesa el POST.
        Then: Se valida el serializador, se llama al servicio y se retorna 201 
            con los datos del nuevo acto serializados.
        """
        data = {'nombre': 'Evento Test'}
        request = self.factory.post(self.path, data)
        force_authenticate(request, user=self.mock_admin)

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
        mock_service.assert_called_once_with(self.mock_admin, data)



    def test_usuario_no_admin_falla_403(self):
        """
        Test: Seguridad - Usuario sin permisos de administrador
        
        Given: Un usuario autenticado pero sin rol de administrador (esAdmin=False).
        When: Se intenta realizar una petición POST para crear un acto.
        Then: La permission_class EsAdministrador bloquea la petición con status 403.
        """
        data = {'nombre': 'Evento Test'}
        request = self.factory.post(self.path, data)
        force_authenticate(request, user=self.mock_normal)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    def test_usuario_no_autenticado_falla(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición POST sin credenciales.
        When: Se intenta acceder al endpoint.
        Then: Las permission_classes bloquean el acceso devolviendo 401/403.
        """
        data = {'nombre': 'Evento Test'}
        request = self.factory.post(self.path, data)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    @patch('api.vistas.acto.crear_acto_view.crear_acto_service')
    @patch('api.vistas.acto.crear_acto_view.ActoCreateSerializer')
    def test_serializer_invalido_retorna_400_con_errores(self, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido → 400 con errores
        
        Given: Una petición de un admin con datos que fallan la validación del serializador.
        When: serializer.is_valid() devuelve False.
        Then: Se retorna status 400, se devuelven los errores del serializador 
            y se garantiza que el servicio no es invocado.
        """
        request = self.factory.post(self.path, {'nombre': ''}, format='json')
        force_authenticate(request, user=self.mock_admin)

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
        force_authenticate(request, user=self.mock_admin)

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
        
        Given: El servicio detecta un error general de validación procesando la petición.
        When: Se lanza DjangoValidationError con un mensaje simple (string).
        Then: La vista retorna un diccionario con la clave 'detail' y status 400.
        """
        request = self.factory.post(self.path, {'nombre': 'Test'}, format='json')
        force_authenticate(request, user=self.mock_admin)

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
        
        Given: Un usuario admin que no supera las validaciones de permisos internos del servicio.
        When: El servicio lanza una excepción PermissionDenied.
        Then: Se retorna un status 403 y el mensaje de error en la clave 'detail'.
        """
        request = self.factory.post(self.path, {'nombre': 'Privado'}, format='json')
        force_authenticate(request, user=self.mock_admin)

        mock_ser = MagicMock()
        mock_ser.is_valid.return_value = True
        mock_serializer_class.return_value = mock_ser

        mensaje_error = "No tienes permisos de área para crear este acto."
        mock_service.side_effect = PermissionDenied(mensaje_error)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': mensaje_error})