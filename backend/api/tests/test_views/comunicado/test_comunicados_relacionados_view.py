import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.comunicado.comunicados_relacionados_view import ComunicadosRelacionadosView


class TestComunicadosRelacionadosView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ComunicadosRelacionadosView.as_view()
        self.exclude_id_prueba = 1
        self.path = f"/api/comunicados/{self.exclude_id_prueba}/relacionados/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_get_devuelve_200_correctamente(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: Devuelve 200 correctamente (flujo feliz)
        
        Given: Un usuario autenticado y un ID de comunicado que se desea excluir.
        When: Se realiza una petición GET a la vista para obtener los comunicados relacionados.
        Then: El servicio devuelve el queryset esperado, se invoca al serializador y 
            la vista retorna un status 200 junto con los datos correctos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_queryset = MagicMock()
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = mock_queryset

        mock_serializer_instance = MagicMock()
        datos_esperados = [{'id': 2, 'titulo': 'Comunicado relacionado'}]
        mock_serializer_instance.data = datos_esperados
        mock_comunicado_serializer.return_value = mock_serializer_instance

        response = self.view(request, exclude_id=self.exclude_id_prueba)

        mock_comunicado_service.obtener_comunicados_relacionados_usuario.assert_called_once_with(
            self.mock_user, 
            self.exclude_id_prueba
        )

        mock_comunicado_serializer.assert_called_once_with(
            mock_queryset, 
            many=True, 
            context={'request': ANY}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_llama_al_servicio_con_user_y_exclude_id(self, mock_comunicado_service):
        """
        Test: Llama al servicio con user y exclude_id
        
        Given: Un usuario autenticado y un ID de exclusión recibido por URL.
        When: Se procesa la petición GET en la vista.
        Then: Se verifica que la capa de servicio reciba exactamente el objeto usuario 
            de la request y el ID de exclusión proporcionado.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = MagicMock()

        self.view(request, exclude_id=self.exclude_id_prueba)

        mock_comunicado_service.obtener_comunicados_relacionados_usuario.assert_called_once_with(
            self.mock_user, 
            self.exclude_id_prueba
        )



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_el_serializer_se_llama_correctamente(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: El serializer se llama correctamente
        
        Given: Un queryset de comunicados devuelto por el servicio.
        When: La vista procede a preparar la respuesta.
        Then: Se valida que el serializador se instancie con el queryset obtenido, 
            la opción many=True y el contexto que incluye la request actual.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_qs = MagicMock()
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = mock_qs

        self.view(request, exclude_id=self.exclude_id_prueba)

        mock_comunicado_serializer.assert_called_once_with(
            mock_qs,
            many=True,
            context={'request': ANY}
        )



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_devuelve_correctamente_serializer_data(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: Devuelve correctamente serializer.data
        
        Given: Un servicio que retorna comunicados relacionados.
        When: La vista accede a la propiedad .data del serializador.
        Then: Se verifica que la respuesta de la API contenga exactamente la información 
            preparada por el serializador.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = MagicMock()

        datos_simulados = [{"id": 1}]
        mock_comunicado_serializer.return_value.data = datos_simulados

        response = self.view(request, exclude_id=self.exclude_id_prueba)

        self.assertEqual(response.data, datos_simulados)



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_funciona_con_lista_vacia(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: Funciona con lista vacía
        
        Given: Un escenario donde no existen comunicados relacionados.
        When: Se realiza la petición GET.
        Then: La vista no aplica lógica condicional de error, retornando un status 200 
            con una lista vacía, cumpliendo con el contrato de la API.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = MagicMock()

        mock_comunicado_serializer.return_value.data = []

        response = self.view(request, exclude_id=self.exclude_id_prueba)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_servicio_devuelve_none_pasa_al_serializer(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: El servicio devuelve None
        
        Given: Un escenario donde el servicio devuelve None en lugar de un queryset.
        When: La vista intenta instanciar el serializador con el resultado del servicio.
        Then: El serializador se llama con None, lo cual permite detectar si existe 
            falta de validación en la vista antes de la serialización.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = None

        try:
            self.view(request, exclude_id=self.exclude_id_prueba)
        except Exception:
            pass

        mock_comunicado_serializer.assert_called_once_with(
            None,
            many=True,
            context={'request': unittest.mock.ANY}
        )



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_servicio_lanza_excepcion(self, mock_comunicado_service):
        """
        Test: El servicio lanza excepción
        
        Given: Un fallo crítico en el servicio al intentar obtener comunicados relacionados.
        When: Se invoca el método del servicio desde la vista.
        Then: La excepción "Service error" se propaga hacia afuera, asegurando que 
            el error no sea silenciado.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_comunicado_service.obtener_comunicados_relacionados_usuario.side_effect = Exception("Service error")

        with self.assertRaises(Exception) as context:
            self.view(request, exclude_id=self.exclude_id_prueba)
            
        self.assertEqual(str(context.exception), "Service error")



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_serializer_lanza_excepcion(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: El serializer lanza excepción
        
        Given: Un queryset válido retornado por el servicio.
        When: La vista intenta instanciar el ComunicadoSerializer.
        Then: La excepción "Serializer error" lanzada durante la instanciación 
            se propaga correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = MagicMock()

        mock_comunicado_serializer.side_effect = Exception("Serializer error")

        with self.assertRaises(Exception) as context:
            self.view(request, exclude_id=self.exclude_id_prueba)
        self.assertEqual(str(context.exception), "Serializer error")



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_serializer_data_lanza_excepcion(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: serializer.data lanza excepción
        
        Given: Un serializador instanciado correctamente.
        When: La vista accede a la propiedad .data para construir la Response.
        Then: La excepción "data error" lanzada al serializar los campos se propaga correctamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = MagicMock()

        mock_instance = mock_comunicado_serializer.return_value
        type(mock_instance).data = property(lambda _: (_ for _ in ()).throw(Exception("data error")))

        with self.assertRaises(Exception) as context:
            self.view(request, exclude_id=self.exclude_id_prueba)
        self.assertEqual(str(context.exception), "data error")



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoSerializer")
    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_el_contexto_incluye_request(self, mock_comunicado_service, mock_comunicado_serializer):
        """
        Test: El contexto incluye request
        
        Given: Una petición válida a la vista.
        When: Se instancia el serializador.
        Then: Se verifica que el diccionario 'context' pasado al serializador 
            contenga la clave 'request', necesaria para la generación de URLs absolutas.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = MagicMock()

        self.view(request, exclude_id=self.exclude_id_prueba)

        _, kwargs = mock_comunicado_serializer.call_args
        self.assertIn('request', kwargs['context'])



    @patch("api.vistas.comunicado.comunicados_relacionados_view.ComunicadoService")
    def test_exclude_id_invalido_no_se_valida_en_vista(self, mock_comunicado_service):
        """
        Test: exclude_id inválido (string, None, etc.)
        
        Given: Un valor de exclude_id que no cumple con el tipo esperado (ej. string).
        When: La vista recibe este parámetro desde la URL.
        Then: La vista no realiza validación previa y delega el valor tal cual 
            hacia la capa de servicio.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        exclude_id_invalido = "invalid"
        mock_comunicado_service.obtener_comunicados_relacionados_usuario.return_value = MagicMock()

        try:
            self.view(request, exclude_id=exclude_id_invalido)
        except Exception:
            pass

        mock_comunicado_service.obtener_comunicados_relacionados_usuario.assert_called_once_with(
            self.mock_user, 
            exclude_id_invalido
        )