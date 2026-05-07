from django.test import TestCase
from unittest.mock import Mock, PropertyMock, patch, MagicMock

from django.core.exceptions import PermissionDenied

from api.servicios.comunicado.comunicado_service import ComunicadoService
from api.models import CuerpoPertenencia


class VerificaPermisosComunicadoServiceTests(TestCase):

    def test_usuario_admin_tiene_acceso_permitido_inmediato(self):
        """
        Test: Usuario admin → acceso permitido inmediato

        Given: Un usuario autenticado con esAdmin = True.
        When: Se llama al método auxiliar _verificar_permisos.
        Then: Retorna silenciosamente (None, no lanza excepción).
                ❗ NO evalúa la relación 'cuerpos' (verificando el early return).
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        try:
            resultado = servicio._verificar_permisos(usuario)
        except PermissionDenied:
            self.fail("_verificar_permisos bloqueó incorrectamente a un Administrador.")

        self.assertIsNone(resultado)

        mock_cuerpos.filter.assert_not_called()



    def test_usuario_junta_gobierno_acceso_permitido_tras_evaluar_cuerpos(self):
        """
        Test: Usuario junta de gobierno → acceso permitido

        Given: Un usuario autenticado.
                Que NO es administrador (esAdmin = False).
                Que posee el atributo 'cuerpos'.
        When: Se llama al método _verificar_permisos.
        Then: Se evalúa la rama de la Junta correctamente.
                El método filter().exists() devuelve True.
                Retorna sin error (None).
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = True
        usuario.cuerpos = mock_cuerpos

        try:
            resultado = servicio._verificar_permisos(usuario)
        except PermissionDenied:
            self.fail("_verificar_permisos debería haber permitido el acceso al miembro de la Junta.")

        self.assertIsNone(resultado)

        from api.models import CuerpoPertenencia
        mock_cuerpos.filter.assert_called_once_with(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )
        mock_cuerpos.filter.return_value.exists.assert_called_once()



    def test_usuario_junta_aunque_tenga_esadmin_false(self):
        """
        Test: Usuario junta aunque tenga esAdmin=False

        Given: Un usuario autenticado con esAdmin = False (o ausente).
                El usuario pertenece al cuerpo de la Junta de Gobierno (exists = True).
        When: Se llama a _verificar_permisos.
        Then: El acceso se concede correctamente.
                Se valida que la lógica continúa hacia el chequeo de cuerpos 
                cuando el check de admin falla.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = True
        usuario.cuerpos = mock_cuerpos

        try:
            resultado = servicio._verificar_permisos(usuario)
        except PermissionDenied:
            self.fail("El acceso debería permitirse por pertenencia a la Junta si no es Admin.")

        self.assertIsNone(resultado)

        from api.models import CuerpoPertenencia
        mock_cuerpos.filter.assert_called_once_with(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )



    def test_usuario_con_cuerpos_pero_no_pertenece_a_junta_lanza_permission_denied(self):
        """
        Test: Usuario con cuerpos pero no junta

        Given: Un usuario autenticado con esAdmin = False.
                El usuario posee el atributo 'cuerpos'.
                Pero la consulta filter(JUNTA_GOBIERNO).exists() devuelve False.
        When: Se llama a _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se valida que el flujo agota la vía de Junta y llega al bloqueo final.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = False
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        mock_cuerpos.filter.assert_called_once()



    def test_usuario_sin_atributo_cuerpos_y_no_admin_lanza_permission_denied(self):
        """
        Test: Usuario sin atributo cuerpos

        Given: Un usuario autenticado.
                Que NO es administrador (esAdmin = False).
                Que NO posee el atributo 'cuerpos' (hasattr = False).
        When: Se llama a _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se valida que el código salta el bloque de la Junta y llega 
                al raise final de forma segura.
        """
        servicio = ComunicadoService()

        usuario = MagicMock(spec=['is_authenticated', 'esAdmin'])
        usuario.is_authenticated = True
        usuario.esAdmin = False

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")



    def test_usuario_no_autenticado_detiene_ejecucion_inmediatamente(self):
        """
        Test: Usuario no autenticado → PermissionDenied

        Given: Un objeto usuario donde is_authenticated = False.
        When: Se llama al método _verificar_permisos.
        Then: Se lanza PermissionDenied.
                ❗ No se accede al atributo 'esAdmin'.
                ❗ No se evalúa el atributo 'cuerpos'.
                Se garantiza que el anonimato es un bloqueo absoluto y prematuro.
        """
        servicio = ComunicadoService()

        usuario = MagicMock()
        usuario.is_authenticated = False

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)
        
        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        self.assertFalse(usuario.esAdmin.called, 
            "Error: Se evaluó 'esAdmin' en un usuario no autenticado.")

        self.assertFalse(usuario.cuerpos.called, 
            "Error: Se intentó acceder a 'cuerpos' en un usuario no autenticado.")



    def test_usuario_autenticado_sin_permisos_lanza_permission_denied(self):
        """
        Test: Usuario autenticado sin permisos

        Given: Un usuario autenticado (is_authenticated = True).
                No es administrador (esAdmin = False).
                Posee el atributo 'cuerpos'.
                La consulta exists() para Junta de Gobierno devuelve False.
        When: Se llama al método _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se garantiza que un usuario común no puede saltarse las restricciones.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = False
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        mock_cuerpos.filter.assert_called_once()