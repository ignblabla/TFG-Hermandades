from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
import sys
from io import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import AreaInteres, Comunicado, CuerpoPertenencia, Hermano, HermanoCuerpo
from api.servicios.comunicado.creacion_comunicado_service import ComunicadoService


class CrearComunicadoServiceTest(TestCase):

    def setUp(self):
        """
        Configuración inicial para testear el servicio de Comunicados.
        """
        self.ahora = timezone.now()

        # ---------------------------------------------------------------------
        # 1. ÁREAS DE INTERÉS (Para probar notificaciones de Telegram)
        # ---------------------------------------------------------------------
        self.area_con_telegram = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS,
            telegram_channel_id="-100987654321"
        )
        
        self.area_sin_telegram = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.JUVENTUD,
            telegram_channel_id=None
        )

        # ---------------------------------------------------------------------
        # 2. CUERPOS DE PERTENENCIA
        # ---------------------------------------------------------------------
        self.cuerpo_junta = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )

        # ---------------------------------------------------------------------
        # 3. USUARIOS (Roles para probar _verificar_permisos)
        # ---------------------------------------------------------------------
        self.admin = Hermano.objects.create_user(
            dni="11111111A",
            username="11111111A",
            password="password",
            nombre="Admin",
            primer_apellido="Root",
            segundo_apellido="Test",
            email="admin@example.com",
            telefono="600000001",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1980-01-01",
            direccion="Calle Administración 1",
            codigo_postal="41001",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=True,
        )

        self.miembro_junta = Hermano.objects.create_user(
            dni="22222222B",
            username="22222222B",
            password="password",
            nombre="Vocal",
            primer_apellido="Junta",
            segundo_apellido="Test",
            email="junta@example.com",
            telefono="600000002",
            estado_civil=Hermano.EstadoCivil.CASADO,
            genero=Hermano.Genero.FEMENINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1001,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1985-05-15",
            direccion="Calle Cabildo 2",
            codigo_postal="41002",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        HermanoCuerpo.objects.create(
            hermano=self.miembro_junta,
            cuerpo=self.cuerpo_junta,
            anio_ingreso=self.ahora.year
        )

        self.usuario_base = Hermano.objects.create_user(
            dni="33333333C",
            username="33333333C",
            password="password",
            nombre="Hermano",
            primer_apellido="Raso",
            segundo_apellido="Test",
            email="base@example.com",
            telefono="600000003",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1002,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1990-10-20",
            direccion="Calle Hermandad 3",
            codigo_postal="41003",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        # ---------------------------------------------------------------------
        # 4. PAYLOADS BASE PARA TESTS
        # ---------------------------------------------------------------------
        self.imagen_dummy = SimpleUploadedFile(
            name='test_portada.jpg', 
            content=b'file_content', 
            content_type='image/jpeg'
        )

        self.payload_comunicado_valido = {
            "titulo": "Nuevo horario de misas",
            "contenido": "Se informa a todos los hermanos del nuevo horario...",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_con_telegram, self.area_sin_telegram],
            "imagen_portada": None
        }
        
        self.payload_comunicado_con_imagen = {
            "titulo": "Restauración completada",
            "contenido": "Presentamos el resultado final...",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_con_telegram],
            "imagen_portada": self.imagen_dummy
        }



    @patch('requests.post')
    def test_admin_crea_comunicado_valido_sin_excepciones_ok(self, mock_post):
        """
        Test: Admin crea comunicado con datos válidos sin restricciones de permisos

        Given: Un usuario con esAdmin = True y un diccionario de datos válidos.
        When: se llama a create_comunicado con la data_validada.
        Then: se crea el Comunicado correctamente, se asocian las áreas y no se lanzan excepciones.
        """
        data_validada = self.payload_comunicado_valido.copy()
        
        servicio = ComunicadoService() 
        
        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertIsNotNone(comunicado.id)
        self.assertEqual(comunicado.autor, self.admin)
        self.assertEqual(comunicado.titulo, "Nuevo horario de misas")
        self.assertEqual(comunicado.tipo_comunicacion, "INFORMATIVO")

        areas_asociadas = list(comunicado.areas_interes.all())
        self.assertEqual(len(areas_asociadas), 2)
        self.assertIn(self.area_con_telegram, areas_asociadas)
        self.assertIn(self.area_sin_telegram, areas_asociadas)

        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())



    @patch('requests.post')
    def test_miembro_junta_crea_comunicado_valido_sin_ser_admin_ok(self, mock_post):
        """
        Test: Miembro de la Junta crea comunicado con datos válidos aunque no sea Admin

        Given: Un usuario con esAdmin = False pero perteneciente al cuerpo JUNTA_GOBIERNO.
        When: se llama a create_comunicado con la data_validada.
        Then: se crea el Comunicado correctamente, validando que el cuerpo otorga permisos.
        """
        data_validada = self.payload_comunicado_valido.copy()

        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.miembro_junta, data_validada)

        self.assertIsNotNone(comunicado.id)
        self.assertEqual(comunicado.autor, self.miembro_junta)
        self.assertEqual(comunicado.titulo, self.payload_comunicado_valido["titulo"])

        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())
        
        self.assertTrue(mock_post.called)



    @patch('requests.post')
    def test_usuario_con_ambos_permisos_crea_comunicado_ok(self, mock_post):
        """
        Test: Usuario que es Admin Y miembro de la Junta crea comunicado

        Given: Un usuario con esAdmin = True y vinculado al cuerpo JUNTA_GOBIERNO.
        When: se llama a create_comunicado.
        Then: se crea el comunicado correctamente sin errores por redundancia de permisos.
        """
        HermanoCuerpo.objects.create(
            hermano=self.admin,
            cuerpo=self.cuerpo_junta,
            anio_ingreso=self.ahora.year
        )
        
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertIsNotNone(comunicado.id)
        self.assertEqual(comunicado.autor, self.admin)

        self.assertEqual(Comunicado.objects.count(), 1)

        self.assertEqual(mock_post.call_count, 1)



    @patch('requests.post')
    def test_usuario_sin_permisos_lanza_permission_denied_error(self, mock_post):
        """
        Test: Usuario sin esAdmin y sin pertenencia a Junta intenta crear comunicado

        Given: Un usuario (usuario_base) con esAdmin = False y sin vínculo a JUNTA_GOBIERNO.
        When: se llama a create_comunicado.
        Then: se lanza la excepción PermissionDenied y no se crea ningún registro ni notificación.
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied) as cm:
            servicio.create_comunicado(self.usuario_base, data_validada)

        self.assertEqual(str(cm.exception), "No tienes permisos para gestionar comunicados.")

        self.assertEqual(Comunicado.objects.count(), 0)

        mock_post.assert_not_called()



    @patch('requests.post')
    def test_usuario_sin_atributo_es_admin_lanza_permission_denied(self, mock_post):
        """
        Test: Usuario que carece totalmente del atributo 'esAdmin'

        Given: Un objeto de usuario que no tiene la propiedad 'esAdmin'.
        When: getattr(usuario, 'esAdmin', False) se ejecuta y el usuario no es de la Junta.
        Then: se evalúa como False y lanza PermissionDenied.
        """
        usuario_sin_attr = MagicMock()
        del usuario_sin_attr.esAdmin
        
        usuario_sin_attr.cuerpos.filter.return_value.exists.return_value = False
        
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.create_comunicado(usuario_sin_attr, data_validada)
            
        mock_post.assert_not_called()



    @patch('requests.post')
    def test_usuario_con_cuerpos_none_lanza_attribute_error(self, mock_post):
        """
        Test: Comportamiento del servicio cuando el atributo 'cuerpos' es None

        Given: Un objeto de usuario donde el atributo 'cuerpos' se ha forzado a None.
        When: El servicio intenta ejecutar .filter() sobre algo que es None.
        Then: Se produce un AttributeError, confirmando que el servicio espera un Manager válido.
        """
        usuario_erroneo = MagicMock()
        usuario_erroneo.esAdmin = False
        usuario_erroneo.cuerpos = None
        
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        with self.assertRaises(AttributeError):
            servicio.create_comunicado(usuario_erroneo, data_validada)
            
        mock_post.assert_not_called()



    @patch('requests.post')
    def test_usuario_real_sin_ninguna_pertenencia_a_cuerpos_deniega_acceso(self, mock_post):
        """
        Test: Comportamiento con un Hermano real que no está en ningún cuerpo

        Given: Un Hermano persistido en BD (usuario_base) que no tiene registros en HermanoCuerpo.
        When: El servicio evalúa usuario.cuerpos.filter(...).exists().
        Then: La consulta devuelve False (no rompe) y se lanza PermissionDenied.
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.create_comunicado(self.usuario_base, data_validada)
            
        self.assertEqual(Comunicado.objects.count(), 0)



    @patch('requests.post')
    def test_usuario_is_none_lanza_excepcion_esperada(self, mock_post):
        """
        Test: Comportamiento del servicio cuando el argumento usuario es None

        Given: Un valor None en lugar de un objeto Hermano.
        When: Se intenta verificar permisos sobre None.
        Then: Debe lanzar una excepción (AttributeError o TypeError) que impida la creación.
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        with self.assertRaises((AttributeError, TypeError)):
            servicio.create_comunicado(None, data_validada)

        self.assertEqual(Comunicado.objects.count(), 0)
        mock_post.assert_not_called()



    @patch('requests.post')
    def test_creacion_basica_comunicado_admin_datos_minimos_ok(self, mock_post):
        """
        Test: Creación básica de comunicado con datos mínimos por un Admin

        Given: Un usuario Admin y un payload con los campos obligatorios.
        When: se llama a create_comunicado del servicio.
        Then: el comunicado se persiste en BD, el autor es el admin y se devuelve la instancia.
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertIsNotNone(comunicado.id, "El comunicado debería tener un ID tras persistirse.")
        self.assertIsInstance(comunicado, Comunicado, "El servicio debe devolver una instancia del modelo Comunicado.")

        self.assertEqual(comunicado.autor, self.admin, "El autor del comunicado debe coincidir con el usuario que lo creó.")

        self.assertEqual(comunicado.titulo, data_validada["titulo"])
        self.assertEqual(comunicado.tipo_comunicacion, data_validada["tipo_comunicacion"])

        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())

        self.assertTrue(mock_post.called)



    @patch('requests.post')
    def test_creacion_basica_comunicado_miembro_junta_datos_validados_ok(self, mock_post):
        """
        Test: Creación de comunicado por un miembro de la Junta (no admin)

        Given: Un usuario con esAdmin = False pero miembro de JUNTA_GOBIERNO.
        When: se llama a create_comunicado con datos válidos.
        Then: el comunicado se crea correctamente, asignando al vocal como autor.
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.miembro_junta, data_validada)

        self.assertIsNotNone(comunicado.id)
        self.assertIsInstance(comunicado, Comunicado)

        self.assertEqual(comunicado.autor, self.miembro_junta)
        self.assertFalse(comunicado.autor.esAdmin)
        
        self.assertEqual(comunicado.titulo, data_validada["titulo"])

        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())

        self.assertTrue(mock_post.called)



    @patch('requests.post')
    def test_creacion_comunicado_sin_areas_interes_no_falla_y_no_crea_relaciones_ok(self, mock_post):
        """
        Test: Creación de comunicado con lista de áreas de interés vacía

        Given: Un payload válido donde 'areas_interes' es una lista vacía [].
        When: se llama a create_comunicado.
        Then: el comunicado se crea correctamente, pero no tiene relaciones ManyToMany asociadas.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = []
        
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertIsNotNone(comunicado.id)
        
        self.assertEqual(comunicado.areas_interes.count(), 0)

        mock_post.assert_not_called()

        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())



    @patch('requests.post')
    def test_creacion_comunicado_con_multiples_areas_validas_se_asocian_correctamente(self, mock_post):
        """
        Test: Creación de comunicado con múltiples áreas de interés

        Given: Un payload con una lista de INSTANCIAS de áreas existentes.
        When: se llama a create_comunicado.
        Then: el comunicado se crea y la tabla intermedia refleja exactamente esas relaciones.
        """
        areas_instancias = [self.area_con_telegram, self.area_sin_telegram]
        
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = areas_instancias
        
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertEqual(comunicado.areas_interes.count(), 2)

        areas_asociadas_ids = list(comunicado.areas_interes.values_list('id', flat=True))
        self.assertIn(self.area_con_telegram.id, areas_asociadas_ids)
        self.assertIn(self.area_sin_telegram.id, areas_asociadas_ids)

        self.assertTrue(
            Comunicado.areas_interes.through.objects.filter(
                comunicado_id=comunicado.id, 
                areainteres_id=self.area_con_telegram.id
            ).exists()
        )

        self.assertTrue(mock_post.called)



    @patch('requests.post')
    def test_creacion_comunicado_con_areas_duplicadas_se_limpian_correctamente(self, mock_post):
        """
        Test: Envío de áreas de interés duplicadas en el payload

        Given: Un payload con la misma instancia de área repetida [area A, area A].
        When: se llama a create_comunicado.
        Then: el comunicado se crea con una única relación hacia esa área (sin duplicados en BD).
        """
        area_duplicada = [self.area_con_telegram, self.area_con_telegram]
        
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = area_duplicada
        
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertEqual(comunicado.areas_interes.count(), 1)

        self.assertEqual(comunicado.areas_interes.first(), self.area_con_telegram)

        conteo_intermedia = Comunicado.areas_interes.through.objects.filter(
            comunicado_id=comunicado.id, 
            areainteres_id=self.area_con_telegram.id
        ).count()
        self.assertEqual(conteo_intermedia, 1)

        self.assertEqual(mock_post.call_count, 1)



    @patch('requests.post')
    def test_usuario_sin_permisos_no_crea_nada_y_hace_rollback_ok(self, mock_post):
        """
        Test: Intento de creación por usuario sin permisos (Caso Negativo)

        Given: Un usuario (usuario_base) que no es Admin ni Junta.
        When: se llama a create_comunicado.
        Then: 
            1. Se lanza PermissionDenied.
            2. No se crea ningún registro en la tabla Comunicado (Rollback/No persistencia).
            3. No se llama al método de notificación (mock_post no ejecutado).
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.create_comunicado(self.usuario_base, data_validada)

        self.assertEqual(Comunicado.objects.count(), 0)

        mock_post.assert_not_called()



    @patch('requests.post')
    def test_creacion_comunicado_con_titulo_null_lanza_error_y_no_persiste(self, mock_post):
        """
        Test: Intento de creación con título como None (campo obligatorio)

        Given: Un payload donde el 'titulo' es None.
        When: se llama a create_comunicado.
        Then: 
            1. Se lanza un IntegrityError por la restricción NOT NULL de la BD.
            2. El registro no se crea.
            3. No se envía notificación.
        """
        data_erronea = self.payload_comunicado_valido.copy()
        data_erronea['titulo'] = None 
        
        servicio = ComunicadoService()

        with self.assertRaises(IntegrityError):
            servicio.create_comunicado(self.admin, data_erronea)

        self.assertEqual(Comunicado.objects.count(), 0)

        mock_post.assert_not_called()



    @patch('requests.post')
    def test_creacion_comunicado_con_areas_inexistentes_lanza_error_orm(self, mock_post):
        """
        Test: Comportamiento del servicio ante objetos no guardados en BD.

        Given: Una instancia de área que no existe en la base de datos.
        When: Se llama a create_comunicado y ejecuta .set().
        Then: Django ORM lanza ValueError protegiendo la integridad relacional.
        """
        area_valida = self.area_con_telegram

        area_inexistente = AreaInteres(id=99999, nombre_area=AreaInteres.NombreArea.PATRIMONIO)

        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = [area_valida, area_inexistente]
        
        servicio = ComunicadoService()

        with self.assertRaises(ValueError):
            servicio.create_comunicado(self.admin, data_validada)

        mock_post.assert_not_called()



    @patch('requests.post')
    def test_error_en_telegram_no_hace_rollback_del_comunicado(self, mock_post):
        """
        Test: Resiliencia del servicio ante fallos de la API de Telegram

        Given: Un payload válido pero una API de Telegram que devuelve un error (ej. Timeout).
        When: se llama a create_comunicado.
        Then: 
            1. El comunicado se crea y persiste correctamente en la BD.
            2. La excepción de Telegram se captura internamente (no rompe el servicio).
            3. El servicio devuelve la instancia del comunicado.
        """
        mock_post.side_effect = Exception("Error de conexión con Telegram")
        
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertIsNotNone(comunicado.id)
        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())

        self.assertTrue(mock_post.called)

        self.assertEqual(comunicado.autor, self.admin)



    @patch('requests.post')
    @patch('api.models.Comunicado.objects.create')
    def test_error_en_creacion_db_hace_rollback_y_no_notifica_telegram(self, mock_create, mock_post):
        """
        Test: Error de base de datos durante el .create()

        Given: Un fallo inesperado en la base de datos (DatabaseError) al crear el objeto.
        When: Se llama a create_comunicado.
        Then: 
            1. Se lanza la excepción de base de datos.
            2. El flujo se interrumpe y NO se llama a _notificar_telegram.
            3. No se envía nada por la API de Telegram.
        """
        from django.db import DatabaseError
        mock_create.side_effect = DatabaseError("Conexión perdida con la base de datos")
        
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()

        with self.assertRaises(DatabaseError):
            servicio.create_comunicado(self.admin, data_validada)

        mock_post.assert_not_called()



    @patch('requests.post')
    def test_notificar_telegram_no_se_ejecuta_si_no_hay_areas_interes(self, mock_post):
        """
        Test: Filtrado de notificaciones cuando el comunicado no tiene áreas

        Given: Un comunicado recién creado con areas_interes = [].
        When: El servicio llega a la ejecución de _notificar_telegram.
        Then: 
            1. El QuerySet de áreas con telegram resulta vacío.
            2. El conjunto de canales_a_enviar queda vacío.
            3. No se realiza ninguna llamada a requests.post.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = []
        
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertEqual(comunicado.areas_interes.count(), 0)
        
        mock_post.assert_not_called()



    @patch('requests.post')
    def test_no_notifica_si_las_areas_no_tienen_channel_id_configurado(self, mock_post):
        """
        Test: Filtrado de áreas con IDs de canal nulos o vacíos

        Given: Un comunicado dirigido a un área que tiene telegram_channel_id = None.
        When: El servicio intenta notificar.
        Then: 
            1. El QuerySet filtra el área por no tener canal válido.
            2. canales_a_enviar resulta vacío.
            3. No se realiza ninguna llamada a requests.post.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = [self.area_sin_telegram]
        
        servicio = ComunicadoService()

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertEqual(comunicado.areas_interes.count(), 1)
        
        mock_post.assert_not_called()



    @patch('requests.post')
    def test_no_notifica_si_el_channel_id_es_un_string_vacio(self, mock_post):
        """
        Test: Filtrado de áreas con telegram_channel_id igual a string vacío ('')

        Given: Un área con telegram_channel_id = '' (string vacío).
        When: Se llama a create_comunicado asociando esta área.
        Then: 
            1. El filtro .exclude(telegram_channel_id__exact='') descarta el área.
            2. No se realiza ninguna petición POST a Telegram.
        """
        area_vacia = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.CARIDAD,
            telegram_channel_id=''
        )
        
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = [area_vacia]
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        mock_post.assert_not_called()



    @patch('requests.post')
    def test_varias_areas_con_mismo_canal_envian_una_sola_notificacion(self, mock_post):
        """
        Test: Evitar spam cuando varias áreas comparten canal
        """
        canal_compartido = "-100987654321"

        self.area_con_telegram.telegram_channel_id = canal_compartido
        self.area_con_telegram.save()
        
        area_extra = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.CULTOS_FORMACION,
            telegram_channel_id=canal_compartido
        )

        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = [self.area_con_telegram, area_extra]
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertEqual(mock_post.call_count, 1, "Se debería haber enviado un solo mensaje al canal común.")

        _, kwargs = mock_post.call_args
        
        payload_enviado = kwargs.get('json') or kwargs.get('data')
        
        self.assertIsNotNone(payload_enviado, "No se encontró payload en la llamada a requests.post")
        self.assertEqual(str(payload_enviado.get('chat_id')), canal_compartido)



    @patch('requests.post')
    def test_envio_de_ids_numericos_en_lugar_de_objetos_lanza_error_de_atributo(self, mock_post):
        """
        Test: Inconsistencia semántica en areas_interes

        Given: Un payload donde 'areas_interes' contiene IDs numéricos [1, 2] 
            en lugar de instancias de AreaInteres.
        When: El servicio intenta ejecutar el list comprehension [a.id for a in areas_ids].
        Then: Se lanza AttributeError porque los 'int' no tienen el atributo '.id'.
        """
        ids_puros = [self.area_con_telegram.id, self.area_sin_telegram.id]
        
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['areas_interes'] = ids_puros
        
        servicio = ComunicadoService()

        with self.assertRaises(AttributeError):
            servicio.create_comunicado(self.admin, data_validada)

        mock_post.assert_not_called()



    @patch('requests.post')
    def test_notificacion_no_falla_si_token_telegram_no_esta_configurado(self, mock_post):
        """
        Test: Comportamiento ante la falta de TELEGRAM_BOT_TOKEN

        Given: Un entorno donde settings.TELEGRAM_BOT_TOKEN es None o vacío.
        When: Se crea un comunicado que debería disparar notificaciones.
        Then: 
            1. El comunicado se crea correctamente (no hay rollback).
            2. Se imprime "TELEGRAM_BOT_TOKEN no configurado." en consola.
            3. No se realiza ninguna llamada a requests.post.
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()
        
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            with patch.object(settings, 'TELEGRAM_BOT_TOKEN', None):
                comunicado = servicio.create_comunicado(self.admin, data_validada)

                self.assertIsNotNone(comunicado.id)

                mock_post.assert_not_called()

                self.assertIn("TELEGRAM_BOT_TOKEN no configurado.", captured_output.getvalue())
        finally:
            sys.stdout = sys.__stdout__



    @patch('requests.post')
    def test_notificacion_no_falla_si_token_telegram_es_string_vacio(self, mock_post):
        """
        Test: Manejo de TELEGRAM_BOT_TOKEN como string vacío ('')

        Given: Un entorno donde settings.TELEGRAM_BOT_TOKEN = ''.
        When: Se intenta notificar un comunicado.
        Then: El servicio debe tratarlo como 'not token', imprimir el aviso y salir.
        """
        data_validada = self.payload_comunicado_valido.copy()
        servicio = ComunicadoService()
        
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            with patch.object(settings, 'TELEGRAM_BOT_TOKEN', ''):
                servicio.create_comunicado(self.admin, data_validada)

                mock_post.assert_not_called()
                self.assertIn("TELEGRAM_BOT_TOKEN no configurado.", captured_output.getvalue())
        finally:
            sys.stdout = sys.__stdout__



    @patch('requests.post')
    def test_comunicado_sin_imagen_usa_endpoint_send_message_y_campo_text(self, mock_post):
        """
        Test: Elección de endpoint para comunicados sin imagen

        Given: Un comunicado con imagen_portada = None.
        When: Se procesa la notificación de Telegram.
        Then: 
            1. La URL debe contener 'sendMessage'.
            2. El payload debe contener el campo 'text' (no 'caption').
            3. No debe haber campo 'photo'.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['imagen_portada'] = None
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        args, kwargs = mock_post.call_args
        url_llamada = args[0]
        payload = kwargs.get('json') or kwargs.get('data')

        self.assertIn("sendMessage", url_llamada, "Debería usar el método sendMessage para texto puro.")
        self.assertNotIn("sendPhoto", url_llamada)

        self.assertIn("text", payload, "El mensaje de texto debe ir en el campo 'text'.")
        self.assertNotIn("caption", payload, "No debe existir el campo 'caption' en un sendMessage.")
        self.assertNotIn("photo", payload)

        texto_enviado = payload['text']
        self.assertIn(data_validada['titulo'], texto_enviado, "El título debe estar incluido en el mensaje.")
        self.assertIn(data_validada['contenido'], texto_enviado, "El contenido base debe estar incluido en el mensaje.")



    @patch('requests.post')
    def test_mensaje_menor_3000_caracteres_se_envia_completo_sin_truncar(self, mock_post):
        """
        Test: Comportamiento con mensajes que no superan el límite (Sin imagen)

        Given: Un comunicado sin imagen_portada y un texto normal (< 3000 chars).
        When: Se procesa la notificación a Telegram.
        Then: El mensaje se envía íntegro y NO se le añaden los puntos suspensivos finales.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['imagen_portada'] = None

        contenido_integro = "Texto de prueba. " * 30
        data_validada['contenido'] = contenido_integro
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)
        
        args, kwargs = mock_post.call_args
        payload = kwargs.get('json') or kwargs.get('data')
        texto_enviado = payload['text']

        self.assertIn(contenido_integro, texto_enviado, "El texto original debe estar completo.")

        self.assertFalse(texto_enviado.endswith("..."), "No debe añadir '...' si no superó el límite de caracteres.")



    @patch('requests.post')
    def test_mensaje_mayor_3000_caracteres_se_trunca_y_anade_puntos_suspensivos(self, mock_post):
        """
        Test: Truncado de mensajes excesivamente largos (Sin imagen)

        Given: Un comunicado sin imagen_portada y un contenido de 4000 caracteres.
        When: Se procesa la notificación a Telegram.
        Then: 
            1. El mensaje enviado se recorta para no superar el límite.
            2. El texto resultante termina con '...'.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['imagen_portada'] = None

        contenido_largo = "A" * 4000
        data_validada['contenido'] = contenido_largo
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)
        
        args, kwargs = mock_post.call_args
        payload = kwargs.get('json') or kwargs.get('data')
        texto_enviado = payload['text']

        self.assertTrue(texto_enviado.endswith("..."), "El mensaje truncado debe terminar obligatoriamente con '...'.")

        self.assertLessEqual(len(texto_enviado), 3010, f"El mensaje es demasiado largo: {len(texto_enviado)} caracteres.")

        self.assertLess(len(texto_enviado), len(contenido_largo), "El texto enviado no se ha recortado respecto al original.")



    @patch('requests.post')
    def test_payload_telegram_contiene_chat_id_text_y_parse_mode_html(self, mock_post):
        """
        Test: Verificación de la estructura del payload para texto (sendMessage)

        Given: Un comunicado válido sin imagen.
        When: Se construye y envía la petición a Telegram.
        Then: El payload incluye obligatoriamente:
            1. chat_id correcto.
            2. campo text con el contenido.
            3. parse_mode establecido en 'HTML'.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['imagen_portada'] = None
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        args, kwargs = mock_post.call_args
        payload = kwargs.get('json') or kwargs.get('data')

        self.assertIn('chat_id', payload)
        self.assertEqual(str(payload['chat_id']), self.area_con_telegram.telegram_channel_id)

        self.assertIn('text', payload)
        self.assertTrue(len(payload['text']) > 0, "El texto no debe estar vacío.")

        self.assertIn('parse_mode', payload)
        self.assertEqual(payload['parse_mode'], 'HTML', "Es vital para que Telegram renderice las negritas y emojis correctamente.")



    @patch('requests.post')
    def test_llamada_a_telegram_tiene_timeout_de_5_segundos(self, mock_post):
        """
        Test: Prevención de bloqueos (Timeout)

        Given: Un comunicado válido.
        When: El servicio realiza la petición HTTP a la API de Telegram.
        Then: La llamada a requests.post debe incluir explícitamente timeout=5.
        """
        data_validada = self.payload_comunicado_valido.copy()
        data_validada['imagen_portada'] = None
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        args, kwargs = mock_post.call_args

        self.assertIn('timeout', kwargs, "Falta configurar el parámetro 'timeout' en requests.post.")
        self.assertEqual(kwargs['timeout'], 5, "El timeout configurado debe ser de exactamente 5 segundos.")



    @patch('requests.post')
    def test_comunicado_con_imagen_usa_endpoint_send_photo_y_campo_caption(self, mock_post):
        """
        Test: Elección de endpoint para comunicados con imagen

        Given: Un comunicado donde imagen_portada contiene un archivo válido.
        When: Se procesa la notificación de Telegram.
        Then: 
            1. La URL de la petición debe apuntar a 'sendPhoto'.
            2. El texto enriquecido debe viajar en el parámetro 'caption'.
            3. No debe usarse el campo 'text'.
        """
        data_validada = self.payload_comunicado_valido.copy()

        imagen_mock = SimpleUploadedFile(
            name='cartel_cultos.jpg',
            content=b'contenido_binario_falso',
            content_type='image/jpeg'
        )
        data_validada['imagen_portada'] = imagen_mock
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        args, kwargs = mock_post.call_args
        url_llamada = args[0]

        payload = kwargs.get('data') or kwargs.get('json') or {}

        self.assertIn("sendPhoto", url_llamada, "La API debe apuntar a sendPhoto al detectar una imagen.")
        self.assertNotIn("sendMessage", url_llamada)

        self.assertIn("caption", payload, "El texto adjunto a una foto debe ir en la clave 'caption'.")
        self.assertNotIn("text", payload, "La clave 'text' es inválida en el endpoint sendPhoto.")

        self.assertIn(data_validada['titulo'], payload['caption'])



    @patch('requests.post')
    def test_caption_menor_1000_caracteres_se_envia_completo_sin_truncar(self, mock_post):
        """
        Test: Comportamiento de mensajes multimedia que no superan el límite (Con imagen)

        Given: Un comunicado con imagen_portada y un texto normal (< 1000 chars).
        When: Se procesa la notificación a Telegram.
        Then: 
            1. El caption se envía íntegro.
            2. NO se le añade la coletilla de recorte "... (ver web)".
        """
        data_validada = self.payload_comunicado_valido.copy()

        imagen_mock = SimpleUploadedFile(
            name='cartel.jpg',
            content=b'imagen_falsa',
            content_type='image/jpeg'
        )
        data_validada['imagen_portada'] = imagen_mock
        
        contenido_normal = "Texto informativo para los hermanos. " * 15
        data_validada['contenido'] = contenido_normal
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        args, kwargs = mock_post.call_args
        payload = kwargs.get('data') or kwargs.get('json') or {}
        caption_enviado = payload.get('caption', '')

        self.assertIn(contenido_normal, caption_enviado, "El texto original debe estar completo dentro del caption.")
        self.assertFalse(
            caption_enviado.endswith("... (ver web)"), 
            "No debe añadir la coletilla '... (ver web)' si no ha superado los 1000 caracteres."
        )
        self.assertFalse(caption_enviado.endswith("..."), "No debe truncar ni añadir puntos suspensivos.")



    @patch('requests.post')
    def test_caption_mayor_1000_caracteres_se_trunca_y_anade_coletilla(self, mock_post):
        """
        Test: Truncado de caption excesivamente largo (Con imagen)

        Given: Un comunicado con imagen_portada y un contenido de > 1000 caracteres.
        When: Se procesa la notificación a Telegram (sendPhoto).
        Then: 
            1. El caption enviado se recorta para no superar el límite de Telegram (1024).
            2. El texto resultante termina obligatoriamente con '... (ver web)'.
        """
        data_validada = self.payload_comunicado_valido.copy()

        imagen_mock = SimpleUploadedFile(
            name='cartel_cultos.jpg',
            content=b'imagen_falsa',
            content_type='image/jpeg'
        )
        data_validada['imagen_portada'] = imagen_mock

        contenido_largo = "A" * 1500
        data_validada['contenido'] = contenido_largo
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        args, kwargs = mock_post.call_args
        payload = kwargs.get('data') or kwargs.get('json') or {}
        caption_enviado = payload.get('caption', '')

        self.assertTrue(
            caption_enviado.endswith("... (ver web)"), 
            "El caption truncado debe terminar con la coletilla '... (ver web)'."
        )

        self.assertLessEqual(
            len(caption_enviado), 1024, 
            f"El caption supera el límite estricto de Telegram (1024 chars). Longitud actual: {len(caption_enviado)}"
        )

        self.assertLess(
            len(caption_enviado), len(contenido_largo), 
            "El caption no se ha recortado respecto al original."
        )



    @patch('requests.post')
    def test_archivo_imagen_no_accesible_captura_excepcion_y_no_rompe_transaccion(self, mock_post):
        """
        Test: Resiliencia ante fallos del sistema de archivos al leer la imagen

        Given: Un comunicado con una imagen.
        When: Durante el envío a Telegram, ocurre un error al intentar acceder al archivo (ej. OSError).
        Then: 
            1. La excepción se captura internamente en _notificar_telegram.
            2. El comunicado persiste en la base de datos (no hay rollback).
        """
        data_validada = self.payload_comunicado_valido.copy()

        imagen_mock = SimpleUploadedFile(
            name='cartel.jpg',
            content=b'imagen_falsa',
            content_type='image/jpeg'
        )
        data_validada['imagen_portada'] = imagen_mock
        
        servicio = ComunicadoService()

        mock_post.side_effect = OSError("Permiso denegado o archivo no accesible")

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)
        
        self.assertIsNotNone(comunicado.id)
        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())



    @patch('requests.post')
    def test_imagen_corrupta_captura_excepcion_y_no_rompe_transaccion(self, mock_post):
        """
        Test: Resiliencia ante imágenes corruptas o formato inválido

        Given: Un comunicado donde la imagen adjunta está corrupta (bytes inválidos).
        When: El servicio intenta empaquetar o enviar el archivo y salta una excepción.
        Then: 
            1. El bloque try/except captura el error de procesamiento.
            2. El comunicado se guarda sin problemas en la base de datos (evita rollback).
        """
        data_validada = self.payload_comunicado_valido.copy()
        
        imagen_corrupta = SimpleUploadedFile(
            name='cartel_corrupto.jpg',
            content=b'esto_no_es_una_imagen_son_bytes_basura',
            content_type='image/jpeg'
        )
        data_validada['imagen_portada'] = imagen_corrupta
        
        servicio = ComunicadoService()

        mock_post.side_effect = ValueError("formato de imagen no reconocido o archivo corrupto")

        comunicado = servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        self.assertIsNotNone(comunicado.id)
        self.assertTrue(Comunicado.objects.filter(id=comunicado.id).exists())



    from django.core.files.uploadedfile import SimpleUploadedFile

    @patch('requests.post')
    def test_payload_telegram_con_imagen_contiene_photo_y_parse_mode_html(self, mock_post):
        """
        Test: Verificación de la estructura del payload multipart para sendPhoto

        Given: Un comunicado válido con imagen_portada.
        When: Se construye y envía la petición a Telegram.
        Then: La llamada a requests.post incluye obligatoriamente:
            1. kwarg 'files' con la clave 'photo' conteniendo la imagen.
            2. kwarg 'data' con el parámetro parse_mode='HTML'.
        """
        data_validada = self.payload_comunicado_valido.copy()

        imagen_mock = SimpleUploadedFile(
            name='cartel_procesion.jpg',
            content=b'bytes_de_la_imagen',
            content_type='image/jpeg'
        )
        data_validada['imagen_portada'] = imagen_mock
        
        servicio = ComunicadoService()

        servicio.create_comunicado(self.admin, data_validada)

        self.assertTrue(mock_post.called)

        args, kwargs = mock_post.call_args

        self.assertIn('files', kwargs, "La petición debe usar el kwarg 'files' para multipart/form-data.")
        archivos_enviados = kwargs['files']
        self.assertIn('photo', archivos_enviados, "El archivo debe enviarse bajo la clave estricta 'photo'.")

        self.assertIn('data', kwargs, "Los metadatos adjuntos a la foto deben ir en el kwarg 'data'.")
        datos_enviados = kwargs['data']

        self.assertIn('parse_mode', datos_enviados, "Debe existir el campo parse_mode en el diccionario data.")
        self.assertEqual(datos_enviados['parse_mode'], 'HTML', "El parse_mode debe ser HTML para que no se vean las etiquetas <b>.")

        self.assertIn('chat_id', datos_enviados)