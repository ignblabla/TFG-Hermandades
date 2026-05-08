from unittest.mock import ANY, patch, MagicMock
from io import BytesIO
from django.http import Http404
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view import DescargarListadoTodasInsigniasView


class TestDescargarListadoTodasInsigniasView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = DescargarListadoTodasInsigniasView.as_view()
        self.url = '/actos/1/descargar-todas-insignias/'



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_descarga_pdf_exitosamente_200(self, mock_get_404, mock_service_class):
        """
        Test: Genera PDF correctamente → 200

        Given: Un acto válido y un servicio que devuelve correctamente el buffer del catálogo completo.
        When: Se realiza la petición GET para descargar el documento.
        Then: La vista retorna status 200, los bytes exactos, el content_type adecuado, los headers correctos y cierra el buffer.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=1)
        mock_get_404.return_value = mock_acto

        contenido_catalogo = b"%PDF-1.4 Catalogo Completo de Insignias"
        mock_buffer = MagicMock(spec=BytesIO)
        mock_buffer.getvalue.return_value = contenido_catalogo
        mock_service_class.generar_pdf_todas_insignias.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, contenido_catalogo)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="catalogo_insignias_1.pdf"')
        
        mock_service_class.generar_pdf_todas_insignias.assert_called_once_with(mock_acto)
        mock_buffer.close.assert_called_once()



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_error_en_generacion_pdf_retorna_500(self, mock_get_404, mock_service_class):
        """
        Test: Error en generación → 500

        Given: Un acto válido pero un fallo inesperado en el servicio al generar el catálogo.
        When: El servicio lanza una excepción genérica.
        Then: La vista debe capturarla, devolver status 500 y un JSON con el mensaje descriptivo.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.return_value = MagicMock(id=1)

        mensaje_error = "Error al renderizar imágenes del catálogo"
        mock_service_class.generar_pdf_todas_insignias.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error al generar el catálogo de insignias")
        self.assertEqual(response.data["detalle"], mensaje_error)



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_404):
        """
        Test: Acto no existe → 404

        Given: Un identificador de acto que no existe en la base de datos.
        When: Se llama a la vista y get_object_or_404 lanza Http404.
        Then: La vista debe retornar un status 404 Not Found.
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