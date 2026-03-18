from zoneinfo import ZoneInfo
import concurrent.futures

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

import pytz
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError

from api.serializers import ActoSerializer, PapeletaSitioSerializer
from api.servicios.acto.acto_service import crear_acto_service

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



    def test_admin_crea_acto_correctamente(self):
        """
        Test: Usuario administrador crea un acto correctamente

        Given: Un usuario con privilegios de administrador (esAdmin=True) y datos válidos para un nuevo acto.
        When: El administrador invoca el servicio de creación de actos.
        Then: El acto se crea exitosamente en la base de datos y la función retorna la nueva instancia.
        """
        datos_acto = self.acto_no_papeleta_ok.copy()

        self.assertEqual(Acto.objects.count(), 0)

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin, 
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.nombre, datos_acto["nombre"])
        self.assertEqual(Acto.objects.count(), 1)



    def test_admin_crear_varios_actos_consecutivos_ok(self):
        """
        Test: Usuario administrador crea varios actos consecutivos

        Given: Un usuario administrador y una lista de datos para diferentes actos válidos.
        When: Se invoca el servicio de creación de actos múltiples veces de forma secuencial.
        Then: El sistema debe crear cada acto correctamente, incrementando el total de registros en la base de datos.
        """
        actos_a_crear = [
            self.acto_no_papeleta_ok.copy(),
            self.acto_tradicional_ok.copy(),
            self.acto_unificado_ok.copy()
        ]

        actos_a_crear[0]["nombre"] = "Acto 1 - Convivencia"
        actos_a_crear[1]["nombre"] = "Acto 2 - Salida"
        actos_a_crear[2]["nombre"] = "Acto 3 - Cabildo"

        for data in actos_a_crear:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=data
            )

        self.assertEqual(Acto.objects.count(), 3)
        self.assertTrue(Acto.objects.filter(nombre="Acto 1 - Convivencia").exists())
        self.assertTrue(Acto.objects.filter(nombre="Acto 2 - Salida").exists())
        self.assertTrue(Acto.objects.filter(nombre="Acto 3 - Cabildo").exists())



    def test_admin_crea_acto_con_todos_los_campos_ok(self):
        """
        Test: Usuario administrador crea un acto con todos los campos opcionales rellenados

        Given: Un usuario administrador y un diccionario de datos que contiene tanto los campos obligatorios 
            como todos los opcionales (descripción, fechas de solicitud de cirios, modalidad).
        When: Se invoca el servicio de creación.
        Then: El acto se crea correctamente y se verifica que los campos opcionales se han persistido con los valores esperados.
        """
        datos_completos = self.acto_tradicional_ok.copy()

        datos_completos["descripcion"] = "Descripción detallada del acto con todos sus campos"

        acto_creado = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_completos
        )

        self.assertEqual(acto_creado.nombre, datos_completos["nombre"])
        self.assertEqual(acto_creado.descripcion, "Descripción detallada del acto con todos sus campos")
        self.assertEqual(acto_creado.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(acto_creado.inicio_solicitud_cirios, self.inicio_cirios)
        self.assertEqual(acto_creado.fin_solicitud_cirios, self.fin_cirios)

        self.assertEqual(acto_creado.tipo_acto.tipo, TipoActo.OpcionesTipo.ESTACION_PENITENCIA)
        self.assertTrue(acto_creado.tipo_acto.requiere_papeleta)



    def test_admin_crea_acto_con_campos_opcionales_vacios_ok(self):
        """
        Test: Usuario administrador crea un acto con campos opcionales vacíos

        Given: Un usuario administrador y un conjunto de datos donde los campos opcionales 
            (como descripción o modalidad en ciertos casos) son None o están ausentes.
        When: Se invoca el servicio de creación.
        Then: El acto se crea exitosamente, persistiendo los campos vacíos como valores nulos en la base de datos.
        """
        datos_vacios = self.acto_no_papeleta_ok.copy()

        datos_vacios["descripcion"] = None

        self.assertIsNone(datos_vacios.get("inicio_solicitud"))
        self.assertIsNone(datos_vacios.get("modalidad"))

        acto_creado = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_vacios
        )

        self.assertIsNotNone(acto_creado.id)
        self.assertEqual(acto_creado.nombre, datos_vacios["nombre"])

        self.assertIsNone(acto_creado.descripcion)
        self.assertIsNone(acto_creado.modalidad)
        self.assertIsNone(acto_creado.inicio_solicitud)
        self.assertIsNone(acto_creado.fin_solicitud_cirios)



    def test_usuario_no_admin_intenta_crear_acto_error(self):
        """
        Test: Usuario no administrador intenta crear un acto

        Given: Un usuario sin privilegios de administrador (esAdmin=False).
        When: El usuario intenta invocar el servicio de creación de actos.
        Then: El sistema debe denegar el acceso lanzando una excepción PermissionDenied.
        """
        datos_acto = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(
                usuario_solicitante=self.hermano,
                data_validada=datos_acto
            )

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_usuario_sin_atributo_es_admin_intenta_crear_acto_error(self):
        """
        Test: Usuario sin el atributo 'esAdmin' intenta crear un acto

        Given: Un objeto de usuario que carece por completo del atributo 'esAdmin'.
        When: Se invoca el servicio de creación de actos.
        Then: El sistema debe manejar la ausencia del atributo como un 'False' por defecto y lanzar PermissionDenied.
        """
        usuario_sin_atributo = User(username="test_simple", email="simple@test.com")
        
        datos_acto = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(
                usuario_solicitante=usuario_sin_atributo,
                data_validada=datos_acto
            )

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_usuario_none_intenta_crear_acto_error(self):
        """
        Test: Usuario None o no proporcionado intenta crear un acto

        Given: Un valor None en lugar de un objeto de usuario válido.
        When: Se invoca el servicio de creación de actos.
        Then: El sistema debe lanzar una excepción (PermissionDenied) al no poder verificar los privilegios de administrador.
        """
        datos_acto = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(
                usuario_solicitante=None,
                data_validada=datos_acto
            )

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_usuario_junta_gobierno_sin_es_admin_intenta_crear_acto_error(self):
        """
        Test: Usuario de la Junta de Gobierno sin flag esAdmin intenta crear un acto

        Given: Un usuario que pertenece al cuerpo de 'Junta de Gobierno' pero tiene esAdmin=False.
        When: El usuario intenta invocar el servicio de creación de actos.
        Then: El sistema debe denegar el acceso lanzando PermissionDenied, ya que el servicio solo valida el atributo esAdmin.
        """
        cuerpo_junta, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=cuerpo_junta,
            anio_ingreso=2024
        )

        self.hermano.esAdmin = False
        self.hermano.save()

        datos_acto = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(
                usuario_solicitante=self.hermano,
                data_validada=datos_acto
            )

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_mismo_nombre_fecha_diferente_ok(self):
        """
        Test: Crear acto con mismo nombre pero fecha diferente

        Given: Un acto ya existente en la base de datos con un nombre específico.
        When: Un administrador intenta crear otro acto con el mismo nombre pero en una fecha distinta.
        Then: El sistema permite la creación, ya que la restricción de duplicidad solo aplica si coinciden nombre y día.
        """
        fecha_primero = self.ahora + timedelta(days=10)
        data_primero = self.acto_no_papeleta_ok.copy()
        data_primero["nombre"] = "Quinario de Reglas"
        data_primero["fecha"] = fecha_primero
        
        crear_acto_service(self.admin, data_primero)

        fecha_segundo = fecha_primero + timedelta(days=1)
        data_segundo = self.acto_no_papeleta_ok.copy()
        data_segundo["nombre"] = "Quinario de Reglas"
        data_segundo["fecha"] = fecha_segundo

        nuevo_acto = crear_acto_service(self.admin, data_segundo)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(Acto.objects.filter(nombre="Quinario de Reglas").count(), 2)

        fechas_db = list(Acto.objects.values_list('fecha__date', flat=True))
        self.assertIn(fecha_primero.date(), fechas_db)
        self.assertIn(fecha_segundo.date(), fechas_db)



    def test_crear_acto_misma_fecha_nombre_diferente_ok(self):
        """
        Test: Crear acto con misma fecha pero nombre diferente

        Given: Un acto ya existente en la base de datos para una fecha específica.
        When: Un administrador intenta crear un segundo acto con un nombre distinto para ese mismo día.
        Then: El sistema permite la creación de ambos, validando que la restricción solo salta cuando coinciden nombre y fecha simultáneamente.
        """
        fecha_comun = self.ahora + timedelta(days=5)
        data_primero = self.acto_no_papeleta_ok.copy()
        data_primero["nombre"] = "Cabildo de Cuentas"
        data_primero["fecha"] = fecha_comun
        
        crear_acto_service(self.admin, data_primero)

        fecha_segundo = fecha_comun + timedelta(hours=4) 
        data_segundo = self.acto_no_papeleta_ok.copy()
        data_segundo["nombre"] = "Almuerzo de Hermandad"
        data_segundo["fecha"] = fecha_segundo

        nuevo_acto = crear_acto_service(self.admin, data_segundo)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(
            Acto.objects.filter(fecha__date=fecha_comun.date()).count(), 
            2
        )
        self.assertTrue(Acto.objects.filter(nombre="Cabildo de Cuentas").exists())
        self.assertTrue(Acto.objects.filter(nombre="Almuerzo de Hermandad").exists())



    def test_crear_acto_mismo_nombre_misma_hora_dia_distinto_ok(self):
        """
        Test: Crear acto con mismo nombre pero día distinto (misma hora)

        Given: Un acto existente programado a una hora específica (ej: 20:00h).
        When: Se intenta crear otro acto con el mismo nombre y exactamente la misma hora, pero en un día diferente.
        Then: El sistema permite la creación, ya que la validación de duplicidad del servicio 
            compara el nombre y la parte 'date' de la fecha, no la hora.
        """
        hora_comun = self.ahora.replace(hour=20, minute=0, second=0, microsecond=0)

        fecha_lunes = hora_comun + timedelta(days=7)
        data_lunes = self.acto_no_papeleta_ok.copy()
        data_lunes["nombre"] = "Triduo Solemne"
        data_lunes["fecha"] = fecha_lunes
        crear_acto_service(self.admin, data_lunes)

        fecha_martes = fecha_lunes + timedelta(days=1)
        data_martes = self.acto_no_papeleta_ok.copy()
        data_martes["nombre"] = "Triduo Solemne"
        data_martes["fecha"] = fecha_martes

        nuevo_acto = crear_acto_service(self.admin, data_martes)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(Acto.objects.filter(nombre="Triduo Solemne").count(), 2)

        actos = Acto.objects.filter(nombre="Triduo Solemne")
        self.assertEqual(actos[0].fecha.time(), actos[1].fecha.time())
        self.assertNotEqual(actos[0].fecha.date(), actos[1].fecha.date())



    def test_crear_acto_mismo_nombre_anio_diferente_ok(self):
        """
        Test: Crear acto con mismo nombre pero en año diferente

        Given: Un acto ya registrado en la base de datos para un año específico (ej: 2026).
        When: Se intenta crear un acto con el mismo nombre para el año siguiente (2027).
        Then: El sistema permite la creación, ya que aunque el nombre coincide, la fecha 
            (día, mes y año) es diferente, cumpliendo la regla de negocio.
        """
        fecha_2026 = self.ahora.replace(year=2026, month=3, day=15)
        data_2026 = self.acto_no_papeleta_ok.copy()
        data_2026["nombre"] = "Cabildo General Ordinario"
        data_2026["fecha"] = fecha_2026
        
        crear_acto_service(self.admin, data_2026)

        fecha_2027 = fecha_2026.replace(year=2027)
        data_2027 = self.acto_no_papeleta_ok.copy()
        data_2027["nombre"] = "Cabildo General Ordinario"
        data_2027["fecha"] = fecha_2027

        nuevo_acto = crear_acto_service(self.admin, data_2027)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(Acto.objects.filter(nombre="Cabildo General Ordinario").count(), 2)

        anios_db = list(Acto.objects.values_list('fecha__year', flat=True))
        self.assertIn(2026, anios_db)
        self.assertIn(2027, anios_db)



    def test_crear_acto_mismo_nombre_distinto_casing_ok(self):
        """
        Test: Crear acto con mismo nombre pero distinto casing ("Quinario" vs "quinario")

        Given: Un acto existente con el nombre "Quinario" en una fecha determinada.
        When: Se intenta crear un segundo acto para la misma fecha con el nombre "quinario" (minúscula).
        Then: Si la base de datos es case-sensitive, el sistema permite la creación ya que 
            técnicamente son strings diferentes para el filtro de Django.
        """
        fecha_comun = self.ahora + timedelta(days=15)
        data_mayuscula = self.acto_no_papeleta_ok.copy()
        data_mayuscula["nombre"] = "Quinario"
        data_mayuscula["fecha"] = fecha_comun
        
        crear_acto_service(self.admin, data_mayuscula)

        data_minuscula = self.acto_no_papeleta_ok.copy()
        data_minuscula["nombre"] = "quinario"
        data_minuscula["fecha"] = fecha_comun

        nuevo_acto = crear_acto_service(self.admin, data_minuscula)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(
            Acto.objects.filter(fecha__date=fecha_comun.date()).count(), 
            2
        )

        nombres = list(Acto.objects.values_list('nombre', flat=True))
        self.assertIn("Quinario", nombres)
        self.assertIn("quinario", nombres)



    def test_crear_acto_mismo_nombre_misma_fecha_error(self):
        """
        Test: Intentar crear acto con mismo nombre y misma fecha exacta

        Given: Un acto ya existente en la base de datos (ej: "Quinario" el 15/03/2026).
        When: Un administrador intenta crear otro acto con el mismo nombre para la misma fecha.
        Then: El sistema debe lanzar un ValidationError con el mensaje de error específico 
            indicando que el acto ya existe para esa fecha.
        """
        nombre_acto = "Quinario Anual"
        fecha_acto = self.ahora + timedelta(days=20)
        
        data_original = self.acto_no_papeleta_ok.copy()
        data_original["nombre"] = nombre_acto
        data_original["fecha"] = fecha_acto

        crear_acto_service(self.admin, data_original)

        data_duplicada = data_original.copy()
        data_duplicada["fecha"] = fecha_acto + timedelta(hours=2)

        with self.assertRaises(DjangoValidationError) as context:
            crear_acto_service(self.admin, data_duplicada)

        mensaje_esperado = f"Ya existe un acto llamado '{nombre_acto}' para la fecha {fecha_acto.strftime('%d/%m/%Y')}."

        self.assertIn('non_field_errors', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['non_field_errors'][0],
            mensaje_esperado
        )

        self.assertEqual(Acto.objects.filter(nombre=nombre_acto).count(), 1)



    def test_crear_acto_mismo_nombre_distinta_hora_misma_fecha_error(self):
        """
        Test: Intentar crear acto con mismo nombre y misma fecha pero distinta hora

        Given: Un acto ya existente en una fecha y hora determinadas (ej: 10:00h).
        When: Se intenta crear otro acto con el mismo nombre en la misma fecha pero a distinta hora (ej: 22:00h).
        Then: El sistema debe fallar lanzando ValidationError, ya que la validación del servicio 
            compara la parte 'date' de la fecha, ignorando la hora.
        """
        fecha_mañana_diez = (self.ahora + timedelta(days=1)).replace(hour=10, minute=0)
        
        data_mañana = self.acto_no_papeleta_ok.copy()
        data_mañana["nombre"] = "Ensayo de Costaleros"
        data_mañana["fecha"] = fecha_mañana_diez

        crear_acto_service(self.admin, data_mañana)

        fecha_mañana_noche = fecha_mañana_diez.replace(hour=22, minute=0)
        data_duplicada = data_mañana.copy()
        data_duplicada["fecha"] = fecha_mañana_noche

        with self.assertRaises(DjangoValidationError) as context:
            crear_acto_service(self.admin, data_duplicada)

        self.assertIn('non_field_errors', context.exception.message_dict)
        self.assertEqual(Acto.objects.filter(nombre="Ensayo de Costaleros").count(), 1)



    def test_crear_acto_mismo_nombre_misma_fecha_existente_error(self):
        """
        Test: Crear acto con mismo nombre y misma fecha ya existente

        Given: Un acto ya persistido en la base de datos (ej: "Cabildo de Oficiales" el 20/03/2026).
        When: Un administrador intenta crear un nuevo acto con idéntico nombre para ese mismo día.
        Then: El sistema debe lanzar un ValidationError capturando la duplicidad y el mensaje de error debe 
            contener el nombre del acto y la fecha formateada.
        """
        nombre_duplicado = "Cabildo de Oficiales"
        fecha_fijada = self.ahora + timedelta(days=14)
        
        data_existente = self.acto_no_papeleta_ok.copy()
        data_existente["nombre"] = nombre_duplicado
        data_existente["fecha"] = fecha_fijada

        crear_acto_service(self.admin, data_existente)

        with self.assertRaises(DjangoValidationError) as context:
            crear_acto_service(self.admin, data_existente)

        mensaje_esperado = f"Ya existe un acto llamado '{nombre_duplicado}' para la fecha {fecha_fijada.strftime('%d/%m/%Y')}."

        self.assertIn('non_field_errors', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['non_field_errors'][0],
            mensaje_esperado
        )

        self.assertEqual(
            Acto.objects.filter(nombre=nombre_duplicado, fecha__date=fecha_fijada.date()).count(), 
            1
        )



    def test_crear_acto_mismo_nombre_con_espacios_extra_error(self):
        """
        Test: Crear acto con espacios adicionales en el nombre ("Cabildo" vs "Cabildo ")

        Given: Un acto ya existente con el nombre "Cabildo".
        When: Se intenta crear un acto para la misma fecha con el nombre "Cabildo " 
            (con un espacio al final).
        Then: El sistema debería detectar que es un duplicado. 
            Nota: Si el servicio no hace un .strip(), este test fallará, 
            lo cual sirve para identificar un posible bug de validación.
        """
        fecha_comun = self.ahora + timedelta(days=5)
        data_original = self.acto_no_papeleta_ok.copy()
        data_original["nombre"] = "Cabildo"
        data_original["fecha"] = fecha_comun
        
        crear_acto_service(self.admin, data_original)

        data_con_espacio = self.acto_no_papeleta_ok.copy()
        data_con_espacio["nombre"] = "Cabildo "
        data_con_espacio["fecha"] = fecha_comun

        with self.assertRaises(DjangoValidationError, msg="El servicio debería haber detectado el duplicado limpiando los espacios."):
            crear_acto_service(self.admin, data_con_espacio)

        self.assertEqual(
            Acto.objects.filter(fecha__date=fecha_comun.date()).count(), 
            1, 
            "No debería haberse creado un segundo acto por un simple espacio extra."
        )



    def test_crear_acto_mismo_nombre_misma_fecha_error(self):
        """
        Test: Crear acto con mismo nombre y misma fecha cuando ya existe en BD

        Given: Un acto ya existente en la base de datos ("Convivencia febrero" en la fecha prevista).
        When: Un administrador intenta crear un segundo acto con el mismo nombre para esa misma fecha.
        Then: El sistema debe impedir la creación lanzando un ValidationError con el mensaje de error correspondiente.
        """
        fecha_fijada = self.fecha_acto
        nombre_acto = "Convivencia febrero"
        
        data_original = self.acto_no_papeleta_ok.copy()
        data_original["nombre"] = nombre_acto
        data_original["fecha"] = fecha_fijada
        
        crear_acto_service(self.admin, data_original)

        with self.assertRaises(DjangoValidationError) as context:
            crear_acto_service(self.admin, data_original)

        mensaje_esperado = f"Ya existe un acto llamado '{nombre_acto}' para la fecha {fecha_fijada.strftime('%d/%m/%Y')}."
        
        self.assertIn('non_field_errors', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['non_field_errors'][0],
            mensaje_esperado
        )

        self.assertEqual(Acto.objects.filter(nombre=nombre_acto).count(), 1)



    def test_crear_acto_sin_papeleta_sin_fechas_solicitud_ok(self):
        """
        Test: Crear acto cuyo tipo no requiere papeleta sin fechas de solicitud

        Given: Un usuario administrador y datos de un acto vinculado a un TipoActo 
            que tiene requiere_papeleta=False.
        When: Se invoca el servicio de creación con los campos de fechas de solicitud y modalidad a None.
        Then: El sistema permite la creación exitosa del acto, persistiendo los valores nulos correctamente.
        """
        datos_acto = self.acto_no_papeleta_ok.copy()

        datos_acto["modalidad"] = None
        datos_acto["inicio_solicitud"] = None
        datos_acto["fin_solicitud"] = None
        datos_acto["inicio_solicitud_cirios"] = None
        datos_acto["fin_solicitud_cirios"] = None

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.nombre, "Convivencia febrero")
        self.assertFalse(nuevo_acto.tipo_acto.requiere_papeleta)

        self.assertIsNone(nuevo_acto.inicio_solicitud)
        self.assertIsNone(nuevo_acto.modalidad)

        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_sin_papeleta_modalidad_none_ok(self):
        """
        Test: Crear acto sin papeleta con modalidad=None

        Given: Un tipo de acto que no requiere papeleta de sitio.
        When: Se intenta crear el acto enviando el campo 'modalidad' como None.
        Then: El servicio debe permitir la creación y el objeto resultante debe tener la modalidad nula.
        """
        datos_acto = self.acto_no_papeleta_ok.copy()
        datos_acto["modalidad"] = None

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertIsNone(nuevo_acto.modalidad)
        self.assertEqual(nuevo_acto.nombre, "Convivencia febrero")

        self.assertTrue(Acto.objects.filter(id=nuevo_acto.id, modalidad__isnull=True).exists())



    def test_crear_acto_sin_papeleta_solo_campos_obligatorios_ok(self):
        """
        Test: Crear acto sin papeleta con solo campos obligatorios

        Given: Un diccionario de datos que contiene únicamente los campos obligatorios del modelo (nombre, lugar, fecha y tipo_acto).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto con éxito, asignando los valores proporcionados y dejando el resto como nulos.
        """
        datos_minimos = {
            "nombre": "Misa de Hermandad",
            "lugar": "Parroquia Mayor",
            "fecha": self.ahora + timedelta(days=2),
            "tipo_acto": self.tipo_no_papeleta
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_minimos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.nombre, "Misa de Hermandad")
        self.assertEqual(nuevo_acto.lugar, "Parroquia Mayor")

        self.assertIsNone(nuevo_acto.descripcion)
        self.assertIsNone(nuevo_acto.modalidad)

        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_con_papeleta_modalidad_unificado_ok(self):
        """
        Test: Crear acto con papeleta con modalidad UNIFICADO

        Given: Un TipoActo que requiere papeleta y un diccionario de datos que incluye 
            la modalidad UNIFICADO y el rango de fechas de solicitud.
        When: El administrador invoca el servicio de creación.
        Then: El sistema crea el acto correctamente, vinculando el tipo de acto y 
            almacenando las fechas de solicitud global.
        """
        inicio = self.ahora + timedelta(days=1)
        fin = self.ahora + timedelta(days=10)
        
        datos_unificado = {
            "nombre": "Vía Crucis Claustral",
            "lugar": "Interior de la Parroquia",
            "fecha": self.ahora + timedelta(days=15),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": inicio,
            "fin_solicitud": fin,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_unificado
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertEqual(nuevo_acto.inicio_solicitud, inicio)
        self.assertEqual(nuevo_acto.fin_solicitud, fin)

        self.assertTrue(nuevo_acto.tipo_acto.requiere_papeleta)
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_con_fechas_solicitud_validas_ok(self):
        """
        Test: Crear acto con fechas inicio_solicitud y fin_solicitud válidas

        Given: Un diccionario de datos para un acto con papeleta que incluye un rango 
            de fechas coherente (inicio anterior al fin).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto y almacenar correctamente las fechas de solicitud, 
            permitiendo que la lógica de apertura de plazos funcione en el futuro.
        """
        fecha_inicio = self.ahora + timedelta(days=2)
        fecha_fin = self.ahora + timedelta(days=12)
        fecha_celebracion = self.ahora + timedelta(days=20)

        datos_acto = {
            "nombre": "Salida Extraordinaria",
            "lugar": "Centro Histórico",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": fecha_inicio,
            "fin_solicitud": fecha_fin
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.inicio_solicitud, fecha_inicio)
        self.assertEqual(nuevo_acto.fin_solicitud, fecha_fin)

        acto_db = Acto.objects.get(id=nuevo_acto.id)
        self.assertTrue(acto_db.inicio_solicitud < acto_db.fin_solicitud)
        self.assertTrue(acto_db.fin_solicitud < acto_db.fecha)



    def test_crear_acto_fechas_orden_cronologico_correcto_ok(self):
        """
        Test: Crear acto donde las fechas están correctamente antes del acto

        Given: Un diccionario con un cronograma lógico: el periodo de solicitud 
            termina antes de que se celebre el acto.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe permitir la creación, ya que el diseño garantiza 
            que el reparto se realice antes del evento.
        """
        inicio_solicitud = self.ahora + timedelta(days=5)
        fin_solicitud = self.ahora + timedelta(days=15)
        fecha_celebracion = self.ahora + timedelta(days=20)

        datos_acto = {
            "nombre": "Traslado procesional",
            "lugar": "Convento de las Clarisas",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": inicio_solicitud,
            "fin_solicitud": fin_solicitud
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertTrue(nuevo_acto.inicio_solicitud < nuevo_acto.fin_solicitud)
        self.assertTrue(nuevo_acto.fin_solicitud < nuevo_acto.fecha)

        self.assertEqual(Acto.objects.filter(id=nuevo_acto.id).count(), 1)



    def test_crear_acto_con_papeleta_modalidad_tradicional_ok(self):
        """
        Test: Crear acto con modalidad TRADICIONAL

        Given: Un TipoActo que requiere papeleta y un diccionario de datos con modalidad 
            TRADICIONAL, incluyendo fechas de solicitud general y fechas de cirios.
        When: El administrador invoca el servicio de creación.
        Then: El sistema crea el acto correctamente, almacenando ambos periodos de 
            solicitud y validando que el de cirios sea posterior al general.
        """

        inicio_fase1 = self.ahora + timedelta(days=1)
        fin_fase1 = self.ahora + timedelta(days=5)

        inicio_fase2 = self.ahora + timedelta(days=6)
        fin_fase2 = self.ahora + timedelta(days=10)
        
        fecha_celebracion = self.ahora + timedelta(days=20)

        datos_tradicional = {
            "nombre": "Estación de Penitencia Viernes Santo",
            "lugar": "Parroquia de San Jacinto",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_fase1,
            "fin_solicitud": fin_fase1,
            "inicio_solicitud_cirios": inicio_fase2,
            "fin_solicitud_cirios": fin_fase2,
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_tradicional
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(nuevo_acto.inicio_solicitud, inicio_fase1)
        self.assertEqual(nuevo_acto.fin_solicitud, fin_fase1)
        self.assertEqual(nuevo_acto.inicio_solicitud_cirios, inicio_fase2)
        self.assertEqual(nuevo_acto.fin_solicitud_cirios, fin_fase2)

        self.assertTrue(nuevo_acto.fin_solicitud < nuevo_acto.inicio_solicitud_cirios)
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_con_todas_las_fechas_requeridas_ok(self):
        """
        Test: Crear acto con todas las fechas requeridas

        Given: Un diccionario de datos completo para un acto TRADICIONAL, incluyendo 
            fechas de solicitud general y fechas específicas para cirios.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe persistir el acto con los cuatro hitos temporales correctamente 
            almacenados y validados.
        """
        inicio_gen = self.ahora + timedelta(days=2)
        fin_gen = self.ahora + timedelta(days=5)

        inicio_cirios = self.ahora + timedelta(days=6)
        fin_cirios = self.ahora + timedelta(days=10)

        fecha_acto = self.ahora + timedelta(days=15)

        datos_completos = {
            "nombre": "Solemne Quinario y Función Principal",
            "lugar": "Altar Mayor",
            "fecha": fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_gen,
            "fin_solicitud": fin_gen,
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios,
            "descripcion": "Reparto anual de papeletas para el Quinario."
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_completos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.inicio_solicitud, inicio_gen)
        self.assertEqual(nuevo_acto.fin_solicitud, fin_gen)
        self.assertEqual(nuevo_acto.inicio_solicitud_cirios, inicio_cirios)
        self.assertEqual(nuevo_acto.fin_solicitud_cirios, fin_cirios)

        self.assertTrue(nuevo_acto.fin_solicitud < nuevo_acto.inicio_solicitud_cirios)
        self.assertTrue(nuevo_acto.fin_solicitud_cirios < nuevo_acto.fecha)
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_fases_orden_correcto_ok(self):
        """
        Test: Crear acto con fases de solicitud correctamente ordenadas

        Given: Un diccionario con un cronograma donde la fase de insignias termina 
            antes de que empiece la de cirios, y esta termina antes del acto.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe permitir la creación exitosa al cumplirse todas las 
            restricciones de orden temporal.
        """
        inicio_insignias = self.ahora + timedelta(days=1)
        fin_insignias = self.ahora + timedelta(days=5)
        
        inicio_cirios = self.ahora + timedelta(days=6)
        fin_cirios = self.ahora + timedelta(days=10)
        
        fecha_celebracion = self.ahora + timedelta(days=15)

        datos_acto = {
            "nombre": "Estación de Penitencia - Orden OK",
            "lugar": "Parroquia",
            "fecha": fecha_celebracion,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_insignias,
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertTrue(nuevo_acto.fin_solicitud < nuevo_acto.inicio_solicitud_cirios)
        self.assertTrue(nuevo_acto.fin_solicitud_cirios < nuevo_acto.fecha)
        
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_fechas_separadas_insignias_y_cirios_ok(self):
        """
        Test: Crear acto con fechas separadas correctamente entre insignias y cirios

        Given: Un diccionario de datos donde el fin de insignias y el inicio de cirios 
            no solo son correlativos, sino que tienen un margen de separación.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe permitir la creación, validando que la secuencia temporal 
            es lógica y no presenta solapamientos.
        """
        inicio_insignias = self.ahora + timedelta(days=1)
        fin_insignias = self.ahora + timedelta(days=5)

        inicio_cirios = self.ahora + timedelta(days=6) 
        fin_cirios = self.ahora + timedelta(days=10)
        
        fecha_acto = self.ahora + timedelta(days=15)

        datos_acto = {
            "nombre": "Salida Procesional con Pausa de Gestión",
            "lugar": "Sede Canónica",
            "fecha": fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_insignias,
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertGreater(nuevo_acto.inicio_solicitud_cirios, nuevo_acto.fin_solicitud)

        self.assertEqual(Acto.objects.count(), 1)
        self.assertEqual(nuevo_acto.nombre, "Salida Procesional con Pausa de Gestión")



    def test_crear_acto_nombre_vacio_error(self):
        """
        Test: Crear acto con nombre="" → error

        Given: Un diccionario de datos donde el nombre es una cadena vacía.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el nombre 
            es obligatorio y no puede estar vacío.
        """
        datos_invalidos = {
            "nombre": "",
            "lugar": "Parroquia de Santa Ana",
            "fecha": self.ahora + timedelta(days=10),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        with self.assertRaises(DjangoValidationError):
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertEqual(Acto.objects.filter(nombre="").count(), 0)



    def test_crear_acto_nombre_espacios_blanco_error(self):
        """
        Test: Crear acto con nombre=" " → error

        Given: Un diccionario de datos donde el nombre contiene únicamente espacios en blanco.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError, ya que el servicio limpia los espacios
            y la validación nativa de Django (o la del modelo) detecta el campo vacío.
        """
        datos_invalidos = {
            "nombre": "   ",
            "lugar": "Casa Hermandad",
            "fecha": self.ahora + timedelta(days=10),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("nombre", cm.exception.message_dict)

        mensaje_error = cm.exception.message_dict["nombre"][0]
        self.assertTrue(
            mensaje_error in ["This field cannot be blank.", "El nombre del acto no puede estar vacío.", "Este campo no puede estar en blanco."],
            f"Mensaje inesperado: {mensaje_error}"
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_lugar_vacio_error(self):
        """
        Test: Crear acto con lugar="" → error

        Given: Un diccionario de datos donde el lugar es una cadena vacía.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el lugar 
            es obligatorio y no puede estar vacío.
        """
        datos_invalidos = {
            "nombre": "Misa de Acción de Gracias",
            "lugar": "",
            "fecha": self.ahora + timedelta(days=10),
            "tipo_acto": self.tipo_no_papeleta
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("lugar", cm.exception.message_dict)
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_lugar_espacios_blanco_error(self):
        """
        Test: Crear acto con lugar=" " → error

        Given: Un diccionario de datos donde el lugar contiene únicamente espacios en blanco.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError debido a que el campo 
            quedará vacío tras la limpieza de datos.
        """
        datos_invalidos = {
            "nombre": "Misa de Hermandad",
            "lugar": "   ",
            "fecha": self.ahora + timedelta(days=10),
            "tipo_acto": self.tipo_no_papeleta
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("lugar", cm.exception.message_dict)

        mensaje_error = cm.exception.message_dict["lugar"][0]
        mensajes_esperados = [
            "This field cannot be blank.", 
            "Este campo no puede estar en blanco.",
            "El lugar de celebración no puede estar vacío."
        ]
        self.assertIn(mensaje_error, mensajes_esperados)

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_sin_tipo_acto_error(self):
        """
        Test: Crear acto sin tipo_acto → error

        Given: Un diccionario de datos donde falta la referencia al tipo de acto.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el tipo de 
            acto es obligatorio para clasificar el evento.
        """
        datos_invalidos = {
            "nombre": "Convivencia de Jóvenes",
            "lugar": "Salones Parroquiales",
            "fecha": self.ahora + timedelta(days=10),
            "tipo_acto": None
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("tipo_acto", cm.exception.message_dict)
        
        mensaje_error = cm.exception.message_dict["tipo_acto"][0]
        mensajes_esperados = [
            "El tipo de acto es obligatorio.",
            "This field cannot be null.",
            "Este campo no puede ser nulo."
        ]
        self.assertIn(mensaje_error, mensajes_esperados)

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_sin_papeleta_con_modalidad_error(self):
        """
        Test: Crear acto sin papeleta pero con modalidad → error

        Given: Un tipo de acto que NO requiere papeleta (self.tipo_no_papeleta) 
            y un diccionario que intenta asignarle una modalidad.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque la modalidad es 
            incompatible con actos que no gestionan papeletas de sitio.
        """
        datos_invalidos = {
            "nombre": "Quinario al Santísimo Cristo",
            "lugar": "Altar Mayor",
            "fecha": self.ahora + timedelta(days=15),
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["modalidad"][0], 
            "Un acto que no requiere papeleta no puede tener modalidad."
        )
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_sin_papeleta_con_inicio_solicitud_error(self):
        """
        Test: Crear acto sin papeleta pero con inicio_solicitud → error

        Given: Un tipo de acto que NO requiere papeleta y un diccionario de datos 
            que incluye una fecha de inicio de solicitud.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque un acto sin papeleta 
            no puede tener hitos temporales de solicitud.
        """
        datos_invalidos = {
            "nombre": "Vía Crucis Parroquial",
            "lugar": "Calles de la feligresía",
            "fecha": self.ahora + timedelta(days=10),
            "tipo_acto": self.tipo_no_papeleta,
            "inicio_solicitud": self.ahora + timedelta(days=1)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud"][0],
            "Un acto que no requiere papeleta no puede tener fechas de solicitud."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_sin_papeleta_con_fin_solicitud_error(self):
        """
        Test: Crear acto sin papeleta pero con fin_solicitud → error

        Given: Un tipo de acto que NO requiere papeleta y un diccionario de datos 
            que incluye una fecha de fin de solicitud.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que un acto 
            sin papeleta no puede tener fechas de solicitud.
        """
        datos_invalidos = {
            "nombre": "Triduo a la Virgen",
            "lugar": "Capilla",
            "fecha": self.ahora + timedelta(days=20),
            "tipo_acto": self.tipo_no_papeleta,
            "fin_solicitud": self.ahora + timedelta(days=10)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud"][0],
            "Un acto que no requiere papeleta no puede tener fechas de solicitud."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_sin_papeleta_con_fechas_cirios_error(self):
        """
        Test: Crear acto sin papeleta pero con fechas de cirios → error

        Given: Un tipo de acto que NO requiere papeleta y un diccionario de datos 
            que incluye fechas para la fase de cirios.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError por cada campo de fecha 
            de cirios presente, ya que son incompatibles con el tipo de acto.
        """
        datos_invalidos = {
            "nombre": "Convivencia de Hermandades",
            "lugar": "Casa Hermandad",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_no_papeleta,
            "inicio_solicitud_cirios": self.ahora + timedelta(days=5),
            "fin_solicitud_cirios": self.ahora + timedelta(days=10)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        
        error_msg = "Un acto que no requiere papeleta no puede tener fechas de solicitud."
        self.assertEqual(cm.exception.message_dict["inicio_solicitud_cirios"][0], error_msg)
        self.assertEqual(cm.exception.message_dict["fin_solicitud_cirios"][0], error_msg)
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_sin_papeleta_con_todas_las_fechas_error(self):
        """
        Test: Crear acto sin papeleta con todas las fechas de solicitud → error

        Given: Un tipo de acto que NO requiere papeleta y un diccionario de datos 
            que incluye erróneamente el cronograma completo de solicitudes.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError con mensajes de error para 
            cada uno de los campos de fecha presentes.
        """
        datos_invalidos = {
            "nombre": "Misa de Hermandad",
            "lugar": "Parroquia",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_no_papeleta,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": self.ahora + timedelta(days=10)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        campos_con_error = ["inicio_solicitud", "fin_solicitud", "inicio_solicitud_cirios", "fin_solicitud_cirios"]
        error_msg = "Un acto que no requiere papeleta no puede tener fechas de solicitud."
        
        for campo in campos_con_error:
            self.assertIn(campo, cm.exception.message_dict)
            self.assertEqual(cm.exception.message_dict[campo][0], error_msg)

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_sin_papeleta_con_fechas_none_ok(self):
        """
        Test: Crear acto sin papeleta con todas esas fechas en None

        Given: Un tipo de acto que NO requiere papeleta y un diccionario de datos 
            donde la modalidad y todas las fechas de solicitud son None.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto correctamente, ya que no hay 
            incoherencias con el tipo de acto.
        """
        datos_acto = {
            "nombre": "Misa de Hermandad Mensual",
            "lugar": "Capilla de los Marineros",
            "fecha": self.ahora + timedelta(days=7),
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
            "descripcion": "Misa mensual ordinaria de la corporación."
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.nombre, "Misa de Hermandad Mensual")
        self.assertEqual(nuevo_acto.tipo_acto, self.tipo_no_papeleta)

        self.assertIsNone(nuevo_acto.modalidad)
        self.assertIsNone(nuevo_acto.inicio_solicitud)
        self.assertIsNone(nuevo_acto.fin_solicitud)
        
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_con_papeleta_sin_modalidad_error(self):
        """
        Test: Crear acto con papeleta sin modalidad → error

        Given: Un tipo de acto que SÍ requiere papeleta y un diccionario de datos 
            donde el campo modalidad es None o está ausente.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que la modalidad 
            es obligatoria para este tipo de actos.
        """
        datos_invalidos = {
            "nombre": "Estación de Penitencia",
            "lugar": "Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": None,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["modalidad"][0],
            "La modalidad es obligatoria para actos con papeleta."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_con_papeleta_sin_inicio_solicitud_error(self):
        """
        Test: Crear acto con papeleta sin inicio_solicitud → error

        Given: Un tipo de acto que requiere papeleta y un diccionario de datos 
            donde falta el campo inicio_solicitud.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que la fecha 
            de inicio es obligatoria para actos con gestión de papeletas.
        """
        datos_invalidos = {
            "nombre": "Salida Extraordinaria",
            "lugar": "Centro Ciudad",
            "fecha": self.ahora + timedelta(days=20),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": None,
            "fin_solicitud": self.ahora + timedelta(days=10)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud"][0],
            "El inicio de solicitud es obligatorio."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_con_papeleta_sin_fin_solicitud_error(self):
        """
        Test: Crear acto con papeleta sin fin_solicitud → error

        Given: Un tipo de acto que requiere papeleta y un diccionario de datos 
            donde falta el campo fin_solicitud.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que la fecha 
            de cierre es obligatoria para actos con gestión de papeletas.
        """
        datos_invalidos = {
            "nombre": "Vía Crucis de la Pía Unión",
            "lugar": "Casa de Pilatos",
            "fecha": self.ahora + timedelta(days=25),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=2),
            "fin_solicitud": None
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud"][0],
            "El fin de solicitud es obligatorio."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_fechas_solicitud_invertidas_error(self):
        """
        Test: Crear acto con inicio_solicitud >= fin_solicitud → error

        Given: Un diccionario de datos donde la fecha de fin de solicitud es 
            anterior (o igual) a la fecha de inicio.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el cierre 
            del plazo debe ser cronológicamente posterior a la apertura.
        """
        inicio_incorrecto = self.ahora + timedelta(days=10)
        fin_incorrecto = self.ahora + timedelta(days=5)

        datos_invalidos = {
            "nombre": "Solemne Procesión de Gloria",
            "lugar": "Centro Histórico",
            "fecha": self.ahora + timedelta(days=20),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": inicio_incorrecto,
            "fin_solicitud": fin_incorrecto
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud"][0],
            "El fin de solicitud debe ser posterior al inicio."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_inicio_solicitud_post_fecha_acto_error(self):
        """
        Test: Crear acto con inicio_solicitud >= fecha acto → error

        Given: Un diccionario de datos donde la fecha de apertura de solicitudes 
            es el mismo día o posterior a la celebración del acto.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque el proceso de 
            solicitud debe preceder necesariamente al evento.
        """
        fecha_del_acto = self.ahora + timedelta(days=10)
        
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Viernes Santo",
            "lugar": "S.I. Catedral",
            "fecha": fecha_del_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": fecha_del_acto + timedelta(hours=1),
            "fin_solicitud": fecha_del_acto + timedelta(days=1)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud"][0],
            "El inicio de solicitud no puede ser igual o posterior a la fecha del acto."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_fin_solicitud_post_fecha_acto_error(self):
        """
        Test: Crear acto con fin_solicitud > fecha acto → error

        Given: Un diccionario de datos donde la fecha de cierre de solicitudes 
            es posterior a la fecha de celebración del acto.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque no se pueden 
            solicitar papeletas para un acto que ya ha ocurrido.
        """
        fecha_del_acto = self.ahora + timedelta(days=5)
        
        datos_invalidos = {
            "nombre": "Salida Procesional del Corpus Christi",
            "lugar": "Parroquia de Santa María",
            "fecha": fecha_del_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": fecha_del_acto - timedelta(days=5),
            "fin_solicitud": fecha_del_acto + timedelta(hours=1)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fin_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud"][0],
            "El fin de solicitud no puede ser posterior a la fecha del acto."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_sin_inicio_cirios_error(self):
        """
        Test: Crear acto tradicional sin inicio_solicitud_cirios → error

        Given: Un tipo de acto con papeleta y modalidad TRADICIONAL, pero sin 
            especificar la fecha de inicio para la fase de cirios.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el inicio 
            de cirios es obligatorio en esta modalidad.
        """
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Tradicional",
            "lugar": "Catedral",
            "fecha": self.ahora + timedelta(days=40),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": self.ahora + timedelta(days=15)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud_cirios"][0],
            "El inicio de cirios es obligatorio en modalidad tradicional."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_sin_fin_cirios_error(self):
        """
        Test: Crear acto tradicional sin fin_solicitud_cirios → error

        Given: Un acto con modalidad TRADICIONAL donde falta la fecha de cierre 
            de la fase de cirios.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el fin 
            de cirios es obligatorio en modalidad tradicional.
        """
        datos_invalidos = {
            "nombre": "Estación de Penitencia Tradicional",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=40),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": None
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud_cirios"][0],
            "El fin de cirios es obligatorio en modalidad tradicional."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_fechas_cirios_invertidas_error(self):
        """
        Test: Crear acto tradicional con inicio_cirios >= fin_cirios → error

        Given: Un acto en modalidad TRADICIONAL donde la fecha de cierre de cirios 
            es anterior o igual a su fecha de apertura.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el fin 
            de cirios debe ser posterior al inicio.
        """
        inicio_cirios = self.ahora + timedelta(days=20)
        fin_cirios = self.ahora + timedelta(days=15)

        datos_invalidos = {
            "nombre": "Estación de Penitencia - Cronograma Inválido",
            "lugar": "Catedral",
            "fecha": self.ahora + timedelta(days=40),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud_cirios"][0],
            "El fin de cirios debe ser posterior al inicio."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_inicio_cirios_post_fecha_acto_error(self):
        """
        Test: Crear acto tradicional con inicio_cirios >= fecha acto → error

        Given: Un acto en modalidad TRADICIONAL donde la fecha de inicio de la 
            fase de cirios es igual o posterior a la fecha del acto.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque todas las fases 
            de solicitud deben ser previas a la celebración del acto.
        """
        fecha_del_acto = self.ahora + timedelta(days=20)
        
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Fase Cirios Tardía",
            "lugar": "S.I. Catedral",
            "fecha": fecha_del_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": fecha_del_acto + timedelta(hours=2),
            "fin_solicitud_cirios": fecha_del_acto + timedelta(days=2)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud_cirios"][0],
            "El inicio de cirios no puede ser igual o posterior a la fecha del acto."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_fin_cirios_post_fecha_acto_error(self):
        """
        Test: Crear acto tradicional con fin_cirios > fecha acto → error

        Given: Un acto en modalidad TRADICIONAL donde el plazo de cirios 
            finaliza después de la fecha programada para el acto.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque el proceso de 
            reparto de cirios debe concluir antes de la celebración.
        """
        fecha_del_acto = self.ahora + timedelta(days=15)
        
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Cierre Cirios Inválido",
            "lugar": "S.I. Catedral",
            "fecha": fecha_del_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=6),
            "fin_solicitud_cirios": fecha_del_acto + timedelta(days=1)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fin_solicitud_cirios"][0],
            "El fin de cirios no puede ser posterior a la fecha del acto."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_fases_solapadas_error(self):
        """
        Test: Crear acto con fases mal ordenadas: cirios antes que insignias

        Given: Un acto en modalidad TRADICIONAL donde la fecha de inicio de cirios 
            es anterior a la fecha de fin de la fase de insignias.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque el cronograma de 
            reparto tradicional debe ser secuencial y no solapado.
        """
        fin_insignias = self.ahora + timedelta(days=10)
        inicio_cirios_invalido = self.ahora + timedelta(days=8)

        datos_invalidos = {
            "nombre": "Estación de Penitencia - Fases Solapadas",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios_invalido,
            "fin_solicitud_cirios": self.ahora + timedelta(days=15)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud_cirios"][0],
            "El período de cirios debe comenzar después de finalizar el de insignias."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_fases_exactamente_solapadas_error(self):
        """
        Test: Crear acto donde fin_solicitud >= inicio_solicitud_cirios

        Given: Un acto en modalidad TRADICIONAL donde la fase de insignias 
            termina exactamente en el mismo momento en que empieza la de cirios.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError porque la lógica de 
            negocio requiere un orden secuencial (inicio_cirios > fin_insignias).
        """
        fecha_critica = self.ahora + timedelta(days=10)

        datos_invalidos = {
            "nombre": "Estación de Penitencia - Solape Exacto",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": fecha_critica,
            "inicio_solicitud_cirios": fecha_critica,
            "fin_solicitud_cirios": self.ahora + timedelta(days=20)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud_cirios"][0],
            "El período de cirios debe comenzar después de finalizar el de insignias."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_con_fases_solapadas_error(self):
        """
        Test: Crear acto donde fases se solapan

        Given: Un acto en modalidad TRADICIONAL donde el inicio de la fase de 
            cirios es anterior al fin de la fase de insignias.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que el período 
            de cirios debe comenzar después de finalizar el de insignias.
        """
        fin_insignias = self.ahora + timedelta(days=10)
        inicio_cirios_invalido = self.ahora + timedelta(days=8)

        datos_invalidos = {
            "nombre": "Estación de Penitencia - Error de Solape",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios_invalido,
            "fin_solicitud_cirios": self.ahora + timedelta(days=20)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud_cirios"][0],
            "El período de cirios debe comenzar después de finalizar el de insignias."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_orden_cronologico_ok(self):
        """
        Test: Crear acto tradicional con orden correcto:
            inicio_insignias < fin_insignias < inicio_cirios < fin_cirios < fecha_acto

        Given: Un acto en modalidad TRADICIONAL con todas sus fechas perfectamente 
            escalonadas y coherentes.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto correctamente y persistir todos los 
            campos de fechas en la base de datos.
        """
        inicio_insignias = self.ahora + timedelta(days=1)
        fin_insignias    = self.ahora + timedelta(days=10)
        inicio_cirios    = self.ahora + timedelta(days=11)
        fin_cirios       = self.ahora + timedelta(days=20)
        fecha_del_acto   = self.ahora + timedelta(days=30)

        datos_validos = {
            "nombre": "Estación de Penitencia 2026",
            "lugar": "S.I. Catedral de Sevilla",
            "fecha": fecha_del_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_insignias,
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios,
            "descripcion": "Reparto tradicional por fases (Insignias y Cirios)."
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(nuevo_acto.inicio_solicitud, inicio_insignias)
        self.assertEqual(nuevo_acto.fin_solicitud, fin_insignias)
        self.assertEqual(nuevo_acto.inicio_solicitud_cirios, inicio_cirios)
        self.assertEqual(nuevo_acto.fin_solicitud_cirios, fin_cirios)

        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_unificado_con_inicio_cirios_error(self):
        """
        Test: Crear acto UNIFICADO con inicio_solicitud_cirios → error

        Given: Un acto con modalidad UNIFICADA donde el administrador intenta 
            definir erróneamente una fecha de inicio para cirios.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError asignado al campo 'modalidad', 
            indicando que en unificado no se deben definir fechas de cirios.
        """
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Unificada Incorrecta",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=5),
            "fin_solicitud_cirios": None
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["modalidad"][0],
            "En modalidad UNIFICADO no se deben definir fechas de cirios."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_unificado_con_fin_cirios_error(self):
        """
        Test: Crear acto UNIFICADO con fin_solicitud_cirios → error

        Given: Un acto con modalidad UNIFICADA donde el administrador rellena 
            el campo fin_solicitud_cirios por error.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError asociado al campo 'modalidad' 
            indicando que no se deben definir fechas de cirios en esta modalidad.
        """
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Reparto Unificado",
            "lugar": "Catedral",
            "fecha": self.ahora + timedelta(days=20),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": self.ahora + timedelta(days=12)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["modalidad"][0],
            "En modalidad UNIFICADO no se deben definir fechas de cirios."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_unificado_con_ambas_fechas_cirios_error(self):
        """
        Test: Crear acto UNIFICADO con ambas fechas de cirios → error

        Given: Un acto con modalidad UNIFICADA donde el administrador rellena 
            tanto el inicio como el fin de cirios por error.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError asociado al campo 'modalidad' 
            porque en unificado no deben existir plazos diferenciados para cirios.
        """
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Error Unificado Total",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=11),
            "fin_solicitud_cirios": self.ahora + timedelta(days=15)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["modalidad"][0],
            "En modalidad UNIFICADO no se deben definir fechas de cirios."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_unificado_campos_correctos_ok(self):
        """
        Test: Crear acto UNIFICADO con solo inicio_solicitud y fin_solicitud

        Given: Un acto con modalidad UNIFICADA donde las fechas de cirios 
            son nulas y el plazo general es coherente.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto correctamente y persistir 
            únicamente las fechas de solicitud global.
        """
        inicio_global = self.ahora + timedelta(days=1)
        fin_global    = self.ahora + timedelta(days=15)
        fecha_acto    = self.ahora + timedelta(days=20)

        datos_validos = {
            "nombre": "Vía Crucis Claustral - Unificado",
            "lugar": "Interior de la Parroquia",
            "fecha": fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": inicio_global,
            "fin_solicitud": fin_global,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
            "descripcion": "Reparto en un solo plazo para todos los puestos."
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertEqual(nuevo_acto.inicio_solicitud, inicio_global)
        self.assertEqual(nuevo_acto.fin_solicitud, fin_global)

        self.assertIsNone(nuevo_acto.inicio_solicitud_cirios)
        self.assertIsNone(nuevo_acto.fin_solicitud_cirios)

        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_con_descripcion_larga_ok(self):
        """
        Test: Crear acto con descripción larga

        Given: Un acto con una descripción que supera la longitud de un CharField 
            convencional, incluyendo saltos de línea y caracteres especiales.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto correctamente y recuperar la 
            descripción íntegra desde la base de datos.
        """
        descripcion_extensa = (
            "Itinerario oficial para la Estación de Penitencia 2026:\n"
            "Salida (18:00h), Plaza del Triunfo, S.I. Catedral, Alemanes, "
            "Placentines, Francos, Cuesta del Rosario...\n\n"
            "NOTAS IMPORTANTES:\n"
            "1. Es obligatorio el uso de calcetines negros.\n"
            "2. Los menores de 12 años deben portar la papeleta de sitio en el exterior.\n"
            "3. Se ruega puntualidad máxima en la formación de los tramos.\n"
            "4. Queda terminantemente prohibido el uso de dispositivos móviles."
        )

        datos_validos = {
            "nombre": "Estación de Penitencia (Detallada)",
            "lugar": "Centro Histórico",
            "fecha": self.ahora + timedelta(days=45),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=15),
            "descripcion": descripcion_extensa
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.descripcion, descripcion_extensa)
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_con_caracteres_especiales_nombre_ok(self):
        """
        Test: Crear acto con caracteres especiales en nombre

        Given: Un nombre de acto que contiene tildes, eñes, símbolos (€, @, #) 
            y emojis para validar la codificación del sistema.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto correctamente y recuperar el 
            nombre exacto sin pérdida de información ni errores de encoding.
        """
        nombre_especial = "¡Función Principal de Instituto! ⛪ ✨ (Señor de la Cañá) - Cuota: 10€ #Hermandad2026"
        
        datos_validos = {
            "nombre": nombre_especial,
            "lugar": "Parroquia de San Antón (Sevilla)",
            "fecha": self.ahora + timedelta(days=60),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=15),
            "descripcion": "Validación de caracteres especiales y emojis."
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.nombre, nombre_especial)

        self.assertEqual(Acto.objects.filter(nombre=nombre_especial).count(), 1)



    def test_crear_acto_con_emojis_en_descripcion_ok(self):
        """
        Test: Crear acto con emojis en descripción

        Given: Una descripción de acto que incluye diversos emojis (UTF-8 de 4 bytes) 
            para organizar la información visualmente.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe crear el acto correctamente y persistir los 
            emojis sin errores de codificación en la base de datos.
        """
        descripcion_con_emojis = (
            "📍 Lugar: Real Parroquia de Señá Santa Ana\n"
            "🕒 Hora: 20:30h\n"
            "⚠️ Nota: Traer medalla de la Hermandad 🏅\n"
            "✨ ¡Os esperamos a todos! 🙏"
        )

        datos_validos = {
            "nombre": "Solemne Quinario 2026",
            "lugar": "Triana",
            "fecha": self.ahora + timedelta(days=15),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "descripcion": descripcion_con_emojis
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.descripcion, descripcion_con_emojis)

        self.assertTrue(Acto.objects.filter(descripcion__contains="🙏").exists())



    def test_crear_acto_fecha_muy_futura_ok(self):
        """
        Test: Crear acto con fecha muy futura

        Given: Un acto programado para una fecha lejana (ej: dentro de 10 años).
        When: El administrador invoca el servicio de creación con plazos de 
            solicitud coherentes con esa fecha futura.
        Then: El sistema debe permitir la creación y persistir la fecha 
            correctamente en la base de datos.
        """
        diez_anios_vista = self.ahora + timedelta(days=365 * 10)
        
        datos_validos = {
            "nombre": "Aniversario Coronación Canónica (Centenario)",
            "lugar": "S.I. Catedral",
            "fecha": diez_anios_vista,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": diez_anios_vista - timedelta(days=30),
            "fin_solicitud": diez_anios_vista - timedelta(days=5),
            "descripcion": "Acto extraordinario planificado a largo plazo."
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.fecha, diez_anios_vista)

        self.assertEqual(nuevo_acto.fecha.year, diez_anios_vista.year)
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_fecha_muy_proxima_ok(self):
        """
        Test: Crear acto con fecha muy próxima (dentro de una hora)

        Given: Un acto programado para dentro de 60 minutos con un plazo 
            de solicitud que finaliza justo antes.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe permitir la creación siempre que se respete 
            el orden cronológico exigido por el modelo.
        """
        fecha_acto = self.ahora + timedelta(minutes=60)
        inicio_solicitud = self.ahora + timedelta(minutes=1)
        fin_solicitud = self.ahora + timedelta(minutes=30)

        datos_validos = {
            "nombre": "Convivencia Urgente de Costaleros",
            "lugar": "Casa Hermandad",
            "fecha": fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": inicio_solicitud,
            "fin_solicitud": fin_solicitud,
            "descripcion": "Acto convocado con carácter de urgencia."
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.fecha, fecha_acto)

        self.assertEqual(Acto.objects.count(), 1)
        self.assertEqual(nuevo_acto.nombre, "Convivencia Urgente de Costaleros")



    def test_crear_acto_fecha_formato_incorrecto_error(self):
        """
        Test: Crear acto con fecha en formato incorrecto

        Given: Un diccionario de datos donde el campo 'fecha' es una cadena 
            de texto no convertible a datetime (formato erróneo).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un error al intentar operar con la fecha.
        """
        datos_invalidos = {
            "nombre": "Ensayo de Costaleros - Error Fecha",
            "lugar": "Almacén de Pasos",
            "fecha": "formato-incorrecto-2026",
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        with self.assertRaises((DjangoValidationError, TypeError, ValueError, AttributeError)):
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tipo_acto_inexistente_error(self):
        """
        Test: Crear acto con tipo_acto inexistente

        Given: Un diccionario de datos donde el tipo_acto no existe 
            (ID inválido o nulo).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError de Django indicando que 
            el campo no puede ser nulo.
        """
        datos_invalidos = {
            "nombre": "Acto Fantasma",
            "lugar": "Ubicación Desconocida",
            "fecha": self.ahora + timedelta(days=10),
            "tipo_acto": None,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("tipo_acto", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["tipo_acto"][0],
            "This field cannot be null."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_modalidad_invalida_error(self):
        """
        Test: Crear acto con modalidad inválida

        Given: Un diccionario de datos donde la modalidad no pertenece 
            a las opciones válidas (TRADICIONAL o UNIFICADO).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError nativo de Django 
            indicando que el valor introducido no es una opción válida.
        """
        datos_invalidos = {
            "nombre": "Estación de Penitencia - Modalidad Errónea",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": "INVENTADA",
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("modalidad", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["modalidad"][0],
            "Value 'INVENTADA' is not a valid choice."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_exitoso_se_persiste_bd(self):
        """
        Test: Crear acto exitoso → se persiste en BD.

        Given: Un conjunto de datos totalmente válidos para un acto.
        When: El administrador invoca el servicio de creación.
        Then: La transacción se completa exitosamente y podemos 
            recuperar el objeto íntegro consultando la base de datos.
        """
        datos_validos = {
            "nombre": "Misa Solemne Extraordinaria",
            "lugar": "Altar Mayor",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "descripcion": "Acto para validar el commit de la transacción."
        }

        cantidad_inicial = Acto.objects.count()

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertIsNotNone(nuevo_acto.id)

        self.assertEqual(Acto.objects.count(), cantidad_inicial + 1)

        acto_en_bd = Acto.objects.get(id=nuevo_acto.id)
        self.assertEqual(acto_en_bd.nombre, "Misa Solemne Extraordinaria")
        self.assertEqual(acto_en_bd.lugar, "Altar Mayor")
        self.assertEqual(acto_en_bd.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_crear_acto_error_previo_rollback_ok(self):
        """
        Test: Crear acto tras error previo → transacción no deja datos corruptos.

        Given: Un intento de creación de acto con datos que violan las reglas 
            de negocio (ej: fechas de solicitud invertidas).
        When: El administrador invoca el servicio de creación.
        Then: El servicio debe lanzar una excepción y la base de datos no debe 
            haber persistido ningún registro (Rollback).
        """
        datos_invalidos = {
            "nombre": "Acto Fallido con Rollback",
            "lugar": "Parroquia",
            "fecha": self.ahora + timedelta(days=20),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=10),
            "fin_solicitud": self.ahora + timedelta(days=5),
            "descripcion": "Este acto no debería guardarse nunca."
        }

        self.assertEqual(Acto.objects.count(), 0)

        with self.assertRaises(DjangoValidationError):
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertEqual(Acto.objects.count(), 0, "La transacción no hizo rollback: hay un acto en la BD.")



    def test_crear_acto_error_validacion_modelo_no_persiste(self):
        """
        Test: Si falla validación de modelo → acto no debe persistirse.

        Given: Un conjunto de datos que superan la validación de tipos pero 
            violan una regla de negocio del clean() (inicio solicitud > fecha acto).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar una ValidationError y la base de datos 
            debe permanecer vacía (Rollback).
        """
        fecha_del_acto = self.ahora + timedelta(days=5)
        
        datos_invalidos = {
            "nombre": "Traslado Extraordinario",
            "lugar": "Calle Pureza",
            "fecha": fecha_del_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": fecha_del_acto + timedelta(days=1), 
            "fin_solicitud": fecha_del_acto + timedelta(days=2),
            "descripcion": "Validación de coherencia de fechas."
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("inicio_solicitud", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud"][0],
            "El inicio de solicitud no puede ser igual o posterior a la fecha del acto."
        )

        self.assertEqual(Acto.objects.count(), 0, "Error: El acto se persistió a pesar de fallar la validación.")



    def test_crear_acto_duplicado_no_se_guarda(self):
        """
        Test: Si falla validación de duplicado → acto no se guarda.

        Given: Un acto ya existente en la base de datos con un nombre 
            y fecha específicos.
        When: El administrador intenta crear otro acto con los mismos 
            datos exactos (nombre y fecha).
        Then: El sistema debe lanzar un error (ValidationError o IntegrityError) 
            y la base de datos no debe contener el duplicado.
        """
        datos_acto = {
            "nombre": "Solemne Besamanos",
            "lugar": "Capilla",
            "fecha": self.ahora + timedelta(days=20),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10)
        }

        crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_acto
        )
        self.assertEqual(Acto.objects.count(), 1)

        with self.assertRaises((DjangoValidationError, Exception)):
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_acto
            )

        self.assertEqual(Acto.objects.count(), 1, "Se ha creado un duplicado en la base de datos.")



    def test_crear_acto_excepcion_durante_create_rollback_completo(self):
        """
        Test: Si ocurre excepción durante create() → rollback completo.

        Given: Un conjunto de datos válidos.
        When: El servicio intenta persistir el acto pero ocurre una 
            excepción inesperada (ej: error de base de datos o integridad).
        Then: La base de datos debe revertir cualquier cambio y el contador 
            de actos debe permanecer en cero.
        """
        datos_validos = {
            "nombre": "Acto para Rollback Forzado",
            "lugar": "S.I. Catedral",
            "fecha": self.ahora + timedelta(days=30),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10)
        }

        datos_validos["nombre"] = "A" * 101

        with self.assertRaises((DjangoValidationError, Exception)):
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_validos
            )

        self.assertEqual(Acto.objects.count(), 0, "El rollback falló: se persistieron datos tras el error.")



    def test_crear_acto_nombre_limite_caracteres_ok(self):
        """
        Test: Crear acto con nombre extremadamente largo (límite 100 caracteres)

        Given: Un nombre de acto que tiene exactamente 100 caracteres.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe permitir la creación sin errores de truncado 
            ni excepciones de base de datos.
        """
        nombre_limite = "Acto de Fe y Caridad con motivo del Centenario de la Hermandad en la S.I. Catedral de la Ciudad 1926"
        self.assertEqual(len(nombre_limite), 100)

        datos_validos = {
            "nombre": nombre_limite,
            "lugar": "Centro Histórico",
            "fecha": self.ahora + timedelta(days=15),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertEqual(nuevo_acto.nombre, nombre_limite)
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_nombre_excede_limite_error(self):
        """
        Test: Crear acto con nombre que excede el límite (>100 caracteres)

        Given: Un nombre de acto con 101 caracteres.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar una ValidationError debido a la 
            restricción de max_length en el modelo.
        """
        nombre_excedido = "A" * 101

        datos_invalidos = {
            "nombre": nombre_excedido,
            "lugar": "Lugar Genérico",
            "fecha": self.ahora + timedelta(days=15),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("nombre", cm.exception.message_dict)



    def test_crear_acto_fecha_igual_fin_solicitud_ok(self):
        """
        Test: Crear acto con fecha exactamente igual al fin de solicitud.

        Given: Un conjunto de datos donde la fecha del acto coincide 
            exactamente con el fin del plazo de solicitud.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe permitir la creación (considerando que es 
            el último momento posible para solicitar).
        """
        fecha_limite = self.ahora + timedelta(days=10)

        datos_validos = {
            "nombre": "Traslado al Paso de Misterio",
            "lugar": "Capilla de la Hermandad",
            "fecha": fecha_limite,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": fecha_limite
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertEqual(nuevo_acto.fecha, nuevo_acto.fin_solicitud)
        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_fecha_inmediatamente_despues_fin_solicitud_ok(self):
        """
        Test: Crear acto con fecha exactamente después de fin de solicitud.

        Given: Un conjunto de datos donde el acto comienza exactamente 
            un minuto después de cerrar el plazo de solicitud.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe validar y persistir el acto correctamente, 
            ya que la cronología es lógica.
        """
        fin_plazo = self.ahora + timedelta(days=5)
        fecha_acto = fin_plazo + timedelta(minutes=1)

        datos_validos = {
            "nombre": "Solemne Traslado - Cierre de Plazo",
            "lugar": "Casa Hermandad",
            "fecha": fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": fin_plazo
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertTrue(nuevo_acto.fecha > nuevo_acto.fin_solicitud)
        self.assertEqual(Acto.objects.count(), 1)
        self.assertEqual(nuevo_acto.nombre, "Solemne Traslado - Cierre de Plazo")



    def test_crear_acto_zona_horaria_distinta_ok(self):
        """
        Test: Crear acto con zona horaria distinta.

        Given: Un conjunto de datos donde la fecha del acto viene 
            en una zona horaria distinta a la del sistema (ej: UTC).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe normalizar la fecha (o aceptarla como aware) 
            y persistir el acto correctamente en la base de datos.
        """
        zona_ny = pytz.timezone('America/New_York')
        fecha_con_tz = zona_ny.localize(datetime(2026, 5, 15, 12, 0, 0))

        datos_validos = {
            "nombre": "Convivencia Internacional",
            "lugar": "Sede Virtual / Zoom",
            "fecha": fecha_con_tz,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        nuevo_acto = crear_acto_service(
            usuario_solicitante=self.admin,
            data_validada=datos_validos
        )

        self.assertEqual(Acto.objects.count(), 1)
        self.assertEqual(nuevo_acto.fecha.astimezone(zona_ny), fecha_con_tz)



    def test_crear_actos_mismo_segundo_exacto_ok(self):
        """
        Test: Crear acto en el mismo segundo que otro.

        Given: Un acto ya existente en una fecha y hora exactas.
        When: El administrador crea un segundo acto (con distinto nombre 
            o lugar) pero con la misma estampa de tiempo exacta.
        Then: El sistema debe permitir ambos registros, ya que la fecha 
            no es un campo de clave única (Unique).
        """
        fecha_exacta = self.ahora + timedelta(days=15)

        datos_1 = {
            "nombre": "Exposición de Enseres",
            "lugar": "Sala Capitular",
            "fecha": fecha_exacta,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        datos_2 = {
            "nombre": "Convivencia de Acólitos",
            "lugar": "Casa Hermandad",
            "fecha": fecha_exacta,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        crear_acto_service(usuario_solicitante=self.admin, data_validada=datos_1)
        crear_acto_service(usuario_solicitante=self.admin, data_validada=datos_2)

        actos_en_ese_segundo = Acto.objects.filter(fecha=fecha_exacta).count()
        self.assertEqual(actos_en_ese_segundo, 2, "El sistema debería permitir actos simultáneos.")



    def test_crear_acto_data_validada_vacio_error(self):
        """
        Test: Crear acto con data_validada vacío.

        Given: Un diccionario de datos vacío ({}).
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError de Django indicando 
            que los campos obligatorios (nombre, lugar, fecha, tipo_acto) 
            no pueden estar vacíos.
        """
        datos_vacios = {}

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_vacios
            )

        errores = cm.exception.message_dict
        self.assertIn("nombre", errores)
        self.assertIn("lugar", errores)
        self.assertIn("fecha", errores)
        self.assertIn("tipo_acto", errores)

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_campos_inesperados_error_type(self):
        """
        Test: Crear acto con campos adicionales inesperados.

        Given: Un diccionario de datos que contiene campos válidos 
            y campos inventados (ej: 'campo_hacker', 'puntos_recompensa').
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un TypeError al intentar instanciar 
            el modelo con argumentos no reconocidos, protegiendo así 
            la base de datos de inyecciones de campos.
        """
        datos_con_basura = {
            "nombre": "Acto de Prueba - Campos Extra",
            "lugar": "Sede Social",
            "fecha": self.ahora + timedelta(days=20),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "campo_hacker": "intento_de_inyeccion",
            "puntos_recompensa": 999
        }

        with self.assertRaises(TypeError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_con_basura
            )

        error_msg = str(cm.exception)
        self.assertIn("unexpected keyword argument", error_msg)
        self.assertIn("campo_hacker", error_msg)

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_nombre_nulo_error(self):
        """
        Test: Crear acto con nombre=None.

        Given: Un diccionario de datos donde el nombre es explícitamente None.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que 
            este campo no puede ser nulo.
        """
        datos_invalidos = {
            "nombre": None,
            "lugar": "Parroquia de Santa Ana",
            "fecha": self.ahora + timedelta(days=15),
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("nombre", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["nombre"][0],
            "This field cannot be null."
        )

        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_fecha_nula_error(self):
        """
        Test: Crear acto con fecha=None.

        Given: Un diccionario de datos donde la fecha es explícitamente None.
        When: El administrador invoca el servicio de creación.
        Then: El sistema debe lanzar un ValidationError indicando que 
            este campo no puede ser nulo.
        """
        datos_invalidos = {
            "nombre": "Ensayo General",
            "lugar": "Casa Hermandad",
            "fecha": None,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=1),
            "fin_solicitud": self.ahora + timedelta(days=5)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            crear_acto_service(
                usuario_solicitante=self.admin,
                data_validada=datos_invalidos
            )

        self.assertIn("fecha", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["fecha"][0],
            "This field cannot be null."
        )

        self.assertEqual(Acto.objects.count(), 0)