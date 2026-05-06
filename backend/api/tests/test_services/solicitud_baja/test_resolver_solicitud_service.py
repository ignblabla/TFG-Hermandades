import unittest
from unittest.mock import MagicMock, patch
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import datetime

from rest_framework.exceptions import ValidationError

with patch('django.db.transaction.atomic', lambda x: x):
    from api.servicios.solicitud_baja.solicitud_baja_service import resolver_solicitud


class TestResolverSolicitudBaja(unittest.TestCase):

    @patch('api.servicios.solicitud_baja.obtener_solicitudes_baja_admin_service.timezone.now')
    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_aceptar_exito(self, mock_atomic, mock_now):
        """
        Test: Aceptación Exitosa (Happy Path - ACEPTAR)
        
        Given: Una solicitud PENDIENTE y un usuario administrador.
        When: Se ejecuta la acción 'ACEPTAR'.
        Then: La solicitud se marca como APROBADA, el hermano se desactiva (is_active=False, estado=BAJA) y se guardan ambos cambios.
        """
        mock_atomic.return_value.__enter__.return_value = None

        ahora = timezone.now()
        mock_now.return_value = ahora
        
        mock_admin = MagicMock()
        mock_admin.esAdmin = True
        
        mock_hermano = MagicMock()
        mock_solicitud = MagicMock()
        mock_solicitud.estado = 'PENDIENTE' 
        mock_solicitud.hermano = mock_hermano

        resultado = resolver_solicitud(mock_solicitud, 'ACEPTAR', mock_admin)

        self.assertEqual(mock_solicitud.estado, 'APROBADA')
        self.assertEqual(mock_solicitud.fecha_resolucion, ahora)
        mock_solicitud.save.assert_called_once()
        
        self.assertFalse(mock_hermano.is_active)
        self.assertEqual(mock_hermano.estado_hermano, 'BAJA')
        mock_hermano.save.assert_called_once()
        
        self.assertEqual(resultado, mock_solicitud)



    @patch('api.servicios.solicitud_baja.obtener_solicitudes_baja_admin_service.timezone.now')
    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_denegar_exito(self, mock_atomic, mock_now):
        """
        Test: Denegación Exitosa (Happy Path - DENEGAR)
        
        Given: Una solicitud PENDIENTE y un usuario administrador.
        When: Se ejecuta la acción 'DENEGAR'.
        Then: La solicitud se marca como DENEGADA, pero los datos del hermano permanecen inalterados.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_now.return_value = timezone.now()
        
        mock_admin = MagicMock()
        mock_admin.esAdmin = True
        
        mock_hermano = MagicMock()
        mock_solicitud = MagicMock()
        mock_solicitud.estado = 'PENDIENTE'
        mock_solicitud.hermano = mock_hermano

        resolver_solicitud(mock_solicitud, 'DENEGAR', mock_admin)

        self.assertEqual(mock_solicitud.estado, 'DENEGADA')
        mock_solicitud.save.assert_called_once()
        mock_hermano.save.assert_not_called()



    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_seguridad_no_admin(self, mock_atomic):
        """
        Test: Seguridad (No Administrador)
        
        Given: Un usuario sin privilegios de administrador (esAdmin=False).
        When: Intenta resolver una solicitud de baja.
        Then: Se lanza PermissionDenied y no se realiza ninguna persistencia.
        """
        mock_atomic.return_value.__enter__.return_value = None
        
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = False
        mock_solicitud = MagicMock()

        with self.assertRaises(PermissionDenied):
            resolver_solicitud(mock_solicitud, 'ACEPTAR', mock_usuario)
        
        mock_solicitud.save.assert_not_called()



    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_ya_resuelta(self, mock_atomic):
        """
        Test: Validación de Estado (Ya Resuelta)
        
        Given: Una solicitud cuyo estado es APROBADA (ya no está PENDIENTE).
        When: Un administrador intenta resolverla nuevamente.
        Then: El servicio lanza una ValidationError impidiendo la duplicidad de la resolución.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_admin = MagicMock(esAdmin=True)
        mock_solicitud = MagicMock(estado='APROBADA')

        with self.assertRaises(ValidationError) as context:
            resolver_solicitud(mock_solicitud, 'ACEPTAR', mock_admin)

        self.assertIn("Solo se pueden resolver solicitudes que estén pendientes.", str(context.exception))



    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_accion_no_valida(self, mock_atomic):
        """
        Test: Acción No Válida
        
        Given: Una solicitud PENDIENTE y un administrador.
        When: Se intenta ejecutar una acción no permitida (ej: 'BORRAR').
        Then: El servicio lanza una ValidationError de Django y no persiste ningún cambio en la base de datos.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_admin = MagicMock(esAdmin=True)
        mock_solicitud = MagicMock(estado='PENDIENTE')

        with self.assertRaises(ValidationError) as context:
            resolver_solicitud(mock_solicitud, 'BORRAR', mock_admin)

        mensaje_error = str(context.exception)
        self.assertIn("Acción no válida", mensaje_error)
        self.assertIn("ACEPTAR", mensaje_error)
        self.assertIn("DENEGAR", mensaje_error)

        mock_solicitud.save.assert_not_called()



    @patch('api.servicios.solicitud_baja.obtener_solicitudes_baja_admin_service.timezone.now')
    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_robustez_tiempos(self, mock_atomic, mock_now):
        """
        Test: Robustez de Tiempos (timezone)
        
        Given: Un punto en el tiempo fijo definido por el sistema.
        When: Se resuelve una solicitud (DENEGAR).
        Then: El campo fecha_resolucion de la solicitud coincide exactamente con el valor proporcionado por el mock de timezone.
        """
        mock_atomic.return_value.__enter__.return_value = None

        tiempo_fijo = datetime.datetime(2026, 5, 6, 12, 0, tzinfo=datetime.timezone.utc)
        mock_now.return_value = tiempo_fijo
        
        mock_admin = MagicMock(esAdmin=True)
        mock_solicitud = MagicMock(estado='PENDIENTE')

        resolver_solicitud(mock_solicitud, 'DENEGAR', mock_admin)

        self.assertEqual(mock_solicitud.fecha_resolucion, tiempo_fijo)
        mock_solicitud.save.assert_called_once()