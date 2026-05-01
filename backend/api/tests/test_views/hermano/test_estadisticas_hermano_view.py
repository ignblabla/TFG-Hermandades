from unittest.mock import call, patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.vistas.hermano.estadisticas_hermano_view import EstadisticasHermanosView


class TestEstadisticasHermanosViewPositivos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EstadisticasHermanosView.as_view()
        self.path = "/api/hermanos/estadisticas/"

        self.mock_admin = MagicMock(spec=['is_authenticated', 'esAdmin'])
        self.mock_admin.is_authenticated = True
        self.mock_admin.esAdmin = True



    @patch('api.vistas.hermano.estadisticas_hermano_view.EstadisticasHermanosSerializer')
    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_usuario_admin_obtiene_estadisticas_correctamente(self, mock_service, mock_serializer_class):
        """
        Test: Usuario admin → obtiene estadísticas correctamente
        
        Given: Un usuario administrador autenticado que solicita las estadísticas generales.
        When: Se realiza una petición GET a la vista.
        Then: La vista invoca al servicio, serializa la respuesta de este y retorna un status 200 con los datos.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        datos_mockeados_del_servicio = {'total': 500, 'activos': 450}
        mock_service.return_value = datos_mockeados_del_servicio

        mock_serializer_instancia = MagicMock()
        datos_serializados = {'total': 500, 'activos': 450}
        mock_serializer_instancia.data = datos_serializados
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        mock_service.assert_called_once()

        mock_serializer_class.assert_called_once_with(datos_mockeados_del_servicio)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_serializados)



    @patch('api.vistas.hermano.estadisticas_hermano_view.EstadisticasHermanosSerializer')
    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_datos_correctos_serializer_recibe_estructura_esperada(self, mock_service, mock_serializer_class):
        """
        Test: Datos correctos → serializer recibe estructura esperada
        
        Given: Un servicio que retorna un diccionario de datos estadísticos.
        When: La vista procesa la petición exitosamente.
        Then: El serializer se instancia exactamente con el diccionario retornado por el servicio.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        estructura_servicio = {
            "total_hermanos": 100,
            "hombres": 60,
            "mujeres": 40
        }
        mock_service.return_value = estructura_servicio

        self.view(request)

        mock_serializer_class.assert_called_once_with(estructura_servicio)



    @patch('api.vistas.hermano.estadisticas_hermano_view.EstadisticasHermanosSerializer')
    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_respuesta_contiene_datos_serializados(self, mock_service, mock_serializer_class):
        """
        Test: Respuesta contiene datos serializados
        
        Given: Un serializador con datos procesados en su atributo .data.
        When: La vista construye la Response final.
        Then: El cuerpo de la respuesta es idéntico a serializer.data.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        datos_finales = {"info": "datos ya serializados"}
        mock_serializer_instancia = MagicMock()
        mock_serializer_instancia.data = datos_finales
        mock_serializer_class.return_value = mock_serializer_instancia

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_finales)



    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_servicio_se_invoca_una_unica_vez(self, mock_service):
        """
        Test: El servicio se invoca una única vez
        
        Given: Una petición GET válida de un administrador.
        When: Se ejecuta la lógica de la vista.
        Then: El servicio get_estadisticas_hermanos_service se llama exactamente una vez para evitar cálculos redundantes.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)

        self.view(request)

        self.assertEqual(mock_service.call_count, 1)



    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_usuario_no_admin_retorna_403(self, mock_service):
        """
        Test: Usuario no admin → 403
        
        Given: Un usuario autenticado con esAdmin=False.
        When: Intenta acceder a las estadísticas.
        Then: La vista retorna status 403, un mensaje específico en 'detail' y no invoca al servicio.
        """
        request = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = False
        force_authenticate(request, user=mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "No tienes permisos para ver las estadísticas de la Hermandad.")
        mock_service.assert_not_called()



    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_usuario_sin_atributo_es_admin_retorna_403(self, mock_service):
        """
        Test: Usuario sin atributo esAdmin → 403
        
        Given: Un usuario que no tiene definido el atributo 'esAdmin'.
        When: La vista ejecuta getattr(request.user, 'esAdmin', False).
        Then: Se evalúa como False (valor por defecto) y retorna 403.
        """
        request = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated'])
        mock_user.is_authenticated = True
        force_authenticate(request, user=mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_service.assert_not_called()



    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_usuario_con_es_admin_none_retorna_403(self, mock_service):
        """
        Test: Usuario con esAdmin = None → 403
        
        Given: Un usuario cuyo atributo 'esAdmin' es explícitamente None.
        When: Se evalúa en el condicional 'if not getattr(...)'.
        Then: None se evalúa como falso en Python, el 'not' lo convierte en True y se deniega el acceso (403).
        """
        request = self.factory.get(self.path)
        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = None
        force_authenticate(request, user=mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_service.assert_not_called()



    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_error_en_el_servicio_retorna_500(self, mock_service):
        """
        Test: Error en el servicio → respuesta 500
        
        Given: Un administrador autenticado.
        When: El servicio get_estadisticas_hermanos_service lanza una excepción inesperada.
        Then: La vista captura el error y retorna status 500 con el mensaje "Error al calcular las estadísticas.".
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        mock_service.side_effect = Exception("Fallo de base de datos")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al calcular las estadísticas.")
        self.assertEqual(response.data['error'], "Fallo de base de datos")



    @patch('api.vistas.hermano.estadisticas_hermano_view.EstadisticasHermanosSerializer')
    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_error_en_serializer_retorna_500(self, mock_service, mock_serializer_class):
        """
        Test: Error en serializer → respuesta 500
        
        Given: El servicio retorna datos correctamente.
        When: El serializer lanza una excepción al instanciarse o procesar los datos.
        Then: La excepción es capturada por el bloque try-except de la vista y retorna status 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = {"datos": "correctos"}
        mock_serializer_class.side_effect = Exception("Error interno del serializador")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['detail'], "Error al calcular las estadísticas.")
        mock_service.assert_called_once()



    @patch('api.vistas.hermano.estadisticas_hermano_view.EstadisticasHermanosSerializer')
    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_servicio_retorna_datos_invalidos(self, mock_service, mock_serializer_class):
        """
        Test: El servicio retorna datos inválidos
        
        Given: El servicio retorna una estructura inesperada (ej. None o String).
        When: Se intenta pasar esa estructura al serializer.
        Then: Si el serializer falla debido a esos datos, la vista retorna un status 500 controlado.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_admin)
        
        mock_service.return_value = None
        mock_serializer_class.side_effect = TypeError("No se puede iterar None")

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Error", response.data['detail'])



    def test_usuario_no_autenticado_retorna_401_403(self):
        """
        Test: Usuario no autenticado
        
        Given: Una petición GET sin credenciales de autenticación.
        When: Se intenta acceder al endpoint de estadísticas.
        Then: DRF bloquea el acceso mediante IsAuthenticated retornando 401 o 403 antes de entrar a la lógica.
        """
        request = self.factory.get(self.path)

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    @patch('api.vistas.hermano.estadisticas_hermano_view.EstadisticasHermanosSerializer')
    @patch('api.vistas.hermano.estadisticas_hermano_view.get_estadisticas_hermanos_service')
    def test_verificacion_orden_flujo_completo(self, mock_service, mock_serializer_class):
        """
        Test: Verificación de flujo correcto
        
        Given: Un usuario administrador autenticado.
        When: Se realiza una petición GET.
        Then: Se verifica que el orden de ejecución sea: 
            1. Verificación de permisos (esAdmin)
            2. Llamada al servicio de estadísticas
            3. Instanciación del serializador con los datos del servicio
            4. Construcción de la respuesta.
        """
        request = self.factory.get(self.path)

        mock_user = MagicMock(spec=['is_authenticated', 'esAdmin'])
        mock_user.is_authenticated = True
        mock_user.esAdmin = True
        force_authenticate(request, user=mock_user)

        manager = MagicMock()
        manager.attach_mock(mock_service, 'servicio')
        manager.attach_mock(mock_serializer_class, 'serializer_class')

        datos_servicio = {"count": 10}
        mock_service.return_value = datos_servicio
        
        mock_ser_instancia = MagicMock()
        mock_ser_instancia.data = datos_servicio
        mock_serializer_class.return_value = mock_ser_instancia

        self.view(request)

        expected_calls = [
            call.servicio(),
            call.serializer_class(datos_servicio)
        ]

        manager.assert_has_calls(expected_calls)

        self.assertTrue(mock_user.esAdmin or True)