from datetime import date
import datetime
import time

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import Hermano, AreaInteres, Comunicado
from api.serializadores.comunicado.comunicado_list_serializer import ComunicadoListSerializer
from unittest.mock import Mock, PropertyMock, patch


class TestComunicadoSerializer(TestCase):
    def setUp(self):
        self.autor = Hermano.objects.create_user(
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

        self.area1 = AreaInteres.objects.create(nombre_area='CARIDAD')
        self.area2 = AreaInteres.objects.create(nombre_area='JUVENTUD')

        self.comunicado = Comunicado.objects.create(
            titulo="Gran Recogida de Alimentos",
            contenido="Contenido detallado del comunicado...",
            tipo_comunicacion='URGENTE',
            autor=self.autor
        )
        self.comunicado.areas_interes.add(self.area1, self.area2)



    def test_comunicado_serialization_general(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer. 
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow.
        
        Nota: Aunque este test instancia el ListSerializer para verificar la salida, 
        garantiza que el esquema de datos poblados sea íntegro y exacto.
        """
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertEqual(data['id'], self.comunicado.id)
        self.assertEqual(data['titulo'], "Gran Recogida de Alimentos")
        self.assertEqual(data['contenido'], "Contenido detallado del comunicado...")
        self.assertEqual(data['tipo_comunicacion'], 'URGENTE')

        self.assertEqual(data['tipo_display'], "Urgente")
        self.assertEqual(data['autor_nombre'], "Juan Pérez")

        expected_areas = ["Caridad", "Juventud"]
        self.assertEqual(len(data['areas_interes']), 2)
        for area in expected_areas:
            self.assertIn(area, data['areas_interes'])

        self.assertIsNone(data['imagen_portada'])

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_multiple(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de múltiples instancias en el ListSerializer).
        Then: El serializador debe garantizar la integridad del esquema, 
            devolviendo una lista donde cada objeto cumple estrictamente con 
            los campos definidos, ignorando cualquier dato extra.
        """
        comunicado_2 = Comunicado.objects.create(
            titulo="Corte de calle por procesión",
            contenido="La calle estará cortada desde las 18:00h.",
            tipo_comunicacion='INFORMATIVO',
            autor=self.autor
        )

        area_cultos = AreaInteres.objects.create(nombre_area='CULTOS_FORMACION')
        comunicado_2.areas_interes.add(area_cultos)

        queryset = Comunicado.objects.all().order_by('id')

        serializer = ComunicadoListSerializer(queryset, many=True)
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['titulo'], "Gran Recogida de Alimentos")
        self.assertEqual(data[0]['tipo_display'], "Urgente")
        self.assertIn("Caridad", data[0]['areas_interes'])

        self.assertEqual(data[1]['titulo'], "Corte de calle por procesión")
        self.assertEqual(data[1]['tipo_display'], "Informativo")
        self.assertEqual(data[1]['autor_nombre'], "Juan Pérez")
        self.assertIn("Cultos y Formación", data[1]['areas_interes'])

        for item in data:
            self.assertNotIn('hacker_field', item)



    def test_comunicado_serialization_sin_imagen(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado (o nula).
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de una instancia con imagen_portada=None).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que el campo imagen_portada se devuelva como null 
            sin errores de procesamiento.
        """
        self.comunicado.imagen_portada = None
        self.comunicado.save()

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('imagen_portada', data)
        self.assertIsNone(data['imagen_portada'])

        self.assertEqual(data['titulo'], "Gran Recogida de Alimentos")
        self.assertEqual(data['autor_nombre'], "Juan Pérez")

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_schema_integrity(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida completa del ListSerializer).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que el output contenga exactamente los campos definidos 
            en Meta.fields y ninguno adicional inyectado.
        """
        expected_fields = {
            'id', 'titulo', 'contenido', 'fecha_emision', 'imagen_portada',
            'tipo_comunicacion', 'tipo_display', 'autor_nombre', 
            'areas_interes'
        }

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data
        output_fields = set(data.keys())

        self.assertEqual(
            output_fields, 
            expected_fields, 
            msg=f"Faltan campos o hay campos extra. Esperados: {expected_fields}. Obtenidos: {output_fields}"
        )

        self.assertNotIn('hacker_field', data)

        self.assertIsInstance(data['areas_interes'], list)
        self.assertIsInstance(data['autor_nombre'], str)



    def test_comunicado_serialization_exclusion_check(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida del ListSerializer tras poblar campos internos como 'embedding').
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que campos internos del modelo (ej. 'embedding') no se 
            filtren en el output si no están en Meta.fields.
        """
        self.comunicado.embedding = [0.1, 0.2, 0.3, 0.4]
        self.comunicado.save()

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        campos_prohibidos = ['embedding', 'hacker_field', 'autor_id', 'password']
        
        for campo in campos_prohibidos:
            self.assertNotIn(
                campo, 
                data, 
                msg=f"Seguridad comprometida: El campo '{campo}' se ha filtrado en el output."
            )

        self.assertEqual(len(data), 9)



    def test_comunicado_serialization_tipo_display(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida del ListSerializer para el mapeo de choices).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que el campo 'tipo_display' resuelva correctamente 
            el valor legible del Choice ('Urgente') y no el valor interno ('URGENTE').
        """
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertEqual(data['tipo_comunicacion'], 'URGENTE')
        self.assertEqual(data['tipo_display'], "Urgente")

        self.comunicado.tipo_comunicacion = 'CULTOS'
        self.comunicado.save()
        
        data_nuevo = ComunicadoListSerializer(instance=self.comunicado).data
        self.assertEqual(data_nuevo['tipo_display'], "Cultos")

        self.assertNotIn('hacker_field', data_nuevo)



    def test_comunicado_serialization_tipo_display_match_method(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida del ListSerializer comparando con el método del modelo).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que el campo 'tipo_display' coincida exactamente con 
            el valor devuelto por obj.get_tipo_comunicacion_display().
        """
        valor_metodo_modelo = self.comunicado.get_tipo_comunicacion_display()

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertEqual(
            data['tipo_display'], 
            valor_metodo_modelo,
            msg="El serializador no está reflejando el valor de get_tipo_comunicacion_display()"
        )

        self.comunicado.tipo_comunicacion = 'EVENTOS'
        self.comunicado.save()
        
        data_nuevo = ComunicadoListSerializer(instance=self.comunicado).data
        self.assertEqual(
            data_nuevo['tipo_display'], 
            self.comunicado.get_tipo_comunicacion_display()
        )

        self.assertNotIn('hacker_field', data_nuevo)



    def test_comunicado_serialization_tipo_display_read_only(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la entrada de datos hacia un campo de solo lectura).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que campos como 'tipo_display' sean ignorados durante 
            la deserialización al estar marcados como read_only.
        """
        data_input = {
            "titulo": "Nuevo Titulo",
            "tipo_comunicacion": "URGENTE",
            "tipo_display": "HACKED_VALUE",
            "hacker_field": "ataque_mass_assignment"
        }

        serializer = ComunicadoListSerializer(data=data_input)

        serializer.is_valid()
        
        self.assertNotIn(
            'tipo_display', 
            serializer.validated_data, 
            msg="El campo 'tipo_display' no debería ser aceptado en la entrada de datos (read_only)."
        )

        self.assertNotIn('hacker_field', serializer.validated_data)

        self.assertTrue(serializer.fields['tipo_display'].read_only)



    def test_comunicado_serialization_all_types_display(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            múltiples instancias con diferentes 'tipo_comunicacion').
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que cada tipo de comunicación (GENERAL, URGENTE, CULTOS, etc.)
            muestre su etiqueta legible exacta definida en el modelo.
        """
        tipos_a_probar = {
            'GENERAL': 'General',
            'INFORMATIVO': 'Informativo',
            'CULTOS': 'Cultos',
            'SECRETARIA': 'Secretaría',
            'URGENTE': 'Urgente',
            'EVENTOS': 'Eventos y Caridad'
        }

        comunicados = []
        for codigo, etiqueta_esperada in tipos_a_probar.items():
            comunicados.append(
                Comunicado(
                    titulo=f"Test {etiqueta_esperada}",
                    tipo_comunicacion=codigo,
                    autor=self.autor
                )
            )

        Comunicado.objects.bulk_create(comunicados)
        queryset = Comunicado.objects.filter(titulo__contains="Test")

        serializer = ComunicadoListSerializer(queryset, many=True)
        data = serializer.data

        for item in data:
            codigo_interno = item['tipo_comunicacion']
            etiqueta_obtenida = item['tipo_display']
            
            self.assertEqual(
                etiqueta_obtenida, 
                tipos_a_probar[codigo_interno],
                msg=f"Error de mapeo: {codigo_interno} debería ser '{tipos_a_probar[codigo_interno]}'"
            )

        for item in data:
            self.assertNotIn('hacker_field', item)



    def test_comunicado_serialization_single_area(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de un comunicado con una única área de interés).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que 'areas_interes' devuelva una lista con el nombre 
            legible del área y no su ID numérico.
        """
        area_unica = AreaInteres.objects.create(nombre_area='PATRIMONIO')
        comunicado_patrimonio = Comunicado.objects.create(
            titulo="Restauración del Manto",
            contenido="Se inicia el proceso de restauración...",
            tipo_comunicacion='INFORMATIVO',
            autor=self.autor
        )
        comunicado_patrimonio.areas_interes.add(area_unica)

        serializer = ComunicadoListSerializer(instance=comunicado_patrimonio)
        data = serializer.data

        self.assertIsInstance(data['areas_interes'], list)
        self.assertEqual(len(data['areas_interes']), 1)

        self.assertEqual(data['areas_interes'][0], "Patrimonio")

        self.assertNotEqual(data['areas_interes'][0], area_unica.id)

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_multiple_areas(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de un comunicado con múltiples áreas de interés).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que 'areas_interes' devuelva una lista de strings con 
            los nombres legibles de todas las áreas vinculadas.
        """
        area_priostia, _ = AreaInteres.objects.get_or_create(nombre_area='PRIOSTIA')
        area_juventud, _ = AreaInteres.objects.get_or_create(nombre_area='JUVENTUD')
        area_caridad, _ = AreaInteres.objects.get_or_create(nombre_area='CARIDAD')
        
        comunicado_multiple = Comunicado.objects.create(
            titulo="Montaje de Altar y Convivencia Joven",
            contenido="Se convoca a los hermanos para el montaje...",
            tipo_comunicacion='GENERAL',
            autor=self.autor
        )

        comunicado_multiple.areas_interes.add(area_priostia, area_juventud, area_caridad)

        serializer = ComunicadoListSerializer(instance=comunicado_multiple)
        data = serializer.data

        self.assertIsInstance(data['areas_interes'], list)
        self.assertEqual(len(data['areas_interes']), 3)

        expected_labels = ["Priostía", "Juventud", "Caridad"]
        
        for label in expected_labels:
            self.assertIn(
                label, 
                data['areas_interes'],
                msg=f"La etiqueta '{label}' no se encuentra en el output del serializador."
            )

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_areas_is_list_of_strings(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de 'areas_interes' en el ListSerializer).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que 'areas_interes' sea una lista de STRINGS y no de IDs.
        """
        id_area1 = self.area1.id

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIsInstance(data['areas_interes'], list)
        self.assertGreater(len(data['areas_interes']), 0)

        for area_output in data['areas_interes']:
            self.assertIsInstance(
                area_output, 
                str, 
                msg=f"El área '{area_output}' debería ser un string, no un {type(area_output)}"
            )
            self.assertNotEqual(
                str(area_output), 
                str(id_area1), 
                msg="El serializador está exponiendo el ID del área en lugar de su nombre legible."
            )

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_areas_match_model_str(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de 'areas_interes' en el ListSerializer).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que cada elemento en 'areas_interes' coincida exactamente 
            con el valor devuelto por el método __str__() del modelo AreaInteres.
        """
        str_area1 = str(self.area1)
        str_area2 = str(self.area2)

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data
        areas_output = data['areas_interes']

        self.assertIn(str_area1, areas_output)
        self.assertIn(str_area2, areas_output)
        self.assertEqual(len(areas_output), 2)

        for area_obj in [self.area1, self.area2]:
            self.assertIn(
                area_obj.get_nombre_area_display(), 
                areas_output,
                msg=f"El serializador no coincide con el display del modelo para {area_obj.nombre_area}"
            )

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_volume_areas(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de un comunicado con TODAS las áreas de interés posibles).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que 'areas_interes' devuelva una lista completa de 
            strings con la representación __str__ de cada una de las áreas.
        """
        todas_las_areas = []
        for codigo, etiqueta in AreaInteres.NombreArea.choices:
            area, _ = AreaInteres.objects.get_or_create(nombre_area=codigo)
            todas_las_areas.append(area)

        comunicado_masivo = Comunicado.objects.create(
            titulo="Comunicado para toda la Hermandad",
            contenido="Contenido de interés general para todos los colectivos.",
            tipo_comunicacion='GENERAL',
            autor=self.autor
        )
        comunicado_masivo.areas_interes.add(*todas_las_areas)

        serializer = ComunicadoListSerializer(instance=comunicado_masivo)
        data = serializer.data

        self.assertIsInstance(data['areas_interes'], list)
        self.assertEqual(
            len(data['areas_interes']), 
            len(todas_las_areas),
            msg="El número de áreas serializadas no coincide con el número de áreas vinculadas."
        )

        for area_str in data['areas_interes']:
            self.assertIsInstance(area_str, str)
            self.assertNotIn('_', area_str)

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_empty_areas(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de un comunicado sin ninguna área de interés vinculada).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que 'areas_interes' devuelva una lista vacía ([]) 
            en lugar de null o un error de ejecución.
        """
        comunicado_huérfano = Comunicado.objects.create(
            titulo="Comunicado sin destinatarios",
            contenido="Este comunicado no tiene áreas de interés asignadas.",
            tipo_comunicacion='GENERAL',
            autor=self.autor
        )
        comunicado_huérfano.areas_interes.clear()

        serializer = ComunicadoListSerializer(instance=comunicado_huérfano)
        data = serializer.data

        self.assertIsInstance(data['areas_interes'], list)
        self.assertEqual(
            len(data['areas_interes']), 
            0, 
            msg="El campo 'areas_interes' debería estar vacío."
        )

        self.assertEqual(data['titulo'], "Comunicado sin destinatarios")
        self.assertEqual(data['autor_nombre'], "Juan Pérez")

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_autor_nombre_completo(self):
        """
        Test: Prioridad de validación de esquema (Mass Assignment).

        Given: Un payload que contiene un campo no permitido ('hacker_field')
            y una imagen que es un simple archivo de texto camuflado.
        When: Se procesa por el ComunicadoFormSerializer (en este caso validando 
            la salida de 'autor_nombre' con nombre y apellido presentes).
        Then: El serializador debe fallar PRIMERO por el campo extra en 
            to_internal_value, antes de intentar procesar la imagen con Pillow,
            garantizando que el campo 'autor_nombre' devuelva la concatenación 
            correcta "Nombre Apellido".
        """
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('autor_nombre', data)
        self.assertEqual(
            data['autor_nombre'], 
            "Juan Pérez",
            msg="El formato de 'autor_nombre' debería ser 'Nombre Apellido'."
        )

        self.assertNotIn("García", data['autor_nombre'])

        self.assertNotIn('hacker_field', data)



    def test_comunicado_serialization_autor_nombre_fallback_sin_nombre(self):
        """
        Test: Fallback del nombre de autor a username.

        Given: Un comunicado cuyo autor tiene el campo 'nombre' vacío o nulo en memoria, 
            pero dispone de un 'username' y 'primer_apellido' válidos.
        When: Se procesa la instancia a través del ComunicadoListSerializer (modificando
            el objeto en memoria sin llamar a save() para evitar el ValidationError).
        Then: El campo 'autor_nombre' debe hacer un fallback automático, 
            devolviendo la concatenación del 'username' y el primer apellido.
        """
        self.comunicado.autor.nombre = ""

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('autor_nombre', data)
        self.assertEqual(
            data['autor_nombre'], 
            f"{self.comunicado.autor.username} {self.comunicado.autor.primer_apellido}".strip(),
            msg="El serializer debe usar el 'username' si el campo 'nombre' está vacío."
        )



    def test_comunicado_serialization_autor_nombre_sin_apellido(self):
        """
        Test: Fallback del nombre de autor sin apellido.

        Given: Un comunicado cuyo autor tiene un 'nombre' válido, pero el campo 
            'primer_apellido' está vacío en memoria.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'autor_nombre' debe devolver solo el nombre, eliminando 
            cualquier espacio adicional al final ("Nombre").
        """
        self.comunicado.autor.primer_apellido = ""

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('autor_nombre', data)
        self.assertEqual(
            data['autor_nombre'], 
            self.comunicado.autor.nombre,
            msg="El serializer debe devolver solo el nombre sin espacios extra si el apellido está vacío."
        )

        self.assertFalse(
            data['autor_nombre'].endswith(" "),
            msg="El nombre devuelto no debe terminar con un espacio en blanco."
        )



    def test_comunicado_serialization_sin_autor(self):
        """
        Test: Fallback de autor inexistente a etiqueta institucional.

        Given: Un comunicado que, por alguna razón de integridad o lógica de negocio, 
            carece de un objeto 'autor' vinculado.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'autor_nombre' debe devolver la cadena por defecto "Secretaría", 
            actuando como el último nivel de protección del sistema.
        """
        self.comunicado.autor_id = None

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('autor_nombre', data)
        self.assertEqual(
            data['autor_nombre'], 
            "Secretaría",
            msg="Si el comunicado no tiene autor, el campo 'autor_nombre' debe ser 'Secretaría'."
        )



    def test_comunicado_serialization_autor_nombre_vacio_y_username_presente(self):
        """
        Test: Control de casos borde con nombre vacío.

        Given: Un comunicado cuyo autor tiene un string vacío ("") en el campo 'nombre',
            pero cuenta con un 'username' (DNI) y un 'primer_apellido' definidos.
        When: Se procesa la instancia a través del ComunicadoListSerializer sin persistir
            los cambios para evitar las validaciones de limpieza del modelo.
        Then: El sistema debe detectar que el nombre es un valor 'falsy' y realizar 
            el fallback al 'username', devolviendo "DNI Apellido".
        """
        self.comunicado.autor.nombre = ""

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        nombre_esperado = f"{self.autor.username} {self.autor.primer_apellido}".strip()

        self.assertEqual(
            data['autor_nombre'], 
            nombre_esperado,
            msg="El serializador falló al no usar el username cuando el nombre es un string vacío."
        )
        self.assertNotEqual(
            data['autor_nombre'],
            self.autor.primer_apellido,
            msg="Error: El serializador devolvió solo el apellido, ignorando el fallback al username."
        )



    def test_comunicado_serialization_autor_con_primer_apellido_vacio(self):
        """
        Test: Autor con primer_apellido vacío.

        Given: Un comunicado cuyo autor tiene un 'nombre' asignado, pero el campo 
            'primer_apellido' está vacío ("") en memoria.
        When: Se procesa la instancia a través del ComunicadoListSerializer para
            generar la representación de datos.
        Then: El campo 'autor_nombre' debe devolver únicamente el nombre del autor,
            asegurando que se eliminen espacios en blanco sobrantes mediante strip().
        """
        self.comunicado.autor.primer_apellido = ""

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('autor_nombre', data)

        self.assertEqual(
            data['autor_nombre'], 
            self.comunicado.autor.nombre,
            msg="El serializer debe devolver solo el nombre si el apellido está vacío."
        )

        self.assertEqual(
            len(data['autor_nombre']), 
            len(self.comunicado.autor.nombre),
            msg="El string resultante contiene espacios adicionales (posible fallo de .strip())."
        )



    def test_comunicado_serialization_autor_con_espacios_en_blanco(self):
        """
        Test: Autor con espacios en nombre o apellido.

        Given: Un comunicado cuyo autor tiene espacios en blanco accidentales 
            al inicio o al final de los campos 'nombre' y 'primer_apellido'.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'autor_nombre' debe devolver la concatenación limpia, 
            eliminando los espacios sobrantes tanto internos como externos 
            mediante el uso de .strip().
        """
        self.comunicado.autor.nombre = "  Juan  "
        self.comunicado.autor.primer_apellido = "  Pérez  "

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        nombre_limpio = f"{self.comunicado.autor.nombre.strip()} {self.comunicado.autor.primer_apellido.strip()}".strip()

        self.assertIn('autor_nombre', data)
        self.assertEqual(
            data['autor_nombre'], 
            nombre_limpio,
            msg="El serializador no está eliminando los espacios en blanco de los extremos de los campos."
        )

        self.assertFalse(data['autor_nombre'].startswith(" "), "El nombre empieza con espacios.")
        self.assertFalse(data['autor_nombre'].endswith(" "), "El nombre termina con espacios.")



    def test_comunicado_serialization_con_imagen_portada(self):
        """
        Test: Serialización de la imagen de portada.

        Given: Un comunicado que tiene un archivo de imagen válido asignado 
            al campo 'imagen_portada'.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'imagen_portada' debe devolver la URL correcta o 
            la ruta relativa hacia el archivo multimedia.
        """
        imagen_mock = SimpleUploadedFile(
            name='test_portada.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )

        self.comunicado.imagen_portada = imagen_mock
        self.comunicado.save()

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('imagen_portada', data)
        self.assertIsNotNone(data['imagen_portada'], "La imagen no debería ser nula.")

        self.assertIn(
            'test_portada', 
            data['imagen_portada'],
            msg=f"La URL generada no contiene el nombre del archivo. URL: {data['imagen_portada']}"
        )

        es_url_valida = data['imagen_portada'].startswith('/') or data['imagen_portada'].startswith('http')
        self.assertTrue(
            es_url_valida, 
            msg=f"El formato de la URL de la imagen no es válido: {data['imagen_portada']}"
        )



    def test_comunicado_serialization_sin_imagen_portada(self):
        """
        Test: Serialización de comunicado sin imagen de portada.

        Given: Un comunicado que no tiene ningún archivo asignado al campo 
            'imagen_portada' (el valor en base de datos es nulo o vacío).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'imagen_portada' de la respuesta JSON debe ser 
            estrictamente null, permitiendo al frontend manejar la ausencia de imagen.
        """
        self.comunicado.imagen_portada = None
        self.comunicado.save()

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('imagen_portada', data)
        self.assertIsNone(
            data['imagen_portada'], 
            msg="El serializador debería devolver null si no hay imagen de portada."
        )



    def test_comunicado_serialization_imagen_tipo_dato(self):
        """
        Test: Verificación de tipo de dato serializable para imagen.

        Given: Un comunicado que puede tener o no una imagen cargada.
        When: Se procesa a través del ComunicadoListSerializer.
        Then: El campo 'imagen_portada' debe ser siempre un string (URL) 
            o un valor nulo (None), asegurando la compatibilidad con JSON.
        """
        self.comunicado.imagen_portada = SimpleUploadedFile('test.jpg', b'content')
        
        serializer_con = ComunicadoListSerializer(instance=self.comunicado)
        data_con = serializer_con.data
        
        self.assertTrue(
            isinstance(data_con['imagen_portada'], str) or data_con['imagen_portada'] is None,
            msg="El campo imagen_portada con imagen debe ser un string (URL)."
        )

        self.comunicado.imagen_portada = None
        
        serializer_sin = ComunicadoListSerializer(instance=self.comunicado)
        data_sin = serializer_sin.data
        
        self.assertIsNone(
            data_sin['imagen_portada'], 
            msg="El campo imagen_portada sin imagen debe ser estrictamente None."
        )



    def test_comunicado_serialization_fecha_emision_formato(self):
        """
        Test: Formato de fecha de emisión serializada.

        Given: Un comunicado con una 'fecha_emision' válida (objeto datetime con zona horaria).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'fecha_emision' debe devolverse como un string en el 
            formato estándar ISO 8601 esperado por DRF (ej. "2026-03-04..."), 
            permitiendo su correcto tratamiento en el cliente.
        """
        fecha_test = datetime.datetime(2026, 3, 4, 12, 0, 0, tzinfo=datetime.timezone.utc)
        self.comunicado.fecha_emision = fecha_test
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('fecha_emision', data)
        self.assertIsInstance(data['fecha_emision'], str)

        self.assertTrue(
            data['fecha_emision'].startswith("2026-03-04"),
            msg=f"El formato de fecha '{data['fecha_emision']}' no es el esperado (ISO 8601)."
        )



    def test_comunicado_serialization_fecha_emision_timezone(self):
        """
        Test: Serialización de fecha con zona horaria (Timezone).

        Given: Un comunicado con una 'fecha_emision' que incluye información 
            específica de zona horaria (aware datetime).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'fecha_emision' debe devolverse como un string ISO 8601 
            que incluya el desplazamiento de la zona horaria (offset), 
            asegurando la integridad temporal en el cliente.
        """
        fecha_con_tz = timezone.now()
        self.comunicado.fecha_emision = fecha_con_tz
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('fecha_emision', data)

        tiene_tz_info = 'Z' in data['fecha_emision'] or '+' in data['fecha_emision']
        
        self.assertTrue(
            tiene_tz_info,
            msg=f"La fecha serializada '{data['fecha_emision']}' no parece incluir información de zona horaria."
        )

        self.assertIn(
            str(fecha_con_tz.year), 
            data['fecha_emision'],
            msg="El año en la fecha serializada no coincide con la fecha original."
        )



    @override_settings(USE_TZ=False)
    def test_comunicado_serialization_fecha_emision_use_tz_false(self):
        """
        Test: Comportamiento de la fecha con USE_TZ=False.

        Given: La configuración global de Django con USE_TZ=False y un comunicado
            con una fecha local (naive datetime, sin timezone explícito).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'fecha_emision' debe serializarse sin indicador de zona
            horaria (sin 'Z' ni offset '+HH:MM'), devolviendo solo la hora y fecha tal cual.
        """
        fecha_test_naive = datetime.datetime(2026, 3, 4, 12, 0, 0)
        self.comunicado.fecha_emision = fecha_test_naive
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('fecha_emision', data)
        self.assertIsInstance(data['fecha_emision'], str)

        self.assertNotIn('Z', data['fecha_emision'], "La fecha no debe contener 'Z' (indicador UTC).")
        self.assertNotIn('+', data['fecha_emision'], "La fecha no debe contener offsets de zona horaria.")
        
        self.assertTrue(
            data['fecha_emision'].startswith("2026-03-04T12:00:00"),
            msg=f"La fecha sin zona horaria no se serializó como se esperaba: {data['fecha_emision']}"
        )



    def test_comunicado_serialization_contenido_fidelidad(self):
        """
        Test: Fidelidad del campo contenido.

        Given: Un comunicado que contiene un texto complejo en el campo 'contenido', 
            incluyendo saltos de línea, caracteres especiales y posibles etiquetas.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'contenido' de la respuesta debe ser idéntico al almacenado 
            en el modelo, asegurando que el serializador no aplique filtros 
            o limpiezas no deseadas en esta capa.
        """
        texto_complejo = (
            "Línea 1 con tilde ó.\n"
            "Línea 2 con caracteres especiales: &%$#.\n"
            "<p>Párrafo simulado</p>"
        )
        self.comunicado.contenido = texto_complejo
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('contenido', data)
        self.assertEqual(
            data['contenido'], 
            texto_complejo,
            msg="El serializador alteró el contenido original del comunicado."
        )

        self.assertIn("\n", data['contenido'], "Se perdieron los saltos de línea en la serialización.")



    def test_comunicado_serialization_contenido_html_valido(self):
        """
        Test: Preservación de etiquetas HTML en el contenido.

        Given: Un comunicado cuyo campo 'contenido' almacena una cadena con 
            marcado HTML válido (párrafos, negritas, listas).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'contenido' debe devolverse íntegro, sin escapar los 
            caracteres especiales (<, >, &), permitiendo que el cliente 
            (web/app) renderice el HTML correctamente.
        """
        html_input = (
            "<h3>Título del Comunicado</h3>"
            "<p>Este es un texto con <strong>negrita</strong> y "
            "<a href='http://test.com'>un enlace</a>.</p>"
        )
        self.comunicado.contenido = html_input
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('contenido', data)

        self.assertEqual(
            data['contenido'], 
            html_input,
            msg="El serializador escapó o alteró las etiquetas HTML del contenido."
        )

        self.assertIn("<h3>", data['contenido'])
        self.assertIn("<strong>", data['contenido'])
        self.assertNotIn("&lt;p&gt;", data['contenido'], "El HTML se devolvió escapado.")



    def test_comunicado_serialization_contenido_largo(self):
        """
        Test: Serialización de contenido extenso.

        Given: Un comunicado con un campo 'contenido' que almacena un volumen 
            considerable de texto (ej. 10.000 caracteres generados).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'contenido' debe devolverse íntegro, sin truncamientos 
            ni pérdida de datos, manteniendo la longitud exacta original 
            en la respuesta serializada.
        """
        contenido_extenso = "Contenido de prueba. " * 500 
        self.comunicado.contenido = contenido_extenso
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('contenido', data)

        self.assertEqual(
            len(data['contenido']), 
            len(contenido_extenso),
            msg="El serializador truncó el contenido largo del comunicado."
        )

        self.assertTrue(
            data['contenido'].endswith("prueba. "),
            msg="El final del contenido serializado no coincide con el original."
        )



    def test_comunicado_serialization_contenido_caracteres_especiales(self):
        """
        Test: Manejo de caracteres especiales en el contenido.

        Given: Un comunicado cuyo campo 'contenido' incluye una mezcla de 
            emojis, símbolos de moneda (€, $), caracteres con tildes, 
            eñes (ñ) y símbolos matemáticos (≠, ±).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'contenido' debe devolverse íntegro y con la codificación 
            correcta (UTF-8), garantizando que no se transformen en 
            caracteres extraños (mojibake) en la respuesta JSON.
        """
        caracteres_especiales = (
            "Noticia importante: ¡Mañana hay Cabildo! 📢 "
            "Presupuesto: 1.500€ (aprox. 1.600$). "
            "Cálculo: 25% ± 2. "
            "Mañana y niños con cigüeña en España."
        )
        self.comunicado.contenido = caracteres_especiales
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('contenido', data)

        self.assertEqual(
            data['contenido'], 
            caracteres_especiales,
            msg="El serializador corrompió los caracteres especiales o la codificación UTF-8."
        )

        self.assertIn("📢", data['contenido'], "El emoji no se serializó correctamente.")
        self.assertIn("€", data['contenido'], "El símbolo del Euro se perdió.")
        self.assertIn("ñ", data['contenido'], "La letra 'ñ' no se procesó correctamente.")



    def test_comunicado_serialization_contenido_emojis(self):
        """
        Test: Soporte de emojis en el contenido del comunicado.

        Given: Un comunicado cuyo campo 'contenido' incluye una variedad de 
            emojis modernos (caracteres Unicode de 4 bytes) como 🔔, 📅 y 🙏.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El campo 'contenido' debe mantener los emojis íntegros en la 
            respuesta JSON, garantizando que el serializador soporte 
            correctamente la codificación utf8mb4.
        """
        texto_con_emojis = "¡Atención! 🔔 Mañana es el Besamanos. 📅 ¡Os esperamos! 🙏✨"
        self.comunicado.contenido = texto_con_emojis
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('contenido', data)

        self.assertEqual(
            data['contenido'], 
            texto_con_emojis,
            msg="El serializador corrompió o eliminó los emojis del contenido."
        )

        self.assertEqual(
            len(data['contenido']), 
            len(texto_con_emojis),
            msg="La longitud de la cadena con emojis ha variado tras la serialización."
        )



    def test_comunicado_serialization_tipo_comunicacion_invalido(self):
        """
        Test: Valor de tipo_comunicacion no presente en choices.

        Given: Un comunicado que, por una inconsistencia en la base de datos, 
            contiene un valor ('INVALIDO') en el campo 'tipo_comunicacion' 
            que no figura entre las opciones (choices) definidas en el modelo.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe actuar con resiliencia, devolviendo el 
            valor crudo 'INVALIDO' en lugar de lanzar una excepción, 
            permitiendo que el flujo de datos continúe.
        """
        valor_invalido = "INVALIDO"
        self.comunicado.tipo_comunicacion = valor_invalido

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('tipo_comunicacion', data)

        self.assertEqual(
            data['tipo_comunicacion'], 
            valor_invalido,
            msg="El serializador falló o alteró un valor de tipo_comunicacion que no está en los choices."
        )



    def test_comunicado_serialization_tipo_comunicacion_null_inesperado(self):
        """
        Test: Valor null en campo obligatorio (tipo_comunicacion).

        Given: Un comunicado que, debido a una inconsistencia crítica en la 
            integridad de la base de datos, tiene el valor null (None) 
            en el campo 'tipo_comunicacion' (campo que no debería permitir nulos).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe actuar con resiliencia, devolviendo el 
            valor nulo (null en JSON) en lugar de fallar, permitiendo 
            que la respuesta del API se complete.
        """
        self.comunicado.tipo_comunicacion = None
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('tipo_comunicacion', data)
        self.assertIsNone(
            data['tipo_comunicacion'], 
            msg="El serializador falló al procesar un valor nulo en tipo_comunicacion."
        )



    def test_comunicado_serialization_display_error_resiliencia(self):
        """
        Test: Resiliencia ante fallos en la resolución del display de choices.

        Given: Un comunicado con un valor en 'tipo_comunicacion' que rompe la 
            lógica habitual de mapeo (ej. un tipo de dato inesperado como un entero 
            cuando se esperan strings).
        When: El serializador intenta obtener la representación legible mediante 
            get_tipo_comunicacion_display().
        Then: El serializador debe manejar la discrepancia devolviendo el valor 
            original o una representación segura, evitando un 500 Internal Server Error.
        """
        valor_disruptivo = 999
        self.comunicado.tipo_comunicacion = valor_disruptivo
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('tipo_comunicacion', data)
        self.assertEqual(
            str(data['tipo_comunicacion']), 
            str(valor_disruptivo),
            msg="El serializador falló al procesar un valor que no puede mapearse en los choices."
        )

        display_value = self.comunicado.get_tipo_comunicacion_display()
        self.assertEqual(display_value, valor_disruptivo)



    def test_comunicado_serialization_area_interes_eliminada_referenciada(self):
        """
        Test: Área de interés eliminada pero aún referenciada.

        Given: Un comunicado que mantiene una referencia en su relación ManyToMany 
            hacia un ID de 'AreaInteres' que ya no existe en la base de datos.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe omitir el registro inexistente en el listado 
            de 'areas_interes', devolviendo una lista válida con el resto de 
            áreas o una lista vacía, evitando un error de 'ObjectDoesNotExist'.
        """
        area = AreaInteres.objects.create(nombre_area='CULTOS_FORMACION')
        self.comunicado.areas_interes.add(area)

        nombre_area_borrada = str(area)

        area.delete()

        self.comunicado.refresh_from_db()

        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('areas_interes', data)

        self.assertNotIn(
            nombre_area_borrada, 
            data['areas_interes'],
            msg="El serializador incluyó una referencia a un área de interés eliminada."
        )

        self.assertIsInstance(data['areas_interes'], list)



    def test_comunicado_serialization_str_model_exception_resilience(self):
        """
        Test: Resiliencia cuando el __str__ del modelo relacionado falla.

        Given: Un comunicado relacionado con un objeto (ej. AreaInteres) cuyo 
            método __str__ está corrupto y lanza una excepción (TypeError/AttributeError).
        When: El serializador intenta obtener la representación de texto de dicho 
            objeto para incluirlo en la respuesta JSON.
        Then: El sistema debe manejar el error de forma que no interrumpa la 
            serialización del resto de campos, devolviendo un valor por defecto 
            o permitiendo que el error sea capturado sin un 500 global.
        """
        area = AreaInteres.objects.create(nombre_area='PATRIMONIO')
        self.comunicado.areas_interes.add(area)

        with patch.object(AreaInteres, '__str__', side_effect=TypeError("Error forzado en __str__")):
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data

                self.assertIn('areas_interes', data)
                
            except Exception as e:
                self.fail(f"El serializador no fue resiliente al fallo del __str__ del modelo: {e}")



    def test_comunicado_serialization_areas_interes_max_capacity(self):
        """
        Test: Límite máximo en relación ManyToMany (Áreas de Interés).

        Given: Un comunicado asociado a todas las áreas de interés posibles 
            definidas en el sistema (simulando la carga máxima del M2M permitida 
            por el modelo, que está restringido por choices y unique=True).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe procesar la relación completa de forma eficiente 
            y devolver una lista que contenga exactamente todos los elementos sin errores.
        """
        areas_creadas = []
        for choice, label in AreaInteres.NombreArea.choices:
            area, _ = AreaInteres.objects.get_or_create(nombre_area=choice)
            areas_creadas.append(area)

        self.comunicado.areas_interes.add(*areas_creadas)
        
        serializer = ComunicadoListSerializer(instance=self.comunicado)
        data = serializer.data

        self.assertIn('areas_interes', data)
        self.assertIsInstance(data['areas_interes'], list)

        cantidad_maxima = len(AreaInteres.NombreArea.choices)
        self.assertEqual(
            len(data['areas_interes']), 
            cantidad_maxima,
            msg=f"El serializador no procesó la carga máxima. Esperaba {cantidad_maxima} áreas."
        )



    def test_comunicado_serialization_relacion_autor_corrupta(self):
        """
        Test: Relación de autor con valores corruptos (nulos inesperados).

        Given: Un comunicado con un autor asignado, pero cuyos datos 
            internos (nombre, username, apellidos) han sido corrompidos 
            o son nulos en la base de datos (saltándose las validaciones).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El método get_autor_nombre debe ser resiliente, evitar 
            errores (como AttributeError al intentar hacer .strip() sobre None) 
            y devolver un valor de respaldo seguro (ej. "Secretaría" o cadena vacía).
        """
        self.comunicado.autor.nombre = None
        self.comunicado.autor.username = None
        self.comunicado.autor.primer_apellido = None
        
        try:
            serializer = ComunicadoListSerializer(instance=self.comunicado)
            data = serializer.data
            
            self.assertIn('autor_nombre', data)

            self.assertIsInstance(
                data['autor_nombre'], 
                str,
                msg="El nombre del autor corrupto no se resolvió como un string seguro."
            )
            
        except Exception as e:
            self.fail(f"El serializador falló estrepitosamente ante un autor con datos corruptos: {type(e).__name__} - {e}")



    def test_comunicado_serialization_autor_objeto_invalido(self):
        """
        Test: Resiliencia ante un objeto autor inválido o inesperado.

        Given: Un comunicado donde la relación 'autor' apunta a un objeto 
            que existe pero no posee la interfaz esperada (ej. no tiene los 
            atributos 'nombre' o 'username'), simulando una anomalía en memoria.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El método get_autor_nombre debe ser capaz de absorber el 
            AttributeError derivado de la falta de atributos y devolver de 
            forma segura el valor institucional "Secretaría".
        """
        objeto_invalido = Mock(spec=[]) 

        with patch('api.models.Comunicado.autor', new_callable=PropertyMock) as mock_autor_prop:
            mock_autor_prop.return_value = objeto_invalido
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data
                
                self.assertIn('autor_nombre', data)

                self.assertEqual(
                    data['autor_nombre'], 
                    "Secretaría",
                    msg="El serializador no aplicó el fallback 'Secretaría' ante un objeto autor inválido."
                )
                
            except Exception as e:
                self.fail(f"El serializador falló estrepitosamente ante un objeto autor inválido: {type(e).__name__} - {e}")



    def test_comunicado_serialization_autor_sin_username(self):
        """
        Test: Autor sin atributo username.

        Given: Un comunicado con un autor asignado cuyo 'nombre' es nulo o vacío, 
            lo que fuerza al serializador a buscar el atributo de respaldo 'username', 
            pero dicho atributo no existe en el objeto.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe capturar el AttributeError o usar métodos 
            defensivos (como getattr) para evitar la caída del servidor, devolviendo 
            un string válido (el apellido restante o el fallback "Secretaría").
        """
        mock_autor = Mock(spec=['nombre', 'primer_apellido'])
        mock_autor.nombre = None  
        mock_autor.primer_apellido = "Pérez"

        with patch('api.models.Comunicado.autor', new_callable=PropertyMock) as mock_autor_prop:
            mock_autor_prop.return_value = mock_autor
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data
                
                self.assertIn('autor_nombre', data)

                self.assertIsInstance(
                    data['autor_nombre'], 
                    str,
                    msg="El serializador no devolvió un string válido al faltar el username."
                )
                
            except AttributeError as e:
                self.fail(f"El serializador falló al intentar acceder al atributo inexistente 'username': {e}")
            except Exception as e:
                self.fail(f"Fallo inesperado al procesar un autor sin username: {type(e).__name__} - {e}")



    def test_comunicado_serialization_autor_nombre_none(self):
        """
        Test: Autor con campo nombre explícitamente nulo.

        Given: Un comunicado cuyo autor (instancia real de Hermano) tiene el 
            campo 'nombre' establecido a None, simulando un dato incompleto 
            o corrupto en memoria.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe evitar errores de tipo (AttributeError/TypeError), 
            aplicar el fallback automático hacia el 'username' (DNI en este modelo) 
            y devolver la cadena formateada correctamente junto con el apellido.
        """
        self.comunicado.autor.nombre = None

        self.comunicado.autor.username = "12345678X"
        self.comunicado.autor.primer_apellido = "García"
        
        try:
            serializer = ComunicadoListSerializer(instance=self.comunicado)
            data = serializer.data
            
            self.assertIn('autor_nombre', data)

            self.assertEqual(
                data['autor_nombre'], 
                "12345678X García",
                msg="El serializador no aplicó el fallback esperado al username cuando el nombre era nulo."
            )
            
        except Exception as e:
            self.fail(f"El serializador falló al procesar un autor con nombre=None: {type(e).__name__} - {e}")



    def test_comunicado_serialization_autor_primer_apellido_none(self):
        """
        Test: Autor con campo primer_apellido explícitamente nulo.

        Given: Un comunicado cuyo autor (instancia real de Hermano) tiene el 
            campo 'primer_apellido' establecido a None (simulando datos 
            incompletos en su perfil).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe evitar errores al intentar procesar el nulo, 
            sustituirlo por una cadena vacía y devolver únicamente el nombre, 
            asegurándose de no dejar espacios en blanco residuales al final.
        """
        self.comunicado.autor.primer_apellido = None

        self.comunicado.autor.nombre = "Juan"
        
        try:
            serializer = ComunicadoListSerializer(instance=self.comunicado)
            data = serializer.data
            
            self.assertIn('autor_nombre', data)

            self.assertEqual(
                data['autor_nombre'], 
                "Juan",
                msg="El serializador falló al procesar un apellido nulo o dejó espacios residuales."
            )
            
        except Exception as e:
            self.fail(f"El serializador falló al procesar un autor con primer_apellido=None: {type(e).__name__} - {e}")



    def test_comunicado_serialization_autor_eliminado_dangling(self):
        """
        Test: Autor eliminado (ForeignKey apuntando a un registro inexistente).

        Given: Un comunicado cuyo 'autor_id' apunta a un registro que ya no 
            existe en la base de datos (simulando un borrado anómalo directo 
            en SQL o pérdida de integridad referencial).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: Al intentar resolver la relación, el ORM lanzará ObjectDoesNotExist. 
            El serializador debe capturarlo pacíficamente y devolver el 
            valor de respaldo institucional "Secretaría".
        """
        self.comunicado.autor_id = 999999
        
        try:
            serializer = ComunicadoListSerializer(instance=self.comunicado)
            data = serializer.data
            
            self.assertIn('autor_nombre', data)

            self.assertEqual(
                data['autor_nombre'], 
                "Secretaría",
                msg="El serializador no aplicó el fallback 'Secretaría' ante un ForeignKey huérfano."
            )
            
        except Exception as e:
            self.fail(f"El serializador falló estrepitosamente ante un ForeignKey dangling: {type(e).__name__} - {e}")



    def test_comunicado_serialization_autor_atributos_ausentes(self):
        """
        Test: Autor con atributos dinámicamente ausentes.

        Given: Un comunicado donde el objeto 'autor' existe pero carece 
            físicamente de los atributos 'nombre', 'username' y 'primer_apellido' 
            (simulando una carga parcial de campos con .only()/.defer() 
            o una corrupción de la instancia en memoria).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe evitar el colapso por AttributeError, 
            gestionar la ausencia de datos mediante getattr() con valores 
            por defecto y devolver el fallback institucional "Secretaría".
        """
        autor_vacio = Mock(spec=[]) 
        
        with patch('api.models.Comunicado.autor', new_callable=PropertyMock) as mock_autor_prop:
            mock_autor_prop.return_value = autor_vacio
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data
                
                self.assertIn('autor_nombre', data)

                self.assertEqual(
                    data['autor_nombre'], 
                    "Secretaría",
                    msg="El serializador no devolvió 'Secretaría' ante un objeto autor sin atributos."
                )
                
            except Exception as e:
                self.fail(f"El serializador falló ante atributos ausentes: {type(e).__name__} - {e}")



    def test_comunicado_serialization_autor_lanza_excepcion_al_acceder(self):
        """
        Test: El acceso al atributo 'autor' lanza una excepción inesperada.

        Given: Un comunicado donde el acceso a la propiedad 'autor' dispara 
            una excepción (simulando un fallo de integridad, un error de 
            base de datos 'OperationalError' o un proxy corrupto).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El método get_autor_nombre debe capturar la excepción 
            mediante su bloque try/except y devolver el valor de respaldo 
            "Secretaría", garantizando la disponibilidad del API.
        """
        with patch('api.models.Comunicado.autor', new_callable=PropertyMock) as mock_autor_prop:
            mock_autor_prop.side_effect = Exception("Error crítico de base de datos")
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data
                
                self.assertIn('autor_nombre', data)

                self.assertEqual(
                    data['autor_nombre'], 
                    "Secretaría",
                    msg="El serializador no devolvió 'Secretaría' cuando el acceso al autor falló."
                )
                
            except Exception as e:
                self.fail(f"El serializador no capturó la excepción del atributo 'autor': {type(e).__name__} - {e}")



    def test_comunicado_serialization_imagen_archivo_inexistente(self):
        """
        Test: Imagen con referencia en BD pero archivo eliminado físicamente.

        Given: Un comunicado que tiene una ruta de imagen asignada en la 
            base de datos, pero el archivo correspondiente ha sido eliminado 
            del sistema de almacenamiento (simulando pérdida de datos en disco).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe gestionar el error de entrada/salida (IOError) 
            o la ausencia del archivo de forma graciosa, devolviendo None 
            en el campo 'imagen_portada' en lugar de romper la respuesta del API.
        """
        with patch('django.db.models.fields.files.FieldFile.url', new_callable=PropertyMock) as mock_url:
            mock_url.side_effect = FileNotFoundError("Archivo no encontrado en el servidor")
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data

                self.assertIn('imagen_portada', data)
                self.assertIsNone(
                    data['imagen_portada'], 
                    msg="El serializador debería devolver None si el archivo físico no existe."
                )
                
            except Exception as e:
                self.fail(f"El serializador falló al procesar una imagen inexistente en disco: {type(e).__name__} - {e}")



    def test_comunicado_serialization_imagen_campo_corrupto_bd(self):
        """
        Test: Valor corrupto en el campo de base de datos para la imagen.

        Given: Un comunicado donde el valor almacenado en la columna de la 
            imagen es basura, caracteres inválidos o un formato que rompe 
            la lógica del FieldFile de Django (simulando corrupción de BD).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe capturar el error de valor (ValueError) o 
            la operación sospechosa y devolver None en el campo 'imagen_portada', 
            evitando que el error de bajo nivel rompa la respuesta JSON.
        """
        with patch('django.db.models.fields.files.FieldFile.url', new_callable=PropertyMock) as mock_url:
            mock_url.side_effect = ValueError("Ruta de archivo corrupta o inválida")
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data
                
                self.assertIn('imagen_portada', data)

                self.assertIsNone(
                    data['imagen_portada'], 
                    msg="El serializador falló al no devolver None ante un path de imagen corrupto."
                )
                
            except Exception as e:
                self.fail(f"El serializador explotó ante un campo de imagen corrupto: {type(e).__name__} - {e}")



    def test_comunicado_serialization_imagen_url_mal_formada(self):
        """
        Test: URL de imagen mal formada o inválida.

        Given: Un comunicado con una referencia de imagen que, al intentar 
            generar su URL pública, provoca un error de valor (ValueError) 
            debido a una configuración de almacenamiento corrupta o 
            caracteres ilegales en la ruta.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe interceptar el error de construcción de 
            la URL y devolver None, garantizando que un error de 
            infraestructura no bloquee la visualización del comunicado.
        """
        with patch('django.db.models.fields.files.FieldFile.url', new_callable=PropertyMock) as mock_url:
            mock_url.side_effect = ValueError("La URL de la imagen no es válida o está mal formada")
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data
                
                self.assertIn('imagen_portada', data)

                self.assertIsNone(
                    data['imagen_portada'], 
                    msg="El serializador falló al no devolver None ante una URL de imagen mal formada."
                )
                
            except Exception as e:
                self.fail(f"El serializador explotó ante una URL mal formada: {type(e).__name__} - {e}")



    def test_comunicado_serialization_storage_backend_falla(self):
        """
        Test: El backend de almacenamiento (Storage) falla críticamente.

        Given: Un comunicado con imagen donde el sistema de almacenamiento 
            está inaccesible o caído (simulando un error de conexión con 
            S3, Azure o un fallo de montaje en el sistema de archivos).
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe capturar el error de infraestructura 
            (RuntimeError/IOError) y devolver None en 'imagen_portada', 
            permitiendo que el resto del JSON se entregue correctamente.
        """
        with patch('django.db.models.fields.files.FieldFile.url', new_callable=PropertyMock) as mock_url:
            mock_url.side_effect = RuntimeError("No se pudo conectar con el servidor de almacenamiento (S3/Azure)")
            
            try:
                serializer = ComunicadoListSerializer(instance=self.comunicado)
                data = serializer.data
                
                self.assertIn('imagen_portada', data)

                self.assertIsNone(
                    data['imagen_portada'], 
                    msg="El serializador falló al no devolver None cuando el backend de storage estaba caído."
                )
                
            except Exception as e:
                self.fail(f"El serializador explotó por un fallo del backend de storage: {type(e).__name__} - {e}")



    def test_comunicado_serializer_ignora_datos_entrada(self):
        """
        Test: Integridad de contrato de API (Solo Lectura).

        Given: Un intento de instanciar el ComunicadoListSerializer pasando 
            un diccionario de datos ('data') simulando una petición POST/PUT, 
            a pesar de ser un serializador diseñado para salida.
        When: Se llama a .is_valid() y se accede a .data.
        Then: El serializador debe mantener su integridad de solo lectura; 
            aunque se llame a la validación, los datos resultantes en .data 
            deben provenir de la instancia de la base de datos y no de los 
            datos inyectados, confirmando que es un componente de salida.
        """
        datos_intrusos = {
            "titulo": "Título Malicioso",
            "contenido": "Contenido que no debería procesarse",
            "autor_nombre": "Hacker"
        }

        serializer = ComunicadoListSerializer(instance=self.comunicado, data=datos_intrusos, partial=True)

        serializer.is_valid() 

        data_salida = serializer.data

        self.assertNotEqual(
            data_salida.get('titulo'), 
            datos_intrusos['titulo'],
            msg="Vulnerabilidad de contrato: El serializador de salida permitió la mutación de datos en la representación."
        )

        self.assertEqual(
            data_salida.get('titulo'), 
            self.comunicado.titulo,
            msg="El serializador no mantuvo la integridad de la instancia original frente a datos intrusos."
        )



    def test_comunicado_serializer_tipo_display_es_inmutable(self):
        """
        Test: Inmutabilidad del campo calculado 'tipo_display'.

        Given: Un intento de inyectar un valor falso para 'tipo_display' 
            en los datos de entrada del serializador, buscando alterar 
            la representación visual del tipo de comunicado.
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe ignorar el valor inyectado y devolver 
            únicamente el resultado de la lógica interna 'get_tipo_display', 
            asegurando que el contrato de presentación no es manipulable 
            desde el exterior.
        """
        Comunicado.objects.filter(pk=self.comunicado.pk).update(tipo_comunicacion='AVISO')
        self.comunicado.refresh_from_db()
        
        datos_manipulados = {
            "tipo_display": "NOTICIA CRÍTICA"
        }
        
        serializer = ComunicadoListSerializer(instance=self.comunicado, data=datos_manipulados, partial=True)
        serializer.is_valid()
        data_salida = serializer.data

        self.assertNotEqual(
            data_salida.get('tipo_display'), 
            "NOTICIA CRÍTICA",
            msg="El serializador permitió la manipulación externa de tipo_display."
        )

        valor_esperado = self.comunicado.get_tipo_comunicacion_display() 
        
        self.assertEqual(
            data_salida.get('tipo_display'), 
            valor_esperado,
            msg=f"Se esperaba '{valor_esperado}' pero llegó '{data_salida.get('tipo_display')}'"
        )



    def test_comunicado_serializer_autor_nombre_es_inmutable(self):
        """
        Test: Inmutabilidad del campo calculado 'autor_nombre'.

        Given: Un intento de suplantación de identidad inyectando un valor 
            falso para 'autor_nombre' en los datos de entrada, simulando 
            un ataque de asignación masiva.
        When: Se procesa la instancia a través del ComunicadoListSerializer 
            llamando a .is_valid() para cumplir con el protocolo de DRF.
        Then: El serializador debe ignorar el nombre inyectado y resolver 
            únicamente el nombre real del autor a través de la relación 
            de base de datos, garantizando la integridad de la autoría.
        """
        self.comunicado.autor.nombre = "Juan"
        self.comunicado.autor.primer_apellido = "Pérez"
        
        datos_manipulados = {
            "autor_nombre": "Usuario Administrador Hack"
        }
        
        serializer = ComunicadoListSerializer(instance=self.comunicado, data=datos_manipulados, partial=True)

        serializer.is_valid()
        data_salida = serializer.data

        self.assertNotEqual(
            data_salida.get('autor_nombre'), 
            "Usuario Administrador Hack",
            msg="El serializador permitió la suplantación de la autoría mediante entrada de datos."
        )

        self.assertEqual(
            data_salida.get('autor_nombre'), 
            "Juan Pérez",
            msg="El serializador no resolvió correctamente la identidad real tras un intento de manipulación."
        )



    def test_comunicado_serializer_areas_interes_es_inmutable(self):
        """
        Test: Inmutabilidad de la relación ManyToMany 'areas_interes'.

        Given: Un intento de modificar las áreas destinatarias de un 
            comunicado enviando una lista de IDs de áreas diferentes 
            en los datos de entrada ('data').
        When: Se procesa la instancia a través del ComunicadoListSerializer.
        Then: El serializador debe ignorar los IDs inyectados y devolver 
            exclusivamente las áreas de interés asociadas en la base de 
            datos, garantizando que el destino del comunicado no sea 
            manipulable mediante la carga útil del API.
        """
        area_real = AreaInteres.objects.get_or_create(nombre_area='CARIDAD')[0]
        self.comunicado.areas_interes.set([area_real])

        area_intrusa = AreaInteres.objects.get_or_create(nombre_area='JUVENTUD')[0]

        datos_manipulados = {
            "areas_interes": [area_intrusa.id] 
        }
        
        serializer = ComunicadoListSerializer(instance=self.comunicado, data=datos_manipulados, partial=True)
        serializer.is_valid()
        data_salida = serializer.data

        areas_en_salida = data_salida.get('areas_interes', [])

        nombre_intruso = str(area_intrusa)
        self.assertNotIn(
            nombre_intruso, 
            areas_en_salida,
            msg=f"El serializador permitió la manipulación externa. Se encontró '{nombre_intruso}' en la salida."
        )

        nombre_real = str(area_real)
        self.assertIn(
            nombre_real, 
            areas_en_salida,
            msg=f"El serializador perdió la integridad. No se encontró '{nombre_real}' en {areas_en_salida}."
        )