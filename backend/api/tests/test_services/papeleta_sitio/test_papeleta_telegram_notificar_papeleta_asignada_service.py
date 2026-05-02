from unittest import TestCase
from unittest.mock import patch
from api.servicios.papeleta_sitio.papeleta_telegram_service import TelegramWebhookService

class TestNotificarPapeletaAsignadaPositivos(TestCase):

    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_envia_notificacion_cuando_estado_asignada(self, mock_settings, mock_post):
        """
        Test: Envía notificación cuando estado = "ASIGNADA"

        Given: Credenciales de bot válidas y los datos de un hermano con un puesto asignado en el reparto.
        When: Se llama al servicio de notificación con el estado "ASIGNADA".
        Then: Se debe realizar una petición POST a Telegram construyendo el mensaje de éxito, incluyendo el nombre del puesto y configurando el parse_mode en HTML.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token_de_prueba"
        mock_settings.FRONTEND_URL = "https://mi-web-frontend.test"

        chat_id = 98765
        nombre_hermano = "Carlos"
        nombre_acto = "Salida Procesional"
        estado = "ASIGNADA"
        nombre_puesto = "Cirio Tramo 2"

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id, nombre_hermano, nombre_acto, estado, nombre_puesto
        )

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        url_llamada = args[0]
        self.assertEqual(url_llamada, "https://api.telegram.org/bottoken_de_prueba/sendMessage")

        payload = kwargs.get('json')
        self.assertEqual(payload['chat_id'], chat_id)
        self.assertEqual(payload['parse_mode'], "HTML")
        self.assertTrue(payload['disable_web_page_preview'])

        texto_enviado = payload['text']
        self.assertIn("✅ Se le ha asignado el puesto:", texto_enviado)
        self.assertIn(f"<b>{nombre_puesto}</b>", texto_enviado)
        self.assertIn(f"<b>{nombre_acto}</b>", texto_enviado)
        self.assertIn("https://mi-web-frontend.test/mis-papeletas-de-sitio", texto_enviado)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_envia_notificacion_cuando_estado_no_es_asignada(self, mock_settings, mock_post):
        """
        Test: Envía notificación cuando estado ≠ "ASIGNADA"

        Given: Credenciales válidas y un hermano al que se le ha procesado el reparto sin obtener un puesto (ej: estado "DENEGADA" o "EN_LISTA_ESPERA").
        When: Se invoca la función de notificación.
        Then: El texto enviado al usuario debe contener el mensaje alternativo indicando que lamentablemente no se le asignó puesto.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        mock_settings.FRONTEND_URL = "http://test-url"

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=123, 
            nombre_hermano="Ana", 
            nombre_acto="Viacrucis", 
            estado="DENEGADA"
        )

        kwargs = mock_post.call_args[1]
        texto_enviado = kwargs['json']['text']
        
        self.assertIn("❌ Lamentablemente, no ha sido posible asignarle ninguno de los puestos", texto_enviado)
        self.assertNotIn("✅ Se le ha asignado el puesto", texto_enviado)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_construye_correctamente_la_url_de_telegram(self, mock_settings, mock_post):
        """
        Test: Construye correctamente la URL de Telegram

        Given: Un token específico almacenado en la configuración de la app.
        When: Se procesa cualquier tipo de notificación.
        Then: La URL de la petición POST a Telegram debe estar construida con el token exacto interpolado en la ruta.
        """
        token_prueba = "token_bot_12345"
        mock_settings.TELEGRAM_BOT_TOKEN = token_prueba

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=123, 
            nombre_hermano="Luis", 
            nombre_acto="Acto", 
            estado="ASIGNADA"
        )

        url_llamada = mock_post.call_args[0][0]
        self.assertEqual(url_llamada, f"https://api.telegram.org/bot{token_prueba}/sendMessage")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_construye_correctamente_url_papeletas(self, mock_settings, mock_post):
        """
        Test: Construye correctamente url_papeletas

        Given: Una URL personalizada para el frontend especificada en las variables de entorno.
        When: Se genera el texto del mensaje para Telegram.
        Then: La ruta hacia las papeletas de sitio debe concatenarse correctamente a la URL base del frontend y aparecer en el texto.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        url_base_custom = "https://hermandad-app.es"
        mock_settings.FRONTEND_URL = url_base_custom

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=123, 
            nombre_hermano="Paco", 
            nombre_acto="Acto", 
            estado="ASIGNADA"
        )

        kwargs = mock_post.call_args[1]
        texto_enviado = kwargs['json']['text']
        self.assertIn(f"{url_base_custom}/mis-papeletas-de-sitio", texto_enviado)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_usa_url_por_defecto_si_frontend_url_no_existe(self, mock_settings, mock_post):
        """
        Test: Usa URL por defecto si FRONTEND_URL no existe

        Given: Un entorno de ejecución donde la variable de configuración FRONTEND_URL no está definida.
        When: Se invoca getattr sobre settings esperando una ruta para el frontend.
        Then: La función debe usar la URL por defecto 'https://mi-web-frontend.onrender.com' de forma segura.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"

        del mock_settings.FRONTEND_URL 

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=123, 
            nombre_hermano="Maria", 
            nombre_acto="Acto", 
            estado="ASIGNADA"
        )

        kwargs = mock_post.call_args[1]
        texto_enviado = kwargs['json']['text']
        self.assertIn("https://mi-web-frontend.onrender.com/mis-papeletas-de-sitio", texto_enviado)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_payload_correcto_chat_id_text_parse_mode_disable_web_page_preview(self, mock_settings, mock_post):
        """
        Test: Payload correcto (chat_id, text, parse_mode, disable_web_page_preview)

        Given: Un entorno configurado y datos válidos para la notificación.
        When: Se construye y envía el mensaje.
        Then: El diccionario json enviado a requests.post debe contener exactamente las cuatro claves requeridas por la API de Telegram con sus valores correspondientes.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token_valido"
        chat_id_prueba = 12345
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=chat_id_prueba, 
            nombre_hermano="Manuel", 
            nombre_acto="Madrugá", 
            estado="ASIGNADA",
            nombre_puesto="Costalero"
        )

        kwargs = mock_post.call_args[1]
        payload = kwargs.get('json')
        
        self.assertIn('chat_id', payload)
        self.assertIn('text', payload)
        self.assertIn('parse_mode', payload)
        self.assertIn('disable_web_page_preview', payload)
        
        self.assertEqual(payload['chat_id'], chat_id_prueba)
        self.assertTrue(payload['disable_web_page_preview'])



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_inserta_correctamente_nombre_hermano_nombre_acto_y_nombre_puesto(self, mock_settings, mock_post):
        """
        Test: Inserta correctamente nombre_hermano, nombre_acto y nombre_puesto

        Given: Cadenas de texto específicas para el nombre del hermano, el acto y el puesto asignado.
        When: Se formatea el mensaje de éxito (estado="ASIGNADA").
        Then: Los tres datos deben aparecer correctamente inyectados dentro del string final que se envía a Telegram.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        hermano = "Elena Rodríguez"
        acto = "Procesión del Corpus"
        puesto = "Acólito Ceriferario"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=111, 
            nombre_hermano=hermano, 
            nombre_acto=acto, 
            estado="ASIGNADA",
            nombre_puesto=puesto
        )

        kwargs = mock_post.call_args[1]
        texto = kwargs['json']['text']
        
        self.assertIn(hermano, texto)
        self.assertIn(acto, texto)
        self.assertIn(puesto, texto)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_usa_correctamente_parse_mode_html(self, mock_settings, mock_post):
        """
        Test: Usa correctamente parse_mode="HTML"

        Given: Una llamada normal al servicio de notificaciones.
        When: Se prepara el payload de la petición.
        Then: El valor de la clave 'parse_mode' debe ser estrictamente "HTML" para que Telegram renderice las etiquetas <b>, <i> y <a>.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=123, 
            nombre_hermano="Juan", 
            nombre_acto="Acto", 
            estado="ASIGNADA"
        )

        kwargs = mock_post.call_args[1]
        self.assertEqual(kwargs['json']['parse_mode'], "HTML")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_usa_timeout_5_en_la_peticion(self, mock_settings, mock_post):
        """
        Test: Usa timeout=5 en la petición

        Given: La ejecución del método que realiza la llamada HTTP a Telegram.
        When: Se invoca la librería requests.
        Then: Se debe incluir el argumento timeout=5 para evitar que la aplicación se bloquee si la API de Telegram no responde.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=123, 
            nombre_hermano="Pepe", 
            nombre_acto="Acto", 
            estado="DENEGADA"
        )

        kwargs = mock_post.call_args[1]
        self.assertEqual(kwargs.get('timeout'), 5)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_se_llama_a_requests_post_una_unica_vez(self, mock_settings, mock_post):
        """
        Test: Se llama a requests.post una única vez

        Given: Un flujo de ejecución completamente válido.
        When: El servicio procesa y notifica al usuario.
        Then: El mock del método post de requests debe registrar exactamente una única llamada, garantizando que no se envían mensajes duplicados.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=999, 
            nombre_hermano="Antonio", 
            nombre_acto="Viernes Santo", 
            estado="ASIGNADA",
            nombre_puesto="Nazareno"
        )

        mock_post.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_no_hay_token(self, mock_settings, mock_post):
        """
        Test: No hay token

        Given: Un entorno donde TELEGRAM_BOT_TOKEN es None.
        When: Se intenta notificar la asignación de una papeleta.
        Then: La función debe retornar inmediatamente sin invocar a requests.post.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = None

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=12345,
            nombre_hermano="Carlos",
            nombre_acto="Viernes Santo",
            estado="ASIGNADA"
        )

        mock_post.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_token_vacio(self, mock_settings, mock_post):
        """
        Test: Token vacío

        Given: Un entorno donde TELEGRAM_BOT_TOKEN es un string vacío.
        When: Se evalúa la condición de salida rápida (if not token).
        Then: La función debe abortar la ejecución sin enviar la petición HTTP.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = ""

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=12345,
            nombre_hermano="Carlos",
            nombre_acto="Viernes Santo",
            estado="ASIGNADA"
        )

        mock_post.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_chat_id_es_none(self, mock_settings, mock_post):
        """
        Test: chat_id es None

        Given: Un token de bot válido pero un chat_id proporcionado como None.
        When: Se verifica si existen los datos mínimos para el envío.
        Then: La función retorna sin intentar enviar el mensaje a un destino nulo.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "valid_token"

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=None,
            nombre_hermano="Carlos",
            nombre_acto="Viernes Santo",
            estado="ASIGNADA"
        )

        mock_post.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_chat_id_vacio(self, mock_settings, mock_post):
        """
        Test: chat_id vacío

        Given: Un token de bot válido y un chat_id que es un string vacío.
        When: Se evalúa la condición booleana (if not chat_id).
        Then: Se activa la salida temprana y no se ejecuta requests.post.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "valid_token"

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id="",
            nombre_hermano="Carlos",
            nombre_acto="Viernes Santo",
            estado="ASIGNADA"
        )

        mock_post.assert_not_called()



    @patch('builtins.print')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_error_en_requests_post(self, mock_settings, mock_post, mock_print):
        """
        Test: Error en requests.post

        Given: Una configuración correcta que permite llegar al bloque de envío HTTP.
        When: La ejecución de requests.post lanza una excepción no controlada internamente (ej. timeout o error de conexión).
        Then: El bloque try/except captura la excepción, impidiendo que escale, y la registra en consola indicando el chat_id afectado.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "valid_token"
        chat_id_prueba = 999
        mensaje_error = "Max retries exceeded"
        mock_post.side_effect = Exception(mensaje_error)

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=chat_id_prueba,
            nombre_hermano="Carlos",
            nombre_acto="Viernes Santo",
            estado="ASIGNADA"
        )

        mock_print.assert_called_once_with(f"Error enviando notificación de papeleta a {chat_id_prueba}: {mensaje_error}")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_estado_distinto_de_asignada_valores_inesperados(self, mock_settings, mock_post):
        """
        Test: estado distinto de "ASIGNADA" (valores inesperados)

        Given: Un estado no contemplado específicamente (ej: "PENDIENTE" o un string vacío).
        When: Se evalúa la condición de la estructura del mensaje.
        Then: El servicio debe caer en la rama 'else' y enviar el mensaje de "no asignación" por defecto, sin fallar.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=1, nombre_hermano="H", nombre_acto="A", estado="VALOR_RARORÍSIMO"
        )

        kwargs = mock_post.call_args[1]
        self.assertIn("❌ Lamentablemente, no ha sido posible", kwargs['json']['text'])



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_nombre_puesto_es_none_en_estado_asignada(self, mock_settings, mock_post):
        """
        Test: nombre_puesto es None en estado "ASIGNADA"

        Given: Una asignación confirmada pero donde el nombre del puesto es nulo.
        When: Se interpola el valor en el f-string del mensaje de éxito.
        Then: El mensaje debe contener el texto "None" en el lugar del puesto y la ejecución debe completarse.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=1, nombre_hermano="H", nombre_acto="A", estado="ASIGNADA", nombre_puesto=None
        )

        kwargs = mock_post.call_args[1]
        self.assertIn("Se le ha asignado el puesto: <b>None</b>", kwargs['json']['text'])



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_nombre_hermano_o_nombre_acto_vacios(self, mock_settings, mock_post):
        """
        Test: nombre_hermano o nombre_acto vacíos

        Given: Strings vacíos en los campos de identificación del hermano o del acto.
        When: Se genera el payload.
        Then: El mensaje se construye con huecos vacíos donde deberían ir los nombres, pero la petición POST se realiza normalmente.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=1, nombre_hermano="", nombre_acto="", estado="ASIGNADA", nombre_puesto="P"
        )

        kwargs = mock_post.call_args[1]
        self.assertIn("Estimado/a ,", kwargs['json']['text'])
        mock_post.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_caracteres_especiales_en_el_mensaje_html(self, mock_settings, mock_post):
        """
        Test: Caracteres especiales en el mensaje (HTML)

        Given: Nombres que contienen símbolos que podrían interferir con HTML (aunque no se escapan explícitamente en el servicio).
        When: Se envía el payload.
        Then: El servicio debe enviar los caracteres tal cual; Telegram se encargará de procesarlos según su soporte de HTML.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        nombre_especial = "J&S > M"
        
        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=1, nombre_hermano=nombre_especial, nombre_acto="Acto", estado="ASIGNADA"
        )

        kwargs = mock_post.call_args[1]
        self.assertIn(nombre_especial, kwargs['json']['text'])



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_verificar_que_no_se_lanza_excepcion_hacia_fuera(self, mock_settings, mock_post):
        """
        Test: Verificar que no se lanza excepción hacia fuera (captura interna)

        Given: Un fallo crítico en la librería requests.
        When: Se invoca la función de notificación.
        Then: Gracias al bloque try/except interno, la excepción no debe subir al nivel superior, evitando romper procesos masivos de reparto.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        mock_post.side_effect = RuntimeError("Fallo de memoria")

        try:
            TelegramWebhookService.notificar_papeleta_asignada(1, "H", "A", "ASIGNADA")
        except RuntimeError:
            self.fail("notificar_papeleta_asignada() permitió que la excepción escapara")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_verificar_que_no_se_llama_a_requests_si_falta_token_o_chat_id(self, mock_settings, mock_post):
        """
        Test: Verificar que no se llama a requests.post si falta token o chat_id

        Given: Una combinación de datos incompleta (sin chat_id).
        When: Se evalúa el guard clause (if not token or not chat_id).
        Then: No se debe realizar ninguna petición HTTP.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"

        TelegramWebhookService.notificar_papeleta_asignada(
            chat_id=None, nombre_hermano="H", nombre_acto="A", estado="ASIGNADA"
        )

        mock_post.assert_not_called()