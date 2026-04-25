from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.core.exceptions import PermissionDenied

from api.servicios.comunicado.comunicado_service import ComunicadoService


class DeleteComunicadoServiceTests(TestCase):

    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_comunicado_sin_imagen_borra_instancia_y_no_activa_on_commit(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Eliminación básica sin imagen

        Given: Un usuario y un comunicado que NO tiene imagen de portada.
        When: Se llama a delete_comunicado.
        Then: Se llama a _verificar_permisos.
                Se ejecuta comunicado_instance.delete().
                ❗ NO se llama a transaction.on_commit para borrar archivos.
                El servicio retorna True.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = None

        resultado = servicio.delete_comunicado(usuario, comunicado_instance)

        mock_verificar_permisos.assert_called_once_with(usuario)

        comunicado_instance.delete.assert_called_once()

        mock_transaction.on_commit.assert_not_called()

        self.assertTrue(resultado)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_comunicado_con_imagen_encola_borrado_de_archivo_en_commit(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Eliminación con imagen

        Given: Un comunicado que tiene una imagen adjunta.
        When: Se llama a delete_comunicado.
        Then: Se ejecuta comunicado_instance.delete().
                Se registra la función de limpieza en transaction.on_commit.
                ❗ IMPORTANTE: No se llama a imagen_adjunta.delete() todavía.
                El servicio retorna True.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        mock_imagen = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen

        resultado = servicio.delete_comunicado(usuario, comunicado_instance)

        comunicado_instance.delete.assert_called_once()

        mock_transaction.on_commit.assert_called_once()

        mock_imagen.delete.assert_not_called()
        
        self.assertTrue(resultado)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_comunicado_pasa_callable_a_on_commit_sin_ejecutarlo(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Verificar que on_commit recibe función (no ejecución)

        Given: Un comunicado con imagen de portada.
        When: Se llama a delete_comunicado.
        Then: transaction.on_commit debe recibir un objeto 'callable' (función).
                ❗ La imagen NO debe haber registrado ninguna llamada a .delete().
                Se confirma que el servicio delega la responsabilidad, no la ejecuta.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        mock_imagen = MagicMock()
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen

        servicio.delete_comunicado(usuario, comunicado_instance)

        callback_pasado = mock_transaction.on_commit.call_args[0][0]

        self.assertTrue(callable(callback_pasado), "on_commit debe recibir una función o lambda")

        self.assertEqual(callback_pasado.__name__, 'eliminar_archivo_seguro')

        mock_imagen.delete.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_ejecucion_del_callback_de_limpieza_elimina_archivo_fisico(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Ejecución manual del callback elimina imagen

        Given: Un proceso de borrado que ha registrado un callback en on_commit.
        When: Se extrae y se ejecuta manualmente la función 'eliminar_archivo_seguro'.
        Then: Se debe llamar al método .delete() del objeto imagen.
                ❗ El parámetro 'save' debe ser False para evitar errores de integridad.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        mock_imagen = MagicMock()
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen

        servicio.delete_comunicado(usuario, comunicado_instance)

        callback_limpieza = mock_transaction.on_commit.call_args[0][0]

        callback_limpieza()

        mock_imagen.delete.assert_called_once_with(save=False)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_comunicado_retorna_true_tras_eliminacion_exitosa(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Retorno correcto

        Given: Un usuario con permisos y un comunicado.
        When: Se completa el flujo de delete_comunicado.
        Then: El servicio debe retornar exactamente True.
                Se valida tanto para el caso con imagen como sin imagen.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_con_imagen = MagicMock()
        comunicado_con_imagen.imagen_portada = MagicMock()

        comunicado_sin_imagen = MagicMock()
        comunicado_sin_imagen.imagen_portada = None

        res_con = servicio.delete_comunicado(usuario, comunicado_con_imagen)
        res_sin = servicio.delete_comunicado(usuario, comunicado_sin_imagen)

        self.assertIs(res_con, True, "Debe retornar True cuando hay imagen")
        self.assertIs(res_sin, True, "Debe retornar True cuando no hay imagen")



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_comunicado_si_falla_permisos_no_borra_nada_y_propaga_error(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Permisos (Fallo de seguridad)

        Given: Un usuario sin permisos suficientes.
        When: Se llama a delete_comunicado y _verificar_permisos lanza PermissionDenied.
        Then: La excepción se propaga al llamador.
                ❗ NO se llama a comunicado_instance.delete().
                ❗ NO se registra nada en transaction.on_commit.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = MagicMock()

        mock_verificar_permisos.side_effect = PermissionDenied("No tienes permiso para borrar")

        with self.assertRaises(PermissionDenied) as context:
            servicio.delete_comunicado(usuario, comunicado_instance)
        
        self.assertEqual(str(context.exception), "No tienes permiso para borrar")

        comunicado_instance.delete.assert_not_called()

        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_fallo_en_delete_de_instancia_impide_limpieza_de_archivos(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Fallo en delete del comunicado (Excepción en ORM)

        Given: Un comunicado con imagen de portada.
        When: El método comunicado_instance.delete() lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga hacia arriba.
                ❗ NO se registra el callback en transaction.on_commit.
                Se garantiza que la imagen no se borra si el registro permanece en BD.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = MagicMock()

        comunicado_instance.delete.side_effect = Exception("Error de integridad referencial")

        with self.assertRaises(Exception) as context:
            servicio.delete_comunicado(usuario, comunicado_instance)
        
        self.assertEqual(str(context.exception), "Error de integridad referencial")

        comunicado_instance.delete.assert_called_once()

        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_fallo_en_borrado_fisico_es_silenciado_por_callback_seguro(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Fallo en eliminación de imagen (Resiliencia del callback)

        Given: Un proceso de borrado que registra 'eliminar_archivo_seguro'.
        When: Se ejecuta el callback y el método imagen_adjunta.delete() lanza una excepción.
        Then: La excepción es capturada por el bloque try/except interno.
                ❗ El error NO se propaga (el test termina sin fallar).
                Se garantiza que un fallo en el storage no afecta el flujo principal.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        mock_imagen = MagicMock()
        mock_imagen.delete.side_effect = Exception("Error de conexión con el storage")
        
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen

        servicio.delete_comunicado(usuario, comunicado_instance)
        callback_limpieza = mock_transaction.on_commit.call_args[0][0]

        try:
            callback_limpieza()
        except Exception as e:
            self.fail(f"El callback lanzó una excepción '{e}' cuando debería haberla capturado.")

        mock_imagen.delete.assert_called_once_with(save=False)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_fallo_en_registro_on_commit_propaga_error_y_detiene_flujo(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Fallo en transaction.on_commit

        Given: Un comunicado con imagen de portada.
        When: transaction.on_commit lanza una excepción al intentar registrar el callback.
        Then: La excepción se propaga hacia arriba.
                ❗ El flujo se interrumpe y no se llega al 'return True'.
                Se confirma que el servicio no ignora fallos en la fase de registro de limpieza.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = MagicMock()

        error_infra = RuntimeError("Error en el manejador de transacciones")
        mock_transaction.on_commit.side_effect = error_infra

        with self.assertRaises(RuntimeError) as context:
            servicio.delete_comunicado(usuario, comunicado_instance)
        
        self.assertEqual(str(context.exception), "Error en el manejador de transacciones")

        comunicado_instance.delete.assert_called_once()

        mock_transaction.on_commit.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_con_imagen_existente_pero_falsy_no_registra_on_commit(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Imagen existe pero es falsy (Caso Límite)

        Given: Un comunicado donde 'imagen_portada' no es None, 
                pero se evalúa como False (ej. un FieldFile vacío).
        When: Se llama a delete_comunicado.
        Then: El servicio debe ignorar el bloque de limpieza.
                ❗ NO se registra nada en transaction.on_commit.
                Se evita el error de intentar borrar un archivo inexistente.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        mock_imagen_vacia = MagicMock()
        mock_imagen_vacia.__bool__.return_value = False 
        
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen_vacia

        resultado = servicio.delete_comunicado(usuario, comunicado_instance)

        comunicado_instance.delete.assert_called_once()

        mock_transaction.on_commit.assert_not_called()
        
        self.assertTrue(resultado)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_callback_es_resiliente_si_la_imagen_no_tiene_metodo_delete(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Imagen sin método .delete (Mock mal formado)

        Given: Una imagen_portada que es un objeto sin el método .delete().
        When: Se ejecuta el callback 'eliminar_archivo_seguro'.
        Then: Se lanza un AttributeError internamente.
                ❗ El bloque try/except captura el error.
                La ejecución no se interrumpe y el test finaliza con éxito.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        class ObjetoIncompleto:
            pass
        
        mock_imagen_rota = ObjetoIncompleto()
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen_rota

        servicio.delete_comunicado(usuario, comunicado_instance)
        callback_limpieza = mock_transaction.on_commit.call_args[0][0]

        try:
            callback_limpieza()
        except AttributeError:
            self.fail("El callback no capturó el AttributeError; la protección falló.")
        except Exception as e:
            self.fail(f"El callback falló con una excepción inesperada: {e}")



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_comunicado_sigue_orden_logico_estricto(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Orden de ejecución correcto en eliminación

        Valida la secuencia crítica:
        1. Permisos (Seguridad primero)
        2. Captura de imagen (Estado previo al borrado)
        3. delete() del comunicado (Persistencia)
        4. registro on_commit (Limpieza diferida)
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        manager = MagicMock()
        manager.attach_mock(mock_verificar_permisos, 'permisos')
        manager.attach_mock(mock_transaction.on_commit, 'on_commit')

        comunicado_instance = MagicMock()
        manager.attach_mock(comunicado_instance.delete, 'delete_db')

        servicio.delete_comunicado(usuario, comunicado_instance)

        nombres_llamadas = [call[0] for call in manager.mock_calls if call[0] in ['permisos', 'delete_db', 'on_commit']]
        
        orden_esperado = [
            'permisos',
            'delete_db',
            'on_commit'
        ]
        
        self.assertEqual(nombres_llamadas, orden_esperado)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_usa_referencia_de_imagen_capturada_antes_del_borrado(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Imagen se guarda antes de borrar comunicado

        Given: Un comunicado con una imagen de portada.
        When: Se ejecuta delete_comunicado.
        Then: Se debe capturar la referencia de la imagen ANTES de llamar a .delete().
                El callback de on_commit debe usar esa referencia previa (imagen_adjunta).
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        mock_imagen_original = MagicMock()
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen_original

        def side_effect_delete():
            comunicado_instance.imagen_portada = None 
            
        comunicado_instance.delete.side_effect = side_effect_delete

        servicio.delete_comunicado(usuario, comunicado_instance)

        callback_limpieza = mock_transaction.on_commit.call_args[0][0]

        callback_limpieza()

        mock_imagen_original.delete.assert_called_once_with(save=False)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_delete_comunicado_sin_imagen_no_registra_nada_en_on_commit(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Callback no se registra si no hay imagen

        Given: Un comunicado cuya imagen_portada es None (o evalúa como False).
        When: Se llama a delete_comunicado.
        Then: Se ejecuta el borrado del comunicado en la base de datos.
                ❗ NO se debe llamar a transaction.on_commit.
                Se confirma que la lógica condicional evita registros innecesarios.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = None

        resultado = servicio.delete_comunicado(usuario, comunicado_instance)

        mock_verificar_permisos.assert_called_once_with(usuario)
        comunicado_instance.delete.assert_called_once()

        mock_transaction.on_commit.assert_not_called()

        self.assertTrue(resultado)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_callback_usa_save_false_al_eliminar_imagen_para_evitar_errores_de_db(self, mock_verificar_permisos, mock_transaction):
        """
        Test: delete(save=False) correcto

        Given: Un proceso de borrado de comunicado con imagen.
        When: Se ejecuta el callback 'eliminar_archivo_seguro'.
        Then: El método .delete() de la imagen DEBE recibir save=False.
                Esto garantiza que solo se borra el archivo del storage
                y no se intenta una actualización imposible en la BD.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        mock_imagen = MagicMock()
        comunicado_instance = MagicMock()
        comunicado_instance.imagen_portada = mock_imagen

        servicio.delete_comunicado(usuario, comunicado_instance)
        callback_limpieza = mock_transaction.on_commit.call_args[0][0]

        callback_limpieza()

        mock_imagen.delete.assert_called_once_with(save=False)