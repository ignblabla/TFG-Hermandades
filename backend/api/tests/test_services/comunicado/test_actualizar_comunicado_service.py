from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from unittest.mock import PropertyMock, patch


from api.models import AreaInteres, Comunicado, CuerpoPertenencia, Hermano, HermanoCuerpo, TipoPuesto
from api.servicios.comunicado.creacion_comunicado_service import ComunicadoService


class ActualizarComunicadoServiceTest(TestCase):

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

        self.comunicado_existente = Comunicado.objects.create(
            titulo="Comunicado Original",
            contenido="Este es el texto original antes de ser modificado.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            embedding=[0.1, 0.2, 0.3]
        )

        self.comunicado_existente.areas_interes.add(self.area_sin_telegram)

        # ---------------------------------------------------------------------
        # 6. PAYLOADS DE ACTUALIZACIÓN
        # ---------------------------------------------------------------------
        self.payload_actualizacion_parcial = {
            "titulo": "Comunicado Original (Actualizado)"
        }

        self.payload_actualizacion_completa = {
            "titulo": "Título totalmente nuevo",
            "contenido": "Contenido modificado para forzar la regeneración del vector de embeddings.",
            "tipo_comunicacion": "URGENTE",
            "areas_interes": [self.area_con_telegram.id, self.area_sin_telegram.id], 
            "imagen_portada": None
        }



    @patch('api.models.genai.Client')
    def test_admin_actualiza_comunicado_valido_sin_excepciones_ok(self, mock_genai_client):
        """
        Test: Admin actualiza un comunicado existente con datos válidos sin restricciones de permisos

        Given: Un usuario con esAdmin = True, un comunicado existente y un diccionario con datos modificados.
        When: se llama a update_comunicado con la instancia del comunicado y la data_validada.
        Then: se actualiza el Comunicado correctamente en la BD, se modifican sus áreas asociadas 
                y no se lanzan excepciones de permisos.
        """

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.9, 0.8, 0.7])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Título totalmente modificado",
            "contenido": "El contenido ha sido actualizado exitosamente por el administrador.",
            "tipo_comunicacion": "URGENTE",
            "areas_interes": [self.area_con_telegram, self.area_sin_telegram]
        }
        
        servicio = ComunicadoService() 

        comunicado_actualizado = servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(comunicado_actualizado.id, self.comunicado_existente.id)
        self.assertEqual(self.comunicado_existente.titulo, "Título totalmente modificado")
        self.assertEqual(self.comunicado_existente.contenido, "El contenido ha sido actualizado exitosamente por el administrador.")
        self.assertEqual(self.comunicado_existente.tipo_comunicacion, "URGENTE")

        areas_asociadas = list(self.comunicado_existente.areas_interes.all())
        self.assertEqual(len(areas_asociadas), 2)
        self.assertIn(self.area_con_telegram, areas_asociadas)
        self.assertIn(self.area_sin_telegram, areas_asociadas)



    @patch('api.models.genai.Client')
    def test_miembro_junta_actualiza_comunicado_ok(self, mock_genai_client):
        """
        Test: Usuario miembro de la Junta de Gobierno puede actualizar un comunicado

        Given: Un usuario que pertenece al cuerpo JUNTA_GOBIERNO (pero no es admin) 
            y un comunicado previamente creado.
        When: se llama a update_comunicado con datos de actualización.
        Then: el servicio permite la operación, actualiza los campos en la base de datos 
            y no lanza excepción de permisos.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.5, 0.5, 0.5])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Actualización desde Vocalía",
            "contenido": "Contenido actualizado por un miembro de la junta.",
            "areas_interes": [self.area_con_telegram]
        }
        
        servicio = ComunicadoService()

        comunicado = servicio.update_comunicado(
            usuario=self.miembro_junta, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, "Actualización desde Vocalía")
        self.assertEqual(self.comunicado_existente.areas_interes.count(), 1)
        self.assertIn(self.area_con_telegram, self.comunicado_existente.areas_interes.all())

        self.assertEqual(self.comunicado_existente.autor, self.admin)



    @patch('api.models.genai.Client')
    def test_usuario_admin_y_junta_actualiza_comunicado_ok(self, mock_genai_client):
        """
        Test: Usuario que es Admin y además pertenece a la Junta puede actualizar sin problemas

        Given: Un usuario con esAdmin = True que también está vinculado al cuerpo JUNTA_GOBIERNO.
        When: se solicita la actualización de un comunicado a través del servicio.
        Then: el sistema identifica que cumple ambos requisitos de privilegio, procesa 
            la actualización y persiste los cambios correctamente.
        """
        HermanoCuerpo.objects.create(
            hermano=self.admin,
            cuerpo=self.cuerpo_junta,
            anio_ingreso=self.ahora.year
        )

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.1, 0.1])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Actualización por Superusuario",
            "contenido": "Cuerpo del mensaje actualizado por un admin de la junta.",
            "tipo_comunicacion": "CULTOS"
        }
        
        servicio = ComunicadoService()

        comunicado = servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, "Actualización por Superusuario")
        self.assertEqual(self.comunicado_existente.tipo_comunicacion, "CULTOS")
        self.assertTrue(self.admin.esAdmin)
        self.assertTrue(self.admin.cuerpos.filter(nombre_cuerpo='JUNTA_GOBIERNO').exists())



    @patch('api.models.genai.Client')
    def test_usuario_multiples_cuerpos_con_junta_actualiza_comunicado_ok(self, mock_genai_client):
        """
        Test: Usuario con múltiples cuerpos, incluyendo JUNTA_GOBIERNO, puede actualizar

        Given: Un usuario que pertenece a varios cuerpos (ej. Costaleros, Acólitos) 
            y además al cuerpo de JUNTA_GOBIERNO.
        When: se llama a update_comunicado con la data modificada.
        Then: el servicio valida correctamente la pertenencia a la Junta entre todos sus cuerpos
            y permite la actualización sin lanzar PermissionDenied.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.4, 0.4, 0.4])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        cuerpo_costaleros = CuerpoPertenencia.objects.create(nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS)
        cuerpo_acolitos = CuerpoPertenencia.objects.create(nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.ACOLITOS)

        for c in [cuerpo_costaleros, cuerpo_acolitos, self.cuerpo_junta]:
            HermanoCuerpo.objects.create(
                hermano=self.usuario_base,
                cuerpo=c,
                anio_ingreso=self.ahora.year
            )

        data_validada = {
            "titulo": "Circular para todos los cuerpos",
            "contenido": "Contenido actualizado por un oficial con múltiples funciones."
        }
        
        servicio = ComunicadoService()

        comunicado = servicio.update_comunicado(
            usuario=self.usuario_base, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, "Circular para todos los cuerpos")
        self.assertEqual(self.usuario_base.cuerpos.count(), 3)



    @patch('api.models.genai.Client')
    def test_usuario_admin_sin_cuerpos_actualiza_comunicado_ok(self, mock_genai_client):
        """
        Test: Usuario con atributo esAdmin=True puede actualizar aunque no tenga relación con cuerpos

        Given: Un usuario con esAdmin = True que no está vinculado a ningún CuerpoPertenencia.
        When: se solicita la actualización de un comunicado.
        Then: el servicio permite la operación basándose exclusivamente en el flag de administrador,
            sin requerir pertenencia a la Junta de Gobierno.
        """
        self.admin.pertenencias_cuerpos.all().delete()
        self.assertEqual(self.admin.cuerpos.count(), 0)

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.7, 0.7, 0.7])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Actualización por Administrador Puro",
            "contenido": "Contenido modificado por alguien que solo tiene el flag esAdmin."
        }
        
        servicio = ComunicadoService()

        comunicado = servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, "Actualización por Administrador Puro")
        self.assertTrue(self.admin.esAdmin)
        self.assertEqual(self.admin.cuerpos.count(), 0)



    @patch('api.models.genai.Client')
    def test_usuario_junta_no_admin_actualiza_comunicado_ok(self, mock_genai_client):
        """
        Test: Usuario con esAdmin=False pero perteneciente a JUNTA_GOBIERNO puede actualizar

        Given: Un usuario (miembro_junta) con esAdmin = False pero vinculado 
            al cuerpo de JUNTA_GOBIERNO.
        When: se invoca el servicio update_comunicado con datos válidos.
        Then: el servicio permite la edición al verificar que el usuario pertenece 
            a la cúpula de la hermandad, a pesar de no ser administrador técnico.
        """

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.2, 0.4, 0.6])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Circular de Secretaría",
            "contenido": "Actualización de datos por parte de la Junta de Gobierno.",
            "tipo_comunicacion": "SECRETARIA"
        }

        self.assertFalse(self.miembro_junta.esAdmin)
        self.assertTrue(
            self.miembro_junta.cuerpos.filter(
                nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()
        )

        servicio = ComunicadoService()

        comunicado = servicio.update_comunicado(
            usuario=self.miembro_junta, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )
        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, "Circular de Secretaría")
        self.assertEqual(self.comunicado_existente.tipo_comunicacion, "SECRETARIA")



    @patch('api.models.genai.Client')
    def test_actualizar_solo_titulo_mantiene_resto_campos(self, mock_genai_client):
        """
        Test: Actualizar solo el título de un comunicado

        Given: Un comunicado con título, contenido y áreas de interés ya definidos.
        When: se invoca update_comunicado enviando únicamente un nuevo título 
            en la data validada.
        Then: el título cambia en la BD, pero el contenido y las relaciones 
            M2M (áreas de interés) permanecen intactas.
        """

        titulo_nuevo = "Nuevo Título de Prueba"
        contenido_original = self.comunicado_existente.contenido
        areas_originales = list(self.comunicado_existente.areas_interes.all())

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.9, 0.9, 0.9])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": titulo_nuevo
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, titulo_nuevo)

        self.assertEqual(self.comunicado_existente.contenido, contenido_original)

        self.assertEqual(list(self.comunicado_existente.areas_interes.all()), areas_originales)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_actualizar_solo_contenido_genera_nuevo_embedding(self, mock_generar_embedding):
        """
        Test: Actualizar solo el contenido de un comunicado

        Given: Un comunicado con título y contenido previos.
        When: se actualiza el campo 'contenido'.
        Then: el título se mantiene, el contenido cambia y se encola la 
            regeneración del vector semántico en segundo plano.
        """
        titulo_original = self.comunicado_existente.titulo
        nuevo_contenido = "Este es el nuevo cuerpo del mensaje, mucho más detallado."

        data_validada = {
            "contenido": nuevo_contenido
        }
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.contenido, nuevo_contenido)
        self.assertEqual(self.comunicado_existente.titulo, titulo_original)

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.id)



    @patch('api.models.genai.Client')
    def test_actualizar_solo_tipo_comunicacion_mantiene_integridad(self, mock_genai_client):
        """
        Test: Actualizar solo el tipo de comunicación

        Given: Un comunicado con tipo 'GENERAL'.
        When: se actualiza el campo 'tipo_comunicacion' a 'CULTOS'.
        Then: el campo cambia en la base de datos, pero el título, contenido 
            y embedding permanecen idénticos.
        """
        tipo_nuevo = "CULTOS"
        titulo_previo = self.comunicado_existente.titulo
        contenido_previo = self.comunicado_existente.contenido
        embedding_previo = self.comunicado_existente.embedding

        data_validada = {
            "tipo_comunicacion": tipo_nuevo
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.tipo_comunicacion, tipo_nuevo)

        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)
        self.assertEqual(self.comunicado_existente.contenido, contenido_previo)
        self.assertEqual(self.comunicado_existente.embedding, embedding_previo)

        mock_genai_client.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_solo_imagen_portada_ok(self, mock_genai_client):
        """
        Test: Actualizar solo la imagen de portada

        Given: Un comunicado con una imagen previa (o sin ella).
        When: se proporciona un nuevo objeto de imagen en data_validada.
        Then: el campo imagen_portada se actualiza con el nuevo archivo y
            el resto de atributos permanecen inalterados.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        imagen_nueva = SimpleUploadedFile(
            name='nueva_portada.jpg',
            content=b'\x00\x01\x02\x03',
            content_type='image/jpeg'
        )

        titulo_previo = self.comunicado_existente.titulo
        contenido_previo = self.comunicado_existente.contenido

        data_validada = {
            "imagen_portada": imagen_nueva
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertIn('nueva_portada', self.comunicado_existente.imagen_portada.name)

        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)
        self.assertEqual(self.comunicado_existente.contenido, contenido_previo)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_actualizar_multiples_campos_simultaneamente_ok(self, mock_generar_embedding):
        """
        Test: Actualizar múltiples campos a la vez

        Given: Un comunicado existente y un usuario con permisos.
        When: se envían nuevos valores para título, contenido, tipo e imagen.
        Then: todos los campos se actualizan correctamente en una sola operación
            y se delega correctamente la regeneración del embedding.
        """
        nueva_img = SimpleUploadedFile(name='multi.jpg', content=b'file_content', content_type='image/jpeg')

        data_validada = {
            "titulo": "Título Multicampo",
            "contenido": "Nuevo contenido para el test masivo.",
            "tipo_comunicacion": "URGENTE",
            "imagen_portada": nueva_img
        }
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, "Título Multicampo")
        self.assertEqual(self.comunicado_existente.contenido, "Nuevo contenido para el test masivo.")
        self.assertEqual(self.comunicado_existente.tipo_comunicacion, "URGENTE")
        self.assertIn('multi', self.comunicado_existente.imagen_portada.name)

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.id)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_actualizar_absolutamente_todos_los_campos_ok(self, mock_generar_embedding):
        """
        Test: Actualización integral de todos los campos editables

        Given: Un comunicado con datos iniciales y un set de áreas de interés.
        When: Se envía un payload que modifica título, contenido, tipo, imagen 
            y la lista de áreas de interés.
        Then: El servicio actualiza cada campo, sincroniza la relación M2M 
            y encola correctamente la tarea asíncrona del embedding.
        """
        nueva_img = SimpleUploadedFile(name='full_update.png', content=b'imgdata', content_type='image/png')
        
        area_nueva = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.CARIDAD, 
            telegram_channel_id="999888"
        )

        data_validada = {
            "titulo": "Actualización Total",
            "contenido": "Texto final verificado.",
            "tipo_comunicacion": "CULTOS",
            "imagen_portada": nueva_img,
            "areas_interes": [area_nueva]
        }
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, "Actualización Total")
        self.assertEqual(self.comunicado_existente.contenido, "Texto final verificado.")
        self.assertEqual(self.comunicado_existente.tipo_comunicacion, "CULTOS")

        self.assertIn('full_update', self.comunicado_existente.imagen_portada.name)
        self.assertTrue(self.comunicado_existente.imagen_portada.name.endswith('.png'))

        self.assertEqual(self.comunicado_existente.areas_interes.count(), 1)
        self.assertIn(area_nueva, self.comunicado_existente.areas_interes.all())

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.id)

        self.assertEqual(len(callbacks), 1)



    @patch('api.models.genai.Client')
    def test_actualizar_con_data_vacia_no_realiza_cambios(self, mock_genai_client):
        """
        Test: Enviar data_validada vacío

        Given: Un comunicado con datos ya existentes y un embedding generado.
        When: Se invoca update_comunicado con un diccionario vacío {}.
        Then: El servicio retorna la instancia original, no modifica ningún campo
            y no realiza llamadas a la API de Gemini.
        """
        titulo_antes = self.comunicado_existente.titulo
        contenido_antes = self.comunicado_existente.contenido
        embedding_antes = self.comunicado_existente.embedding
        areas_count_antes = self.comunicado_existente.areas_interes.count()

        data_validada = {}
        
        servicio = ComunicadoService()

        resultado = servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(resultado.pk, self.comunicado_existente.pk)

        self.assertEqual(self.comunicado_existente.titulo, titulo_antes)
        self.assertEqual(self.comunicado_existente.contenido, contenido_antes)
        self.assertEqual(self.comunicado_existente.embedding, embedding_antes)
        self.assertEqual(self.comunicado_existente.areas_interes.count(), areas_count_antes)

        mock_genai_client.assert_not_called()



    @patch('api.models.genai.Client')
    def test_enviar_valores_identicos_no_cambia_nada(self, mock_genai_client):
        """
        Test: Enviar campos con el mismo valor que ya tienen en BD

        Given: Un comunicado con título y contenido ya definidos.
        When: Se llama a update_comunicado enviando exactamente esos mismos valores.
        Then: La operación tiene éxito, los datos se mantienen y NO se llama a la IA.
        """
        titulo_actual = self.comunicado_existente.titulo
        contenido_actual = self.comunicado_existente.contenido
        embedding_actual = self.comunicado_existente.embedding

        data_validada = {
            "titulo": titulo_actual,
            "contenido": contenido_actual
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()
        
        self.assertEqual(self.comunicado_existente.titulo, titulo_actual)
        self.assertEqual(self.comunicado_existente.contenido, contenido_actual)
        self.assertEqual(self.comunicado_existente.embedding, embedding_actual)

        mock_genai_client.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_actualizar_titulo_dispara_metodo_save(self, mock_generar_embedding):
        """
        Test: Actualizar título y verificar que el método save() se ejecuta

        Given: Un comunicado existente y un nuevo título.
        When: Se llama a update_comunicado.
        Then: El método save() de la instancia debe ser invocado exactamente una vez
            para persistir los cambios y se debe encolar la actualización del embedding.
        """
        nuevo_titulo = "Título verificado con save"
        data_validada = {"titulo": nuevo_titulo}
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):

            with patch.object(self.comunicado_existente, 'save', wraps=self.comunicado_existente.save) as mock_save:
                servicio.update_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=self.comunicado_existente, 
                    data_validada=data_validada
                )

                self.assertTrue(mock_save.called)
                self.assertEqual(mock_save.call_count, 1)

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, nuevo_titulo)

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.id)



    @patch('api.models.genai.Client')
    def test_actualizar_contenido_dispara_metodo_save(self, mock_genai_client):
        """
        Test: Actualizar contenido y verificar la ejecución de save()

        Given: Un comunicado existente.
        When: Se modifica el campo 'contenido'.
        Then: El servicio debe llamar al método save() de la instancia para 
            persistir tanto el nuevo texto como el nuevo embedding generado.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        nuevo_contenido = "Este contenido requiere un nuevo guardado y nuevo embedding."
        data_validada = {"contenido": nuevo_contenido}
        
        servicio = ComunicadoService()

        with patch.object(self.comunicado_existente, 'save', wraps=self.comunicado_existente.save) as spy_save:
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

            self.assertTrue(spy_save.called, "El método save() debería haber sido llamado.")
            self.assertEqual(spy_save.call_count, 1, "El método save() debería llamarse exactamente una vez.")

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.contenido, nuevo_contenido)
        self.assertEqual(self.comunicado_existente.embedding, [0.1, 0.2, 0.3])



    @patch('api.models.genai.Client')
    def test_actualizar_solo_areas_interes_ok(self, mock_genai_client):
        """
        Test: Actualizar solo areas_interes con una lista válida.

        Given: Un comunicado que ya tiene un área de interés asignada (area_sin_telegram).
        When: Se envía un payload que contiene únicamente una nueva lista de áreas de interés.
        Then: El servicio reemplaza las áreas anteriores por las nuevas sin alterar
            el título, contenido u otros atributos.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        titulo_previo = self.comunicado_existente.titulo
        contenido_previo = self.comunicado_existente.contenido

        self.assertIn(self.area_sin_telegram, self.comunicado_existente.areas_interes.all())

        data_validada = {
            "areas_interes": [self.area_con_telegram]
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)
        self.assertEqual(self.comunicado_existente.contenido, contenido_previo)

        areas_actualizadas = self.comunicado_existente.areas_interes.all()
        self.assertEqual(areas_actualizadas.count(), 1)
        self.assertIn(self.area_con_telegram, areas_actualizadas)
        self.assertNotIn(self.area_sin_telegram, areas_actualizadas)



    @patch('api.models.genai.Client')
    def test_actualizar_areas_interes_reemplaza_las_anteriores_ok(self, mock_genai_client):
        """
        Test: Reemplazo total de áreas de interés.

        Given: Un comunicado que ya tiene asociadas el 'area_sin_telegram' 
            y el 'area_con_telegram'.
        When: Se envía un payload con una nueva área creada al vuelo.
        Then: El servicio debe desvincular las dos áreas anteriores y 
            vincular únicamente la nueva.
        """
        self.comunicado_existente.areas_interes.set([
            self.area_sin_telegram, 
            self.area_con_telegram
        ])
        self.assertEqual(self.comunicado_existente.areas_interes.count(), 2)

        area_sustituta = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.CULTOS_FORMACION, 
            telegram_channel_id="777888"
        )

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        data_validada = {
            "areas_interes": [area_sustituta]
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()
        
        areas_finales = self.comunicado_existente.areas_interes.all()

        self.assertEqual(areas_finales.count(), 1)
        self.assertIn(area_sustituta, areas_finales)
        self.assertNotIn(self.area_sin_telegram, areas_finales)
        self.assertNotIn(self.area_con_telegram, areas_finales)



    @patch('api.models.genai.Client')
    def test_actualizar_areas_interes_con_lista_vacia_elimina_todas(self, mock_genai_client):
        """
        Test: Vaciar las áreas de interés.

        Given: Un comunicado que ya tiene asociadas áreas de interés.
        When: Se envía 'areas_interes': [] en el diccionario de datos.
        Then: El servicio debe eliminar todas las relaciones existentes,
            dejando el contador de áreas en cero.
        """
        self.comunicado_existente.areas_interes.set([
            self.area_sin_telegram, 
            self.area_con_telegram
        ])
        self.assertEqual(self.comunicado_existente.areas_interes.count(), 2)

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        data_validada = {
            "areas_interes": []
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.areas_interes.count(), 0)

        self.assertFalse(self.comunicado_existente.areas_interes.exists())



    @patch('api.models.genai.Client')
    def test_actualizar_campos_mixtos_y_areas_ok(self, mock_genai_client):
        """
        Test: Actualización simultánea de campos directos, imagen y relaciones M2M.

        Given: Un comunicado con datos iniciales.
        When: Se envía un payload con nuevo título, nueva imagen y una lista de áreas.
        Then: Todos los cambios deben persistir y el título debe disparar la IA.
        """
        nueva_img = SimpleUploadedFile(
            name='update_mixto.png', 
            content=b'file_content', 
            content_type='image/png'
        )

        area_nueva = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.CULTOS_FORMACION,
            telegram_channel_id="-100222"
        )

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        nuevo_embedding = [0.1, 0.2, 0.3]
        mock_resultado.embeddings = [MagicMock(values=nuevo_embedding)]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Nuevo Título Integrado",
            "imagen_portada": nueva_img,
            "areas_interes": [area_nueva]
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, "Nuevo Título Integrado")

        self.assertIn('update_mixto', self.comunicado_existente.imagen_portada.name)

        self.assertEqual(self.comunicado_existente.areas_interes.count(), 1)
        self.assertIn(area_nueva, self.comunicado_existente.areas_interes.all())

        self.assertEqual(self.comunicado_existente.embedding, nuevo_embedding)



    @patch('api.models.genai.Client')
    def test_actualizar_areas_interes_dispara_metodo_set(self, mock_genai_client):
        """
        Test: Verificar que el método .set() de la relación M2M se ejecuta.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        nuevas_areas = [self.area_con_telegram, self.area_sin_telegram]
        data_validada = {
            "areas_interes": nuevas_areas
        }
        
        servicio = ComunicadoService()

        ManagerClass = type(self.comunicado_existente.areas_interes)

        with patch.object(ManagerClass, 'set', autospec=True) as mock_set:
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

            self.assertTrue(mock_set.called, "El método .set() no fue invocado en el manager M2M.")

            args, kwargs = mock_set.call_args

            self.assertEqual(list(args[1]), nuevas_areas)

        mock_genai_client.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_actualizar_comunicado_sin_areas_no_toca_relacion_m2m(self, mock_generar_embedding):
        """
        Test: Si 'areas_interes' no está en data_validada, no se llama a .set().

        Given: Un comunicado que ya tiene áreas asociadas.
        When: Se actualiza solo el título (u otro campo).
        Then: El método .set() del manager M2M no debe ejecutarse, 
            manteniendo las áreas que ya tenía, y se lanza la actualización del vector.
        """
        self.comunicado_existente.areas_interes.set([self.area_con_telegram])

        data_validada = {
            "titulo": "Título cambiado sin tocar áreas"
        }
        
        servicio = ComunicadoService()
        ManagerClass = type(self.comunicado_existente.areas_interes)

        with self.captureOnCommitCallbacks(execute=True):
            with patch.object(ManagerClass, 'set', autospec=True) as mock_set:
                servicio.update_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=self.comunicado_existente, 
                    data_validada=data_validada
                )

                self.assertFalse(
                    mock_set.called, 
                    "Se llamó a .set() a pesar de que 'areas_interes' no venía en el payload"
                )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, "Título cambiado sin tocar áreas")

        self.assertEqual(self.comunicado_existente.areas_interes.count(), 1)
        self.assertIn(self.area_con_telegram, self.comunicado_existente.areas_interes.all())

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.id)



    @patch('api.models.genai.Client')
    def test_actualizar_con_misma_lista_areas_no_falla(self, mock_genai_client):
        """
        Test: Enviar las mismas áreas que ya tiene el comunicado.

        Given: Un comunicado con 'area_con_telegram' y 'area_sin_telegram'.
        When: Se envía exactamente esa misma lista en 'areas_interes'.
        Then: El servicio debe completar la operación sin errores y 
            la relación debe permanecer idéntica.
        """
        areas_actuales = [self.area_con_telegram, self.area_sin_telegram]
        self.comunicado_existente.areas_interes.set(areas_actuales)

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Título actualizado",
            "areas_interes": areas_actuales
        }
        
        servicio = ComunicadoService()

        try:
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )
        except Exception as e:
            self.fail(f"update_comunicado lanzó una excepción inesperada: {e}")

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.areas_interes.count(), 2)

        areas_finales = list(self.comunicado_existente.areas_interes.all())
        self.assertCountEqual(areas_finales, areas_actuales)

        self.assertEqual(self.comunicado_existente.embedding, [0.1, 0.2, 0.3])



    @patch('api.models.genai.Client')
    def test_actualizar_con_una_sola_area_valida(self, mock_genai_client):
        """
        Test: Pasar de varias áreas a una sola lista con un único objeto.

        Given: Un comunicado que inicialmente tiene 2 áreas.
        When: Se envía un payload con una lista que contiene solo 'area_con_telegram'.
        Then: La relación debe actualizarse para reflejar solo esa área.
        """
        areas_iniciales = [self.area_con_telegram, self.area_sin_telegram]
        self.comunicado_existente.areas_interes.set(areas_iniciales)

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.9, 0.8, 0.7])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        una_sola_area = [self.area_con_telegram]
        data_validada = {
            "titulo": "Actualización a área única",
            "areas_interes": una_sola_area
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.areas_interes.count(), 1)

        areas_finales = list(self.comunicado_existente.areas_interes.all())
        self.assertEqual(areas_finales, una_sola_area)
        self.assertNotIn(self.area_sin_telegram, areas_finales)



    @patch('api.models.genai.Client')
    def test_actualizar_con_multiple_areas_validas(self, mock_genai_client):
        """
        Test: Enviar múltiples áreas válidas en una actualización.
        """
        self.comunicado_existente.areas_interes.set([self.area_con_telegram])

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        area_extra = AreaInteres.objects.get_or_create(
            nombre_area=AreaInteres.NombreArea.CULTOS_FORMACION
        )[0]
        
        nuevas_areas = [
            self.area_con_telegram,
            self.area_sin_telegram,
            area_extra
        ]
        
        data_validada = {
            "titulo": "Título actualizado con múltiples áreas",
            "areas_interes": nuevas_areas
        }
        
        servicio = ComunicadoService()

        servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.areas_interes.count(), len(nuevas_areas))

        areas_finales = list(self.comunicado_existente.areas_interes.all())
        for area in nuevas_areas:
            self.assertIn(area, areas_finales)

        self.assertEqual(self.comunicado_existente.titulo, "Título actualizado con múltiples áreas")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_transaccion_confirmada_cuando_datos_son_validos(self, mock_generar_embedding):
        """
        Test: Confirmar que los cambios persisten en la BD al finalizar el servicio.
        
        Given: Un comunicado existente y datos válidos para actualizar.
        When: Se ejecuta update_comunicado satisfactoriamente.
        Then: Al recuperar el objeto de nuevo de la BD, los cambios deben estar allí
            y la tarea del embedding debe encolarse correctamente.
        """
        nuevo_titulo = "Título Post-Transacción"
        nuevas_areas = [self.area_con_telegram]
        data_validada = {
            "titulo": nuevo_titulo,
            "areas_interes": nuevas_areas
        }
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):
            resultado = servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        comunicado_db = Comunicado.objects.get(pk=self.comunicado_existente.pk)

        self.assertEqual(comunicado_db.titulo, nuevo_titulo)
        self.assertEqual(list(comunicado_db.areas_interes.all()), nuevas_areas)

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.pk)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_persistencia_total_tras_actualizacion_exitosa(self, mock_generar_embedding):
        """
        Test: Verificación de persistencia completa (Campos + M2M + Embedding).

        Given: Un comunicado con datos antiguos.
        When: Se actualizan múltiples campos y las áreas de interés.
        Then: La base de datos debe reflejar todos los cambios tras el commit
            y la regeneración del vector debe encolarse correctamente.
        """
        nuevas_areas = [self.area_con_telegram]
        data_validada = {
            "titulo": "Título Definitivo",
            "contenido": "Contenido verificado por transacciones",
            "areas_interes": nuevas_areas
        }
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        comunicado_final = Comunicado.objects.get(pk=self.comunicado_existente.pk)

        self.assertEqual(comunicado_final.titulo, "Título Definitivo")
        self.assertEqual(comunicado_final.contenido, "Contenido verificado por transacciones")

        self.assertEqual(comunicado_final.areas_interes.count(), 1)
        self.assertIn(self.area_con_telegram, comunicado_final.areas_interes.all())

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.pk)



    @patch('api.models.genai.Client')
    def test_update_comunicado_retorna_instancia_actualizada(self, mock_genai_client):
        """
        Test: El método retorna la instancia con sus atributos y relaciones actualizados.

        Given: Un comunicado existente y un conjunto de datos nuevos válidos.
        When: Se invoca al método update_comunicado del servicio.
        Then: El servicio debe retornar la misma instancia de objeto, pero con sus 
            campos directos (titulo) y relaciones (areas_interes) ya modificados.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.1, 0.1])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Título de retorno",
            "areas_interes": [self.area_con_telegram]
        }
        
        servicio = ComunicadoService()

        instancia_retornada = servicio.update_comunicado(
            usuario=self.admin, 
            comunicado_instance=self.comunicado_existente, 
            data_validada=data_validada
        )

        self.assertIs(instancia_retornada, self.comunicado_existente)

        self.assertEqual(instancia_retornada.titulo, "Título de retorno")
        self.assertEqual(instancia_retornada.pk, self.comunicado_existente.pk)

        self.assertIn(self.area_con_telegram, instancia_retornada.areas_interes.all())



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_update_comunicado_mantiene_referencia_de_memoria(self, mock_generar_embedding):
        """
        Test: Verificación de identidad del objeto retornado (Referencia de memoria).

        Given: Una instancia de comunicado existente.
        When: Se actualiza el comunicado a través del servicio.
        Then: El método debe retornar exactamente la misma instancia física en memoria 
            que se pasó como argumento, asegurando que no se realizan consultas redundantes,
            y encolar la tarea del embedding.
        """
        data_validada = {
            "titulo": "Cambio de título para verificar referencia",
            "areas_interes": [self.area_con_telegram]
        }
        
        servicio = ComunicadoService()
        instancia_original = self.comunicado_existente

        with self.captureOnCommitCallbacks(execute=True):
            instancia_retornada = servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=instancia_original, 
                data_validada=data_validada
            )

        self.assertIs(
            instancia_retornada, 
            instancia_original, 
            "El servicio devolvió un objeto nuevo en lugar de la misma instancia."
        )

        self.assertEqual(instancia_original.titulo, "Cambio de título para verificar referencia")

        mock_generar_embedding.assert_called_once_with(instancia_original.id)



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_usuario_sin_permisos_lanza_excepcion(self, mock_genai_client):
        """
        Test: Usuario sin permisos de administración ni de junta no puede actualizar.

        Given: Un comunicado existente y un usuario sin privilegios (esAdmin=False).
        When: Se intenta llamar a update_comunicado con dicho usuario.
        Then: El servicio debe lanzar una excepción PermissionDenied y no realizar cambios.
        """
        titulo_original = self.comunicado_existente.titulo
        data_validada = {
            "titulo": "Intento de hackeo de título"
        }
        
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.update_comunicado(
                usuario=self.usuario_base,
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(
            self.comunicado_existente.titulo, 
            titulo_original, 
            "El título cambió a pesar de que el usuario no tenía permisos."
        )

        mock_genai_client.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_usuario_anonimo_lanza_permission_denied(self, mock_genai_client):
        """
        Test: Un usuario anónimo (sin atributo esAdmin ni relación cuerpos) no tiene acceso.

        Given: Un comunicado existente y un objeto AnonymousUser que carece de atributos de Hermano.
        When: Se intenta ejecutar el método update_comunicado para modificar datos.
        Then: El servicio debe lanzar una excepción PermissionDenied antes de procesar 
            cualquier cambio, protegiendo la integridad de la BD y la cuota de la IA.
        """
        usuario_anonimo = AnonymousUser()
        titulo_previo = self.comunicado_existente.titulo
        
        data_validada = {
            "titulo": "Intento de edición por usuario no autenticado"
        }
        
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.update_comunicado(
                usuario=usuario_anonimo, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(
            self.comunicado_existente.titulo, 
            titulo_previo, 
            "La base de datos se modificó a pesar de ser un usuario anónimo."
        )

        mock_genai_client.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_hermano_sin_privilegios_lanza_permission_denied(self, mock_genai_client):
        """
        Test: Usuario con esAdmin=False y sin cuerpos de pertenencia no tiene acceso.

        Given: Un comunicado existente y un usuario (usuario_base) que es Hermano 
            pero no tiene cargos ni permisos de administración.
        When: Se intenta ejecutar el método update_comunicado.
        Then: El servicio debe lanzar una excepción PermissionDenied, garantizando que 
            solo el personal autorizado pueda modificar la información oficial.
        """
        titulo_previo = self.comunicado_existente.titulo
        data_validada = {
            "titulo": "Intento de modificación por usuario base"
        }
        
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.update_comunicado(
                usuario=self.usuario_base, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(
            self.comunicado_existente.titulo, 
            titulo_previo, 
            "El servicio permitió la modificación a un usuario sin privilegios."
        )

        mock_genai_client.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_usuario_en_otro_cuerpo_lanza_permission_denied(self, mock_genai_client):
        """
        Test: Usuario en un cuerpo distinto a JUNTA_GOBIERNO no tiene acceso.

        Given: Un comunicado existente y un usuario que pertenece al cuerpo de COSTALEROS.
        When: El usuario intenta actualizar el comunicado.
        Then: El servicio debe lanzar PermissionDenied, ya que estar en la nómina 
            de un cuerpo no administrativo no otorga permisos de gestión.
        """
        cuerpo_costaleros, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )
        HermanoCuerpo.objects.create(
            hermano=self.usuario_base,
            cuerpo=cuerpo_costaleros,
            anio_ingreso=2020
        )

        self.assertFalse(self.usuario_base.esAdmin)
        
        data_validada = {"titulo": "Nuevo título no autorizado"}
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.update_comunicado(
                usuario=self.usuario_base,
                comunicado_instance=self.comunicado_existente,
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertNotEqual(self.comunicado_existente.titulo, "Nuevo título no autorizado")

        mock_genai_client.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_usuario_con_esadmin_none_lanza_permission_denied(self, mock_genai_client):
        """
        Test: Usuario con esAdmin=None se trata como False y se deniega el acceso.

        Given: Un comunicado existente y un usuario cuyo atributo esAdmin es None.
        When: Se intenta ejecutar update_comunicado.
        Then: El servicio debe lanzar PermissionDenied, tratando el valor nulo 
            como falta de privilegios administrativos.
        """
        self.usuario_base.esAdmin = None 

        self.assertEqual(self.usuario_base.cuerpos.count(), 0)
        
        titulo_previo = self.comunicado_existente.titulo
        data_validada = {"titulo": "Título denegado por valor None"}
        
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.update_comunicado(
                usuario=self.usuario_base,
                comunicado_instance=self.comunicado_existente,
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)

        mock_genai_client.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_tipo_invalido_lanza_validation_error(self, mock_genai_client):
        """
        Test: Enviar un tipo_comunicacion que no existe en los Choices del modelo.

        Given: Un comunicado existente y un diccionario con un tipo de comunicación 
            inválido (ej: 'NIVEL').
        When: Se intenta actualizar el comunicado a través del servicio.
        Then: El modelo debe lanzar un ValidationError y la base de datos no debe 
            persistir el cambio erróneo.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        tipo_inexistente = "NIVEL"
        titulo_previo = self.comunicado_existente.titulo
        data_validada = {
            "titulo": "Intento de cambio de tipo",
            "tipo_comunicacion": tipo_inexistente
        }
        
        servicio = ComunicadoService()

        with self.assertRaises(ValidationError):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)
        self.assertNotEqual(self.comunicado_existente.tipo_comunicacion, tipo_inexistente)



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_titulo_none_lanza_validation_error(self, mock_genai_client):
        """
        Test: Enviar titulo=None (violando la restricción de CharField obligatorio).

        Given: Un comunicado existente y un payload con titulo=None.
        When: Se intenta actualizar a través del servicio.
        Then: El método full_clean del modelo debe detectar el nulo y lanzar ValidationError.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        data_validada = {
            "titulo": None,
            "contenido": "Contenido que no llegará a procesarse"
        }
        
        servicio = ComunicadoService()
        titulo_previo = self.comunicado_existente.titulo

        with self.assertRaises(ValidationError):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_titulo_vacio_lanza_validation_error(self, mock_genai_client):
        """
        Test: Enviar titulo="" (cadena vacía) en un campo obligatorio.

        Given: Un comunicado existente y un payload con titulo="".
        When: Se intenta actualizar a través del servicio.
        Then: El método full_clean() del modelo debe detectar que el campo 
            está vacío y lanzar un ValidationError.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        data_validada = {
            "titulo": "",
            "contenido": "Este contenido es válido, pero el título no."
        }
        
        servicio = ComunicadoService()
        titulo_previo = self.comunicado_existente.titulo

        with self.assertRaises(ValidationError):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)

        mock_client_instance.models.embed_content.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_autor_nulo_lanza_validation_error(self, mock_genai_client):
        """
        Test: Intentar dejar el autor como None (campo obligatorio).

        Given: Un comunicado existente y un payload con autor=None.
        When: Se intenta actualizar a través del servicio.
        Then: El modelo debe lanzar ValidationError o IntegrityError dependiendo 
            de en qué momento se detecte la violación de la FK.
        """
        data_validada = {
            "titulo": "Título válido",
            "autor": None
        }
        
        servicio = ComunicadoService()
        autor_original = self.comunicado_existente.autor

        with self.assertRaises((ValidationError, IntegrityError)):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.autor, autor_original)



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_autor_tipo_invalido_lanza_error(self, mock_genai_client):
        """
        Test: Intentar asignar un objeto de otro modelo en lugar de un Hermano.

        Given: Un comunicado existente y un objeto de base de datos que NO es un Hermano.
        When: Se intenta actualizar el autor a través del servicio.
        Then: El descriptor ForeignKey de Django debe lanzar un ValueError 
            al detectar el desajuste de tipos.
        """
        objeto_intruso = TipoPuesto.objects.create(nombre_tipo="Objeto Intruso para Test")
        
        data_validada = {
            "titulo": "Intento de autor inválido",
            "autor": objeto_intruso
        }
        
        servicio = ComunicadoService()
        autor_original = self.comunicado_existente.autor

        with self.assertRaises((ValidationError, IntegrityError, ValueError)):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.autor, autor_original)



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_campo_inexistente_lanza_attribute_error(self, mock_genai_client):
        """
        Test: Enviar un campo que no existe en el modelo Comunicado.

        Given: Un comunicado existente y un payload con una clave 'campo_fantasma'.
        When: Se intenta actualizar a través del servicio.
        Then: El servicio debe lanzar AttributeError al intentar asignar el valor.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
        mock_client_instance.models.embed_content.return_value = mock_resultado

        data_validada = {
            "titulo": "Nuevo Título",
            "campo_fantasma": "Este campo no existe en la BD"
        }
        
        servicio = ComunicadoService()
        titulo_previo = self.comunicado_existente.titulo

        with self.assertRaises(AttributeError):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, titulo_previo)



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_fecha_tipo_incorrecto_lanza_validation_error(self, mock_genai_client):
        """
        Test: Enviar un valor de tipo incorrecto (string en vez de fecha).

        Given: Un comunicado existente y un payload con fecha_emision="basura".
        When: Se intenta actualizar a través del servicio.
        Then: El método full_clean del modelo debe detectar el error de tipo y lanzar ValidationError.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        data_validada = {
            "titulo": "Título correcto",
            "fecha_emision": "esto-no-es-una-fecha-valida"
        }
        
        servicio = ComunicadoService()
        fecha_original = self.comunicado_existente.fecha_emision

        with self.assertRaises(ValidationError):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.fecha_emision, fecha_original)



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_areas_no_persistidas_lanza_error(self, mock_genai_client):
        """
        Test: Enviar una lista de áreas de interés con objetos que no están en la BD.

        Given: Un comunicado existente y un objeto AreaInteres nuevo (no guardado).
        When: Se intenta actualizar a través del servicio.
        Then: Django lanzará un ValueError al intentar hacer el .set() de la relación M2M.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        area_fantasma = AreaInteres(nombre_area=AreaInteres.NombreArea.CARIDAD)
        
        data_validada = {
            "titulo": "Título Válido",
            "areas_interes": [area_fantasma]
        }
        
        servicio = ComunicadoService()

        with self.assertRaises(ValueError):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(
            self.comunicado_existente.areas_interes.count(), 
            1,
            "El número de áreas de interés fue modificado a pesar del error."
        )



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_areas_none_lanza_error(self, mock_genai_client):
        """
        Test: Enviar areas_interes=None.

        Given: Un comunicado existente y un payload con 'areas_interes': None.
        When: El servicio intenta hacer .set(None).
        Then: Debe lanzar un TypeError (o ValueError según la versión de Django).
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        data_validada = {
            "titulo": "Título Válido",
            "areas_interes": None
        }
        
        servicio = ComunicadoService()

        areas_originales_count = self.comunicado_existente.areas_interes.count()

        with self.assertRaises((TypeError, ValueError)):
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.areas_interes.count(), areas_originales_count)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_actualizar_comunicado_ok_incluso_si_falla_ia(self, mock_generar_embedding):
        """
        Test: Tolerancia a fallos de servicios externos (No debe haber rollback).
        
        Given: Un comunicado existente.
        When: Se intenta actualizar el título, pero simulamos que el encolado de la tarea de IA falla.
        Then: La base de datos DEBE guardar los cambios exitosamente, aislando el 
            fallo de la IA del flujo principal del usuario.
        """
        mock_generar_embedding.side_effect = Exception("Google AI Service Unavailable")

        data_validada = {
            "titulo": "ESTE TITULO SÍ DEBE GUARDARSE",
            "contenido": "Contenido nuevo"
        }
        
        servicio = ComunicadoService()

        try:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                servicio.update_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=self.comunicado_existente, 
                    data_validada=data_validada
                )
        except Exception as e:
            self.assertIn("Google AI Service Unavailable", str(e))

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(
            self.comunicado_existente.titulo, 
            "ESTE TITULO SÍ DEBE GUARDARSE",
            "ERROR: Ocurrió un rollback inesperado."
        )

        self.assertEqual(self.comunicado_existente.contenido, "Contenido nuevo")

        mock_generar_embedding.assert_called_once_with(self.comunicado_existente.id)



    @patch('api.models.Comunicado.save')
    def test_actualizar_comunicado_rollback_areas_si_falla_save(self, mock_save):
        """
        Test: Atomicidad de la transacción al fallar el guardado final.

        Given: Un comunicado existente y un payload que modifica las áreas de interés.
        When: Se aplica el .set() en BD, pero ocurre un error inesperado al guardar el modelo.
        Then: @transaction.atomic debe revertir la asignación de las áreas en la BD.
        """
        mock_save.side_effect = Exception("Fallo catastrófico en base de datos")

        areas_originales = list(self.comunicado_existente.areas_interes.all())
        titulo_original = self.comunicado_existente.titulo

        data_validada = {
            "titulo": "Título nuevo que no se guardará",
            "areas_interes": [self.area_con_telegram]
        }
        
        servicio = ComunicadoService()

        with self.assertRaises(Exception) as context:
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )
        
        self.assertIn("Fallo catastrófico en base de datos", str(context.exception))

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(self.comunicado_existente.titulo, titulo_original)

        self.assertEqual(
            list(self.comunicado_existente.areas_interes.all()), 
            areas_originales,
            "Error fatal: El .set() no se revirtió. Falta atomicidad en la transacción."
        )



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_usuario_sin_permisos_no_modifica_instancia(self, mock_genai_client):
        """
        Test: Simular excepción en _verificar_permisos.

        Given: Un usuario raso (sin permisos) y un payload válido.
        When: Intenta llamar al servicio para actualizar el comunicado.
        Then: Se lanza PermissionDenied inmediatamente y la instancia queda intacta.
        """
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        data_validada = {
            "titulo": "Intento de hackeo",
            "contenido": "Este texto no debe llegar a la base de datos"
        }
        
        servicio = ComunicadoService()
        titulo_original = self.comunicado_existente.titulo

        with self.assertRaises(PermissionDenied):
            servicio.update_comunicado(
                usuario=self.usuario_base,
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )

        self.comunicado_existente.refresh_from_db()

        self.assertEqual(
            self.comunicado_existente.titulo, 
            titulo_original,
            "Error: El título fue modificado por un usuario sin permisos."
        )

        mock_client_instance.models.embed_content.assert_not_called()



    @patch('api.models.genai.Client')
    def test_actualizar_comunicado_fallo_en_setattr_no_persiste_nada(self, mock_genai_client):
        """
        Test: Simular excepción durante la asignación de atributos (setattr).
        
        Given: Un comunicado cuya propiedad 'titulo' lanza un error al ser modificada.
        When: El servicio intenta iterar sobre data_validada y asignar el nuevo título.
        Then: La excepción aborta el proceso y la base de datos no sufre cambios.
        """
        titulo_original = "Comunicado Original"
        self.comunicado_existente.titulo = titulo_original
        self.comunicado_existente.save()

        type(self.comunicado_existente).titulo = PropertyMock(side_effect=RuntimeError("Fallo físico en memoria"))

        data_validada = {
            "titulo": "ESTO VA A FALLAR",
            "contenido": "Contenido que nunca se guardará"
        }
        
        servicio = ComunicadoService()

        with self.assertRaises(RuntimeError) as context:
            servicio.update_comunicado(
                usuario=self.admin, 
                comunicado_instance=self.comunicado_existente, 
                data_validada=data_validada
            )
        
        self.assertEqual(str(context.exception), "Fallo físico en memoria")

        del type(self.comunicado_existente).titulo

        self.comunicado_existente.refresh_from_db()
        self.assertEqual(self.comunicado_existente.titulo, titulo_original)

        mock_genai_client.assert_not_called()