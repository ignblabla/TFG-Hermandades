from unittest import TestCase
from unittest.mock import patch, MagicMock
from django.core.signing import BadSignature

import builtins

from api.servicios.papeleta_sitio.papeleta_telegram_service import TelegramWebhookService, User


class TestProcesarActualizacionWebhook(TestCase):

    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.TelegramWebhookService._enviar_bienvenida')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    def test_procesa_correctamente_start_con_token_valido(self, mock_base64, mock_signer_class, mock_user_model, mock_enviar_bienvenida):
        """
        Test: Procesa correctamente /start con token válido

        Given: Un payload de Telegram válido que contiene el comando /start seguido de un token de vinculación.
        When: Se procesa la actualización del webhook.
        Then: Se debe decodificar el token, verificar la firma, obtener al usuario, guardar su chat_id de Telegram y enviarle el mensaje de bienvenida.
        """
        chat_id_esperado = 123456789
        token_limpio = "mocktoken"

        data_webhook = {
            'message': {
                'chat': {'id': chat_id_esperado},
                'text': f'/start {token_limpio}'
            }
        }

        padding = 4 - (len(token_limpio) % 4)
        token_base64 = token_limpio + ("=" * padding)

        token_decodificado_esperado = "token_decodificado_mock"
        mock_base64.urlsafe_b64decode.return_value = token_decodificado_esperado.encode()

        mock_signer_instancia = mock_signer_class.return_value
        usuario_id_esperado = 1
        mock_signer_instancia.unsign.return_value = usuario_id_esperado

        mock_hermano = MagicMock()
        mock_hermano.nombre = "Juan"
        mock_user_model.objects.get.return_value = mock_hermano

        TelegramWebhookService.procesar_actualizacion(data_webhook)

        mock_base64.urlsafe_b64decode.assert_called_once_with(token_base64.encode())

        mock_signer_class.assert_called_once()
        mock_signer_instancia.unsign.assert_called_once_with(token_decodificado_esperado)

        mock_user_model.objects.get.assert_called_once_with(id=usuario_id_esperado)

        self.assertEqual(mock_hermano.telegram_chat_id, str(chat_id_esperado))
        mock_hermano.save.assert_called_once()

        mock_enviar_bienvenida.assert_called_once_with(chat_id_esperado, mock_hermano.nombre)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.print')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    def test_token_con_firma_invalida(self, mock_base64, mock_signer_class, mock_print):
        """
        Test: Token con firma inválida

        Given: Un token decodificado pero cuya firma de Django no es válida.
        When: Se ejecuta el método unsign del Signer.
        Then: Se captura BadSignature y se registra el intento fallido.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token_manipulado'}}
        mock_base64.urlsafe_b64decode.return_value = b"data"
        mock_signer_class.return_value.unsign.side_effect = BadSignature("Signature mismatch")

        TelegramWebhookService.procesar_actualizacion(data)

        mock_print.assert_called_with("Intento de vinculación fallido. Error: Signature mismatch")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.print')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    def test_usuario_no_existe(self, mock_signer, mock_user_model, mock_print):
        """
        Test: Usuario no existe

        Given: Un ID de usuario obtenido del token que no corresponde a ningún hermano.
        When: Se intenta recuperar el usuario con User.objects.get.
        Then: Se captura User.DoesNotExist y se informa del error de vinculación con el mensaje esperado.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token_valido'}}

        mock_signer.return_value.unsign.return_value = 999

        mensaje_error = "Usuario no encontrado"
        mock_user_model.DoesNotExist = User.DoesNotExist
        mock_user_model.objects.get.side_effect = User.DoesNotExist(mensaje_error)

        with patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64.urlsafe_b64decode') as mock_b64:
            mock_b64.return_value = b"decoded"
            TelegramWebhookService.procesar_actualizacion(data)

        mock_print.assert_called_with(f"Intento de vinculación fallido. Error: {mensaje_error}")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    def test_verificar_que_no_se_lanza_excepcion_hacia_fuera(self, mock_base64):
        """
        Test: Verificar que no se lanza excepción hacia fuera (todo se captura)

        Given: Una dependencia que lanza una excepción crítica no prevista.
        When: Se ejecuta el servicio.
        Then: El servicio debe capturarla internamente y no dejar que suba al framework (evitando errores 500 en el webhook).
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token'}}

        mock_base64.urlsafe_b64decode.side_effect = SystemError("Fallo crítico del sistema")

        try:
            TelegramWebhookService.procesar_actualizacion(data)
        except Exception as e:
            self.fail(f"El servicio permitió que la excepción {type(e).__name__} escapara")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.print')
    def test_text_no_empieza_por_start(self, mock_print):
        """
        Test: text no empieza por /start

        Given: Un mensaje de texto común que no es el comando de vinculación.
        When: Se valida si el texto comienza con '/start '.
        Then: El servicio debe ignorar el mensaje y no realizar ninguna acción de decodificación o búsqueda de usuario.
        """
        data_texto_comun = {
            'message': {
                'chat': {'id': 1},
                'text': 'Hola, ¿cómo puedo ver mi papeleta?'
            }
        }

        TelegramWebhookService.procesar_actualizacion(data_texto_comun)

        mock_print.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.print')
    def test_no_hay_message_en_el_payload(self, mock_print):
        """
        Test: No hay message en el payload

        Given: Un diccionario vacío o malformado que no contiene la clave 'message'.
        When: Se intenta procesar la actualización.
        Then: El servicio debe manejar la ausencia de la clave mediante .get() devolviendo un diccionario vacío y no debe lanzar ninguna excepción.
        """
        data_invalida = {'update_id': 12345}

        TelegramWebhookService.procesar_actualizacion(data_invalida)

        mock_print.assert_not_called()