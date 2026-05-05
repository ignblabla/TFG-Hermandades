from unittest import TestCase
from unittest.mock import patch, MagicMock

from api.servicios.papeleta_sitio.papeleta_sitio_service import obtener_asistentes_leidos_por_acto



class TestObtenerAsistentesLeidosPorActo(TestCase):

    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_el_queryset_correctamente(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve el queryset correctamente

        Given: Un identificador de acto válido.
        When: Se solicita obtener los asistentes con papeletas en estado LEIDA.
        Then: Se debe devolver el queryset resultante tras aplicar filter, select_related y order_by.
        """
        acto_id = 1
        mock_queryset_esperado = MagicMock()

        estado_leida_mock = 'LEIDA'
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = estado_leida_mock

        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value = mock_queryset_esperado

        resultado = obtener_asistentes_leidos_por_acto(acto_id)

        self.assertEqual(resultado, mock_queryset_esperado)

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            acto_id=acto_id,
            estado_papeleta=estado_leida_mock
        )
        
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.assert_called_once_with(
            'hermano', 'puesto', 'tramo'
        )
        
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value.order_by.assert_called_once_with(
            'tramo__paso', 'tramo__numero_orden', 'orden_en_tramo'
        )