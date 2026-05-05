from unittest.mock import PropertyMock, patch, MagicMock
from django.http import Http404
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from api.servicios.hermano.hermano_service import update_hermano_por_admin_service, User

class TestUpdateHermanoPorAdminService(TestCase):

    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_service_atributos_normales(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> actualiza atributos correctamente
        
        Given: Un usuario administrador, el ID de un hermano existente y un diccionario con datos de actualización.
        When: Se ejecuta la actualización.
        Then: Se obtienen los datos mediante get_object_or_404, se actualizan los atributos, se llama a save() y retorna el objeto modificado.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        hermano_id = 1
        data_validada = {
            'nombre': 'Carlos',
            'email': 'carlos@example.com'
        }

        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        resultado = update_hermano_por_admin_service(usuario_admin, hermano_id, data_validada)

        mock_get_object_or_404.assert_called_once_with(User, pk=hermano_id)

        self.assertEqual(mock_hermano.nombre, 'Carlos')
        self.assertEqual(mock_hermano.email, 'carlos@example.com')

        mock_hermano.save.assert_called_once()
        self.assertEqual(resultado, mock_hermano)



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_password_valido(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> actualiza contraseña correctamente
        
        Given: Un usuario administrador y un diccionario de datos que incluye 'password'.
        When: Se ejecuta la actualización.
        Then: Se llama a set_password con el valor, no se usa setattr para password y se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        data_validada = {'password': 'nueva_password_segura'}
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        update_hermano_por_admin_service(usuario_admin, 1, data_validada)

        mock_hermano.set_password.assert_called_once_with('nueva_password_segura')

        mock_hermano.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_password_vacio(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> password vacío no actualiza contraseña
        
        Given: Un usuario administrador y un diccionario con 'password' como string vacío o None.
        When: Se procesan los datos.
        Then: NO se llama a set_password para evitar sobreescribir con vacío, pero se llama a save() por el resto del flujo.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        data_validada = {'password': ''}
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        update_hermano_por_admin_service(usuario_admin, 1, data_validada)

        mock_hermano.set_password.assert_not_called()
        mock_hermano.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_no_admin(self, mock_get_object_or_404):
        """
        Test: Usuario no administrador -> lanza PermissionDenied
        
        Given: Un usuario con esAdmin = False y unos datos de actualización.
        When: Se intenta ejecutar el servicio de actualización.
        Then: Se lanza PermissionDenied y no se llega a llamar a get_object_or_404.
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False
        data = {'nombre': 'Nuevo Nombre'}

        with self.assertRaises(PermissionDenied) as cm:
            update_hermano_por_admin_service(usuario_no_admin, 1, data)

        self.assertEqual(str(cm.exception), "No tienes permisos para editar los datos de otros hermanos.")
        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_sin_atributo(self, mock_get_object_or_404):
        """
        Test: Usuario sin atributo esAdmin -> lanza PermissionDenied
        
        Given: Un usuario que no dispone del atributo 'esAdmin'.
        When: El servicio usa getattr(usuario, 'esAdmin', False).
        Then: Se evalúa como False, lanza la excepción y no se llama a get_object_or_404.
        """
        usuario_sin_atributo = MagicMock(spec=[])

        with self.assertRaises(PermissionDenied):
            update_hermano_por_admin_service(usuario_sin_atributo, 1, {})

        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_admin_none(self, mock_get_object_or_404):
        """
        Test: Usuario con esAdmin = None -> lanza PermissionDenied
        
        Given: Un usuario solicitante cuyo atributo esAdmin es None.
        When: Se intenta realizar la actualización.
        Then: El valor None se evalúa como falso, se lanza PermissionDenied y no se llama a get_object_or_404.
        """
        usuario_admin_none = MagicMock()
        usuario_admin_none.esAdmin = None

        with self.assertRaises(PermissionDenied):
            update_hermano_por_admin_service(usuario_admin_none, 1, {})
        
        mock_get_object_or_404.assert_not_called()