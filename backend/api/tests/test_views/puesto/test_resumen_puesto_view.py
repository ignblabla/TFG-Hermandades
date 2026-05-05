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
    def test_devuelve_resumen_correctamente_200(self, mock_obtener_resumen):
        """
        Test: Devuelve resumen correctamente (200)
        
        Given: Un identificador de acto válido en la URL y un usuario autenticado.
        When: Se realiza una petición GET a la vista de resumen de puestos.
        Then: La vista invoca al servicio obtener_resumen_puestos_acto y devuelve el diccionario resultante con un código HTTP 200 OK.
        """
        request = self.factory.get(self.url)

        force_authenticate(request, user=self.user)

        datos_resumen = {
            "total_puestos": 15,
            "total_cristo": 10,
            "total_virgen": 5
        }
        mock_obtener_resumen.return_value = datos_resumen

        response = self.vista_callable(request, acto_id=self.acto_id)

        mock_obtener_resumen.assert_called_once_with(acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data, datos_resumen)



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_llama_al_servicio_con_acto_id_correcto(self, mock_obtener_resumen):
        """
        Test: Llama al servicio con acto_id correcto
        
        Given: Una petición GET a la vista de resumen y un acto_id extraído de la URL.
        When: Se procesa la petición en la vista.
        Then: Se verifica que la vista invoca al servicio subyacente pasando exactamente el acto_id proporcionado en los parámetros de la ruta.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        mock_obtener_resumen.return_value = {}

        self.vista_callable(request, acto_id=self.acto_id)

        mock_obtener_resumen.assert_called_once_with(acto_id=self.acto_id)



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_devuelve_exactamente_el_dict_del_servicio(self, mock_obtener_resumen):
        """
        Test: Devuelve exactamente el dict del servicio
        
        Given: Un diccionario controlado y específico retornado por la capa de servicio.
        When: La vista construye la respuesta HTTP.
        Then: Los datos de la respuesta (response.data) deben ser exactamente iguales al diccionario generado por el servicio, demostrando que la vista no altera la estructura de datos.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        dict_controlado = {
            "total_puestos": 100, 
            "total_cristo": 60, 
            "total_virgen": 40
        }
        mock_obtener_resumen.return_value = dict_controlado

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.data, dict_controlado)



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_status_code_200_correcto(self, mock_obtener_resumen):
        """
        Test: Status code 200 correcto
        
        Given: Un flujo de ejecución exitoso donde el servicio devuelve los datos solicitados sin lanzar errores.
        When: Se emite la respuesta final hacia el cliente.
        Then: El código de estado de la respuesta HTTP debe ser explícitamente 200 OK.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_obtener_resumen.return_value = {"resumen": "ok"}

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_error_en_el_servicio_lanza_excepcion(self, mock_obtener_resumen):
        """
        Test: Error en el servicio
        
        Given: Una petición GET válida, pero donde la capa de servicio encuentra un error (por ejemplo, base de datos caída o datos corruptos).
        When: La vista invoca a obtener_resumen_puestos_acto.
        Then: La excepción lanzada por el servicio se propaga hacia arriba, interrumpiendo el flujo de la vista para que el gestor de errores global la maneje.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mensaje_error = "Error crítico de base de datos al calcular el resumen"
        mock_obtener_resumen.side_effect = Exception(mensaje_error)

        with self.assertRaises(Exception) as context:
            self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(str(context.exception), mensaje_error)

        mock_obtener_resumen.assert_called_once_with(acto_id=self.acto_id)



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_servicio_devuelve_dict_vacio(self, mock_obtener_resumen):
        """
        Test: Servicio devuelve dict vacío
        
        Given: Un escenario donde el servicio de cálculo de métricas retorna un diccionario vacío (ej. no hay datos inicializados).
        When: La vista recoge este resultado para construir la respuesta HTTP.
        Then: Se devuelve un código 200 OK con un payload que es exactamente un diccionario vacío {}.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_obtener_resumen.return_value = {}

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_servicio_devuelve_valores_none_o_incompletos(self, mock_obtener_resumen):
        """
        Test: Servicio devuelve valores None o incompletos
        
        Given: El servicio de negocio devuelve una estructura de datos parcial con valores nulos o claves faltantes.
        When: Se procesa la petición a través de la vista.
        Then: La vista maneja el objeto sin lanzar excepciones por atributos faltantes y lo transfiere directamente en la respuesta.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        
        datos_incompletos = {
            "total_puestos": None,
            "total_cristo": 0
        }
        mock_obtener_resumen.return_value = datos_incompletos

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_incompletos)



    @patch('api.vistas.puesto.resumen_puesto_view.obtener_resumen_puestos_acto')
    def test_verificar_que_no_transforma_la_respuesta_del_servicio(self, mock_obtener_resumen):
        """
        Test: Verificar que no transforma la respuesta del servicio
        
        Given: Un diccionario con claves y valores arbitrarios que difieren de la estructura estándar esperada.
        When: La vista toma los datos del servicio y crea el objeto Response.
        Then: Se comprueba que la vista actúa puramente como pasarela y no muta, filtra ni formatea el diccionario devuelto por el servicio.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        datos_arbitrarios = {
            "estado": "calculado",
            "detalles": [1, 2, 3],
            "metadatos": {"version": 1.2}
        }
        mock_obtener_resumen.return_value = datos_arbitrarios

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_arbitrarios)