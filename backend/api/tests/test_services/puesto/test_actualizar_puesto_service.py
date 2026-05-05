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
        
        Given: Un usuario administrador, un ID de puesto existente, y datos validados a modificar. El acto asociado tiene fecha de solicitud futura y requiere papeleta.
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
            'descripcion': 'Nueva Descripción'
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

        puesto_mock.save.assert_called_once()

        self.assertEqual(resultado, puesto_mock)



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_devuelve_el_puesto_actualizado(self, mock_timezone, mock_get_object):
        """
        Test: Devuelve el puesto actualizado
        
        Given: Un proceso de actualización válido.
        When: Se completa la ejecución de update_puesto_service.
        Then: El servicio debe retornar la misma instancia del objeto puesto que fue recuperada y modificada.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.fecha_futura
        puesto_mock.acto.tipo_acto.requiere_papeleta = True
        mock_get_object.return_value = puesto_mock

        with patch('api.servicios.puesto.puesto_service.Puesto') as mock_puesto_model:
            mock_puesto_model.objects.filter.return_value.exclude.return_value.exists.return_value = False

            resultado = update_puesto_service(self.usuario_admin, 1, {'nombre': 'Nuevo'})

            self.assertEqual(resultado, puesto_mock)



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_actualiza_atributos_correctamente_con_setattr(self, mock_timezone, mock_get_object):
        """
        Test: Actualiza atributos correctamente con setattr
        
        Given: Un diccionario con múltiples campos validados (nombre, descripción, prioridad).
        When: Se itera sobre data_validada.items().
        Then: Se verifica que cada atributo se asigna al objeto puesto mediante setattr y finalmente se invoca el método save().
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.fecha_futura
        puesto_mock.acto.tipo_acto.requiere_papeleta = True
        mock_get_object.return_value = puesto_mock
        
        data_validada = {
            'nombre': 'Capataz',
            'descripcion': 'Líder del paso',
            'prioridad': 10
        }

        with patch('api.servicios.puesto.puesto_service.Puesto') as mock_puesto_model:
            mock_puesto_model.objects.filter.return_value.exclude.return_value.exists.return_value = False

            update_puesto_service(self.usuario_admin, 1, data_validada)

            self.assertEqual(puesto_mock.nombre, 'Capataz')
            self.assertEqual(puesto_mock.descripcion, 'Líder del paso')
            self.assertEqual(puesto_mock.prioridad, 10)
            puesto_mock.save.assert_called_once()



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_usa_nombre_existente_si_no_viene_en_data_validada(self, mock_timezone, mock_get_object):
        """
        Test: Usa nombre existente si no viene en data_validada
        
        Given: Un diccionario de actualización que no contiene la clave 'nombre'.
        When: Se evalúa el conflicto de nombres en el mismo acto.
        Then: El servicio debe utilizar el nombre actual del objeto puesto (puesto.nombre) para realizar la comprobación de duplicados en el queryset.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        puesto_mock = MagicMock()
        puesto_mock.nombre = "Nombre Original"
        puesto_mock.acto.inicio_solicitud.date.return_value = self.fecha_futura
        puesto_mock.acto.tipo_acto.requiere_papeleta = True
        mock_get_object.return_value = puesto_mock

        data_sin_nombre = {'descripcion': 'Solo cambio esto'}

        with patch('api.servicios.puesto.puesto_service.Puesto') as mock_puesto_model:
            mock_filter = mock_puesto_model.objects.filter
            mock_filter.return_value.exclude.return_value.exists.return_value = False

            update_puesto_service(self.usuario_admin, 1, data_sin_nombre)

            mock_filter.assert_called_once_with(acto=puesto_mock.acto, nombre="Nombre Original")



    def test_usuario_no_admin_lanza_error_permisos(self):
        """
        Test: Usuario no admin
        
        Given: Un usuario sin privilegios de administrador (esAdmin=False).
        When: Se intenta actualizar cualquier puesto.
        Then: Se lanza una excepción PermissionDenied de REST Framework con el mensaje correspondiente.
        """
        usuario = MagicMock(esAdmin=False)

        with self.assertRaises(PermissionDenied) as context:
            update_puesto_service(usuario, 1, {})
        self.assertEqual(str(context.exception), "No tienes permisos para editar puestos.")



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_puesto_no_existe_lanza_404(self, mock_puesto, mock_get_404):
        """
        Test: Puesto no existe
        
        Given: Un ID de puesto que no se encuentra en la base de datos.
        When: Se llama a get_object_or_404.
        Then: Se lanza una excepción Http404, deteniendo la ejecución del servicio.
        """
        usuario = MagicMock(esAdmin=True)
        mock_get_404.side_effect = Http404("No se encontró el puesto.")

        with self.assertRaises(Http404):
            update_puesto_service(usuario, 999, {})



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_es_none_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Fecha inicio es None
        
        Given: Un puesto asociado a un acto que no tiene definida la fecha de inicio de solicitud (None).
        When: Se intenta actualizar el puesto.
        Then: Se lanza una ValidationError indicando que no se pueden actualizar puestos sin fecha definida.
        """
        usuario = MagicMock(esAdmin=True)
        mock_timezone.now.return_value.date.return_value = date(2026, 5, 5)
        
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud = None
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError) as context:
            update_puesto_service(usuario, 1, {})
        self.assertIn("no tienen fecha definida", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_fecha_inicio_ya_pasada_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Fecha inicio ya pasada
        
        Given: Un puesto cuyo periodo de solicitud de acto ya ha comenzado o finalizado en el pasado.
        When: Se evalúa la fecha mediante .date() contra la fecha actual.
        Then: Se lanza una ValidationError prohibiendo la actualización.
        """
        usuario = MagicMock(esAdmin=True)
        hoy = date(2026, 5, 5)
        mock_timezone.now.return_value.date.return_value = hoy
        
        puesto_mock = MagicMock()

        puesto_mock.acto.inicio_solicitud.date.return_value = hoy - timedelta(days=1)
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError) as context:
            update_puesto_service(usuario, 1, {})
        self.assertIn("ya ha comenzado, es en el pasado", str(context.exception))



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_acto_no_requiere_papeleta_lanza_error(self, mock_timezone, mock_get_404):
        """
        Test: Acto no requiere papeleta
        
        Given: Un puesto existente cuyo acto asociado ha cambiado de configuración y ya no requiere papeleta.
        When: Se intenta actualizar el puesto.
        Then: Se lanza una ValidationError con el mensaje "Este acto ya no admite la gestión de puestos."
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy + timedelta(days=1)
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
        
        Given: Un intento de cambiar el nombre de un puesto a uno que ya pertenece a OTRO puesto dentro del mismo acto.
        When: Se ejecuta el filtro con .exclude(pk=puesto_id).
        Then: Se detecta la existencia del duplicado y se lanza una ValidationError.
        """
        puesto_id = 1
        nuevo_nombre = "Nombre Duplicado"
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()
        puesto_mock.pk = puesto_id
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy + timedelta(days=1)
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



    @patch('api.servicios.puesto.puesto_service.Puesto')
    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_data_validada_vacio_solo_guarda_sin_cambios(self, mock_timezone, mock_get_404, mock_puesto_model):
        """
        Test: data_validada vacío (solo guarda sin cambios)
        
        Given: Un diccionario de datos vacío.
        When: Se ejecuta el servicio de actualización.
        Then: No se deben modificar atributos, pero se debe llamar al método save() del objeto para confirmar la transacción, y el filtro de duplicados debe usar el nombre actual.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()
        puesto_mock.nombre = "Nombre Persistente"
        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy + timedelta(days=1)
        puesto_mock.acto.tipo_acto.requiere_papeleta = True
        mock_get_404.return_value = puesto_mock
        
        mock_puesto_model.objects.filter.return_value.exclude.return_value.exists.return_value = False

        update_puesto_service(self.usuario_admin, 1, {})

        self.assertEqual(puesto_mock.nombre, "Nombre Persistente")

        puesto_mock.save.assert_called_once()



    @patch('api.servicios.puesto.puesto_service.get_object_or_404')
    @patch('api.servicios.puesto.puesto_service.timezone')
    def test_no_se_llama_a_save_si_falla_validacion(self, mock_timezone, mock_get_404):
        """
        Test: Verificar que no se llama a save si falla validación
        
        Given: Un puesto cuyo acto ya ha comenzado el periodo de solicitud.
        When: Se intenta realizar una actualización.
        Then: Se lanza una ValidationError y se garantiza que el método save() del objeto nunca llega a ejecutarse para evitar persistencia de datos inválidos.
        """
        mock_timezone.now.return_value.date.return_value = self.hoy
        
        puesto_mock = MagicMock()

        puesto_mock.acto.inicio_solicitud.date.return_value = self.hoy - timedelta(days=5)
        mock_get_404.return_value = puesto_mock

        with self.assertRaises(ValidationError):
            update_puesto_service(self.usuario_admin, 1, {'nombre': 'Nuevo'})

        puesto_mock.save.assert_not_called()