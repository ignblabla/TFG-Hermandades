import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

from django.http import Http404
from rest_framework.exceptions import PermissionDenied, ValidationError

from api.servicios.puesto.puesto_service import update_puesto_service


class TestUpdatePuestoService(unittest.TestCase):

    def setUp(self):
        self.usuario_admin = MagicMock(esAdmin=True)
        self.hoy = date(2026, 5, 5)
        self.fecha_futura = self.hoy + timedelta(days=5)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_actualiza_puesto_correctamente(self, mock_timezone, mock_get_object, mock_puesto):
        """
        Test: Actualiza puesto correctamente (caso válido)
        
        Given: Un usuario administrador, un ID de puesto existente y datos validados a modificar. El acto asociado tiene fecha de solicitud futura y requiere papeleta.
        When: Se invoca la función de actualización.
        Then: Se verifica que el puesto recuperado se actualiza con los nuevos valores, se guarda correctamente y se retorna la instancia modificada sin conflictos de nombre.
        """
        usuario = MagicMock()
        usuario.esAdmin = True

        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy

        acto_mock = MagicMock()
        acto_mock.tipo_acto.requiere_papeleta = True
        acto_mock.inicio_solicitud.date.return_value = hoy + timedelta(days=10)

        puesto_id = 1
        puesto_mock = MagicMock()
        puesto_mock.pk = puesto_id
        puesto_mock.acto = acto_mock
        puesto_mock.nombre = "Nombre Antiguo"
        puesto_mock.descripcion = "Descripción Antigua"
        
        mock_get_object.return_value = puesto_mock

        data_validada = {
            'nombre': 'Nuevo Nombre',
            'descripcion': 'Nueva Descripción',
            'acto': acto_mock 
        }

        mock_queryset_filter = MagicMock()
        mock_queryset_exclude = MagicMock()
        
        mock_puesto.objects.filter.return_value = mock_queryset_filter
        mock_queryset_filter.exclude.return_value = mock_queryset_exclude
        mock_queryset_exclude.exists.return_value = False

        resultado = update_puesto_service(usuario, puesto_id, data_validada)

        mock_get_object.assert_called_once_with(mock_puesto, pk=puesto_id)

        mock_puesto.objects.filter.assert_called_once_with(acto=acto_mock, nombre='Nuevo Nombre')
        mock_queryset_filter.exclude.assert_called_once_with(pk=puesto_id)
        mock_queryset_exclude.exists.assert_called_once()

        self.assertEqual(puesto_mock.nombre, 'Nuevo Nombre')
        self.assertEqual(puesto_mock.descripcion, 'Nueva Descripción')

        self.assertNotIn('acto', data_validada)

        puesto_mock.save.assert_called_once()

        self.assertEqual(resultado, puesto_mock)



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_actualiza_atributos_correctamente_sin_incluir_acto(self, mock_timezone, mock_get_object):
        """
        Test: Actualiza atributos correctamente (sin incluir acto)
        
        Given: Un diccionario de datos que incluye el campo 'acto' (mismo que el original) y otros atributos.
        When: Se procesa la actualización.
        Then: El campo 'acto' debe ser eliminado del diccionario con .pop() y no debe intentarse un setattr sobre él, mientras que el resto de campos sí deben actualizarse.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.fecha_futura
        puesto_mock.acto.tipo_acto.requiere_papeleta = True
        mock_get_object.return_value = puesto_mock
        
        data_validada = {
            'acto': puesto_mock.acto,
            'nombre': 'Nombre Editado',
            'descripcion': 'Nueva Desc'
        }

        with patch('api.servicios.puesto.puesto_service.Puesto') as mock_model:
            mock_model.objects.filter.return_value.exclude.return_value.exists.return_value = False

            update_puesto_service(self.usuario_admin, 1, data_validada)

            self.assertNotIn('acto', data_validada)
            self.assertEqual(puesto_mock.nombre, 'Nombre Editado')
            self.assertEqual(puesto_mock.descripcion, 'Nueva Desc')
            puesto_mock.save.assert_called_once()



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_usa_nombre_existente_si_no_viene_en_data_validada(self, mock_timezone, mock_get_object):
        """
        Test: Usa nombre existente si no viene en data_validada
        
        Given: Datos de actualización que no contienen la clave 'nombre'.
        When: Se valida la duplicidad de nombres en el acto.
        Then: El servicio debe usar el valor actual de puesto.nombre para realizar el filtrado en la base de datos.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.nombre = "Nombre Actual"
        puesto_mock.acto.inicio_solicitud.date.return_value = self.fecha_futura
        puesto_mock.acto.tipo_acto.requiere_papeleta = True
        mock_get_object.return_value = puesto_mock

        with patch('api.servicios.puesto.puesto_service.Puesto') as mock_model:
            mock_filter = mock_model.objects.filter
            mock_filter.return_value.exclude.return_value.exists.return_value = False

            update_puesto_service(self.usuario_admin, 1, {'descripcion': 'Cambio'})

            mock_filter.assert_called_once_with(acto=puesto_mock.acto, nombre="Nombre Actual")



    def test_usuario_no_admin_lanza_error_permisos(self):
        """
        Test: Usuario no admin
        
        Given: Un usuario que no tiene permisos de administrador (esAdmin=False).
        When: Se intenta acceder al servicio de actualización.
        Then: Se lanza una excepción PermissionDenied con el mensaje "No tienes permisos para editar puestos."
        """
        usuario = MagicMock(esAdmin=False)

        with self.assertRaises(PermissionDenied) as context:
            update_puesto_service(usuario, 1, {})
        self.assertEqual(str(context.exception), "No tienes permisos para editar puestos.")



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    def test_intento_de_cambiar_el_acto_lanza_error(self, mock_get_404):
        """
        Test: Intento de cambiar el acto
        
        Given: Un puesto existente vinculado a un Acto A, y datos validados que intentan vincularlo a un Acto B.
        When: Se comparan los actos en el servicio.
        Then: Se lanza una ValidationError indicando que no está permitido cambiar el acto asociado una vez creado el puesto.
        """
        acto_original = MagicMock(id=1)
        acto_nuevo = MagicMock(id=2)
        
        puesto_mock = MagicMock()
        puesto_mock.acto = acto_original
        mock_get_404.return_value = puesto_mock
        
        data = {'acto': acto_nuevo}

        with self.assertRaises(ValidationError) as context:
            update_puesto_service(self.usuario_admin, 1, data)
        self.assertIn("No está permitido cambiar el acto asociado", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_es_none_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Fecha inicio es None
        
        Given: Un puesto cuyo acto asociado no tiene definida la fecha de inicio de solicitud.
        When: Se valida el periodo de solicitud.
        Then: Se lanza una ValidationError informando que no se pueden actualizar puestos sin fecha definida.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud = None
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError) as context:
            update_puesto_service(self.usuario_admin, 1, {})
        self.assertIn("no tienen fecha definida", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_pasada_o_hoy_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Fecha inicio pasada o hoy
        
        Given: Un puesto cuyo acto asociado tiene una fecha de inicio de solicitud igual a hoy o anterior.
        When: Se evalúa la condición temporal mediante .date().
        Then: Se lanza una ValidationError prohibiendo la actualización ya que el periodo ha comenzado o es inválido.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy

        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError) as context:
            update_puesto_service(self.usuario_admin, 1, {})
        self.assertIn("ya ha comenzado, es en el pasado", str(context.exception))

        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy - timedelta(days=1)
        with self.assertRaises(ValidationError):
            update_puesto_service(self.usuario_admin, 1, {})



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_acto_no_requiere_papeleta_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Acto no requiere papeleta
        
        Given: Un acto cuya configuración ha cambiado y ya no requiere papeleta (tipo_acto.requiere_papeleta = False).
        When: Se intenta actualizar el puesto.
        Then: Se lanza una ValidationError con el mensaje "Este acto ya no admite la gestión de puestos."
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()

        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy + timedelta(days=5)
        puesto_mock.acto.tipo_acto.requiere_papeleta = False
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError) as context:
            update_puesto_service(self.usuario_admin, 1, {})
        self.assertIn("Este acto ya no admite la gestión de puestos", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_ya_existe_otro_puesto_con_mismo_nombre(self, mock_timezone, mock_get_404, mock_puesto_model):
        """
        Test: Ya existe otro puesto con mismo nombre
        
        Given: Un intento de actualizar el nombre de un puesto a uno que ya está en uso por OTRO puesto (diferente ID) en el mismo acto.
        When: Se ejecuta la consulta filter().exclude(pk=puesto_id).exists().
        Then: Se lanza una ValidationError por duplicidad de nombre.
        """
        puesto_id = 1
        nuevo_nombre = "Fiscal de Tramo"
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()
        puesto_mock.pk = puesto_id
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy + timedelta(days=5)
        puesto_mock.acto.tipo_acto.requiere_papeleta = True
        mock_get_404.return_value = puesto_mock

        mock_filter = mock_puesto_model.objects.filter
        mock_exclude = mock_filter.return_value.exclude
        mock_exclude.return_value.exists.return_value = True

        with self.assertRaises(ValidationError) as context:
            update_puesto_service(self.usuario_admin, puesto_id, {'nombre': nuevo_nombre})
        
        self.assertIn(f"Ya existe un puesto con el nombre '{nuevo_nombre}'", str(context.exception))

        mock_filter.assert_called_with(acto=puesto_mock.acto, nombre=nuevo_nombre)
        mock_exclude.assert_called_with(pk=puesto_id)