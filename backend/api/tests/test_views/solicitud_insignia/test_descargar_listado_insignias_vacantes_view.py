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
    def test_genera_pdf_correctamente_retorna_200(self, mock_get_object, mock_service_class):
        """
        Test: Genera PDF correctamente → 200

        Given: Un acto válido y un servicio que devuelve un buffer con el listado de vacantes.
        When: Se procesa una petición GET para descargar las vacantes.
        Then: La vista debe retornar un status 200, el content_type application/pdf y el contenido exacto del buffer.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock()
        mock_acto.id = 1
        mock_get_object.return_value = mock_acto

        contenido_falso_pdf = b"%PDF-1.4 Documento de vacantes"
        mock_buffer = BytesIO(contenido_falso_pdf)
        mock_service_class.generar_pdf_vacantes.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        self.assertEqual(
            response['Content-Disposition'], 
            'attachment; filename="insignias_vacantes_1.pdf"'
        )

        self.assertEqual(response.content, contenido_falso_pdf)

        mock_service_class.generar_pdf_vacantes.assert_called_once_with(mock_acto)
        self.assertTrue(mock_buffer.closed)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_header_correcto_content_disposition(self, mock_get_object, mock_service_class):
        """
        Test: Header correcto

        Given: Un acto con un ID específico (por ejemplo, 42).
        When: Se procesa la descarga del listado de vacantes.
        Then: La respuesta debe incluir el header Content-Disposition con el formato y nombre de archivo correctos.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock()
        mock_acto.id = 42
        mock_get_object.return_value = mock_acto

        mock_service_class.generar_pdf_vacantes.return_value = BytesIO(b"dummy")

        response = self.view(request, pk=42)

        header_esperado = 'attachment; filename="insignias_vacantes_42.pdf"'
        self.assertEqual(response['Content-Disposition'], header_esperado)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_llamada_correcta_al_servicio(self, mock_get_object, mock_service_class):
        """
        Test: Llamada correcta al servicio

        Given: Un objeto acto recuperado exitosamente por get_object_or_404.
        When: Se delega la lógica de negocio al servicio.
        Then: El método generar_pdf_vacantes debe ser invocado pasándole exactamente la instancia del acto recuperada.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        acto_de_bd = MagicMock()
        mock_get_object.return_value = acto_de_bd

        mock_service_class.generar_pdf_vacantes.return_value = BytesIO(b"dummy")

        self.view(request, pk=1)

        mock_service_class.generar_pdf_vacantes.assert_called_once_with(acto_de_bd)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_buffer_se_cierra_despues_de_la_respuesta(self, mock_get_object, mock_service_class):
        """
        Test: Buffer se cierra

        Given: Una generación de PDF de vacantes exitosa.
        When: La vista termina de construir la respuesta HTTP.
        Then: Se debe invocar el método .close() del buffer devuelto por el servicio para liberar recursos.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"%PDF-1.4 vacantes"
        
        mock_service_class.generar_pdf_vacantes.return_value = mock_buffer

        self.view(request, pk=1)

        mock_buffer.close.assert_called_once()



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_object):
        """
        Test: Acto no existe → 404

        Given: Un identificador de acto que no se encuentra en la base de datos.
        When: Se intenta acceder a la descarga de vacantes.
        Then: La vista debe propagar la excepción Http404 y retornar un status 404.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_get_object.side_effect = Http404

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_get_object.assert_called_once_with(ANY, pk=1)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_error_generando_pdf_retorna_500_con_detalle(self, mock_get_object, mock_service_class):
        """
        Test: Error generando PDF → 500

        Given: Un acto válido pero un fallo inesperado en el motor de generación de informes.
        When: El servicio lanza una excepción genérica.
        Then: La vista debe capturarla, retornar status 500 y un JSON con el mensaje de error específico.
        """
        request = self.factory.get(self.url, format='json')
        force_authenticate(request, user=MagicMock())
        
        mock_get_object.return_value = MagicMock(id=1)

        mensaje_error = "Error al conectar con el motor de informes"
        mock_service_class.generar_pdf_vacantes.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=1)
        response.render()

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error al generar el documento de vacantes")
        self.assertEqual(response.data["detalle"], mensaje_error)
        self.assertEqual(response['Content-Type'], 'application/json')



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_vacantes_view.get_object_or_404')
    def test_buffer_vacio_sigue_devolviendo_pdf(self, mock_get_object, mock_service_class):
        """
        Test: Buffer vacío

        Given: Un acto válido pero un servicio que, por un error lógico, devuelve un buffer de BytesIO vacío.
        When: Se genera la HttpResponse.
        Then: La vista debe procesar el buffer sin explotar, devolviendo un contenido vacío (b'') con status 200 y el content_type correcto.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_buffer = BytesIO() 
        mock_service_class.generar_pdf_vacantes.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.content, b"")

        self.assertEqual(response['Content-Type'], 'application/pdf')

        self.assertTrue(mock_buffer.closed)