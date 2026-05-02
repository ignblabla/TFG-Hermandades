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



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    def test_asigna_correctamente_telegram_chat_id(self, mock_base64, mock_signer, mock_user):
        """
        Test: Asigna correctamente telegram_chat_id

        Given: Un usuario mock y un chat_id proveniente de Telegram.
        When: Se procesa el comando /start con un token válido.
        Then: El atributo telegram_chat_id del usuario debe actualizarse con el ID del chat en formato string.
        """
        chat_id = 998877
        data = {'message': {'chat': {'id': chat_id}, 'text': '/start token'}}
        
        mock_hermano = MagicMock()
        mock_user.objects.get.return_value = mock_hermano

        mock_base64.urlsafe_b64decode.return_value = b'1'
        mock_signer.return_value.unsign.return_value = 1

        TelegramWebhookService.procesar_actualizacion(data)

        self.assertEqual(mock_hermano.telegram_chat_id, str(chat_id))
        mock_hermano.save.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.TelegramWebhookService._enviar_bienvenida')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    def test_llama_a_enviar_bienvenida_con_datos_correctos(self, mock_base64, mock_signer, mock_user, mock_bienvenida):
        """
        Test: Llama a _enviar_bienvenida con datos correctos

        Given: Un usuario encontrado llamado "Test User" y un chat_id 123.
        When: La vinculación se completa exitosamente tras decodificar el token.
        Then: Se debe invocar el método privado _enviar_bienvenida con el chat_id y el nombre del hermano.
        """
        chat_id = 123
        mock_hermano = MagicMock()
        mock_hermano.nombre = "Test User"
        mock_user.objects.get.return_value = mock_hermano

        mock_base64.urlsafe_b64decode.return_value = b"token_decodificado"
        mock_signer.return_value.unsign.return_value = 1
        
        data = {'message': {'chat': {'id': chat_id}, 'text': '/start valid_token'}}

        TelegramWebhookService.procesar_actualizacion(data)

        mock_bienvenida.assert_called_once_with(chat_id, "Test User")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    def test_decodifica_correctamente_el_token_base64(self, mock_base64):
        """
        Test: Decodifica correctamente el token base64

        Given: Un token en el mensaje de texto "/start mytoken".
        When: Se procesa la actualización.
        Then: Se debe llamar a urlsafe_b64decode añadiendo el padding necesario y codificando a bytes.
        """
        token_input = "abc"
        data = {'message': {'chat': {'id': 1}, 'text': f'/start {token_input}'}}
        
        TelegramWebhookService.procesar_actualizacion(data)

        mock_base64.urlsafe_b64decode.assert_called_once_with(b"abc=")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    def test_usa_correctamente_signer_unsign(self, mock_signer_class):
        """
        Test: Usa correctamente Signer.unsign

        Given: Un token decodificado "decoded_val".
        When: Se intenta extraer el ID del usuario.
        Then: Se debe instanciar Signer y llamar al método unsign con el valor decodificado.
        """
        mock_signer_instancia = mock_signer_class.return_value
        data = {'message': {'chat': {'id': 1}, 'text': '/start token'}}

        with patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64.urlsafe_b64decode') as mock_b64:
            mock_b64.return_value = b"decoded_val"
            TelegramWebhookService.procesar_actualizacion(data)

        mock_signer_instancia.unsign.assert_called_once_with("decoded_val")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.TelegramWebhookService._enviar_bienvenida')
    def test_guarda_el_usuario_tras_asignar_el_chat_id(self, mock_bienvenida, mock_base64, mock_signer, mock_user_model):
        """
        Test: Guarda el usuario tras asignar el chat_id

        Given: Un usuario (hermano) recuperado de la base de datos mediante su ID.
        When: Se recibe un chat_id válido de Telegram.
        Then: Se debe asignar el chat_id al atributo telegram_chat_id y llamar al método save() del modelo.
        """
        chat_id_telegram = 555444
        data = {
            'message': {
                'chat': {'id': chat_id_telegram},
                'text': '/start token_valido'
            }
        }

        mock_hermano = MagicMock()
        mock_user_model.objects.get.return_value = mock_hermano

        mock_base64.urlsafe_b64decode.return_value = b"decoded"
        mock_signer.return_value.unsign.return_value = 1

        TelegramWebhookService.procesar_actualizacion(data)

        self.assertEqual(mock_hermano.telegram_chat_id, str(chat_id_telegram))

        mock_hermano.save.assert_called_once()

        mock_user_model.objects.get.assert_called_once_with(id=1)



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



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.print')
    def test_no_hay_text_en_el_mensaje(self, mock_print):
        """
        Test: No hay text en el mensaje

        Given: Un mensaje de Telegram que no contiene texto (por ejemplo, el envío de una foto o contacto).
        When: Se accede a la clave 'text'.
        Then: Se debe obtener un string vacío por defecto y la ejecución debe terminar pacíficamente sin procesar nada.
        """
        data_sin_texto = {
            'message': {
                'chat': {'id': 1},
                'photo': [...]
            }
        }

        TelegramWebhookService.procesar_actualizacion(data_sin_texto)
        
        mock_print.assert_not_called()



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
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    def test_token_mal_formado_error_base64(self, mock_base64, mock_print):
        """
        Test: Token mal formado (error en base64)

        Given: Un token que no puede ser decodificado por base64.
        When: Se intenta realizar el urlsafe_b64decode.
        Then: Se captura el ValueError y se imprime el error por consola sin detener la ejecución.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token_invalido'}}
        mock_base64.urlsafe_b64decode.side_effect = ValueError("Invalid base64")

        TelegramWebhookService.procesar_actualizacion(data)

        mock_print.assert_called_with("Intento de vinculación fallido. Error: Invalid base64")



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



    @patch('builtins.print') 
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    def test_error_al_guardar_el_usuario(self, mock_signer, mock_user_model, mock_print):
        """
        Test: Error al guardar el usuario

        Given: Un usuario recuperado correctamente cuya actualización de chat_id falla.
        When: Se invoca al método save() del modelo User.
        Then: Se captura la excepción general en el bloque try/except externo y se imprime el error procesando el webhook.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token_valido'}}
        
        mock_hermano = MagicMock()
        mensaje_error = "Error de escritura en disco"
        mock_hermano.save.side_effect = Exception(mensaje_error)

        mock_user_model.objects.get.return_value = mock_hermano
        mock_signer.return_value.unsign.return_value = 1

        mock_user_model.DoesNotExist = type('DoesNotExist', (Exception,), {})

        with patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64.urlsafe_b64decode') as mock_b64:
            mock_b64.return_value = b"decoded"
            TelegramWebhookService.procesar_actualizacion(data)

        mock_print.assert_called_with(f"Error procesando webhook de Telegram: {mensaje_error}")



    @patch('builtins.print')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.TelegramWebhookService._enviar_bienvenida')
    def test_error_en_enviar_bienvenida(self, mock_bienvenida, mock_signer, mock_user_model, mock_print):
        """
        Test: Error en _enviar_bienvenida

        Given: Un proceso de vinculación exitoso hasta el paso final.
        When: El método privado _enviar_bienvenida lanza una excepción (ej. fallo de API de Telegram).
        Then: La excepción debe ser capturada por el bloque Exception externo y logueada correctamente.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token'}}
        mock_hermano = MagicMock(nombre="Test")
        mock_user_model.objects.get.return_value = mock_hermano
        mock_signer.return_value.unsign.return_value = 1

        mock_user_model.DoesNotExist = type('DoesNotExist', (Exception,), {})

        mensaje_error = "Error de red en API Telegram"
        mock_bienvenida.side_effect = Exception(mensaje_error)

        with patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64.urlsafe_b64decode') as mock_b64:
            mock_b64.return_value = b"decoded"
            TelegramWebhookService.procesar_actualizacion(data)

        mock_print.assert_called_with(f"Error procesando webhook de Telegram: {mensaje_error}")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    def test_chat_id_es_none(self, mock_signer, mock_user_model):
        """
        Test: chat_id es None

        Given: Un payload donde el chat_id no viene informado.
        When: Se intenta asignar telegram_chat_id al hermano.
        Then: Se debe guardar el valor como string 'None' sin romper la ejecución.
        """
        data = {'message': {'chat': {}, 'text': '/start token'}}
        
        mock_hermano = MagicMock()
        mock_user_model.objects.get.return_value = mock_hermano
        mock_signer.return_value.unsign.return_value = 1
        
        with patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64.urlsafe_b64decode') as mock_b64:
            mock_b64.return_value = b"decoded"
            TelegramWebhookService.procesar_actualizacion(data)

        self.assertEqual(mock_hermano.telegram_chat_id, "None")
        mock_hermano.save.assert_called_once()



    @patch('builtins.print')
    def test_token_sin_parte_despues_de_start(self, mock_print):
        """
        Test: Token sin parte después de /start

        Given: Un mensaje que contiene exactamente "/start " pero sin el token.
        When: Se intenta procesar, lo que resulta en un token vacío que llega hasta el Signer.
        Then: Signer.unsign lanzará BadSignature al no encontrar la firma, capturándose en el bloque interno.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start '}}

        TelegramWebhookService.procesar_actualizacion(data)

        mock_print.assert_called_with('Intento de vinculación fallido. Error: No ":" found in value')



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    def test_token_con_padding_incorrecto(self, mock_signer, mock_base64):
        """
        Test: Token con padding incorrecto

        Given: Un token cuya longitud no permite un padding válido.
        When: Se intenta decodificar con base64.urlsafe_b64decode.
        Then: La excepción ValueError/binascii.Error debe ser capturada en el bloque interno.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token_corrupto'}}
        mock_base64.urlsafe_b64decode.side_effect = ValueError("Incorrect padding")

        try:
            TelegramWebhookService.procesar_actualizacion(data)
        except ValueError:
            self.fail("procesar_actualizacion() lanzó ValueError inesperadamente")



    @patch('builtins.print')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    def test_signer_unsign_devuelve_valor_no_esperado(self, mock_signer, mock_user_model, mock_print):
        """
        Test: Signer.unsign devuelve valor no esperado (no convertible a id)

        Given: Un token firmado que al descifrarse devuelve un valor no numérico (ej: un string aleatorio).
        When: Se intenta buscar el usuario mediante User.objects.get(id=...).
        Then: Django lanzará un ValueError/TypeError que debe ser capturado por el bloque de excepción interno.
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token_raro'}}
        mock_signer.return_value.unsign.return_value = "no-soy-un-id"

        mock_user_model.DoesNotExist = type('DoesNotExist', (Exception,), {})

        mock_user_model.objects.get.side_effect = ValueError("invalid literal for int()")
        
        with patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64.urlsafe_b64decode') as mock_b64:
            mock_b64.return_value = b"decoded"
            TelegramWebhookService.procesar_actualizacion(data)

        mock_print.assert_called_with("Intento de vinculación fallido. Error: invalid literal for int()")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.TelegramWebhookService._enviar_bienvenida')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.User')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.Signer')
    def test_user_get_devuelve_objeto_sin_nombre(self, mock_signer, mock_user_model, mock_bienvenida):
        """
        Test: User.objects.get devuelve objeto sin nombre

        Given: Un usuario que existe pero tiene el campo nombre como None o vacío.
        When: Se llama a _enviar_bienvenida.
        Then: El servicio debe continuar y enviar el mensaje con el valor tal cual (o None).
        """
        data = {'message': {'chat': {'id': 1}, 'text': '/start token'}}
        mock_hermano = MagicMock()
        mock_hermano.nombre = None
        mock_user_model.objects.get.return_value = mock_hermano
        mock_signer.return_value.unsign.return_value = 1

        with patch('api.servicios.papeleta_sitio.papeleta_telegram_service.base64.urlsafe_b64decode') as mock_b64:
            mock_b64.return_value = b"dec"
            TelegramWebhookService.procesar_actualizacion(data)

        mock_bienvenida.assert_called_once_with(1, None)



    @patch('builtins.print')
    def test_excepcion_generica_en_bloque_externo(self, mock_print):
        """
        Test: Excepción genérica en el bloque externo

        Given: Un payload que causa un error antes de entrar al bloque try interno (ej: data es None).
        When: Se intenta ejecutar data.get().
        Then: El AttributeError debe ser capturado por el bloque except Exception externo.
        """
        data_nula = None 

        TelegramWebhookService.procesar_actualizacion(data_nula)

        args, _ = mock_print.call_args
        self.assertIn("Error procesando webhook de Telegram", args[0])



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