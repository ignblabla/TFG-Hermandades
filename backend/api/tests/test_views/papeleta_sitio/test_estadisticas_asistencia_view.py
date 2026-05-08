from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.response import Response as RealResponse
from unittest.mock import patch, MagicMock

from api.vistas.papeleta_sitio.estadisticas_asistencia_view import EstadisticasAsistenciaView

class TestEstadisticasAsistenciaViewPermisos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EstadisticasAsistenciaView.as_view()
        self.acto_id = 1
        self.path = f"/api/actos/{self.acto_id}/estadisticas-asistencia/"

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_get_devuelve_estadisticas_correctamente_200(self, mock_service):
        """
        Test: Devuelve estadísticas correctamente (200)
        
        Given: Una petición GET de un usuario admin a la vista de estadísticas de un acto.
        When: El servicio obtiene las estadísticas con éxito.
        Then: La vista retorna un status 200 OK con los datos exactos del servicio.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        datos_esperados = {"total_asistentes": 100, "leidos": 50}
        mock_service.return_value = datos_esperados
        
        response = self.view(request, acto_id=self.acto_id)
        
        mock_service.assert_called_once_with(self.acto_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_get_error_en_el_servicio_devuelve_400(self, mock_service):
        """
        Test: Error en el servicio → devuelve 400
        
        Given: Una petición GET válida de un usuario admin.
        When: El servicio lanza una excepción durante la obtención de datos.
        Then: La vista la captura en el except y retorna un status 400 con el mensaje de error.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mensaje_error = "El acto especificado no existe"
        mock_service.side_effect = Exception(mensaje_error)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": mensaje_error})



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_acceso_denegado_usuarios_sin_permisos(self, mock_service):
        """
        Test: Acceso denegado a usuarios sin permisos
        
        Given: Peticiones de un usuario no autenticado y un usuario autenticado pero no admin.
        When: Intentan acceder a la ruta de estadísticas.
        Then: La clase EsAdminHermano bloquea ambas peticiones (401/403) y el servicio no se ejecuta.
        """
        request_anon = self.factory.get(self.path)
        response_anon = self.view(request_anon, acto_id=self.acto_id)
        self.assertIn(response_anon.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        request_user = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = False
        force_authenticate(request_user, user=mock_user)
        
        response_user = self.view(request_user, acto_id=self.acto_id)
        self.assertEqual(response_user.status_code, status.HTTP_403_FORBIDDEN)

        mock_service.assert_not_called()