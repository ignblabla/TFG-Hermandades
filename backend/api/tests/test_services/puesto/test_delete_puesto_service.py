import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

from django.http import Http404
from rest_framework.exceptions import PermissionDenied, ValidationError

from api.servicios.puesto.puesto_service import delete_puesto_service


class TestDeletePuestoService(unittest.TestCase):

    def setUp(self):
        self.usuario_admin = MagicMock(esAdmin=True)
        self.hoy = date(2026, 5, 5)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_elimina_puesto_correctamente(self, mock_timezone, mock_get_object, mock_puesto_model):
        """
        Test: Elimina puesto correctamente (caso válido)
        
        Given: Un usuario administrador y un ID de puesto cuyo acto asociado tiene un periodo de solicitud que aún no ha comenzado (fecha en el futuro).
        When: Se invoca el servicio de eliminación de puesto.
        Then: Se recupera el puesto, se ejecuta satisfactoriamente el método delete() del objeto y la función retorna True.
        """
        usuario = MagicMock()
        usuario.esAdmin = True

        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy

        puesto_id = 1
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = hoy + timedelta(days=10)
        
        mock_get_object.return_value = puesto_mock

        resultado = delete_puesto_service(usuario, puesto_id)

        mock_get_object.assert_called_once_with(mock_puesto_model, pk=puesto_id)

        puesto_mock.delete.assert_called_once()

        self.assertTrue(resultado)



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_devuelve_true_tras_eliminar(self, mock_timezone, mock_get_object):
        """
        Test: Devuelve True tras eliminar
        
        Given: Un flujo de eliminación válido donde el puesto existe y la fecha es permitida.
        When: Se completa la ejecución de delete_puesto_service.
        Then: El servicio debe retornar exactamente el valor booleano True.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy + timedelta(days=1)
        mock_get_object.return_value = puesto_mock

        resultado = delete_puesto_service(self.usuario_admin, 1)

        self.assertIs(resultado, True)



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_llama_a_delete_una_sola_vez(self, mock_timezone, mock_get_object):
        """
        Test: Llama a delete() una sola vez
        
        Given: Una solicitud de borrado autorizada.
        When: Se ejecuta la lógica del servicio.
        Then: Se debe verificar que el método delete() del modelo se invoca exactamente una vez, evitando ejecuciones redundantes en la base de datos.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy + timedelta(days=1)
        mock_get_object.return_value = puesto_mock

        delete_puesto_service(self.usuario_admin, 1)

        puesto_mock.delete.assert_called_once()



    def test_usuario_no_admin_lanza_error_permisos(self):
        """
        Test: Usuario no admin
        
        Given: Un usuario con esAdmin=False.
        When: Se intenta eliminar un puesto.
        Then: Se lanza una excepción PermissionDenied informando de la falta de permisos.
        """
        usuario = MagicMock(esAdmin=False)

        with self.assertRaises(PermissionDenied) as context:
            delete_puesto_service(usuario, 1)
        self.assertEqual(str(context.exception), "No tienes permisos para eliminar puestos.")



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_puesto_no_existe_lanza_excepcion(self, mock_puesto_model, mock_get_404):
        """
        Test: Puesto no existe
        
        Given: Un ID de puesto que no existe en la base de datos.
        When: El servicio llama a get_object_or_404.
        Then: Se propaga la excepción Http404 lanzada por el atajo de Django.
        """
        mock_get_404.side_effect = Http404("Puesto no encontrado")

        with self.assertRaises(Http404):
            delete_puesto_service(self.usuario_admin, 999)



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_ya_pasada_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Fecha inicio ya pasada
        
        Given: Un puesto cuyo periodo de solicitud comenzó en una fecha anterior a la actual.
        When: Se evalúa la condición de fecha de inicio.
        Then: Se lanza una ValidationError impidiendo la eliminación del registro.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy - timedelta(days=1)
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError) as context:
            delete_puesto_service(self.usuario_admin, 1)
        self.assertIn("periodo de solicitud para este acto ya ha comenzado", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_es_hoy_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Fecha inicio es hoy
        
        Given: Un puesto cuya fecha de inicio de solicitud coincide exactamente con el día de hoy.
        When: Se realiza la comparación fecha_inicio.date() <= hoy.
        Then: El servicio lanza una ValidationError puesto que el periodo ya se considera iniciado.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()

        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError) as context:
            delete_puesto_service(self.usuario_admin, 1)
        self.assertIn("ya ha comenzado", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_es_none_permite_eliminar(self, mock_timezone, mock_get_404):
        """
        Test: fecha_inicio es None -> permite eliminar
        
        Given: Un puesto cuyo acto no tiene configurada una fecha de inicio de solicitud (None).
        When: Se evalúa la condición 'if fecha_inicio and...'.
        Then: La condición es falsa, se salta la validación de error y se permite la ejecución de puesto.delete().
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud = None
        mock_get_404.return_value = puesto_mock

        resultado = delete_puesto_service(self.usuario_admin, 1)

        puesto_mock.delete.assert_called_once()
        self.assertTrue(resultado)



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_no_se_llama_a_delete_si_falla_validacion(self, mock_timezone, mock_get_404):
        """
        Test: Verificar que no se llama a delete si falla validación
        
        Given: Un usuario que intenta eliminar un puesto pero no tiene permisos de administrador.
        When: Se lanza la excepción PermissionDenied al inicio del servicio.
        Then: El flujo se interrumpe inmediatamente y el método delete() del modelo nunca es invocado.
        """
        usuario_no_admin = MagicMock(esAdmin=False)
        puesto_mock = MagicMock()
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(PermissionDenied):
            delete_puesto_service(usuario_no_admin, 1)

        puesto_mock.delete.assert_not_called()



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_inicio_solicitud_manejo_de_tipos_date(self, mock_timezone, mock_get_404):
        """
        Test: inicio_solicitud sin .date() (ya es date/datetime inconsistente)
        
        Given: Un objeto inicio_solicitud que se comporta como un objeto datetime (requiere .date() para comparar).
        When: Se ejecuta la comparación con la fecha actual de timezone.now().date().
        Then: El test verifica que el servicio llama correctamente al método .date() del campo para asegurar la compatibilidad de tipos en la comparación.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()

        fecha_mock = MagicMock()
        fecha_mock.date.return_value = self.hoy + date.resolution
        
        puesto_mock.acto.inicio_solicitud = fecha_mock
        mock_get_404.return_value = puesto_mock

        delete_puesto_service(self.usuario_admin, 1)

        fecha_mock.date.assert_called()
        puesto_mock.delete.assert_called_once()