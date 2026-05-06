import unittest
from unittest.mock import MagicMock, patch
from django.core.exceptions import PermissionDenied

from api.servicios.solicitud_baja.solicitud_baja_service import obtener_solicitudes_baja_admin



class TestObtenerSolicitudesBajaAdmin(unittest.TestCase):

    @patch('api.servicios.solicitud_baja.obtener_solicitudes_baja_admin_service.SolicitudBaja.objects')
    def test_obtener_solicitudes_baja_admin_exito(self, mock_objects):
        """
        Test: Acceso Autorizado y Contrato (Happy Path)
        
        Given: Un usuario con atributos de administrador (esAdmin=True).
        When: Se solicita el listado de solicitudes de baja.
        Then: El servicio retorna un QuerySet optimizado con select_related y ordenado por fecha de forma descendente.
        """
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = True

        mock_queryset_final = MagicMock()
        mock_objects.select_related.return_value.all.return_value.order_by.return_value = mock_queryset_final

        resultado = obtener_solicitudes_baja_admin(mock_usuario)

        mock_objects.select_related.assert_called_once_with('hermano')
        mock_objects.select_related.return_value.all.return_value.order_by.assert_called_once_with('-fecha_solicitud')
        self.assertIs(resultado, mock_queryset_final)



    @patch('api.servicios.solicitud_baja.obtener_solicitudes_baja_admin_service.SolicitudBaja.objects')
    def test_obtener_solicitudes_baja_admin_seguridad(self, mock_objects):
        """
        Test: Seguridad (Usuario no administrador)
        
        Given: Un usuario autenticado cuyo atributo esAdmin es False.
        When: Intenta acceder al listado de solicitudes reservado para administración.
        Then: Se lanza una excepción PermissionDenied y no se realiza ninguna consulta al ORM.
        """
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = False

        with self.assertRaises(PermissionDenied) as context:
            obtener_solicitudes_baja_admin(mock_usuario)
        
        self.assertEqual(str(context.exception), "No tiene permisos de administrador para visualizar las solicitudes de baja.")

        mock_objects.select_related.assert_not_called()



    def test_obtener_solicitudes_baja_admin_robustez_getattr(self):
        """
        Test: Robustez de Atributos (Garantía de getattr)
        
        Given: Un objeto de usuario incompleto o anónimo que carece del atributo 'esAdmin'.
        When: El servicio evalúa los permisos utilizando getattr.
        Then: El servicio deniega el acceso lanzando PermissionDenied al no encontrar una confirmación explícita de administrador.
        """
        usuario_incompleto = object() 

        with self.assertRaises(PermissionDenied):
            obtener_solicitudes_baja_admin(usuario_incompleto)