from unittest import TestCase
from unittest.mock import patch, MagicMock

from api.servicios.papeleta_sitio.papeleta_sitio_service import obtener_estadisticas_asistencia
from django.core.exceptions import ValidationError


class TestObtenerEstadisticasAsistencia(TestCase):

    def setUp(self):
        self.patcher_acto = patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
        self.mock_acto = self.patcher_acto.start()
        self.mock_acto.objects.filter.return_value.exists.return_value = True

    def tearDown(self):
        self.patcher_acto.stop()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_estadisticas_correctas(self, mock_papeleta_sitio_model, mock_acto_model):
        """
        Test: Devuelve estadísticas correctas (caso normal)

        Given: Un acto existente con papeletas procesadas en diferentes estados.
        When: Se solicitan las estadísticas de asistencia del acto.
        Then: Se debe calcular y devolver el total, las leídas y las pendientes correctamente.
        """
        acto_id = 1

        mock_acto_model.objects.filter.return_value.exists.return_value = True

        mock_papeleta_sitio_model.EstadoPapeleta.EMITIDA = 'EMITIDA'
        mock_papeleta_sitio_model.EstadoPapeleta.RECOGIDA = 'RECOGIDA'
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = 'LEIDA'

        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': 100,
            'leidas': 60
        }

        resultado = obtener_estadisticas_asistencia(acto_id)

        diccionario_esperado = {
            "total_papeletas": 100,
            "papeletas_leidas": 60,
            "papeletas_pendientes": 40
        }
        self.assertEqual(resultado, diccionario_esperado)

        mock_acto_model.objects.filter.assert_called_once_with(id=acto_id)
        mock_acto_model.objects.filter.return_value.exists.assert_called_once()

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            acto_id=acto_id,
            estado_papeleta__in=['EMITIDA', 'RECOGIDA', 'LEIDA']
        )

        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_maneja_ambos_valores_none(self, mock_papeleta_sitio_model):
        """
        Test: Maneja ambos valores None

        Given: Una respuesta de aggregate donde tanto total como leidas son None.
        When: El servicio inicializa las variables.
        Then: Todos los campos de la respuesta deben ser 0 para evitar errores de tipo.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {
            'total': None,
            'leidas': None
        }

        resultado = obtener_estadisticas_asistencia(1)

        self.assertEqual(resultado["total_papeletas"], 0)
        self.assertEqual(resultado["papeletas_leidas"], 0)
        self.assertEqual(resultado["papeletas_pendientes"], 0)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Q')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Count')
    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_usa_correctamente_aggregate_con_count_y_q(self, mock_papeleta_sitio_model, mock_count, mock_q):
        """
        Test: Usa correctamente aggregate con Count y Q

        Given: La necesidad de contar el total de registros y filtrar condicionalmente los leídos.
        When: Se realiza la agregación en la base de datos.
        Then: Se debe llamar al método aggregate utilizando instancias de Count y un objeto Q para el filtro de leídas.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.return_value = {'total': 10, 'leidas': 5}
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = "LEIDA"

        obtener_estadisticas_asistencia(1)

        mock_papeleta_sitio_model.objects.filter.return_value.aggregate.assert_called_once()

        mock_q.assert_called_with(estado_papeleta="LEIDA")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.Acto')
    def test_el_acto_no_existe(self, mock_acto_model):
        """
        Test: El acto no existe

        Given: Un identificador de acto que no se encuentra en la base de datos.
        When: Se valida la existencia del acto al inicio del servicio.
        Then: Se debe lanzar una excepción ValidationError con el mensaje "El acto especificado no existe.".
        """
        mock_acto_model.objects.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError) as context:
            obtener_estadisticas_asistencia(999)
        
        self.assertEqual(str(context.exception.message), "El acto especificado no existe.")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_verificar_que_exists_se_evalua_antes_del_aggregate(self, mock_papeleta_sitio):
        """
        Test: Verificar que exists() se evalúa antes del aggregate

        Given: Un acto que no existe en la base de datos.
        When: Se llama al servicio.
        Then: Se debe lanzar ValidationError y el mock de PapeletaSitio no debe haber sido llamado nunca.
        """
        self.mock_acto.objects.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError):
            obtener_estadisticas_asistencia(1)

        mock_papeleta_sitio.objects.filter.assert_not_called()