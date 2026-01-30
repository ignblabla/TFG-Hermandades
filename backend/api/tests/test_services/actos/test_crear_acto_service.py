from zoneinfo import ZoneInfo
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

from ....models import Acto, TipoActo, Hermano
from ....services import crear_acto_service
from api.tests.factories import HermanoFactory

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
            "descripcion": "Acto unificado",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

    

    def test_admin_crea_acto_sin_papeleta_ok(self):
        """
        Test: Admin crea acto sin papeleta (tipo_acto.requiere_papeleta = False)

        Given: tipo_acto sin papeleta.
        When: data_validada incluye nombre, fecha, tipo_acto, descripcion opcional.
        Then: se crea Acto; modalidad y fechas de solicitud quedan None.
        """
        data_validada = self.acto_no_papeleta_ok.copy()

        acto = crear_acto_service(self.admin, data_validada)

        self.assertIsNotNone(acto.id)
        self.assertEqual(acto.nombre, data_validada["nombre"])
        self.assertEqual(acto.tipo_acto, self.tipo_no_papeleta)
        self.assertEqual(acto.fecha, data_validada["fecha"])
        self.assertEqual(acto.descripcion, data_validada["descripcion"])

        self.assertIsNone(acto.modalidad)
        self.assertIsNone(acto.inicio_solicitud)
        self.assertIsNone(acto.fin_solicitud)
        self.assertIsNone(acto.inicio_solicitud_cirios)
        self.assertIsNone(acto.fin_solicitud_cirios)

        self.assertTrue(Acto.objects.filter(id=acto.id).exists())



    def test_admin_crea_acto_sin_papeleta_con_descripcion_ok(self):
        """
        Test: Admin crea acto sin papeleta incluyendo descripción

        Given: tipo_acto que no requiere papeleta.
        When: data_validada incluye nombre, fecha, tipo_acto y descripción.
        Then: el acto se crea y la descripción se persiste correctamente.
        """
        # Given
        data_validada = {
            "nombre": "Convivencia con descripción",
            "descripcion": "Descripción opcional del acto",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        acto = crear_acto_service(self.admin, data_validada)

        self.assertIsNotNone(acto.id)
        self.assertEqual(acto.nombre, "Convivencia con descripción")
        self.assertEqual(acto.descripcion, "Descripción opcional del acto")
        self.assertEqual(acto.tipo_acto, self.tipo_no_papeleta)

        self.assertIsNone(acto.modalidad)
        self.assertIsNone(acto.inicio_solicitud)
        self.assertIsNone(acto.fin_solicitud)
        self.assertIsNone(acto.inicio_solicitud_cirios)
        self.assertIsNone(acto.fin_solicitud_cirios)

        acto_db = Acto.objects.get(id=acto.id)
        self.assertEqual(acto_db.descripcion, "Descripción opcional del acto")



    def test_admin_crea_acto_con_papeleta_unificado_fechas_validas_ok(self):
        """
        Test: Admin crea acto con papeleta modalidad UNIFICADO (fechas válidas)

        Given: requiere_papeleta=True, modalidad=UNIFICADO,
            inicio_solicitud < fin_solicitud <= fecha,
            e inicio_solicitud_cirios=None, fin_solicitud_cirios=None.
        When: se llama a crear_acto_service con data_validada.
        Then: se crea el Acto correctamente.
        """
        data_validada = self.acto_unificado_ok.copy()

        acto = crear_acto_service(self.admin, data_validada)

        self.assertIsNotNone(acto.id)
        self.assertEqual(acto.tipo_acto, self.tipo_con_papeleta)
        self.assertEqual(acto.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertEqual(acto.inicio_solicitud, self.inicio_insignias)
        self.assertEqual(acto.fin_solicitud, self.fin_insignias)
        self.assertEqual(acto.fecha, self.fecha_acto)

        self.assertIsNone(acto.inicio_solicitud_cirios)
        self.assertIsNone(acto.fin_solicitud_cirios)

        self.assertTrue(Acto.objects.filter(id=acto.id).exists())



    def test_admin_crea_acto_con_papeleta_tradicional_fases_validas_encadenadas_ok(self):
        """
        Test: Admin crea acto con papeleta modalidad TRADICIONAL (fases válidas y encadenadas)

        Given: inicio_solicitud < fin_solicitud < inicio_solicitud_cirios < fin_solicitud_cirios <= fecha.
        When: se llama a crear_acto_service con data_validada.
        Then: se crea el Acto correctamente.
        """
        data_validada = self.acto_tradicional_ok.copy()

        acto = crear_acto_service(self.admin, data_validada)

        self.assertIsNotNone(acto.id)
        self.assertEqual(acto.tipo_acto, self.tipo_con_papeleta)
        self.assertEqual(acto.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(acto.inicio_solicitud, self.inicio_insignias)
        self.assertEqual(acto.fin_solicitud, self.fin_insignias)

        self.assertEqual(acto.inicio_solicitud_cirios, self.inicio_cirios)
        self.assertEqual(acto.fin_solicitud_cirios, self.fin_cirios)

        self.assertEqual(acto.fecha, self.fecha_acto)

        self.assertTrue(Acto.objects.filter(id=acto.id).exists())



    def test_admin_crea_acto_mismo_nombre_dias_distintos_ok(self):
        """
        Test: Mismo nombre en días distintos

        Given: ya existe un Acto llamado "Cabildo" el día 2026-02-01.
        When: se crea otro Acto llamado "Cabildo" el día 2026-02-02.
        Then: la creación es válida y no lanza error.
        """
        fecha_1 = self.fecha_acto.replace(day=1, month=2, year=2026)
        fecha_2 = self.fecha_acto.replace(day=2, month=2, year=2026)

        crear_acto_service(self.admin, {
            "nombre": "Cabildo",
            "descripcion": "Primer cabildo",
            "fecha": fecha_1,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        })

        acto_2 = crear_acto_service(self.admin, {
            "nombre": "Cabildo",
            "descripcion": "Segundo cabildo",
            "fecha": fecha_2,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        })

        self.assertIsNotNone(acto_2.id)
        self.assertEqual(acto_2.nombre, "Cabildo")
        self.assertEqual(acto_2.fecha.date(), fecha_2.date())

        self.assertEqual(
            Acto.objects.filter(nombre="Cabildo").count(),
            2
        )



    def test_admin_crea_acto_mismo_nombre_mismo_dia_distinta_hora_falla(self):
        """
        Test: Mismo nombre el mismo día pero distinta hora -> FALLA

        Given: ya existe un Acto llamado "Cabildo" el día 2026-02-01 a las 10:00.
        When: se intenta crear "Cabildo" el mismo día a las 18:00.
        Then: falla por unicidad (nombre + fecha__date).
        """

        fecha_10 = self.fecha_acto.replace(year=2026, month=2, day=1, hour=10, minute=0, second=0, microsecond=0)
        fecha_18 = self.fecha_acto.replace(year=2026, month=2, day=1, hour=18, minute=0, second=0, microsecond=0)

        crear_acto_service(self.admin, {
            "nombre": "Cabildo",
            "descripcion": "Cabildo mañana",
            "fecha": fecha_10,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        })

        with self.assertRaises(DRFValidationError) as ctx:
            crear_acto_service(self.admin, {
                "nombre": "Cabildo",
                "descripcion": "Cabildo tarde",
                "fecha": fecha_18,
                "tipo_acto": self.tipo_no_papeleta,
                "modalidad": None,
                "inicio_solicitud": None,
                "fin_solicitud": None,
                "inicio_solicitud_cirios": None,
                "fin_solicitud_cirios": None,
            })

        self.assertIn("Ya existe el acto 'Cabildo' en esa fecha.", str(ctx.exception))



    def test_admin_crea_acto_distinto_nombre_mismo_dia_ok(self):
        """
        Test: Distinto nombre el mismo día -> OK

        Given: ya existe un Acto llamado "Cabildo" el día 2026-02-01.
        When: se crea otro Acto con nombre distinto ("Cabildo Extraordinario") el mismo día (aunque cambie la hora o no).
        Then: OK, porque la unicidad del service es por (nombre + fecha__date).
        """
        fecha_10 = self.fecha_acto.replace(year=2026, month=2, day=1, hour=10, minute=0, second=0, microsecond=0)
        fecha_18 = self.fecha_acto.replace(year=2026, month=2, day=1, hour=18, minute=0, second=0, microsecond=0)

        crear_acto_service(self.admin, {
            "nombre": "Cabildo",
            "descripcion": "Cabildo mañana",
            "fecha": fecha_10,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        })

        acto_2 = crear_acto_service(self.admin, {
            "nombre": "Cabildo Extraordinario",
            "descripcion": "Cabildo tarde",
            "fecha": fecha_18,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        })

        self.assertIsNotNone(acto_2.id)
        self.assertEqual(acto_2.nombre, "Cabildo Extraordinario")
        self.assertEqual(acto_2.fecha.date(), fecha_18.date())

        self.assertTrue(Acto.objects.filter(nombre="Cabildo", fecha__date=fecha_10.date()).exists())
        self.assertTrue(Acto.objects.filter(nombre="Cabildo Extraordinario", fecha__date=fecha_18.date()).exists())



    def test_admin_crea_acto_unificado_fin_solicitud_igual_fecha_ok(self):
        """
        Test: UNIFICADO con fin_solicitud == fecha -> OK

        Given: requiere_papeleta=True, modalidad=UNIFICADO,
            inicio_solicitud < fin_solicitud == fecha,
            inicio_solicitud_cirios=None, fin_solicitud_cirios=None.
        When: se crea el acto.
        Then: OK, porque clean() solo prohíbe fin_solicitud > fecha (permite igualdad).
        """
        # Given
        fecha_acto = self.fecha_acto.replace(year=2026, month=3, day=10, hour=20, minute=0, second=0, microsecond=0)
        inicio = fecha_acto - timedelta(days=2)
        fin = fecha_acto

        data_validada = {
            "nombre": "Acto Unificado fin==fecha",
            "descripcion": "Caso borde permitido",
            "fecha": fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": inicio,
            "fin_solicitud": fin,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        acto = crear_acto_service(self.admin, data_validada)

        self.assertIsNotNone(acto.id)
        self.assertEqual(acto.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertEqual(acto.inicio_solicitud, inicio)
        self.assertEqual(acto.fin_solicitud, fin)
        self.assertEqual(acto.fecha, fecha_acto)

        self.assertIsNone(acto.inicio_solicitud_cirios)
        self.assertIsNone(acto.fin_solicitud_cirios)

        self.assertTrue(Acto.objects.filter(id=acto.id).exists())



    def test_admin_crea_acto_tradicional_fin_cirios_igual_fecha_ok(self):
        """
        Test: TRADICIONAL con fin_solicitud_cirios == fecha -> OK

        Given: requiere_papeleta=True, modalidad=TRADICIONAL,
            inicio_solicitud < fin_solicitud < inicio_solicitud_cirios < fin_solicitud_cirios == fecha.
        When: se crea el acto.
        Then: OK, porque clean() solo prohíbe fin_solicitud_cirios > fecha (permite igualdad).
        """
        fecha_acto = self.fecha_acto.replace(year=2026, month=4, day=5, hour=21, minute=0, second=0, microsecond=0)

        inicio_insignias = fecha_acto - timedelta(days=6)
        fin_insignias = fecha_acto - timedelta(days=4)

        inicio_cirios = fecha_acto - timedelta(days=2)
        fin_cirios = fecha_acto

        data_validada = {
            "nombre": "Acto Tradicional fin cirios == fecha",
            "descripcion": "Caso borde permitido",
            "fecha": fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_insignias,
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios,
        }

        acto = crear_acto_service(self.admin, data_validada)

        self.assertIsNotNone(acto.id)
        self.assertEqual(acto.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(acto.inicio_solicitud, inicio_insignias)
        self.assertEqual(acto.fin_solicitud, fin_insignias)

        self.assertEqual(acto.inicio_solicitud_cirios, inicio_cirios)
        self.assertEqual(acto.fin_solicitud_cirios, fin_cirios)

        self.assertEqual(acto.fecha, fecha_acto)

        self.assertTrue(Acto.objects.filter(id=acto.id).exists())



    def test_usuario_no_admin_intenta_crear_acto_falla_por_permisos(self):
        """
        Test: Usuario no admin intenta crear acto

        Given: usuario_solicitante.esAdmin = False.
        When: intenta crear un acto válido.
        Then: PermissionDenied("No tienes permisos...").
        """
        data_validada = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(DRFPermissionDenied) as ctx:
            crear_acto_service(self.hermano, data_validada)

        self.assertIn(
            "No tienes permisos para crear actos. Se requiere ser Administrador.",
            str(ctx.exception)
        )



    def test_usuario_sin_atributo_esAdmin_intenta_crear_acto_falla_por_permisos(self):
        """
        Test: usuario_solicitante es un objeto sin atributo esAdmin

        Given: usuario_solicitante no tiene atributo esAdmin (getattr(..., False) => False).
        When: intenta crear un acto válido.
        Then: PermissionDenied.
        """
        class UsuarioSinAdmin:
            pass

        usuario = UsuarioSinAdmin()
        data_validada = self.acto_no_papeleta_ok.copy()

        with self.assertRaises(DRFPermissionDenied) as ctx:
            crear_acto_service(usuario, data_validada)

        self.assertIn(
            "No tienes permisos para crear actos. Se requiere ser Administrador.",
            str(ctx.exception)
        )



    def test_admin_crea_acto_duplicado_mismo_nombre_mismo_dia_falla(self):
        """
        Test: Acto duplicado por (nombre + fecha en el mismo día)

        Given: existe Acto con nombre="Cabildo" y fecha 2026-02-01 10:00.
        When: se intenta crear otro Acto con nombre="Cabildo" y fecha 2026-02-01 20:00.
        Then: falla porque el service valida unicidad por nombre + fecha__date.
        """
        fecha_manana = self.fecha_acto.replace(
            year=2026, month=2, day=1, hour=10, minute=0, second=0, microsecond=0
        )
        fecha_tarde = self.fecha_acto.replace(
            year=2026, month=2, day=1, hour=20, minute=0, second=0, microsecond=0
        )

        crear_acto_service(self.admin, {
            "nombre": "Cabildo",
            "descripcion": "Cabildo de mañana",
            "fecha": fecha_manana,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        })

        with self.assertRaises(DRFValidationError) as ctx:
            crear_acto_service(self.admin, {
                "nombre": "Cabildo",
                "descripcion": "Cabildo de tarde",
                "fecha": fecha_tarde,
                "tipo_acto": self.tipo_no_papeleta,
                "modalidad": None,
                "inicio_solicitud": None,
                "fin_solicitud": None,
                "inicio_solicitud_cirios": None,
                "fin_solicitud_cirios": None,
            })

        self.assertIn(
            "Ya existe el acto 'Cabildo' en esa fecha.",
            str(ctx.exception)
        )



    def test_admin_crea_acto_nombre_igual_datetime_equivalente_distinta_tz_mismo_dia_falla(self):
        """
        Test: Edge - nombre coincide, pero la fecha cambia solo por zona horaria (datetime equivalente)

        Given: existe Acto "Cabildo" con fecha tz-aware (Europe/Madrid) en 2026-02-01.
        When: intentas crear "Cabildo" con un datetime equivalente (misma hora instantánea) pero en UTC,
            y al hacer fecha.date() cae en el mismo día (2026-02-01).
        Then: debe fallar igual porque el service valida por nombre + fecha__date (mismo date()).
        """
        madrid = ZoneInfo("Europe/Madrid")
        utc = ZoneInfo("UTC")

        fecha_madrid = self.fecha_acto.replace(
            year=2026, month=2, day=1, hour=10, minute=0, second=0, microsecond=0, tzinfo=madrid
        )
        fecha_utc_equivalente = self.fecha_acto.replace(
            year=2026, month=2, day=1, hour=9, minute=0, second=0, microsecond=0, tzinfo=utc
        )

        self.assertEqual(fecha_madrid.astimezone(utc), fecha_utc_equivalente)

        self.assertEqual(fecha_madrid.date(), fecha_utc_equivalente.date())
        self.assertEqual(fecha_madrid.date().isoformat(), "2026-02-01")

        crear_acto_service(self.admin, {
            "nombre": "Cabildo",
            "descripcion": "Cabildo creado en tz Madrid",
            "fecha": fecha_madrid,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        })

        with self.assertRaises(DRFValidationError) as ctx:
            crear_acto_service(self.admin, {
                "nombre": "Cabildo",
                "descripcion": "Cabildo equivalente en UTC",
                "fecha": fecha_utc_equivalente,
                "tipo_acto": self.tipo_no_papeleta,
                "modalidad": None,
                "inicio_solicitud": None,
                "fin_solicitud": None,
                "inicio_solicitud_cirios": None,
                "fin_solicitud_cirios": None,
            })

        self.assertIn("Ya existe el acto 'Cabildo' en esa fecha.", str(ctx.exception))



    def test_admin_crea_acto_con_nombre_none_falla_por_modelo(self):
        """
        Test: nombre=None

        Given: data_validada tiene nombre=None (service no entra en la unicidad).
        When: se intenta crear el acto.
        Then: falla por full_clean() del modelo con ValidationError en 'nombre'.
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["nombre"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("nombre", ctx.exception.message_dict)
        self.assertIn("This field cannot be null.", ctx.exception.message_dict["nombre"])



    def test_admin_crea_acto_con_fecha_none_falla_por_modelo(self):
        """
        Test: fecha=None

        Given: data_validada tiene fecha=None (service no entra en la unicidad).
        When: se intenta crear el acto.
        Then: falla por full_clean() del modelo con ValidationError en 'fecha'.
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["fecha"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fecha", ctx.exception.message_dict)
        self.assertIn("This field cannot be null.", ctx.exception.message_dict["fecha"])



    def test_admin_crea_acto_tipo_sin_papeleta_con_modalidad_falla(self):
        """
        Test: Tipo sin papeleta pero se envía modalidad

        Given: tipo_acto.requiere_papeleta = False.
        When: data_validada incluye modalidad.
        Then: ValidationError con error en 'modalidad'
            ("Un acto que no requiere papeleta no puede tener modalidad.").
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["modalidad"] = Acto.ModalidadReparto.UNIFICADO

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("modalidad", ctx.exception.message_dict)
        self.assertIn(
            "Un acto que no requiere papeleta",
            ctx.exception.message_dict["modalidad"][0]
        )



    def test_admin_crea_acto_tipo_sin_papeleta_con_inicio_solicitud_falla(self):
        """
        Test: Tipo sin papeleta pero se envía inicio_solicitud

        Given: tipo_acto.requiere_papeleta = False.
        When: data_validada incluye inicio_solicitud.
        Then: ValidationError con error en 'inicio_solicitud'
            ("Un acto que no requiere papeleta no puede tener fechas de solicitud.").
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["inicio_solicitud"] = self.inicio_insignias

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "Un acto que no requiere papeleta",
            ctx.exception.message_dict["inicio_solicitud"][0]
        )



    def test_admin_crea_acto_tipo_sin_papeleta_con_fin_solicitud_falla(self):
        """
        Test: Tipo sin papeleta pero se envía fin_solicitud

        Given: tipo_acto.requiere_papeleta = False.
        When: data_validada incluye fin_solicitud.
        Then: ValidationError con error en 'fin_solicitud'
            ("Un acto que no requiere papeleta no puede tener fechas de solicitud.").
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["fin_solicitud"] = self.fin_insignias

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "Un acto que no requiere papeleta",
            ctx.exception.message_dict["fin_solicitud"][0]
        )



    def test_admin_crea_acto_tipo_sin_papeleta_con_fechas_cirios_falla(self):
        """
        Test: Tipo sin papeleta pero se envían fechas de cirios

        Given: tipo_acto.requiere_papeleta = False.
        When: data_validada incluye inicio_solicitud_cirios y/o fin_solicitud_cirios.
        Then: ValidationError con error en inicio_solicitud_cirios y/o fin_solicitud_cirios
            ("Un acto que no requiere papeleta no puede tener fechas de solicitud.").
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["inicio_solicitud_cirios"] = self.inicio_cirios
        data_validada["fin_solicitud_cirios"] = self.fin_cirios

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertTrue(
            "inicio_solicitud_cirios" in ctx.exception.message_dict
            or "fin_solicitud_cirios" in ctx.exception.message_dict
        )

        errores = ctx.exception.message_dict
        if "inicio_solicitud_cirios" in errores:
            self.assertIn(
                "no requiere papeleta",
                errores["inicio_solicitud_cirios"][0]
            )
        if "fin_solicitud_cirios" in errores:
            self.assertIn(
                "no requiere papeleta",
                errores["fin_solicitud_cirios"][0]
            )



    def test_admin_crea_acto_tipo_sin_papeleta_con_multiples_campos_prohibidos_falla_con_varios_errores(self):
        """
        Test: Tipo sin papeleta pero envías varias cosas prohibidas a la vez

        Given: tipo_acto.requiere_papeleta = False.
        When: envías modalidad + varias fechas (insignias y cirios) a la vez.
        Then: ValidationError con múltiples claves en message_dict (acumula errores en `errors`).
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada.update({
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        })

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        errores = ctx.exception.message_dict

        self.assertGreaterEqual(len(errores.keys()), 2)

        self.assertIn("modalidad", errores)
        self.assertIn("inicio_solicitud", errores)
        self.assertIn("fin_solicitud", errores)
        self.assertIn("inicio_solicitud_cirios", errores)
        self.assertIn("fin_solicitud_cirios", errores)

        self.assertIn("no requiere papeleta", errores["modalidad"][0].lower())
        self.assertIn("no requiere papeleta", errores["inicio_solicitud"][0].lower())
        self.assertIn("no requiere papeleta", errores["fin_solicitud"][0].lower())
        self.assertIn("no requiere papeleta", errores["inicio_solicitud_cirios"][0].lower())
        self.assertIn("no requiere papeleta", errores["fin_solicitud_cirios"][0].lower())



    def test_admin_crea_acto_con_papeleta_sin_modalidad_falla(self):
        """
        Test: Falta modalidad

        Given: tipo_acto.requiere_papeleta = True.
        When: data_validada no incluye modalidad (modalidad=None) pero sí fechas obligatorias.
        Then: ValidationError con error en 'modalidad'.
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["modalidad"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("modalidad", ctx.exception.message_dict)
        self.assertIn(
            "La modalidad es obligatoria para actos con papeleta.",
            ctx.exception.message_dict["modalidad"]
        )



    def test_admin_crea_acto_con_papeleta_sin_inicio_solicitud_falla(self):
        """
        Test: Falta inicio_solicitud

        Given: tipo_acto.requiere_papeleta = True.
        When: data_validada no incluye inicio_solicitud.
        Then: ValidationError con error en 'inicio_solicitud'.
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["inicio_solicitud"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "El inicio de solicitud es obligatorio.",
            ctx.exception.message_dict["inicio_solicitud"]
        )



    def test_admin_crea_acto_con_papeleta_sin_fin_solicitud_falla(self):
        """
        Test: Falta fin_solicitud

        Given: tipo_acto.requiere_papeleta = True.
        When: data_validada no incluye fin_solicitud.
        Then: ValidationError con error en 'fin_solicitud'.
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["fin_solicitud"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "El fin de solicitud es obligatorio.",
            ctx.exception.message_dict["fin_solicitud"]
        )



    def test_admin_crea_acto_inicio_solicitud_igual_fin_solicitud_falla(self):
        """
        Test: inicio_solicitud == fin_solicitud

        Given: tipo_acto.requiere_papeleta = True y modalidad válida.
        When: inicio_solicitud == fin_solicitud.
        Then: ValidationError con error en 'fin_solicitud'
            ("El fin de solicitud debe ser posterior al inicio.").
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["inicio_solicitud"] = self.inicio_insignias
        data_validada["fin_solicitud"] = self.inicio_insignias

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud"][0]
        )



    def test_admin_crea_acto_inicio_solicitud_mayor_que_fin_solicitud_falla(self):
        """
        Test: inicio_solicitud > fin_solicitud

        Given: tipo_acto.requiere_papeleta = True y modalidad válida.
        When: inicio_solicitud es posterior a fin_solicitud.
        Then: ValidationError con error en 'fin_solicitud'
            ("El fin de solicitud debe ser posterior al inicio.").
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["inicio_solicitud"] = self.fin_insignias
        data_validada["fin_solicitud"] = self.inicio_insignias

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud"][0]
        )



    def test_admin_crea_acto_inicio_solicitud_igual_o_posterior_a_fecha_falla(self):
        """
        Test: inicio_solicitud >= fecha

        Given: tipo_acto.requiere_papeleta = True y modalidad válida.
        When: inicio_solicitud es igual o posterior a la fecha del acto.
        Then: ValidationError con error en 'inicio_solicitud'
            ("El inicio de solicitud no puede ser igual o posterior a la fecha del acto.").
        """
        data_validada = self.acto_unificado_ok.copy()

        data_validada["inicio_solicitud"] = self.fecha_acto

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud"][0]
        )

        data_validada = self.acto_unificado_ok.copy()
        data_validada["inicio_solicitud"] = self.fecha_acto + timedelta(hours=1)

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud"][0]
        )



    def test_admin_crea_acto_fin_solicitud_posterior_a_fecha_falla(self):
        """
        Test: fin_solicitud > fecha

        Given: tipo_acto.requiere_papeleta = True y modalidad válida.
        When: fin_solicitud es posterior a la fecha del acto.
        Then: ValidationError con error en 'fin_solicitud'
            ("El fin de solicitud no puede ser posterior a la fecha del acto.").
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["fin_solicitud"] = self.fecha_acto + timedelta(hours=1)

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser posterior a la fecha del acto",
            ctx.exception.message_dict["fin_solicitud"][0]
        )



    def test_admin_crea_acto_tradicional_sin_inicio_solicitud_cirios_falla(self):
        """
        Test: TRADICIONAL sin inicio_solicitud_cirios

        Given: tipo_acto.requiere_papeleta = True y modalidad = TRADICIONAL.
        When: falta inicio_solicitud_cirios.
        Then: ValidationError con error en 'inicio_solicitud_cirios'
            ("El inicio de cirios es obligatorio en modalidad tradicional.").
        """
        data_validada = self.acto_tradicional_ok.copy()
        data_validada["inicio_solicitud_cirios"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "obligatorio en modalidad tradicional",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )



    def test_admin_crea_acto_tradicional_sin_fin_solicitud_cirios_falla(self):
        """
        Test: TRADICIONAL sin fin_solicitud_cirios

        Given: tipo_acto.requiere_papeleta = True y modalidad = TRADICIONAL.
        When: falta fin_solicitud_cirios.
        Then: ValidationError con error en 'fin_solicitud_cirios'
            ("El fin de cirios es obligatorio en modalidad tradicional.").
        """
        data_validada = self.acto_tradicional_ok.copy()
        data_validada["fin_solicitud_cirios"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "obligatorio en modalidad tradicional",
            ctx.exception.message_dict["fin_solicitud_cirios"][0]
        )



    def test_admin_crea_acto_tradicional_inicio_cirios_igual_fin_cirios_falla(self):
        """
        Test: inicio_solicitud_cirios == fin_solicitud_cirios

        Given: tipo_acto.requiere_papeleta = True y modalidad = TRADICIONAL.
        When: inicio_solicitud_cirios es igual a fin_solicitud_cirios.
        Then: ValidationError con error en 'fin_solicitud_cirios'
            ("El fin de cirios debe ser posterior al inicio.").
        """
        data_validada = self.acto_tradicional_ok.copy()
        data_validada["inicio_solicitud_cirios"] = self.inicio_cirios
        data_validada["fin_solicitud_cirios"] = self.inicio_cirios

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud_cirios"][0]
        )



    def test_admin_crea_acto_tradicional_inicio_cirios_mayor_que_fin_cirios_falla(self):
        """
        Test: inicio_solicitud_cirios > fin_solicitud_cirios

        Given: tipo_acto.requiere_papeleta = True y modalidad = TRADICIONAL.
        When: inicio_solicitud_cirios es posterior a fin_solicitud_cirios.
        Then: ValidationError con error en 'fin_solicitud_cirios'
            ("El fin de cirios debe ser posterior al inicio.").
        """
        data_validada = self.acto_tradicional_ok.copy()
        data_validada["inicio_solicitud_cirios"] = self.fin_cirios
        data_validada["fin_solicitud_cirios"] = self.inicio_cirios

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud_cirios"][0]
        )



    def test_admin_crea_acto_tradicional_inicio_cirios_igual_o_posterior_a_fecha_falla(self):
        """
        Test: inicio_solicitud_cirios >= fecha

        Given: tipo_acto.requiere_papeleta = True y modalidad = TRADICIONAL.
        When: inicio_solicitud_cirios es igual o posterior a la fecha del acto.
        Then: ValidationError con error en 'inicio_solicitud_cirios'
            ("El inicio de cirios no puede ser igual o posterior a la fecha del acto.").
        """
        data_validada = self.acto_tradicional_ok.copy()

        data_validada["inicio_solicitud_cirios"] = self.fecha_acto

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )

        data_validada = self.acto_tradicional_ok.copy()
        data_validada["inicio_solicitud_cirios"] = self.fecha_acto + timedelta(hours=1)

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )



    def test_admin_crea_acto_tradicional_fin_cirios_posterior_a_fecha_falla(self):
        """
        Test: fin_solicitud_cirios > fecha

        Given: tipo_acto.requiere_papeleta = True y modalidad = TRADICIONAL.
        When: fin_solicitud_cirios es posterior a la fecha del acto.
        Then: ValidationError con error en 'fin_solicitud_cirios'
            ("El fin de cirios no puede ser posterior a la fecha del acto.").
        """
        data_validada = self.acto_tradicional_ok.copy()
        data_validada["fin_solicitud_cirios"] = self.fecha_acto + timedelta(hours=1)

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser posterior a la fecha del acto",
            ctx.exception.message_dict["fin_solicitud_cirios"][0]
        )



    def test_admin_crea_acto_tradicional_conflicto_fases_fin_insignias_mayor_o_igual_inicio_cirios_falla(self):
        """
        Test: Conflicto de fases (fin_solicitud >= inicio_solicitud_cirios)

        Given: tipo_acto.requiere_papeleta = True y modalidad = TRADICIONAL.
            inicio_solicitud < fin_solicitud >= inicio_solicitud_cirios < fin_solicitud_cirios <= fecha.
        When: fin_solicitud es igual o posterior al inicio de cirios.
        Then: ValidationError con error en 'inicio_solicitud_cirios' y mensaje:
            "El período de cirios debe comenzar después de finalizar el de insignias."
        """
        data_validada = self.acto_tradicional_ok.copy()

        data_validada["fin_solicitud"] = self.inicio_cirios
        data_validada["inicio_solicitud_cirios"] = self.inicio_cirios

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "El período de cirios debe comenzar después",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )



    def test_tradicional_orden_global_invalido_por_fin_cirios_no_posterior_sale_error_especifico(self):
        """
        Test: Orden global inválido, pero el fallo real es fin_cirios no posterior a inicio_cirios

        Given: inicio_solicitud < fin_solicitud < inicio_cirios
            pero inicio_cirios >= fin_cirios (rompe el orden global)
        Then: error en fin_solicitud_cirios con mensaje específico ("posterior al inicio"),
            no el genérico de "Orden de fases incorrecto".
        """
        data_validada = self.acto_tradicional_ok.copy()
        data_validada["inicio_solicitud_cirios"] = self.inicio_cirios
        data_validada["fin_solicitud_cirios"] = self.inicio_cirios

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn("posterior al inicio", ctx.exception.message_dict["fin_solicitud_cirios"][0])



    def test_admin_crea_acto_unificado_con_inicio_cirios_informado_falla(self):
        """
        Test: UNIFICADO con inicio_solicitud_cirios informado

        Given: tipo_acto.requiere_papeleta=True, modalidad=UNIFICADO.
        When: se informa inicio_solicitud_cirios (no permitido en UNIFICADO).
        Then: ValidationError con error en 'modalidad'
            ("En modalidad UNIFICADO no se deben definir fechas de cirios.").
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["inicio_solicitud_cirios"] = self.inicio_cirios

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("modalidad", ctx.exception.message_dict)
        self.assertIn(
            "no se deben definir fechas de cirios",
            ctx.exception.message_dict["modalidad"][0]
        )



    def test_admin_crea_acto_unificado_con_fin_cirios_informado_falla(self):
        """
        Test: UNIFICADO con fin_solicitud_cirios informado

        Given: tipo_acto.requiere_papeleta = True y modalidad = UNIFICADO.
        When: se informa fin_solicitud_cirios (campo prohibido en UNIFICADO).
        Then: ValidationError con error en 'modalidad'
            ("En modalidad UNIFICADO no se deben definir fechas de cirios.").
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["fin_solicitud_cirios"] = self.fin_cirios

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("modalidad", ctx.exception.message_dict)
        self.assertIn(
            "no se deben definir fechas de cirios",
            ctx.exception.message_dict["modalidad"][0]
        )



    def test_admin_crea_acto_unificado_con_ambas_fechas_cirios_informadas_falla(self):
        """
        Test: UNIFICADO con ambas fechas de cirios informadas

        Given: tipo_acto.requiere_papeleta = True y modalidad = UNIFICADO.
        When: se informan inicio_solicitud_cirios y fin_solicitud_cirios a la vez.
        Then: ValidationError con un único error en 'modalidad'
            ("En modalidad UNIFICADO no se deben definir fechas de cirios.").
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada.update({
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        })

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        errores = ctx.exception.message_dict

        self.assertIn("modalidad", errores)
        self.assertEqual(len(errores.keys()), 1)

        self.assertIn(
            "no se deben definir fechas de cirios",
            errores["modalidad"][0]
        )



    def test_admin_crea_acto_sin_tipo_acto_falla(self):
        """
        Test: tipo_acto no viene

        Given: data_validada no incluye tipo_acto (queda None).
        When: se intenta crear el acto.
        Then: ValidationError con clave 'tipo_acto' y mensaje:
            "El tipo de acto es obligatorio."
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["tipo_acto"] = None

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("tipo_acto", ctx.exception.message_dict)
        self.assertIn(
            "El tipo de acto es obligatorio.",
            ctx.exception.message_dict["tipo_acto"]
        )



    def test_admin_crea_acto_con_tipo_acto_id_inexistente_falla(self):
        """
        Test: tipo_acto_id inválido (FK no existe)

        Given: data_validada incluye tipo_acto_id con un id que no existe.
        When: se intenta crear el acto.
        Then: falla. En este flujo concreto, Django puede lanzar TipoActo.DoesNotExist
            al intentar resolver el FK (antes de llegar a BD).
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada.pop("tipo_acto", None)
        data_validada["tipo_acto_id"] = 999999

        with self.assertRaises((TipoActo.DoesNotExist, DjangoValidationError, IntegrityError)):
            crear_acto_service(self.admin, data_validada)



    def test_admin_crea_acto_con_modalidad_no_permitida_falla_por_choices(self):
        """
        Test: modalidad con valor no permitido

        Given: tipo_acto.requiere_papeleta = True.
        When: modalidad tiene un valor que no está en Acto.ModalidadReparto.choices.
        Then: ValidationError lanzado por full_clean() (choices inválido).
        """
        data_validada = self.acto_unificado_ok.copy()
        data_validada["modalidad"] = "INVALIDA"

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("modalidad", ctx.exception.message_dict)

        msg = ctx.exception.message_dict["modalidad"][0]
        self.assertTrue(
            ("valid choice" in msg.lower()) or ("not a valid choice" in msg.lower()),
            f"Mensaje inesperado para choices inválido: {msg}"
        )



    def test_admin_crea_acto_con_nombre_vacio_falla(self):
        """
        Test: nombre=""

        Given: nombre es string vacío.
        When: se intenta crear el acto.
        Then: ValidationError en 'nombre' (blank).
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["nombre"] = ""

        with self.assertRaises(DjangoValidationError) as ctx:
            crear_acto_service(self.admin, data_validada)

        self.assertIn("nombre", ctx.exception.message_dict)
        self.assertTrue(len(ctx.exception.message_dict["nombre"]) >= 1)



    def test_admin_crea_acto_con_nombre_solo_espacios_deberia_fallar(self):
        """
        Test: nombre="   " (solo espacios)

        Expected: debería fallar (defensa), pero OJO: con el modelo actual puede colarse.
        """
        data_validada = self.acto_no_papeleta_ok.copy()
        data_validada["nombre"] = "   "

        with self.assertRaises(DjangoValidationError):
            crear_acto_service(self.admin, data_validada)