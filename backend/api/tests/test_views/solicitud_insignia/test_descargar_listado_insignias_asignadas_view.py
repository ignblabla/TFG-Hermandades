from unittest.mock import ANY, patch, MagicMock
from io import BytesIO
from django.http import Http404
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view import DescargarListadoInsigniasView


class TestDescargarListadoInsigniasView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = DescargarListadoInsigniasView.as_view()
        self.url = '/actos/1/descargar-listado-insignias/'

    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_genera_pdf_correctamente_retorna_200(self, mock_get_object, mock_service_class):
        """
        Test: Genera PDF correctamente → 200

        Given: Un acto existente en base de datos.
        When: Se solicita la descarga del listado de insignias.
        Then: Se retorna una HttpResponse (200) con el contenido binario del PDF y el content_type adecuado.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock()
        mock_acto.id = 1
        mock_get_object.return_value = mock_acto

        contenido_pdf = b"%PDF-1.4 test content"
        mock_buffer = BytesIO(contenido_pdf)

        mock_service_class.generar_pdf_asignados.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="asignacion_insignias_1.pdf"', response['Content-Disposition'])

        self.assertEqual(response.content, contenido_pdf)

        self.assertTrue(mock_buffer.closed)

        mock_service_class.generar_pdf_asignados.assert_called_once_with(mock_acto)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_cabecera_content_disposition_correcta(self, mock_get_object, mock_service_class):
        """
        Test: Cabecera Content-Disposition correcta

        Given: Un acto con ID 42.
        When: Se genera la respuesta de descarga.
        Then: La cabecera Content-Disposition debe ser 'attachment' e incluir el nombre de archivo con el ID del acto.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock()
        mock_acto.id = 42
        mock_get_object.return_value = mock_acto

        mock_service_class.generar_pdf_asignados.return_value = BytesIO(b"dummy")

        response = self.view(request, pk=42)

        header_esperado = 'attachment; filename="asignacion_insignias_42.pdf"'
        self.assertEqual(response['Content-Disposition'], header_esperado)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_se_llama_al_servicio_con_el_acto_correcto(self, mock_get_object, mock_service_class):
        """
        Test: Se llama al servicio con el acto correcto

        Given: Un acto recuperado de la base de datos mediante get_object_or_404.
        When: La vista procesa la petición de descarga.
        Then: Se debe invocar al método generar_pdf_asignados pasando exactamente ese objeto acto.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        acto_de_bd = MagicMock()
        mock_get_object.return_value = acto_de_bd
        
        mock_service_class.generar_pdf_asignados.return_value = BytesIO(b"dummy")

        self.view(request, pk=1)

        mock_service_class.generar_pdf_asignados.assert_called_once_with(acto_de_bd)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_se_cierra_el_buffer_tras_generar_la_respuesta(self, mock_get_object, mock_service_class):
        """
        Test: Se cierra el buffer

        Given: Un proceso de generación de PDF exitoso.
        When: La vista termina de construir la HttpResponse.
        Then: Se debe llamar al método .close() del buffer para liberar los recursos de memoria.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_buffer = MagicMock()

        mock_buffer.getvalue.return_value = b"%PDF-1.4 mock content"
        
        mock_service_class.generar_pdf_asignados.return_value = mock_buffer

        self.view(request, pk=1)

        mock_buffer.close.assert_called_once()



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_object):
        """
        Test: Acto no existe (404)

        Given: Un ID de acto que no se encuentra en la base de datos.
        When: Se llama a get_object_or_404.
        Then: La vista debe propagar la excepción Http404 y DRF debe retornar un status 404.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_get_object.side_effect = Http404

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_error_generando_pdf_retorna_500_con_detalle(self, mock_get_object, mock_service_class):
        """
        Test: Error generando PDF → 500

        Given: Un acto válido pero un error inesperado durante la generación del buffer.
        When: El servicio lanza una excepción.
        Then: La vista debe capturarla, devolver status 500 y un JSON con el detalle del error.
        """
        request = self.factory.get(self.url, format='json')
        force_authenticate(request, user=MagicMock())

        mock_get_object.return_value = MagicMock(id=1)

        mensaje_error = "Error crítico en el motor de PDF"
        mock_service_class.generar_pdf_asignados.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=1)

        response.render()

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.assertEqual(response.data["error"], "Error al generar el documento")
        self.assertEqual(response.data["detalle"], mensaje_error)

        self.assertEqual(response['Content-Type'], 'application/json')


    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_buffer_vacio_sigue_devolviendo_pdf_valido(self, mock_get_object, mock_service_class):
        """
        Test: Buffer vacío

        Given: Un acto válido pero un servicio que devuelve un buffer de BytesIO vacío (sin bytes).
        When: Se genera la respuesta.
        Then: La vista debe devolver un status 200 y un contenido de respuesta vacío (b''), manteniendo el content_type.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_buffer = BytesIO() 
        mock_service_class.generar_pdf_asignados.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"")
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(mock_buffer.closed)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_acto_con_id_invalido_tipo_string(self, mock_get_object):
        """
        Test: Acto con id raro (string)

        Given: Un parámetro pk que no es un entero (aunque el URL conf debería filtrarlo).
        When: La vista llama a get_object_or_404.
        Then: El comportamiento debe ser delegado a get_object_or_404, que lanzará 404 si no encuentra el registro con ese "id".
        """
        pk_raro = "abc"
        url_rara = f'/actos/{pk_raro}/descargar-listado-insignias/'
        request = self.factory.get(url_rara)
        force_authenticate(request, user=MagicMock())

        mock_get_object.side_effect = Http404

        response = self.view(request, pk=pk_raro)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        mock_get_object.assert_called_once_with(ANY, pk=pk_raro)