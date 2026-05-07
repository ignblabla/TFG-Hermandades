import unittest
from unittest.mock import MagicMock, patch
from django.core.exceptions import PermissionDenied

from api.servicios.solicitud_baja.solicitud_baja_service import obtener_solicitudes_baja_admin



class TestObtenerSolicitudesBajaAdmin(unittest.TestCase):

    @patch('api.servicios.solicitud_baja.solicitud_baja_service.SolicitudBaja.objects')
    def test_obtener_solicitudes_baja_admin_exito(self, mock_objects):
        """
        Test: Acceso Autorizado (Happy Path)
        
        Given: Un usuario con permisos de administrador (esAdmin=True).
        When: Se solicita el listado de bajas.
        Then: El servicio retorna el QuerySet optimizado con select_related y ordenado por fecha.
        """
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = True

        mock_queryset_final = MagicMock()
        mock_objects.select_related.return_value.all.return_value.order_by.return_value = mock_queryset_final

        resultado = obtener_solicitudes_baja_admin(mock_usuario)

        mock_objects.select_related.assert_called_once_with('hermano')
        mock_objects.select_related.return_value.all.return_value.order_by.assert_called_once_with('-fecha_solicitud')
        self.assertIs(resultado, mock_queryset_final)



    @patch('api.servicios.solicitud_baja.solicitud_baja_service.SolicitudBaja.objects')
    def test_obtener_solicitudes_baja_admin_denegado(self, mock_objects):
        """
        Test: Seguridad (Usuario no administrador)
        
        Given: Un usuario cuyo atributo esAdmin es False o inexistente.
        When: Intenta acceder al listado.
        Then: Lanza PermissionDenied y no consulta la base de datos.
        """
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = False

        with self.assertRaises(PermissionDenied) as context:
            obtener_solicitudes_baja_admin(mock_usuario)
        
        self.assertEqual(
            str(context.exception), 
            "No tiene permisos de administrador para visualizar las solicitudes de baja."
        )
        mock_objects.select_related.assert_not_called()