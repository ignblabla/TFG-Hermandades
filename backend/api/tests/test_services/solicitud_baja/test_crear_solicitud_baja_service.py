import unittest
from unittest.mock import MagicMock, patch
from django.core.exceptions import ValidationError

from api.servicios.solicitud_baja.solicitud_baja_service import crear_solicitud_baja


class TestCrearSolicitudBaja(unittest.TestCase):

    @patch('api.servicios.solicitud_baja.crear_solicitud_baja_service.SolicitudBaja')
    def test_crear_solicitud_baja_exito(self, mock_solicitud_class):
        """
        Test: Creación Exitosa (Happy Path)
        
        Given: Un usuario autenticado con estado de ALTA y sin solicitudes previas pendientes.
        When: Se intenta crear una nueva solicitud de baja con un motivo específico.
        Then: El servicio crea la instancia, la guarda en base de datos y retorna el objeto correctamente configurado.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_usuario.estado_hermano = 'ALTA'
        motivo_test = "Cambio de residencia"

        mock_solicitud_class.objects.filter.return_value.exists.return_value = False

        mock_instancia = mock_solicitud_class.return_value

        resultado = crear_solicitud_baja(mock_usuario, motivo=motivo_test)

        mock_instancia.save.assert_called_once()
        self.assertEqual(resultado, mock_instancia)
        mock_solicitud_class.assert_called_with(hermano=mock_usuario, motivo=motivo_test)



    def test_crear_solicitud_usuario_no_autenticado(self):
        """
        Test: Usuario no Autenticado
        
        Given: Un objeto de usuario que no ha iniciado sesión (is_authenticated=False).
        When: Se intenta realizar la solicitud de baja.
        Then: El servicio lanza una ValidationError impidiendo la acción por falta de credenciales.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = False

        with self.assertRaises(ValidationError) as context:
            crear_solicitud_baja(mock_usuario)
        
        self.assertEqual(str(context.exception.message), "El usuario debe estar autenticado para realizar esta acción.")



    def test_crear_solicitud_hermano_no_en_alta(self):
        """
        Test: Hermano que no está de ALTA
        
        Given: Un usuario autenticado pero cuyo estado es distinto a ALTA (ej. ya está de BAJA).
        When: Se intenta solicitar una baja.
        Then: El servicio lanza una ValidationError informando que solo los hermanos activos pueden solicitarla.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_usuario.estado_hermano = 'BAJA'

        with self.assertRaises(ValidationError) as context:
            crear_solicitud_baja(mock_usuario)
        
        self.assertIn("Solo los hermanos en estado de ALTA", str(context.exception.message))



    @patch('api.servicios.solicitud_baja.crear_solicitud_baja_service.SolicitudBaja')
    def test_crear_solicitud_duplicada_pendiente(self, mock_solicitud_class):
        """
        Test: Solicitud Duplicada (Pendiente)
        
        Given: Un usuario que ya tiene una solicitud de baja en estado PENDIENTE en el sistema.
        When: El usuario intenta crear una nueva solicitud de baja.
        Then: El servicio lanza una ValidationError para evitar la duplicidad de peticiones en curso.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_usuario.estado_hermano = 'ALTA'

        mock_solicitud_class.objects.filter.return_value.exists.return_value = True

        with self.assertRaises(ValidationError) as context:
            crear_solicitud_baja(mock_usuario)
        
        self.assertEqual(str(context.exception.message), "Ya tienes una solicitud de baja en curso pendiente de revisión.")



    @patch('api.servicios.solicitud_baja.crear_solicitud_baja_service.SolicitudBaja')
    def test_persistencia_motivo_opcional(self, mock_solicitud_class):
        """
        Test: Persistencia de Motivo Opcional
        
        Given: Un usuario válido realizando una solicitud de baja.
        When: Se realiza una petición con un motivo específico y otra con el motivo ausente (None).
        Then: El servicio instancia correctamente SolicitudBaja con el valor de motivo proporcionado en cada caso.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True
        mock_usuario.estado_hermano = 'ALTA'
        mock_solicitud_class.objects.filter.return_value.exists.return_value = False
        
        motivos_a_probar = ["Motivo personal", None]

        for motivo in motivos_a_probar:
            with self.subTest(motivo=motivo):
                crear_solicitud_baja(mock_usuario, motivo=motivo)

                mock_solicitud_class.assert_called_with(
                    hermano=mock_usuario, 
                    motivo=motivo
                )
                mock_solicitud_class.return_value.save.assert_called()