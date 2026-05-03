import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
from django.http import FileResponse
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.comunicado.chat_comunicados_view import ChatComunicadosView


class TestChatComunicadosValidacion(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ChatComunicadosView.as_view()
        self.path = "/api/comunicados/chat/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    def test_no_envia_pregunta_devuelve_400(self):
        """
        Test: No envía pregunta
        
        Given: Un usuario autenticado que realiza una petición POST con un payload vacío.
        When: La vista procesa la solicitud y valida el campo 'pregunta'.
        Then: La ejecución se detiene y se retorna un status 400 BAD REQUEST con 
            un mensaje indicando que el campo es obligatorio.
        """
        payload = {}
        request = self.factory.post(self.path, data=payload, format='json')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.data['detail'], 
            "Debes enviar una pregunta válida en el campo 'pregunta'."
        )



    def test_pregunta_vacia_devuelve_400(self):
        """
        Test: pregunta vacía
        
        Given: Un usuario enviando el campo 'pregunta' como una cadena vacía.
        When: La vista valida el contenido de la petición.
        Then: Se retorna un status 400 ya que la pregunta no es válida.
        """
        request = self.factory.post(self.path, data={"pregunta": ""}, format='json')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    def test_pregunta_solo_espacios_devuelve_400(self):
        """
        Test: pregunta solo espacios
        
        Given: Un usuario enviando una cadena compuesta únicamente por espacios en blanco.
        When: La vista aplica el strip() a la entrada.
        Then: Se retorna un status 400 al considerarse una pregunta vacía.
        """
        request = self.factory.post(self.path, data={"pregunta": "   "}, format='json')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    def test_pregunta_normal_flujo_ia_exitoso(self, mock_rag_class):
        """
        Test: Pregunta normal -> flujo IA
        
        Given: Una pregunta válida que no contiene palabras clave de descarga de archivos.
        When: Se invoca al servicio ComunicadoRAGService.
        Then: Se retorna status 200 y la respuesta generada por la IA.
        """
        request = self.factory.post(self.path, data={"pregunta": "¿Cuándo es el cabildo?"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_service_instance = mock_rag_class.return_value
        mock_service_instance.preguntar_a_comunicados.return_value = "respuesta IA"

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"respuesta": "respuesta IA"})
        mock_service_instance.preguntar_a_comunicados.assert_called_once_with("¿Cuándo es el cabildo?")



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    def test_se_llama_correctamente_al_servicio_ia(self, mock_rag_class):
        """
        Test: Se llama correctamente al servicio IA
        
        Given: Una pregunta válida enviada por el usuario.
        When: La vista procesa el POST y no detecta palabras clave de archivos.
        Then: Se instancia el servicio RAG y se llama a preguntar_a_comunicados 
            exactamente con el texto de la pregunta.
        """
        pregunta = "¿Cuál es el horario de la secretaría?"
        request = self.factory.post(self.path, data={"pregunta": pregunta}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_service_instance = mock_rag_class.return_value

        self.view(request)

        mock_service_instance.preguntar_a_comunicados.assert_called_once_with(pregunta)



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    def test_servicio_ia_lanza_excepcion_devuelve_500(self, mock_rag_class):
        """
        Test: Servicio IA lanza excepción
        
        Given: Una consulta que provoca un error inesperado en el servicio RAG.
        When: El servicio lanza una excepción durante el procesamiento.
        Then: La vista captura el error y retorna un status 500 con el detalle del fallo.
        """
        request = self.factory.post(self.path, data={"pregunta": "test error"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_rag_class.return_value.preguntar_a_comunicados.side_effect = Exception("fallo IA")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Ocurrió un error interno", response.data['detail'])
        self.assertEqual(response.data['error'], "fallo IA")



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    @patch("api.vistas.comunicado.chat_comunicados_view.open", new_callable=mock_open, read_data=b"pdf_content")
    def test_pregunta_contiene_programa_descarga_pdf(self, m_open, m_exists, mock_rag_class):
        """
        Test: Pregunta contiene "programa" -> descarga PDF
        
        Given: Una pregunta que incluye la palabra clave "programa".
        When: El archivo PDF existe físicamente en el servidor.
        Then: Se retorna un FileResponse con el archivo y NO se llega a invocar al servicio de IA.
        """
        request = self.factory.post(self.path, data={"pregunta": "Quiero el programa"}, format='json')
        force_authenticate(request, user=self.mock_user)

        m_exists.return_value = True

        response = self.view(request)

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="horarios.pdf"')

        mock_rag_class.assert_not_called()



    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    @patch("api.vistas.comunicado.chat_comunicados_view.open", new_callable=mock_open, read_data=b"llamador_content")
    def test_pregunta_contiene_llamador_descarga_pdf(self, m_open, m_exists):
        """
        Test: Pregunta contiene "llamador" -> descarga PDF
        
        Given: Una pregunta que incluye la palabra clave "llamador".
        When: El sistema verifica las palabras clave para decidir entre IA o descarga.
        Then: Al detectar "llamador", se intenta abrir el archivo horarios.pdf y 
            se retorna como un FileResponse.
        """
        request = self.factory.post(self.path, data={"pregunta": "Dame el llamador"}, format='json')
        force_authenticate(request, user=self.mock_user)
        m_exists.return_value = True

        response = self.view(request)

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="horarios.pdf"')



    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    def test_pdf_no_existe_devuelve_404(self, m_exists):
        """
        Test: PDF no existe
        
        Given: Una pregunta válida para descarga ("programa"), pero el archivo físico no está en el servidor.
        When: os.path.exists retorna False.
        Then: La vista retorna un status 404 con un mensaje indicando que el programa 
            aún no está disponible.
        """
        request = self.factory.post(self.path, data={"pregunta": "Descargar programa"}, format='json')
        force_authenticate(request, user=self.mock_user)

        m_exists.return_value = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(
            response.data['detail'], 
            "El programa de mano aún no está disponible para su descarga en el servidor."
        )



    @patch("api.vistas.comunicado.chat_comunicados_view.settings")
    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    def test_verifica_ruta_del_archivo_construida_correctamente(self, m_exists, m_settings):
        """
        Test: Verifica ruta del archivo construida correctamente
        
        Given: Un MEDIA_ROOT específico definido en la configuración.
        When: Se solicita la descarga de un archivo.
        Then: Se valida que la vista construya la ruta uniendo el MEDIA_ROOT con 
            la subcarpeta 'documentos' y el nombre del archivo 'horarios.pdf'.
        """
        request = self.factory.post(self.path, data={"pregunta": "programa"}, format='json')
        force_authenticate(request, user=self.mock_user)

        m_settings.MEDIA_ROOT = "/fake/media"
        m_exists.return_value = False
        
        ruta_esperada = os.path.join("/fake/media", "documentos", "horarios.pdf")

        self.view(request)

        m_exists.assert_called_once_with(ruta_esperada)



    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    @patch("api.vistas.comunicado.chat_comunicados_view.open", side_effect=Exception("file error"))
    def test_open_lanza_excepcion_no_capturada(self, m_open, m_exists):
        """
        Test: open lanza excepción
        
        Given: Una pregunta que solicita el "programa" y un archivo que existe en el disco.
        When: El sistema intenta abrir el archivo con open() pero ocurre un error de permisos o acceso.
        Then: La vista no captura esta excepción específica de I/O, por lo que el test 
            debe esperar que la excepción se propague, revelando un bug potencial de robustez.
        """
        request = self.factory.post(self.path, data={"pregunta": "programa"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        m_exists.return_value = True

        with self.assertRaises(Exception) as context:
            self.view(request)
        
        self.assertEqual(str(context.exception), "file error")



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    @patch("api.vistas.comunicado.chat_comunicados_view.open", new_callable=mock_open, read_data=b"data")
    def test_no_llama_al_servicio_ia_si_entra_en_rama_de_pdf(self, m_open, m_exists, mock_rag_class):
        """
        Test: No llama al servicio IA si entra en rama de PDF
        
        Given: Una pregunta que contiene la palabra clave "programa".
        When: La vista identifica la intención de descarga y encuentra el archivo.
        Then: Se retorna el archivo PDF y se verifica que el servicio de IA (RAG) 
            no sea instanciado ni utilizado, ahorrando recursos y tokens.
        """
        request = self.factory.post(self.path, data={"pregunta": "quiero el programa"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        m_exists.return_value = True

        self.view(request)

        mock_rag_class.assert_not_called()