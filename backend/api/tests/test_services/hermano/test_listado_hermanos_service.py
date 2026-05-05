from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from api.servicios.hermano.hermano_service import get_listado_hermanos_service


class TestListadoHermanosService(TestCase):

    @patch('api.servicios.hermano.hermano_service.User.objects.all') 
    def test_get_listado_hermanos_service_admin(self, mock_user_all):
        """
        Test: Usuario administrador -> retorna listado ordenado
        
        Given: Un usuario solicitante con esAdmin = True.
        When: Se llama a get_listado_hermanos_service con dicho usuario.
        Then: No lanza excepción, llama a User.objects.all().order_by('numero_registro') y retorna el listado.
        """
        mock_queryset_all = MagicMock()
        mock_queryset_ordenado = MagicMock()

        mock_user_all.return_value = mock_queryset_all
        mock_queryset_all.order_by.return_value = mock_queryset_ordenado
        
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        resultado = get_listado_hermanos_service(usuario_admin)

        mock_user_all.assert_called_once()
        mock_queryset_all.order_by.assert_called_once_with('numero_registro')
        assert resultado == mock_queryset_ordenado



    @patch('api.servicios.hermano.hermano_service.User.objects.all')
    def test_get_listado_hermanos_service_no_admin(self, mock_user_all):
        """
        Test: Usuario no administrador -> lanza PermissionDenied
        
        Given: Un usuario solicitante con esAdmin = False.
        When: Se intenta acceder al listado de hermanos.
        Then: Se lanza una excepción PermissionDenied y no se accede al ORM.
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False

        with self.assertRaises(PermissionDenied) as cm:
            get_listado_hermanos_service(usuario_no_admin)

        assert str(cm.exception) == "No tienes permisos para visualizar el listado de hermanos."
        mock_user_all.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.User.objects.all')
    def test_get_listado_hermanos_service_sin_atributo_esadmin(self, mock_user_all):
        """
        Test: Usuario sin atributo esAdmin -> lanza PermissionDenied
        
        Given: Un objeto de usuario que carece por completo del atributo 'esAdmin'.
        When: Se intenta acceder al listado.
        Then: Se usa getattr con valor por defecto False, se lanza PermissionDenied y no se llama al ORM.
        """
        usuario_sin_atributo = MagicMock(spec=[])

        with self.assertRaises(PermissionDenied):
            get_listado_hermanos_service(usuario_sin_atributo)

        mock_user_all.assert_not_called()