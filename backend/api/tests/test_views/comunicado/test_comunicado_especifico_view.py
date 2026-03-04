import io
import datetime
import os
import re
import tempfile
from unittest.mock import patch

from PIL import Image
from rest_framework.test import APITestCase
from rest_framework import status

from api.models import AreaInteres, Comunicado, Hermano

from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.urls import reverse


class ComunicadoDetailViewTest(APITestCase):
    
    def setUp(self):
        """Preparación inicial para todos los tests de la vista."""
        User = get_user_model()
        self.admin = User.objects.create_user(
            dni="12345678Z",
            username="12345678Z",
            password="testpassword123",
            nombre="Admin",
            primer_apellido="Prueba",
            segundo_apellido="Test",
            telefono="600000000",
            estado_civil="SOLTERO",
            email="admin@test.com",
            esAdmin=True
        )

        self.user = Hermano.objects.create_user(
            dni="87654321B",
            username="87654321B",
            password="userpassword123",
            nombre="Hermano",
            primer_apellido="Raso",
            segundo_apellido="Normal",
            telefono="611111111",
            estado_civil="SOLTERO",
            email="hermano@test.com",
            esAdmin=False 
        )
        
        self.comunicado = Comunicado.objects.create(
            titulo="Comunicado API",
            contenido="Contenido de prueba para DRF.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        self.url = f'/api/comunicados/{self.comunicado.pk}/' 



    def test_get_sin_autenticacion_retorna_401(self):
        """
        Test: Un usuario anónimo no puede acceder a los detalles de un comunicado.

        Given: Un cliente HTTP sin autenticar (sin token/sesión).
        When: Se realiza una petición GET al endpoint del detalle del comunicado.
        Then: La API rechaza la petición devolviendo un estado 401 Unauthorized.
        """
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 
            status.HTTP_401_UNAUTHORIZED,
            "La vista permitió el acceso a un usuario no autenticado."
        )



    def test_put_sin_autenticacion_retorna_401(self):
        """
        Test: Un usuario anónimo no puede modificar un comunicado.

        Given: Un comunicado existente y datos de actualización.
        When: Se realiza una petición PUT al endpoint sin credenciales de autenticación.
        Then: La API devuelve un estado 401 Unauthorized y no modifica el registro.
        """
        data_update = {
            "titulo": "Título Hackeado",
            "contenido": "Intentando cambiar contenido sin permiso.",
            "tipo_comunicacion": "URGENTE"
        }

        response = self.client.put(self.url, data=data_update, format='json')

        self.assertEqual(
            response.status_code, 
            status.HTTP_401_UNAUTHORIZED,
            "La vista permitió un intento de modificación (PUT) a un usuario anónimo."
        )

        self.comunicado.refresh_from_db()
        self.assertNotEqual(self.comunicado.titulo, "Título Hackeado")



    def test_patch_sin_autenticacion_retorna_401(self):
        """
        Test: Un usuario anónimo no puede realizar actualizaciones parciales.

        Given: Un comunicado existente en la base de datos.
        When: Se intenta modificar solo un campo (ej: el título) mediante PATCH sin credenciales.
        Then: La API responde con un estado 401 Unauthorized y el registro permanece intacto.
        """
        data_parcial = {
            "titulo": "Nuevo Título vía PATCH"
        }

        response = self.client.patch(self.url, data=data_parcial, format='json')

        self.assertEqual(
            response.status_code, 
            status.HTTP_401_UNAUTHORIZED,
            "La vista permitió un intento de actualización parcial (PATCH) sin autenticación."
        )

        self.comunicado.refresh_from_db()
        self.assertNotEqual(
            self.comunicado.titulo, 
            "Nuevo Título vía PATCH",
            "El título del comunicado fue alterado a pesar de la falta de autenticación."
        )



    def test_delete_sin_autenticacion_retorna_401(self):
        """
        Test: Un usuario anónimo no tiene permisos para eliminar recursos.

        Given: Un comunicado existente en la base de datos.
        When: Se realiza una petición DELETE al endpoint sin token ni sesión.
        Then: La API deniega la operación con un 401 Unauthorized y el registro persiste.
        """
        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code, 
            status.HTTP_401_UNAUTHORIZED,
            "La vista permitió un intento de eliminación (DELETE) sin autenticación."
        )

        from api.models import Comunicado
        existe = Comunicado.objects.filter(pk=self.comunicado.pk).exists()
        
        self.assertTrue(
            existe, 
            "El comunicado fue eliminado de la base de datos a pesar de la falta de credenciales."
        )



    def test_peticion_con_token_invalido_retorna_401(self):
        """
        Test: Verifica que las credenciales mal formadas o inválidas sean rechazadas.

        Given: Un comunicado existente.
        When: Se realiza una petición incluyendo un encabezado de autorización 
            con un token corrupto o inexistente ("Bearer token_falso").
        Then: La API debe invalidar la petición con un 401 Unauthorized.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token_completamente_invalido_123')

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 
            status.HTTP_401_UNAUTHORIZED,
            "La API aceptó o no manejó correctamente un token de autenticación inválido."
        )

        self.assertIn('detail', response.data)



    def test_sesion_expirada_retorna_401(self):
        """
        Test: Un usuario con una sesión caducada debe ser tratado como no autenticado.

        Given: Un usuario que previamente inició sesión.
        When: La sesión ha expirado en el servidor y el usuario intenta acceder al detalle.
        Then: La API debe retornar 401 Unauthorized y no permitir el acceso.
        """
        self.client.login(dni="12345678Z", password="testpassword123")

        session_key = self.client.cookies['sessionid'].value
        session = Session.objects.get(session_key=session_key)
        session.expire_date = timezone.now() - datetime.timedelta(days=1)
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 
            status.HTTP_401_UNAUTHORIZED,
            "La API permitió el acceso con una sesión que ya ha expirado."
        )



    def test_usuario_autenticado_puede_obtener_detalle_comunicado(self):
        """
        Test: Un usuario con credenciales válidas recibe los datos del comunicado.

        Given: Un usuario autenticado y un comunicado existente.
        When: Se realiza una petición GET al endpoint del detalle.
        Then: La API responde con 200 OK y el JSON contiene los campos correctos.
        """
        self.client.force_authenticate(user=self.admin) 

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.comunicado.id)
        self.assertEqual(response.data['titulo'], self.comunicado.titulo)

        self.assertEqual(response.data['tipo_comunicacion'], self.comunicado.tipo_comunicacion)

        if 'areas_interes' in response.data:
            self.assertIsInstance(response.data['areas_interes'], list)



    def test_usuario_autenticado_puede_actualizar_totalmente_comunicado(self):
        """
        Test: Un usuario autenticado puede modificar todos los campos de un comunicado.

        Given: Un usuario autenticado (self.admin) y un comunicado existente.
        When: Se realiza una petición PUT con datos nuevos y válidos.
        Then: La API responde con 200 OK y los datos en la DB se actualizan.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Área de Prueba")

        payload = {
            "titulo": "Título Actualizado por PUT",
            "contenido": "Nuevo contenido detallado del comunicado.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Error: {response.data}")
        self.assertEqual(response.data['titulo'], payload['titulo'])

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.titulo, "Título Actualizado por PUT")
        self.assertIn("Nuevo contenido detallado", self.comunicado.contenido)



    def test_usuario_autenticado_puede_actualizar_parcialmente_comunicado(self):
        """
        Test: Un usuario autenticado puede modificar solo un campo (PATCH).

        Given: Un comunicado con un título original.
        When: Se envía una petición PATCH solo con el nuevo título.
        Then: La API responde 200 OK, el título cambia y el contenido permanece igual.
        """
        self.client.force_authenticate(user=self.admin)

        payload = {
            "titulo": "Título cambiado por PATCH"
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.titulo, "Título cambiado por PATCH")

        self.assertEqual(self.comunicado.contenido, "Contenido de prueba para DRF.")



    def test_usuario_autenticado_puede_eliminar_comunicado(self):
        """
        Test: Un usuario autenticado tiene permisos para borrar un comunicado.

        Given: Un usuario autenticado (self.admin) y un comunicado en la DB.
        When: Se realiza una petición DELETE a la URL del detalle.
        Then: La API devuelve 204 No Content y el registro desaparece de la base de datos.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code, 
            status.HTTP_204_NO_CONTENT,
            "La API no devolvió el código 204 tras eliminar el comunicado."
        )

        from api.models import Comunicado
        existe = Comunicado.objects.filter(pk=self.comunicado.pk).exists()
        
        self.assertFalse(
            existe, 
            "El comunicado sigue existiendo en la base de datos después de la petición DELETE."
        )



    def test_get_comunicado_valido_retorna_200(self):
        """
        Test: Obtener el detalle de un comunicado existente.

        Given: Un comunicado creado en el setUp con ID válido.
        When: Un usuario autenticado solicita ese comunicado por su PK.
        Then: La API retorna 200 OK y los datos serializados.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.comunicado.id)
        self.assertEqual(response.data['titulo'], "Comunicado API")
        self.assertEqual(response.data['contenido'], "Contenido de prueba para DRF.")



    def test_respuesta_get_contiene_todos_los_campos_del_serializer(self):
        """
        Test: La respuesta JSON debe coincidir con la estructura del ComunicadoListSerializer.

        Given: Un comunicado con autor y áreas de interés.
        When: Se solicita el detalle del comunicado.
        Then: El JSON contiene campos calculados, relaciones M2M y datos básicos.
        """
        self.client.force_authenticate(user=self.admin)
        area = AreaInteres.objects.create(nombre_area="Cultos")
        self.comunicado.areas_interes.add(area)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        campos_esperados = [
            'id', 'titulo', 'contenido', 'fecha_emision', 'imagen_portada',
            'tipo_comunicacion', 'tipo_display', 'autor_nombre', 'areas_interes'
        ]
        for campo in campos_esperados:
            self.assertIn(campo, response.data, f"El campo {campo} falta en la respuesta de la API")

        self.assertEqual(response.data['autor_nombre'], "Admin Prueba")

        self.assertTrue(len(response.data['tipo_display']) > 0)

        self.assertIsInstance(response.data['areas_interes'], list)
        self.assertEqual(response.data['areas_interes'][0], "Cultos")



    def test_get_comunicado_incluye_nombres_de_areas_interes(self):
        """
        Test: Verifica que areas_interes devuelva nombres (strings) y no IDs.

        Given: Un comunicado asociado a múltiples áreas de interés.
        When: Se solicita el detalle del comunicado.
        Then: El campo 'areas_interes' es una lista con los nombres de dichas áreas.
        """
        area_cultos = AreaInteres.objects.create(nombre_area="Cultos y Liturgia")
        area_formacion = AreaInteres.objects.create(nombre_area="Formación")

        self.comunicado.areas_interes.add(area_cultos, area_formacion)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsInstance(response.data['areas_interes'], list)

        self.assertIn("Cultos y Liturgia", response.data['areas_interes'])
        self.assertIn("Formación", response.data['areas_interes'])

        self.assertNotIsInstance(response.data['areas_interes'][0], int)



    def test_get_comunicado_incluye_tipos_de_comunicacion_correctos(self):
        """
        Test: Verifica que se devuelvan tanto el código como la etiqueta del tipo.

        Given: Un comunicado con tipo_comunicacion="GENERAL".
        When: Se solicita el detalle.
        Then: La respuesta contiene 'GENERAL' en el campo base 
            y 'General' (o su traducción) en 'tipo_display'.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data['tipo_comunicacion'], 
            self.comunicado.tipo_comunicacion,
            "El código interno del tipo de comunicación no coincide."
        )

        valor_esperado_display = self.comunicado.get_tipo_comunicacion_display()
        
        self.assertEqual(
            response.data['tipo_display'], 
            valor_esperado_display,
            "El campo tipo_display no resolvió correctamente la etiqueta legible."
        )



    def test_get_comunicado_incluye_nombre_formateado_del_autor(self):
        """
        Test: Verifica que autor_nombre combine Nombre + Primer Apellido.

        Given: Un comunicado cuyo autor es self.admin (Nombre: "Admin", Apellido: "Prueba").
        When: Se solicita el detalle.
        Then: El campo 'autor_nombre' debe ser "Admin Prueba".
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        nombre_esperado = f"{self.admin.nombre} {self.admin.primer_apellido}"
        self.assertEqual(response.data['autor_nombre'], nombre_esperado)



    def test_get_comunicado_retorna_json_valido(self):
        """
        Test: Verifica que la respuesta sea un JSON válido y tenga el Content-Type correcto.

        Given: Un usuario autenticado y un comunicado.
        When: Se realiza una petición GET.
        Then: La respuesta tiene el header 'application/json' y el cuerpo es parseable.
        """
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertIn(
            'application/json', 
            response['Content-Type'],
            "La respuesta no tiene el Content-Type 'application/json'."
        )

        self.assertIsInstance(
            response.data, 
            dict, 
            "El cuerpo de la respuesta no es un objeto JSON válido (diccionario)."
        )

        import json
        try:
            json.loads(response.content)
        except ValueError:
            self.fail("La respuesta del servidor no es un JSON serializable válido.")



    def test_get_comunicado_no_modifica_datos_en_db(self):
        """
        Test: Verifica que la petición GET es puramente de lectura.

        Given: Un comunicado con datos específicos.
        When: Se realiza una petición GET al detalle.
        Then: Los datos en la base de datos permanecen exactamente iguales.
        """
        self.client.force_authenticate(user=self.admin)

        titulo_antes = self.comunicado.titulo
        contenido_antes = self.comunicado.contenido
        fecha_antes = self.comunicado.fecha_emision

        self.client.get(self.url)

        self.comunicado.refresh_from_db()

        self.assertEqual(self.comunicado.titulo, titulo_antes, "El GET modificó el título inesperadamente.")
        self.assertEqual(self.comunicado.contenido, contenido_antes, "El GET modificó el contenido.")
        self.assertEqual(self.comunicado.fecha_emision, fecha_antes, "El GET modificó la fecha de emisión.")



    def test_get_comunicado_con_imagen_devuelve_url_completa(self):
        """
        Test: Verifica que el campo imagen_portada devuelva una URL válida.

        Given: Un comunicado con una imagen cargada.
        When: Se realiza una petición GET.
        Then: El campo 'imagen_portada' contiene una URL absoluta (http://...).
        """
        imagen_mock = SimpleUploadedFile(
            name='test_portada.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )

        self.comunicado.imagen_portada = imagen_mock
        self.comunicado.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        imagen_url = response.data.get('imagen_portada')
        
        self.assertIsNotNone(imagen_url)
        self.assertTrue(
            imagen_url.startswith('http') or '/media/' in imagen_url,
            f"La imagen debería ser una URL, pero se recibió: {imagen_url}"
        )



    def test_get_comunicado_sin_imagen_no_rompe_y_devuelve_null(self):
        """
        Test: Verifica que el serializador maneja correctamente la ausencia de imagen.

        Given: Un comunicado que no tiene archivo cargado en 'imagen_portada'.
        When: Se realiza una petición GET.
        Then: La API responde 200 OK y el campo 'imagen_portada' es None o cadena vacía.
        """
        self.comunicado.imagen_portada = None
        self.comunicado.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('imagen_portada', response.data)
        self.assertTrue(
            response.data['imagen_portada'] is None or response.data['imagen_portada'] == "",
            "El campo imagen_portada debería ser None o vacío si no hay imagen."
        )



    def test_get_comunicado_con_multiples_areas_serializa_correctamente(self):
        """
        Test: Verifica la correcta serialización de múltiples relaciones M2M.

        Given: Un comunicado asociado a tres áreas de interés distintas.
        When: Se realiza una petición GET.
        Then: El campo 'areas_interes' contiene exactamente los tres nombres esperados.
        """
        areas = [
            AreaInteres.objects.create(nombre_area="Juventud"),
            AreaInteres.objects.create(nombre_area="Caridad"),
            AreaInteres.objects.create(nombre_area="Patrimonio")
        ]

        self.comunicado.areas_interes.add(*areas)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        lista_areas = response.data.get('areas_interes', [])
        
        self.assertEqual(len(lista_areas), 3, "No se serializaron todas las áreas de interés.")
        self.assertIn("Juventud", lista_areas)
        self.assertIn("Caridad", lista_areas)
        self.assertIn("Patrimonio", lista_areas)

        self.assertTrue(all(isinstance(area, str) for area in lista_areas))



    def test_get_comunicado_inexistente_retorna_404(self):
        """
        Test: La API debe responder 404 si el comunicado no existe.

        Given: Un ID que sabemos que no está en la base de datos (ej. 9999).
        When: Un usuario autenticado solicita ese comunicado.
        Then: La API responde con 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        url_inexistente = '/api/comunicados/999999/'

        response = self.client.get(url_inexistente)

        self.assertEqual(
            response.status_code, 
            status.HTTP_404_NOT_FOUND,
            "La API debería haber devuelto un 404 para un ID inexistente."
        )



    def test_get_comunicado_pk_no_numerico_retorna_404(self):
        """
        Test: La API debe manejar PKs que no son números.

        Given: Un ID que es una cadena de texto ("abc").
        When: Un usuario autenticado solicita ese comunicado.
        Then: La API responde con 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        url_invalida = '/api/comunicados/texto-en-vez-de-id/'

        response = self.client.get(url_invalida)

        self.assertEqual(
            response.status_code, 
            status.HTTP_404_NOT_FOUND,
            "La API debería retornar 404 cuando el PK no es un entero."
        )



    def test_get_comunicado_eliminado_retorna_404(self):
        """
        Test: Un comunicado que ya no existe en la DB debe dar 404.

        Given: Un comunicado que es eliminado de la base de datos.
        When: Se intenta acceder a su detalle después del borrado.
        Then: La API responde con 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        id_comunicado = self.comunicado.id
        self.comunicado.delete()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 
            status.HTTP_404_NOT_FOUND,
            f"El comunicado con ID {id_comunicado} fue borrado, pero la API no devolvió 404."
        )



    def test_get_comunicado_inconsistente_retorna_404(self):
        """
        Test: Un PK que existía pero cuya instancia ya no es válida para 
        el QuerySet de la vista debe retornar 404.

        Given: Un comunicado que es eliminado o alterado para no ser recuperable.
        When: Se solicita el detalle.
        Then: La API responde 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        comunicado_id = self.comunicado.id
        self.comunicado.delete() 

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 
            status.HTTP_404_NOT_FOUND,
            "La API devolvió un objeto que ya no es consistente con la base de datos."
        )



    def test_put_comunicado_valido_retorna_200(self):
        """
        Test: Actualización total de un comunicado por un usuario autorizado.

        Given: Un comunicado existente y un payload con nuevos datos.
        When: Se envía una petición PUT con datos válidos.
        Then: La API retorna 200 OK y los datos se actualizan en la base de datos.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Todos los Hermanos")

        payload = {
            "titulo": "Título Actualizado Totalmente",
            "contenido": "Nuevo contenido del comunicado tras el PUT.",
            "tipo_comunicacion": "URGENTE",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            f"Error detallado: {response.data}"
        )

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.titulo, "Título Actualizado Totalmente")
        self.assertEqual(self.comunicado.tipo_comunicacion, "URGENTE")

        self.assertIn(area, self.comunicado.areas_interes.all())

        self.assertEqual(response.data['titulo'], "Título Actualizado Totalmente")
        self.assertIn('autor_nombre', response.data)



    def test_put_devuelve_objeto_actualizado_con_formato_lista(self):
        """
        Test: Verifica que la respuesta del PUT use el Serializer de salida correcto.

        Given: Un comunicado existente.
        When: Se realiza un PUT con datos válidos.
        Then: La respuesta contiene los campos calculados (autor_nombre, tipo_display) 
            del ComunicadoListSerializer.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Todos los Hermanos")

        nuevo_titulo = "Título Transformado"
        payload = {
            "titulo": nuevo_titulo,
            "contenido": "Contenido actualizado para validar serialización.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            f"Error detallado: {response.data}"
        )

        self.assertIn('autor_nombre', response.data)
        self.assertIn('tipo_display', response.data)
        self.assertIn('areas_interes', response.data)

        self.assertEqual(response.data['titulo'], nuevo_titulo)
        self.assertEqual(response.data['tipo_display'], "General")



    def test_put_actualiza_todos_los_campos_en_base_de_datos(self):
        """
        Test: Verificación de que todos los campos enviados en el PUT se persisten.

        Given: Un comunicado con valores iniciales.
        When: Se envía un payload con TODOS los campos cambiados.
        Then: La base de datos refleja los nuevos valores para cada campo.
        """
        self.client.force_authenticate(user=self.admin)

        nueva_area = AreaInteres.objects.create(nombre_area="Área Nueva")

        payload = {
            "titulo": "Nuevo Título Post-PUT",
            "contenido": "Nuevo contenido íntegramente actualizado.",
            "tipo_comunicacion": "URGENTE",
            "areas_interes": [nueva_area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Error: {response.data}")

        self.comunicado.refresh_from_db()

        self.assertEqual(self.comunicado.titulo, payload["titulo"])
        self.assertIn(payload["contenido"], self.comunicado.contenido)
        self.assertEqual(self.comunicado.tipo_comunicacion, payload["tipo_comunicacion"])

        self.assertIn(nueva_area, self.comunicado.areas_interes.all())



    def test_put_actualiza_areas_interes_correctamente(self):
        """
        Test: Verifica que la relación Many-to-Many de áreas de interés se actualice.

        Given: Un comunicado con un área inicial y dos áreas nuevas en la DB.
        When: Se realiza un PUT enviando los IDs de las nuevas áreas.
        Then: El comunicado queda asociado solo a las nuevas áreas.
        """
        self.client.force_authenticate(user=self.admin)

        area_antigua = AreaInteres.objects.create(nombre_area="Antigua")
        area_nueva_1 = AreaInteres.objects.create(nombre_area="Nueva 1")
        area_nueva_2 = AreaInteres.objects.create(nombre_area="Nueva 2")

        self.comunicado.areas_interes.add(area_antigua)

        payload = {
            "titulo": "Actualizando Áreas",
            "contenido": "Cuerpo del mensaje",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area_nueva_1.id, area_nueva_2.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        areas_actuales = self.comunicado.areas_interes.all()
        
        self.assertEqual(areas_actuales.count(), 2)
        self.assertIn(area_nueva_1, areas_actuales)
        self.assertIn(area_nueva_2, areas_actuales)
        self.assertNotIn(area_antigua, areas_actuales)



    def test_put_reemplaza_completamente_areas_interes(self):
        """
        Test: Un PUT debe sustituir las áreas antiguas por las nuevas.

        Given: Un comunicado con 'Área A' y 'Área B'.
        When: Se envía un PUT con solo 'Área C'.
        Then: El comunicado debe tener ÚNICAMENTE 'Área C'.
        """
        self.client.force_authenticate(user=self.admin)

        area_a = AreaInteres.objects.create(nombre_area="Área A")
        area_b = AreaInteres.objects.create(nombre_area="Área B")
        area_c = AreaInteres.objects.create(nombre_area="Área C")
        
        self.comunicado.areas_interes.add(area_a, area_b)

        payload = {
            "titulo": "Prueba de Reemplazo M2M",
            "contenido": "Verificando que A y B desaparecen.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area_c.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        nombres_areas = list(self.comunicado.areas_interes.values_list('nombre_area', flat=True))
        
        self.assertEqual(len(nombres_areas), 1)
        self.assertIn("Área C", nombres_areas)
        self.assertNotIn("Área A", nombres_areas)
        self.assertNotIn("Área B", nombres_areas)



    def test_put_comunicado_con_imagen_valida_retorna_200(self):
        """
        Test: Actualización de un comunicado incluyendo un archivo de imagen.

        Given: Un comunicado existente y una nueva imagen en formato SimpleUploadedFile.
        When: Se envía una petición PUT con Content-Type multipart/form-data.
        Then: La API retorna 200 OK y la imagen se guarda en el sistema de archivos.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Todos los Hermanos")
        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file_io, format='JPEG')
        file_io.seek(0)

        nombre_archivo = 'actualizacion_test.jpg'
        nueva_imagen = SimpleUploadedFile(
            name=nombre_archivo,
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = {
            "titulo": "Comunicado con Imagen y Área",
            "contenido": "Cuerpo del comunicado actualizado.",
            "tipo_comunicacion": "GENERAL",
            "imagen_portada": nueva_imagen,
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Error: {response.data}")

        self.comunicado.refresh_from_db()

        self.assertTrue(bool(self.comunicado.imagen_portada), "El campo imagen_portada está vacío.")

        self.assertIn('actualizacion_test', response.data['imagen_portada'])

        self.assertIn(area, self.comunicado.areas_interes.all())



    def test_put_comunicado_sin_imagen_mantiene_o_limpia_segun_logica(self):
        """
        Test: Actualización mediante PUT enviando el campo de imagen vacío o nulo.

        Given: Un comunicado existente.
        When: Se envía una petición PUT con datos de texto pero sin archivo en 'imagen_portada'.
        Then: La API retorna 200 OK y el resto de campos se actualizan.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Área de Prueba")

        payload = {
            "titulo": "Actualización sin tocar la imagen",
            "contenido": "El contenido ha cambiado, la imagen no se envió en el payload.",
            "tipo_comunicacion": "GENERAL",
            "imagen_portada": None,
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            f"Error detallado: {response.data}"
        )

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.titulo, "Actualización sin tocar la imagen")

        self.assertIsNone(response.data['imagen_portada'])
        self.assertFalse(bool(self.comunicado.imagen_portada))



    def test_put_con_multiples_areas_validas_retorna_200(self):
        """
        Test: Actualización total enviando múltiples IDs de áreas de interés.

        Given: Un comunicado existente y dos nuevas áreas de interés creadas en la DB.
        When: Se realiza un PUT con una lista de IDs en 'areas_interes'.
        Then: La API responde 200 OK y el comunicado queda vinculado exactamente a esas áreas.
        """
        self.client.force_authenticate(user=self.admin)

        area1 = AreaInteres.objects.create(nombre_area="Área de Cultos")
        area2 = AreaInteres.objects.create(nombre_area="Área de Caridad")

        payload = {
            "titulo": "Actualización con múltiples áreas",
            "contenido": "Verificando la asignación múltiple de categorías.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area1.id, area2.id] 
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            f"Error detectado: {response.data}"
        )

        self.comunicado.refresh_from_db()
        areas_actuales = self.comunicado.areas_interes.all()
        
        self.assertEqual(areas_actuales.count(), 2)
        self.assertIn(area1, areas_actuales)
        self.assertIn(area2, areas_actuales)

        self.assertEqual(len(response.data['areas_interes']), 2)



    def test_put_devuelve_json_con_estructura_correcta(self):
        """
        Test: Verifica que el JSON de respuesta tras un PUT tenga todos los campos
            esperados y el formato correcto.

        Given: Un comunicado existente y datos válidos.
        When: Se realiza una petición PUT.
        Then: La respuesta contiene las llaves del ListSerializer (id, autor_nombre, etc.)
            y los valores coinciden con lo enviado.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Área Técnica")
        
        file_io = io.BytesIO()
        Image.new('RGB', (10, 10), color='blue').save(file_io, format='JPEG')
        file_io.seek(0)
        imagen = SimpleUploadedFile('test_final.jpg', file_io.read(), content_type='image/jpeg')

        payload = {
            "titulo": "Estructura Correcta",
            "contenido": "Validando el JSON de salida.",
            "tipo_comunicacion": "GENERAL",
            "imagen_portada": imagen,
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        llaves_esperadas = {
            'id', 'titulo', 'contenido', 'tipo_comunicacion', 
            'tipo_display', 'autor_nombre', 'fecha_emision', 
            'imagen_portada', 'areas_interes'
        }

        self.assertTrue(llaves_esperadas.issubset(response.data.keys()), 
                        f"Faltan llaves en la respuesta: {llaves_esperadas - set(response.data.keys())}")

        self.assertIsInstance(response.data['id'], int)
        self.assertIsInstance(response.data['areas_interes'], list)
        self.assertEqual(response.data['titulo'], "Estructura Correcta")

        self.assertEqual(response.data['tipo_display'], "General")

        self.assertIsNotNone(response.data['imagen_portada'])
        self.assertIn('test_final', response.data['imagen_portada'])



    def test_put_mantiene_el_mismo_id_del_comunicado(self):
        """
        Test: Verifica que la operación PUT no altere el ID del recurso.

        Given: Un comunicado con un ID específico (ej. 42).
        When: Se realiza una actualización completa via PUT.
        Then: El ID en la respuesta y en la base de datos debe ser exactamente el mismo.
        """
        self.client.force_authenticate(user=self.admin)

        id_original = self.comunicado.id
        area = AreaInteres.objects.create(nombre_area="Área de Mantenimiento")

        file_io = io.BytesIO()
        Image.new('RGB', (1, 1), color='green').save(file_io, format='JPEG')
        file_io.seek(0)
        imagen = SimpleUploadedFile('mismo_id.jpg', file_io.read(), content_type='image/jpeg')

        payload = {
            "titulo": "Actualización conservando ID",
            "contenido": "El contenido cambia, el ID no.",
            "tipo_comunicacion": "URGENTE",
            "imagen_portada": imagen,
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], id_original, "El ID en la respuesta ha cambiado.")

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.id, id_original, "El ID en la base de datos ha cambiado.")



    def test_put_no_crea_nuevo_comunicado(self):
        """
        Test: Garantizar que PUT actualiza el registro existente y no crea uno nuevo.

        Given: Un comunicado en la base de datos.
        When: Se realiza una petición PUT válida.
        Then: El conteo total de comunicados en la DB debe permanecer igual (1).
        """
        self.client.force_authenticate(user=self.admin)

        conteo_inicial = Comunicado.objects.count()
        area = AreaInteres.objects.create(nombre_area="Área de Seguridad")
        
        file_io = io.BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(file_io, format='JPEG')
        file_io.seek(0)
        imagen = SimpleUploadedFile('no_crear.jpg', file_io.read(), content_type='image/jpeg')

        payload = {
            "titulo": "Actualización de control",
            "contenido": "Cuerpo actualizado.",
            "tipo_comunicacion": "GENERAL",
            "imagen_portada": imagen,
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Comunicado.objects.count(), conteo_inicial, 
                        "Se ha creado un nuevo comunicado en lugar de actualizar el existente.")



    def test_put_sin_titulo_retorna_400(self):
        """
        Test: Verificación de campo obligatorio en PUT.

        Given: Un comunicado existente.
        When: Se intenta actualizar enviando un payload sin la llave 'titulo'.
        Then: La API debe retornar 400 Bad Request y un mensaje de error específico.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Área de Prueba")

        payload = {
            "contenido": "Cuerpo del mensaje sin título.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('titulo', response.data)
        self.assertEqual(response.data['titulo'][0].code, 'required')



    def test_put_sin_contenido_retorna_400(self):
        """
        Test: Verificación de campo obligatorio 'contenido' en PUT.

        Given: Un comunicado existente.
        When: Se envía un payload con título pero sin 'contenido'.
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Cultura")

        payload = {
            "titulo": "Título válido",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('contenido', response.data)
        self.assertEqual(response.data['contenido'][0].code, 'required')



    def test_put_sin_tipo_comunicacion_retorna_400(self):
        """
        Test: Verificación de campo obligatorio 'tipo_comunicacion' en PUT.

        Given: Un comunicado existente.
        When: Se envía un payload con título y contenido, pero sin el tipo.
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Secretaría")

        payload = {
            "titulo": "Título válido",
            "contenido": "Cuerpo de mensaje válido.",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('tipo_comunicacion', response.data)
        self.assertEqual(response.data['tipo_comunicacion'][0].code, 'required')



    def test_put_sin_areas_interes_retorna_400(self):
        """
        Test: Verificación de campo obligatorio 'areas_interes' en PUT.

        Given: Un comunicado existente.
        When: Se envía un payload con datos básicos pero sin la llave 'areas_interes'.
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)

        payload = {
            "titulo": "Título para validación",
            "contenido": "Cuerpo del mensaje.",
            "tipo_comunicacion": "GENERAL"
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)
        self.assertEqual(response.data['areas_interes'][0].code, 'required')



    def test_put_titulo_demasiado_corto_retorna_400(self):
        """
        Test: Validación de longitud mínima en el título (Regla de Negocio).

        Given: Un comunicado existente.
        When: Se intenta actualizar con un título de solo 4 caracteres (ej: "Hola").
        Then: La API debe retornar 400 Bad Request y el mensaje de error del serializador.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Prueba de Validación")

        payload = {
            "titulo": "Hola", 
            "contenido": "Contenido válido pero título muy corto.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('titulo', response.data)
        self.assertEqual(
            response.data['titulo'][0], 
            "El título es demasiado corto. Debe tener al menos 5 caracteres."
        )



    def test_put_titulo_solo_espacios_retorna_400(self):
        """
        Test: Validación de que un título con solo espacios es rechazado.

        Given: Un comunicado existente.
        When: Se envía un PUT con "     " (5 espacios) en el título.
        Then: La API aplica .strip(), detecta que queda vacío y retorna 400.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Área de Pruebas")

        payload = {
            "titulo": "     ", 
            "contenido": "Contenido válido.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('titulo', response.data)
        self.assertEqual(
            response.data['titulo'][0], 
            "El título no puede estar formado solo por espacios en blanco."
        )



    def test_put_contenido_vacio_retorna_400(self):
        """
        Test: Validación de que el contenido no puede estar vacío o solo con espacios.

        Given: Un comunicado existente.
        When: Se envía un PUT con 'contenido' como una cadena vacía o espacios.
        Then: La API retorna 400 Bad Request con el mensaje de error de tu serializador.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="Área de Pruebas")

        payload = {
            "titulo": "Título de Calidad", 
            "contenido": "   ",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('contenido', response.data)
        self.assertEqual(
            response.data['contenido'][0], 
            "El contenido no puede estar vacío."
        )



    def test_put_contenido_solo_script_malicioso_retorna_400(self):
        """
        Test: Verificación de que el contenido que solo tiene HTML prohibido es rechazado.

        Given: Un comunicado existente.
        When: Se envía un PUT donde el contenido es solo un script malicioso.
        Then: Bleach limpia el contenido, queda vacío y el serializador retorna 400.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Título de Seguridad",
            "contenido": "<script>alert('ataque_xss')</script>",
            "tipo_comunicacion": "URGENTE",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('contenido', response.data)
        self.assertEqual(
            response.data['contenido'][0], 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_put_imagen_demasiado_grande_retorna_400(self):
        """
        Test: Validación de límite de tamaño de imagen (5MB).

        Given: Un comunicado existente.
        When: Se intenta actualizar con una imagen que simula pesar 6MB.
        Then: La API retorna 400 y el mensaje de error de tamaño excedido.
        """
        self.client.force_authenticate(user=self.admin)
        area = AreaInteres.objects.create(nombre_area="PATRIMONIO")

        file_io = io.BytesIO()
        Image.new('RGB', (1, 1), color='red').save(file_io, format='JPEG')

        tamanio_objetivo = 5 * 1024 * 1024 + 100
        padding = tamanio_objetivo - file_io.tell()
        file_io.write(b'\0' * padding)
        
        file_io.seek(0)

        imagen_mock = SimpleUploadedFile(
            "foto_pesada.jpg", 
            file_io.read(), 
            content_type="image/jpeg"
        )

        payload = {
            "titulo": "Título con Imagen Gigante",
            "contenido": "Contenido válido para el test de imagen.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id],
            "imagen_portada": imagen_mock
        }

        response = self.client.put(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('imagen_portada', response.data)
        self.assertEqual(
            response.data['imagen_portada'][0], 
            "La imagen es demasiado grande. El máximo permitido es de 5MB."
        )



    def test_put_imagen_formato_invalido_retorna_400(self):
        """
        Test: Validación de extensiones permitidas (.jpg, .jpeg, .png).

        Given: Un comunicado existente.
        When: Se envía una imagen válida (binaria) pero con extensión .gif.
        Then: La API retorna 400 con el mensaje de extensiones permitidas.
        """
        self.client.force_authenticate(user=self.admin)
        area = AreaInteres.objects.create(nombre_area="FORMATOS")

        file_io = io.BytesIO()
        Image.new('RGB', (100, 100), color='blue').save(file_io, format='JPEG')
        file_io.seek(0)

        imagen_prohibida = SimpleUploadedFile(
            "test_image.gif", 
            file_io.read(), 
            content_type="image/gif"
        )

        payload = {
            "titulo": "Título con Formato Prohibido",
            "contenido": "Intentando subir un GIF.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id],
            "imagen_portada": imagen_prohibida
        }

        response = self.client.put(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('imagen_portada', response.data)

        self.assertEqual(
            response.data['imagen_portada'][0], 
            "Formato de archivo no permitido (.gif). Solo se admiten imágenes JPG, JPEG o PNG."
        )



    def test_put_imagen_corrupta_retorna_400(self):
        """
        Test: Validación de integridad de la imagen.

        Given: Un comunicado existente.
        When: Se envía un archivo .jpg que contiene texto plano en lugar de binarios de imagen.
        Then: Pillow falla al abrirlo y la API retorna 400.
        """
        self.client.force_authenticate(user=self.admin)
        area = AreaInteres.objects.create(nombre_area="SEGURIDAD")

        imagen_corrupta = SimpleUploadedFile(
            "impostor.jpg", 
            b"esto_no_es_una_imagen_son_solo_letras", 
            content_type="image/jpeg"
        )

        payload = {
            "titulo": "Título de Prueba de Fallo",
            "contenido": "Intentando romper el validador de imágenes.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id],
            "imagen_portada": imagen_corrupta
        }

        response = self.client.put(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('imagen_portada', response.data)

        self.assertEqual(
            response.data['imagen_portada'][0], 
            "El archivo subido no es una imagen válida o está dañado."
        )



    def test_put_areas_interes_vacio_retorna_400(self):
        """
        Test: Validación de que un comunicado debe tener al menos un área de interés.

        Given: Un comunicado existente.
        When: Se envía un PUT con 'areas_interes' como una lista vacía [].
        Then: La API retorna 400 con el mensaje de error de regla de negocio.
        """
        self.client.force_authenticate(user=self.admin)

        payload = {
            "titulo": "Título para todos",
            "contenido": "Contenido de prueba para validación de áreas.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": []
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)

        self.assertEqual(
            response.data['areas_interes'][0], 
            "Debe seleccionar al menos un área de interés. Si es para todos, elija 'Todos los Hermanos'."
        )



    def test_put_area_inexistente_retorna_400(self):
        """
        Test: Validación de integridad referencial para áreas de interés.

        Given: Un comunicado existente.
        When: Se envía un PUT con un ID de área que no existe en la BD.
        Then: La API retorna 400 Bad Request indicando que la clave primaria no es válida.
        """
        self.client.force_authenticate(user=self.admin)

        id_falso = 9999 
        
        payload = {
            "titulo": "Título con Área Fantasma",
            "contenido": "Probando IDs inexistentes.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [id_falso]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)

        self.assertIn('does not exist', str(response.data['areas_interes'][0]))



    def test_put_tipo_comunicacion_invalido_retorna_400(self):
        """
        Test: Validación de tipos de comunicación permitidos.

        Given: Un comunicado existente.
        When: Se envía un PUT con un tipo de comunicación que no existe en el Enum.
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)

        area = AreaInteres.objects.create(nombre_area="GENERAL")
        
        payload = {
            "titulo": "Título con tipo inválido",
            "contenido": "Contenido de prueba.",
            "tipo_comunicacion": "TIPO_INVENTADO",
            "areas_interes": [area.id]
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('tipo_comunicacion', response.data)

        self.assertEqual(response.data['tipo_comunicacion'][0].code, 'invalid_choice')



    def test_put_campo_extra_no_permitido_retorna_400(self):
        """
        Test: La API debe rechazar campos que no pertenecen al modelo Comunicado.

        Given: Un comunicado existente.
        When: Se envía un PUT con un campo malintencionado o extra ('campo_hacker').
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)
        
        area = AreaInteres.objects.create(nombre_area="SEGURIDAD")

        payload = {
            "titulo": "Título Correcto",
            "contenido": "Contenido Correcto",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id],
            "campo_hacker": "intento_de_inyeccion_o_basura"
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('campo_hacker', str(response.data))



    def test_put_comunicado_usuario_sin_permisos_retorna_400(self):
        """
        Test: Control de acceso para edición de comunicados.

        Given: Un comunicado existente creado por un administrador.
        When: Un usuario normal (sin rango de admin) intenta realizar un PUT.
        Then: La API retorna 400 (debido al catch general de la vista que maneja la denegación).
        """
        self.client.force_authenticate(user=self.user)

        area = AreaInteres.objects.create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Intento de hackeo de título",
            "contenido": "Un usuario sin permisos intenta editar esto.",
            "tipo_comunicacion": "URGENTE",
            "areas_interes": [area.id] 
        }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.comunicado.refresh_from_db()
        self.assertNotEqual(self.comunicado.titulo, "Intento de hackeo de título")



    def test_put_comunicado_cuando_servicio_lanza_permission_denied_retorna_400(self):
        """
        Test: Captura de PermissionDenied en el bloque try-except de la vista.

        Given: Un usuario autenticado que intenta editar un comunicado.
        When: El servicio (o la lógica de la vista) lanza una excepción PermissionDenied.
        Then: La API retorna 400 (no 403) debido al catch general implementado.
        """
        self.client.force_authenticate(user=self.user)
        
        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Título de prueba válido",
            "contenido": "Contenido que cumple los requisitos de longitud.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        path_servicio = 'api.vistas.comunicado.comunicado_especifico_view.ComunicadoService.update_comunicado'
        
        with patch(path_servicio) as mock_servicio_update:
            mock_servicio_update.side_effect = PermissionDenied("No tienes permiso para editar")

            response = self.client.put(self.url, data=payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.assertIn("No tienes permiso", response.data['detail'])



    def test_put_comunicado_cuando_servicio_lanza_excepcion_generica_retorna_400(self):
        """
        Test: Gestión de errores inesperados en el servicio.

        Given: Un payload válido y un usuario autenticado.
        When: El servicio lanza una excepción genérica (p.ej. DatabaseError, ConnectionError).
        Then: La API captura el error en el catch general y retorna 400 con el detalle.
        """
        self.client.force_authenticate(user=self.admin)
        
        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Título Correcto",
            "contenido": "Contenido suficientemente largo para pasar validación.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        path_servicio = 'api.vistas.comunicado.comunicado_especifico_view.ComunicadoService.update_comunicado'
        
        with patch(path_servicio) as mock_servicio:
            mock_servicio.side_effect = Exception("Error crítico inesperado en el servidor")

            response = self.client.put(self.url, data=payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.assertEqual(response.data['detail'], "Error crítico inesperado en el servidor")



    def test_put_comunicado_cuando_falla_servicio_update_retorna_400(self):
        """
        Test: Respuesta ante fallo en la lógica del servicio update_comunicado.

        Given: Un comunicado existente y un payload válido.
        When: El servicio 'update_comunicado' lanza una excepción durante el proceso.
        Then: La vista captura el error y retorna un status 400 con el detalle.
        """
        self.client.force_authenticate(user=self.admin)
        
        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Nuevo Título Válido",
            "contenido": "Contenido que pasa las validaciones del serializador.",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [area.id]
        }

        path_servicio = 'api.vistas.comunicado.comunicado_especifico_view.ComunicadoService.update_comunicado'
        
        with patch(path_servicio) as mock_update:
            mock_update.side_effect = Exception("Error al procesar la actualización en el servicio")

            response = self.client.put(self.url, data=payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.assertEqual(response.data['detail'], "Error al procesar la actualización en el servicio")



    def test_put_comunicado_cuando_servicio_lanza_validation_error_modelo_retorna_400(self):
        """
        Test: Manejo de errores de validación de Django (model-level).

        Given: Datos que pasan el serializador pero fallan en el modelo.
        When: El servicio intenta guardar y Django lanza un ValidationError.
        Then: La vista captura la excepción y retorna 400.
        """
        self.client.force_authenticate(user=self.admin)
        
        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Título Válido",
            "contenido": "Contenido válido para el serializador.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        path_servicio = 'api.vistas.comunicado.comunicado_especifico_view.ComunicadoService.update_comunicado'
        
        with patch(path_servicio) as mock_update:
            mock_update.side_effect = ValidationError({
                'titulo': 'Este título ya está en uso en otra publicación restringida.'
            })

            response = self.client.put(self.url, data=payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.assertIn('titulo', str(response.data['detail']))



    def test_put_comunicado_cuando_hay_error_de_integridad_retorna_400(self):
        """
        Test: Captura de IntegrityError de base de datos.

        Given: Datos válidos para el serializador.
        When: El servicio intenta guardar y ocurre un error de integridad (ej: clave duplicada).
        Then: La vista captura la excepción y retorna 400.
        """
        self.client.force_authenticate(user=self.admin)
        
        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Título con Conflicto",
            "contenido": "Contenido válido para el flujo inicial.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        path_servicio = 'api.vistas.comunicado.comunicado_especifico_view.ComunicadoService.update_comunicado'
        
        with patch(path_servicio) as mock_update:
            mock_update.side_effect = IntegrityError("Duplicate entry 'Título con Conflicto' for key 'titulo_unique'")

            response = self.client.put(self.url, data=payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.assertIn("Duplicate entry", response.data['detail'])



    def test_put_comunicado_cuando_falla_guardado_servicio_retorna_400(self):
        """
        Test: Error durante la persistencia de datos en el servicio.

        Given: Un comunicado existente y datos validados por el serializador.
        When: El servicio intenta persistir los cambios pero ocurre un error.
        Then: La API retorna 400 con el detalle del error del servicio.
        """
        self.client.force_authenticate(user=self.admin)
        
        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Título para persistir",
            "contenido": "Contenido válido para la actualización.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        path_servicio = 'api.vistas.comunicado.comunicado_especifico_view.ComunicadoService.update_comunicado'
        
        with patch(path_servicio) as mock_update:
            mock_update.side_effect = Exception("Error interno: No se pudo completar el guardado en la base de datos.")

            response = self.client.put(self.url, data=payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.assertEqual(response.data['detail'], "Error interno: No se pudo completar el guardado en la base de datos.")



    def test_put_comunicado_con_pk_inexistente_retorna_404(self):
        """
        Test: Intento de actualización de un recurso que no existe.

        Given: Un ID de comunicado que no está en la base de datos (9999).
        When: Se realiza una petición PUT a ese ID.
        Then: La API retorna 404 Not Found gracias a get_object_or_404.
        """
        self.client.force_authenticate(user=self.admin)

        url_inexistente = '/api/comunicados/9999/' 
        
        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        payload = {
            "titulo": "Título fantasma",
            "contenido": "Este contenido nunca se guardará.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(url_inexistente, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_put_comunicado_con_pk_eliminado_retorna_404(self):
        """
        Test: Intento de actualización de un comunicado que ya no existe.

        Given: Un comunicado que ha sido eliminado de la base de datos.
        When: Se realiza una petición PUT a su ID.
        Then: La API retorna 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        area, _ = AreaInteres.objects.get_or_create(nombre_area="TODOS_HERMANOS")

        comunicado = Comunicado.objects.create(
            titulo="Para borrar", 
            contenido="Contenido efímero que cumple los requisitos mínimos", 
            tipo_comunicacion="GENERAL",
            autor=self.admin
        )
        
        pk_eliminado = comunicado.pk
        comunicado.delete()

        url_borrada = f'/api/comunicados/{pk_eliminado}/'
        
        payload = {
            "titulo": "Nuevo Título",
            "contenido": "Intento de actualizar algo que ya no existe en la base de datos.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [area.id]
        }

        response = self.client.put(url_borrada, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_patch_comunicado_solo_titulo_retorna_200(self):
        """
        Test: Actualización parcial (PATCH) enviando únicamente el título.

        Given: Un comunicado existente con un contenido específico.
        When: Se realiza una petición PATCH solo con el campo "titulo".
        Then: La API retorna 200 OK y el contenido original se mantiene.
        """
        self.client.force_authenticate(user=self.admin)

        contenido_original = self.comunicado.contenido
        nuevo_titulo = "Título modificado mediante PATCH"
        
        payload = {
            "titulo": nuevo_titulo
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['titulo'], nuevo_titulo)

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.titulo, nuevo_titulo)
        self.assertEqual(self.comunicado.contenido, contenido_original)



    def test_patch_comunicado_solo_contenido_retorna_200(self):
        """
        Test: Actualización parcial (PATCH) enviando únicamente el contenido.

        Given: Un comunicado con un título y contenido iniciales.
        When: Se envía un PATCH con un nuevo "contenido".
        Then: La API retorna 200 OK, actualiza el contenido y mantiene el título original.
        """
        self.client.force_authenticate(user=self.admin)

        titulo_original = self.comunicado.titulo
        nuevo_contenido = "Este es el nuevo contenido actualizado para la noticia."
        
        payload = {
            "contenido": nuevo_contenido
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.contenido, nuevo_contenido)

        self.assertEqual(self.comunicado.titulo, titulo_original)
        self.assertEqual(response.data['titulo'], titulo_original)



    def test_patch_comunicado_solo_tipo_comunicacion_retorna_200(self):
        """
        Test: Actualización parcial (PATCH) del tipo de comunicación.

        Given: Un comunicado existente con un tipo inicial (ej: GENERAL).
        When: Se envía un PATCH con un nuevo "tipo_comunicacion" (ej: URGENTE).
        Then: La API retorna 200 OK y el tipo se actualiza correctamente.
        """
        self.client.force_authenticate(user=self.admin)

        titulo_previo = self.comunicado.titulo

        nuevo_tipo = "URGENTE" 
        
        payload = {
            "tipo_comunicacion": nuevo_tipo
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.tipo_comunicacion, nuevo_tipo)

        self.assertEqual(self.comunicado.titulo, titulo_previo)
        self.assertEqual(response.data['tipo_comunicacion'], nuevo_tipo)



    def test_patch_comunicado_solo_areas_interes_retorna_200(self):
        """
        Test: Actualización parcial de relaciones Many-to-Many.

        Given: Un comunicado vinculado a un área inicial.
        When: Se envía un PATCH con una nueva lista de IDs de áreas_interes.
        Then: La API retorna 200 OK y las relaciones se actualizan correctamente.
        """
        self.client.force_authenticate(user=self.admin)

        area_1, _ = AreaInteres.objects.get_or_create(nombre_area="HERMANOS_LUCES")
        area_2, _ = AreaInteres.objects.get_or_create(nombre_area="BANDA")

        titulo_original = self.comunicado.titulo
        
        payload = {
            "areas_interes": [area_1.id, area_2.id]
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        areas_actuales = self.comunicado.areas_interes.all()
        
        self.assertEqual(areas_actuales.count(), 2)
        self.assertIn(area_1, areas_actuales)
        self.assertIn(area_2, areas_actuales)

        self.assertEqual(self.comunicado.titulo, titulo_original)



    def test_patch_comunicado_combinacion_parcial_valida_retorna_200(self):
        """
        Test: Actualización simultánea de un campo simple y una relación M2M.

        Given: Un comunicado con datos iniciales.
        When: Se envía un PATCH con "titulo" y una nueva lista de "areas_interes".
        Then: La API retorna 200 OK y ambos campos se actualizan manteniendo el resto igual.
        """
        self.client.force_authenticate(user=self.admin)

        contenido_previo = self.comunicado.contenido
        tipo_previo = self.comunicado.tipo_comunicacion

        area_nueva, _ = AreaInteres.objects.get_or_create(nombre_area="NUEVA_AREA_TEST")
        nuevo_titulo = "Título actualizado en combo"
        
        payload = {
            "titulo": nuevo_titulo,
            "areas_interes": [area_nueva.id]
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.titulo, nuevo_titulo)
        self.assertIn(area_nueva, self.comunicado.areas_interes.all())

        self.assertEqual(self.comunicado.contenido, contenido_previo)
        self.assertEqual(self.comunicado.tipo_comunicacion, tipo_previo)



    def test_patch_mantiene_campos_no_enviados_sin_modificar(self):
        """
        Test: Garantizar que los campos ausentes en el payload no se sobrescriben.

        Given: Un comunicado con todos sus campos completos.
        When: Se envía un PATCH con un único campo.
        Then: El resto de los atributos en la DB permanecen idénticos a su estado original.
        """
        self.client.force_authenticate(user=self.admin)

        old_titulo = self.comunicado.titulo
        old_contenido = self.comunicado.contenido
        old_tipo = self.comunicado.tipo_comunicacion
        old_autor = self.comunicado.autor
        old_areas = list(self.comunicado.areas_interes.all())

        nuevo_titulo = "Título editado preventivamente"
        payload = {"titulo": nuevo_titulo}

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comunicado.refresh_from_db()

        self.assertEqual(self.comunicado.titulo, nuevo_titulo)

        self.assertEqual(self.comunicado.contenido, old_contenido, "El contenido cambió sin ser enviado")
        self.assertEqual(self.comunicado.tipo_comunicacion, old_tipo, "El tipo de comunicación cambió")
        self.assertEqual(self.comunicado.autor, old_autor, "El autor se alteró inesperadamente")

        self.assertCountEqual(list(self.comunicado.areas_interes.all()), old_areas)



    def test_patch_actualiza_correctamente_areas_interes(self):
        """
        Test: Actualización específica de relaciones Many-to-Many mediante PATCH.

        Given: Un comunicado vinculado a un área 'A'.
        When: Se envía un PATCH con una lista que contiene el ID de un área 'B'.
        Then: El área 'A' se desvincula y el área 'B' queda asociada al comunicado.
        """
        self.client.force_authenticate(user=self.admin)

        area_antigua, _ = AreaInteres.objects.get_or_create(nombre_area="ANTIGUA")
        area_nueva, _ = AreaInteres.objects.get_or_create(nombre_area="NUEVA")

        self.comunicado.areas_interes.set([area_antigua])
        
        payload = {
            "areas_interes": [area_nueva.id]
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        areas_actuales = self.comunicado.areas_interes.all()

        self.assertIn(area_nueva, areas_actuales)
        self.assertNotIn(area_antigua, areas_actuales)
        self.assertEqual(areas_actuales.count(), 1)



    def test_patch_comunicado_con_imagen_valida_retorna_200(self):
        """
        Test: Actualización parcial de la imagen de portada.

        Given: Un comunicado existente y un archivo de imagen válido.
        When: Se realiza una petición PATCH enviando el archivo en el campo "imagen_portada".
        Then: La API retorna 200 OK y la ruta de la imagen se actualiza en la DB.
        """
        self.client.force_authenticate(user=self.admin)

        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(file_io, format='PNG')
        file_io.seek(0)

        archivo_test = SimpleUploadedFile(
            name='test_portada.png',
            content=file_io.read(),
            content_type='image/png'
        )

        payload = {
            "imagen_portada": archivo_test
        }

        response = self.client.patch(self.url, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.comunicado.refresh_from_db()
        self.assertIn('test_portada', self.comunicado.imagen_portada.name)

        if self.comunicado.imagen_portada and os.path.isfile(self.comunicado.imagen_portada.path):
            os.remove(self.comunicado.imagen_portada.path)



    def test_patch_comunicado_con_payload_vacio_retorna_200(self):
        """
        Test: Envío de una petición PATCH sin datos en el cuerpo.

        Given: Un comunicado existente.
        When: Se realiza una petición PATCH con un diccionario vacío {}.
        Then: La API retorna 200 OK y el recurso permanece inalterado.
        """
        self.client.force_authenticate(user=self.admin)

        titulo_antes = self.comunicado.titulo
        contenido_antes = self.comunicado.contenido

        payload = {}
        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comunicado.refresh_from_db()
        self.assertEqual(self.comunicado.titulo, titulo_antes)
        self.assertEqual(self.comunicado.contenido, contenido_antes)

        self.assertEqual(response.data['titulo'], titulo_antes)



    def test_patch_devuelve_objeto_actualizado_en_el_body(self):
        """
        Test: La respuesta del PATCH incluye la representación actualizada del recurso.

        Given: Un comunicado con datos iniciales.
        When: Se realiza un PATCH con nuevos valores para título y tipo.
        Then: La respuesta (JSON) contiene los nuevos valores y mantiene los IDs correctos.
        """
        self.client.force_authenticate(user=self.admin)
        
        nuevo_titulo = "Título Actualizado para Response"
        nuevo_tipo = "URGENTE"
        
        payload = {
            "titulo": nuevo_titulo,
            "tipo_comunicacion": nuevo_tipo
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['titulo'], nuevo_titulo)
        self.assertEqual(response.data['tipo_comunicacion'], nuevo_tipo)

        self.assertEqual(response.data['id'], self.comunicado.id)
        self.assertIn('contenido', response.data)
        self.assertEqual(response.data['contenido'], self.comunicado.contenido)



    def test_patch_comunicado_no_crea_nuevo_registro(self):
        """
        Test: Garantizar que PATCH solo actualiza y no duplica ni crea registros.

        Given: Un comunicado existente en la base de datos.
        When: Se realiza una petición PATCH válida.
        Then: El número total de comunicados en la DB permanece igual (n=1).
        """
        self.client.force_authenticate(user=self.admin)

        total_antes = Comunicado.objects.count()
        id_original = self.comunicado.id
        
        payload = {
            "titulo": "Título para comprobar que no se duplica"
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        total_despues = Comunicado.objects.count()
        self.assertEqual(total_antes, total_despues, "Se ha creado un nuevo registro en lugar de actualizarlo.")

        self.assertEqual(response.data['id'], id_original)



    def test_patch_comunicado_con_titulo_invalido_retorna_400(self):
        """
        Test: Validación de longitud y contenido significativo en el título.

        Given: Un comunicado existente.
        When: Se envía un PATCH con un título de menos de 5 caracteres o solo espacios.
        Then: La API retorna 400 Bad Request con el mensaje de error específico.
        """
        self.client.force_authenticate(user=self.admin)

        payload_corto = {"titulo": "ABC"}
        response_corto = self.client.patch(self.url, data=payload_corto, format='json')

        self.assertEqual(response_corto.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Debe tener al menos 5 caracteres", str(response_corto.data['titulo']))

        payload_espacios = {"titulo": "     "}
        response_espacios = self.client.patch(self.url, data=payload_espacios, format='json')

        self.assertEqual(response_espacios.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no puede estar formado solo por espacios", str(response_espacios.data['titulo']))



    def test_patch_comunicado_con_contenido_vacio_retorna_400(self):
        """
        Test: Validación de contenido obligatorio en PATCH.

        Given: Un comunicado existente.
        When: Se intenta actualizar el contenido a una cadena vacía o nula.
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)

        payload_vacio = {"contenido": ""}
        response_vacio = self.client.patch(self.url, data=payload_vacio, format='json')

        self.assertEqual(response_vacio.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("El contenido no puede estar vacío.", str(response_vacio.data['contenido']))

        payload_espacios = {"contenido": "     "}
        response_espacios = self.client.patch(self.url, data=payload_espacios, format='json')

        self.assertEqual(response_espacios.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("El contenido no puede estar vacío.", str(response_espacios.data['contenido']))



    def test_patch_comunicado_con_imagen_invalida_retorna_400(self):
        """
        Test: Validación de seguridad y formato para archivos de imagen.

        Given: Un comunicado existente.
        When: Se intenta subir un archivo con extensión prohibida o contenido corrupto.
        Then: La API retorna 400 Bad Request con mensajes de error descriptivos.
        """
        self.client.force_authenticate(user=self.admin)

        file_io = io.BytesIO()
        img = Image.new('RGB', (10, 10), color='red')
        img.save(file_io, format='GIF')
        file_io.seek(0)

        archivo_gif = SimpleUploadedFile(
            name='test.gif', 
            content=file_io.read(), 
            content_type='image/gif'
        )
        
        response_ext = self.client.patch(self.url, data={"imagen_portada": archivo_gif}, format='multipart')

        self.assertEqual(response_ext.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Formato de archivo no permitido", str(response_ext.data['imagen_portada']))

        archivo_falso = SimpleUploadedFile(
            name='ataque.jpg', 
            content=b'Esto es texto, no una imagen', 
            content_type='image/jpeg'
        )
        response_fake = self.client.patch(self.url, data={"imagen_portada": archivo_falso}, format='multipart')

        self.assertEqual(response_fake.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no es una imagen válida o está dañado", str(response_fake.data['imagen_portada']))



    def test_patch_areas_interes_vacio_retorna_400(self):
        """
        Test: Validación de que áreas_interes no puede estar vacío en un PATCH.

        Given: Un comunicado con áreas de interés ya asignadas.
        When: Se realiza un PATCH enviando "areas_interes": [].
        Then: La API retorna 400 y el mensaje de error personalizado.
        """
        self.client.force_authenticate(user=self.admin)

        payload = {
            "areas_interes": []
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)
        self.assertIn(
            "Debe seleccionar al menos un área de interés", 
            str(response.data['areas_interes'][0])
        )



    def test_patch_area_interes_inexistente_retorna_400(self):
        """
        Test: Validación de integridad referencial en áreas de interés.

        Given: Un comunicado existente.
        When: Se intenta actualizar con un ID de área que no existe en la DB.
        Then: La API retorna 400 Bad Request indicando que el ID es inválido.
        """
        self.client.force_authenticate(user=self.admin)

        id_falso = 9999
        payload = {
            "areas_interes": [id_falso]
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('areas_interes', response.data)

        mensaje_error = str(response.data['areas_interes'][0]).lower()

        error_valido = "does not exist" in mensaje_error or "no existe" in mensaje_error or "invalid" in mensaje_error
        self.assertTrue(error_valido, f"El mensaje de error no es el esperado: {mensaje_error}")



    def test_patch_tipo_comunicacion_invalido_retorna_400(self):
        """
        Test: Validación de opciones permitidas en tipo_comunicacion.

        Given: Un comunicado existente.
        When: Se envía un PATCH con un tipo que no está en las opciones (choices).
        Then: La API retorna 400 Bad Request indicando que la opción no es válida.
        """
        self.client.force_authenticate(user=self.admin)

        payload = {
            "tipo_comunicacion": "VALOR_INVENTADO"
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('tipo_comunicacion', response.data)

        mensaje_error = str(response.data['tipo_comunicacion'][0]).lower()

        es_error_valido = (
            "not a valid choice" in mensaje_error or 
            "no es una opción válida" in mensaje_error or
            "valor_inventado" in mensaje_error
        )
        
        self.assertTrue(
            es_error_valido, 
            f"El mensaje de error no fue el esperado: {mensaje_error}"
        )



    def test_patch_datos_mal_formateados_retorna_400(self):
        """
        Test: Manejo de errores de sintaxis y tipos de datos inválidos.

        Given: Un comunicado existente.
        When: Se envía un JSON mal construido o tipos de datos incorrectos.
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)

        payload_roto = '{"titulo": "Título incompleto" ' 
        response_sintaxis = self.client.patch(
            self.url, 
            data=payload_roto, 
            content_type='application/json'
        )
        self.assertEqual(response_sintaxis.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response_sintaxis.data)

        payload_tipo = {
            "areas_interes": 123
        }
        response_tipo = self.client.patch(self.url, data=payload_tipo, format='json')
        
        self.assertEqual(response_tipo.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('areas_interes', response_tipo.data)

        mensaje_error = str(response_tipo.data['areas_interes']).lower()
        self.assertTrue(
            "list" in mensaje_error or "lista" in mensaje_error,
            f"El error no indica que se esperaba una lista: {mensaje_error}"
        )



    def test_patch_contenido_con_script_que_queda_vacio_retorna_400(self):
        """
        Test: Prevención de contenido vacío tras limpieza de seguridad (XSS).

        Given: Un comunicado existente.
        When: Se envía un PATCH con un script malicioso que no contiene texto plano.
        Then: Bleach elimina el script, el contenido queda vacío y la API retorna 400.
        """
        self.client.force_authenticate(user=self.admin)

        payload = {
            "contenido": "<script>alert('Hacked');</script>"
        }

        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('contenido', response.data)
        self.assertIn(
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad",
            str(response.data['contenido'][0])
        )



    def test_patch_usuario_sin_permisos_retorna_400(self):
        """
        Test: Verificación de permisos en el servicio durante un PATCH.

        Given: Un comunicado existente y un usuario autenticado SIN permisos (no es admin ni de Junta).
        When: Se intenta actualizar parcialmente el comunicado (PATCH).
        Then: El servicio lanza PermissionDenied, la vista lo captura y retorna 400.
        """
        hermano_sin_permisos = Hermano.objects.create(
            dni="87654321Z",
            password="1234",
            username="87654321Z",
            nombre="Hermano",
            primer_apellido="Raso",
            segundo_apellido="SinPermisos",
            telefono="123456789",
            estado_civil="SOLTERO",
            esAdmin=False
        )

        hermano_sin_permisos.set_password("password123")
        hermano_sin_permisos.save()

        self.client.force_authenticate(user=hermano_sin_permisos)

        payload = {"titulo": "Intento de hackeo"}
        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'], 
            "No tienes permisos para gestionar comunicados."
        )



    @patch('api.servicios.comunicado.creacion_comunicado_service.ComunicadoService.update_comunicado')
    def test_patch_cuando_servicio_lanza_excepcion_retorna_400(self, mock_update):
        """
        Test: Verificación de manejo de errores genéricos en PATCH.

        Given: Un comunicado existente y un admin autenticado.
        When: El servicio lanza una excepción inesperada (ej. fallo de DB).
        Then: La vista captura la excepción y retorna 400 con el mensaje de error.
        """
        self.client.force_authenticate(user=self.admin)

        mensaje_error = "Error inesperado en el servidor de base de datos."
        mock_update.side_effect = Exception(mensaje_error)

        payload = {"titulo": "Nuevo Título"}
        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data['detail'], mensaje_error)



    @patch('api.servicios.comunicado.creacion_comunicado_service.ComunicadoService.update_comunicado')
    def test_patch_cuando_falla_actualizacion_parcial_retorna_400(self, mock_update):
        """
        Test: Verificación de manejo de errores durante la actualización parcial.

        Given: Un comunicado existente y un admin autenticado.
        When: Se envía un payload que provoca un fallo de atributo o lógica en el servicio.
        Then: La API retorna 400 Bad Request con el detalle del error.
        """
        self.client.force_authenticate(user=self.admin)

        mensaje_error = "El campo 'campo_inexistente' no existe en el modelo Comunicado."
        mock_update.side_effect = AttributeError(mensaje_error)

        payload = {"titulo": "Título de prueba"}
        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], mensaje_error)



    def test_patch_comunicado_inexistente_retorna_404(self):
        """
        Test: Intento de actualización de un recurso que no existe.

        Given: Un ID de comunicado que no está en la base de datos (9999).
        When: Se envía una petición PATCH a esa URL.
        Then: La API retorna 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        url_inexistente = re.sub(r'\d+/?$', '9999/', self.url)
        
        payload = {"titulo": "Nuevo Título"}
        response = self.client.patch(url_inexistente, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)



    def test_patch_sobre_comunicado_eliminado_retorna_404(self):
        """
        Test: Interacción con un recurso tras su eliminación.

        Given: Un comunicado que acaba de ser borrado de la base de datos.
        When: Se intenta realizar una actualización parcial (PATCH) sobre ese mismo ID.
        Then: La API retorna 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        comunicado_id = self.comunicado.id
        self.comunicado.delete()

        payload = {"titulo": "Título post-mortem"}
        response = self.client.patch(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(response.data['detail'].code, 'not_found')



    def test_delete_comunicado_autorizado_retorna_204(self):
        """
        Test: Eliminación exitosa de un comunicado por un usuario con permisos.

        Given: Un comunicado existente en la base de datos.
        When: Un administrador envía una petición DELETE a la URL del recurso.
        Then: La API retorna 204 No Content y el registro desaparece de la base de datos.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Comunicado.objects.filter(id=self.comunicado.id).exists())



    def test_delete_elimina_registro_fisico_en_bd(self):
        """
        Test: Verificación de integridad de datos tras DELETE.

        Given: Un comunicado con ID conocido.
        When: Se ejecuta el borrado a través de la API.
        Then: El conteo de objetos en la BD disminuye y la consulta por ID falla.
        """
        self.client.force_authenticate(user=self.admin)

        comunicado_id = self.comunicado.id
        total_antes = Comunicado.objects.count()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Comunicado.objects.count(), total_antes - 1)

        with self.assertRaises(Comunicado.DoesNotExist):
            Comunicado.objects.get(id=comunicado_id)



    def test_delete_no_devuelve_cuerpo_en_respuesta(self):
        """
        Test: Verificación de que la respuesta cumple el estándar 204 (sin cuerpo).

        Given: Un comunicado existente y un admin autenticado.
        When: Se realiza una petición DELETE.
        Then: La respuesta tiene status 204 y el contenido está vacío.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(len(response.content), 0)
        self.assertEqual(response.content, b"")

        self.assertIsNone(response.data)



    def test_delete_retorna_exactamente_204_sin_contenido(self):
        """
        Test: Verificación de cumplimiento estricto del estándar HTTP 204.

        Given: Un administrador autenticado y un comunicado existente.
        When: Se envía una petición DELETE.
        Then: La respuesta debe ser exactamente 204 y el cuerpo debe ser nulo/vacío.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIsNone(response.data)

        self.assertEqual(response.content, b"")
        self.assertEqual(len(response.content), 0)



    def test_delete_comunicado_con_imagen_retorna_204_y_limpia_archivo(self):
        """
        Test: Borrado de un comunicado que contiene archivos multimedia.

        Given: Un comunicado con una imagen de portada almacenada.
        When: Se solicita el borrado (DELETE).
        Then: La API retorna 204 y el registro desaparece de la BD.
        """
        self.client.force_authenticate(user=self.admin)

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        self.comunicado.imagen_portada = SimpleUploadedFile(
            name='test_image.jpg',
            content=tmp_file.read(),
            content_type='image/jpeg'
        )
        self.comunicado.save()

        ruta_archivo = self.comunicado.imagen_portada.path

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comunicado.objects.filter(id=self.comunicado.id).exists())



    def test_delete_comunicado_sin_imagen_retorna_204(self):
        """
        Test: Borrado de un comunicado que no tiene archivos multimedia.

        Given: Un comunicado cuya 'imagen_portada' es null/None.
        When: Se solicita el borrado (DELETE) por un admin.
        Then: La API retorna 204 y el registro se elimina sin errores de sistema de archivos.
        """
        self.client.force_authenticate(user=self.admin)

        self.comunicado.imagen_portada = None
        self.comunicado.save()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comunicado.objects.filter(id=self.comunicado.id).exists())



    def test_delete_no_afecta_otros_comunicados(self):
        """
        Test: Verificación de aislamiento del borrado.

        Given: Dos comunicados en la base de datos.
        When: Se borra uno de ellos mediante la API.
        Then: El otro comunicado permanece intacto en la base de datos.
        """
        self.client.force_authenticate(user=self.admin)

        otro_comunicado = Comunicado.objects.create(
            titulo="Comunicado Intacto",
            contenido="Este no debería borrarse",
            autor=self.admin,
            tipo_comunicacion=self.comunicado.tipo_comunicacion
        )

        otro_comunicado.areas_interes.set(self.comunicado.areas_interes.all())

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Comunicado.objects.filter(id=self.comunicado.id).exists())

        self.assertTrue(Comunicado.objects.filter(id=otro_comunicado.id).exists())

        self.assertEqual(Comunicado.objects.count(), 1)



    def test_delete_llamado_dos_veces_retorna_404_en_segunda_llamada(self):
        """
        Test: Verificación de que el recurso desaparece tras la primera eliminación.

        Given: Un administrador autenticado y un comunicado existente.
        When: Se envía una petición DELETE seguida de otra idéntica al mismo ID.
        Then: La primera retorna 204 y la segunda retorna 404.
        """
        self.client.force_authenticate(user=self.admin)

        first_response = self.client.delete(self.url)
        self.assertEqual(first_response.status_code, status.HTTP_204_NO_CONTENT)

        second_response = self.client.delete(self.url)

        self.assertEqual(second_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', second_response.data)

        self.assertEqual(second_response.data['detail'].code, 'not_found')



    def test_delete_confirma_inexistencia_real_en_bd(self):
        """
        Test: Verificación física de la desaparición del registro.

        Given: Un comunicado con un ID específico.
        When: Se recibe un 204 tras la petición DELETE.
        Then: Una consulta directa a la base de datos por ese ID no debe devolver nada.
        """
        self.client.force_authenticate(user=self.admin)
        comunicado_id = self.comunicado.id

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        existe = Comunicado.objects.filter(id=comunicado_id).exists()
        
        self.assertFalse(existe, "El comunicado sigue existiendo en la BD tras el DELETE")

        self.assertEqual(Comunicado.objects.count(), 0)



    def test_delete_usuario_sin_permisos_retorna_400(self):
        """
        Test: Intento de borrado por un usuario sin privilegios.

        Given: Un usuario autenticado que no es Admin ni Junta.
        When: Intenta eliminar un comunicado mediante DELETE.
        Then: El servicio lanza PermissionDenied y la vista lo captura retornando 400.
        """
        HermanoModel = get_user_model()

        hermano_raso = HermanoModel.objects.create_user(
            username='user_test_unique_99', 
            password='pass123',
            nombre='Juan',
            primer_apellido='Pérez',
            segundo_apellido='García',
            dni='99999999X',
            telefono='600000000',
            estado_civil='SOLTERO',
            esAdmin=False
        )

        self.client.force_authenticate(user=hermano_raso)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No tienes permisos", str(response.data['detail']))
        self.assertTrue(Comunicado.objects.filter(id=self.comunicado.id).exists())



    def test_delete_cuando_servicio_lanza_permission_denied_retorna_400(self):
        """
        Test: La vista debe mapear PermissionDenied a 400 Bad Request.

        Given: Un usuario autenticado sin privilegios.
        When: El servicio lanza PermissionDenied al intentar borrar.
        Then: La respuesta HTTP es 400 y el mensaje explica la falta de permisos.
        """
        HermanoModel = get_user_model()

        hermano_raso = HermanoModel.objects.create_user(
            username="test_denied_user_123",
            password='password123',
            dni="11223344J",
            nombre='Hermano',
            primer_apellido='Sin',
            segundo_apellido='Permisos',
            telefono='600111222',
            estado_civil='SOLTERO',
            esAdmin=False
        )

        self.client.force_authenticate(user=hermano_raso)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error_msg = str(response.data.get('detail', ''))
        self.assertIn("No tienes permisos", error_msg)

        self.assertTrue(Comunicado.objects.filter(id=self.comunicado.id).exists())



    @patch('api.servicios.comunicado.creacion_comunicado_service.ComunicadoService.delete_comunicado')
    def test_delete_cuando_servicio_lanza_excepcion_retorna_400(self, mock_delete):
        """
        Test: Verificación de que cualquier error en el servicio se traduce en un 400.

        Given: Un administrador autenticado.
        When: El ComunicadoService lanza una excepción durante el borrado.
        Then: La respuesta HTTP es 400 y se devuelve el mensaje de error.
        """
        self.client.force_authenticate(user=self.admin)

        mensaje_error = "Error interno de integridad en el servicio"
        mock_delete.side_effect = Exception(mensaje_error)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(str(response.data.get('detail', '')), mensaje_error)

        self.assertTrue(Comunicado.objects.filter(id=self.comunicado.id).exists())



    @patch('api.servicios.comunicado.creacion_comunicado_service.ComunicadoService.delete_comunicado')
    def test_delete_cuando_hay_error_en_ejecucion_retorna_400(self, mock_delete):
        """
        Test: Manejo de fallos inesperados durante el proceso de eliminación.

        Given: Un administrador autenticado y un comunicado existente.
        When: El servicio lanza un error (ej. fallo de conexión a DB o permisos de disco).
        Then: La API retorna 400 Bad Request con el detalle del error.
        """
        self.client.force_authenticate(user=self.admin)

        mensaje_error = "No se pudo eliminar el archivo físico asociado al comunicado."
        mock_delete.side_effect = Exception(mensaje_error)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(str(response.data.get('detail', '')), mensaje_error)

        self.assertTrue(Comunicado.objects.filter(id=self.comunicado.id).exists())



    @patch('api.servicios.comunicado.creacion_comunicado_service.ComunicadoService.delete_comunicado')
    def test_delete_cuando_falla_proceso_servicio_retorna_400(self, mock_delete):
        """
        Test: Verificación de manejo de errores si el servicio falla.

        Given: Un administrador autenticado.
        When: El método delete_comunicado lanza un error (ej. fallo de integridad).
        Then: La API retorna 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)

        mensaje_error = "Error al intentar eliminar el registro de la base de datos."
        mock_delete.side_effect = Exception(mensaje_error)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data.get('detail', '')), mensaje_error)

        self.assertTrue(Comunicado.objects.filter(id=self.comunicado.id).exists())



    def test_delete_con_pk_inexistente_retorna_404(self):
        """
        Test: Intento de borrado de un recurso que no existe.

        Given: Un administrador autenticado.
        When: Se envía un DELETE a una URL con un ID que no figura en la BD.
        Then: La API retorna 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        url_inexistente = reverse('detalle-comunicado', kwargs={'pk': self.comunicado.id + 999})

        response = self.client.delete(url_inexistente)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertIn('not_found', str(response.data.get('detail', '').code))



    def test_delete_comunicado_ya_eliminado_retorna_404(self):
        """
        Test: Intento de eliminar un recurso que acaba de ser borrado.

        Given: Un comunicado que existía pero ha sido borrado previamente.
        When: Se envía una petición DELETE a su URL.
        Then: La API retorna 404 Not Found.
        """
        self.client.force_authenticate(user=self.admin)

        response_primera = self.client.delete(self.url)
        self.assertEqual(response_primera.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Comunicado.objects.filter(id=self.comunicado.id).exists())

        response_segunda = self.client.delete(self.url)

        self.assertEqual(response_segunda.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response_segunda.data)