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



    def test_post_pregunta_invalida_retorna_400(self):
        """
        Test: Validaciones de pregunta (Vacía, Nula o Espacios)
        
        Given: Peticiones POST con payloads inválidos para 'pregunta'.
        When: La vista ejecuta la validación inicial (strip).
        Then: La ejecución se detiene y se retorna un status 400 BAD REQUEST.
        """
        casos_invalidos = [
            {},
            {"pregunta": ""},
            {"pregunta": "   "}
        ]

        for payload in casos_invalidos:
            with self.subTest(payload=payload):
                request = self.factory.post(self.path, data=payload, format='json')
                force_authenticate(request, user=self.mock_user)

                response = self.view(request)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(
                    response.data['detail'], 
                    "Debes enviar una pregunta válida en el campo 'pregunta'."
                )



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    @patch("api.vistas.comunicado.chat_comunicados_view.open", new_callable=mock_open, read_data=b"pdf_content")
    def test_post_descarga_pdf_exitoso(self, m_open, m_exists, mock_rag_class):
        """
        Test: Flujo de descarga de PDF exitoso (Rama 'programa' o 'llamador')
        
        Given: Una pregunta con palabras clave ("programa" o "llamador") y el archivo existe.
        When: La vista intercepta la petición.
        Then: Retorna el archivo mediante FileResponse y NUNCA llama al servicio IA.
        """
        request = self.factory.post(self.path, data={"pregunta": "Quiero el programa de la hermandad"}, format='json')
        force_authenticate(request, user=self.mock_user)

        m_exists.return_value = True

        response = self.view(request)

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="horarios.pdf"')

        mock_rag_class.assert_not_called()



    @patch("api.vistas.comunicado.chat_comunicados_view.os.path.exists")
    def test_post_pdf_no_existe_retorna_404(self, m_exists):
        """
        Test: PDF no existe en el servidor
        
        Given: Una pregunta válida para descarga, pero el archivo físico no está.
        When: os.path.exists retorna False.
        Then: La vista retorna un status 404 con un mensaje de no disponibilidad.
        """
        request = self.factory.post(self.path, data={"pregunta": "dame el llamador"}, format='json')
        force_authenticate(request, user=self.mock_user)

        m_exists.return_value = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data['detail'], 
            "El programa de mano aún no está disponible para su descarga en el servidor."
        )



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    def test_post_flujo_ia_exitoso(self, mock_rag_class):
        """
        Test: Flujo IA normal exitoso
        
        Given: Una pregunta válida que no activa la descarga de archivos.
        When: Se invoca al servicio ComunicadoRAGService.
        Then: Se llama al servicio correctamente y se retorna 200 con la respuesta generada.
        """
        pregunta = "¿Cuándo es el próximo cabildo?"
        request = self.factory.post(self.path, data={"pregunta": pregunta}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_service_instance = mock_rag_class.return_value
        mock_service_instance.preguntar_a_comunicados.return_value = "El cabildo es el viernes."

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"respuesta": "El cabildo es el viernes."})

        mock_service_instance.preguntar_a_comunicados.assert_called_once_with(pregunta)



    @patch("api.vistas.comunicado.chat_comunicados_view.ComunicadoRAGService")
    def test_post_servicio_ia_lanza_excepcion_retorna_500(self, mock_rag_class):
        """
        Test: Manejo de errores en servicio IA (try/except)
        
        Given: Una consulta que provoca un error en el servicio RAG.
        When: El bloque try/except captura la excepción.
        Then: Se retorna un status 500 INTERNAL SERVER ERROR con detalles del error.
        """
        request = self.factory.post(self.path, data={"pregunta": "¿Alguna novedad?"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_rag_class.return_value.preguntar_a_comunicados.side_effect = Exception("Fallo de conexión RAG")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Ocurrió un error interno", response.data['detail'])
        self.assertEqual(response.data['error'], "Fallo de conexión RAG")



    def test_post_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición HTTP POST sin credenciales.
        When: La petición intenta acceder a la vista.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso.
        """
        request = self.factory.post(self.path, data={"pregunta": "Hola"}, format='json')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])