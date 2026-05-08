import unittest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.core.exceptions import ValidationError

from api.vistas.solicitud_baja.solicitud_baja_view import SolicitudBajaAPIView


class TestSolicitudBajaAPIView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/api/solicitudes-baja/'
        self.vista_callable = SolicitudBajaAPIView.as_view()

        self.user = MagicMock()
        self.user.is_authenticated = True



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch('api.vistas.solicitud_baja.solicitud_baja_view.SolicitudBajaSerializer')
    @patch('api.vistas.solicitud_baja.solicitud_baja_view.PaginacionDiezElementos')
    @patch('api.vistas.solicitud_baja.solicitud_baja_view.SolicitudBaja')
    def test_get_admin_devuelve_todas_con_resumen_paginado(self, mock_model, mock_paginator_class, mock_serializer_class):
        """
        Test: Admin obtiene todas las solicitudes con resumen (paginado)
        
        Given: Un usuario administrador.
        When: Realiza una petición GET y hay resultados suficientes para paginar.
        Then: Se consultan TODAS las solicitudes (.all()), se añade el bloque 'resumen' y retorna 200 OK.
        """
        request = self.factory.get(self.url)
        self.user.esAdmin = True
        force_authenticate(request, user=self.user)

        mock_qs = MagicMock()
        mock_model.objects.all.return_value.order_by.return_value = mock_qs

        mock_qs.filter.return_value.count.return_value = 5 

        mock_paginator = mock_paginator_class.return_value
        mock_paginator.paginate_queryset.return_value = ['solicitud_1']
        
        mock_response_data = {'results': [{'id': 1}]}
        mock_paginator_response = MagicMock()
        mock_paginator_response.data = mock_response_data
        mock_paginator.get_paginated_response.return_value = mock_paginator_response

        response = self.vista_callable(request)

        mock_model.objects.all.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resumen', response.data)
        self.assertEqual(response.data['resumen']['total_pendientes'], 5)



    @patch('api.vistas.solicitud_baja.solicitud_baja_view.SolicitudBajaSerializer')
    @patch('api.vistas.solicitud_baja.solicitud_baja_view.PaginacionDiezElementos')
    @patch('api.vistas.solicitud_baja.solicitud_baja_view.SolicitudBaja')
    def test_get_hermano_devuelve_suyas_sin_paginar(self, mock_model, mock_paginator_class, mock_serializer_class):
        """
        Test: Hermano obtiene sus solicitudes sin paginar (fallback)
        
        Given: Un usuario no administrador.
        When: Realiza una petición GET y el paginador devuelve None (no aplica paginación).
        Then: Se filtran SOLO sus solicitudes (.filter(hermano=user)) y se devuelven planas (sin resumen).
        """
        request = self.factory.get(self.url)
        self.user.esAdmin = False
        force_authenticate(request, user=self.user)

        mock_qs = MagicMock()
        mock_model.objects.filter.return_value.order_by.return_value = mock_qs

        mock_paginator = mock_paginator_class.return_value
        mock_paginator.paginate_queryset.return_value = None

        datos_esperados = [{'id': 2, 'motivo': 'Motivo Baja'}]
        mock_serializer_class.return_value.data = datos_esperados

        response = self.vista_callable(request)

        mock_model.objects.filter.assert_called_once_with(hermano=self.user)
        mock_paginator.get_paginated_response.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    def test_get_usuario_no_autenticado_acceso_denegado(self):
        """
        Test: Usuario no autenticado -> acceso denegado
        
        Given: Una petición GET enviada por un usuario sin credenciales.
        When: La petición entra en la vista.
        Then: DRF la bloquea automáticamente (401/403) por el permiso IsAuthenticated.
        """
        request = self.factory.get(self.url)
        
        response = self.vista_callable(request)
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    # ---------------------------------------------------------------------------
    # TESTS POST
    # ---------------------------------------------------------------------------

    @patch('api.vistas.solicitud_baja.solicitud_baja_view.SolicitudBajaSerializer')
    @patch('api.vistas.solicitud_baja.solicitud_baja_view.crear_solicitud_baja')
    def test_post_creacion_exitosa_201(self, mock_service, mock_serializer_class):
        """
        Test: Creación exitosa de solicitud (201)
        
        Given: Un usuario autenticado enviando un motivo válido en el payload.
        When: La vista ejecuta el servicio y este crea la solicitud correctamente.
        Then: Se serializa la nueva instancia y se retorna un status 201 Created.
        """
        payload = {'motivo': 'Motivo de prueba'}
        request = self.factory.post(self.url, data=payload, format='json')
        force_authenticate(request, user=self.user)

        nueva_solicitud_mock = MagicMock()
        mock_service.return_value = nueva_solicitud_mock

        datos_esperados = {'id': 1, 'motivo': 'Motivo de prueba'}
        mock_serializer_class.return_value.data = datos_esperados

        response = self.vista_callable(request)

        mock_service.assert_called_once_with(usuario=self.user, motivo='Motivo de prueba')
        mock_serializer_class.assert_called_once_with(nueva_solicitud_mock)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, datos_esperados)



    @patch('api.vistas.solicitud_baja.solicitud_baja_view.crear_solicitud_baja')
    def test_post_validation_error_con_mensajes_400(self, mock_service):
        """
        Test: Error de validación con atributo messages (400)
        
        Given: Un payload procesado por el servicio de negocio.
        When: El servicio lanza un ValidationError nativo de Django (que contiene .messages).
        Then: El bloque except evalúa hasattr como True y retorna la lista de errores con status 400.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=self.user)

        error_django = ValidationError(["El motivo es obligatorio", "La solicitud ya existe"])
        mock_service.side_effect = error_django

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": ["El motivo es obligatorio", "La solicitud ya existe"]})



    @patch('api.vistas.solicitud_baja.solicitud_baja_view.crear_solicitud_baja')
    def test_post_validation_error_sin_mensajes_400(self, mock_service):
        """
        Test: Error de validación sin atributo messages (Fallback 400)
        
        Given: Un error de validación anómalo o de diferente librería.
        When: El servicio lanza un ValidationError que carece del atributo 'messages'.
        Then: El operador ternario ejecuta el fallback str(e) y retorna el error en status 400.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=self.user)

        class ValidationErrorSinMensajes(ValidationError):
            @property
            def messages(self):
                raise AttributeError()
                
            def __str__(self):
                return "Error de formato genérico"

        mock_service.side_effect = ValidationErrorSinMensajes("dummy")

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Error de formato genérico"})



    @patch('api.vistas.solicitud_baja.solicitud_baja_view.crear_solicitud_baja')
    def test_post_excepcion_inesperada_500(self, mock_service):
        """
        Test: Excepción inesperada (500)
        
        Given: Una petición POST válida.
        When: Ocurre un fallo crítico (ej. base de datos) que lanza una Exception genérica.
        Then: La vista la captura en el último bloque except y devuelve status 500 con un mensaje de seguridad.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=self.user)

        mock_service.side_effect = Exception("Caída de conexión de BD")

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Ocurrió un error inesperado al procesar la solicitud."})