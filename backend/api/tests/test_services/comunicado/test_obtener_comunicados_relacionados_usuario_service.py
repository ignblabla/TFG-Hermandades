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
    def test_obtener_relacionados_aplica_exclusion_inicial_del_id_actual(self, mock_Comunicado):
        """
        Test: Verificar exclusión del comunicado actual

        Given: Un ID de comunicado (comunicado_actual_id).
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: Se debe llamar a Comunicado.objects.exclude() con el ID proporcionado.
                Se valida que esta es la operación base de todo el servicio.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True
        comunicado_actual_id = 500

        mock_exclude = MagicMock()
        mock_Comunicado.objects.exclude.return_value = mock_exclude

        ComunicadoService.obtener_comunicados_relacionados_usuario(
            usuario, comunicado_actual_id
        )

        mock_Comunicado.objects.exclude.assert_called_once_with(id=comunicado_actual_id)

        self.assertTrue(mock_exclude.filter.called)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_aplica_orden_descendente_por_fecha(self, mock_Comunicado):
        """
        Test: Verificar orden descendente

        Given: Un usuario y un comunicado actual.
        When: Se solicita obtener comunicados relacionados.
        Then: El QuerySet resultante debe llamar a .order_by() con '-fecha_emision'.
                Esto garantiza que las sugerencias sean las más nuevas disponibles.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_order_by = MagicMock()
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value.order_by = mock_order_by

        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        mock_order_by.assert_called_once_with('-fecha_emision')



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_aplica_limite_de_tres_resultados(self, mock_Comunicado):
        """
        Test: Verificar límite de resultados

        Given: Un usuario y un comunicado actual.
        When: Se ejecuta obtener_comunicados_relacionados_usuario.
        Then: Se debe aplicar el slicing [:3] al final de la cadena del QuerySet.
                Se valida que el límite técnico coincide con el requerimiento de negocio.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True
        
        mock_order_by = MagicMock()
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 3, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_mantiene_orden_encadenamiento_correcto(self, mock_Comunicado):
        """
        Test: Encadenamiento correcto del queryset

        Given: Un usuario con áreas de interés.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: Se debe seguir estrictamente el orden: exclude -> filter -> distinct -> order_by.
                Se verifica que cada método se ejecute sobre el objeto retornado por el anterior.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True
        
        mock_exclude = MagicMock(name="MockExclude")
        mock_filter = MagicMock(name="MockFilter")
        mock_distinct = MagicMock(name="MockDistinct")
        mock_order_by = MagicMock(name="MockOrderBy")

        mock_Comunicado.objects.exclude.return_value = mock_exclude
        mock_exclude.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        mock_distinct.order_by.return_value = mock_order_by

        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        mock_exclude.filter.assert_called_once()

        mock_filter.distinct.assert_called_once()

        mock_distinct.order_by.assert_called_once()

        mock_order_by.__getitem__.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_retorna_exactamente_el_objeto_final(self, mock_Comunicado):
        """
        Test: Retorno correcto

        Given: Un flujo de QuerySet que termina en un slicing de 3 elementos.
        When: Se ejecuta obtener_comunicados_relacionados_usuario.
        Then: El valor retornado debe ser la referencia exacta al objeto final de la cadena.
                Se verifica la integridad de la referencia (assertIs).
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_queryset_final = MagicMock(spec=list, name="ObjetoFinal")

        mock_order_by = MagicMock()
        mock_order_by.__getitem__.return_value = mock_queryset_final
        
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        self.assertIs(resultado, mock_queryset_final)

        self.assertEqual(mock_Comunicado.objects.exclude.call_count, 1)



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
    def test_obtener_relacionados_si_falla_exists_propaga_excepcion(self, mock_Comunicado):
        """
        Test: .exists() lanza excepción (Fallo en evaluación)

        Given: Un usuario cuya relación de áreas funciona, pero la evaluación 
                de existencia (.exists()) falla en la base de datos.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: La excepción se propaga hacia arriba.
                Se verifica que exclude() llegó a ejecutarse (por estar antes en el código),
                ❗ pero la cadena se rompe y NO se llega a llamar a filter().
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()

        usuario.areas_interes.all.return_value = mock_areas_queryset
        mock_areas_queryset.exists.side_effect = RuntimeError("Conexión perdida durante .exists()")

        mock_exclude = MagicMock()
        mock_Comunicado.objects.exclude.return_value = mock_exclude

        with self.assertRaises(RuntimeError) as context:
            ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)
        
        self.assertEqual(str(context.exception), "Conexión perdida durante .exists()")

        mock_Comunicado.objects.exclude.assert_called_once_with(id=1)

        mock_exclude.filter.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_si_falla_exclude_inicial_propaga_excepcion(self, mock_Comunicado):
        """
        Test: Error en ORM base (exclude() lanza excepción)

        Given: Un ID de comunicado y un usuario.
        When: Comunicado.objects.exclude() falla (ej. DatabaseError).
        Then: La excepción se propaga hacia arriba.
                ❗ No se llama a .exists() ni a .filter().
                Se verifica que el servicio muere en el primer contacto con el ORM.
        """
        usuario = MagicMock()
        comunicado_actual_id = 123

        error_orm = Exception("Fallo de conexión al motor de base de datos")
        mock_Comunicado.objects.exclude.side_effect = error_orm

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, comunicado_actual_id)
        
        self.assertEqual(str(context.exception), "Fallo de conexión al motor de base de datos")

        mock_Comunicado.objects.exclude.assert_called_once_with(id=comunicado_actual_id)

        usuario.areas_interes.all.return_value.exists.assert_not_called()

        mock_Comunicado.objects.exclude.return_value.filter.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_si_falla_filter_propaga_excepcion(self, mock_Comunicado):
        """
        Test: .filter() lanza excepción (Fallo en filtrado específico)

        Given: Un usuario con áreas de interés y un queryset_base válido.
        When: Se intenta aplicar el .filter() y este falla (ej. FieldError).
        Then: La excepción se propaga hacia arriba.
                ❗ No se llega a ejecutar distinct(), order_by() ni slicing.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_exclude = MagicMock()
        mock_Comunicado.objects.exclude.return_value = mock_exclude

        error_db = Exception("Error en los parámetros de filtrado SQL")
        mock_exclude.filter.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)
        
        self.assertEqual(str(context.exception), "Error en los parámetros de filtrado SQL")

        mock_exclude.filter.assert_called_once()

        mock_exclude.filter.return_value.distinct.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_si_falla_distinct_propaga_excepcion(self, mock_Comunicado):
        """
        Test: .distinct() lanza excepción

        Given: Un usuario con áreas y un flujo de filtrado iniciado.
        When: Se llega al paso de .distinct() y ocurre un error de base de datos.
        Then: La excepción se propaga hacia arriba.
                ❗ No se llega a ejecutar el ordenamiento ni el límite (slice).
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_filter = MagicMock()
        mock_Comunicado.objects.exclude.return_value.filter.return_value = mock_filter
        
        error_db = Exception("Error SQL: DISTINCT no permitido en campos de este tipo")
        mock_filter.distinct.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)
        
        self.assertEqual(str(context.exception), "Error SQL: DISTINCT no permitido en campos de este tipo")

        mock_filter.distinct.assert_called_once()
        mock_filter.distinct.return_value.order_by.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_si_falla_order_by_propaga_excepcion(self, mock_Comunicado):
        """
        Test: .order_by() lanza excepción (Fallo de clasificación)

        Given: Un usuario con áreas de interés y una cadena de consulta válida.
        When: Se llega al método .order_by() y este falla.
        Then: La excepción se propaga hacia arriba.
                ❗ No se llega a intentar el slicing final [:3].
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_distinct = MagicMock()
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value = mock_distinct
        
        error_db = Exception("Error de ordenación: campo '-fecha_emision' no válido")
        mock_distinct.order_by.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)
        
        self.assertEqual(str(context.exception), "Error de ordenación: campo '-fecha_emision' no válido")

        mock_distinct.order_by.assert_called_once_with('-fecha_emision')

        mock_distinct.order_by.return_value.__getitem__.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_si_falla_slicing_propaga_excepcion(self, mock_Comunicado):
        """
        Test: slicing [:3] falla (Fallo en límite de resultados)

        Given: Un flujo de consulta perfectamente construido hasta el ordenamiento.
        When: Se intenta aplicar el slicing [:3] y el ORM/Base de datos falla.
        Then: La excepción se propaga hacia arriba.
                Se valida que el fallo ocurre en el último eslabón de la cadena.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_order_by = MagicMock()
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        error_db = Exception("Error de sintaxis SQL en cláusula LIMIT")
        mock_order_by.__getitem__.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)
        
        self.assertEqual(str(context.exception), "Error de sintaxis SQL en cláusula LIMIT")

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 3, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_obedece_a_exists_aunque_el_contenido_este_vacio(self, mock_Comunicado):
        # [2026-03-04]
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
    def test_obtener_relacionados_funciona_con_menos_de_tres_resultados(self, mock_Comunicado):
        """
        Test: Queryset devuelve menos de 3 resultados (Caso Límite)

        Given: Un usuario y un comunicado actual donde solo hay 1 relacionado disponible.
        When: Se aplica el slicing [:3].
        Then: El servicio debe retornar el único comunicado encontrado sin errores.
            Se valida que el slicing del ORM maneja correctamente conjuntos pequeños.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        resultado_insuficiente = ['el_unico_relacionado']
        
        mock_order_by = MagicMock()
        mock_order_by.__getitem__.return_value = resultado_insuficiente
        
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado, resultado_insuficiente)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 3, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_limita_a_tres_aunque_existan_muchos_resultados(self, mock_Comunicado):
        """
        Test: Queryset devuelve más de 3 resultados

        Given: Un usuario y una base de datos con 10 comunicados relacionados.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: El resultado debe contener exactamente 3 elementos.
                Se confirma que el slicing [:3] recorta el excedente.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        resultado_limitado = ['relacionado_1', 'relacionado_2', 'relacionado_3']
        
        mock_order_by = MagicMock()

        mock_order_by.__getitem__.return_value = resultado_limitado
        
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        self.assertEqual(len(resultado), 3)
        self.assertEqual(resultado, resultado_limitado)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 3, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_devuelve_exactamente_tres_resultados_cuando_existen(self, mock_Comunicado):
        """
        Test: Queryset devuelve exactamente 3

        Given: Un usuario con áreas y una base de datos con 3 comunicados relacionados 
            (además del que se está leyendo).
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: Se debe retornar una lista/queryset con exactamente esos 3 elementos.
            Se confirma que el límite coincide con la disponibilidad total de datos.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        resultado_exacto = ['relacionado_1', 'relacionado_2', 'relacionado_3']
        
        mock_order_by = MagicMock()
        mock_order_by.__getitem__.return_value = resultado_exacto
        
        mock_Comunicado.objects.exclude.return_value.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        self.assertEqual(len(resultado), 3)
        self.assertEqual(resultado, resultado_exacto)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 3, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_aplica_exclude_independientemente_de_las_areas(self, mock_Comunicado):
        """
        Test: Verificar que exclude se aplica SIEMPRE

        Given: Dos escenarios: uno con áreas y otro sin áreas.
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: En ambos casos, el primer método llamado del ORM debe ser .exclude().
            Se valida que la exclusión es la base inamovible de la consulta.
        """
        id_actual = 77

        usuario_con_areas = MagicMock()
        usuario_con_areas.areas_interes.all.return_value.exists.return_value = True
        
        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario_con_areas, id_actual)

        mock_Comunicado.objects.exclude.assert_any_call(id=id_actual)
        
        mock_Comunicado.objects.reset_mock()

        usuario_sin_areas = MagicMock()
        usuario_sin_areas.areas_interes.all.return_value.exists.return_value = False
        
        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario_sin_areas, id_actual)

        mock_Comunicado.objects.exclude.assert_any_call(id=id_actual)



    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_ejecuta_solo_una_rama_logica_exclusivamente(self, mock_Comunicado, mock_AreaInteres):
        """
        Test: Verificar que no mezcla ramas

        Given: Un usuario con áreas de interés (exists() = True).
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: Solo se debe ejecutar el filtro por áreas del usuario (Rama A).
            ❗ NO debe llamarse al filtro de fallback (TODOS_HERMANOS) (Rama B).
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()
        mock_areas_queryset.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas_queryset

        mock_exclude = MagicMock()
        mock_filter = MagicMock()
        mock_Comunicado.objects.exclude.return_value = mock_exclude
        mock_exclude.filter.return_value = mock_filter

        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        mock_exclude.filter.assert_called_once_with(
            areas_interes__in=mock_areas_queryset
        )

        for call in mock_exclude.filter.call_args_list:
            args, kwargs = call
            self.assertNotIn('areas_interes__nombre_area', kwargs, 
                            "Se ejecutó el filtro de fallback cuando el usuario tenía áreas")
            


    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_relacionados_usa_constante_exacta_en_fallback(self, mock_Comunicado, mock_AreaInteres):
        """
        Test: Verificar argumento correcto en fallback

        Given: Un usuario sin áreas de interés (exists() = False).
        When: Se llama a obtener_comunicados_relacionados_usuario.
        Then: El filtro 'areas_interes__nombre_area' debe recibir exactamente 
            el valor de la constante AreaInteres.NombreArea.TODOS_HERMANOS.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = False

        VALOR_CONSTANTE = "AREA_PARA_TODOS"
        mock_AreaInteres.NombreArea.TODOS_HERMANOS = VALOR_CONSTANTE

        mock_exclude = MagicMock()
        mock_Comunicado.objects.exclude.return_value = mock_exclude

        ComunicadoService.obtener_comunicados_relacionados_usuario(usuario, 1)

        mock_exclude.filter.assert_called_once_with(
            areas_interes__nombre_area=VALOR_CONSTANTE
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