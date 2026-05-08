import base64
from unittest.mock import patch, MagicMock
from io import BytesIO
from django.http import Http404
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError

from api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view import EjecutarRepartoView


class TestEjecutarRepartoView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EjecutarRepartoView.as_view()
        self.url = '/reparto/1/reparto-automatico/'



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_reparto_exitoso_y_calculo_estadisticas_200(self, mock_get_404, mock_reparto_service, mock_puesto, mock_papeleta, mock_pdf_service):
        """
        Test: Reparto exitoso y cálculo de estadísticas (200)

        Given: Un acto válido, puestos configurados y un algoritmo que devuelve un diccionario.
        When: Se procesa la petición POST autenticada por un administrador.
        Then: Se ejecuta el reparto, se fusionan las estadísticas, se genera el PDF real en base64 y retorna 200 OK.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=1)
        mock_get_404.return_value = mock_acto
        
        mock_reparto_service.ejecutar_asignacion_automatica.return_value = {"algoritmo_ok": True}

        mock_puesto.objects.filter.return_value = [MagicMock(numero_maximo_asignaciones=5), MagicMock(numero_maximo_asignaciones=5)]
        mock_papeleta.objects.filter.return_value.count.return_value = 4

        mock_pdf_buffer = BytesIO(b"dummy_pdf_content")
        mock_pdf_service.generar_pdf_asignados.return_value = mock_pdf_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mensaje"], "Reparto ejecutado con éxito.")
        self.assertEqual(response.data["filename"], "asignacion_insignias_1.pdf")
        self.assertEqual(response.data["pdf_base64"], base64.b64encode(b"dummy_pdf_content").decode('utf-8'))

        stats = response.data["detalle_algoritmo"]
        self.assertTrue(stats["algoritmo_ok"])
        self.assertEqual(stats["total_insignias"], 10)
        self.assertEqual(stats["total_asignados"], 4)
        self.assertEqual(stats["total_no_asignados"], 6)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_reparto_algoritmo_sin_dict_y_limite_negativo_200(self, mock_get_404, mock_reparto_service, mock_puesto, mock_papeleta, mock_pdf_service):
        """
        Test: Algoritmo sin dict y control de negativos (200)

        Given: Un algoritmo que devuelve None y un escenario donde hay más asignaciones que cupo.
        When: La vista calcula los resultados.
        Then: La respuesta asigna las estadísticas directamente e impide que 'total_no_asignados' sea negativo.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.return_value = MagicMock(id=1)
        
        mock_reparto_service.ejecutar_asignacion_automatica.return_value = None
        mock_puesto.objects.filter.return_value = [MagicMock(numero_maximo_asignaciones=5)]
        mock_papeleta.objects.filter.return_value.count.return_value = 8
        mock_pdf_service.generar_pdf_asignados.return_value = BytesIO(b"")

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.data["detalle_algoritmo"]
        self.assertEqual(stats["total_insignias"], 5)
        self.assertEqual(stats["total_asignados"], 8)
        self.assertEqual(stats["total_no_asignados"], 0)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_error_validacion_algoritmo_retorna_400(self, mock_get_404, mock_reparto_service):
        """
        Test: Error de validación del reparto (400)

        Given: Condiciones de negocio no válidas detectadas por el servicio de reparto.
        When: Se lanza una DjangoValidationError.
        Then: La vista captura la excepción y retorna 400 Bad Request.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.return_value = MagicMock(id=1)

        mensaje_error = "Regla de negocio no cumplida."
        mock_reparto_service.ejecutar_asignacion_automatica.side_effect = DjangoValidationError(mensaje_error)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(mensaje_error, response.data["error"])



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_error_interno_inesperado_retorna_500(self, mock_get_404, mock_reparto_service):
        """
        Test: Error inesperado (500)

        Given: Un fallo no controlado en el servidor (ej. base de datos caída).
        When: Cualquier servicio lanza una Exception genérica.
        Then: La vista captura el error y retorna 500 Internal Server Error con el detalle.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.return_value = MagicMock(id=1)
        
        mock_reparto_service.ejecutar_asignacion_automatica.side_effect = Exception("Crash total")

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error interno del servidor")
        self.assertEqual(response.data["detalle"], "Crash total")



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_404):
        """
        Test: Acto no existe (404)

        Given: Una petición para un acto_id que no se encuentra en base de datos.
        When: get_object_or_404 falla.
        Then: DRF maneja la excepción devolviendo status 404 Not Found.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.side_effect = Http404

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_usuario_no_autorizado_retorna_401_403(self):
        """
        Test: Usuario sin permisos (401/403)

        Given: Una petición sin autenticar o de un usuario sin rol de administrador.
        When: Se intenta acceder a la vista.
        Then: El decorador de permisos bloquea el acceso.
        """
        request = self.factory.post(self.url)

        response = self.view(request, pk=1)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])