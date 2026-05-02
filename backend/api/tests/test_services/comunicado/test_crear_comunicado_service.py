from django.test import TestCase
from unittest.mock import Mock, PropertyMock, patch, MagicMock

from django.core.exceptions import PermissionDenied

from api.servicios.comunicado.comunicado_service import ComunicadoService
from api.models import CuerpoPertenencia


class ComunicadoServiceTests(TestCase):

    # -----------------------------------------------------------------------------------------------------
    # CREAR COMUNICADO 
    # -----------------------------------------------------------------------------------------------------

    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_flujo_completo_correcto_sin_areas_sin_podcast(self, mock_create, mock_on_commit):
        """
        Test: Flujo completo correcto (sin áreas, sin podcast)

        Given: Un usuario válido.
                Un payload sin 'areas_interes' y con generar_podcast=False.
        When: Se llama a create_comunicado del servicio.
        Then: Se verifican permisos.
                Se crea el comunicado en BD asociado al autor.
                NO se asocian áreas de interés.
                Se notifica a Telegram con una lista de áreas vacía.
                Se registra en transaction.on_commit el embedding.
                NO se registra la tarea del podcast.
                Se retorna el objeto creado.
        """
        servicio = ComunicadoService()

        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        usuario = MagicMock()

        data_validada = {
            'titulo': 'Nuevo comunicado',
            'contenido': 'Texto importante',
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 1
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        resultado = servicio.create_comunicado(usuario, data_validada.copy())

        servicio._verificar_permisos.assert_called_once_with(usuario)

        mock_create.assert_called_once_with(autor=usuario, **data_validada)

        mock_comunicado.areas_interes.set.assert_not_called()

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, [])

        mock_on_commit.assert_called_once()

        self.assertEqual(resultado, mock_comunicado)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_flujo_con_areas_interes_asigna_m2m_y_notifica(self, mock_create, mock_on_commit):
        """
        Test: Flujo con áreas_interes

        Given: Un usuario válido.
                Un payload que incluye una lista de IDs en 'areas_interes'.
        When: Se llama a create_comunicado.
        Then: Las áreas se extraen del payload y NO se pasan al create().
                Se llama al método .set() del manager M2M con las áreas.
                Se llama a _notificar_telegram pasando las áreas correctas.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        usuario = MagicMock()

        areas_lista = [1, 2]
        data_validada = {
            'titulo': 'Comunicado segmentado',
            'contenido': 'Texto para ciertas áreas',
            'areas_interes': areas_lista,
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 1
        mock_comunicado.generar_podcast = False

        mock_m2m_manager = MagicMock()
        mock_comunicado.areas_interes = mock_m2m_manager
        
        mock_create.return_value = mock_comunicado

        resultado = servicio.create_comunicado(usuario, data_validada.copy())

        mock_create.assert_called_once_with(
            autor=usuario, 
            titulo='Comunicado segmentado',
            contenido='Texto para ciertas áreas',
            generar_podcast=False
        )

        mock_m2m_manager.set.assert_called_once_with(areas_lista)

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, areas_lista)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_flujo_con_podcast_activado_registra_ambas_tareas_en_commit(self, mock_create, mock_on_commit):
        """
        Test: Flujo con podcast activado

        Given: Un usuario con permisos.
                Un payload donde 'generar_podcast' es True.
        When: Se llama a create_comunicado.
        Then: Se deben registrar dos llamadas a transaction.on_commit.
                La primera para la generación del embedding.
                La segunda específicamente para la generación del podcast.
                Se verifica que ambas lambdas se registran correctamente.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado con Audio',
            'generar_podcast': True
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 42
        mock_comunicado.generar_podcast = True
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_validada.copy())

        self.assertEqual(mock_on_commit.call_count, 2)

        with patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async') as mock_emb, \
            patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_podcast_async') as mock_pod:

            func_embedding = mock_on_commit.call_args_list[0][0][0]
            func_embedding()
            mock_emb.assert_called_once_with(mock_comunicado.id)

            func_podcast = mock_on_commit.call_args_list[1][0][0]
            func_podcast()
            mock_pod.assert_called_once_with(mock_comunicado.id)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_create_comunicado_inyecta_autor_proporcionado_ignora_suplantacion(self, mock_create):
        """
        Test: Verificar uso de autor=usuario

        Given: Un usuario autenticado (autor_real).
                Un payload de datos que malintencionadamente intenta incluir 
                un campo 'autor' o 'autor_id' (suplantación).
        When: Se llama al método create_comunicado.
        Then: El servicio debe llamar a Comunicado.objects.create usando 
                explícitamente autor=autor_real.
                Se garantiza que la identidad del autor proviene del contexto 
                del sistema y no del payload del usuario.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        autor_real = MagicMock()
        data_validada = {
            'titulo': 'Título legal',
            'autor': 999,
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(autor_real, data_validada.copy())

        args, kwargs = mock_create.call_args
        
        self.assertEqual(kwargs['autor'], autor_real)
        self.assertNotEqual(kwargs['autor'], 999)

        self.assertEqual(kwargs['titulo'], 'Título legal')



    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_areas_interes_se_elimina_de_data_validada_antes_del_create(self, mock_create):
        """
        Test: Verificar que data_validada se modifica correctamente

        Given: Un usuario con permisos.
                Un diccionario data_validada que contiene 'areas_interes'.
        When: Se llama a create_comunicado.
        Then: El campo 'areas_interes' debe ser extraído (pop) del diccionario.
                El método Comunicado.objects.create NO debe recibir 'areas_interes' 
                como argumento, evitando errores de integridad del ORM.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado de Prueba',
            'contenido': 'Contenido',
            'areas_interes': [1, 2, 3],
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_validada)

        args, kwargs = mock_create.call_args

        self.assertNotIn('areas_interes', kwargs, 
            "Error: 'areas_interes' se pasó al método create y debería haber sido extraído.")

        self.assertEqual(kwargs['titulo'], 'Comunicado de Prueba')
        self.assertEqual(kwargs['autor'], usuario)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_verificar_permisos_lanza_excepcion_detiene_ejecucion_total(self, mock_create, mock_on_commit):
        """
        Test: Permisos -> _verificar_permisos lanza PermissionDenied

        Given: Un usuario que no tiene los permisos necesarios.
                El método _verificar_permisos está configurado para lanzar PermissionDenied.
        When: Se intenta llamar a create_comunicado.
        Then: La excepción PermissionDenied se propaga.
                Garantiza que NO se llama a Comunicado.objects.create (no hay persistencia).
                Garantiza que NO se llama a _notificar_telegram.
                Garantiza que NO se registra ninguna tarea en on_commit.
        """
        servicio = ComunicadoService()

        servicio._verificar_permisos = MagicMock(side_effect=PermissionDenied("No tienes permiso"))
        servicio._notificar_telegram = MagicMock()
        
        usuario_no_autorizado = MagicMock()
        data_validada = {'titulo': 'Intento fallido', 'generar_podcast': True}

        with self.assertRaises(PermissionDenied):
            servicio.create_comunicado(usuario_no_autorizado, data_validada)

        mock_create.assert_not_called()

        servicio._notificar_telegram.assert_not_called()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_create_lanza_excepcion_y_detiene_flujo_posterior(self, mock_create, mock_on_commit):
        """
        Test: Errores en creación -> Comunicado.objects.create lanza excepción

        Given: Un usuario con permisos.
        When: El método Comunicado.objects.create lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga hacia arriba.
                ❗ NO se llama al método de notificación a Telegram.
                ❗ NO se registran lambdas en transaction.on_commit.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {'titulo': 'Comunicado Fallido', 'generar_podcast': True}

        mensaje_error = "Error de integridad o conexión en BD"
        mock_create.side_effect = Exception(mensaje_error)

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_create.assert_called_once()

        servicio._notificar_telegram.assert_not_called()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_set_areas_interes_lanza_excepcion_y_detiene_flujo_posterior(self, mock_create, mock_on_commit):
        """
        Test: Errores en asignación de áreas -> .areas_interes.set lanza excepción

        Given: Un usuario con permisos y un payload con áreas.
                El comunicado se crea correctamente.
        When: El método .set() de la relación areas_interes falla.
        Then: La excepción se propaga hacia arriba.
                ❗ NO se llama al método de notificación a Telegram.
                ❗ NO se registran las tareas asíncronas en on_commit.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado con Áreas Fallidas',
            'areas_interes': [1, 2],
            'generar_podcast': True
        }

        mock_comunicado = MagicMock()
        mock_m2m = MagicMock()
        mensaje_error = "Fallo en tabla intermedia M2M"
        mock_m2m.set.side_effect = Exception(mensaje_error)
        
        mock_comunicado.areas_interes = mock_m2m
        mock_create.return_value = mock_comunicado

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_create.assert_called_once()
        mock_m2m.set.assert_called_once()

        servicio._notificar_telegram.assert_not_called()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_notificar_telegram_lanza_excepcion_y_detiene_on_commit(self, mock_create, mock_on_commit):
        """
        Test: Errores en notificación -> _notificar_telegram lanza excepción

        Given: Un usuario con permisos.
                El comunicado y sus áreas se procesan correctamente.
        When: El método _notificar_telegram lanza una excepción.
        Then: La excepción se propaga hacia arriba.
                ❗ NO se registran las tareas en transaction.on_commit.
                Nota: Al no haber manejo de errores, esto provocará un rollback 
                del comunicado en la base de datos debido al decorador @transaction.atomic.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        
        usuario = MagicMock()
        data_validada = {'titulo': 'Comunicado con Telegram Roto', 'generar_podcast': True}

        mock_comunicado = MagicMock()
        mock_create.return_value = mock_comunicado

        mensaje_error = "Error de conexión con la API de Telegram"
        servicio._notificar_telegram = MagicMock(side_effect=Exception(mensaje_error))

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_create.assert_called_once()
        servicio._notificar_telegram.assert_called_once()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_on_commit_lanza_excepcion_y_propaga_error(self, mock_create, mock_on_commit):
        """
        Test: Errores en transaction.on_commit -> lanza excepción

        Given: Un usuario con permisos y datos válidos (generar_podcast=True).
                El comunicado se crea y se notifica correctamente.
        When: La primera llamada a transaction.on_commit (para el embedding) falla.
        Then: La excepción se propaga hacia arriba.
                ❗ NO se llega a procesar la lógica del podcast (segundo on_commit).
                Garantiza que el flujo se detiene ante fallos de infraestructura de transacciones.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado con Fallo en Commit',
            'generar_podcast': True 
        }
        
        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = True
        mock_create.return_value = mock_comunicado

        mensaje_error = "Error al registrar hook de on_commit"
        mock_on_commit.side_effect = Exception(mensaje_error)

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        self.assertEqual(mock_on_commit.call_count, 1)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_areas_interes_ausente_usa_lista_vacia_por_defecto_y_no_rompe(self, mock_create, mock_on_commit):
        """
        Test: Casos límite -> areas_interes no viene en data_validada

        Given: Un usuario con permisos.
                Un payload donde la clave 'areas_interes' no existe en el diccionario.
        When: Se llama al método create_comunicado.
        Then: El servicio no debe lanzar KeyError.
                Se debe usar una lista vacía [] por defecto para las áreas.
                NO se debe llamar a comunicado.areas_interes.set().
                Se llama a _notificar_telegram con la lista vacía.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_parcial = {
            'titulo': 'Comunicado sin áreas',
            'generar_podcast': False
        }
        
        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        resultado = servicio.create_comunicado(usuario, data_parcial)

        mock_create.assert_called_once()

        mock_comunicado.areas_interes.set.assert_not_called()

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, [])
        
        self.assertEqual(resultado, mock_comunicado)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_areas_interes_es_none_no_ejecuta_set_y_continua_flujo(self, mock_create, mock_on_commit):
        """
        Test: areas_interes = None

        Given: Un usuario con permisos.
                Un payload donde 'areas_interes' es explícitamente None.
        When: Se llama al método create_comunicado.
        Then: El valor None se extrae correctamente.
                La condición 'if areas:' evalúa a False.
                ❗ NO se llama a comunicado.areas_interes.set().
                Se llama a _notificar_telegram pasando None (o el valor extraído).
                El flujo termina correctamente.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_con_none = {
            'titulo': 'Comunicado con None',
            'areas_interes': None,
            'generar_podcast': False
        }
        
        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_con_none)

        mock_create.assert_called_once()

        mock_comunicado.areas_interes.set.assert_not_called()

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, None)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_generar_podcast_false_no_registra_segundo_on_commit(self, mock_create, mock_on_commit):
        """
        Test: generar_podcast = False

        Given: Un usuario con permisos.
                Un payload donde 'generar_podcast' es False.
        When: Se llama al método create_comunicado.
        Then: Se debe registrar exactamente UN transaction.on_commit (para el embedding).
                NO se debe registrar un segundo on_commit para el podcast.
                Se garantiza que la lógica condicional de tareas asíncronas es correcta.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado solo texto',
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 100
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_validada)

        self.assertEqual(mock_on_commit.call_count, 1)

        with patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async') as mock_emb:
            func_registrada = mock_on_commit.call_args[0][0]
            func_registrada()

            mock_emb.assert_called_once_with(mock_comunicado.id)

        with patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_podcast_async') as mock_pod:
            mock_pod.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_generar_podcast_ausente_en_objeto_lanza_attribute_error(self, mock_create, mock_on_commit):
        """
        Test: generar_podcast no existe en el objeto

        Given: Un usuario con permisos.
                El ORM crea un objeto comunicado que, por error de esquema o mock,
                no posee el atributo 'generar_podcast'.
        When: Se llama al método create_comunicado.
        Then: Se debe lanzar un AttributeError al intentar evaluar la condición final.
                Se garantiza que el servicio no silencia errores de estructura del modelo.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {'titulo': 'Test de Atributo Faltante'}

        mock_comunicado_incompleto = MagicMock(spec=[]) 
        
        mock_create.return_value = mock_comunicado_incompleto

        with self.assertRaises(AttributeError):
            servicio.create_comunicado(usuario, data_validada)

        mock_create.assert_called_once()
        servicio._notificar_telegram.assert_called_once()

        self.assertEqual(mock_on_commit.call_count, 1)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_on_commit_recibe_objetos_llamables_no_resultados(self, mock_create, mock_on_commit):
        """
        Test: Verificar que on_commit recibe funciones (no ejecución inmediata)

        Given: Un flujo de creación de comunicado estándar.
        When: El servicio registra las tareas en transaction.on_commit.
        Then: El primer argumento de cada llamada a on_commit debe ser un 
                objeto 'callable' (lambda o función).
                Se garantiza que no se están ejecutando las tareas de embedding 
                o podcast de forma síncrona durante la creación.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = True
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(MagicMock(), {'generar_podcast': True})

        self.assertEqual(mock_on_commit.call_count, 2)

        for i, call in enumerate(mock_on_commit.call_args_list):
            func_registrada = call[0][0]

            self.assertTrue(
                callable(func_registrada), 
                f"El registro {i} en on_commit no es un callable. ¿Se ejecutó por error?"
            )



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_verificar_orden_logico_de_pasos_del_servicio(self, mock_create, mock_on_commit):
        """
        Test: Verificar orden lógico de llamadas

        Given: Un flujo de creación con todos los elementos (áreas y podcast).
        When: Se ejecuta create_comunicado.
        Then: Se debe respetar estrictamente el orden:
                1. Verificar permisos (Seguridad primero).
                2. Crear objeto en BD (Persistencia).
                3. Asignar áreas M2M (Relaciones).
                4. Notificar a Telegram (Comunicación).
                5. Registrar tareas en on_commit (Post-procesamiento).
        """
        servicio = ComunicadoService()
        manager = Mock()

        servicio._verificar_permisos = manager.verificar_permisos
        servicio._notificar_telegram = manager.notificar_telegram
        mock_create.side_effect = lambda **kwargs: manager.create(**kwargs)
        mock_on_commit.side_effect = lambda func: manager.on_commit(func)
        mock_comunicado = MagicMock(name="Comunicado_Mock")
        mock_comunicado.generar_podcast = True
        mock_comunicado.areas_interes.set = manager.set_areas
        manager.create.return_value = mock_comunicado

        data_validada = {
            'titulo': 'Test de Orden',
            'areas_interes': [1],
            'generar_podcast': True
        }

        servicio.create_comunicado(MagicMock(), data_validada)

        nombres_llamadas = [call[0] for call in manager.mock_calls]

        orden_esperado = [
            'verificar_permisos',
            'create',
            'set_areas',
            'notificar_telegram',
            'on_commit',
            'on_commit'
        ]

        self.assertEqual(nombres_llamadas, orden_esperado, 
            f"El orden de ejecución es incorrecto. Se ejecutó: {nombres_llamadas}")