from django.http import Http404
from django.test import TestCase
from unittest.mock import patch, MagicMock, ANY
from django.core.exceptions import PermissionDenied, ValidationError

from api.servicios.acto.acto_service import update_acto_service


class UpdateActoServiceTests(TestCase):

    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_admin_actualizacion_basica_correcta(self, mock_get_object_or_404):
        """
        Test: Usuario admin -> actualización básica correcta

        Given: Un usuario administrador, un ID de acto válido, y un diccionario 
                de datos (data_validada) que no modifica el tipo_acto.
        When: Se llama al servicio update_acto_service.
        Then: Se obtiene el acto mediante get_object_or_404.
                Se actualizan los atributos dinámicamente usando setattr.
                Se llama a acto.save() para persistir los cambios.
                Se retorna el acto modificado sin tocar la base de datos.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        acto_id = 1
        data_validada = {
            'nombre': 'Ensayo Modificado',
            'lugar': 'Nueva Sede'
        }
        
        mock_acto = MagicMock()
        mock_acto.tipo_acto = 'ENSAYO'

        mock_get_object_or_404.return_value = mock_acto

        resultado = update_acto_service(usuario_admin, acto_id, data_validada)

        mock_get_object_or_404.assert_called_once_with(ANY, pk=acto_id)

        self.assertEqual(mock_acto.nombre, 'Ensayo Modificado')
        self.assertEqual(mock_acto.lugar, 'Nueva Sede')

        self.assertEqual(mock_acto.tipo_acto, 'ENSAYO')

        mock_acto.save.assert_called_once()

        self.assertEqual(resultado, mock_acto)



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_admin_cambia_tipo_acto_sin_puestos_asignados_exito(self, mock_get_object_or_404):
        """
        Test: Usuario admin -> cambia tipo_acto sin puestos asignados

        Given: Un usuario administrador.
                Un acto existente con tipo_acto='ENSAYO'.
                El acto NO tiene puestos asignados (exists() -> False).
        When: Se llama al servicio para cambiar el tipo_acto a 'PROCESION'.
        Then: El servicio debe permitir el cambio, actualizar el atributo
                y llamar a save() exitosamente.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        data_validada = {'tipo_acto': 'PROCESION'}

        mock_acto = MagicMock()
        mock_acto.tipo_acto = 'ENSAYO'

        mock_acto.puestos_disponibles.exists.return_value = False
        
        mock_get_object_or_404.return_value = mock_acto

        resultado = update_acto_service(usuario_admin, 1, data_validada)

        mock_acto.puestos_disponibles.exists.assert_called_once()

        self.assertEqual(mock_acto.tipo_acto, 'PROCESION')

        mock_acto.save.assert_called_once()
        self.assertEqual(resultado, mock_acto)



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_cambiar_tipo_acto_con_puestos_asignados_lanza_validation_error(self, mock_get_object_or_404):
        """
        Test: Cambio de tipo_acto con puestos asignados -> ValidationError

        Given: Un usuario administrador.
                Un acto existente con tipo_acto='ENSAYO'.
                El acto TIENE puestos asignados (exists() -> True).
        When: Se intenta cambiar el tipo_acto a 'PROCESION'.
        Then: El servicio debe lanzar un ValidationError con el mensaje específico.
                Se debe garantizar que el método save() NUNCA se llama.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_validada = {'tipo_acto': 'PROCESION'}

        mock_acto = MagicMock()
        mock_acto.tipo_acto = 'ENSAYO'

        mock_acto.puestos_disponibles.exists.return_value = True
        
        mock_get_object_or_404.return_value = mock_acto

        with self.assertRaises(ValidationError) as context:
            update_acto_service(usuario_admin, 1, data_validada)

        self.assertIn('tipo_acto', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['tipo_acto'], 
            ["No se puede cambiar el tipo de acto porque ya tiene puestos asignados."]
        )

        mock_acto.save.assert_not_called()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_admin_tipo_acto_igual_al_actual_no_valida_puestos(self, mock_get_object_or_404):
        """
        Test: Usuario admin -> tipo_acto igual al actual

        Given: Un usuario administrador.
                Un acto existente con tipo_acto='ENSAYO'.
                Un payload donde el tipo_acto sigue siendo 'ENSAYO'.
        When: Se llama al servicio update_acto_service.
        Then: El servicio debe detectar que el tipo no ha cambiado.
                NO debe llamar a puestos_disponibles.exists().
                Se llama a save() y se retorna el objeto.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        tipo_actual = 'ENSAYO'
        data_validada = {'tipo_acto': tipo_actual, 'nombre': 'Nombre Nuevo'}
        
        mock_acto = MagicMock()
        mock_acto.tipo_acto = tipo_actual
        mock_get_object_or_404.return_value = mock_acto

        update_acto_service(usuario_admin, 1, data_validada)

        mock_acto.puestos_disponibles.exists.assert_not_called()

        self.assertEqual(mock_acto.nombre, 'Nombre Nuevo')

        mock_acto.save.assert_called_once()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_no_admin_lanza_permission_denied_y_detiene_ejecucion(self, mock_get_object_or_404):
        """
        Test: Usuario NO admin -> PermissionDenied

        Given: Un usuario solicitante con esAdmin = False.
        When: Se llama al servicio update_acto_service.
        Then: Se lanza la excepción PermissionDenied.
                No se debe llamar a get_object_or_404 (evita consulta innecesaria).
                No se debe llamar al método save (seguridad de integridad).
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False
        
        data_validada = {'nombre': 'Intento de hackeo'}

        with self.assertRaises(PermissionDenied) as context:
            update_acto_service(usuario_no_admin, 1, data_validada)

        self.assertEqual(str(context.exception), "No tienes permisos para editar actos.")

        mock_get_object_or_404.assert_not_called()

        mock_acto = MagicMock()
        mock_acto.save.assert_not_called()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_usuario_sin_atributo_es_admin_lanza_permission_denied(self, mock_get_object_or_404):
        """
        Test: Usuario sin atributo esAdmin -> PermissionDenied

        Given: Un objeto de usuario que carece por completo del atributo 'esAdmin'.
        When: Se llama al servicio update_acto_service.
        Then: La función getattr(usuario, 'esAdmin', False) debe retornar False.
                Se lanza la excepción PermissionDenied.
                La ejecución se detiene antes de buscar el objeto o intentar guardarlo.
        """
        class UsuarioIncompleto:
            pass
            
        usuario_sin_attr = UsuarioIncompleto()
        data_validada = {'nombre': 'Cambio no autorizado'}

        with self.assertRaises(PermissionDenied) as context:
            update_acto_service(usuario_sin_attr, 1, data_validada)
        
        self.assertEqual(str(context.exception), "No tienes permisos para editar actos.")

        mock_get_object_or_404.assert_not_called()