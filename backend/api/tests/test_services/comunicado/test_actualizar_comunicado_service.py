from unittest.mock import MagicMock, patch
from django.test import TestCase
from api.servicios.comunicado.comunicado_service import ComunicadoService
from django.core.exceptions import PermissionDenied


class UpdateComunicadoServiceTests(TestCase):

    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_comunicado_flujo_completo_con_cambio_de_texto_y_areas(self, mock_permisos, mock_transaction):
        """
        Test: Actualización completa con disparadores asíncronos.

        Given: Un comunicado existente (con generar_podcast=True) y datos válidos que 
            modifican el 'titulo' y actualizan las 'areas_interes'.
        When: Se llama a update_comunicado.
        Then: Se actualizan las áreas mediante .set().
            El título se modifica en la instancia.
            Se detecta el cambio de texto y se encolan DOS tareas (embedding y podcast).
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.titulo = "Titulo Viejo"
        comunicado_instance.contenido = "Contenido original"
        comunicado_instance.generar_podcast = True
        
        mock_areas = [MagicMock(id=1), MagicMock(id=2)]
        data_validada = {
            'titulo': 'Titulo Nuevo',
            'estado': 'PUBLICADO',
            'areas_interes': mock_areas
        }

        resultado = servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        mock_permisos.assert_called_once_with(usuario)

        comunicado_instance.areas_interes.set.assert_called_once_with(mock_areas)

        self.assertEqual(comunicado_instance.titulo, 'Titulo Nuevo')
        self.assertEqual(comunicado_instance.estado, 'PUBLICADO')
        comunicado_instance.save.assert_called_once()

        self.assertEqual(mock_transaction.on_commit.call_count, 2)
        self.assertEqual(resultado, comunicado_instance)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_comunicado_sin_cambio_de_texto_no_dispara_tareas_asincronas(self, mock_permisos, mock_transaction):
        """
        Test: Actualización menor (sin triggers).

        Given: Un comunicado y datos que NO modifican ni el título ni el contenido 
            (ej. solo se cambia un estado o fecha).
        When: Se llama a update_comunicado.
        Then: La instancia se actualiza y se guarda.
            NUNCA se llama a transaction.on_commit para regenerar vectores.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.titulo = "Mismo Titulo"
        comunicado_instance.contenido = "Mismo Contenido"
        
        data_validada = {
            'titulo': 'Mismo Titulo',
            'es_destacado': True
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertTrue(comunicado_instance.es_destacado)
        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_not_called()



    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_comunicado_falla_si_se_envian_areas_vacias(self, mock_permisos):
        """
        Test: Validación de áreas vacías.

        Given: Un payload que incluye la clave 'areas_interes' explícitamente vacía.
        When: Se intenta actualizar.
        Then: Se lanza un ValueError antes de modificar la instancia o guardar en BD.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        comunicado_instance = MagicMock()
        
        data_mala = {'areas_interes': [], 'titulo': 'Intento fallido'}

        with self.assertRaisesMessage(ValueError, "No se puede actualizar un comunicado sin al menos un área de interés asociada."):
            servicio.update_comunicado(usuario, comunicado_instance, data_mala)

        comunicado_instance.areas_interes.set.assert_not_called()
        comunicado_instance.save.assert_not_called()



    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_comunicado_falla_si_se_envia_atributo_inexistente(self, mock_permisos):
        """
        Test: Prevención de inyección de atributos.

        Given: Un payload de actualización con un campo que el modelo no posee 
            (hasattr devolverá False).
        When: Se ejecuta update_comunicado.
        Then: Se lanza AttributeError protegiendo la integridad de la base de datos.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        class ComunicadoSimulado:
            titulo = "Original"

        comunicado_instance = ComunicadoSimulado()
        comunicado_instance.save = MagicMock()
        
        data_con_basura = {'titulo': 'Nuevo', 'campo_inventado': 'hacker'}

        with self.assertRaisesMessage(AttributeError, "El campo 'campo_inventado' no existe en el modelo Comunicado."):
            servicio.update_comunicado(usuario, comunicado_instance, data_con_basura)

        comunicado_instance.save.assert_not_called()



    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_comunicado_falla_si_usuario_no_tiene_permisos(self, mock_permisos):
        """
        Test: Bloqueo de seguridad de actualización.

        Given: Un usuario sin privilegios.
        When: Llama a update_comunicado.
        Then: Se lanza PermissionDenied y el modelo queda intacto.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        comunicado_instance = MagicMock()
        
        mock_permisos.side_effect = PermissionDenied("Sin acceso")

        with self.assertRaises(PermissionDenied):
            servicio.update_comunicado(usuario, comunicado_instance, {'titulo': 'Nuevo'})

        comunicado_instance.save.assert_not_called()