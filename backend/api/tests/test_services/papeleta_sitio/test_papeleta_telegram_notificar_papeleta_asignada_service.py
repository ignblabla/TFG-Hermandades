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