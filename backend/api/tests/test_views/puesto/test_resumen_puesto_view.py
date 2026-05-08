import unittest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.puesto.resumen_puesto_view import ResumenPuestosActoAPIView


class TestResumenPuestosActoAPIView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.acto_id = 1
        self.url = f'/actos/{self.acto_id}/puestos/resumen/'

        self.user = MagicMock()
        self.user.is_authenticated = True 
        
        self.vista_callable = ResumenPuestosActoAPIView.as_view()



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_get_devuelve_resumen_correctamente_200(self, mock_obtener_resumen):
        """
        Test: Devuelve resumen correctamente (200)
        
        Given: Un identificador de acto válido en la URL y una petición GET.
        When: La vista invoca al servicio obtener_resumen_puestos_acto.
        Then: Se pasan los parámetros correctos, y la vista devuelve el diccionario íntegro con status 200 OK.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        datos_esperados = {
            "total_puestos": 15,
            "total_cristo": 10,
            "total_virgen": 5
        }
        mock_obtener_resumen.return_value = datos_esperados

        response = self.vista_callable(request, acto_id=self.acto_id)

        mock_obtener_resumen.assert_called_once_with(acto_id=self.acto_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)