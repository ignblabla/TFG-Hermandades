from django.db import IntegrityError
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.exceptions import PermissionDenied

from api.servicios.acto.acto_service import crear_acto_service


class CrearActoServiceTests(TestCase):

    @patch('api.models.Acto.objects.create')
    def test_usuario_admin_creacion_exitosa(self, mock_acto_create):
        """
        Test: Usuario admin -> creación exitosa

        Given: Un usuario solicitante con el atributo esAdmin a True 
                y un diccionario con los datos validados del acto.
        When: Se llama al servicio crear_acto_service con estos parámetros.
        Then: El servicio invoca Acto.objects.create desempaquetando los datos (**data_validada)
                y retorna exactamente el objeto acto instanciado (sin tocar la base de datos).
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_validada = {
            'nombre': 'Ensayo Solidario',
            'lugar': 'Plaza Mayor',
            'fecha': '2026-10-10T10:00:00Z',
        }

        acto_esperado = MagicMock()
        mock_acto_create.return_value = acto_esperado

        resultado = crear_acto_service(usuario_admin, data_validada)

        mock_acto_create.assert_called_once_with(**data_validada)

        self.assertEqual(resultado, acto_esperado)



    @patch('api.servicios.acto.acto_service.Acto.objects.create')
    def test_usuario_no_admin_lanza_permission_denied_y_no_crea_acto(self, mock_acto_create):
        """
        Test: Usuario NO admin -> PermissionDenied

        Given: Un usuario solicitante cuyo atributo 'esAdmin' es False.
        When: Se intenta llamar al servicio crear_acto_service para crear un nuevo acto.
        Then: El servicio debe elevar una excepción PermissionDenied con el mensaje 
                específico de restricción de administrador.
                Se debe garantizar que Acto.objects.create NO sea llamado, protegiendo 
                la integridad de la base de datos.
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False
        
        data_validada = {
            'nombre': 'Acto Prohibido',
            'lugar': 'Ubicación Secreta'
        }

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(usuario_no_admin, data_validada)

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        mock_acto_create.assert_not_called()



    @patch('api.servicios.acto.acto_service.Acto.objects.create')
    def test_usuario_sin_atributo_es_admin_lanza_permission_denied(self, mock_acto_create):
        """
        Test: Usuario sin atributo esAdmin -> PermissionDenied

        Given: Un objeto de usuario que no posee el atributo 'esAdmin' en absoluto.
        When: Se intenta llamar al servicio crear_acto_service.
        Then: La función getattr debe no encontrar el atributo y retornar el valor por defecto (False).
                El servicio lanza PermissionDenied.
                Acto.objects.create NO se ejecuta.
        """
        class UsuarioSinAtributos:
            pass
            
        usuario_vacio = UsuarioSinAtributos()
        
        data_validada = {
            'nombre': 'Acto Clandestino',
            'lugar': 'Catacumbas'
        }

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(usuario_vacio, data_validada)

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        mock_acto_create.assert_not_called()