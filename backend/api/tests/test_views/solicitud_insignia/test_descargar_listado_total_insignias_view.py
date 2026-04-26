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
    def test_genera_pdf_correctamente_retorna_200(self, mock_get_object, mock_service_class):
        """
        Test: Genera PDF correctamente → 200

        Given: Un acto válido y un servicio que devuelve correctamente el buffer del catálogo completo.
        When: Se realiza la petición GET para descargar el documento.
        Then: La vista retorna status 200, el content_type adecuado y los bytes exactos generados por el servicio.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock()
        mock_acto.id = 1
        mock_get_object.return_value = mock_acto

        contenido_catalogo = b"%PDF-1.4 Catalogo Completo de Insignias"
        mock_buffer = BytesIO(contenido_catalogo)
        mock_service_class.generar_pdf_todas_insignias.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(
            response['Content-Disposition'], 
            'attachment; filename="catalogo_insignias_1.pdf"'
        )

        self.assertEqual(response.content, contenido_catalogo)

        mock_service_class.generar_pdf_todas_insignias.assert_called_once_with(mock_acto)

        self.assertTrue(mock_buffer.closed)



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_header_correcto_filename_catalogo(self, mock_get_object, mock_service_class):
        """
        Test: Header correcto (clave aquí)

        Given: Un acto con un ID específico (por ejemplo, 100).
        When: Se genera la respuesta de descarga para el catálogo completo.
        Then: La cabecera Content-Disposition debe seguir el patrón "catalogo_insignias_100.pdf".
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock()
        mock_acto.id = 100
        mock_get_object.return_value = mock_acto

        mock_service_class.generar_pdf_todas_insignias.return_value = BytesIO(b"data")

        response = self.view(request, pk=100)

        header_esperado = 'attachment; filename="catalogo_insignias_100.pdf"'
        self.assertEqual(response['Content-Disposition'], header_esperado)



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_llamada_correcta_al_servicio_todas_insignias(self, mock_get_object, mock_service_class):
        """
        Test: Llamada correcta al servicio

        Given: Un objeto acto recuperado exitosamente.
        When: Se ejecuta el método GET de la vista.
        Then: Se debe llamar específicamente a 'generar_pdf_todas_insignias' con el objeto acto.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        acto_mock = MagicMock()
        mock_get_object.return_value = acto_mock
        
        mock_service_class.generar_pdf_todas_insignias.return_value = BytesIO(b"data")

        self.view(request, pk=1)

        mock_service_class.generar_pdf_todas_insignias.assert_called_once_with(acto_mock)



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_buffer_se_cierra_tras_generar_catalogo(self, mock_get_object, mock_service_class):
        """
        Test: Buffer se cierra

        Given: Una generación exitosa del catálogo de insignias.
        When: La vista ha terminado de leer los datos para el HttpResponse.
        Then: Se debe llamar al método .close() del buffer para liberar la memoria asignada.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"%PDF-1.4 catalogo"
        
        mock_service_class.generar_pdf_todas_insignias.return_value = mock_buffer

        self.view(request, pk=1)

        mock_buffer.close.assert_called_once()



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_object):
        """
        Test: Acto no existe → 404

        Given: Un identificador de acto que no existe en la base de datos.
        When: Se llama a la vista y get_object_or_404 lanza Http404.
        Then: La vista debe retornar un status 404 Not Found.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_get_object.side_effect = Http404

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        mock_get_object.assert_called_once_with(ANY, pk=1)



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_error_en_generacion_retorna_500_con_json_detalle(self, mock_get_object, mock_service_class):
        """
        Test: Error en generación → 500

        Given: Un acto válido pero un fallo inesperado en el servicio al generar el catálogo.
        When: El servicio lanza una excepción genérica.
        Then: La vista debe capturarla, devolver status 500 y un JSON con el mensaje descriptivo.
        """
        request = self.factory.get(self.url, format='json')
        force_authenticate(request, user=MagicMock())
        
        mock_get_object.return_value = MagicMock(id=1)

        mensaje_error = "Error al renderizar imágenes del catálogo"
        mock_service_class.generar_pdf_todas_insignias.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=1)
        response.render()

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.assertEqual(response.data["error"], "Error al generar el catálogo de insignias")
        self.assertEqual(response.data["detalle"], mensaje_error)

        self.assertEqual(response['Content-Type'], 'application/json')



    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_todas_insignias_view.get_object_or_404')
    def test_buffer_vacio_sigue_devolviendo_respuesta_valida(self, mock_get_object, mock_service_class):
        """
        Test: Buffer vacío

        Given: Un acto válido pero un servicio que devuelve un buffer de BytesIO sin contenido.
        When: La vista intenta generar la respuesta de descarga.
        Then: La vista debe responder con status 200 y un cuerpo de respuesta vacío (b''), 
            asegurando que el buffer se cierre correctamente.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_buffer = BytesIO() 
        mock_service_class.generar_pdf_todas_insignias.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.content, b"")

        self.assertEqual(response['Content-Type'], 'application/pdf')

        self.assertTrue(mock_buffer.closed)