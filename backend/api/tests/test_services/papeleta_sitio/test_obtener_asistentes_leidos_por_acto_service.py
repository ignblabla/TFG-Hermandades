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



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_filtra_correctamente_por_acto_y_estado(self, mock_papeleta_sitio_model):
        """
        Test: Filtra correctamente por acto_id y estado LEIDA

        Given: Un ID de acto y la constante de estado LEIDA.
        When: Se invoca al servicio.
        Then: El método filter debe recibir el acto_id y el valor correcto de la constante EstadoPapeleta.LEIDA.
        """
        acto_id = 500
        estado_mock = 'ESTADO_LEIDA'
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = estado_mock
        
        obtener_asistentes_leidos_por_acto(acto_id)
        
        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            acto_id=acto_id,
            estado_papeleta=estado_mock
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_usa_correctamente_select_related(self, mock_papeleta_sitio_model):
        """
        Test: Usa correctamente select_related

        Given: Una consulta de asistentes que requiere datos de tablas relacionadas.
        When: Se construye el queryset.
        Then: Se debe llamar a select_related con 'hermano', 'puesto' y 'tramo'.
        """
        mock_filter = mock_papeleta_sitio_model.objects.filter.return_value
        
        obtener_asistentes_leidos_por_acto(1)
        
        mock_filter.select_related.assert_called_once_with(
            'hermano', 'puesto', 'tramo'
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_ordenacion_correcta(self, mock_papeleta_sitio_model):
        """
        Test: Ordenación correcta (paso -> tramo -> orden)

        Given: Un listado de asistentes a ordenar para la cofradía.
        When: Se aplica la ordenación al queryset.
        Then: Se debe llamar a order_by con los campos 'tramo__paso', 'tramo__numero_orden' y 'orden_en_tramo'.
        """
        mock_select = mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value
        
        obtener_asistentes_leidos_por_acto(1)
        
        mock_select.order_by.assert_called_once_with(
            'tramo__paso', 'tramo__numero_orden', 'orden_en_tramo'
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_encadenamiento_correcto_del_queryset(self, mock_papeleta_sitio_model):
        """
        Test: Encadenamiento correcto del queryset

        Given: La necesidad de realizar una consulta compleja encadenada.
        When: Se ejecuta el servicio.
        Then: Cada eslabón de la cadena (.filter, .select_related, .order_by) debe devolver el mock del siguiente nivel.
        """
        mock_filter = MagicMock()
        mock_select = MagicMock()
        mock_order = MagicMock()

        mock_papeleta_sitio_model.objects.filter.return_value = mock_filter
        mock_filter.select_related.return_value = mock_select
        mock_select.order_by.return_value = mock_order

        resultado = obtener_asistentes_leidos_por_acto(1)

        self.assertEqual(resultado, mock_order)
        mock_papeleta_sitio_model.objects.filter.assert_called_once()
        mock_filter.select_related.assert_called_once()
        mock_select.order_by.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_exactamente_el_resultado_de_order_by(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve exactamente el resultado de order_by

        Given: El queryset final ya ordenado.
        When: El servicio retorna el valor.
        Then: El objeto devuelto por el servicio debe ser exactamente el mismo objeto mock retornado por order_by.
        """
        mock_final_qs = MagicMock()
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value = mock_final_qs

        resultado = obtener_asistentes_leidos_por_acto(1)

        self.assertIs(resultado, mock_final_qs)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_acto_id_es_none(self, mock_papeleta_sitio_model):
        """
        Test: acto_id es None

        Given: Un valor None como identificador de acto.
        When: Se intenta realizar el filtrado en la base de datos.
        Then: El método filter debe ser llamado con acto_id=None, dejando que el ORM gestione la consulta (que normalmente resultará en un conjunto vacío o error según la BD).
        """
        obtener_asistentes_leidos_por_acto(None)
        
        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            acto_id=None,
            estado_papeleta=mock_papeleta_sitio_model.EstadoPapeleta.LEIDA
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_acto_id_invalido_tipo_incorrecto(self, mock_papeleta_sitio_model):
        """
        Test: acto_id inválido (tipo incorrecto)

        Given: Un string en lugar de un entero para el acto_id.
        When: Se ejecuta el servicio.
        Then: El servicio debe intentar realizar la consulta con el valor proporcionado, delegando la validación de tipo al ORM de Django.
        """
        acto_id_invalido = "id_invalido"
        obtener_asistentes_leidos_por_acto(acto_id_invalido)
        
        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            acto_id=acto_id_invalido,
            estado_papeleta=mock_papeleta_sitio_model.EstadoPapeleta.LEIDA
        )



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_filter(self, mock_papeleta_sitio_model):
        """
        Test: Error en filter()

        Given: Un error de sintaxis o de conexión en el método filter.
        When: Se inicia la construcción del queryset.
        Then: La excepción debe propagarse hacia arriba sin ser capturada por el servicio.
        """
        mock_papeleta_sitio_model.objects.filter.side_effect = Exception("Error en filter")

        with self.assertRaises(Exception) as context:
            obtener_asistentes_leidos_por_acto(1)
        
        self.assertEqual(str(context.exception), "Error en filter")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_select_related(self, mock_papeleta_sitio_model):
        """
        Test: Error en select_related()

        Given: Un fallo al intentar definir las relaciones de carga optimizada.
        When: Se encadena el método select_related.
        Then: El servicio debe fallar permitiendo que la excepción del ORM sea visible.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.side_effect = Exception("Error en select_related")

        with self.assertRaises(Exception) as context:
            obtener_asistentes_leidos_por_acto(1)
        
        self.assertEqual(str(context.exception), "Error en select_related")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_error_en_order_by(self, mock_papeleta_sitio_model):
        """
        Test: Error en order_by()

        Given: Una excepción lanzada durante la fase de ordenación del queryset.
        When: Se ejecuta el último paso de la lógica del servicio.
        Then: Se debe capturar y verificar la excepción lanzada por order_by.
        """
        mock_qs = mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value
        mock_qs.order_by.side_effect = Exception("Error en order_by")

        with self.assertRaises(Exception) as context:
            obtener_asistentes_leidos_por_acto(1)
        
        self.assertEqual(str(context.exception), "Error en order_by")



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_cadena_queryset_rota(self, mock_papeleta_sitio_model):
        """
        Test: Cadena de queryset rota (algún método devuelve None)

        Given: Un fallo de configuración en el mock donde un eslabón intermedio (select_related) devuelve None.
        When: El servicio intenta aplicar la ordenación (.order_by()) sobre ese resultado.
        Then: Se debe lanzar un AttributeError, confirmando que la cadena no puede continuar si un método falla devolviendo None.
        """
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value = None

        with self.assertRaises(AttributeError):
            obtener_asistentes_leidos_por_acto(1)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_queryset_vacio_sin_asistentes_leidos(self, mock_papeleta_sitio_model):
        """
        Test: Queryset vacío (sin asistentes leídos)

        Given: Un acto válido pero que aún no tiene papeletas marcadas como LEIDA.
        When: Se ejecuta la consulta completa.
        Then: El servicio debe devolver un objeto que actúe como un iterable vacío, permitiendo su uso en bucles sin errores.
        """
        mock_qs_vacio = MagicMock()
        mock_qs_vacio.__iter__.return_value = iter([])
        mock_qs_vacio.__len__.return_value = 0
        
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value = mock_qs_vacio

        resultado = obtener_asistentes_leidos_por_acto(1)

        self.assertEqual(len(list(resultado)), 0)
        self.assertIs(resultado, mock_qs_vacio)



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_verificar_uso_exacto_del_estado_leida(self, mock_papeleta_sitio_model):
        """
        Test: Verificar uso exacto del estado LEIDA

        Given: La definición de los estados en el modelo PapeletaSitio.
        When: Se realiza el filtrado de asistentes.
        Then: El servicio debe utilizar obligatoriamente la constante PapeletaSitio.EstadoPapeleta.LEIDA para filtrar los registros.
        """
        valor_estado_esperado = "VALOR_MAGICO_LEIDA"
        mock_papeleta_sitio_model.EstadoPapeleta.LEIDA = valor_estado_esperado
        
        obtener_asistentes_leidos_por_acto(1)

        args, kwargs = mock_papeleta_sitio_model.objects.filter.call_args
        self.assertEqual(kwargs['estado_papeleta'], valor_estado_esperado)