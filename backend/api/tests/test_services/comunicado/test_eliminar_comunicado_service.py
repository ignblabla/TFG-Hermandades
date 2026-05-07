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