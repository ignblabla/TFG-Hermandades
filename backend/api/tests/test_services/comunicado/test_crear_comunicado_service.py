from django.test import TestCase
from unittest.mock import patch, MagicMock

from django.core.exceptions import PermissionDenied

from api.servicios.comunicado.comunicado_service import ComunicadoService


class ComunicadoServiceTests(TestCase):

    # -----------------------------------------------------------------------------------------------------
    # CREAR COMUNICADO 
    # -----------------------------------------------------------------------------------------------------

    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    @patch.object(ComunicadoService, '_notificar_telegram')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_create_comunicado_flujo_completo_con_podcast(self, mock_permisos, mock_notificar, mock_comunicado, mock_transaction):
        """
        Test: Creación exitosa (flujo completo con podcast)

        Given: Un usuario válido y datos correctos que incluyen áreas de interés y generar_podcast=True.
        When: Se llama a create_comunicado.
        Then: Se crea el comunicado vinculando al usuario como autor.
            Se asignan las áreas de interés.
            Se notifica por Telegram.
            Se encolan DOS tareas en on_commit (embedding y podcast).
            Retorna la instancia creada.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        mock_areas = [MagicMock(id=1), MagicMock(id=2)]
        
        data_validada = {
            'titulo': 'Nuevo Evento',
            'contenido': 'Detalles...',
            'areas_interes': mock_areas,
            'generar_podcast': True
        }

        mock_instancia = MagicMock()
        mock_instancia.generar_podcast = True
        mock_comunicado.objects.create.return_value = mock_instancia

        resultado = servicio.create_comunicado(usuario, data_validada)

        mock_permisos.assert_called_once_with(usuario)
        mock_comunicado.objects.create.assert_called_once_with(
            autor=usuario, 
            titulo='Nuevo Evento', 
            contenido='Detalles...', 
            generar_podcast=True
        )
        mock_instancia.areas_interes.set.assert_called_once_with(mock_areas)

        mock_notificar.assert_called_once_with(mock_instancia, mock_areas)
        self.assertEqual(mock_transaction.on_commit.call_count, 2, "Deberían encolarse 2 tareas (embedding y podcast)")
        
        self.assertEqual(resultado, mock_instancia)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    @patch.object(ComunicadoService, '_notificar_telegram')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_create_comunicado_sin_podcast_solo_encola_tarea_de_embedding(self, mock_permisos, mock_notificar, mock_comunicado, mock_transaction):
        """
        Test: Creación exitosa sin podcast

        Given: Datos válidos pero con generar_podcast=False.
        When: Se llama a create_comunicado.
        Then: El flujo procede normalmente, pero NUNCA se encola 
            la tarea secundaria de generar podcast.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        mock_areas = [MagicMock(id=1)]
        
        data_validada = {'areas_interes': mock_areas, 'generar_podcast': False}

        mock_instancia = MagicMock()
        mock_instancia.generar_podcast = False
        mock_comunicado.objects.create.return_value = mock_instancia

        servicio.create_comunicado(usuario, data_validada)

        self.assertEqual(mock_transaction.on_commit.call_count, 1, "Solo debe encolarse el embedding")



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_create_comunicado_falla_si_no_se_proveen_areas_de_interes(self, mock_permisos, mock_comunicado):
        """
        Test: Fallo de validación por áreas vacías

        Given: Un payload de datos que no contiene 'areas_interes' o está vacío.
        When: Se intenta crear el comunicado.
        Then: Se lanza un ValueError explícito.
            Se aborta la ejecución ANTES de llamar a la base de datos.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        data_sin_areas = {'titulo': 'Fallo', 'areas_interes': []}

        with self.assertRaisesMessage(ValueError, "No se puede crear un comunicado sin al menos un área de interés asociada."):
            servicio.create_comunicado(usuario, data_sin_areas)

        mock_comunicado.objects.create.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    @patch.object(ComunicadoService, '_notificar_telegram')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_create_comunicado_ignora_intentos_de_suplantar_al_autor(self, mock_permisos, mock_notificar, mock_comunicado, mock_transaction):
        """
        Test: Saneamiento de datos de seguridad (Anti-suplantación)

        Given: Un payload malicioso que incluye 'autor' o 'autor_id' para forzar la autoría.
        When: Se llama a create_comunicado.
        Then: Los campos maliciosos son eliminados del diccionario (pop).
            La creación se realiza forzando autor=usuario (el usuario autenticado real).
        """
        servicio = ComunicadoService()
        usuario_real = MagicMock()
        
        data_maliciosa = {
            'titulo': 'Hack', 
            'areas_interes': [MagicMock(id=1)],
            'autor': 'Usuario_Falso',
            'autor_id': 999
        }

        mock_comunicado.objects.create.return_value = MagicMock(generar_podcast=False)

        servicio.create_comunicado(usuario_real, data_maliciosa)

        mock_comunicado.objects.create.assert_called_once_with(
            autor=usuario_real, 
            titulo='Hack'
        )



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_create_comunicado_falla_si_usuario_no_tiene_permisos(self, mock_permisos, mock_comunicado):
        """
        Test: Bloqueo de seguridad inicial

        Given: Un usuario sin permisos.
        When: Se llama a create_comunicado y _verificar_permisos lanza PermissionDenied.
        Then: La excepción se propaga y NINGUNA operación posterior 
            (saneamiento, creación, notificación) se ejecuta.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        mock_permisos.side_effect = PermissionDenied("Bloqueado")

        with self.assertRaises(PermissionDenied):
            servicio.create_comunicado(usuario, {'areas_interes': [1, 2]})

        mock_comunicado.objects.create.assert_not_called()