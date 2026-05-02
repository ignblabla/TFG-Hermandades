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
    def test_usuario_admin_autenticado_acceso_permitido(self, mock_service):
        """
        Test: Usuario admin autenticado → acceso permitido
        
        Given: Un usuario que está autenticado y tiene su atributo esAdmin en True.
        When: Realiza una petición GET a la vista de estadísticas.
        Then: El permiso es concedido y la vista continúa su ejecución (retornando 200 OK).
        """
        request = self.factory.get(self.path)

        mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_admin.is_authenticated = True
        mock_admin.esAdmin = True
        force_authenticate(request, user=mock_admin)

        mock_service.return_value = {"total_asistentes": 100}
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once_with(self.acto_id)



    def test_usuario_no_admin_acceso_denegado(self):
        """
        Test: Usuario no admin → acceso denegado
        
        Given: Un usuario logueado pero cuyo atributo esAdmin es False.
        When: Intenta acceder a la ruta de estadísticas.
        Then: La clase de permisos bloquea la petición devolviendo un status 403 Forbidden.
        """
        request = self.factory.get(self.path)

        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = False
        force_authenticate(request, user=mock_user)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    def test_usuario_no_autenticado_acceso_denegado(self):
        """
        Test: Usuario no autenticado → acceso denegado
        
        Given: Una petición sin sesión activa ni token de autenticación.
        When: Se recibe la petición GET en la vista.
        Then: La vista deniega el acceso automáticamente con un status 403 Forbidden.
        """
        request = self.factory.get(self.path)

        mock_anonimo = MagicMock(spec=['is_authenticated'])
        mock_anonimo.is_authenticated = False
        force_authenticate(request, user=mock_anonimo)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_devuelve_estadisticas_correctamente_200(self, mock_service):
        """
        Test: Devuelve estadísticas correctamente (200)
        
        Given: Un acto_id válido y un usuario con permisos.
        When: El servicio devuelve datos estadísticos.
        Then: La vista retorna un status 200 OK y los datos en el cuerpo de la respuesta.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = {"asistentes": 10, "leidos": 5}
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('asistentes', response.data)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_llama_correctamente_al_servicio_con_acto_id(self, mock_service):
        """
        Test: Llama correctamente al servicio con acto_id
        
        Given: Una petición con un acto_id específico en la URL.
        When: Se ejecuta la lógica de la vista.
        Then: Se verifica que el servicio obtener_estadisticas_asistencia es invocado exactamente con ese acto_id.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = {}
        
        self.view(request, acto_id=self.acto_id)
        
        mock_service.assert_called_once_with(self.acto_id)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_devuelve_exactamente_el_diccionario_del_servicio(self, mock_service):
        """
        Test: Devuelve exactamente el diccionario del servicio
        
        Given: Un diccionario de datos complejo devuelto por el servicio.
        When: La vista recibe dichos datos.
        Then: La respuesta contiene exactamente la misma estructura y valores que el diccionario original.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        datos_fijos = {
            "total": 100,
            "detalles": {"hombres": 50, "mujeres": 50},
            "porcentaje": 100.0
        }
        mock_service.return_value = datos_fijos
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.data, datos_fijos)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.Response')
    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_respuesta_con_status_200(self, mock_service, mock_response_class):
        """
        Test: Respuesta con status 200
        
        Given: Una ejecución sin errores del servicio.
        When: Se construye la respuesta final.
        Then: Se verifica que se instancia la clase Response de rest_framework con el status 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = {"ok": True}

        mock_response_class.return_value = RealResponse({"ok": True})
        
        self.view(request, acto_id=self.acto_id)

        args, kwargs = mock_response_class.call_args
        self.assertEqual(kwargs.get('status'), status.HTTP_200_OK)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_error_en_el_servicio_devuelve_400(self, mock_service):
        """
        Test: Error en el servicio → devuelve 400
        
        Given: Un fallo general al intentar obtener las estadísticas.
        When: El servicio lanza una excepción estándar.
        Then: La vista la captura y retorna un status 400 Bad Request.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.side_effect = Exception()
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_servicio_lanza_excepcion_con_mensaje(self, mock_service):
        """
        Test: Servicio lanza excepción con mensaje
        
        Given: El servicio falla por una razón específica y lanza una excepción con un mensaje detallado.
        When: Se procesa la petición GET.
        Then: La respuesta contiene un diccionario con la clave 'error' y el mensaje exacto convertido a string.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mensaje_esperado = "error X"
        mock_service.side_effect = Exception(mensaje_esperado)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": mensaje_esperado})



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_error_generico_en_la_view(self, mock_service):
        """
        Test: Error genérico en la view
        
        Given: Un error de tipo inesperado (por ejemplo, TypeError o ValueError) ocurre dentro del bloque try.
        When: El motor de Python levanta la excepción.
        Then: El bloque 'except Exception' la captura genéricamente, previniendo un error 500 del servidor 
            y emitiendo un 400 controlado.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        mensaje_tipo = "Tipos de datos incompatibles al calcular porcentajes"
        mock_service.side_effect = TypeError(mensaje_tipo)
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": mensaje_tipo})



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_servicio_devuelve_dict_vacio(self, mock_service):
        """
        Test: Servicio devuelve dict vacío
        
        Given: Un acto válido pero el servicio no encuentra estadísticas aplicables y devuelve {}.
        When: La vista recibe este diccionario vacío.
        Then: La vista no debe fallar, retornando un status 200 OK con el diccionario vacío.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = {}
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_servicio_devuelve_valores_nulos_o_incompletos(self, mock_service):
        """
        Test: Servicio devuelve valores nulos o incompletos
        
        Given: El servicio procesa la información pero faltan datos, devolviendo valores nulos (None).
        When: La vista prepara la respuesta.
        Then: La vista debe ser agnóstica al contenido y devolver los valores nulos sin lanzar excepciones.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        datos_incompletos = {"total_papeletas": None, "porcentaje": None}
        mock_service.return_value = datos_incompletos
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_incompletos)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_verificar_que_no_se_transforma_la_respuesta_del_servicio(self, mock_service):
        """
        Test: Verificar que no se transforma la respuesta del servicio
        
        Given: Un diccionario de respuesta con estructuras anidadas complejas.
        When: Pasa a través del flujo de la vista hacia la Response de DRF.
        Then: Se verifica estrictamente que la vista actúa como un "pasatubos" transparente 
            y no altera, filtra ni muta las claves del diccionario original.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        datos_complejos = {
            "metadatos": {"fecha": "2023-10-01"},
            "series": [1, 2, 3],
            "valido": True
        }
        mock_service.return_value = datos_complejos
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data, datos_complejos)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_verificar_status_200_en_flujo_normal(self, mock_service):
        """
        Test: Verificar status 200 en flujo normal
        
        Given: Un escenario ideal donde todo funciona correctamente.
        When: El cliente solicita las estadísticas.
        Then: Se garantiza expresamente que el código HTTP de éxito es 200 OK.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = {"estado": "completado"}
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_verificar_status_400_en_excepcion(self, mock_service):
        """
        Test: Verificar status 400 en excepción
        
        Given: Un error provocado durante la ejecución del servicio de negocio.
        When: Se lanza cualquier excepción dentro del bloque try.
        Then: La vista debe capturar el error y responder obligatoriamente con un status 400 Bad Request, 
            tal como define la implementación.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        mock_service.side_effect = Exception("Fallo controlado para test")
        
        response = self.view(request, acto_id=self.acto_id)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch('api.vistas.papeleta_sitio.estadisticas_asistencia_view.obtener_estadisticas_asistencia')
    def test_verificar_que_el_servicio_recibe_exactamente_acto_id(self, mock_service):
        """
        Test: Verificar que el servicio recibe exactamente acto_id
        
        Given: Un identificador de acto específico en la URL (ej: 555).
        When: La vista procesa la petición GET.
        Then: El argumento pasado a la función obtener_estadisticas_asistencia debe coincidir 
            numéricamente con el acto_id capturado por el router de Django.
        """
        acto_especifico = 555
        path_especifico = f"/api/actos/{acto_especifico}/estadisticas-asistencia/"
        request = self.factory.get(path_especifico)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = {}
        
        self.view(request, acto_id=acto_especifico)

        mock_service.assert_called_once_with(acto_especifico)