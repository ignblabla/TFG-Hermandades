from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError

from api.servicios.papeleta_sitio.papeleta_sitio_service import validar_acceso_papeleta
from api.models import PapeletaSitio

from rest_framework.exceptions import PermissionDenied


class TestValidarAccesoPapeleta(TestCase):

    def setUp(self):
        self.mock_usuario_admin = MagicMock()
        self.mock_usuario_admin.is_staff = False
        self.mock_usuario_admin.esAdmin = True

        self.mock_usuario_staff = MagicMock()
        self.mock_usuario_staff.is_staff = True
        self.mock_usuario_staff.esAdmin = False

        self.mock_usuario_sin_permisos = MagicMock()
        self.mock_usuario_sin_permisos.is_staff = False
        self.mock_usuario_sin_permisos.esAdmin = False



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.get_object_or_404')
    def test_validar_acceso_exitoso_con_admin(self, mock_get_object):
        """
        Test: Valida la papeleta exitosamente (usuario Admin)

        Given: Un usuario con esAdmin=True, un ID de papeleta y un código de verificación correcto.
        When: La papeleta se encuentra en estado EMITIDA o RECOGIDA.
        Then: El estado cambia a LEIDA, se llama a save() y retorna un diccionario con status 'success'.
        """
        papeleta_id = 1
        codigo_enviado = "ABC123XYZ"
        
        mock_papeleta = MagicMock()
        mock_papeleta.codigo_verificacion = "ABC123XYZ"
        mock_papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
        mock_get_object.return_value = mock_papeleta

        resultado = validar_acceso_papeleta(papeleta_id, codigo_enviado, self.mock_usuario_admin)

        mock_get_object.assert_called_once_with(PapeletaSitio, pk=papeleta_id)
        self.assertEqual(mock_papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.LEIDA)
        mock_papeleta.save.assert_called_once()
        
        self.assertEqual(resultado["status"], "success")
        self.assertEqual(resultado["mensaje"], "Acceso Correcto. Papeleta marcada como LEÍDA.")
        self.assertEqual(resultado["papeleta"], mock_papeleta)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.get_object_or_404')
    def test_validar_acceso_exitoso_con_staff(self, mock_get_object):
        """
        Test: Valida la papeleta exitosamente (usuario Staff)

        Given: Un usuario con is_staff=True, un ID de papeleta y un código correcto.
        When: La papeleta se encuentra en estado RECOGIDA.
        Then: El servicio la procesa exitosamente igual que si fuera administrador.
        """
        mock_papeleta = MagicMock()
        mock_papeleta.codigo_verificacion = "CODIGO123"
        mock_papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.RECOGIDA
        mock_get_object.return_value = mock_papeleta

        resultado = validar_acceso_papeleta(1, "CODIGO123", self.mock_usuario_staff)

        self.assertEqual(resultado["status"], "success")
        self.assertEqual(mock_papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.LEIDA)
        mock_papeleta.save.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.get_object_or_404')
    def test_usuario_sin_permisos_lanza_excepcion(self, mock_get_object):
        """
        Test: Usuario sin permisos

        Given: Un usuario que tiene is_staff=False y esAdmin=False.
        When: Se invoca la función validar_acceso_papeleta.
        Then: Lanza PermissionDenied inmediatamente y no se llama a la base de datos.
        """
        with self.assertRaises(PermissionDenied) as context:
            validar_acceso_papeleta(1, "CODIGO123", self.mock_usuario_sin_permisos)

        self.assertEqual(str(context.exception), "No tienes permisos para validar accesos.")
        mock_get_object.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.get_object_or_404')
    def test_papeleta_ya_leida_retorna_warning(self, mock_get_object):
        """
        Test: Papeleta previamente leída

        Given: Un usuario con permisos, código válido, pero la papeleta ya tiene el estado LEIDA.
        When: Se procesa la validación.
        Then: No se lanza excepción, no se guarda nuevamente, pero retorna un diccionario con status 'warning'.
        """
        mock_papeleta = MagicMock()
        mock_papeleta.codigo_verificacion = "CODIGO123"
        mock_papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.LEIDA
        mock_papeleta.fecha_emision = "2026-05-08"
        mock_get_object.return_value = mock_papeleta

        resultado = validar_acceso_papeleta(1, "CODIGO123", self.mock_usuario_admin)

        self.assertEqual(resultado["status"], "warning")
        self.assertIn("YA FUE LEÍDA anteriormente", resultado["mensaje"])
        self.assertIn("2026-05-08", resultado["mensaje"])
        self.assertEqual(resultado["papeleta"], mock_papeleta)

        mock_papeleta.save.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.get_object_or_404')
    def test_codigo_verificacion_invalido_lanza_excepcion(self, mock_get_object):
        """
        Test: Código de verificación incorrecto

        Given: Un usuario escaneador válido y un ID de papeleta.
        When: El código de verificación proporcionado no coincide con el de la papeleta.
        Then: Lanza DjangoValidationError y no guarda ningún cambio.
        """
        mock_papeleta = MagicMock()
        mock_papeleta.codigo_verificacion = "REAL123"
        mock_get_object.return_value = mock_papeleta

        with self.assertRaises(DjangoValidationError) as context:
            validar_acceso_papeleta(1, "FALSO999", self.mock_usuario_admin)

        self.assertIn("El código de verificación no es válido.", str(context.exception))
        mock_papeleta.save.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.get_object_or_404')
    def test_papeleta_estado_no_activo_lanza_excepcion(self, mock_get_object):
        """
        Test: Papeleta en estado no válido (ej. ANULADA)

        Given: Permisos correctos, código válido, pero la papeleta está en un estado distinto a EMITIDA, RECOGIDA o LEIDA.
        When: Se intenta validar el acceso.
        Then: Se lanza DjangoValidationError indicando que no está activa.
        """
        mock_papeleta = MagicMock()
        mock_papeleta.codigo_verificacion = "CODIGO123"
        mock_papeleta.estado_papeleta = "ANULADA" 
        mock_get_object.return_value = mock_papeleta

        with self.assertRaises(DjangoValidationError) as context:
            validar_acceso_papeleta(1, "CODIGO123", self.mock_usuario_admin)

        self.assertIn("La papeleta no está activa", str(context.exception))
        mock_papeleta.save.assert_not_called()