from django.test import TestCase
from unittest.mock import Mock, PropertyMock, patch, MagicMock

from django.core.exceptions import PermissionDenied

from api.servicios.comunicado.comunicado_service import ComunicadoService
from api.models import CuerpoPertenencia


class ComunicadoNotificarTelegramServiceTests(TestCase):

    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_envio_correcto_con_imagen_flujo_completo(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Envío correcto con imagen (flujo completo)

        Given: El token de Telegram está configurado.
                El comunicado tiene imagen_portada.
                Las áreas tienen canales de Telegram configurados.
        When: Se llama a _notificar_telegram.
        Then: Se valida la cadena del ORM (filter -> exclude).
                Se abre el archivo en modo binario.
                Se usa la API /sendPhoto con el timeout de 10s.
                Se adjuntan los files y el payload correctamente.
        """
        servicio = ComunicadoService()

        mock_settings.TELEGRAM_BOT_TOKEN = 'token_secreto_123'

        area_input_1 = MagicMock(id=10)
        area_input_2 = MagicMock(id=20)
        areas_ids = [area_input_1, area_input_2]

        area_db_1 = MagicMock(telegram_channel_id='@canal_general')
        area_db_2 = MagicMock(telegram_channel_id='@canal_socios')

        mock_exclude = mock_area_interes.objects.filter.return_value.exclude
        mock_exclude.return_value = [area_db_1, area_db_2]

        comunicado = MagicMock()
        comunicado.titulo = "Gran Evento"
        comunicado.contenido = "Contenido de prueba"

        mock_file_handler = MagicMock()
        comunicado.imagen_portada.open.return_value.__enter__.return_value = mock_file_handler

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_area_interes.objects.filter.assert_called_once_with(
            id__in=[10, 20],
            telegram_channel_id__isnull=False
        )
        mock_exclude.assert_called_once_with(telegram_channel_id__exact='')

        self.assertEqual(comunicado.imagen_portada.open.call_count, 2)
        comunicado.imagen_portada.open.assert_called_with('rb')

        self.assertEqual(mock_post.call_count, 2)

        url_esperada = "https://api.telegram.org/bottoken_secreto_123/sendPhoto"
        
        args, kwargs = mock_post.call_args

        self.assertEqual(args[0], url_esperada)

        self.assertEqual(kwargs.get('timeout'), 10)

        self.assertEqual(kwargs.get('files'), {'photo': mock_file_handler})

        payload = kwargs.get('data')
        self.assertIn('chat_id', payload)
        self.assertEqual(payload['parse_mode'], 'HTML')
        self.assertIn("<b>🔔 Nuevo Comunicado: Gran Evento</b>", payload['caption'])



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_envio_correcto_sin_imagen(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Envío correcto sin imagen

        Given: El token de Telegram está configurado.
                El comunicado NO tiene imagen_portada (None).
                Hay un canal de Telegram configurado en el área.
        When: Se llama a _notificar_telegram.
        Then: Se utiliza el endpoint 'sendMessage'.
                El texto del comunicado se envía en el campo 'text' del payload.
                Se utiliza el timeout estándar de 5s para mensajes de texto.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'bot_token_abc'

        area_db = MagicMock(telegram_channel_id='@canal_solo_texto')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado = MagicMock()
        comunicado.titulo = "Aviso Urgente"
        comunicado.contenido = "Este es un mensaje sin foto."
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        url_esperada = "https://api.telegram.org/botbot_token_abc/sendMessage"
        args, kwargs = mock_post.call_args
        
        self.assertEqual(args[0], url_esperada)

        payload = kwargs.get('data')
        self.assertEqual(payload['chat_id'], '@canal_solo_texto')
        self.assertIn("Aviso Urgente", payload['text'])
        self.assertNotIn('caption', payload)

        self.assertEqual(kwargs.get('timeout'), 5)

        self.assertNotIn('files', kwargs, "Se adjuntó un archivo cuando no debía haber ninguno.")



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_envio_a_multiples_canales_de_telegram(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Múltiples canales de Telegram

        Given: El token de Telegram está configurado.
                Existen múltiples áreas con diferentes IDs de canal.
        When: Se llama a _notificar_telegram.
        Then: Se itera sobre todos los canales únicos.
                Se llama a requests.post tantas veces como canales haya.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        area_db_1 = MagicMock(telegram_channel_id='@canal_A')
        area_db_2 = MagicMock(telegram_channel_id='@canal_B')
        area_db_3 = MagicMock(telegram_channel_id='@canal_A')
        
        mock_area_interes.objects.filter.return_value.exclude.return_value = [
            area_db_1, area_db_2, area_db_3
        ]

        comunicado = MagicMock()
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(mock_post.call_count, 2)

        llamadas = [call.kwargs['data']['chat_id'] for call in mock_post.call_args_list]
        self.assertIn('@canal_A', llamadas)
        self.assertIn('@canal_B', llamadas)



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_telegram_token_no_configurado_aborta_ejecucion(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Token no configurado (Early Return)

        Given: TELEGRAM_BOT_TOKEN es None o no existe en settings.
        When: Se llama a _notificar_telegram.
        Then: Se imprime un mensaje de advertencia específico.
                El método termina inmediatamente (return).
                ❗ No se realiza ninguna petición HTTP (requests.post).
        """
        servicio = ComunicadoService()

        mock_settings.TELEGRAM_BOT_TOKEN = None
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1)]

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_print.assert_called_once_with("TELEGRAM_BOT_TOKEN no configurado.")

        mock_post.assert_not_called()



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_error_en_un_envio_no_detiene_el_bucle_de_otros_canales(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Excepción en requests (Resiliencia)

        Given: Dos canales de Telegram configurados.
        When: La primera petición a requests.post lanza una excepción (ej. Timeout).
                La segunda petición es exitosa.
        Then: Se captura el error del primer canal y se imprime por consola.
                El bucle continúa y se realiza el segundo envío correctamente.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'

        canal_A = "@canal_A"
        canal_B = "@canal_B"
        
        area_1 = MagicMock(telegram_channel_id=canal_A)
        area_2 = MagicMock(telegram_channel_id=canal_B)
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_1, area_2]

        error_msg = "Connection Timeout"
        mock_post.side_effect = [Exception(error_msg), MagicMock()]
        
        comunicado = MagicMock(imagen_portada=None)

        servicio._notificar_telegram(comunicado, [MagicMock(id=1), MagicMock(id=2)])

        self.assertEqual(mock_post.call_count, 2)

        canal_que_fallo = mock_post.call_args_list[0].kwargs['data']['chat_id']
        canal_que_tuvo_exito = mock_post.call_args_list[1].kwargs['data']['chat_id']

        mock_print.assert_called_with(f"Error enviando telegram al canal {canal_que_fallo}: {error_msg}")

        self.assertCountEqual(
            [canal_que_fallo, canal_que_tuvo_exito], 
            [canal_A, canal_B]
        )



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_error_al_abrir_imagen_se_captura_y_continua_bucle(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Error en open imagen (Resiliencia I/O)

        Given: Un comunicado con imagen_portada.
                Existen dos canales de Telegram.
        When: El método .open('rb') de la imagen lanza un IOError en el primer canal.
        Then: La excepción se captura en el bloque except.
                Se imprime el error en consola.
                El bucle continúa e intenta procesar el siguiente canal.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        canal_1 = "@canal_fallido"
        canal_2 = "@canal_exitoso"
        
        area_1 = MagicMock(telegram_channel_id=canal_1)
        area_2 = MagicMock(telegram_channel_id=canal_2)
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_1, area_2]

        comunicado = MagicMock()
        comunicado.titulo = "Test I/O"

        error_io = IOError("No se pudo leer el archivo de imagen")
        comunicado.imagen_portada.open.side_effect = error_io

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(comunicado.imagen_portada.open.call_count, 2)

        mock_print.assert_any_call(f"Error enviando telegram al canal {canal_1}: {error_io}")

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_truncado_de_caption_cuando_supera_limite_de_imagen(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Texto demasiado largo -> Caption > 1000 caracteres (con imagen)

        Given: Un comunicado con un contenido muy extenso (ej. 1500 caracteres).
                El comunicado tiene imagen_portada.
        When: Se llama a _notificar_telegram.
        Then: El campo 'caption' enviado a Telegram no supera los 1011 caracteres 
                (1000 del recorte + el sufijo "... (ver web)").
                Se verifica que el texto termina con el sufijo de truncado.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        contenido_extenso = "A" * 1500
        comunicado = MagicMock()
        comunicado.titulo = "Noticia Larga"
        comunicado.contenido = contenido_extenso

        comunicado.imagen_portada.open.return_value.__enter__.return_value = MagicMock()

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        payload = mock_post.call_args.kwargs['data']
        caption_enviado = payload['caption']

        self.assertEqual(len(caption_enviado), 1013)
        self.assertTrue(caption_enviado.endswith("... (ver web)"))

        self.assertIn("<b>🔔 Nuevo Comunicado: Noticia Larga</b>", caption_enviado)



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_truncado_de_mensaje_cuando_supera_limite_de_texto_plano(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Texto > 3000 caracteres (sin imagen)

        Given: Un comunicado con un contenido extremadamente largo (ej. 5000 caracteres).
                El comunicado NO tiene imagen_portada.
        When: Se llama a _notificar_telegram.
        Then: El campo 'text' enviado a Telegram se corta a 3000 caracteres.
                Se verifica que se añade el sufijo de truncado "...".
                El tamaño final del mensaje es controlado para evitar errores 400.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        area_db = MagicMock(telegram_channel_id='@canal_texto_largo')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        contenido_gigante = "B" * 5000
        comunicado = MagicMock()
        comunicado.titulo = "Boletín Extenso"
        comunicado.contenido = contenido_gigante
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        payload = mock_post.call_args.kwargs['data']
        texto_enviado = payload['text']

        self.assertEqual(len(texto_enviado), 3003) 
        self.assertTrue(texto_enviado.endswith("..."))

        self.assertIn("<b>🔔 Nuevo Comunicado: Boletín Extenso</b>", texto_enviado)