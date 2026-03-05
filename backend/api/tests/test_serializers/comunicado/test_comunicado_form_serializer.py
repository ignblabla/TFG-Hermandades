import io
import os
import re
import time
from PIL import Image
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock, patch

from api.models import AreaInteres, Comunicado
from api.serializadores.comunicado.comunicado_form_serializer import ComunicadoFormSerializer

class ComunicadoFormSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Configuración inicial de la base de datos para todas las pruebas de esta clase.
        Creamos las áreas de interés necesarias para satisfacer las relaciones del serializador.
        """
        cls.area_todos = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS
        )
        cls.area_juventud = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.JUVENTUD
        )

    def setUp(self):
        """
        Payload base válido que se reinicia antes de cada test.
        """
        self.valid_payload = {
            'titulo': 'Título de prueba válido',
            'contenido': '<p>Este es un comunicado <strong>importante</strong>.</p>',
            'tipo_comunicacion': Comunicado.TipoComunicacion.GENERAL,
            'areas_interes': [self.area_todos.id]
        }

    def generar_imagen_valida(self, width=100, height=100, format='JPEG', extension='.jpg', size_mb=0):
        """Genera una imagen válida en memoria."""
        file_obj = io.BytesIO()
        image = Image.new('RGB', size=(width, height), color=(255, 0, 0))
        image.save(file_obj, format)

        if size_mb > 0:
            file_obj.write(b'\0' * (size_mb * 1024 * 1024))
            
        file_obj.seek(0)
        return SimpleUploadedFile(f'test_image{extension}', file_obj.read(), content_type=f'image/{format.lower()}')

    def generar_archivo_falso(self):
        """Genera un archivo de texto con extensión de imagen (para testear archivos corruptos/maliciosos)."""
        return SimpleUploadedFile(
            'fake_image.jpg', 
            b'Esto es un texto, no una imagen binaria', 
            content_type='image/jpeg'
        )



    def test_payload_completo_con_todos_los_campos_validos(self):
        """
        Test: Validación exitosa de un payload completo y válido.

        Given: Un conjunto de datos completo (payload) para crear un comunicado, 
            que incluye título, contenido, tipo de comunicación, IDs de áreas 
            de interés y un archivo de imagen de portada correcto generado en memoria.
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador aprueba la validación (True), no contiene errores 
            y los datos validados (validated_data) están correctamente transformados 
            para ser guardados en la base de datos.
        """
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = self.generar_imagen_valida()

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador debería ser válido, pero retornó los siguientes errores: {serializer.errors}"
        )

        self.assertEqual(len(serializer.errors), 0)

        datos_validados = serializer.validated_data
        self.assertEqual(datos_validados['titulo'], payload['titulo'])
        self.assertEqual(datos_validados['tipo_comunicacion'], payload['tipo_comunicacion'])

        self.assertIn(self.area_todos, datos_validados['areas_interes'])

        self.assertIsNotNone(datos_validados.get('imagen_portada'))



    def test_payload_sin_imagen_portada_campo_opcional(self):
        """
        Test: Validación exitosa de un comunicado sin imagen de portada.

        Given: Un payload válido que contiene todos los campos obligatorios 
            (título, contenido, tipo, áreas) pero omite el campo 'imagen_portada'.
        When: Se inicializa el ComunicadoFormSerializer con este diccionario y 
            se ejecuta la validación is_valid().
        Then: El serializador es marcado como válido (True) debido a que la 
            imagen está definida como opcional (required=False) en la lógica 
            del serializador.
        """
        payload = self.valid_payload.copy()

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador debería aceptar la ausencia de imagen, errores: {serializer.errors}"
        )

        self.assertNotIn('imagen_portada', serializer.errors)

        self.assertIsNone(serializer.validated_data.get('imagen_portada'))



    def test_payload_con_imagen_portada_nula(self):
        """
        Test: Validación exitosa enviando explícitamente null en la imagen.

        Given: Un payload válido donde el campo 'imagen_portada' se envía 
            con valor None (equivalente a null en JSON).
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador retorna True, ya que el campo permite nulos 
            (allow_null=True) y el método validate_imagen_portada gestiona 
            correctamente la ausencia de archivo sin intentar procesarlo con PIL.
        """
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = None

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador debería permitir null en imagen_portada, errores: {serializer.errors}"
        )

        self.assertIn('imagen_portada', serializer.validated_data)
        self.assertIsNone(serializer.validated_data['imagen_portada'])

        self.assertNotIn('imagen_portada', serializer.errors)



    def test_payload_con_multiples_areas_interes_validas(self):
        """
        Test: Validación de comunicado dirigido a múltiples áreas de interés.

        Given: Un payload válido que incluye una lista con múltiples IDs 
            de áreas de interés (ej: TODOS_HERMANOS y JUVENTUD).
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y el campo 'areas_interes' en 
            los datos validados contiene la lista de instancias de modelo 
            correspondientes a esos IDs.
        """
        payload = self.valid_payload.copy()
        payload['areas_interes'] = [self.area_todos.id, self.area_juventud.id]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador debería permitir múltiples áreas, errores: {serializer.errors}"
        )

        areas_validadas = serializer.validated_data['areas_interes']
        self.assertEqual(len(areas_validadas), 2)

        self.assertIn(self.area_todos, areas_validadas)
        self.assertIn(self.area_juventud, areas_validadas)



    def test_payload_con_un_unico_area_interes_valido(self):
        """
        Test: Validación de comunicado dirigido a una única área de interés.

        Given: Un payload válido que contiene una lista con un único ID de 
            área de interés existente en la base de datos.
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y los datos validados contienen 
            exactamente una instancia de AreaInteres coincidente con el ID enviado.
        """
        payload = self.valid_payload.copy()
        payload['areas_interes'] = [self.area_todos.id]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador debería validar correctamente una única área, errores: {serializer.errors}"
        )

        areas_validadas = serializer.validated_data['areas_interes']

        self.assertEqual(len(areas_validadas), 1)

        self.assertEqual(areas_validadas[0], self.area_todos)



    def test_titulo_exactamente_cinco_caracteres_pasa_validacion(self):
        """
        Test: Validación del límite inferior permitido para el título.

        Given: Un payload válido donde el campo 'titulo' tiene una longitud 
            exacta de 5 caracteres (ej: 'Aviso').
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es marcado como válido (True), confirmando que 
            el validador 'validate_titulo' permite el límite inferior 
            definido en la regla de negocio (len >= 5).
        """
        payload = self.valid_payload.copy()
        payload['titulo'] = 'Aviso'

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El título de 5 caracteres debería ser válido, errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['titulo'], 'Aviso')



    def test_titulo_con_mas_de_cinco_caracteres_pasa_validacion(self):
        """
        Test: Validación de título con longitud superior al mínimo.

        Given: Un payload donde el campo 'titulo' tiene una longitud mayor 
            a 5 caracteres (ej: 'Reunión General de Hermanos').
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True), demostrando que cualquier 
            cadena que supere el umbral mínimo es aceptada correctamente.
        """
        payload = self.valid_payload.copy()
        payload['titulo'] = 'Reunión General de Hermanos 2024'

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"Un título largo debería ser válido, errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['titulo'], 'Reunión General de Hermanos 2024')



    def test_titulo_con_espacios_perifericos_aplica_strip_correctamente(self):
        """
        Test: Saneamiento de espacios en blanco en el título.

        Given: Un payload donde el campo 'titulo' contiene espacios en blanco 
            al inicio y al final (ej: '  Aviso Importante  ').
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y el valor resultante en 
            'validated_data' ha sido saneado mediante strip(), eliminando 
            los espacios innecesarios pero manteniendo el contenido central.
        """
        titulo_con_espacios = "  Aviso Importante  "
        payload = self.valid_payload.copy()
        payload['titulo'] = titulo_con_espacios

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El título con espacios debería ser válido tras el strip, errores: {serializer.errors}"
        )

        titulo_final = serializer.validated_data['titulo']
        self.assertEqual(titulo_final, "Aviso Importante")
        self.assertEqual(len(titulo_final), 16)



    def test_titulo_con_caracteres_especiales_validos_pasa_validacion(self):
        """
        Test: Soporte de caracteres especiales en el título.

        Given: Un payload donde el campo 'titulo' contiene caracteres propios 
            del español como tildes, la letra eñe y signos de apertura de 
            interrogación y exclamación (ej: '¡Mañana, reunión en la Peña! ¿Iréis?').
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y los caracteres se mantienen 
            íntegros en 'validated_data' sin problemas de codificación.
        """
        titulo_especial = "¡Atención! Mañana habrá reunión de la Peña."
        payload = self.valid_payload.copy()
        payload['titulo'] = titulo_especial

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El título con caracteres españoles debería ser válido, errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['titulo'], titulo_especial)



    def test_titulo_con_emojis_pasa_validacion(self):
        """
        Test: Soporte de caracteres Emoji en el título.

        Given: Un payload donde el campo 'titulo' contiene emojis (Unicode),
            cumpliendo con la longitud mínima requerida (ej: 'Aviso 📢').
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y los emojis se preservan 
            correctamente en 'validated_data' sin ser eliminados ni 
            corrompidos por el proceso de saneamiento.
        """
        titulo_con_emojis = "Comunicado Urgente 🚨📅"
        payload = self.valid_payload.copy()
        payload['titulo'] = titulo_con_emojis

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El título con emojis debería ser válido, errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['titulo'], titulo_con_emojis)



    def test_titulo_con_saltos_de_linea_internos(self):
        """
        Test: Manejo de saltos de línea dentro del título.

        Given: Un payload donde el campo 'titulo' contiene un salto de línea 
            en medio del texto (ej: 'Título con\nSalto').
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y los saltos de línea internos 
            se preservan en 'validated_data', mientras que el strip() solo 
            afecta a los extremos de la cadena completa.
        """
        titulo_con_lineas = "\nNoticia\nde Interés  "
        payload = self.valid_payload.copy()
        payload['titulo'] = titulo_con_lineas

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El título con saltos de línea internos debería ser válido, errores: {serializer.errors}"
        )

        titulo_esperado = "Noticia\nde Interés"
        self.assertEqual(serializer.validated_data['titulo'], titulo_esperado)

        self.assertGreaterEqual(len(serializer.validated_data['titulo']), 5)



    def test_contenido_texto_plano_valido_pasa_validacion(self):
        """
        Test: Validación de contenido en formato de texto plano.

        Given: Un payload válido donde el campo 'contenido' consiste únicamente 
            en una cadena de texto sin etiquetas HTML (ej: 'Reunión de junta mañana').
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y los datos validados contienen 
            el texto íntegro, confirmando que el validador de contenido permite 
            texto plano siempre que supere la longitud mínima.
        """
        contenido_plano = "Este es un comunicado de texto plano sin etiquetas."
        payload = self.valid_payload.copy()
        payload['contenido'] = contenido_plano

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El contenido en texto plano debería ser válido, errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['contenido'], contenido_plano)
        self.assertGreater(len(serializer.validated_data['contenido']), 10)



    def test_contenido_con_multiples_etiquetas_permitidas_pasa_validacion(self):
        """
        Test: Validación de contenido con set completo de etiquetas HTML permitidas.

        Given: Un payload donde el campo 'contenido' utiliza una estructura compleja
            incluyendo encabezados (h1-h3), formatos de texto (b, i, u, em, strong),
            listas (ul, ol, li), saltos de línea (br) y párrafos (p).
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y todas las etiquetas se preservan 
            íntegras en 'validated_data', confirmando que la política de limpieza 
            (bleach/saneamiento) es compatible con el editor de texto enriquecido.
        """
        contenido_complejo = (
            "<h1>Título 1</h1>"
            "<h2>Título 2</h2>"
            "<h3>Título 3</h3>"
            "<p>Texto con <b>negrita</b>, <i>cursiva</i> y <u>subrayado</u>.</p>"
            "<p>También con <em>énfasis</em> y <strong>fuerza</strong>.<br>Salto de línea.</p>"
            "<ul><li>Elemento lista 1</li><li>Elemento lista 2</li></ul>"
            "<ol><li>Paso 1</li></ol>"
        )
        payload = self.valid_payload.copy()
        payload['contenido'] = contenido_complejo

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El contenido con HTML enriquecido debería ser válido, errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['contenido'], contenido_complejo)

        self.assertIn('<h1>', serializer.validated_data['contenido'])
        self.assertIn('<ul>', serializer.validated_data['contenido'])
        self.assertIn('<br>', serializer.validated_data['contenido'])



    def test_contenido_con_enlaces_y_atributos_permitidos(self):
        """
        Test: Validación de contenido con enlaces HTML y sus atributos.

        Given: Un payload donde el campo 'contenido' incluye una etiqueta de 
            enlace <a> con atributos de destino (href), título (title) y 
            comportamiento de apertura (target="_blank").
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y los enlaces junto con sus 
            atributos se mantienen intactos en 'validated_data', confirmando 
            que la política de limpieza permite atributos específicos para <a>.
        """
        enlace_html = (
            '<p>Para más información, visita nuestra '
            '<a href="https://hermandad.es" title="Web Oficial" target="_blank">'
            'página web</a>.</p>'
        )
        payload = self.valid_payload.copy()
        payload['contenido'] = enlace_html

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El contenido con enlaces <a> y atributos debería ser válido, errores: {serializer.errors}"
        )

        resultado = serializer.validated_data['contenido']
        self.assertIn('href="https://hermandad.es"', resultado)
        self.assertIn('title="Web Oficial"', resultado)
        self.assertIn('target="_blank"', resultado)
        self.assertEqual(resultado, enlace_html)



    def test_contenido_con_etiquetas_no_permitidas_se_limpian_sin_fallar(self):
        """
        Test: Limpieza automática de etiquetas HTML no permitidas (div).

        Given: Un payload donde el campo 'contenido' incluye una etiqueta <div>,
            la cual no está en la lista blanca de etiquetas permitidas.
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True), pero los datos validados en 
            'validated_data' ya no contienen la etiqueta <div>, habiendo 
            mantenido únicamente el texto o las etiquetas permitidas en su interior.
        """
        contenido_con_div = "<div>Este es un contenido dentro de un div.</div>"
        contenido_esperado = "Este es un contenido dentro de un div."
        
        payload = self.valid_payload.copy()
        payload['contenido'] = contenido_con_div

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador debería ser válido tras limpiar las etiquetas, errores: {serializer.errors}"
        )

        resultado = serializer.validated_data['contenido']
        self.assertNotIn('<div>', resultado)
        self.assertNotIn('</div>', resultado)
        self.assertEqual(resultado, contenido_esperado)



    def test_contenido_que_tras_limpieza_mantiene_texto_valido(self):
        """
        Test: Validación de longitud sobre contenido saneado.

        Given: Un payload con algunas etiquetas no permitidas (div) pero 
            con texto real que supera los 10 caracteres.
        When: Se inicializa el ComunicadoFormSerializer y se invoca is_valid().
        Then: El serializador es válido (True) porque el residuo textual 
            tras eliminar las etiquetas no permitidas sigue cumpliendo 
            la regla de negocio de longitud mínima.
        """
        contenido_sucio = (
            "<div><strong>Aviso importante:</strong></div>"
            "<div>La reunión será el próximo lunes a las 20:00.</div>"
        )
        
        payload = self.valid_payload.copy()
        payload['contenido'] = contenido_sucio

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"Debe ser válido si el texto restante tras la limpieza es suficiente. Errores: {serializer.errors}"
        )

        resultado = serializer.validated_data['contenido']

        self.assertNotIn('<div>', resultado)

        self.assertIn('<strong>Aviso importante:</strong>', resultado)
        self.assertIn('La reunión será el próximo lunes', resultado)

        texto_plano = re.sub('<[^<]+?>', '', resultado).strip()
        self.assertGreaterEqual(len(texto_plano), 10)



    def test_contenido_con_etiquetas_en_mayusculas_se_procesa_correctamente(self):
        """
        Test: Manejo de etiquetas HTML en mayúsculas.

        Given: Un payload donde el campo 'contenido' usa etiquetas permitidas 
            pero escritas en mayúsculas (ej: <P>, <STRONG>).
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y las etiquetas son aceptadas 
            y normalizadas a minúsculas en 'validated_data' por el proceso 
            de saneamiento, manteniendo el texto íntegro.
        """
        contenido_mayusculas = "<P>Texto en un párrafo con <B>negrita</B>.</P>"
        contenido_normalizado = "<p>Texto en un párrafo con <b>negrita</b>.</p>"
        
        payload = self.valid_payload.copy()
        payload['contenido'] = contenido_mayusculas

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"Las etiquetas en mayúsculas deberían ser aceptadas, errores: {serializer.errors}"
        )

        resultado = serializer.validated_data['contenido']
        self.assertIn('Texto en un párrafo', resultado)
        self.assertIn('<p>', resultado)
        self.assertNotIn('<P>', resultado)



    def test_contenido_con_espacios_perifericos_aplica_strip_correctamente(self):
        """
        Test: Saneamiento de espacios en blanco en el contenido HTML.

        Given: Un payload donde el campo 'contenido' tiene espacios en blanco,
            tabulaciones o saltos de línea al inicio y al final de las etiquetas HTML.
        When: Se inicializa el ComunicadoFormSerializer con este payload y 
            se invoca el método is_valid().
        Then: El serializador es válido (True) y los datos validados en 
            'validated_data' han sido limpiados con strip(), eliminando el 
            espacio sobrante pero manteniendo intacto el HTML interno.
        """
        contenido_con_ruido = "  \n<p>Contenido con formato.</p>\t  "
        contenido_esperado = "<p>Contenido con formato.</p>"
        
        payload = self.valid_payload.copy()
        payload['contenido'] = contenido_con_ruido

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El contenido con espacios periféricos debería ser válido, errores: {serializer.errors}"
        )

        resultado = serializer.validated_data['contenido']
        self.assertEqual(resultado, contenido_esperado)

        self.assertFalse(resultado.startswith(" "))
        self.assertFalse(resultado.endswith(" "))



    def test_imagen_portada_jpg_valida_pasa_validacion(self):
        """
        Test: Validación de carga de imagen JPG válida dentro del límite de tamaño.

        Given: Un archivo de imagen en formato JPG de 100x100 píxeles,
            cuyo tamaño de archivo es inferior a 5MB.
        When: Se inicializa el ComunicadoFormSerializer incluyendo la imagen
            dentro del diccionario 'data' y se invoca is_valid().
        Then: El serializador es válido (True) y el archivo se reconoce 
            correctamente como un objeto de archivo en 'validated_data'.
        """
        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(file_io, format='JPEG')
        file_io.seek(0)
        
        imagen_valida = SimpleUploadedFile(
            name='test_portada.jpg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_valida

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La imagen JPG válida debería ser aceptada. Errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['imagen_portada'].name, 'test_portada.jpg')



    def test_imagen_portada_jpeg_valida_pasa_validacion(self):
        """
        Test: Validación de carga de imagen con extensión .jpeg.

        Given: Un archivo de imagen en formato JPEG (extensión larga)
            dentro de los límites de tamaño permitidos.
        When: Se inicializa el ComunicadoFormSerializer con este archivo.
        Then: El serializador es válido (True) y procesa el archivo 
            sin errores de extensión o formato.
        """
        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file_io, format='JPEG')
        file_io.seek(0)
        
        imagen_valida = SimpleUploadedFile(
            name='test_portada.jpeg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_valida

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La imagen JPEG con extensión larga debería ser aceptada. Errores: {serializer.errors}"
        )
        self.assertEqual(serializer.validated_data['imagen_portada'].name, 'test_portada.jpeg')



    def test_imagen_portada_png_valida_pasa_validacion(self):
        """
        Test: Validación de carga de imagen en formato PNG.

        Given: Un archivo de imagen en formato PNG de 100x100 píxeles,
            con canal alfa (RGBA) y tamaño inferior a 5MB.
        When: Se inicializa el ComunicadoFormSerializer con este archivo
            en el campo 'imagen_portada'.
        Then: El serializador es válido (True) y el objeto ImageField
            identifica correctamente el formato PNG.
        """
        file_io = io.BytesIO()
        image = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        image.save(file_io, format='PNG')
        file_io.seek(0)
        
        imagen_valida = SimpleUploadedFile(
            name='test_portada.png',
            content=file_io.read(),
            content_type='image/png'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_valida

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La imagen PNG debería ser aceptada correctamente. Errores: {serializer.errors}"
        )
        self.assertEqual(serializer.validated_data['imagen_portada'].name, 'test_portada.png')



    def test_imagen_portada_limite_exacto_5mb_pasa_validacion(self):
        """
        Test: Validación del límite superior de tamaño (Exactamente 5MB).

        Given: Un archivo que pesa exactamente 5.242.880 bytes (5MB).
        When: Se inicializa el ComunicadoFormSerializer con este archivo.
        Then: El serializador es válido (True), confirmando que el límite 
            de 5MB es inclusivo y permite archivos de ese tamaño exacto.
        """
        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(file_io, format='JPEG')

        cinco_megas_en_bytes = 5 * 1024 * 1024
        tamano_actual = file_io.tell()
        bytes_faltantes = cinco_megas_en_bytes - tamano_actual

        file_io.write(b'\x00' * bytes_faltantes)
        file_io.seek(0)
        
        imagen_limite = SimpleUploadedFile(
            name='heavy_image.jpg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_limite

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La imagen de exactamente 5MB (con estructura válida) debería ser aceptada. Errores: {serializer.errors}"
        )
        self.assertEqual(serializer.validated_data['imagen_portada'].size, cinco_megas_en_bytes)



    def test_imagen_portada_resolucion_4000x4000_pasa_validacion(self):
        """
        Test: Validación de una imagen con alta resolución (4000x4000 px).

        Given: Una imagen válida de 4000x4000 píxeles que no supera 
            el límite de peso de 5MB.
        When: Se inicializa el ComunicadoFormSerializer con esta imagen.
        Then: El serializador es válido (True) y las dimensiones se mantienen 
            correctas en el archivo resultante.
        """
        file_io = io.BytesIO()
        image = Image.new('RGB', (4000, 4000), color='green')
        image.save(file_io, format='JPEG', quality=60)
        file_io.seek(0)
        
        imagen_grande = SimpleUploadedFile(
            name='resolucion_alta.jpg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_grande

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La imagen de 4000x4000 debería ser aceptada. Errores: {serializer.errors}"
        )

        archivo_validado = serializer.validated_data['imagen_portada']
        archivo_validado.seek(0)
        with Image.open(archivo_validado) as img:
            width, height = img.size
            self.assertEqual(width, 4000)
            self.assertEqual(height, 4000)



    def test_imagen_portada_dimensiones_estandar_pasa_validacion(self):
        """
        Test: Validación de una imagen con dimensiones comunes (ej: 1920x1080).

        Given: Una imagen válida de 1920x1080 píxeles (Full HD).
        When: Se inicializa el ComunicadoFormSerializer con esta imagen.
        Then: El serializador es válido (True) y las dimensiones se mantienen 
            íntegras, confirmando que el rango de resolución permitido 
            es amplio.
        """
        file_io = io.BytesIO()
        ancho, alto = 1920, 1080
        image = Image.new('RGB', (ancho, alto), color='blue')
        image.save(file_io, format='JPEG')
        file_io.seek(0)
        
        imagen_estandar = SimpleUploadedFile(
            name='full_hd.jpg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_estandar

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La imagen de 1920x1080 debería ser aceptada. Errores: {serializer.errors}"
        )

        archivo_validado = serializer.validated_data['imagen_portada']
        archivo_validado.seek(0)
        with Image.open(archivo_validado) as img:
            self.assertEqual(img.width, ancho)
            self.assertEqual(img.height, alto)



    def test_imagen_portada_con_extension_en_mayusculas_pasa_validacion(self):
        """
        Test: Validación de imagen con extensión en mayúsculas (.JPG).

        Given: Un archivo de imagen válido cuyo nombre termina en '.JPG'.
        When: Se inicializa el ComunicadoFormSerializer con este archivo.
        Then: El serializador es válido (True) y procesa la imagen correctamente,
            confirmando que la validación de formato no es sensible a mayúsculas.
        """
        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='yellow')
        image.save(file_io, format='JPEG')
        file_io.seek(0)

        nombre_archivo = 'CAMARA_DSC001.JPG'
        imagen_mayusculas = SimpleUploadedFile(
            name=nombre_archivo,
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_mayusculas

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La extensión .JPG en mayúsculas debería ser aceptada. Errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['imagen_portada'].name, nombre_archivo)



    def test_imagen_portada_con_multiples_puntos_en_nombre_pasa_validacion(self):
        """
        Test: Validación de imagen con puntos adicionales en el nombre del archivo.

        Given: Un archivo de imagen válido cuyo nombre contiene varios puntos 
            (ej: 'banner.v1.final.jpg').
        When: Se inicializa el ComunicadoFormSerializer con este archivo.
        Then: El serializador es válido (True) y no se confunde con las 
            extensiones intermedias, reconociendo el archivo como un JPG válido.
        """
        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='purple')
        image.save(file_io, format='JPEG')
        file_io.seek(0)

        nombre_complejo = 'comunicado.oficial.v2.0.temp.jpg'
        imagen_puntos = SimpleUploadedFile(
            name=nombre_complejo,
            content=file_io.read(),
            content_type='image/jpeg'
        )

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_puntos

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"Los nombres con múltiples puntos deberían ser válidos. Errores: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['imagen_portada'].name, nombre_complejo)



    def test_areas_interes_con_lista_de_id_valido_pasa_validacion(self):
        """
        Test: Validación de relación Many-to-Many con un ID existente.

        Given: Una instancia de AreaInteres (JUVENTUD) creada en setUpTestData.
        When: Se inicializa el ComunicadoFormSerializer pasando el ID de dicha
            área dentro de una lista en el campo 'areas_interes'.
        Then: El serializador es válido (True) y los datos validados contienen
            el objeto del modelo correspondiente.
        """
        area = self.area_juventud 
        id_valido = area.id
        
        payload = self.valid_payload.copy()
        payload['areas_interes'] = [id_valido]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El ID de área válido debería ser aceptado. Errores: {serializer.errors}"
        )

        areas_validadas = serializer.validated_data['areas_interes']
        self.assertIn(area, areas_validadas)
        self.assertEqual(len(areas_validadas), 1)



    def test_areas_interes_con_multiples_ids_validos_pasa_validacion(self):
        """
        Test: Validación de múltiples relaciones Many-to-Many.

        Given: Dos o más instancias de AreaInteres existentes en la base de datos.
        When: Se envía una lista con ambos IDs en el campo 'areas_interes'.
        Then: El serializador es válido (True) y 'validated_data' contiene 
            una lista con ambas instancias del modelo.
        """
        ids_validos = [self.area_todos.id, self.area_juventud.id]
        
        payload = self.valid_payload.copy()
        payload['areas_interes'] = ids_validos

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"La lista con múltiples IDs válidos debería ser aceptada. Errores: {serializer.errors}"
        )

        areas_validadas = serializer.validated_data['areas_interes']
        self.assertEqual(len(areas_validadas), 2)
        self.assertIn(self.area_todos, areas_validadas)
        self.assertIn(self.area_juventud, areas_validadas)



    def test_areas_interes_con_id_todos_los_hermanos_pasa_validacion(self):
        """
        Test: Validación específica del área 'Todos los Hermanos'.

        Given: El área 'TODOS_HERMANOS' creada en la configuración inicial.
        When: Se envía su ID dentro de la lista de 'areas_interes'.
        Then: El serializador es válido y reconoce correctamente la instancia,
            permitiendo la comunicación global.
        """
        area_todos = self.area_todos
        
        payload = self.valid_payload.copy()
        payload['areas_interes'] = [area_todos.id]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El ID de 'Todos los Hermanos' debería ser válido. Errores: {serializer.errors}"
        )

        areas_validadas = serializer.validated_data['areas_interes']
        self.assertEqual(areas_validadas[0].nombre_area, AreaInteres.NombreArea.TODOS_HERMANOS)
        self.assertEqual(areas_validadas[0].id, area_todos.id)



    def test_areas_interes_array_json_valido_pasa_validacion(self):
        """
        Test: Validación de recepción de áreas de interés como array JSON.

        Given: Una lista de IDs válidos representados en formato de array.
        When: Se inicializa el ComunicadoFormSerializer con este array.
        Then: El serializador es válido (True) y mapea cada ID del JSON 
            a su respectiva instancia de modelo en la base de datos.
        """
        ids_envio = [self.area_todos.id, self.area_juventud.id]

        payload = self.valid_payload.copy()
        payload['areas_interes'] = ids_envio 

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador debe aceptar un array de IDs. Errores: {serializer.errors}"
        )

        areas_validadas = serializer.validated_data['areas_interes']
        self.assertEqual(len(areas_validadas), 2)

        for area in areas_validadas:
            self.assertIsInstance(area, AreaInteres)



    def test_comunicado_payload_completo_campos_definidos_pasa_validacion(self):
        """
        Test: Validación de un payload con la estructura exacta definida.

        Given: Un diccionario que contiene exclusivamente los campos:
            id (opcional en creación), titulo, contenido, imagen_portada, 
            tipo_comunicacion y areas_interes.
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador es válido (True) y los datos validados contienen
            exactamente estas llaves mapeadas correctamente.
        """
        imagen = self.generar_imagen_valida()

        payload_estricto = {
            'titulo': 'Nuevo comunicado de la Hermandad',
            'contenido': 'Cuerpo del mensaje con información relevante.',
            'imagen_portada': imagen,
            'tipo_comunicacion': Comunicado.TipoComunicacion.INFORMATIVO,
            'areas_interes': [self.area_juventud.id]
        }

        serializer = ComunicadoFormSerializer(data=payload_estricto)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El payload con los campos definidos debería ser válido. Errores: {serializer.errors}"
        )

        data = serializer.validated_data
        self.assertEqual(data['titulo'], payload_estricto['titulo'])
        self.assertEqual(data['tipo_comunicacion'], payload_estricto['tipo_comunicacion'])
        self.assertIn(self.area_juventud, data['areas_interes'])



    def test_comunicado_con_campo_extra_falla_validacion_estricta(self):
        """
        Test: Protección contra Mass Assignment (Esquema estricto).

        Given: Un payload que incluye un campo 'created_at' no definido 
            en el serializador.
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) porque 
            'to_internal_value' bloquea cualquier campo extra no permitido.
        """
        payload_con_extra = self.valid_payload.copy()
        payload_con_extra['created_at'] = '2023-01-01T00:00:00Z'
        campo_intruso = 'created_at'

        serializer = ComunicadoFormSerializer(data=payload_con_extra)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un campo no definido. El control de Mass Assignment falló."
        )

        mensaje_error = str(serializer.errors)
        self.assertIn('error', serializer.errors)
        self.assertIn('Campos no permitidos detectados', mensaje_error)
        self.assertIn(campo_intruso, mensaje_error)



    def test_comunicado_con_campo_is_admin_extra_falla_por_seguridad(self):
        """
        Test: Protección contra Mass Assignment de campos sensibles (is_admin).

        Given: Un payload que intenta inyectar el campo 'is_admin' para 
            manipular privilegios.
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) y el error 
            debe mencionar que el campo no está permitido.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['is_admin'] = True
        campo_intruso = 'is_admin'

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió el campo 'is_admin'. ¡Riesgo de seguridad!"
        )
        
        self.assertIn('error', serializer.errors)
        mensaje_error = str(serializer.errors['error'])
        
        self.assertIn('Campos no permitidos detectados', mensaje_error)
        self.assertIn(campo_intruso, mensaje_error)



    def test_comunicado_con_campo_usuario_id_extra_falla_por_suplantacion(self):
        """
        Test: Protección contra suplantación de identidad (usuario_id).

        Given: Un payload que intenta asignar un autor manualmente enviando 'usuario_id'.
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) y el error 
            debe indicar que el campo no está permitido en el esquema estricto.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['usuario_id'] = 999
        campo_intruso = 'usuario_id'

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió el campo 'usuario_id'. ¡Riesgo de suplantación!"
        )
        
        mensaje_error = str(serializer.errors)
        self.assertIn('error', serializer.errors)
        self.assertIn('Campos no permitidos detectados', mensaje_error)
        self.assertIn(campo_intruso, mensaje_error)



    def test_comunicado_con_campo_inventado_hack_falla_por_esquema_estricto(self):
        """
        Test: Protección contra ruido en el payload (Campo inventado).

        Given: Un payload que incluye un campo totalmente ajeno al dominio: 'hack'.
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) y el error 
            debe capturar el campo 'hack' como no permitido.
        """
        payload_con_ruido = self.valid_payload.copy()
        payload_con_ruido['hack'] = 'drop table hermanos;'
        campo_intruso = 'hack'

        serializer = ComunicadoFormSerializer(data=payload_con_ruido)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un campo inventado ('hack'). El esquema no es lo suficientemente estricto."
        )

        mensaje_error = str(serializer.errors)
        self.assertIn('error', serializer.errors)
        self.assertIn('Campos no permitidos detectados', mensaje_error)
        self.assertIn(campo_intruso, mensaje_error)



    def test_comunicado_con_multiples_campos_extra_falla_y_los_lista_todos(self):
        """
        Test: Protección contra Mass Assignment múltiple.

        Given: Un payload con varios campos no permitidos: 'hack', 'is_admin', 'usuario_id'.
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) y el mensaje de error 
            debe listar todos los campos intrusos detectados.
        """
        campos_intrusos = ['hack', 'is_admin', 'usuario_id']
        payload_sucio = self.valid_payload.copy()
        
        for campo in campos_intrusos:
            payload_sucio[campo] = 'valor_no_permitido'

        serializer = ComunicadoFormSerializer(data=payload_sucio)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió múltiples campos extra a la vez."
        )

        self.assertIn('error', serializer.errors)
        mensaje_error = str(serializer.errors['error'])
        
        self.assertIn('Campos no permitidos detectados', mensaje_error)
        for campo in campos_intrusos:
            self.assertIn(
                campo, 
                mensaje_error, 
                msg=f"El campo extra '{campo}' no fue reportado en el mensaje de error."
            )



    def test_comunicado_payload_vacio_falla_por_campos_requeridos(self):
        """
        Test: Validación de payload vacío.

        Given: Un diccionario vacío {}.
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) y los errores 
            deben listar todos los campos obligatorios que faltan.
        """
        payload_vacio = {}

        serializer = ComunicadoFormSerializer(data=payload_vacio)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)

        campos_obligatorios = ['titulo', 'contenido', 'tipo_comunicacion', 'areas_interes']
        
        for campo in campos_obligatorios:
            self.assertIn(campo, serializer.errors)
            self.assertEqual(serializer.errors[campo][0].code, 'required')



    def test_comunicado_titulo_vacio_falla_validacion(self):
        """
        Test: Validación de título vacío (cadena vacía).

        Given: Un payload donde el campo 'titulo' es una cadena vacía "".
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) y el error 
            debe indicar que el título no puede estar formado solo por espacios.
        """
        payload_titulo_vacio = self.valid_payload.copy()
        payload_titulo_vacio['titulo'] = ""

        serializer = ComunicadoFormSerializer(data=payload_titulo_vacio)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un título vacío."
        )

        self.assertIn('titulo', serializer.errors)
        mensaje_error = str(serializer.errors['titulo'][0])
        self.assertEqual(
            mensaje_error, 
            "El título no puede estar formado solo por espacios en blanco."
        )



    def test_comunicado_titulo_solo_espacios_falla_validacion_limpieza(self):
        """
        Test: Validación de título con espacios en blanco.

        Given: Un título que contiene 5 caracteres de espacio ("     ").
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) porque el 
            método 'validate_titulo' limpia los espacios y detecta el vacío.
        """
        payload_solo_espacios = self.valid_payload.copy()
        payload_solo_espacios['titulo'] = "     "

        serializer = ComunicadoFormSerializer(data=payload_solo_espacios)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un título compuesto solo por espacios."
        )

        self.assertIn('titulo', serializer.errors)
        mensaje_error = str(serializer.errors['titulo'][0])
        self.assertEqual(
            mensaje_error, 
            "El título no puede estar formado solo por espacios en blanco."
        )



    def test_comunicado_titulo_demasiado_corto_falla_validacion(self):
        """
        Test: Validación de longitud mínima del título.

        Given: Un título con 4 caracteres ("Hdad"), incumpliendo el mínimo de 5 
            definido en el serializador.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) y el mensaje de 
            error debe indicar que requiere al menos 5 caracteres.
        """
        payload_corto = self.valid_payload.copy()
        payload_corto['titulo'] = "Hdad" 

        serializer = ComunicadoFormSerializer(data=payload_corto)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un título de menos de 5 caracteres."
        )

        self.assertIn('titulo', serializer.errors)
        mensaje_error = str(serializer.errors['titulo'][0])
        self.assertEqual(
            mensaje_error, 
            "El título es demasiado corto. Debe tener al menos 5 caracteres."
        )



    def test_comunicado_titulo_null_falla_validacion(self):
        """
        Test: Validación de título con valor null.

        Given: Un payload donde 'titulo' es None (null en JSON).
        When: Se inicializa el ComunicadoFormSerializer con este payload.
        Then: El serializador debe fallar (is_valid es False) con el 
            código de error 'null' de DRF.
        """
        payload_titulo_null = self.valid_payload.copy()
        payload_titulo_null['titulo'] = None

        serializer = ComunicadoFormSerializer(data=payload_titulo_null)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un valor null en el título."
        )

        self.assertIn('titulo', serializer.errors)
        self.assertEqual(
            serializer.errors['titulo'][0].code, 
            'null',
            msg="El error debería ser de tipo 'null' (This field may not be null)."
        )



    def test_comunicado_titulo_como_numero_se_trata_como_string_y_valida(self):
        """
        Test: Validación de tipo de dato (Número en campo CharField).

        Given: Un payload donde 'titulo' es un entero (123).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: DRF lo convierte a string "123", pero tu validación de 
            longitud mínima (5) debería rechazarlo por ser corto.
        """
        payload_numero = self.valid_payload.copy()
        payload_numero['titulo'] = 123

        serializer = ComunicadoFormSerializer(data=payload_numero)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un número que al ser string es demasiado corto."
        )

        self.assertIn('titulo', serializer.errors)
        mensaje_error = str(serializer.errors['titulo'][0])
        self.assertEqual(
            mensaje_error, 
            "El título es demasiado corto. Debe tener al menos 5 caracteres."
        )



    def test_comunicado_titulo_como_lista_falla_por_tipo_incorrecto(self):
        """
        Test: Validación de tipo de dato complejo (Lista en CharField).

        Given: Un payload donde 'titulo' es una lista ['Not', 'a', 'string'].
        When: Se procesa por el ComunicadoFormSerializer.
        Then: DRF debe fallar antes de la validación de negocio con un 
            error de tipo ('invalid').
        """
        payload_lista = self.valid_payload.copy()
        payload_lista['titulo'] = ["Hdad", "de", "Prueba"]

        serializer = ComunicadoFormSerializer(data=payload_lista)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió una lista en un campo CharField."
        )

        self.assertIn('titulo', serializer.errors)
        codigo_error = serializer.errors['titulo'][0].code

        self.assertEqual(
            codigo_error, 
            'invalid',
            msg=f"Se esperaba el código 'invalid', se obtuvo: {codigo_error}"
        )



    def test_comunicado_titulo_como_objeto_falla_por_tipo_incorrecto(self):
        """
        Test: Validación de tipo de dato (Diccionario/Objeto en CharField).

        Given: Un payload donde 'titulo' es un objeto JSON {"key": "value"}.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: DRF debe fallar con un error de tipo (not a string).
        """
        payload_objeto = self.valid_payload.copy()
        payload_objeto['titulo'] = {"intento_hack": "titulo_falso"}

        serializer = ComunicadoFormSerializer(data=payload_objeto)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un objeto JSON en un campo CharField."
        )

        self.assertIn('titulo', serializer.errors)

        codigo_error = serializer.errors['titulo'][0].code
        self.assertIn(
            codigo_error, 
            ['not_a_string', 'invalid'],
            msg=f"Se esperaba un error de tipo de dato, se obtuvo: {codigo_error}"
        )



    def test_comunicado_contenido_vacio_falla_validacion(self):
        """
        Test: Validación de contenido vacío.

        Given: Un payload donde el campo 'contenido' es una cadena vacía "".
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) y mostrar el 
            mensaje de error personalizado indicando que no puede estar vacío.
        """
        payload_contenido_vacio = self.valid_payload.copy()
        payload_contenido_vacio['contenido'] = ""

        serializer = ComunicadoFormSerializer(data=payload_contenido_vacio)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un comunicado sin contenido."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no puede estar vacío."
        )



    def test_comunicado_contenido_solo_espacios_falla_validacion(self):
        """
        Test: Validación de contenido compuesto solo por espacios.

        Given: Un payload donde el campo 'contenido' contiene múltiples espacios "     ".
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) porque el método 
            'validate_contenido' limpia los espacios y detecta que está vacío.
        """
        payload_espacios = self.valid_payload.copy()
        payload_espacios['contenido'] = "       "

        serializer = ComunicadoFormSerializer(data=payload_espacios)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un contenido compuesto solo por espacios."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no puede estar vacío."
        )



    def test_comunicado_contenido_null_falla_validacion(self):
        """
        Test: Validación de contenido con valor null.

        Given: Un payload donde 'contenido' es None (null en JSON).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) con el 
            código de error 'null' nativo de DRF.
        """
        payload_contenido_null = self.valid_payload.copy()
        payload_contenido_null['contenido'] = None

        serializer = ComunicadoFormSerializer(data=payload_contenido_null)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió un valor null en el contenido."
        )

        self.assertIn('contenido', serializer.errors)
        self.assertEqual(
            serializer.errors['contenido'][0].code, 
            'null',
            msg="El error debería ser de tipo 'null' (This field may not be null)."
        )



    def test_comunicado_contenido_como_numero_se_trata_como_string(self):
        """
        Test: Validación de tipo de dato (Número en campo de contenido).

        Given: Un payload donde 'contenido' es un entero (8888).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: DRF lo convierte a string "8888". Este valor no tiene etiquetas 
            prohibidas y sobrevive a bleach, por lo que debería ser VÁLIDO.
        """
        payload_numero = self.valid_payload.copy()
        payload_numero['contenido'] = 8888 

        serializer = ComunicadoFormSerializer(data=payload_numero)
        es_valido = serializer.is_valid()

        self.assertTrue(
            es_valido, 
            msg=f"El serializador falló con un número en el contenido: {serializer.errors}"
        )

        self.assertEqual(serializer.validated_data['contenido'], "8888")



    def test_comunicado_contenido_como_lista_falla_por_tipo_incorrecto(self):
        """
        Test: Validación de tipo de dato complejo (Lista en contenido).

        Given: Un payload donde 'contenido' es una lista ["texto", "html"].
        When: Se procesa por el ComunicadoFormSerializer.
        Then: DRF debe fallar con un error de tipo ('invalid') antes de 
            llegar a la validación de negocio.
        """
        payload_lista = self.valid_payload.copy()
        payload_lista['contenido'] = ["<p>Párrafo 1</p>", "<p>Párrafo 2</p>"]

        serializer = ComunicadoFormSerializer(data=payload_lista)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió una lista en un campo de texto (contenido)."
        )

        self.assertIn('contenido', serializer.errors)
        self.assertEqual(
            serializer.errors['contenido'][0].code, 
            'invalid',
            msg=f"Se esperaba el código 'invalid', se obtuvo: {serializer.errors['contenido'][0].code}"
        )



    def test_comunicado_contenido_con_script_falla_por_blacklist(self):
        """
        Test: Protección contra inyección de scripts (XSS).

        Given: Un payload con la etiqueta prohibida '<script>'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar bloqueando la inyección.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = "<script>alert('Te he hackeado la hermandad');</script>"

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió una etiqueta <script> prohibida."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])

        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_iframe_falla_por_blacklist(self):
        """
        Test: Protección contra inyección de iframes (Clickjacking/Phishing).

        Given: Un contenido que intenta incrustar un sitio externo con '<iframe>'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) debido a la 
            presencia de una etiqueta prohibida en la lista negra.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = (
            "<p>Mira este video:</p>"
            "<iframe src='http://sitio-malvado.com/login-falso'></iframe>"
        )

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió una etiqueta <iframe> prohibida."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_object_falla_por_blacklist(self):
        """
        Test: Protección contra inyección de objetos externos (<object>).

        Given: Un contenido que intenta usar la etiqueta prohibida '<object>'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) con el mensaje
            de error de formato no válido/seguridad.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = (
            "<p>Mira este archivo:</p>"
            "<object data='http://malicious.com/exploit.swf'></object>"
        )

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_embed_falla_por_blacklist(self):
        """
        Test: Protección contra inyección de contenido incrustado (<embed>).

        Given: Un payload con la etiqueta prohibida '<embed>'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) y el mensaje de 
            error debe ser el genérico de seguridad/limpieza.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = (
            "<p>Mira este archivo:</p>"
            "<embed type='video/quicktime' src='http://malicious.com/exploit.mov' width='300' height='200'>"
        )

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió una etiqueta <embed> prohibida."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_style_falla_por_blacklist(self):
        """
        Test: Protección contra inyección de estilos CSS (<style>).

        Given: Un contenido que intenta inyectar un bloque de estilos.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) detectando 
            la firma de la etiqueta prohibida.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = (
            "<style>body { display: none !important; }</style>"
            "<p>Este texto no se vería si el CSS cargara.</p>"
        )

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió una etiqueta <style> prohibida."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_onerror_falla_por_blacklist(self):
        """
        Test: Protección contra atributos de evento JavaScript (XSS).

        Given: Un contenido con una etiqueta <img> que usa el atributo 'onerror='.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) al detectar 
            la cadena prohibida 'onerror=' en el texto.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = (
            "<p>Imagen decorativa</p>"
            "<img src='ruta_inexistente.jpg' onerror='alert(\"XSS\")'>"
        )

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió el atributo de evento 'onerror='."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_onload_falla_por_blacklist(self):
        """
        Test: Protección contra atributo 'onload' en etiqueta permitida (<p>).

        Given: Un párrafo estándar <p> que incluye el atributo 'onload='.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) al detectar 
            'onload=' en la lista negra de atributos.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = "<p onload='alert(\"Hack\")'>Texto legítimo</p>"

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió el atributo de evento 'onload=' en un párrafo."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_onerror_fragmento_falla_por_blacklist(self):
        """
        Test: Protección contra fragmentos de atributos de evento (onerror=).

        Given: Un contenido que incluye la cadena prohibida 'onerror=' de forma aislada o en atributo.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) al detectar la firma 
            específica de la lista negra.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = "Texto normal con trampa: <b onerror=alert(1)>negrita</b>"

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió la cadena prohibida 'onerror='."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_con_onload_fragmento_falla_por_blacklist(self):
        """
        Test: Protección contra fragmentos de atributos de evento (onload=).

        Given: Un contenido que incluye la cadena prohibida 'onload=' inyectada.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) al detectar la firma 
            específica de la lista negra 'onload='.
        """
        payload_malicioso = self.valid_payload.copy()
        payload_malicioso['contenido'] = "Noticia importante <p onload='alert(1)'>Cuerpo del mensaje</p>"

        serializer = ComunicadoFormSerializer(data=payload_malicioso)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió la cadena prohibida 'onload='."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_vacio_tras_limpieza_falla(self):
        """
        Test: Validación de contenido que solo contiene etiquetas no permitidas.

        Given: Un contenido con etiquetas no permitidas por bleach pero sin texto 
            (ej: "<div><span></span></div>").
        When: Se procesa por el ComunicadoFormSerializer.
        Then: Bleach elimina las etiquetas, el resultado es "" y el serializador 
            debe lanzar la ValidationError de "formato no válido".
        """

        payload_evaporado = self.valid_payload.copy()
        payload_evaporado['contenido'] = "<div><span></span></div>"

        serializer = ComunicadoFormSerializer(data=payload_evaporado)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió contenido que queda vacío tras la limpieza."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_solo_etiquetas_no_permitidas_falla(self):
        """
        Test: Validación de contenido con etiquetas fuera de la allowlist.

        Given: Un payload con etiquetas HTML que no están permitidas (<div> y <span>).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: Bleach las elimina por completo. Al quedar un string vacío, 
            la validación final debe lanzar el error de seguridad.
        """
        payload_solo_divs = self.valid_payload.copy()
        payload_solo_divs['contenido'] = "<div><span></span></div>"

        serializer = ComunicadoFormSerializer(data=payload_solo_divs)
        es_valido = serializer.is_valid()

        self.assertFalse(
            es_valido, 
            msg="El serializador permitió etiquetas no autorizadas que no aportan texto."
        )

        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_html_malformado_extremo_se_sanea(self):
        """
        Test: Resiliencia ante HTML malformado.

        Given: Un contenido con etiquetas mal cerradas, corchetes angulares 
            redundantes y una etiqueta prohibida malformada.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: La Blacklist o Bleach deben neutralizar el ataque. En este caso,
            '<<<<script' contiene '<script', por lo que la Blacklist debería saltar.
        """
        payload_caos = self.valid_payload.copy()
        payload_caos['contenido'] = "<<<<script>alert('XSS')</script> <p>Texto <b>negrita sin cerrar"

        serializer = ComunicadoFormSerializer(data=payload_caos)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)

        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_extremadamente_largo_estres(self):
        """
        Test: Prueba de estrés con contenido masivo.

        Given: Un payload donde 'contenido' tiene 1.000.000 de caracteres (aprox 1MB).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe procesarlo sin colapsar. 
            Nota: Si quieres poner un límite real, deberías añadir 
            MaxLengthValidator en el campo.
        """
        contenido_gigante = "A" * 1_000_000 
        payload_estres = self.valid_payload.copy()
        payload_estres['contenido'] = contenido_gigante

        start_time = time.time()
        serializer = ComunicadoFormSerializer(data=payload_estres)
        es_valido = serializer.is_valid()
        end_time = time.time()

        self.assertTrue(es_valido)
        print(f"\n[INFO] Tiempo de procesamiento para 1MB: {end_time - start_time:.4f}s")



    def test_comunicado_imagen_portada_demasiado_grande_falla(self):
        """
        Test: Validación de límite de tamaño de archivo (5MB).

        Given: Un archivo de imagen que pesa 6MB (simulado).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) con el mensaje
            indicando que el máximo permitido es 5MB.
        """
        imagen_pesada = SimpleUploadedFile(
            "foto_gigante.jpg", 
            b"contenido_falso", 
            content_type="image/jpeg"
        )
        imagen_pesada.size = 6 * 1024 * 1024 + 1 

        payload_pesado = self.valid_payload.copy()
        payload_pesado['imagen_portada'] = imagen_pesada

        serializer = ComunicadoFormSerializer(data=payload_pesado)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('imagen_portada', serializer.errors)
        
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "La imagen es demasiado grande. El máximo permitido es de 5MB."
        )



    def test_comunicado_imagen_portada_limite_exacto_falla(self):
        """
        Test: Precisión del límite de tamaño.

        Given: Un archivo cuyo tamaño es exactamente (5 * 1024 * 1024) + 1 byte.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) porque el operador
            '>' detecta que se ha superado el máximo permitido.
        """
        limite_maximo_bytes = 5 * 1024 * 1024
        tamano_prohibido = limite_maximo_bytes + 1

        imagen_al_limite = SimpleUploadedFile(
            "foto_limite.png", 
            b"data", 
            content_type="image/png"
        )

        imagen_al_limite.size = tamano_prohibido

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_al_limite

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador debería rechazar 5MB + 1 byte.")

        self.assertIn('imagen_portada', serializer.errors)
        self.assertEqual(
            str(serializer.errors['imagen_portada'][0]),
            "La imagen es demasiado grande. El máximo permitido es de 5MB."
        )



    def test_comunicado_imagen_portada_gif_falla_por_extension(self):
        """
        Test: Restricción de formatos de imagen.

        Given: Un archivo de imagen con extensión '.gif'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) porque .gif 
            no está en la lista de permitidos (.jpg, .jpeg, .png).
        """
        imagen_gif = SimpleUploadedFile(
            "animacion.gif", 
            b"contenido_binario_gif", 
            content_type="image/gif"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_gif

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('imagen_portada', serializer.errors)
        
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn("Formato de archivo no permitido (.gif)", mensaje_error)
        self.assertIn("Solo se admiten imágenes JPG, JPEG o PNG", mensaje_error)



    def test_comunicado_imagen_portada_bmp_falla_por_extension(self):
        """
        Test: Restricción de formato BMP.

        Given: Un archivo de imagen con extensión '.bmp'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) indicando
            que el formato no está permitido.
        """
        imagen_bmp = SimpleUploadedFile(
            "escudo_hermandad.bmp", 
            b"contenido_binario_bmp", 
            content_type="image/bmp"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_bmp

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('imagen_portada', serializer.errors)
        
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "Formato de archivo no permitido (.bmp). Solo se admiten imágenes JPG, JPEG o PNG."
        )



    def test_comunicado_imagen_portada_webp_falla_por_extension(self):
        """
        Test: Restricción de formato WebP.

        Given: Un archivo de imagen con extensión '.webp'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) indicando
            que el formato no está permitido, a pesar de ser una imagen.
        """
        imagen_webp = SimpleUploadedFile(
            "imagen_moderna.webp", 
            b"contenido_binario_webp", 
            content_type="image/webp"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_webp

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('imagen_portada', serializer.errors)
        
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "Formato de archivo no permitido (.webp). Solo se admiten imágenes JPG, JPEG o PNG."
        )



    def test_comunicado_imagen_portada_svg_falla_por_extension(self):
        """
        Test: Restricción de formato SVG por seguridad.

        Given: Un archivo con extensión '.svg' que contiene un script malicioso.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) por la extensión,
            antes incluso de intentar procesar el XML.
        """
        contenido_svg_malicioso = (
            '<?xml version="1.0" standalone="no"?>'
            '<svg onload="alert(1)" xmlns="http://www.w3.org/2000/svg">'
            '<circle r="10" />'
            '</svg>'
        )
        imagen_svg = SimpleUploadedFile(
            "ataque.svg", 
            contenido_svg_malicioso.encode('utf-8'), 
            content_type="image/svg+xml"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_svg

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('imagen_portada', serializer.errors)
        
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "Formato de archivo no permitido (.svg). Solo se admiten imágenes JPG, JPEG o PNG."
        )



    def test_comunicado_imagen_sin_extension_falla(self):
        """
        Test: Rechazo de archivos sin extensión.

        Given: Un archivo de imagen válido internamente pero con nombre sin extensión ('portada').
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) porque la 
            cadena vacía '' no es una extensión permitida.
        """
        imagen_anonima = SimpleUploadedFile(
            "imagen_sin_ext", 
            b"contenido_binario_de_imagen", 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_anonima

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('imagen_portada', serializer.errors)
        
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn("Formato de archivo no permitido", mensaje_error)



    def test_comunicado_imagen_doble_extension_falla(self):
        """
        Test: Protección contra archivos con doble extensión (.jpg.exe).

        Given: Un archivo malicioso llamado 'evidencia.jpg.exe'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe identificar '.exe' como la extensión real
            y rechazarlo por no estar en la allowlist.
        """
        archivo_malicioso = SimpleUploadedFile(
            "imagen_falsa.jpg.exe", 
            b"contenido_binario_malicioso", 
            content_type="application/x-msdownload"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = archivo_malicioso

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un archivo .exe camuflado.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn(".exe", mensaje_error)
        self.assertIn("Formato de archivo no permitido", mensaje_error)



    def test_comunicado_imagen_mismatch_contenido_real_falla(self):
        """
        Test: Validación de integridad binaria del archivo.

        Given: Un archivo llamado 'foto.jpg' cuyo contenido real es un 
            ejecutable binario (cabecera MZ de Windows).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: La extensión .jpg pasa, pero Pillow lanza una excepción al 
            intentar abrirlo. El serializador debe capturarla y fallar.
        """
        contenido_ejecutable = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"
        imagen_falsa = SimpleUploadedFile(
            "virgen_de_la_paz.jpg", 
            contenido_ejecutable, 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_falsa

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un binario como si fuera imagen.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo subido no es una imagen válida o está dañado."
        )



    def test_comunicado_imagen_texto_plano_disfrazado_falla(self):
        """
        Test: Protección contra archivos de texto con extensión de imagen.

        Given: Un archivo llamado 'notas.png' que contiene solo texto ASCII.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: Pillow (Image.open) no reconocerá la firma de un PNG real y 
            lanzará una excepción, invalidando el serializador.
        """
        contenido_texto = b"Este es un mensaje secreto que intenta saltar el filtro."
        imagen_falsa = SimpleUploadedFile(
            "comunicado_oficial.png", 
            contenido_texto, 
            content_type="image/png"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_falsa

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó texto plano como PNG.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo subido no es una imagen válida o está dañado."
        )



    def test_comunicado_imagen_contenido_corrupto_falla(self):
        """
        Test: Protección contra archivos binarios corruptos o aleatorios.

        Given: Un archivo llamado 'corrupta.jpg' que contiene bytes aleatorios
            sin estructura de imagen.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: Pillow debe fallar al procesar el stream binario y el serializador
            debe devolver el mensaje de error por defecto para excepciones.
        """
        contenido_basura = b"\xff\xff\xff\xff\x00\x11\x22\x33\x44\x55"
        imagen_corrupta = SimpleUploadedFile(
            "imagen_rota.jpg", 
            contenido_basura, 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_corrupta

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó bytes corruptos como imagen.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo subido no es una imagen válida o está dañado."
        )



    from io import BytesIO

    def test_comunicado_imagen_extension_falsa_formato_distinto_falla(self):
        """
        Test: Detección de mismatch entre extensión y formato real.

        Given: Una imagen real en formato BMP pero guardada con nombre '.jpg'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: La extensión pasa, Pillow abre la imagen con éxito, pero al 
            verificar 'img.format', el serializador detecta que es BMP 
            y lanza la ValidationError de 'extensión falsa'.
        """
        archivo_en_memoria = io.BytesIO()
        imagen_real = Image.new('RGB', (100, 100), color='red')
        imagen_real.save(archivo_en_memoria, format='BMP')
        archivo_en_memoria.seek(0)

        imagen_disfrazada = SimpleUploadedFile(
            "foto_engañosa.jpg", 
            archivo_en_memoria.read(), 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_disfrazada

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un BMP disfrazado de JPG.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo parece tener una extensión falsa o está corrupto. Asegúrese de subir una imagen real."
       )



    def test_comunicado_imagen_dimensiones_excesivas_falla(self):
        """
        Test: Validación de dimensiones máximas (4000x4000px).

        Given: Una imagen válida en formato PNG pero con un ancho de 4001px.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) indicando que
            las dimensiones superan el máximo permitido.
        """
        archivo_en_memoria = io.BytesIO()
        width, height = 4001, 4000
        imagen_grande = Image.new('RGB', (width, height), color='blue')
        imagen_grande.save(archivo_en_memoria, format='PNG')
        archivo_en_memoria.seek(0)

        imagen_prohibida = SimpleUploadedFile(
            "foto_panoramica.png", 
            archivo_en_memoria.read(), 
            content_type="image/png"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_prohibida

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó una imagen de 4001px de ancho.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn(f"Las dimensiones de la imagen son demasiado grandes ({width}x{height})", mensaje_error)



    def test_comunicado_imagen_dimensiones_verticales_excesivas_falla(self):
        """
        Test: Validación de altura máxima (4000px).

        Given: Una imagen válida en formato PNG pero con un alto de 4001px.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) indicando que
            la altura supera el máximo permitido de 4000 píxeles.
        """
        archivo_en_memoria = io.BytesIO()
        width, height = 4000, 4001
        imagen_alta = Image.new('RGB', (width, height), color='green')
        imagen_alta.save(archivo_en_memoria, format='PNG')
        archivo_en_memoria.seek(0)

        imagen_prohibida = SimpleUploadedFile(
            "foto_vertical_extrema.png", 
            archivo_en_memoria.read(), 
            content_type="image/png"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_prohibida

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó una imagen de 4001px de alto.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn(f"Las dimensiones de la imagen son demasiado grandes ({width}x{height})", mensaje_error)



    def test_comunicado_imagen_dimensiones_prohibitivas_falla(self):
        """
        Test: Protección contra imágenes de resolución masiva.

        Given: Una imagen de 8000x8000 píxeles.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar inmediatamente al detectar que 
            supera el límite de 4000px, protegiendo la RAM del servidor.
        """
        archivo_en_memoria = io.BytesIO()
        width, height = 8000, 8000
        imagen_masiva = Image.new('RGB', (width, height), color='white')
        imagen_masiva.save(archivo_en_memoria, format='JPEG')
        archivo_en_memoria.seek(0)

        imagen_payload = SimpleUploadedFile(
            "bomba_pixeles.jpg", 
            archivo_en_memoria.read(), 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_payload

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('imagen_portada', serializer.errors)
        
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn(f"Las dimensiones de la imagen son demasiado grandes ({width}x{height})", mensaje_error)



    def test_comunicado_imagen_dimensiones_nulas_falla(self):
        """
        Test: Protección contra imágenes con dimensiones 0x0.

        Given: Un archivo que intenta hacerse pasar por imagen pero no tiene dimensiones.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: Pillow lanzará una excepción al no poder procesar una imagen sin área,
            y el serializador devolverá el mensaje de error por defecto.
        """
        archivo_en_memoria = io.BytesIO(b"GIF89a\x00\x00\x00\x00")
        archivo_en_memoria.seek(0)

        imagen_nula = SimpleUploadedFile(
            "nada.jpg", 
            archivo_en_memoria.read(), 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_nula

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó una imagen de 0x0.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo subido no es una imagen válida o está dañado."
        )



    def test_comunicado_imagen_limite_horizontal_maximo_pasa(self):
        """
        Test: Aceptación de imagen en el límite exacto (4000px).

        Given: Una imagen de 4000x1 píxeles (justo en el límite).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe ser válido (is_valid es True) porque 
            el límite es inclusivo (no estrictamente menor).
        """
        archivo_en_memoria = io.BytesIO()
        width, height = 4000, 1
        imagen_limite = Image.new('RGB', (width, height), color='blue')
        imagen_limite.save(archivo_en_memoria, format='PNG')
        archivo_en_memoria.seek(0)

        imagen_payload = SimpleUploadedFile(
            "separador_largo.png", 
            archivo_en_memoria.read(), 
            content_type="image/png"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_payload

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(es_valido, msg=f"Error en validación: {serializer.errors}")



    def test_comunicado_imagen_no_procesable_por_pillow_falla(self):
        """
        Test: Rechazo de archivos con contenido binario no identificable.

        Given: Un archivo 'foto.jpg' que contiene datos aleatorios 
            que Pillow no puede identificar como imagen.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: Image.open() lanzará un UnidentifiedImageError, el bloque 
            except lo capturará y el serializador devolverá un error.
        """
        contenido_basura = os.urandom(1024) 
        imagen_falsa = SimpleUploadedFile(
            "intento_hack.jpg", 
            contenido_basura, 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_falsa

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó basura binaria como JPG.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo subido no es una imagen válida o está dañado."
        )



    def test_comunicado_imagen_metadata_danada_falla(self):
        """
        Test: Protección contra archivos con metadatos o segmentos corruptos.

        Given: Un archivo que tiene la firma inicial de un PNG (\x89PNG...)
            pero cuyos datos posteriores son inconsistentes.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: Pillow detectará la inconsistencia estructural y el serializador
            devolverá el error de archivo dañado.
        """
        cabecera_png = b"\x89PNG\r\n\x1a\n"
        datos_corruptos = cabecera_png + b"\x00\x00\x00\x0D IHDR" + os.urandom(50)
        
        imagen_malformada = SimpleUploadedFile(
            "foto_corrupta.png", 
            datos_corruptos, 
            content_type="image/png"
        )
        
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_malformada

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó una imagen con metadata dañada.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo subido no es una imagen válida o está dañado."
        )



    def test_comunicado_areas_interes_vacia_falla(self):
        """
        Test: Obligatoriedad de áreas de interés.

        Given: Un payload con título e imagen válidos, pero con 
            'areas_interes' como una lista vacía [].
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid es False) y devolver
            el mensaje indicando que debe seleccionar al menos una.
        """
        payload = self.valid_payload.copy()
        payload['areas_interes'] = []

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador permitió un comunicado sin áreas de interés.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])
        self.assertEqual(
            mensaje_error, 
            "Debe seleccionar al menos un área de interés. Si es para todos, elija 'Todos los Hermanos'."
        )



    def test_comunicado_areas_interes_no_enviado_falla(self):
        """
        Test: Campo obligatorio no presente en el payload.

        Given: Un payload que contiene título, contenido e imagen, 
            pero al que le falta la clave 'areas_interes'.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar indicando que el campo es requerido.
        """
        payload = self.valid_payload.copy()
        if 'areas_interes' in payload:
            del payload['areas_interes']

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un payload sin el campo areas_interes.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])
        self.assertEqual(mensaje_error, "This field is required.")



    def test_comunicado_areas_interes_null_falla(self):
        """
        Test: Rechazo de valor nulo en campo obligatorio.

        Given: Un payload donde 'areas_interes' se envía como null.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar indicando que el valor no puede ser nulo.
        """
        payload = self.valid_payload.copy()
        payload['areas_interes'] = None

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó null en areas_interes.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])
        self.assertEqual(mensaje_error, "This field may not be null.")



    def test_comunicado_areas_interes_id_inexistente_falla(self):
        """
        Test: Validación de integridad referencial.

        Given: Un payload con un ID de 'areas_interes' que no existe en la base de datos.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar porque el PrimaryKeyRelatedField 
            no puede resolver el ID a una instancia del modelo.
        """
        payload = self.valid_payload.copy()
        id_inexistente = 9999
        payload['areas_interes'] = [id_inexistente]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un ID de área inexistente.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])

        self.assertIn("does not exist", mensaje_error)
        self.assertIn(str(id_inexistente), mensaje_error)



    def test_comunicado_areas_interes_mezcla_ids_falla(self):
        """
        Test: Rechazo de lista con IDs válidos e inválidos.

        Given: Un payload con 'areas_interes' que contiene un ID real y uno ficticio.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar completamente, rechazando la petición
            por el ID que no existe, sin aceptar parcialmente el válido.
        """
        payload = self.valid_payload.copy()
        id_valido = payload['areas_interes'][0] 
        id_inexistente = 9999

        payload['areas_interes'] = [id_valido, id_inexistente]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó una mezcla de IDs válidos e inválidos.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])
        
        self.assertIn("does not exist", mensaje_error)
        self.assertIn(str(id_inexistente), mensaje_error)



    def test_comunicado_areas_interes_lista_strings_falla(self):
        """
        Test: Rechazo de tipos de datos incorrectos.

        Given: Un payload con 'areas_interes' que contiene strings alfabéticos.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar indicando que se esperaba un 
            valor de clave primaria (pk) pero se recibió un string.
        """
        payload = self.valid_payload.copy()
        payload['areas_interes'] = ['juventud', 'banda']

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó strings en lugar de IDs numéricos.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])

        self.assertIn("Incorrect type", mensaje_error)
        self.assertIn("received str", mensaje_error)



    def test_comunicado_areas_interes_objetos_json_falla(self):
        """
        Test: Rechazo de objetos completos cuando se esperan IDs.

        Given: Un payload con 'areas_interes' conteniendo diccionarios 
            en lugar de números enteros.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar con un error de tipo (Incorrect type).
        """
        payload = self.valid_payload.copy()
        payload['areas_interes'] = [
            {"id": 1, "nombre": "Juventud"},
            {"id": 2, "nombre": "Costaleros"}
        ]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó objetos JSON en lugar de IDs.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])

        self.assertIn("Incorrect type", mensaje_error)
        self.assertIn("received dict", mensaje_error)



    def test_comunicado_areas_interes_numero_simple_falla(self):
        """
        Test: Rechazo de valor atómico cuando se espera una lista.

        Given: Un payload donde 'areas_interes' es un entero (1) 
            en lugar de una lista de enteros ([1]).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar indicando que se esperaba 
            una lista de ítems.
        """
        payload = self.valid_payload.copy()
        id_valido = payload['areas_interes'][0]
        payload['areas_interes'] = id_valido 

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un entero simple en lugar de una lista.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])

        self.assertIn("Expected a list of items", mensaje_error)



    def test_comunicado_titulo_valido_pero_contenido_malicioso_falla(self):
        """
        Test: Validación parcial de campos de texto.

        Given: Un payload con un título perfectamente válido ("Solemne Traslado")
            pero un contenido que incluye etiquetas <script> prohibidas.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe ser inválido (is_valid == False), 
            marcando el error específicamente en el campo 'contenido'.
        """
        payload = self.valid_payload.copy()
        payload['titulo'] = "Solemne Traslado de la Imagen"
        payload['contenido'] = "<script>alert('XSS')</script> Contenido malicioso."

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó contenido malicioso a pesar de tener un título válido.")

        self.assertNotIn('titulo', serializer.errors)
        self.assertIn('contenido', serializer.errors)
        
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_valido_pero_imagen_pesada_falla(self):
        """
        Test: Validación de archivos con metadatos de texto correctos.

        Given: Un payload con título, contenido y áreas válidos, 
            pero una imagen de 6MB (supera el límite de 5MB).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid == False), 
            señalando el error específicamente en 'imagen_portada'.
        """
        seis_megas_de_basura = b'0' * (6 * 1024 * 1024)
        imagen_pesada = SimpleUploadedFile(
            "procesion_pesada.jpg", 
            seis_megas_de_basura, 
            content_type="image/jpeg"
        )
        
        payload = self.valid_payload.copy()
        payload['titulo'] = "Solemne Quinario a Nuestro Padre Jesús"
        payload['contenido'] = "<p>Horarios de los cultos para la próxima semana.</p>"
        payload['imagen_portada'] = imagen_pesada

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó una imagen de 6MB.")

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn("La imagen es demasiado grande", mensaje_error)
        self.assertIn("5MB", mensaje_error)



    def test_comunicado_datos_validos_pero_areas_vacia_falla(self):
        """
        Test: Validación de integridad de negocio con datos de medios correctos.

        Given: Un payload con título, contenido e imagen perfectamente válidos,
            pero con 'areas_interes' como una lista vacía [].
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar (is_valid == False), indicando que
            es obligatorio seleccionar al menos un área.
        """
        img_file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(img_file, 'JPEG')
        img_file.seek(0)
        imagen_valida = SimpleUploadedFile("portada.jpg", img_file.read(), content_type="image/jpeg")

        payload = self.valid_payload.copy()
        payload['titulo'] = "Solemne Besamanos de la Virgen"
        payload['contenido'] = "<p>Invitamos a todos los hermanos.</p>"
        payload['imagen_portada'] = imagen_valida
        payload['areas_interes'] = []

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un comunicado sin áreas de interés.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])
        self.assertEqual(
            mensaje_error, 
            "Debe seleccionar al menos un área de interés. Si es para todos, elija 'Todos los Hermanos'."
        )



    def test_comunicado_campo_extra_e_imagen_invalida_falla_por_esquema(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow.
        """
        imagen_falsa = SimpleUploadedFile(
            "fake.jpg", 
            b"esto es texto, no binario de imagen", 
            content_type="image/jpeg"
        )
        payload = self.valid_payload.copy()
        payload['imagen_portada'] = imagen_falsa
        payload['hacker_field'] = "intento_de_inyeccion"

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)

        self.assertIn('error', serializer.errors) 

        error_msg = str(serializer.errors['error'])
        self.assertIn("Campos no permitidos detectados: hacker_field", error_msg)

        self.assertNotIn('imagen_portada', serializer.errors)



    def test_comunicado_payload_correcto_pero_imagen_corrupta_falla(self):
        """
        Test: Combinación de texto/relaciones válidas con imagen binariamente corrupta.

        Given: Un payload perfecto en textos y áreas de interés, pero cuya
            imagen de portada contiene bytes aleatorios ilegibles para Pillow.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar ÚNICAMENTE en el campo 'imagen_portada',
            respetando la validez del resto de los datos.
        """
        basura_binaria = b"\x00\xFF\x00\xFF" * 1024
        imagen_corrupta = SimpleUploadedFile(
            "cartel_corrupto.jpg", 
            basura_binaria, 
            content_type="image/jpeg"
        )

        payload = self.valid_payload.copy()
        payload['titulo'] = "Cultos Mensuales de Reglas"
        payload['contenido'] = "<p>Asistencia con medalla.</p>"
        payload['imagen_portada'] = imagen_corrupta

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó una imagen corrupta junto a datos válidos.")

        self.assertNotIn('titulo', serializer.errors)
        self.assertNotIn('contenido', serializer.errors)
        self.assertNotIn('areas_interes', serializer.errors)

        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertEqual(
            mensaje_error, 
            "El archivo subido no es una imagen válida o está dañado."
        )



    def test_comunicado_datos_correctos_pero_id_inexistente_falla(self):
        """
        Test: Validación de integridad referencial con el resto del payload válido.

        Given: Un payload con título, contenido e imagen válidos, pero 
            un ID en 'areas_interes' que no existe en la BD (999).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe ser inválido, señalando que el objeto no existe.
        """
        img_file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(img_file, 'JPEG')
        img_file.seek(0)
        imagen_valida = SimpleUploadedFile("test.jpg", img_file.read(), content_type="image/jpeg")

        payload = self.valid_payload.copy()
        payload['titulo'] = "Título perfectamente válido"
        payload['contenido'] = "<p>Contenido limpio y seguro.</p>"
        payload['imagen_portada'] = imagen_valida

        id_fantasma = 999
        payload['areas_interes'] = [id_fantasma]

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un ID que no existe en la base de datos.")

        self.assertIn('areas_interes', serializer.errors)
        mensaje_error = str(serializer.errors['areas_interes'][0])

        self.assertIn("does not exist", mensaje_error)
        self.assertIn(str(id_fantasma), mensaje_error)



    def test_comunicado_contenido_bypass_mayusculas_falla(self):
        """
        Test: Intento de saltarse el filtro de seguridad usando mayúsculas.

        Given: Un contenido que incluye la etiqueta <SCRIPT> en mayúsculas
            para intentar evadir un filtro que solo busque minúsculas.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe detectar la etiqueta gracias al uso de .lower()
            y lanzar el ValidationError de seguridad.
        """
        payload = self.valid_payload.copy()
        payload['contenido'] = "<SCRIPT>alert('Hackeo')</SCRIPT> Texto normal."

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El filtro de seguridad fue evadido por el uso de mayúsculas.")
        
        self.assertIn('contenido', serializer.errors)
        mensaje_error = str(serializer.errors['contenido'][0])
        self.assertEqual(
            mensaje_error, 
            "El contenido no contiene texto o formato válido tras la limpieza de seguridad."
        )



    def test_comunicado_contenido_encoding_html_saneado(self):
        """
        Test: Verificación de que las entidades HTML no ejecutan script.

        Given: Un contenido que intenta colar un script usando entidades 
            como &lt;script&gt;.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe o bien rechazarlo si detecta el patrón,
            o bien sanearlo transformándolo en texto inofensivo que 
            no se ejecutará en el navegador.
        """
        payload = self.valid_payload.copy()
        payload['contenido'] = "&lt;script&gt;alert('XSS')&lt;/script&gt;"

        serializer = ComunicadoFormSerializer(data=payload)

        es_valido = serializer.is_valid()

        if not es_valido:
            self.assertIn('contenido', serializer.errors)
        else:
            contenido_limpio = serializer.validated_data['contenido']
            self.assertNotIn("<script>", contenido_limpio)
            self.assertIn("&lt;script&gt;", contenido_limpio)



    def test_comunicado_titulo_sql_injection_es_tratado_como_texto(self):
        """
        Test: Resistencia a inyección SQL.

        Given: Un título que contiene comandos SQL maliciosos 
            ("'; DROP TABLE api_comunicado; --").
        When: Se procesa por el ComunicadoFormSerializer e is_valid().
        Then: El serializador debe aceptar el texto (porque no es XSS), 
            pero tratarlo como un simple string de texto, demostrando
            que el ORM parametrizará el valor sin ejecutar el SQL.
        """
        payload = self.valid_payload.copy()
        sql_malicioso = "Título'; DROP TABLE api_comunicado; --"
        payload['titulo'] = sql_malicioso

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertTrue(es_valido, msg="El serializador debería aceptar el texto; el ORM se encargará de la seguridad.")

        self.assertEqual(serializer.validated_data['titulo'], sql_malicioso)



    def test_comunicado_titulo_json_anidado_falla(self):
        """
        Test: Robustez ante tipos de datos estructurados inesperados.

        Given: Un payload donde el campo 'titulo' no es un string, 
            sino un objeto JSON anidado.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe fallar con un error de tipo (Incorrect type)
            antes de que los métodos de validación personalizados 
            intenten procesarlo.
        """
        payload = self.valid_payload.copy()
        payload['titulo'] = {"intento": "inyectar_objeto"}

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El serializador aceptó un objeto donde esperaba un string.")

        self.assertIn('titulo', serializer.errors)
        mensaje_error = str(serializer.errors['titulo'][0])

        self.assertIn("Not a valid string", mensaje_error)



    def test_comunicado_archivo_extremo_falla_por_limite_peso(self):
        """
        Test: Protección contra agotamiento de memoria/almacenamiento.

        Given: Un payload con un archivo de 100MB (muy por encima de los 5MB).
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe rechazarlo inmediatamente en validate_imagen_portada
            comprobando solo el atributo .size, sin intentar abrirlo con Pillow.
        """

        cien_megas = 100 * 1024 * 1024
        archivo_gigante = SimpleUploadedFile(
            "video_disfrazado.jpg", 
            b"0",
            content_type="image/jpeg"
        )

        archivo_gigante.size = cien_megas 

        payload = self.valid_payload.copy()
        payload['imagen_portada'] = archivo_gigante

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido, msg="El sistema permitió un archivo de 100MB.")
        
        self.assertIn('imagen_portada', serializer.errors)
        mensaje_error = str(serializer.errors['imagen_portada'][0])
        self.assertIn("La imagen es demasiado grande", mensaje_error)



    def test_comunicado_inundacion_campos_repetidos_falla(self):
        """
        Test: Protección contra DoS por inundación de claves en JSON.

        Given: Un payload malformado con 1,000 repeticiones de la misma clave
            para intentar agotar el tiempo de CPU del parser.
        When: Se procesa por el ComunicadoFormSerializer.
        Then: El serializador debe rechazar la estructura por campos no 
            permitidos (gracias a to_internal_value) o el parser de DRF 
            debe manejarlo eficientemente sin colapsar.
        """
        payload = self.valid_payload.copy()
        for i in range(1000):
            payload[f'campo_basura_{i}'] = "dato_inutil"

        serializer = ComunicadoFormSerializer(data=payload)
        es_valido = serializer.is_valid()

        self.assertFalse(es_valido)
        self.assertIn('error', serializer.errors)
        
        error_msg = str(serializer.errors['error'])
        self.assertIn("Campos no permitidos detectados", error_msg)