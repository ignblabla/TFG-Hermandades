from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from unittest.mock import patch, MagicMock

from api.vistas.papeleta_sitio.ultima_papeleta_view import UltimaPapeletaView

class TestUltimaPapeletaViewPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UltimaPapeletaView.as_view()
        self.path = "/api/papeletas/ultima/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_devuelve_200_con_datos_cuando_hay_papeleta(self, mock_service, mock_serializer_class):
        """
        Test: Devuelve 200 con datos cuando hay papeleta
        
        Given: Un usuario autenticado que tiene al menos una papeleta de sitio y solicita verla.
        When: Se realiza una petición GET a la vista.
        Then: La vista invoca al servicio, serializa la papeleta obtenida y retorna un status 200 con los datos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        datos_mockeados_del_servicio = MagicMock()
        mock_service.return_value = datos_mockeados_del_servicio

        mock_serializer_instancia = MagicMock()
        datos_serializados = {'id': 1, 'acto': 'Salida Procesional', 'puesto': 'Nazareno'}
        mock_serializer_instancia.data = datos_serializados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_service.assert_called_once_with(usuario=self.mock_user)
        mock_serializer_class.assert_called_once_with(datos_mockeados_del_servicio)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_serializados)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_serializer_recibe_la_papeleta_correcta(self, mock_service, mock_serializer_class):
        """
        Test: El serializer recibe la papeleta correcta
        
        Given: El servicio devuelve una instancia específica de una papeleta.
        When: Se procesa la petición GET.
        Then: Se verifica que el serializador se instancia pasando exactamente ese objeto papeleta.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        papeleta_esperada = MagicMock()
        mock_service.return_value = papeleta_esperada
        
        self.view(request)
        
        mock_serializer_class.assert_called_once_with(papeleta_esperada)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_devuelve_serializer_data_correctamente(self, mock_service, mock_serializer_class):
        """
        Test: Devuelve serializer.data correctamente
        
        Given: El serializador contiene un diccionario de datos específico en su atributo .data.
        When: La vista retorna la respuesta.
        Then: El cuerpo de la respuesta (response.data) debe ser idéntico al contenido de serializer.data.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        
        datos_en_serializer = {"clave": "valor_de_prueba"}
        mock_instancia = MagicMock()
        mock_instancia.data = datos_en_serializer
        mock_serializer_class.return_value = mock_instancia
        
        response = self.view(request)
        
        self.assertEqual(response.data, datos_en_serializer)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_se_llama_al_servicio_con_request_user(self, mock_service):
        """
        Test: Se llama al servicio con request.user
        
        Given: Un usuario autenticado realiza la petición.
        When: La vista busca la última papeleta.
        Then: Se valida que el servicio de negocio reciba el objeto usuario de la request como argumento.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        self.view(request)
        
        mock_service.assert_called_once_with(usuario=self.mock_user)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_se_usa_status_200_correctamente(self, mock_service, mock_serializer_class):
        """
        Test: Se usa status 200 correctamente
        
        Given: El proceso de obtención y serialización es exitoso.
        When: Se genera la respuesta final.
        Then: El código de estado HTTP debe ser exactamente 200 (OK).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_no_hay_papeleta_devuelve_404(self, mock_service):
        """
        Test: No hay papeleta (devuelve 404)
        
        Given: Un usuario autenticado que no tiene ninguna papeleta registrada.
        When: Se llama al servicio y este retorna None.
        Then: La vista retorna un status 404 y un mensaje de detalle informativo.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = None
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "No se han encontrado papeletas para este hermano.")



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_error_en_el_servicio(self, mock_service):
        """
        Test: Error en el servicio
        
        Given: El servicio de obtención de papeletas falla (ej: error de base de datos).
        When: Se lanza una excepción durante la ejecución del servicio.
        Then: La excepción debe propagarse o ser manejada por el framework (DRF), 
            resultando generalmente en un error 500 si no se captura internamente.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.side_effect = Exception("Error de conexión a BD")
        
        with self.assertRaises(Exception):
            self.view(request)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_error_en_el_serializer(self, mock_service, mock_serializer_class):
        """
        Test: Error en el serializer
        
        Given: Una papeleta obtenida correctamente pero que falla al ser serializada.
        When: El serializador lanza una excepción (ej: campo obligatorio faltante en objeto).
        Then: La vista no captura el error y este escala.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        mock_serializer_class.side_effect = TypeError("Error de formato en datos")
        
        with self.assertRaises(TypeError):
            self.view(request)



    def test_usuario_no_autenticado_permiso(self):
        """
        Test: Usuario no autenticado (permiso)
        
        Given: Una petición realizada por un usuario anónimo (is_authenticated = False).
        When: DRF evalúa las permission_classes (IsAuthenticated).
        Then: La vista deniega el acceso con un status 403 (Forbidden) o 401 (Unauthorized) 
            dependiendo de la configuración de autenticación.
        """
        request = self.factory.get(self.path)

        anon_user = MagicMock()
        anon_user.is_authenticated = False
        force_authenticate(request, user=anon_user)
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_serializer_devuelve_data_vacio(self, mock_service, mock_serializer_class):
        """
        Test: Serializer devuelve data vacío
        
        Given: El servicio encuentra una papeleta, pero el serializador por algún motivo devuelve un diccionario vacío.
        When: Se procesa la respuesta.
        Then: La vista debe devolver 200 OK con el cuerpo vacío {}, ya que técnicamente la serialización fue exitosa.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        mock_instancia = MagicMock()
        mock_instancia.data = {}
        mock_serializer_class.return_value = mock_instancia
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_serializer_devuelve_datos_inesperados(self, mock_service, mock_serializer_class):
        """
        Test: Serializer devuelve datos inesperados
        
        Given: El serializador devuelve tipos de datos no estándar (ej: una lista en lugar de un diccionario).
        When: Se genera la Response.
        Then: La vista debe retornar lo que el serializador entregue, manteniendo el status 200.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = MagicMock()
        datos_raros = ["papeleta1", "papeleta2"]
        mock_instancia = MagicMock()
        mock_instancia.data = datos_raros
        mock_serializer_class.return_value = mock_instancia
        
        response = self.view(request)
        
        self.assertEqual(response.data, datos_raros)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_verificar_no_se_instancia_serializer_si_no_hay_papeleta(self, mock_service, mock_serializer_class):
        """
        Test: Verificar que no se instancia serializer si no hay papeleta
        
        Given: El servicio devuelve None (no hay papeletas).
        When: La vista ejecuta el flujo de control.
        Then: Se debe retornar el 404 antes de intentar llamar al serializador, evitando consumo innecesario de recursos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_service.return_value = None
        
        self.view(request)
        
        mock_serializer_class.assert_not_called()



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_verificar_mensaje_error_404_correcto(self, mock_service):
        """
        Test: Verificar que el mensaje de error 404 es correcto
        
        Given: Un caso de ausencia de datos.
        When: Se recibe la respuesta 404.
        Then: El mensaje en el campo 'detail' debe coincidir exactamente con el definido en los requisitos de negocio.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_service.return_value = None
        
        response = self.view(request)
        
        mensaje_esperado = "No se han encontrado papeletas para este hermano."
        self.assertEqual(response.data['detail'], mensaje_esperado)



    def test_verificar_que_el_metodo_es_get(self):
        """
        Test: Verificar que el método es GET
        
        Given: La vista solo define el método get().
        When: Se intenta realizar una petición POST.
        Then: DRF debe rechazar la petición con un status 405 (Method Not Allowed).
        """
        request = self.factory.post(self.path)
        force_authenticate(request, user=self.mock_user)
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)



    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.HistorialPapeletaSerializer')
    @patch('api.vistas.papeleta_sitio.ultima_papeleta_view.get_ultima_papeleta_hermano_service')
    def test_serializer_se_llama_una_sola_vez(self, mock_service, mock_serializer_class):
        """
        Test: El serializer se llama una sola vez
        
        Given: Una petición válida con datos existentes.
        When: Se ejecuta la lógica de la vista.
        Then: El serializador debe instanciarse exactamente una vez para evitar redundancias.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_service.return_value = MagicMock()
        
        self.view(request)
        
        self.assertEqual(mock_serializer_class.call_count, 1)