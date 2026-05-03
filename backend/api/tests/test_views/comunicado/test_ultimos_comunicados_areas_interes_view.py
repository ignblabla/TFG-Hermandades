import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.comunicado.ultimos_comunicados_areas_interes_view import UltimosComunicadosAreaInteresView


class TestUltimosComunicadosAreaInteresView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UltimosComunicadosAreaInteresView.as_view()
        self.path = "/api/comunicados/ultimos-area-interes/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_get_devuelve_200_cuando_hay_comunicados(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: Devuelve 200 cuando hay comunicados
        
        Given: Un usuario autenticado que solicita sus comunicados y el servicio encuentra resultados.
        When: Se realiza una petición GET a la vista UltimosComunicadosAreaInteresView.
        Then: El servicio devuelve datos (exists() es True), el serializador es instanciado 
            y se retorna status 200 con la información.
        """
        request = self.factory.get(self.path)

        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True

        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_queryset

        mock_serializer_instance = MagicMock()
        datos_esperados = [{'id': 1, 'titulo': 'Comunicado de prueba'}]
        mock_serializer_instance.data = datos_esperados
        mock_comunicado_serializer.return_value = mock_serializer_instance

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.assert_called_once_with(self.mock_user)
        mock_queryset.exists.assert_called_once()

        mock_comunicado_serializer.assert_called_once_with(
            mock_queryset, 
            many=True, 
            context={'request': ANY}
        )

        self.assertEqual(response.data, datos_esperados)



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_llama_al_servicio_con_el_usuario_correcto(self, mock_comunicado_service):
        """
        Test: Llama al servicio con el usuario correcto
        
        Given: Un usuario autenticado realizando una petición.
        When: La vista procesa la solicitud GET.
        Then: Se invoca al método obtener_ultimos_comunicados_areas_usuario del servicio
            pasándole exactamente el objeto user de la request.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        self.view(request)

        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.assert_called_once_with(self.mock_user)



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_llama_a_exists(self, mock_comunicado_service):
        """
        Test: Llama a .exists()
        
        Given: Un queryset retornado por el servicio de comunicados.
        When: La vista decide si debe serializar los datos o devolver un 404.
        Then: Se debe llamar al método .exists() del queryset para verificar la presencia
            de registros antes de proceder.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        self.view(request)

        mock_qs.exists.assert_called_once()



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_serializa_correctamente_cuando_hay_datos(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: Serializa correctamente cuando hay datos
        
        Given: Un servicio que retorna un queryset con comunicados existentes.
        When: La vista procesa la petición y confirma que existen datos.
        Then: El serializador se instancia con el queryset, el parámetro many=True 
            y el contexto del request.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        mock_serializer_instance = mock_comunicado_serializer.return_value
        mock_serializer_instance.data = [{"id": 1}]

        self.view(request)

        mock_comunicado_serializer.assert_called_once_with(
            mock_qs, 
            many=True, 
            context={'request': ANY}
        )



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_devuelve_404_si_no_hay_comunicados(self, mock_comunicado_service):
        """
        Test: Devuelve 404 si NO hay comunicados
        
        Given: Un usuario que no tiene comunicados recientes en sus áreas de interés.
        When: El método exists() del queryset devuelve False.
        Then: La vista retorna una respuesta con status 404 y un mensaje detallando 
            la ausencia de registros.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()

        mock_qs.exists.return_value = False
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(
            response.data['detail'], 
            'No hay comunicados recientes en sus áreas de interés.'
        )



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_no_se_llama_al_serializer_si_no_hay_datos(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: No se llama al serializer si no hay datos
        
        Given: Un queryset vacío (exists() devuelve False).
        When: La vista procesa la petición GET.
        Then: La ejecución debe saltar directamente al retorno del 404 sin llegar a 
            instanciar el serializador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        self.view(request)

        mock_comunicado_serializer.assert_not_called()



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_el_servicio_devuelve_none_lanza_attribute_error(self, mock_comunicado_service):
        """
        Test: El servicio devuelve None
        
        Given: Un error de lógica en el servicio que provoca que retorne None en lugar de un queryset.
        When: La vista intenta invocar el método .exists() sobre el resultado del servicio.
        Then: Se lanza un AttributeError debido a que None no tiene el atributo 'exists'.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = None

        with self.assertRaises(AttributeError):
            self.view(request)



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_exists_lanza_excepcion(self, mock_comunicado_service):
        """
        Test: .exists() lanza excepción
        
        Given: Un fallo de conexión con la base de datos durante la verificación de existencia.
        When: Se ejecuta el método .exists() sobre el queryset.
        Then: La excepción lanzada se propaga hacia afuera de la vista.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_qs.exists.side_effect = Exception("DB error")
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        with self.assertRaises(Exception) as context:
            self.view(request)
            
        self.assertEqual(str(context.exception), "DB error")



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_serializer_falla_lanza_excepcion(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: El serializer falla
        
        Given: Un queryset válido retornado por el servicio.
        When: Se intenta instanciar el ComunicadoSerializer pero ocurre un error interno.
        Then: La excepción "Serializer error" se propaga correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        mock_comunicado_serializer.side_effect = Exception("Serializer error")

        with self.assertRaises(Exception) as context:
            self.view(request)
        self.assertEqual(str(context.exception), "Serializer error")



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_serializer_data_falla_lanza_excepcion(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: serializer.data falla
        
        Given: Un serializador instanciado correctamente.
        When: Se intenta acceder a la propiedad .data para obtener los resultados.
        Then: Si ocurre un error al procesar los datos, se lanza la excepción "data error".
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        mock_instance = mock_comunicado_serializer.return_value
        type(mock_instance).data = property(lambda _: (_ for _ in ()).throw(Exception("data error")))

        with self.assertRaises(Exception) as context:
            self.view(request)
        self.assertEqual(str(context.exception), "data error")



    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.ultimos_comunicados_areas_interes_view.ComunicadoService")
    def test_contexto_del_serializer_incluye_request(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: El contexto del serializer incluye request
        
        Given: Una petición exitosa que requiere serialización.
        When: La vista instancia el serializador.
        Then: Se valida que el diccionario de contexto contenga la clave 'request', 
            asegurando que los campos Hyperlinked u otros que dependan del contexto funcionen.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_comunicado_service.obtener_ultimos_comunicados_areas_usuario.return_value = mock_qs

        self.view(request)

        args, kwargs = mock_comunicado_serializer.call_args
        self.assertIn('request', kwargs['context'])
        self.assertIsNotNone(kwargs['context']['request'])