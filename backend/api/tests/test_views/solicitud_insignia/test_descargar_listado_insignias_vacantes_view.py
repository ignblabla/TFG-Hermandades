from unittest.mock import ANY, patch, MagicMock
from io import BytesIO
from django.http import Http404
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view import DescargarListadoVacantesView


class TestDescargarListadoVacantesView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = DescargarListadoVacantesView.as_view()
        self.url = '/actos/1/descargar-listado-vacantes/'



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_descarga_pdf_vacantes_exitosamente_200(self, mock_get_404, mock_service_class):
        """
        Test: Genera PDF correctamente → 200

        Given: Un acto válido y un servicio que devuelve un buffer con el listado de vacantes.
        When: Se procesa una petición GET para descargar las vacantes.
        Then: La vista retorna status 200, los bytes exactos, el content_type adecuado, los headers correctos y cierra el buffer.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=1)
        mock_get_404.return_value = mock_acto

        contenido_falso_pdf = b"%PDF-1.4 Documento de vacantes"
        mock_buffer = MagicMock(spec=BytesIO) 
        mock_buffer.getvalue.return_value = contenido_falso_pdf
        mock_service_class.generar_pdf_vacantes.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, contenido_falso_pdf)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="insignias_vacantes_1.pdf"')
        
        mock_service_class.generar_pdf_vacantes.assert_called_once_with(mock_acto)
        mock_buffer.close.assert_called_once()



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_error_generando_pdf_retorna_500(self, mock_get_404, mock_service_class):
        """
        Test: Error generando PDF → 500

        Given: Un acto válido pero un fallo inesperado en el motor de generación de informes.
        When: El servicio lanza una excepción genérica.
        Then: La vista debe capturarla, retornar status 500 y un JSON con el mensaje de error específico.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.return_value = MagicMock(id=1)

        mensaje_error = "Error al conectar con el motor de informes"
        mock_service_class.generar_pdf_vacantes.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error al generar el documento de vacantes")
        self.assertEqual(response.data["detalle"], mensaje_error)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_404):
        """
        Test: Acto no existe → 404

        Given: Un identificador de acto que no se encuentra en la base de datos.
        When: Se intenta acceder a la descarga de vacantes.
        Then: La vista debe propagar la excepción Http404 y retornar un status 404.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.side_effect = Http404

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado (401/403)
        
        Given: Un usuario anónimo intentando descargar el listado.
        When: Se realiza la petición GET.
        Then: La clase IsAuthenticated bloquea el acceso devolviendo 401 o 403.
        """
        request = self.factory.get(self.url)

        response = self.view(request, pk=1)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])