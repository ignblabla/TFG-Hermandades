from unittest.mock import MagicMock, patch

from django.test import TestCase

from api.servicios.comunicado.comunicado_service import ComunicadoService

class ObtenerComunicadosRelacionadosUsuariosServiceTests(TestCase):

    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_con_areas_flujo_principal_correcto(self, mock_Comunicado):
        """
        Test: Usuario con áreas -> flujo principal correcto

        Given: Un usuario que tiene áreas de interés y un ID de comunicado actual.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: Se excluye el ID actual, se filtra por áreas del usuario,
                se limpia con distinct, se ordena por fecha y se limita a 3.
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()
        mock_areas_queryset.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas_queryset

        comunicado_actual_id = 99
        resultado_esperado = ['relacionado_1', 'relacionado_2', 'relacionado_3']

        mock_exclude = MagicMock()
        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        mock_order_by = MagicMock()

        mock_Comunicado.objects.exclude.return_value = mock_exclude
        mock_exclude.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        mock_distinct.order_by.return_value = mock_order_by

        mock_order_by.__getitem__.return_value = resultado_esperado

        resultado = ComunicadoService.obtener_comunicados_relacionados_usuario(
            usuario, comunicado_actual_id
        )

        usuario.areas_interes.all.assert_called_once()
        mock_areas_queryset.exists.assert_called_once()

        mock_Comunicado.objects.exclude.assert_called_once_with(id=comunicado_actual_id)

        mock_exclude.filter.assert_called_once_with(areas_interes__in=mock_areas_queryset)

        mock_filter.distinct.assert_called_once()
        mock_distinct.order_by.assert_called_once_with('-fecha_emision')

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 3, None))

        self.assertEqual(resultado, resultado_esperado)



    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_sin_areas_usa_fallback_todos_hermanos(self, mock_Comunicado, mock_AreaInteres):
        """
        Test: Usuario sin áreas -> fallback a TODOS_HERMANOS

        Given: Un usuario que NO tiene áreas de interés (exists() = False) 
                y un ID de comunicado actual.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: Se debe aplicar el exclude(id) inicial.
                Se debe filtrar por la constante AreaInteres.NombreArea.TODOS_HERMANOS.
                Se mantiene la cadena técnica: distinct -> order_by -> slice [:3].
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()
        mock_areas_queryset.exists.return_value = False
        usuario.areas_interes.all.return_value = mock_areas_queryset

        comunicado_actual_id = 10
        mock_exclude = MagicMock()
        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        mock_order_by = MagicMock()
        resultado_esperado = ['fallback_1', 'fallback_2', 'fallback_3']

        mock_AreaInteres.NombreArea.TODOS_HERMANOS = "AREA_GLOBAL"

        mock_Comunicado.objects.exclude.return_value = mock_exclude
        mock_exclude.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        mock_distinct.order_by.return_value = mock_order_by
        mock_order_by.__getitem__.return_value = resultado_esperado

        resultado = ComunicadoService.obtener_comunicados_relacionados_usuario(
            usuario, comunicado_actual_id
        )

        mock_areas_queryset.exists.assert_called_once()

        mock_Comunicado.objects.exclude.assert_called_once_with(id=comunicado_actual_id)

        mock_exclude.filter.assert_called_once_with(
            areas_interes__nombre_area="AREA_GLOBAL"
        )

        mock_filter.distinct.assert_called_once()
        mock_distinct.order_by.assert_called_once_with('-fecha_emision')

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 3, None))

        self.assertEqual(resultado, resultado_esperado)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_si_falla_acceso_a_areas_propaga_excepcion(self, mock_Comunicado):
        """
        Test: Error en áreas (Fallo de relación inicial)

        Given: Un usuario cuya relación 'areas_interes' lanza una excepción.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: La excepción se propaga hacia arriba.
                ❗ No se llega a ejecutar ninguna consulta sobre Comunicado (ni exclude ni filter).
        """
        usuario = MagicMock()

        error_db = Exception("Fallo crítico: Relación de base de datos corrupta")
        usuario.areas_interes.all.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)
        
        self.assertEqual(str(context.exception), "Fallo crítico: Relación de base de datos corrupta")

        mock_Comunicado.objects.exclude.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_obedece_a_exists_aunque_el_contenido_este_vacio(self, mock_Comunicado):
        """
        Test: Usuario con áreas vacías pero exists()=True (Caso de inconsistencia)

        Given: Un mock donde areas_usuario.exists() devuelve True, 
            pero el contenido de la relación está vacío.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: El servicio DEBE entrar en la rama de filtrado por áreas (Rama A),
            porque confía ciegamente en el booleano de .exists().
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()

        mock_areas_queryset.exists.return_value = True 
        usuario.areas_interes.all.return_value = mock_areas_queryset

        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        mock_Comunicado.objects.exclude.return_value.filter.assert_called_once_with(
            areas_interes__in=mock_areas_queryset
        )



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_evalua_areas_usuario_una_sola_vez(self, mock_Comunicado):
        """
        Test: areas_usuario evaluado una sola vez

        Given: Un usuario con áreas de interés.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: El método .all() de la relación areas_interes debe llamarse EXACTAMENTE una vez.
            Se garantiza que el servicio optimiza el acceso a la relación del usuario.
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()

        mock_areas_queryset.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas_queryset

        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        self.assertEqual(usuario.areas_interes.all.call_count, 1)