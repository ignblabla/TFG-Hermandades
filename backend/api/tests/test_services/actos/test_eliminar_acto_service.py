from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404

from api.servicios.acto.acto_service import delete_acto_service


class DeleteActoServiceTests(TestCase):

    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_admin_eliminacion_exitosa(self, mock_get_object_or_404):
        """
        Test: Usuario admin y acto sin papeletas -> eliminación exitosa

        Given: Un usuario solicitante con el atributo esAdmin a True 
            y un ID de acto existente. El acto no tiene papeletas vinculadas.
        When: Se llama al servicio delete_acto_service.
        Then: El servicio recupera el acto, invoca su método delete() 
            y retorna el valor booleano True.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        acto_id = 1

        acto_mock = MagicMock()
        acto_mock.papeletas.exists.return_value = False
        mock_get_object_or_404.return_value = acto_mock

        resultado = delete_acto_service(usuario_admin, acto_id)

        mock_get_object_or_404.assert_called_once()
        acto_mock.papeletas.exists.assert_called_once()
        acto_mock.delete.assert_called_once()
        self.assertTrue(resultado)



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_no_admin_lanza_permission_denied(self, mock_get_object_or_404):
        """
        Test: Usuario NO admin -> PermissionDenied

        Given: Un usuario solicitante cuyo atributo 'esAdmin' es False.
        When: Se intenta llamar al servicio delete_acto_service para eliminar un acto.
        Then: El servicio eleva una excepción PermissionDenied.
            get_object_or_404 NO es llamado, protegiendo el acceso a BD.
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False
        acto_id = 1

        with self.assertRaises(PermissionDenied) as context:
            delete_acto_service(usuario_no_admin, acto_id)

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para eliminar actos."
        )
        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_sin_atributo_es_admin_lanza_permission_denied(self, mock_get_object_or_404):
        """
        Test: Usuario sin atributo esAdmin -> PermissionDenied

        Given: Un objeto de usuario que no posee el atributo 'esAdmin'.
        When: Se intenta llamar al servicio delete_acto_service.
        Then: La función getattr retorna False por defecto.
            El servicio lanza PermissionDenied y get_object_or_404 NO se ejecuta.
        """
        class UsuarioSinAtributos:
            pass
            
        usuario_vacio = UsuarioSinAtributos()
        acto_id = 1

        with self.assertRaises(PermissionDenied) as context:
            delete_acto_service(usuario_vacio, acto_id)

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para eliminar actos."
        )
        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_acto_no_encontrado_lanza_404(self, mock_get_object_or_404):
        """
        Test: Acto inexistente -> Http404

        Given: Un usuario admin y un ID de acto que no existe en BD.
        When: Se llama al servicio delete_acto_service.
        Then: get_object_or_404 lanza la excepción Http404.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        acto_id = 999

        mock_get_object_or_404.side_effect = Http404()

        with self.assertRaises(Http404):
            delete_acto_service(usuario_admin, acto_id)



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_acto_con_papeletas_lanza_validation_error(self, mock_get_object_or_404):
        """
        Test: Acto con papeletas -> ValidationError

        Given: Un usuario admin y un ID de acto válido, pero el acto 
            ya tiene papeletas de sitio vinculadas (exists() == True).
        When: Se llama al servicio delete_acto_service.
        Then: Se eleva una excepción ValidationError indicando el motivo.
            El método delete() del acto NO debe ejecutarse.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        acto_id = 1

        acto_mock = MagicMock()

        acto_mock.papeletas.exists.return_value = True  
        mock_get_object_or_404.return_value = acto_mock

        with self.assertRaises(ValidationError) as context:
            delete_acto_service(usuario_admin, acto_id)

        self.assertIn("No se puede eliminar un acto que ya tiene papeletas", str(context.exception))

        acto_mock.papeletas.exists.assert_called_once()
        acto_mock.delete.assert_not_called()