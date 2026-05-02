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
    def test_token_configurado_construye_urls_correctamente(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Token configurado correctamente -> Construcción de URLs

        Given: Un token de Telegram específico configurado en settings.
        When: Se procesan envíos con y sin imagen.
        Then: Las URLs generadas deben seguir el formato estricto:
                https://api.telegram.org/bot<token>/<metodo>
        """
        servicio = ComunicadoService()
        token_test = "123456789:ABCDEFGH"
        mock_settings.TELEGRAM_BOT_TOKEN = token_test

        area_db = MagicMock(telegram_channel_id='@test_channel')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado_con_foto = MagicMock()
        comunicado_con_foto.imagen_portada = MagicMock()

        comunicado_con_foto.imagen_portada.open.return_value.__enter__.return_value = MagicMock()
        
        servicio._notificar_telegram(comunicado_con_foto, [MagicMock(id=1)])
        
        expected_photo_url = f"https://api.telegram.org/bot{token_test}/sendPhoto"
        self.assertEqual(mock_post.call_args_list[0][0][0], expected_photo_url)

        mock_post.reset_mock()
        comunicado_sin_foto = MagicMock()
        comunicado_sin_foto.imagen_portada = None
        
        servicio._notificar_telegram(comunicado_sin_foto, [MagicMock(id=1)])
        
        expected_message_url = f"https://api.telegram.org/bot{token_test}/sendMessage"
        self.assertEqual(mock_post.call_args_list[0][0][0], expected_message_url)



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



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mensaje_corto_no_se_trunca_en_ningun_flujo(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Mensaje normal (< límites)

        Given: Un comunicado con título y contenido cortos.
        When: Se envía con imagen (límite 1000) y sin imagen (límite 3000).
        Then: El texto llega completo al payload.
                No se añade el sufijo de truncado "...".
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        
        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        titulo = "Aviso Corto"
        contenido = "Este contenido es breve."
        texto_esperado = f"<b>🔔 Nuevo Comunicado: {titulo}</b>\n\n{contenido}"

        comunicado_foto = MagicMock()
        comunicado_foto.titulo = titulo
        comunicado_foto.contenido = contenido
        comunicado_foto.imagen_portada.open.return_value.__enter__.return_value = MagicMock()

        servicio._notificar_telegram(comunicado_foto, [MagicMock(id=1)])
        
        payload_foto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_foto['caption'], texto_esperado)
        self.assertNotIn("... (ver web)", payload_foto['caption'])

        mock_post.reset_mock()
        comunicado_texto = MagicMock()
        comunicado_texto.titulo = titulo
        comunicado_texto.contenido = contenido
        comunicado_texto.imagen_portada = None

        servicio._notificar_telegram(comunicado_texto, [MagicMock(id=1)])

        payload_texto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_texto['text'], texto_esperado)
        self.assertNotIn("...", payload_texto['text'])



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mensaje_con_lista_de_areas_vacia_no_realiza_envios(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Mensaje con áreas vacías

        Given: Una lista de areas_ids vacía [].
        When: Se llama a _notificar_telegram.
        Then: La consulta al ORM devuelve un QuerySet vacío.
                No se inicia el bucle de envío.
                NUNCA se llama a requests.post.
                El flujo termina sin errores.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        mock_area_interes.objects.filter.return_value.exclude.return_value = []
        
        comunicado = MagicMock()
        areas_ids_vacias = []

        servicio._notificar_telegram(comunicado, areas_ids_vacias)

        mock_area_interes.objects.filter.assert_called_once_with(
            id__in=[], 
            telegram_channel_id__isnull=False
        )

        mock_post.assert_not_called()

        self.assertFalse(comunicado.titulo.called)



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



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_fallo_orm_en_filtro_de_areas_propaga_excepcion(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Errores en áreas -> AreaInteres.objects.filter falla

        Given: El token de Telegram está configurado.
        When: Se intenta filtrar las áreas en la base de datos.
                El ORM lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga y corta la ejecución del método.
                ❗ No se llega a la sección de envío (requests.post).
                Se garantiza que no se ignoran errores de infraestructura.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'

        error_db = Exception("Error de conexión a la base de datos")
        mock_area_interes.objects.filter.side_effect = error_db
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1)]

        with self.assertRaises(Exception) as context:
            servicio._notificar_telegram(comunicado, areas_ids)
            
        self.assertEqual(str(context.exception), "Error de conexión a la base de datos")

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
    def test_areas_sin_configuracion_telegram_no_producen_envios(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: áreas_con_telegram vacío

        Given: El token de Telegram está configurado.
                Se pasan IDs de áreas, pero el ORM devuelve una lista vacía 
                (porque no tienen channel_id o están vacíos).
        When: Se llama a _notificar_telegram.
        Then: El conjunto 'canales_a_enviar' resulta vacío.
                No se realiza ninguna llamada a requests.post.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        mock_area_interes.objects.filter.return_value.exclude.return_value = []
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1), MagicMock(id=2)]

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_area_interes.objects.filter.assert_called_once()

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_canales_con_string_vacio_son_excluidos_y_no_reciben_notificacion(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Telegram channels inválidos (string vacío)

        Given: El token de Telegram está configurado.
                Existen áreas donde telegram_channel_id es una cadena vacía ('').
        When: Se llama a _notificar_telegram.
        Then: La consulta al ORM utiliza .exclude(telegram_channel_id__exact='') correctamente.
                No se realiza ninguna petición a requests.post para esos registros.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'

        mock_area_interes.objects.filter.return_value.exclude.return_value = []
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1)]

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_area_interes.objects.filter.return_value.exclude.assert_called_once_with(
            telegram_channel_id__exact=''
        )

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



    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_areas_ids_con_objetos_mal_formados_lanza_attribute_error(self, mock_area_interes, mock_settings):
        """
        Test: Datos mal formados -> areas_ids sin .id

        Given: El token de Telegram está configurado.
                Se pasa una lista 'areas_ids' que contiene objetos inválidos 
                (ej. strings) que no tienen el atributo .id.
        When: Se intenta construir la lista para el filtro del ORM.
        Then: Se lanza un AttributeError.
                Se valida que el método requiere objetos con una estructura específica.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        
        comunicado = MagicMock()
        areas_ids_corruptos = ["area_1", "area_2"] 

        with self.assertRaises(AttributeError):
            servicio._notificar_telegram(comunicado, areas_ids_corruptos)

        mock_area_interes.objects.filter.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_comunicado_sin_atributos_necesarios_lanza_error_al_construir_mensaje(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Comunicado sin título o contenido (Atributos faltantes)

        Given: Un objeto 'comunicado' que carece del atributo 'titulo' o 'contenido'.
        When: El servicio intenta construir el 'texto_mensaje'.
        Then: Se lanza un AttributeError.
                Se valida que el servicio depende de un objeto comunicado completo 
                y no gestiona la ausencia de campos obligatorios de plantilla.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado_incompleto = MagicMock(spec=[])

        with self.assertRaises(AttributeError):
            servicio._notificar_telegram(comunicado_incompleto, [MagicMock(id=1)])

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mezcla_canales_validos_e_invalidos_solo_procesa_los_validos(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Un canal válido + uno inválido (Mezcla de canales)

        Given: El token de Telegram está configurado.
                Existen tres áreas: una válida, una con channel_id None 
                y una con channel_id vacío ('').
        When: Se llama a _notificar_telegram.
        Then: Solo se realiza una petición requests.post (la del canal válido).
                Se valida que los filtros .filter() y .exclude() limpian 
                correctamente la lista de destinatarios.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        canal_valido = "@canal_valido"
        area_valida = MagicMock(telegram_channel_id=canal_valido)

        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_valida]
        
        comunicado = MagicMock(imagen_portada=None)
        areas_ids = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]

        servicio._notificar_telegram(comunicado, areas_ids)

        self.assertEqual(mock_post.call_count, 1)

        payload = mock_post.call_args.kwargs['data']
        self.assertEqual(payload['chat_id'], canal_valido)

        mock_area_interes.objects.filter.assert_called_once_with(
            id__in=[a.id for a in areas_ids],
            telegram_channel_id__isnull=False
        )
        mock_area_interes.objects.filter.return_value.exclude.assert_called_once_with(
            telegram_channel_id__exact=''
        )



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_excepcion_en_un_canal_no_detiene_envio_a_otros(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Excepción en un canal no afecta otros

        Given: Dos canales de Telegram configurados.
        When: El primer envío de requests.post lanza una excepción (ej. ConnectionError).
        Then: Se captura el error y se imprime por consola.
                El bucle continúa con el siguiente canal.
                Se verifica que se realizaron ambos intentos de envío.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        canal_1 = "@canal_con_error"
        canal_2 = "@canal_exitoso"
        
        area_1 = MagicMock(telegram_channel_id=canal_1)
        area_2 = MagicMock(telegram_channel_id=canal_2)

        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_1, area_2]

        mock_post.side_effect = [Exception("Error de red"), MagicMock()]
        
        comunicado = MagicMock(imagen_portada=None)

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(mock_post.call_count, 2)

        llamadas_print = [call.args[0] for call in mock_print.call_args_list]
        self.assertTrue(any("Error enviando telegram al canal" in s for s in llamadas_print))

        chat_ids_procesados = [call.kwargs['data']['chat_id'] for call in mock_post.call_args_list]
        self.assertIn(canal_1, chat_ids_procesados)
        self.assertIn(canal_2, chat_ids_procesados)



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mensaje_se_construye_una_sola_vez_fuera_del_bucle(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Orden correcto de construcción del mensaje

        Given: El token de Telegram está configurado.
                Existen múltiples canales de Telegram (3 canales).
        When: Se llama a _notificar_telegram.
        Then: El título y contenido del comunicado solo se acceden una vez.
                Se garantiza que la construcción del string es externa al bucle for,
                optimizando el uso de CPU y memoria.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        canales = ['@canal_1', '@canal_2', '@canal_3']
        areas_db = [MagicMock(telegram_channel_id=c) for c in canales]
        mock_area_interes.objects.filter.return_value.exclude.return_value = areas_db

        comunicado = MagicMock()

        mock_titulo = PropertyMock(return_value="Título Único")
        mock_contenido = PropertyMock(return_value="Contenido Único")

        type(comunicado).titulo = mock_titulo
        type(comunicado).contenido = mock_contenido
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(mock_post.call_count, 3)

        mock_titulo.assert_called_once()
        mock_contenido.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_siempre_se_utiliza_html_como_parse_mode(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Uso correcto de HTML parse_mode

        Given: El token de Telegram está configurado.
        When: Se realiza un envío tanto con imagen como sin imagen.
        Then: El parámetro 'parse_mode' en el payload de la petición 
                debe ser siempre exactamente "HTML".
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado_con_foto = MagicMock()
        comunicado_con_foto.imagen_portada.open.return_value.__enter__.return_value = MagicMock()
        
        servicio._notificar_telegram(comunicado_con_foto, [MagicMock(id=1)])
        
        payload_foto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_foto.get('parse_mode'), "HTML", "sendPhoto debe usar parse_mode HTML")

        mock_post.reset_mock()
        comunicado_sin_foto = MagicMock()
        comunicado_sin_foto.imagen_portada = None
        
        servicio._notificar_telegram(comunicado_sin_foto, [MagicMock(id=1)])
        
        payload_texto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_texto.get('parse_mode'), "HTML", "sendMessage debe usar parse_mode HTML")