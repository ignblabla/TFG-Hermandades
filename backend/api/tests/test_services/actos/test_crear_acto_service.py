import io
from zoneinfo import ZoneInfo
import concurrent.futures

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

import pytz
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError

from api.servicios.acto.acto_service import crear_acto_service
from api.serializadores.acto.acto_serializer import ActoCreateSerializer

from ....models import Acto, CuerpoPertenencia, HermanoCuerpo, PapeletaSitio, TipoActo, Hermano

User = get_user_model()


class CrearActoServiceTest(TestCase):

    def setUp(self):
        # ---------------------------------------------------------------------
        # FECHA BASE
        # ---------------------------------------------------------------------
        self.ahora = timezone.now()

        # ---------------------------------------------------------------------
        # USUARIO ADMIN
        # ---------------------------------------------------------------------
        self.admin = Hermano.objects.create_user(
            dni="12345678A",
            username="12345678A",
            password="password",
            nombre="Admin",
            primer_apellido="Test",
            segundo_apellido="User",
            email="admin@example.com",
            telefono="600000000",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1980-01-01",
            direccion="Calle Admin",
            codigo_postal="41001",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=True,
        )

        # ---------------------------------------------------------------------
        # USUARIO NO ADMIN (tal como indicas)
        # ---------------------------------------------------------------------
        self.hermano = Hermano.objects.create_user(
            dni="87654321X",
            username="87654321X",
            password="password",
            nombre="Luis",
            primer_apellido="Ruiz",
            segundo_apellido="Díaz",
            email="luis@example.com",
            telefono="600654321",
            estado_civil=Hermano.EstadoCivil.CASADO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1002,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1985-06-15",
            direccion="Calle Sierpes",
            codigo_postal="41004",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        # ---------------------------------------------------------------------
        # TIPOS DE ACTO
        # ---------------------------------------------------------------------
        self.tipo_no_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        self.tipo_con_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        # ---------------------------------------------------------------------
        # FECHAS COHERENTES
        # ---------------------------------------------------------------------
        self.fecha_acto = self.ahora + timedelta(days=30)

        self.inicio_insignias = self.ahora + timedelta(days=1)
        self.fin_insignias = self.ahora + timedelta(days=3)

        self.inicio_cirios = self.fin_insignias + timedelta(hours=1)
        self.fin_cirios = self.inicio_cirios + timedelta(days=2)

        # ---------------------------------------------------------------------
        # ACTO BASE (válidos)
        # ---------------------------------------------------------------------
        self.acto_no_papeleta_ok = {
            "nombre": "Convivencia febrero",
            "lugar": "Casa Hermandad",
            "descripcion": "Acto sin papeleta",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        self.acto_tradicional_ok = {
            "nombre": "Estación de Penitencia 2026",
            "lugar": "Parroquia",
            "descripcion": "Acto con reparto tradicional",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        }

        self.acto_unificado_ok = {
            "nombre": "Cabildo General 2026",
            "lugar": "Salón de Actos",
            "descripcion": "Acto unificado",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }



    def test_admin_crea_acto_valido_ok(self):
        """
        Test: Usuario administrador (esAdmin=True) crea un acto válido -> OK

        Given: Un usuario con rol de administrador y un diccionario de datos validados para un acto nuevo.
        When: Se invoca el servicio 'crear_acto_service' enviando el usuario solicitante y los datos.
        Then: El sistema debe permitir la operación, crear el acto en la base de datos y retornar la instancia del acto creado.
        """
        datos_nuevo_acto = self.acto_tradicional_ok.copy()

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_nuevo_acto
        )

        self.assertIsNotNone(nuevo_acto.id)

        acto_en_bd = Acto.objects.get(id=nuevo_acto.id)
        self.assertEqual(acto_en_bd.nombre, "Estación de Penitencia 2026")
        self.assertEqual(acto_en_bd.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        self.assertEqual(acto_en_bd.tipo_acto, self.tipo_con_papeleta)



    def test_admin_crea_acto_campos_opcionales_nulos_ok(self):
        """
        Test: Usuario admin con todos los campos opcionales nulos -> OK

        Given: Un usuario administrador y un conjunto de datos donde los campos opcionales 
                (descripcion, modalidad, fechas de solicitud e imagen) son nulos, 
                pero el tipo de acto no requiere papeleta.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe crear el acto correctamente en la base de datos, 
                validando que la ausencia de campos opcionales no impide el registro.
        """
        datos_minimos = {
            "nombre": "Acto Mínimo",
            "lugar": "Sede Social",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_no_papeleta,
            "descripcion": None,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
            "imagen_portada": None
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_minimos
        )

        self.assertTrue(Acto.objects.filter(id=nuevo_acto.id).exists())
        self.assertIsNone(nuevo_acto.descripcion)
        self.assertEqual(nuevo_acto.nombre, "Acto Mínimo")



    def test_admin_crea_acto_con_imagen_valida_ok(self):
        """
        Test: Usuario admin con imagen válida -> OK

        Given: Un usuario administrador y un payload de datos que incluye un objeto de archivo 
                simulando una imagen válida (formato y tamaño correcto).
        When: Se invoca el servicio 'crear_acto_service' con estos datos.
        Then: El sistema debe crear el acto correctamente y el campo 'imagen_portada' debe 
                contener la referencia al archivo subido.
        """
        imagen_mock = SimpleUploadedFile(
            name='test_imagen.png',
            content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89',
            content_type='image/png'
        )

        datos_con_imagen = self.acto_no_papeleta_ok.copy()
        datos_con_imagen["imagen_portada"] = imagen_mock

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_con_imagen
        )

        self.assertTrue(Acto.objects.filter(id=nuevo_acto.id).exists())
        self.assertTrue(nuevo_acto.imagen_portada.name.endswith('.png'))



    def test_admin_crea_acto_con_nombre_espacios_extra_ok(self):
        """
        Test: Nombre con espacios al inicio y final -> se guarda correctamente sin espacios

        Given: Un usuario administrador y un payload donde el nombre del acto tiene espacios en blanco accidentales al principio y al final.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe procesar el nombre, eliminar los espacios en blanco (trim) y persistir el acto con el nombre limpio en la base de datos.
        """
        nombre_con_espacios = "   Vía Crucis Cuaresmal   "
        nombre_esperado = "Vía Crucis Cuaresmal"
        
        datos_con_espacios = self.acto_no_papeleta_ok.copy()
        datos_con_espacios["nombre"] = nombre_con_espacios

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_con_espacios
        )

        self.assertEqual(nuevo_acto.nombre, nombre_esperado)

        acto_bd = Acto.objects.get(id=nuevo_acto.id)
        self.assertEqual(acto_bd.nombre, nombre_esperado)



    def test_admin_crea_acto_nombre_con_espacios_no_vacio_ok(self):
        """
        Test: Nombre con espacios pero no vacío tras strip -> OK

        Given: Un usuario administrador y un payload donde el nombre contiene caracteres 
                de espacio mezclados con texto (ej: "  Quinario  2026  ").
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe permitir la creación, aplicando el strip correspondiente 
                y guardando el nombre resultante sin los espacios en los extremos.
        """
        nombre_sucio = "  Quinario 2026  "
        nombre_limpio = "Quinario 2026"

        datos_nombre_espacios = self.acto_no_papeleta_ok.copy()
        datos_nombre_espacios["nombre"] = nombre_sucio

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_nombre_espacios
        )

        self.assertEqual(nuevo_acto.nombre, nombre_limpio)
        self.assertTrue(Acto.objects.filter(nombre=nombre_limpio).exists())



    def test_admin_crea_acto_sin_modalidad_ni_fechas_ok(self):
        """
        Test: Acto sin modalidad ni fechas -> OK

        Given: Un usuario administrador y un conjunto de datos para un tipo de acto que 
                no requiere papeleta (como una Convivencia), por lo que no se envían 
                modalidad ni fechas de solicitud.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe crear el acto correctamente, ya que estos campos son opcionales 
                o irrelevantes para actos que no implican reparto de sitios.
        """
        datos_sin_reparto = {
            "nombre": "Convivencia de Hermandad",
            "lugar": "Casa Hermandad",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_no_papeleta,
            "descripcion": "Almuerzo de hermandad tras el cabildo.",
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_sin_reparto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.tipo_acto.requiere_papeleta, False)
        self.assertIsNone(nuevo_acto.modalidad)
        self.assertIsNone(nuevo_acto.inicio_solicitud)



    def test_admin_crea_acto_campos_basicos_validos_ok(self):
        """
        Test: Acto con todos los campos básicos válidos -> OK

        Given: Un usuario administrador y un payload que contiene únicamente los campos obligatorios 
                y básicos (nombre, lugar, fecha y tipo de acto) correctamente cumplimentados.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe procesar la solicitud con éxito, persistir el registro en la base de datos 
                y devolver la instancia del acto con los valores proporcionados.
        """
        datos_basicos = {
            "nombre": "Misa de Hermandad",
            "lugar": "Altar Mayor",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_no_papeleta
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_basicos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.nombre, "Misa de Hermandad")
        self.assertEqual(nuevo_acto.lugar, "Altar Mayor")
        self.assertEqual(nuevo_acto.fecha, self.fecha_acto)
        self.assertEqual(nuevo_acto.tipo_acto, self.tipo_no_papeleta)



    def test_admin_crea_acto_unificado_valido_ok(self):
        """
        Test: Con modalidad UNIFICADO + fechas inicio/fin válidas -> OK

        Given: Un usuario administrador y un diccionario de datos con modalidad UNIFICADO, 
                donde se definen las fechas de inicio y fin de solicitud generales, 
                dejando las fechas de cirios como nulas.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe crear el acto correctamente, validando que la configuración 
                unificada es consistente con la ausencia de fases separadas para cirios.
        """
        datos_unificado = self.acto_unificado_ok.copy()

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_unificado
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertIsNotNone(nuevo_acto.inicio_solicitud)
        self.assertIsNotNone(nuevo_acto.fin_solicitud)
        self.assertIsNone(nuevo_acto.inicio_solicitud_cirios)
        self.assertIsNone(nuevo_acto.fin_solicitud_cirios)



    def test_admin_crea_acto_unificado_sin_fechas_cirios_ok(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Modalidad UNIFICADO, Sin fechas de cirios -> OK

        Given: Un usuario administrador y un payload para un acto que requiere papeleta en modalidad UNIFICADO, 
                proporcionando fechas de solicitud de insignias pero dejando las de cirios como None.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe permitir la creación del acto, ya que en la modalidad unificada el reparto se 
                gestiona en un solo plazo y las fechas específicas de cirios no deben definirse.
        """
        datos_unificado_sin_cirios = {
            "nombre": "Vía Crucis Claustral",
            "lugar": "Interior Parroquia",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_unificado_sin_cirios
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertIsNone(nuevo_acto.inicio_solicitud_cirios)
        self.assertIsNone(nuevo_acto.fin_solicitud_cirios)
        self.assertTrue(Acto.objects.filter(id=nuevo_acto.id).exists())



    def test_admin_crea_acto_tradicional_fechas_ordenadas_ok(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Modalidad TRADICIONAL, Con todas las fechas correctas y ordenadas -> OK

        Given: Un usuario administrador y un payload para un acto que requiere papeleta en modalidad TRADICIONAL, 
                con una secuencia cronológica válida: inicio_insignias < fin_insignias < inicio_cirios < fin_cirios < fecha_acto.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe validar positivamente la jerarquía de fechas, crear el acto y persistir 
                correctamente los dos periodos de solicitud diferenciados.
        """
        datos_tradicional = self.acto_tradicional_ok.copy()

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_tradicional
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertTrue(nuevo_acto.inicio_solicitud < nuevo_acto.fin_solicitud)
        self.assertTrue(nuevo_acto.fin_solicitud < nuevo_acto.inicio_solicitud_cirios)
        self.assertTrue(nuevo_acto.inicio_solicitud_cirios < nuevo_acto.fin_solicitud_cirios)
        self.assertTrue(nuevo_acto.fin_solicitud_cirios < nuevo_acto.fecha)



    def test_admin_crea_acto_tradicional_flujo_fechas_perfecto_ok(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Modalidad TRADICIONAL, Flujo correcto: 
                inicio_solicitud < fin_solicitud < inicio_solicitud_cirios < fin_solicitud_cirios < fecha -> OK

        Given: Un usuario administrador y un payload con una secuencia temporal estricta donde el periodo 
                de insignias termina antes de que empiece el de cirios, y ambos terminan antes del acto.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe validar que el flujo de fases es coherente y crear el registro satisfactoriamente.
        """
        t1_inicio_insignias = self.ahora + timedelta(days=1)
        t2_fin_insignias = self.ahora + timedelta(days=5)
        t3_inicio_cirios = self.ahora + timedelta(days=6)
        t4_fin_cirios = self.ahora + timedelta(days=10)
        t5_fecha_acto = self.ahora + timedelta(days=15)

        datos_flujo_ok = {
            "nombre": "Estación de Penitencia - Flujo Temporal",
            "lugar": "Parroquia",
            "fecha": t5_fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": t1_inicio_insignias,
            "fin_solicitud": t2_fin_insignias,
            "inicio_solicitud_cirios": t3_inicio_cirios,
            "fin_solicitud_cirios": t4_fin_cirios,
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_flujo_ok
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.inicio_solicitud, t1_inicio_insignias)
        self.assertEqual(nuevo_acto.fin_solicitud, t2_fin_insignias)
        self.assertEqual(nuevo_acto.inicio_solicitud_cirios, t3_inicio_cirios)
        self.assertEqual(nuevo_acto.fin_solicitud_cirios, t4_fin_cirios)
        self.assertEqual(nuevo_acto.fecha, t5_fecha_acto)



    def test_admin_crea_acto_inicio_menor_que_fin_ok(self):
        """
        Test: Fechas válidas: inicio_solicitud < fin_solicitud -> OK

        Given: Un usuario administrador y un payload para un acto con papeleta donde 
                la fecha de inicio de solicitud es cronológicamente anterior a la de fin.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe validar correctamente la coherencia del rango temporal 
                y permitir la creación del acto en la base de datos.
        """
        datos_fechas_coherentes = self.acto_unificado_ok.copy()

        datos_fechas_coherentes["inicio_solicitud"] = self.ahora + timedelta(days=1)
        datos_fechas_coherentes["fin_solicitud"] = self.ahora + timedelta(days=2)

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_fechas_coherentes
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertLess(nuevo_acto.inicio_solicitud, nuevo_acto.fin_solicitud)
        self.assertTrue(Acto.objects.filter(id=nuevo_acto.id).exists())



    def test_admin_crea_acto_fin_solicitud_antes_de_fecha_ok(self):
        """
        Test: fin_solicitud < fecha -> OK

        Given: Un usuario administrador y un payload para un acto con papeleta donde el periodo 
                de solicitud finaliza antes de la celebración del acto.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe validar que es posible cerrar el plazo de solicitudes antes del evento 
                y permitir la creación del registro.
        """
        fecha_celebracion = self.ahora + timedelta(days=20)
        fin_plazo_solicitud = self.ahora + timedelta(days=15)

        datos_fecha_limite_ok = self.acto_unificado_ok.copy()
        datos_fecha_limite_ok["fecha"] = fecha_celebracion
        datos_fecha_limite_ok["fin_solicitud"] = fin_plazo_solicitud

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_fecha_limite_ok
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertLess(nuevo_acto.fin_solicitud, nuevo_acto.fecha)
        self.assertEqual(nuevo_acto.fecha, fecha_celebracion)



    def test_admin_crea_acto_todas_las_fechas_anteriores_al_evento_ok(self):
        """
        Test: Todas las fechas anteriores al acto -> OK

        Given: Un usuario administrador y un payload para un acto tradicional donde tanto el fin 
                de la primera fase (insignias) como el fin de la segunda fase (cirios) ocurren 
                antes de la fecha y hora de inicio del acto.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe confirmar que el cronograma es lógico (las solicitudes terminan antes 
                de que empiece el evento) y crear el acto satisfactoriamente.
        """
        fecha_celebracion = self.ahora + timedelta(days=50)

        datos_fechas_previas = self.acto_tradicional_ok.copy()
        datos_fechas_previas["fecha"] = fecha_celebracion
        datos_fechas_previas["fin_solicitud"] = self.ahora + timedelta(days=10)
        datos_fechas_previas["inicio_solicitud_cirios"] = self.ahora + timedelta(days=11)
        datos_fechas_previas["fin_solicitud_cirios"] = self.ahora + timedelta(days=20)

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_fechas_previas
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertLess(nuevo_acto.fin_solicitud, nuevo_acto.fecha)
        self.assertLess(nuevo_acto.fin_solicitud_cirios, nuevo_acto.fecha)
        self.assertEqual(nuevo_acto.fecha, fecha_celebracion)



    def test_admin_crea_acto_mismo_nombre_distinta_fecha_ok(self):
        """
        Test: Unicidad (caso válido) - Mismo nombre en distinta fecha -> OK

        Given: Un usuario administrador y un acto ya existente en la base de datos ("Convivencia").
        When: Se intenta crear un nuevo acto con el mismo nombre ("Convivencia") pero en una fecha diferente.
        Then: El sistema debe permitir la creación, ya que la restricción de unicidad solo debe 
                aplicarse cuando coinciden nombre y fecha simultáneamente.
        """
        Acto.objects.create(**self.acto_no_papeleta_ok)

        datos_mismo_nombre = self.acto_no_papeleta_ok.copy()
        datos_mismo_nombre["fecha"] = self.fecha_acto + timedelta(days=1)

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_mismo_nombre
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(Acto.objects.filter(nombre=self.acto_no_papeleta_ok["nombre"]).count(), 2)



    def test_admin_crea_acto_con_imagen_jpg_valida_ok(self):
        """
        Test: Imagen válida - JPG < 5MB -> OK

        Given: Un usuario administrador y un payload que incluye un archivo de imagen en formato JPG 
                con un tamaño inferior al límite de 5MB (ej: 1MB).
        When: Se invoca el servicio 'crear_acto_service' con los datos validados por el serializador.
        Then: El sistema debe procesar la creación correctamente, almacenando el archivo y 
                confirmando que el registro del acto persiste en la base de datos.
        """
        file_io = io.BytesIO()
        img = Image.new('RGB', (100, 100), color='red')
        img.save(file_io, format='JPEG')
        file_io.seek(0)

        imagen_jpg = SimpleUploadedFile(
            name='cartel_semana_santa.jpg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        datos_con_jpg = self.acto_no_papeleta_ok.copy()
        datos_con_jpg["imagen_portada"] = imagen_jpg

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_con_jpg
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertTrue(nuevo_acto.imagen_portada.name.endswith('.jpg'))
        self.assertLess(nuevo_acto.imagen_portada.size, 5 * 1024 * 1024)



    def test_admin_crea_acto_con_imagen_png_valida_ok(self):
        """
        Test: Imagen válida - PNG < 5MB -> OK

        Given: Un usuario administrador y un payload que incluye un archivo de imagen en formato PNG 
                con un tamaño inferior al límite de 5MB.
        When: Se invoca el servicio 'crear_acto_service' con los datos que han pasado la validación del serializador.
        Then: El sistema debe permitir la creación del acto, vinculando correctamente el archivo PNG 
                al campo 'imagen_portada' en la base de datos.
        """
        file_io = io.BytesIO()
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
        img.save(file_io, format='PNG')
        file_io.seek(0)

        imagen_png = SimpleUploadedFile(
            name='logo_hermandad.png',
            content=file_io.read(),
            content_type='image/png'
        )

        datos_con_png = self.acto_no_papeleta_ok.copy()
        datos_con_png["imagen_portada"] = imagen_png

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_con_png
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertTrue(nuevo_acto.imagen_portada.name.endswith('.png'))
        self.assertLess(nuevo_acto.imagen_portada.size, 5 * 1024 * 1024)
        self.assertEqual(Acto.objects.count(), 1)



    def test_admin_crea_acto_con_dimensiones_imagen_validas_ok(self):
        """
        Test: Imagen con dimensiones válidas (<4000x4000) -> OK

        Given: Un usuario administrador y un payload que contiene una imagen con dimensiones 
                dentro del rango permitido (por ejemplo, 800x600 píxeles).
        When: Se invoca el servicio 'crear_acto_service' tras la validación del serializador.
        Then: El sistema debe procesar la creación correctamente, verificando que las dimensiones 
                no exceden el límite técnico de 4000x4000 píxeles.
        """
        file_io = io.BytesIO()
        img = Image.new('RGB', (800, 600), color='blue')
        img.save(file_io, format='JPEG')
        file_io.seek(0)

        imagen_valida = SimpleUploadedFile(
            name='dimensiones_ok.jpg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        datos_con_imagen = self.acto_no_papeleta_ok.copy()
        datos_con_imagen["imagen_portada"] = imagen_valida

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_con_imagen
        )

        self.assertIsNotNone(nuevo_acto.id)

        img_guardada = Image.open(nuevo_acto.imagen_portada)
        self.assertEqual(img_guardada.width, 800)
        self.assertEqual(img_guardada.height, 600)
        self.assertLess(img_guardada.width, 4000)
        self.assertLess(img_guardada.height, 4000)



    def test_usuario_no_admin_intenta_crear_acto_error(self):
        """
        Test: Usuario NO admin intenta crear acto -> PermissionDenied

        Given: Un usuario con rol de hermano (esAdmin=False) y un conjunto de datos válidos para un acto.
        When: Se invoca el servicio 'crear_acto_service' con el usuario no autorizado.
        Then: El sistema debe lanzar una excepción de tipo 'PermissionDenied' y no debe crear ningún registro en la base de datos.
        """
        datos_acto = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(PermissionDenied):
            crear_acto_service(
                usuario_solicitante=self.hermano,
                data_validada=datos_acto
            )

        self.assertEqual(Acto.objects.count(), 0)



    def test_usuario_sin_atributo_esadmin_error(self):
        """
        Test: Usuario sin atributo esAdmin -> tratado como False -> error

        Given: Un objeto de usuario (por ejemplo, un AnonymousUser o un mock) que carece 
                del atributo 'esAdmin'.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El sistema debe tratar la ausencia del atributo como False mediante 'getattr', 
                lanzar una excepción 'PermissionDenied' y no crear el acto.
        """

        class UsuarioSinAtributo:
            pass
        
        usuario_incompleto = UsuarioSinAtributo()
        datos_acto = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(PermissionDenied):
            crear_acto_service(
                usuario_solicitante=usuario_incompleto,
                data_validada=datos_acto
            )

        self.assertEqual(Acto.objects.count(), 0)



    def test_admin_crea_acto_duplicado_mismo_nombre_y_fecha_error(self):
        """
        Test: Mismo nombre + misma fecha (mismo día) -> ValidationError

        Given: Un usuario administrador y un acto ya existente en la base de datos para una fecha específica.
        When: Se intenta crear un nuevo acto con el mismo nombre y en la misma fecha (día) a través del servicio.
        Then: El sistema debe detectar la duplicidad y lanzar una excepción 'ValidationError' con un mensaje informativo, evitando la creación del duplicado.
        """
        Acto.objects.create(**self.acto_no_papeleta_ok)

        datos_duplicados = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_duplicados
            )

        self.assertIn("non_field_errors", cm.exception.message_dict)
        self.assertTrue(any("Ya existe un acto llamado" in msg for msg in cm.exception.message_dict["non_field_errors"]))

        self.assertEqual(Acto.objects.filter(nombre=self.acto_no_papeleta_ok["nombre"]).count(), 1)



    def test_admin_crea_acto_nombre_con_espacios_duplicado_tras_strip_error(self):
        """
        Test: Nombre con espacios que al hacer strip coincide con otro -> error

        Given: Un usuario administrador y un acto ya existente en la base de datos con el nombre "Quinario".
        When: Se intenta crear un nuevo acto en la misma fecha pero con el nombre "  Quinario  " (con espacios adicionales).
        Then: El sistema debe aplicar el strip al nombre, detectar que coincide con el acto existente para ese día y lanzar una excepción 'ValidationError'.
        """
        nombre_base = "Quinario"
        Acto.objects.create(
            nombre=nombre_base,
            lugar="Parroquia",
            fecha=self.fecha_acto,
            tipo_acto=self.tipo_no_papeleta
        )

        datos_duplicado_espacios = self.acto_no_papeleta_ok.copy()
        datos_duplicado_espacios["nombre"] = f"   {nombre_base}   "
        datos_duplicado_espacios["fecha"] = self.fecha_acto

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_duplicado_espacios
            )

        self.assertIn("non_field_errors", cm.exception.message_dict)
        self.assertEqual(Acto.objects.filter(fecha__date=self.fecha_acto.date()).count(), 1)



    def test_admin_crea_acto_mismo_nombre_misma_fecha_distinta_hora_error(self):
        """
        Test: Caso borde: mismo nombre, misma fecha pero distinta hora -> ❌ también debe fallar

        Given: Un usuario administrador y un acto ya registrado en la base de datos para una fecha específica a las 10:00 AM.
        When: Se intenta crear un acto con el mismo nombre en la misma fecha (mismo día) pero a las 20:00 PM.
        Then: El sistema debe lanzar un 'ValidationError' debido a que la validación del servicio 
                compara por el día (fecha__date) y no permite duplicidad de nombre en la misma jornada.
        """
        fecha_manana = self.fecha_acto.replace(hour=10, minute=0)
        Acto.objects.create(
            nombre="Ensayo de Costaleros",
            lugar="Almacén",
            fecha=fecha_manana,
            tipo_acto=self.tipo_no_papeleta
        )

        fecha_tarde = self.fecha_acto.replace(hour=20, minute=0)
        datos_misma_fecha_tarde = self.acto_no_papeleta_ok.copy()
        datos_misma_fecha_tarde["nombre"] = "Ensayo de Costaleros"
        datos_misma_fecha_tarde["fecha"] = fecha_tarde

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_misma_fecha_tarde
            )

        self.assertIn("non_field_errors", cm.exception.message_dict)
        self.assertEqual(
            Acto.objects.filter(nombre="Ensayo de Costaleros", fecha__date=self.fecha_acto.date()).count(), 
            1
        )



    def test_acto_model_nombre_vacio_error(self):
        """
        Test: Nombre vacío ("" o "   ") -> error

        Given: Un diccionario de datos donde el nombre del acto es una cadena vacía o solo contiene espacios en blanco.
        When: Se intenta crear el acto llamando al servicio 'crear_acto_service', el cual gatilla el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que el nombre no puede estar vacío, impidiendo el registro en la base de datos.
        """
        datos_nombre_vacio = self.acto_no_papeleta_ok.copy()
        datos_nombre_vacio["nombre"] = "   "

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_nombre_vacio
            )

        self.assertIn("nombre", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_model_lugar_vacio_error(self):
        """
        Test: Lugar vacío -> error

        Given: Un usuario administrador y un payload donde el campo 'lugar' es una cadena vacía 
                o compuesta solo por espacios en blanco.
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el método 'full_clean()' del modelo.
        Then: El sistema debe lanzar un 'ValidationError' capturado desde la validación del modelo, 
                impidiendo que el acto se guarde sin una ubicación válida.
        """
        datos_lugar_vacio = self.acto_no_papeleta_ok.copy()
        datos_lugar_vacio["lugar"] = "   "

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_lugar_vacio
            )

        self.assertIn("lugar", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_model_tipo_acto_nulo_error(self):
        """
        Test: tipo_acto = None -> error

        Given: Un usuario administrador y un payload donde el campo 'tipo_acto' es None.
        When: Se invoca el servicio 'crear_acto_service', el cual intenta persistir el modelo Acto.
        Then: El sistema debe lanzar un 'ValidationError' indicando que el tipo de acto es obligatorio, 
                evitando la creación de un acto huérfano de categoría.
        """
        datos_sin_tipo = self.acto_no_papeleta_ok.copy()
        datos_sin_tipo["tipo_acto"] = None

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_sin_tipo
            )

        self.assertIn("tipo_acto", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_sin_papeleta_con_modalidad_error(self):
        """
        Test: Actos sin papeleta (requiere_papeleta=False), Se envía modalidad -> error

        Given: Un usuario administrador y un payload para un tipo de acto que no requiere papeleta 
                (requiere_papeleta=False), pero que erróneamente incluye una modalidad de reparto.
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en el campo 'modalidad', ya que un acto 
                sin papeleta no debe definir una lógica de reparto.
        """
        datos_invalidos = self.acto_no_papeleta_ok.copy()
        datos_invalidos["modalidad"] = Acto.ModalidadReparto.UNIFICADO

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_sin_papeleta_con_inicio_solicitud_error(self):
        """
        Test: Actos sin papeleta (requiere_papeleta=False), Se envía inicio_solicitud -> error

        Given: Un usuario administrador y un payload para un tipo de acto que no requiere papeleta, 
                pero que incluye una fecha de inicio de solicitud.
        When: Se invoca el servicio 'crear_acto_service', activando la validación del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que un acto que no requiere 
                papeleta no puede tener fechas de solicitud definidas.
        """
        datos_invalidos = self.acto_no_papeleta_ok.copy()
        datos_invalidos["inicio_solicitud"] = self.ahora + timedelta(days=1)

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_sin_papeleta_con_fin_solicitud_error(self):
        """
        Test: Actos sin papeleta (requiere_papeleta=False), Se envía fin_solicitud -> error

        Given: Un usuario administrador y un payload para un tipo de acto que no requiere papeleta, 
                proporcionando una fecha de fin de solicitud.
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El sistema debe lanzar un 'ValidationError' en el campo 'fin_solicitud', ya que si el 
                acto no requiere papeleta, no debe existir un periodo de solicitud.
        """
        datos_con_fin_erroneo = self.acto_no_papeleta_ok.copy()
        datos_con_fin_erroneo["fin_solicitud"] = self.ahora + timedelta(days=5)

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_con_fin_erroneo
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_sin_papeleta_con_fechas_cirios_error(self):
        """
        Test: Actos sin papeleta (requiere_papeleta=False), Se envía fechas de cirios -> error

        Given: Un usuario administrador y un payload para un acto que NO requiere papeleta,
                pero que incluye erróneamente fechas de inicio o fin de solicitud de cirios.
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en los campos de cirios, ya que un acto
                sin papeleta no debe tener ningún tipo de cronograma de solicitud.
        """
        datos_con_cirios_erroneos = self.acto_no_papeleta_ok.copy()
        datos_con_cirios_erroneos["inicio_solicitud_cirios"] = self.ahora + timedelta(days=2)
        datos_con_cirios_erroneos["fin_solicitud_cirios"] = self.ahora + timedelta(days=4)

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_con_cirios_erroneos
            )

        self.assertTrue(
            "inicio_solicitud_cirios" in cm.exception.message_dict or 
            "fin_solicitud_cirios" in cm.exception.message_dict
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_con_papeleta_sin_modalidad_error(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Falta de campos obligatorios, Sin modalidad -> error

        Given: Un usuario administrador y un payload para un acto que requiere papeleta, 
                pero omitiendo el campo 'modalidad' (enviándolo como None).
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en el campo 'modalidad', ya que si el 
                acto requiere papeleta, es obligatorio definir si el reparto es unificado o tradicional.
        """
        datos_sin_modalidad = {
            "nombre": "Salida Procesional",
            "lugar": "Catedral",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": None,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_sin_modalidad
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_con_papeleta_sin_inicio_solicitud_error(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Falta de campos obligatorios, Sin inicio_solicitud -> error

        Given: Un usuario administrador y un payload para un acto que requiere papeleta, 
                pero omitiendo la fecha de 'inicio_solicitud' (enviándola como None).
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en el campo 'inicio_solicitud', ya que 
                todo acto con papeleta debe tener definido al menos el periodo principal de solicitud.
        """
        datos_sin_inicio = {
            "nombre": "Traslado",
            "lugar": "Capilla",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": None,
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_sin_inicio
            )

        self.assertIn("inicio_solicitud", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_con_papeleta_sin_fin_solicitud_error(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Falta de campos obligatorios, Sin fin_solicitud -> error

        Given: Un usuario administrador y un payload para un acto que requiere papeleta, 
                pero omitiendo la fecha de 'fin_solicitud' (enviándola como None).
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en el campo 'fin_solicitud', ya que es 
                imprescindible marcar el límite temporal para las solicitudes de insignias.
        """
        datos_sin_fin = {
            "nombre": "Solemne Quinario",
            "lugar": "Parroquia",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": None,
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_sin_fin
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_con_papeleta_inicio_solicitud_mayor_o_igual_que_fin_error(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Orden de fechas incorrecto, 
                inicio_solicitud >= fin_solicitud -> error

        Given: Un usuario administrador y un payload para un acto con papeleta donde la fecha 
                de inicio de solicitud es posterior o igual a la fecha de fin de solicitud.
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que el rango de fechas es 
                inválido. Se verifica que el error esté vinculado al campo 'fin_solicitud'.
        """
        datos_fechas_invalidas = {
            "nombre": "Ensayo Real",
            "lugar": "Casa Hermandad",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=10),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_fechas_invalidas
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud"][0], 
            "El fin de solicitud debe ser posterior al inicio."
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_con_papeleta_inicio_solicitud_mayor_o_igual_que_fecha_error(self):
        """
        Test: Actos con papeleta (requiere_papeleta=True), Orden de fechas incorrecto, 
                inicio_solicitud >= fecha -> error

        Given: Un usuario administrador y un payload para un acto con papeleta donde la fecha 
                de inicio de solicitud es igual o posterior a la fecha de celebración del acto.
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que el periodo de solicitud 
                no puede comenzar después de que el evento haya tenido lugar.
        """
        fecha_celebracion = self.ahora + timedelta(days=5)
        datos_inicio_tras_acto = {
            "nombre": "Salida Extraordinaria",
            "lugar": "Centro Ciudad",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": fecha_celebracion + timedelta(days=1),
            "fin_solicitud": fecha_celebracion + timedelta(days=2),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_inicio_tras_acto
            )

        self.assertIn("inicio_solicitud", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_con_papeleta_fin_solicitud_mayor_que_fecha_error(self):
        """
        Test: fin_solicitud > fecha -> error

        Given: Un usuario administrador y un payload para un acto con papeleta donde el periodo 
                de solicitud finaliza después de la fecha de celebración del acto.
        When: Se invoca el servicio 'crear_acto_service', el cual ejecuta el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que no se puede cerrar un plazo 
                de solicitud después de que el evento haya ocurrido.
        """
        fecha_celebracion = self.ahora + timedelta(days=5)
        datos_fin_tras_acto = {
            "nombre": "Traslado Extraordinario",
            "lugar": "Parroquia",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": fecha_celebracion + timedelta(days=1),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_fin_tras_acto
            )

        self.assertTrue(
            "fin_solicitud" in cm.exception.message_dict or 
            "fecha" in cm.exception.message_dict
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_sin_inicio_solicitud_cirios_error(self):
        """
        Test: Modalidad TRADICIONAL, Campos obligatorios, Sin inicio_solicitud_cirios -> error

        Given: Un usuario administrador y un payload para un acto con modalidad TRADICIONAL,
                pero omitiendo la fecha de 'inicio_solicitud_cirios'.
        When: Se invoca el servicio 'crear_acto_service', activando la validación del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en el campo 'inicio_solicitud_cirios', 
                ya que la modalidad tradicional requiere obligatoriamente un periodo para cirios.
        """
        datos_tradicional_sin_cirios = {
            "nombre": "Estación de Penitencia",
            "lugar": "S.I. Catedral",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": self.ahora + timedelta(days=10),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_tradicional_sin_cirios
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_sin_fin_solicitud_cirios_error(self):
        """
        Test: Modalidad TRADICIONAL, Campos obligatorios, Sin fin_solicitud_cirios -> error

        Given: Un usuario administrador y un payload para un acto con modalidad TRADICIONAL,
                pero omitiendo la fecha de 'fin_solicitud_cirios' (enviándola como None).
        When: Se invoca el servicio 'crear_acto_service', activando la validación del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en el campo 'fin_solicitud_cirios', 
                ya que la modalidad tradicional exige definir el cierre del periodo de cirios.
        """
        datos_tradicional_sin_fin_cirios = {
            "nombre": "Salida Procesional Tradicional",
            "lugar": "Centro",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": None,
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_tradicional_sin_fin_cirios
            )

        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_inicio_solicitud_cirios_mayor_o_igual_que_fin_error(self):
        """
        Test: Modalidad TRADICIONAL, Orden incorrecto, 
                inicio_solicitud_cirios >= fin_solicitud_cirios -> error

        Given: Un usuario administrador y un payload para un acto tradicional donde la fecha 
                de inicio de solicitud de cirios es posterior a la de fin.
        When: Se invoca el servicio 'crear_acto_service', activando el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError'. Se verifica que el error se asocie 
                al campo 'fin_solicitud_cirios' por coherencia con las validaciones de fechas previas.
        """
        datos_fechas_cirios_invalidas = {
            "nombre": "Vía Crucis Tradicional",
            "lugar": "Barrio",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=10),
            "fin_solicitud_cirios": self.ahora + timedelta(days=6),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_fechas_cirios_invalidas
            )

        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_inicio_solicitud_cirios_mayor_o_igual_que_fecha_error(self):
        """
        Test: Modalidad TRADICIONAL, Orden incorrecto, 
                inicio_solicitud_cirios >= fecha -> error

        Given: Un usuario administrador y un payload para un acto tradicional donde la fecha 
                de inicio de solicitud de cirios es posterior a la celebración del acto.
        When: Se invoca el servicio 'crear_acto_service', activando la validación del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que no se pueden solicitar 
                cirios para un evento que ya ha ocurrido o está ocurriendo.
        """
        fecha_celebracion = self.ahora + timedelta(days=10)
        datos_cirios_tras_acto = {
            "nombre": "Procesión de Gloria",
            "lugar": "Centro Histórico",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": fecha_celebracion + timedelta(days=1),
            "fin_solicitud_cirios": fecha_celebracion + timedelta(days=2),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_cirios_tras_acto
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_fin_solicitud_cirios_mayor_que_fecha_error(self):
        """
        Test: Modalidad TRADICIONAL, Orden incorrecto, 
                fin_solicitud_cirios > fecha -> error

        Given: Un usuario administrador y un payload para un acto tradicional donde el fin de 
                la solicitud de cirios se extiende más allá de la fecha del propio acto.
        When: Se invoca el servicio 'crear_acto_service', activando el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' en el campo 'fin_solicitud_cirios', 
                impidiendo que el plazo de cirios termine después de la celebración.
        """
        fecha_celebracion = self.ahora + timedelta(days=10)
        datos_fin_cirios_tardio = {
            "nombre": "Salida Procesional",
            "lugar": "Centro",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": fecha_celebracion + timedelta(days=1),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_fin_cirios_tardio
            )

        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_solapamiento_fases_error(self):
        """
        Test: Orden entre fases, fin_solicitud >= inicio_solicitud_cirios -> error

        Given: Un usuario administrador y un payload para un acto tradicional donde el periodo 
                de solicitud de insignias se solapa con el inicio de la solicitud de cirios.
        When: Se invoca el servicio 'crear_acto_service', activando el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que las fases deben ser 
                consecutivas y no pueden solaparse (el fin de una debe ser anterior al inicio de la siguiente).
        """
        fecha_fin_insignias = self.ahora + timedelta(days=5)
        fecha_inicio_cirios = fecha_fin_insignias

        datos_fases_solapadas = {
            "nombre": "Estación de Penitencia",
            "lugar": "S.I. Catedral",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": fecha_fin_insignias,
            "inicio_solicitud_cirios": fecha_inicio_cirios,
            "fin_solicitud_cirios": fecha_inicio_cirios + timedelta(days=2),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_fases_solapadas
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_secuencia_fechas_mezclada_error(self):
        """
        Test: Secuencia incorrecta (mezclada) -> error

        Given: Un usuario administrador y un payload para un acto tradicional con una cronología 
                totalmente ilógica (ej. la solicitud de cirios empieza antes que la de insignias).
        When: Se invoca el servicio 'crear_acto_service', activando el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' al detectar que la secuencia temporal 
                de las fases de solicitud no es lineal ni coherente.
        """
        fecha_celebracion = self.ahora + timedelta(days=20)

        datos_secuencia_invertida = {
            "nombre": "Procesión Magna",
            "lugar": "Centro Ciudad",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=6),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=1),
            "fin_solicitud_cirios": self.ahora + timedelta(days=5),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_secuencia_invertida
            )

        self.assertTrue(
            "inicio_solicitud_cirios" in cm.exception.message_dict or 
            "non_field_errors" in cm.exception.message_dict
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_tradicional_fecha_ejecucion_cirios_sin_ejecucion_reparto_error(self):
        """
        Test: Ejecución inválida, fecha_ejecucion_cirios definida sin fecha_ejecucion_reparto -> error

        Given: Un usuario administrador y un payload para un acto con modalidad TRADICIONAL que 
                tiene definida una 'fecha_ejecucion_cirios' pero carece de 'fecha_ejecucion_reparto'.
        When: Se invoca el servicio 'crear_acto_service', activando el 'full_clean()' del modelo.
        Then: El modelo debe lanzar un 'ValidationError' indicando que no puede existir una ejecución 
                de cirios (segunda fase) si no se ha definido primero la ejecución del reparto de insignias.
        """
        datos_ejecucion_incompleta = {
            "nombre": "Estación de Penitencia",
            "lugar": "S.I. Catedral",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": self.ahora + timedelta(days=10),
            "fecha_ejecucion_reparto": None,
            "fecha_ejecucion_cirios": self.ahora + timedelta(days=11),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_ejecucion_incompleta
            )

        self.assertIn("fecha_ejecucion_cirios", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_modalidad_unificado_con_fechas_cirios_error(self):
        """
        Test: Modalidad UNIFICADO, Se envían fechas de cirios -> error
        
        Ubicación del error en el modelo: bloque 'elif self.modalidad == self.ModalidadReparto.UNIFICADO'
        asociando el mensaje a la clave 'modalidad'.
        """
        datos_unificado_con_cirios = {
            "nombre": "Traslado Unificado",
            "lugar": "Capilla",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": self.ahora + timedelta(days=10),
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_unificado_con_cirios
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["modalidad"][0], 
            "En modalidad UNIFICADO no se deben definir fechas de cirios."
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_serializer_imagen_demasiado_grande_error(self):
        """
        Test: Validación del serializer (imagen), Tamaño, Imagen > 5MB -> error

        Given: Un payload para crear un acto que incluye una imagen cuyo peso 
                excede el límite de 5MB (simulado con un archivo de 6MB).
        When: Se instancia el 'ActoCreateSerializer' y se ejecuta 'is_valid()'.
        Then: El serializador debe devolver False y el diccionario de errores debe 
                contener el campo 'imagen_portada' con el mensaje de límite excedido.
        """
        contenido_pesado = b"0" * (6 * 1024 * 1024)
        imagen_grande = SimpleUploadedFile(
            name='imagen_pesada.jpg',
            content=contenido_pesado,
            content_type='image/jpeg'
        )

        datos_con_imagen_pesada = {
            "nombre": "Acto con imagen pesada",
            "lugar": "Sede Social",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "imagen_portada": imagen_grande
        }

        serializer = ActoCreateSerializer(data=datos_con_imagen_pesada)

        self.assertFalse(serializer.is_valid(), "El serializador debería ser inválido para archivos > 5MB")
        self.assertIn("imagen_portada", serializer.errors)

        error_msg = str(serializer.errors["imagen_portada"][0])
        self.assertIn("La imagen es demasiado grande", error_msg)
        self.assertIn("5MB", error_msg)



    def test_acto_serializer_extension_no_permitida_error(self):
        """
        Test: Validación del serializer (imagen), Extensión, Archivo .gif -> error

        Given: Un usuario administrador y un payload para crear un acto que incluye 
                una imagen con extensión '.gif'.
        When: Se valida la información a través del serializador 'ActoCreateSerializer'.
        Then: El serializador debe ser inválido y devolver un error en el campo 
                'imagen_portada' indicando que solo se admiten JPG, JPEG o PNG.
        """
        archivo_gif = SimpleUploadedFile(
            name='test_imagen.gif',
            content=b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/gif'
        )

        datos_con_gif = {
            "nombre": "Acto con GIF",
            "lugar": "Lugar de prueba",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "imagen_portada": archivo_gif
        }

        serializer = ActoCreateSerializer(data=datos_con_gif)

        self.assertFalse(serializer.is_valid())
        self.assertIn("imagen_portada", serializer.errors)

        error_msg = str(serializer.errors["imagen_portada"][0])
        self.assertIn("Formato de archivo no permitido", error_msg)
        self.assertIn(".gif", error_msg)



    def test_acto_serializer_extension_bmp_no_permitida_error(self):
        """
        Test: Validación del serializer (imagen), Extensión, Archivo .bmp -> error

        Given: Un payload para crear un acto que incluye un archivo con extensión '.bmp'.
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe fallar la validación, indicando que el formato 
                no está entre los admitidos (JPG, JPEG, PNG).
        """
        archivo_bmp = SimpleUploadedFile(
            name='portada_acto.bmp',
            content=b'BM\x36\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00',
            content_type='image/bmp'
        )

        datos_con_bmp = {
            "nombre": "Acto con formato BMP",
            "lugar": "Parroquia",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "imagen_portada": archivo_bmp
        }

        serializer = ActoCreateSerializer(data=datos_con_bmp)

        self.assertFalse(serializer.is_valid(), "El serializador no debería aceptar archivos .bmp")
        self.assertIn("imagen_portada", serializer.errors)

        error_msg = str(serializer.errors["imagen_portada"][0])
        self.assertIn("Formato de archivo no permitido", error_msg)
        self.assertIn(".bmp", error_msg)
        self.assertIn("Solo se admiten imágenes JPG, JPEG o PNG", error_msg)



    def test_acto_serializer_archivo_sin_extension_error(self):
        """
        Test: Validación del serializer (imagen), Extensión, Archivo sin extensión -> error

        Given: Un payload para crear un acto que incluye un archivo de imagen 
                válido en contenido pero cuyo nombre no tiene extensión (ej. 'portada').
        When: El serializador intenta extraer la extensión para validarla.
        Then: El serializador debe fallar indicando que el formato no es permitido 
                o que solo se admiten JPG, JPEG o PNG.
        """
        archivo_sin_ext = SimpleUploadedFile(
            name='archivo_sin_extension',
            content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdcG\x01\x00\x00\x00\x00IEND\xaeB`\x82',
            content_type='image/png'
        )

        datos_sin_extension = {
            "nombre": "Acto Nombre Incompleto",
            "lugar": "Sede Social",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "imagen_portada": archivo_sin_ext
        }

        serializer = ActoCreateSerializer(data=datos_sin_extension)

        self.assertFalse(serializer.is_valid(), "El serializador debe rechazar archivos sin extensión")
        self.assertIn("imagen_portada", serializer.errors)

        error_msg = str(serializer.errors["imagen_portada"][0])
        self.assertIn("Formato de archivo no permitido", error_msg)
        self.assertIn("Solo se admiten imágenes JPG, JPEG o PNG", error_msg)



    def test_acto_serializer_contenido_falso_error(self):
        """
        Test: Validación del serializer (imagen), Formato real, 
                Archivo con extensión .jpg pero contenido no imagen -> error

        Given: Un payload que incluye un archivo llamado 'foto.jpg' pero cuyo 
                contenido real es texto plano (no una estructura de imagen válida).
        When: El serializador intenta abrir la imagen con PIL en 'validate_imagen_portada'.
        Then: Debe capturarse la excepción y lanzar un 'serializers.ValidationError' 
                indicando que el archivo no es una imagen válida o está dañado.
        """
        contenido_falso = b"Esto no es una imagen, es un archivo de texto malintencionado."
        archivo_falso = SimpleUploadedFile(
            name='intruso.jpg',
            content=contenido_falso,
            content_type='image/jpeg'
        )

        datos_con_contenido_falso = {
            "nombre": "Acto con Imagen Falsa",
            "lugar": "Sede",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "imagen_portada": archivo_falso
        }

        serializer = ActoCreateSerializer(data=datos_con_contenido_falso)

        self.assertFalse(serializer.is_valid())
        self.assertIn("imagen_portada", serializer.errors)

        error_msg = str(serializer.errors["imagen_portada"][0])
        self.assertEqual(error_msg, "El archivo subido no es una imagen válida o está dañado.")



    def test_acto_serializer_archivo_corrupto_error(self):
        """
        Test: Validación del serializer (imagen), Formato real, Archivo corrupto -> error

        Given: Un payload con un archivo que tiene una cabecera de imagen válida 
                pero el resto del contenido está dañado o incompleto.
        When: El serializador intenta validar la integridad de la imagen mediante PIL.
        Then: El serializador debe capturar el error de procesamiento y devolver un 
                'ValidationError' indicando que la imagen está dañada.
        """
        contenido_corrupto = b"\xff\xd8\xff\xe0" + b"basura" * 10
        archivo_corrupto = SimpleUploadedFile(
            name='imagen_danada.jpg',
            content=contenido_corrupto,
            content_type='image/jpeg'
        )

        datos_con_archivo_corrupto = {
            "nombre": "Acto Imagen Corrupta",
            "lugar": "Casa Hermandad",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "imagen_portada": archivo_corrupto
        }

        serializer = ActoCreateSerializer(data=datos_con_archivo_corrupto)

        self.assertFalse(serializer.is_valid(), "El serializador no debe validar una imagen corrupta")
        self.assertIn("imagen_portada", serializer.errors)

        error_msg = str(serializer.errors["imagen_portada"][0])
        self.assertEqual(error_msg, "El archivo subido no es una imagen válida o está dañado.")



    def test_acto_serializer_dimensiones_excesivas_error(self):
        """
        Test: Validación del serializer (imagen), Dimensiones, Imagen > 4000x4000 -> error

        Given: Un payload con una imagen válida (PNG) pero con dimensiones de 4001x4001 píxeles.
        When: El serializador valida el ancho y alto en 'validate_imagen_portada'.
        Then: El serializador debe fallar indicando que las dimensiones exceden el máximo 
                permitido de 4000x4000 píxeles.
        """
        ancho_excesivo, alto_excesivo = 4001, 4001
        img_byte_arr = io.BytesIO()
        img = Image.new('RGB', (ancho_excesivo, alto_excesivo), color='red')
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        imagen_gigante = SimpleUploadedFile(
            name='foto_gigante.png',
            content=img_byte_arr.getvalue(),
            content_type='image/png'
        )

        datos_dimensiones_invalidas = {
            "nombre": "Acto con Imagen Enorme",
            "lugar": "Exterior",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "imagen_portada": imagen_gigante
        }

        serializer = ActoCreateSerializer(data=datos_dimensiones_invalidas)

        self.assertFalse(serializer.is_valid())
        self.assertIn("imagen_portada", serializer.errors)

        error_msg = str(serializer.errors["imagen_portada"][0])
        self.assertIn("Las dimensiones de la imagen son demasiado grandes", error_msg)
        self.assertIn("4001x4001", error_msg)
        self.assertIn("El máximo permitido es 4000x4000 píxeles", error_msg)



    def test_acto_serializer_fecha_formato_invalido_error(self):
        """
        Test: Datos inválidos generales, fecha no es datetime -> error

        Given: Un payload para crear un acto donde el campo 'fecha' contiene 
                un valor que no representa una fecha (un string aleatorio).
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe fallar la validación y devolver un error en el 
                campo 'fecha' indicando que el formato de fecha es incorrecto.
        """
        datos_fecha_corrupta = {
            "nombre": "Acto con Fecha Inválida",
            "lugar": "Plaza Mayor",
            "fecha": "esto-no-es-una-fecha",
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_fecha_corrupta)

        self.assertFalse(serializer.is_valid(), "El serializador no debe aceptar strings aleatorios como fecha")
        self.assertIn("fecha", serializer.errors)

        error_msg = str(serializer.errors["fecha"][0])
        self.assertTrue(len(error_msg) > 0)



    def test_acto_serializer_tipo_acto_no_existe_error(self):
        """
        Test: Datos inválidos generales, tipo_acto no existe en BD -> error

        Given: Un payload para crear un acto donde el 'tipo_acto' es un valor 
                que no está registrado previamente en la base de datos.
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe ser inválido y el error debe indicar que 
                el objeto con ese identificador (slug) no existe.
        """
        datos_tipo_inexistente = {
            "nombre": "Evento Fantasma",
            "lugar": "Desconocido",
            "fecha": self.fecha_acto,
            "tipo_acto": "TIPO_QUE_NO_EXISTE",
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_tipo_inexistente)

        self.assertFalse(serializer.is_valid(), "El serializador no debe aceptar tipos de acto inexistentes")
        self.assertIn("tipo_acto", serializer.errors)

        error_msg = str(serializer.errors["tipo_acto"][0]).lower()

        self.assertTrue(
            "no existe" in error_msg or "does not exist" in error_msg,
            f"El mensaje de error no indica que el objeto no existe: {error_msg}"
        )

        self.assertIn("tipo_que_no_existe", error_msg)



    def test_acto_serializer_modalidad_valor_no_permitido_error(self):
        """
        Test: Datos inválidos generales, modalidad con valor no permitido -> error

        Given: Un payload donde el campo 'modalidad' contiene un valor que no 
                pertenece a las opciones 'TRADICIONAL' o 'UNIFICADO'.
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe fallar la validación indicando que el valor 
                enviado no es una opción válida.
        """
        datos_modalidad_invalida = {
            "nombre": "Acto con Modalidad Rara",
            "lugar": "Sede",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": "MODALIDAD_INVENTADA",
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_modalidad_invalida)

        self.assertFalse(serializer.is_valid(), "El serializador debe rechazar modalidades no definidas en TextChoices")
        self.assertIn("modalidad", serializer.errors)

        error_msg = str(serializer.errors["modalidad"][0]).lower()

        self.assertTrue(
            "no es una opción válida" in error_msg or "is not a valid choice" in error_msg,
            f"El mensaje de error no indica una opción inválida: {error_msg}"
        )

        self.assertIn("modalidad_inventada", error_msg)



    def test_acto_serializer_nombre_none_error(self):
        """
        Test: Casos edge, Nombre None -> debería fallar (campo requerido)

        Given: Un payload para crear un acto donde el campo 'nombre' es None.
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe ser inválido y devolver un error indicando 
                que este campo no puede ser nulo o es requerido.
        """
        datos_nombre_none = {
            "nombre": None,
            "lugar": "Lugar válido",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_nombre_none)

        self.assertFalse(serializer.is_valid(), "El serializador debe rechazar un nombre nulo")
        self.assertIn("nombre", serializer.errors)

        error_msg = str(serializer.errors["nombre"][0]).lower()
        self.assertTrue(
            "no puede ser nulo" in error_msg or "may not be null" in error_msg,
            f"El mensaje de error no indica que el campo es nulo: {error_msg}"
        )



    def test_acto_serializer_lugar_none_error(self):
        """
        Test: Casos edge, Lugar None -> debería fallar

        Given: Un payload para crear un acto donde el campo 'lugar' es enviado como None.
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe fallar la validación y devolver un error en el 
                campo 'lugar' indicando que no puede ser nulo.
        """
        datos_lugar_none = {
            "nombre": "Acto Válido",
            "lugar": None,
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_lugar_none)

        self.assertFalse(serializer.is_valid(), "El serializador debe rechazar un lugar nulo")
        self.assertIn("lugar", serializer.errors)

        error_msg = str(serializer.errors["lugar"][0]).lower()
        self.assertTrue(
            "no puede ser nulo" in error_msg or "may not be null" in error_msg,
            f"El mensaje de error no es el esperado: {error_msg}"
        )



    def test_acto_serializer_fecha_en_pasado_error(self):
        """
        Test: Casos edge, Fecha en pasado -> error

        Given: Un payload para crear un acto con una fecha de celebración 
                anterior al momento actual (ayer).
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe fallar la validación y devolver un error en el 
                campo 'fecha' indicando que no puede ser anterior a la actual.
        """
        fecha_pasada = timezone.now() - timedelta(days=1)

        datos_pasados = {
            "nombre": "Acto Antiguo",
            "lugar": "Sede Social",
            "fecha": fecha_pasada,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": fecha_pasada - timedelta(days=10),
            "fin_solicitud": fecha_pasada - timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_pasados)

        self.assertFalse(serializer.is_valid(), "El serializador debería rechazar fechas en el pasado.")
        self.assertIn("fecha", serializer.errors)

        error_msg = str(serializer.errors["fecha"][0])
        self.assertEqual(error_msg, "La fecha del acto no puede ser anterior a la actual.")



    def test_acto_fechas_solicitud_identicas_error(self):
        """
        Test: Fechas exactamente iguales, inicio_solicitud == fin_solicitud -> error

        Given: Un payload donde la fecha de inicio y fin de solicitud son el mismo instante.
        When: Se invoca el servicio 'crear_acto_service' disparando la validación del modelo.
        Then: Debe lanzar un 'ValidationError' en el campo 'fin_solicitud' indicando 
                que el fin debe ser posterior al inicio.
        """
        instante_identico = self.ahora + timedelta(days=2)

        datos_fechas_iguales = {
            "nombre": "Acto Error Fechas",
            "lugar": "Parroquia",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": instante_identico,
            "fin_solicitud": instante_identico,
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_fechas_iguales
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud"][0],
            "El fin de solicitud debe ser posterior al inicio."
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_fin_solicitud_igual_a_fecha_error(self):
        """
        Test: fin_solicitud == fecha -> error

        Given: Un payload donde el 'fin_solicitud' coincide exactamente con 
                la 'fecha' de celebración del acto.
        When: Se invoca el servicio 'crear_acto_service'.
        Then: Debe lanzar un 'ValidationError' indicando que el fin de solicitud 
                no puede ser posterior (incluyendo igualdad) a la fecha del acto.
        """
        instante_acto = self.fecha_acto 

        datos_limite_iguales = {
            "nombre": "Acto Límite Prohibido",
            "lugar": "Catedral",
            "fecha": instante_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": instante_acto - timedelta(days=5),
            "fin_solicitud": instante_acto,
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_limite_iguales
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud"][0],
            "El fin de solicitud no puede ser posterior a la fecha del acto."
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_acto_serializer_nombre_demasiado_largo_error(self):
        """
        Test: Strings extremadamente largos, Nombre > 100 caracteres -> error

        Given: Un payload donde el nombre del acto tiene 101 caracteres, 
                superando el 'max_length=100' definido en el modelo.
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe fallar indicando que el texto es demasiado largo.
        """
        nombre_muy_largo = "A" * 101

        datos_nombre_largo = {
            "nombre": nombre_muy_largo,
            "lugar": "Lugar válido",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_nombre_largo)

        self.assertFalse(serializer.is_valid(), "El serializador debe rechazar nombres que excedan max_length")
        self.assertIn("nombre", serializer.errors)

        error_msg = str(serializer.errors["nombre"][0]).lower()
        self.assertTrue(
            "100" in error_msg and ("caracteres" in error_msg or "characters" in error_msg),
            f"El mensaje de error no menciona el límite de caracteres: {error_msg}"
        )

    def test_acto_serializer_lugar_demasiado_largo_error(self):
        """
        Test: Strings extremadamente largos, Lugar > 200 caracteres -> error

        Given: Un payload donde el lugar de celebración tiene 201 caracteres.
        When: Se procesan los datos a través del 'ActoCreateSerializer'.
        Then: El serializador debe fallar indicando que el límite es de 200.
        """
        lugar_muy_largo = "B" * 201

        datos_lugar_largo = {
            "nombre": "Acto Válido",
            "lugar": lugar_muy_largo,
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta.tipo,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        serializer = ActoCreateSerializer(data=datos_lugar_largo)

        self.assertFalse(serializer.is_valid())
        self.assertIn("lugar", serializer.errors)
        
        error_msg = str(serializer.errors["lugar"][0]).lower()
        self.assertIn("200", error_msg)



    def test_crear_acto_atomicidad_ante_error_validacion(self):
        """
        Test: Integridad y atomicidad, Error en validación -> NO se crea ningún acto

        Given: Un usuario administrador y un payload que contiene un error de 
                validación (ej: nombre vacío).
        When: Se invoca el servicio 'crear_acto_service'.
        Then: El servicio debe lanzar un 'ValidationError' y la base de datos 
                debe confirmar que no se ha persistido el objeto (count == 0).
        """
        datos_invalidos = {
            "nombre": "   ",
            "lugar": "Sede Social",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
        }

        with self.assertRaises(DjangoValidationError):
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertEqual(
            Acto.objects.count(), 
            0, 
            "La base de datos debería estar vacía debido al rollback de la transacción."
        )



    def test_crear_acto_rollback_por_error_en_clean_modelo(self):
        """
        Test: Error en clean() -> rollback completo

        Given: Un payload con datos válidos para la base de datos, pero que 
                violan la lógica de negocio (ej: modalidad UNIFICADO con fechas de cirios).
        When: Se invoca el servicio 'crear_acto_service', el cual llama a .create() 
                y este a su vez ejecuta el clean() del modelo.
        Then: Se debe lanzar un 'ValidationError', y no debe quedar rastro del 
                acto en la base de datos.
        """
        datos_conflicto_logico = {
            "nombre": "Acto Transacción Fallida",
            "lugar": "Iglesia",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": self.ahora + timedelta(days=10),
        }

        with self.assertRaises(DjangoValidationError):
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_conflicto_logico
            )

        existe_acto = Acto.objects.filter(nombre="Acto Transacción Fallida").exists()
        self.assertFalse(
            existe_acto, 
            "El acto no debería existir. El error en clean() debe provocar un rollback total."
        )
        self.assertEqual(Acto.objects.count(), 0)