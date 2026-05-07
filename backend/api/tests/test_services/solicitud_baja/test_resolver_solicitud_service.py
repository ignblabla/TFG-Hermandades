import unittest
from unittest.mock import MagicMock, patch
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import datetime

import pytest
from rest_framework.exceptions import ValidationError

with patch('django.db.transaction.atomic', lambda x: x):
    from api.servicios.solicitud_baja.solicitud_baja_service import resolver_solicitud

@pytest.mark.django_db
class TestResolverSolicitudBaja(unittest.TestCase):

    @patch('api.servicios.solicitud_baja.solicitud_baja_service.timezone.now')
    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_aceptar_exito(self, mock_atomic, mock_now):
        """
        Test: Aceptación Exitosa (Happy Path - ACEPTAR)
        
        Given: Una solicitud PENDIENTE y un administrador.
        When: Se ejecuta la acción 'ACEPTAR'.
        Then: 
            - La solicitud pasa a APROBADA con fecha de resolución.
            - El hermano se desactiva y pasa a estado BAJA con fecha registrada.
            - Se persisten ambos objetos.
        """
        mock_atomic.return_value.__enter__.return_value = None
        ahora = MagicMock()
        mock_now.return_value = ahora
        mock_now.date.return_value = ahora.date()
        
        mock_admin = MagicMock(esAdmin=True)
        mock_hermano = MagicMock()
        mock_solicitud = MagicMock(estado='PENDIENTE', hermano=mock_hermano)

        resultado = resolver_solicitud(mock_solicitud, 'ACEPTAR', mock_admin)

        self.assertEqual(mock_solicitud.estado, 'APROBADA')
        self.assertEqual(mock_solicitud.fecha_resolucion, ahora)
        mock_solicitud.save.assert_called_once()

        self.assertFalse(mock_hermano.is_active)
        self.assertEqual(mock_hermano.estado_hermano, 'BAJA')
        mock_hermano.save.assert_called_once()
        
        self.assertEqual(resultado, mock_solicitud)



    @patch('api.servicios.solicitud_baja.solicitud_baja_service.timezone.now')
    @patch('django.db.transaction.atomic')
    def test_resolver_solicitud_denegar_exito(self, mock_atomic, mock_now):
        """
        Test: Denegación Exitosa (Happy Path - DENEGAR)
        
        Given: Una solicitud PENDIENTE y un administrador.
        When: Se ejecuta la acción 'DENEGAR'.
        Then: La solicitud se marca como DENEGADA, pero el hermano no se modifica.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_now.return_value = MagicMock()
        
        mock_admin = MagicMock(esAdmin=True)
        mock_hermano = MagicMock()
        mock_solicitud = MagicMock(estado='PENDIENTE', hermano=mock_hermano)

        resolver_solicitud(mock_solicitud, 'DENEGAR', mock_admin)

        self.assertEqual(mock_solicitud.estado, 'DENEGADA')
        mock_solicitud.save.assert_called_once()
        mock_hermano.save.assert_not_called()



    def test_resolver_solicitud_seguridad_no_admin(self):
        """
        Test: Seguridad (No Administrador)
        
        Given: Un usuario sin esAdmin=True.
        When: Intenta resolver una solicitud.
        Then: Lanza PermissionDenied y no guarda cambios.
        """
        mock_usuario = MagicMock(esAdmin=False)
        mock_solicitud = MagicMock()

        with self.assertRaises(PermissionDenied):
            resolver_solicitud(mock_solicitud, 'ACEPTAR', mock_usuario)
        
        mock_solicitud.save.assert_not_called()



    def test_resolver_solicitud_ya_resuelta_falla(self):
        """
        Test: Validación de Estado (No Pendiente)
        
        Given: Una solicitud con estado APROBADA o DENEGADA.
        When: Se intenta resolver de nuevo.
        Then: Lanza ValidationError impidiendo la re-resolución.
        """
        mock_admin = MagicMock(esAdmin=True)
        mock_solicitud = MagicMock(estado='APROBADA')

        with self.assertRaises(ValidationError) as context:
            resolver_solicitud(mock_solicitud, 'ACEPTAR', mock_admin)

        self.assertIn("Solo se pueden resolver solicitudes que estén pendientes", str(context.exception))



    def test_resolver_solicitud_accion_invalida_falla(self):
        """
        Test: Acción No Válida
        
        Given: Una acción distinta de ACEPTAR/DENEGAR.
        When: Se intenta resolver.
        Then: Lanza ValidationError y no persiste nada.
        """
        mock_admin = MagicMock(esAdmin=True)
        mock_solicitud = MagicMock(estado='PENDIENTE')

        with self.assertRaises(ValidationError) as context:
            resolver_solicitud(mock_solicitud, 'OTRA_COSA', mock_admin)

        self.assertIn("Acción no válida", str(context.exception))
        mock_solicitud.save.assert_not_called()