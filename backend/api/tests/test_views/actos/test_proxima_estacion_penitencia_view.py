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
    def test_existe_proxima_estacion_devuelve_200(self, mock_obtener_servicio, mock_serializer):
        """
        Test: Existe próxima estación → devuelve 200 con datos serializados
        
        Given: Un usuario autenticado y la existencia de una Estación de Penitencia futura.
        When: Se realiza una petición GET a la vista.
        Then: Se llama al servicio de obtención, se instancia el serializer con el objeto 
            devuelto y se retorna status 200 junto con los datos serializados.
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



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.ActoCultoCardSerializer")
    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_flujo_datos_servicio_hacia_serializer(self, mock_obtener_servicio, mock_serializer):
        """
        Test: Serializer recibe correctamente el objeto del servicio
        
        Given: Un resultado válido proveniente del servicio 'obtener_proxima_estacion_penitencia'.
        When: La vista procesa la petición GET.
        Then: La instancia exacta del objeto devuelta por el servicio es pasada como 
            primer argumento al constructor del serializer para su transformación.
        """
        instancia_acto_esperada = MagicMock()
        mock_obtener_servicio.return_value = instancia_acto_esperada

        mock_serializer.return_value = MagicMock(data={})

        self.client.get(self.url)

        mock_obtener_servicio.assert_called_once()
        mock_serializer.assert_called_once_with(instancia_acto_esperada)



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.ActoCultoCardSerializer")
    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_flujo_completo_exitoso_con_tracking(self, mock_obtener_servicio, mock_serializer):
        """
        Test: Flujo correcto cuando hay resultado (Servicio -> Serializer -> Response)
        
        Given: Una cadena de ejecución donde el servicio encuentra un acto y el serializer lo procesa.
        When: Se completa el ciclo de la petición.
        Then: Se verifica el tracking de llamadas: el servicio provee el dato, el serializer 
            lo transforma y la respuesta final contiene exactamente esos datos serializados.
        """
        acto_mock = MagicMock()
        mock_obtener_servicio.return_value = acto_mock

        datos_finales = {"titulo": "Procesión Test", "fecha": "2026-04-01"}
        serializer_instancia = MagicMock()
        serializer_instancia.data = datos_finales
        mock_serializer.return_value = serializer_instancia

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_finales)

        mock_obtener_servicio.assert_called_once()
        mock_serializer.assert_called_once_with(acto_mock)



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_no_hay_proxima_estacion_retorna_404(self, mock_obtener_servicio):
        """
        Test: No hay próxima estación → retorna 404
        
        Given: Una base de datos sin actos de tipo Estación de Penitencia futuros.
        When: El servicio 'obtener_proxima_estacion_penitencia' devuelve None.
        Then: La vista retorna un status 404 y un mensaje descriptivo en el campo 'detail'.
        """
        mock_obtener_servicio.return_value = None

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], 
            "No hay ninguna Estación de Penitencia futura programada."
        )



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_error_en_servicio_propaga_excepcion(self, mock_obtener_servicio):
        """
        Test: Error en servicio → excepción no controlada
        
        Given: Un fallo crítico en la capa de base de datos o lógica de negocio.
        When: El servicio lanza una excepción (ej. DatabaseError).
        Then: La vista no captura el error (no hay try/except), permitiendo que la 
            excepción se propague hacia arriba en el stack de Django.
        """
        mock_obtener_servicio.side_effect = Exception("Error crítico de base de datos")

        with self.assertRaises(Exception):
            self.client.get(self.url)



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.ActoCultoCardSerializer")
    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_error_en_serializer_falla_ejecucion(self, mock_obtener_servicio, mock_serializer):
        """
        Test: Error en serializer
        
        Given: Un acto válido devuelto por el servicio.
        When: El serializer falla al acceder a la propiedad '.data'.
        Then: La ejecución se interrumpe y la excepción lanzada por el serializer es la 
            que domina el flujo de salida.
        """
        mock_obtener_servicio.return_value = MagicMock()

        class SerializerQueFalla:
            @property
            def data(self):
                raise AttributeError("Error en mapeo de campos")

        mock_serializer.return_value = SerializerQueFalla()

        with self.assertRaises(AttributeError):
            self.client.get(self.url)



    def test_usuario_no_autenticado_bloquea_acceso(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición HTTP sin credenciales de autenticación válidas.
        When: Se intenta acceder al endpoint de próxima estación.
        Then: DRF bloquea el acceso (clase IsAuthenticated) retornando un 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.ActoCultoCardSerializer")
    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_servicio_llamado_exactamente_una_vez(self, mock_obtener_servicio, mock_serializer):
        """
        Test: Servicio llamado exactamente una vez
        
        Given: Un usuario autenticado realizando una petición válida.
        When: La vista procesa la solicitud GET.
        Then: El servicio de obtención se invoca exactamente una vez, asegurando 
            que no hay duplicación de lógica ni consultas redundantes a la base de datos.
        """
        mock_obtener_servicio.return_value = MagicMock()
        mock_serializer.return_value = MagicMock(data={})

        self.client.get(self.url)

        mock_obtener_servicio.assert_called_once()



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.ActoCultoCardSerializer")
    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_servicio_retorna_objeto_valido_no_entra_en_404(self, mock_obtener_servicio, mock_serializer):
        """
        Test: Servicio retorna objeto válido → no entra en 404
        
        Given: El servicio encuentra y retorna una instancia válida de Estación de Penitencia.
        When: La vista evalúa la condición de existencia del objeto.
        Then: Se ejecuta la rama positiva (serialización y retorno 200), evadiendo 
            completamente el bloque que genera el error 404.
        """
        mock_obtener_servicio.return_value = MagicMock()
        mock_serializer.return_value = MagicMock(data={"id": 1})

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.acto.proxima_estacion_penitencia_view.obtener_proxima_estacion_penitencia")
    def test_servicio_retorna_none_entra_en_404_correctamente(self, mock_obtener_servicio):
        """
        Test: Servicio retorna None → entra en 404 correctamente
        
        Given: El servicio evalúa que no hay ninguna Estación de Penitencia futura y retorna None.
        When: La vista evalúa la condición de existencia del objeto.
        Then: Se ejecuta la rama negativa, construyendo y retornando correctamente la 
            respuesta con status 404.
        """
        mock_obtener_servicio.return_value = None

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)