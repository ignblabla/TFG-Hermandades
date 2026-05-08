from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from datetime import date

from api.servicios.hermano.hermano_service import dar_de_baja_hermano_service, User


class TestDarDeBajaHermanoService(TestCase):

    @patch('api.servicios.hermano.hermano_service.timezone.now')
    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_dar_de_baja_hermano_exito(self, mock_get_object_or_404, mock_timezone_now):
        """
        Test: Usuario administrador -> da de baja a un hermano correctamente
        
        Given: Un usuario administrador y el ID de un hermano (que no es administrador).
        When: Se ejecuta el servicio para dar de baja.
        Then: Se actualiza el estado a BAJA, se establece la fecha actual, se desactiva el acceso y se guarda.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        hermano_id = 1

        mock_hermano = MagicMock()
        mock_hermano.esAdmin = False
        mock_get_object_or_404.return_value = mock_hermano

        fecha_simulada = date(2026, 5, 8)
        mock_now = MagicMock()
        mock_now.date.return_value = fecha_simulada
        mock_timezone_now.return_value = mock_now

        resultado = dar_de_baja_hermano_service(usuario_admin, hermano_id)

        mock_get_object_or_404.assert_called_once_with(User, pk=hermano_id)
        self.assertEqual(mock_hermano.estado_hermano, User.EstadoHermano.BAJA)
        self.assertEqual(mock_hermano.fecha_baja_corporacion, fecha_simulada)
        self.assertFalse(mock_hermano.is_active)
        
        mock_hermano.save.assert_called_once()
        self.assertEqual(resultado, mock_hermano)



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_dar_de_baja_hermano_objetivo_es_admin(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> intenta dar de baja a otro administrador
        
        Given: Un usuario administrador y el ID de un hermano que también tiene esAdmin = True.
        When: Se ejecuta el servicio para dar de baja.
        Then: Se lanza PermissionDenied y no se efectúan cambios ni se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        mock_hermano_admin = MagicMock()
        mock_hermano_admin.esAdmin = True
        mock_get_object_or_404.return_value = mock_hermano_admin

        with self.assertRaises(PermissionDenied) as cm:
            dar_de_baja_hermano_service(usuario_admin, 1)

        self.assertEqual(str(cm.exception), "Un administrador no puede dar de baja a otro administrador.")
        mock_get_object_or_404.assert_called_once_with(User, pk=1)
        mock_hermano_admin.save.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_dar_de_baja_hermano_solicitante_no_admin(self, mock_get_object_or_404):
        """
        Test: Usuario no administrador -> intenta dar de baja a un hermano
        
        Given: Un usuario solicitante con esAdmin = False.
        When: Se intenta ejecutar el servicio.
        Then: Se lanza PermissionDenied de inmediato y no se llama a la base de datos (get_object_or_404).
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False

        with self.assertRaises(PermissionDenied) as cm:
            dar_de_baja_hermano_service(usuario_no_admin, 1)

        self.assertEqual(str(cm.exception), "No tienes permisos para dar de baja a un hermano.")
        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_dar_de_baja_hermano_solicitante_sin_atributo(self, mock_get_object_or_404):
        """
        Test: Usuario sin atributo esAdmin -> lanza PermissionDenied
        
        Given: Un usuario que carece del atributo 'esAdmin' en su instancia.
        When: El servicio usa getattr(usuario, 'esAdmin', False).
        Then: Retorna el valor por defecto (False), lanza PermissionDenied y bloquea la consulta a BBDD.
        """
        usuario_sin_atributo = MagicMock(spec=[])

        with self.assertRaises(PermissionDenied) as cm:
            dar_de_baja_hermano_service(usuario_sin_atributo, 1)

        self.assertEqual(str(cm.exception), "No tienes permisos para dar de baja a un hermano.")
        mock_get_object_or_404.assert_not_called()