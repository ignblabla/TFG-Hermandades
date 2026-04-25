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
    def test_usuario_admin_actualiza_multiples_campos_correctamente(self, mock_get_object_or_404):
        """
        Test: Usuario admin -> múltiples campos en data_validada

        Given: Un usuario administrador.
                Un payload con múltiples campos de distinta naturaleza (strings, fechas, booleanos).
        When: Se llama al servicio update_acto_service.
        Then: El servicio debe iterar sobre todos los elementos de data_validada.
                Debe aplicar setattr para cada uno de ellos en el objeto acto.
                Se llama a save() una única vez al final del proceso.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_validada = {
            'nombre': 'Gran Procesión 2026',
            'lugar': 'Centro Histórico',
            'fecha': '2026-04-10T20:00:00Z',
            'descripcion': 'Actualización de itinerario',
            'publicado': True
        }
        
        mock_acto = MagicMock()
        mock_acto.tipo_acto = 'PROCESION'
        mock_get_object_or_404.return_value = mock_acto

        resultado = update_acto_service(usuario_admin, 1, data_validada)

        self.assertEqual(mock_acto.nombre, 'Gran Procesión 2026')
        self.assertEqual(mock_acto.lugar, 'Centro Histórico')
        self.assertEqual(mock_acto.fecha, '2026-04-10T20:00:00Z')
        self.assertEqual(mock_acto.descripcion, 'Actualización de itinerario')
        self.assertTrue(mock_acto.publicado)

        mock_acto.save.assert_called_once()
        self.assertEqual(resultado, mock_acto)



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_data_validada_vacio_no_rompe_y_llama_a_save(self, mock_get_object_or_404):
        """
        Test: data_validada vacío

        Given: Un usuario administrador.
                Un diccionario de datos vacío ({}).
        When: Se llama al servicio update_acto_service.
        Then: El servicio no debe lanzar ninguna excepción.
                El bucle de actualización no realiza ninguna operación.
                Se llama a acto.save() igualmente (según la lógica actual del servicio).
                Se devuelve el objeto original.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        data_vacia = {}
        
        mock_acto = MagicMock()
        mock_acto.nombre = "Nombre Original"
        mock_get_object_or_404.return_value = mock_acto

        resultado = update_acto_service(usuario_admin, 1, data_vacia)

        self.assertEqual(mock_acto.nombre, "Nombre Original")

        mock_acto.save.assert_called_once()

        self.assertEqual(resultado, mock_acto)



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
    def test_acto_no_existe_lanza_http404_y_detiene_ejecucion(self, mock_get_object_or_404):
        """
        Test: Errores de obtención -> get_object_or_404 lanza excepción (404)

        Given: Un usuario administrador y un payload válido.
                Un ID de acto que no existe.
                El mock de get_object_or_404 está configurado para lanzar Http404.
        When: Se llama al servicio update_acto_service.
        Then: La excepción Http404 se propaga limpiamente hacia arriba.
                La ejecución de la función se detiene al instante, garantizando 
                que no se evalúan reglas de negocio ni se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        acto_id_inexistente = 999
        data_validada = {'nombre': 'Acto Fantasma'}

        mock_get_object_or_404.side_effect = Http404("No Acto matches the given query.")

        with self.assertRaises(Http404):
            update_acto_service(usuario_admin, acto_id_inexistente, data_validada)
        
        mock_get_object_or_404.assert_called_once()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_acto_save_lanza_excepcion_y_se_propaga(self, mock_get_object_or_404):
        """
        Test: Errores durante guardado -> acto.save() lanza excepción

        Given: Un usuario administrador y datos válidos.
                El objeto acto se recupera correctamente.
        When: Se llama al método save() del acto y este lanza una excepción 
                inesperada (ej. un error de base de datos).
        Then: El servicio no debe capturar la excepción.
                La excepción debe propagarse hacia arriba para permitir el 
                manejo de errores global y el rollback de la transacción.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        data_validada = {'nombre': 'Nombre con fallo en BD'}

        mock_acto = MagicMock()
        mensaje_error = "Error de escritura en disco o base de datos"
        mock_acto.save.side_effect = Exception(mensaje_error)
        
        mock_get_object_or_404.return_value = mock_acto

        with self.assertRaises(Exception) as context:
            update_acto_service(usuario_admin, 1, data_validada)

        self.assertEqual(str(context.exception), mensaje_error)

        mock_acto.save.assert_called_once()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_tipo_acto_no_presente_en_data_validada_no_evalua_puestos(self, mock_get_object_or_404):
        """
        Test: Casos límite -> tipo_acto no presente en data_validada

        Given: Un usuario administrador.
                Un payload de actualización que solo contiene campos como 'lugar' o 'nombre'.
        When: Se llama al servicio update_acto_service.
        Then: El servicio debe identificar que 'tipo_acto' no está en data_validada.
                NO debe acceder a la relación puestos_disponibles.
                Se actualizan los campos presentes y se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_parcial = {'lugar': 'Plaza Mayor'}
        
        mock_acto = MagicMock()
        mock_get_object_or_404.return_value = mock_acto

        update_acto_service(usuario_admin, 1, data_parcial)

        mock_acto.puestos_disponibles.exists.assert_not_called()

        self.assertEqual(mock_acto.lugar, 'Plaza Mayor')

        mock_acto.save.assert_called_once()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_tipo_acto_es_none_en_data_validada_no_evalua_puestos(self, mock_get_object_or_404):
        """
        Test: tipo_acto = None

        Given: Un usuario administrador.
                Un payload donde 'tipo_acto' es explícitamente None (falsy).
        When: Se llama al servicio update_acto_service.
        Then: La condición 'if nuevo_tipo' debe evaluar a False.
                NO debe llamarse a puestos_disponibles.exists().
                Se llama a setattr(acto, 'tipo_acto', None) y a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_nula = {'tipo_acto': None}
        
        mock_acto = MagicMock()
        mock_acto.tipo_acto = 'ENSAYO'
        mock_get_object_or_404.return_value = mock_acto

        update_acto_service(usuario_admin, 1, data_nula)

        mock_acto.puestos_disponibles.exists.assert_not_called()

        self.assertIsNone(mock_acto.tipo_acto)

        mock_acto.save.assert_called_once()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_puestos_disponibles_exists_lanza_excepcion_y_se_propaga(self, mock_get_object_or_404):
        """
        Test: puestos_disponibles.exists() lanza excepción

        Given: Un usuario administrador intentando cambiar el tipo_acto.
                Al consultar si existen puestos asignados, el ORM lanza una 
                excepción (ej. error de conexión o timeout).
        When: Se llama al servicio update_acto_service.
        Then: La excepción debe propagarse íntegramente hacia arriba.
                Se garantiza que la ejecución se detiene y no se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_validada = {'tipo_acto': 'NUEVO_TIPO'}
        
        mock_acto = MagicMock()
        mock_acto.tipo_acto = 'TIPO_ANTIGUO'

        mensaje_error = "Database timeout al consultar puestos_disponibles"
        mock_acto.puestos_disponibles.exists.side_effect = Exception(mensaje_error)
        
        mock_get_object_or_404.return_value = mock_acto

        with self.assertRaises(Exception) as context:
            update_acto_service(usuario_admin, 1, data_validada)

        self.assertEqual(str(context.exception), mensaje_error)

        mock_acto.save.assert_not_called()



    @patch('api.servicios.acto.acto_service.get_object_or_404')
    def test_data_validada_con_atributo_inexistente_intenta_setattr_igualmente(self, mock_get_object_or_404):
        """
        Test: data_validada contiene atributo inexistente

        Given: Un usuario administrador.
                Un diccionario data_validada con un campo que no pertenece al modelo Acto
                (ej. 'campo_fantasma').
        When: Se llama al servicio update_acto_service.
        Then: El servicio debe intentar aplicar setattr para ese campo igualmente.
                Esto demuestra que el servicio no tiene una lista blanca (whitelist) 
                de campos, delegando la integridad estructural al modelo y al serializador.
                Se llama a save() con el objeto modificado en memoria.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_con_ruido = {'campo_fantasma': 'valor_arbitrario'}
        
        mock_acto = MagicMock()
        mock_get_object_or_404.return_value = mock_acto

        update_acto_service(usuario_admin, 1, data_con_ruido)

        self.assertEqual(mock_acto.campo_fantasma, 'valor_arbitrario')

        mock_acto.save.assert_called_once()