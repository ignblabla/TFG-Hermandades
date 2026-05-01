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
    def test_get_listado_hermanos_service_lista_vacia(self, mock_user_all):
        """
        Test: Usuario administrador con lista vacía -> retorna lista vacía
        
        Given: Un usuario administrador y una base de datos sin hermanos.
        When: Se solicita el listado de hermanos.
        Then: No lanza excepción y retorna una colección vacía.
        """
        mock_queryset_all = MagicMock()

        mock_queryset_all.order_by.return_value = []
        mock_user_all.return_value = mock_queryset_all
        
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        resultado = get_listado_hermanos_service(usuario_admin)

        assert resultado == []
        mock_user_all.assert_called_once()
        mock_queryset_all.order_by.assert_called_once_with('numero_registro')



    @patch('api.servicios.hermano.hermano_service.User.objects.all')
    def test_get_listado_hermanos_service_verifica_orden(self, mock_user_all):
        """
        Test: Usuario administrador -> verifica orden por campo correcto
        
        Given: Un usuario administrador.
        When: Se ejecuta el servicio de listado.
        Then: El método .order_by debe ser invocado exactamente con el campo 'numero_registro'.
        """
        mock_queryset_all = MagicMock()
        mock_user_all.return_value = mock_queryset_all
        
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        get_listado_hermanos_service(usuario_admin)

        mock_queryset_all.order_by.assert_called_once_with('numero_registro')



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



    @patch('api.servicios.hermano.hermano_service.User.objects.all')
    def test_get_listado_hermanos_service_admin_none(self, mock_user_all):
        """
        Test: Usuario con esAdmin = None -> lanza PermissionDenied
        
        Given: Un usuario solicitante con esAdmin explícitamente en None.
        When: Se evalúa el permiso en el servicio.
        Then: None se evalúa como falso, se lanza PermissionDenied y no se accede al ORM.
        """
        usuario_admin_none = MagicMock()
        usuario_admin_none.esAdmin = None

        with self.assertRaises(PermissionDenied):
            get_listado_hermanos_service(usuario_admin_none)
        
        mock_user_all.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.User.objects.all')
    def test_get_listado_hermanos_service_error_db(self, mock_user_all):
        """
        Test: Error en acceso a datos (User.objects.all falla)
        
        Given: Un usuario administrador pero con un fallo en la base de datos.
        When: User.objects.all() es invocado.
        Then: La excepción (p.ej. RuntimeError) se propaga correctamente hacia arriba.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        mock_user_all.side_effect = RuntimeError("Error de conexión a la BD")

        with self.assertRaises(RuntimeError) as cm:
            get_listado_hermanos_service(usuario_admin)
        
        assert str(cm.exception) == "Error de conexión a la BD"



    @patch('api.servicios.hermano.hermano_service.User.objects.all')
    def test_get_listado_hermanos_service_error_ordenacion(self, mock_user_all):
        """
        Test: Error en ordenación (order_by falla)
        
        Given: Un usuario administrador y un queryset que falla al ordenar.
        When: Se intenta ejecutar .order_by('numero_registro').
        Then: La excepción se propaga correctamente.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        mock_queryset = MagicMock()
        mock_user_all.return_value = mock_queryset
        mock_queryset.order_by.side_effect = ValueError("Campo de ordenación no válido")

        with self.assertRaises(ValueError) as cm:
            get_listado_hermanos_service(usuario_admin)
        
        assert str(cm.exception) == "Campo de ordenación no válido"



    @patch('api.servicios.hermano.hermano_service.User.objects.all')
    def test_get_listado_hermanos_service_all_retorna_none(self, mock_user_all):
        """
        Test: Usuario admin pero User.objects.all() devuelve None
        
        Given: Un escenario donde el primer método del ORM devuelve None inesperadamente.
        When: El servicio intenta encadenar el método .order_by().
        Then: Se produce un AttributeError controlado al intentar acceder a .order_by en un NoneType.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        mock_user_all.return_value = None

        with self.assertRaises(AttributeError):
            get_listado_hermanos_service(usuario_admin)