from unittest.mock import PropertyMock, patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class ProximaEstacionPenitenciaViewTests(APITestCase):

    def setUp(self):
        self.url = reverse("proxima-estacion")

        self.user = MagicMock()
        self.client.force_authenticate(user=self.user)



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.ActoCultoCardSerializer")
    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_get_existe_proxima_estacion_devuelve_200(self, mock_obtener_servicio, mock_serializer):
        """
        Test: Existe próxima estación → devuelve 200 con datos serializados
        
        Given: Un usuario autenticado y la existencia de una Estación de Penitencia futura.
        When: Se realiza una petición GET a la vista.
        Then: Se llama al servicio, se serializa el objeto devuelto y se retorna 200 OK.
        """
        mock_estacion = MagicMock()
        mock_obtener_servicio.return_value = mock_estacion
        
        mock_serializer_instance = MagicMock()
        datos_simulados = {"id": 1, "nombre": "Madrugá"}
        mock_serializer_instance.data = datos_simulados
        mock_serializer.return_value = mock_serializer_instance

        response = self.client.get(self.url)

        mock_obtener_servicio.assert_called_once()
        mock_serializer.assert_called_once_with(mock_estacion)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_simulados)



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_get_no_hay_proxima_estacion_retorna_404(self, mock_obtener_servicio):
        """
        Test: No hay próxima estación → retorna 404
        
        Given: Una base de datos sin actos de tipo Estación de Penitencia futuros.
        When: El servicio 'obtener_proxima_estacion_penitencia' devuelve None.
        Then: La vista retorna un status 404 con un mensaje descriptivo en 'detail'.
        """
        mock_obtener_servicio.return_value = None

        response = self.client.get(self.url)

        mock_obtener_servicio.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], 
            "No hay ninguna Estación de Penitencia futura programada."
        )



    def test_get_usuario_no_autenticado_bloquea_acceso(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición HTTP sin credenciales de autenticación válidas.
        When: Se intenta acceder al endpoint.
        Then: DRF bloquea el acceso retornando 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)