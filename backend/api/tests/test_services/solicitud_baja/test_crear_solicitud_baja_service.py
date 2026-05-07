import unittest
from unittest.mock import MagicMock, patch
from rest_framework.exceptions import ValidationError

from api.servicios.solicitud_baja.solicitud_baja_service import crear_solicitud_baja


class TestCrearSolicitudBaja(unittest.TestCase):

    @patch('api.servicios.solicitud_baja.solicitud_baja_service.SolicitudBaja')
    def test_crear_solicitud_baja_exito(self, mock_solicitud_class):
        """
        Test: Creación Exitosa (Happy Path)
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_usuario.estado_hermano = 'ALTA'
        motivo_test = "Cambio de residencia"

        mock_solicitud_class.objects.filter.return_value.exists.return_value = False
        mock_instancia = mock_solicitud_class.return_value

        resultado = crear_solicitud_baja(mock_usuario, motivo=motivo_test)

        mock_solicitud_class.assert_called_with(hermano=mock_usuario, motivo=motivo_test)
        mock_instancia.save.assert_called_once()
        self.assertEqual(resultado, mock_instancia)



    def test_crear_solicitud_usuario_no_autenticado(self):
        """
        Test: Usuario no Autenticado
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = False

        with self.assertRaises(ValidationError) as context:
            crear_solicitud_baja(mock_usuario)

        self.assertEqual(context.exception.detail[0], "El usuario debe estar autenticado para realizar esta acción.")



    def test_crear_solicitud_hermano_no_en_alta(self):
        """
        Test: Hermano que no está de ALTA
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_usuario.estado_hermano = 'BAJA'

        with self.assertRaises(ValidationError) as context:
            crear_solicitud_baja(mock_usuario)
        
        self.assertIn("Solo los hermanos en estado de ALTA", str(context.exception.detail[0]))



    @patch('api.servicios.solicitud_baja.solicitud_baja_service.SolicitudBaja')
    def test_crear_solicitud_duplicada_pendiente(self, mock_solicitud_class):
        """
        Test: Solicitud Duplicada (Pendiente)
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_usuario.estado_hermano = 'ALTA'

        mock_solicitud_class.objects.filter.return_value.exists.return_value = True

        with self.assertRaises(ValidationError) as context:
            crear_solicitud_baja(mock_usuario)
        
        self.assertEqual(context.exception.detail[0], "Ya tienes una solicitud de baja en curso pendiente de revisión.")