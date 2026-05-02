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



    def test_usuario_admin_con_atributos_adicionales_ignora_evaluacion_de_junta(self):
        """
        Test: Usuario admin con atributos adicionales irrelevantes

        Given: Un usuario con esAdmin = True.
                El usuario también posee el atributo 'cuerpos' (que en este flujo es irrelevante).
        When: Se llama a _verificar_permisos.
        Then: El acceso se concede inmediatamente.
                ❗ No se realiza ninguna consulta al filtro de 'cuerpos'.
                Se valida que la lógica de Admin tiene prioridad y eficiencia sobre la de Junta.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_not_called()
        mock_cuerpos.filter.return_value.exists.assert_not_called()



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



    def test_es_admin_falsy_no_activa_early_return_y_continua_verificacion(self):
        """
        Test: Casos límite de atributos falsy (esAdmin = None o False)

        Given: Un usuario autenticado.
                El atributo 'esAdmin' es None o False.
        When: Se llama a _verificar_permisos.
        Then: El early return de Admin NO se ejecuta.
                El flujo continúa para evaluar el atributo 'cuerpos'.
                Se garantiza que solo un True explícito (o evaluable como True) 
                concede el acceso inmediato.
        """
        for valor_falsy in [None, False]:
            with self.subTest(valor=valor_falsy):
                # 1. Setup
                servicio = ComunicadoService()
                usuario = MagicMock()
                usuario.is_authenticated = True
                usuario.esAdmin = valor_falsy

                mock_cuerpos = MagicMock()
                mock_cuerpos.filter.return_value.exists.return_value = False
                usuario.cuerpos = mock_cuerpos

                with self.assertRaises(PermissionDenied):
                    servicio._verificar_permisos(usuario)

                self.assertTrue(hasattr(usuario, 'cuerpos'))
                mock_cuerpos.filter.assert_called_once()



    def test_is_authenticated_es_none_se_trata_como_no_autenticado(self):
        """
        Test: is_authenticated = None (Falsy)

        Given: Un usuario donde is_authenticated es None.
        When: Se llama al método _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se garantiza que el sistema no es laxo con valores nulos 
                en la propiedad de autenticación.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        usuario.is_authenticated = None

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        self.assertFalse(usuario.esAdmin.called)



    def test_filter_cuerpos_lanza_excepcion_y_se_propaga(self):
        """
        Test: Errores en queryset -> .filter() lanza excepción

        Given: Un usuario autenticado que no es administrador.
        When: Se intenta filtrar sus cuerpos de pertenencia.
                El ORM lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga hacia arriba sin ser silenciada.
                Se garantiza que el servicio no asume un 'False' ante un error técnico.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mensaje_error = "Error crítico de conexión con la base de datos"
        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.side_effect = Exception(mensaje_error)
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(Exception) as context:
            servicio._verificar_permisos(usuario)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_cuerpos.filter.assert_called_once()



    def test_exists_en_cuerpos_lanza_excepcion_y_se_propaga(self):
        """
        Test: .exists() lanza excepción

        Given: Un usuario autenticado que no es administrador.
        When: Se ejecuta la consulta final .exists() para verificar la Junta.
                La base de datos lanza un error de conexión (DatabaseError).
        Then: La excepción NO se captura dentro del método y se propaga.
                Se garantiza que el servicio no enmascara problemas de infraestructura.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mensaje_error = "Database Connection Timeout"
        mock_queryset = MagicMock()
        mock_queryset.exists.side_effect = Exception(mensaje_error)
        
        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value = mock_queryset
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(Exception) as context:
            servicio._verificar_permisos(usuario)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_cuerpos.filter.assert_called_once()
        mock_queryset.exists.assert_called_once()



    def test_usuario_admin_con_cuerpos_roto_no_falla_por_early_return(self):
        """
        Test: Usuario admin con cuerpos roto

        Given: Un usuario autenticado con esAdmin = True.
                El atributo 'cuerpos' está en un estado corrupto o lanzaría 
                un error si se intentara acceder a él.
        When: Se llama al método _verificar_permisos.
        Then: El acceso se concede inmediatamente (None).
                ❗ NUNCA se accede al atributo 'cuerpos'.
                Se garantiza que un fallo en datos secundarios no bloquea al administrador.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        type(usuario).cuerpos = PropertyMock(side_effect=RuntimeError("Acceso prohibido"))

        try:
            resultado = servicio._verificar_permisos(usuario)
        except RuntimeError:
            self.fail("El Admin fue bloqueado porque el código intentó acceder a 'cuerpos' innecesariamente.")
        except PermissionDenied:
            self.fail("El Admin fue denegado a pesar de tener privilegios superiores.")

        self.assertIsNone(resultado)



    def test_filter_devuelve_objeto_sin_exists_lanza_attribute_error(self):
        """
        Test: Usuario junta pero sin .exists()

        Given: Un usuario autenticado que no es administrador.
                El método .filter() de cuerpos devuelve, por error de mock o 
                de lógica, un objeto que carece de .exists() (ej. una lista o None).
        When: Se llama a _verificar_permisos.
        Then: Se lanza un AttributeError.
                Se valida que el servicio espera un contrato estricto con el ORM 
                y no silencia errores de tipos de datos.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value = ["no_soy_un_queryset"] 
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(AttributeError):
            servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_called_once()



    def test_verificar_permisos_usa_el_filtro_de_cuerpo_correcto(self):
        """
        Test: Verificar que Junta usa filtro correcto

        Given: Un usuario autenticado que no es administrador.
        When: Se evalúa la pertenencia a cuerpos.
        Then: La llamada a .filter() debe incluir exactamente el argumento 
                nombre_cuerpo = CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False
        
        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_called_once_with(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )



    def test_prioridad_de_acceso_admin_corta_ejecucion_antes_de_consultar_junta(self):
        """
        Test: Flujo correcto de prioridad (Admin sobre Junta)

        Given: Un usuario que cumple AMBAS condiciones (esAdmin=True y pertenece a Junta).
        When: Se llama a _verificar_permisos.
        Then: El método debe retornar en la validación de Admin.
                ❗ No debe ejecutarse la consulta a la relación 'cuerpos'.
                Se garantiza que la vía más rápida tiene prioridad absoluta.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_not_called()