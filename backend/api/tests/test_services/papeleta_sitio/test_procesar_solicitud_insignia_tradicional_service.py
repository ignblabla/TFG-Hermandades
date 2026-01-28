from django.test import TestCase
from django.utils import timezone
from unittest import mock
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from unittest.mock import patch

from api.models import (
    Acto, Cuota, Hermano, PreferenciaSolicitud, TipoActo, Puesto, TipoPuesto, 
    CuerpoPertenencia, HermanoCuerpo, PapeletaSitio
)

from api.servicios.papeleta_sitio_service import PapeletaSitioService
from api.tests.factories import HermanoFactory

User = get_user_model()


class ProcesarSolicitudInsigniaServiceTest(TestCase):

    def setUp(self):
        self.service = PapeletaSitioService()

        self.ahora = timezone.now()

        # ---------------------------------------------------------------------
        # Cuerpos
        # ---------------------------------------------------------------------
        self.cuerpo_junta = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )
        self.cuerpo_nazarenos = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS
        )
        self.cuerpo_priostia = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.PRIOSTÍA
        )
        self.cuerpo_juventud = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUVENTUD
        )
        self.cuerpo_caridad = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL
        )
        self.cuerpo_no_permitido_costaleros = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )

        # ---------------------------------------------------------------------
        # Hermanos
        # ---------------------------------------------------------------------
        self.hermano_junta = Hermano.objects.create_user(
            dni="55667788C",
            username="55667788C",
            password="password",
            nombre="Antonio",
            primer_apellido="García",
            segundo_apellido="Luna",
            email="antonio@example.com",
            telefono="600999888",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=2001,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1980-04-04",
            esAdmin=False,
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_junta,
            cuerpo=self.cuerpo_junta,
            anio_ingreso=self.ahora.year - 10,
        )

        HermanoCuerpo.objects.create(
            hermano=self.hermano_junta,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 10,
        )

        self.hermano_ok = Hermano.objects.create_user(
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
        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 5,
        )

        self.hermano_no_permitido = Hermano.objects.create_user(
            dni="12345678Z",
            username="12345678Z",
            password="password",
            nombre="Juan",
            primer_apellido="Pérez",
            segundo_apellido="Gómez",
            email="juan@example.com",
            telefono="600123456",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1001,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1990-01-01",
            direccion="Calle Feria",
            codigo_postal="41001",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_no_permitido,
            cuerpo=self.cuerpo_no_permitido_costaleros,
            anio_ingreso=self.ahora.year - 3,
        )

        self.hermano_baja = Hermano.objects.create_user(
            dni="11223344A",
            username="11223344A",
            password="password",
            nombre="Pedro",
            primer_apellido="López",
            segundo_apellido="Martín",
            email="pedro@example.com",
            telefono="600111222",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.BAJA,
            numero_registro=1003,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_baja_corporacion=self.ahora.date(),
            fecha_nacimiento="1992-02-02",
            esAdmin=False,
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_baja,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 2,
        )

        self.hermano_sin_cuerpos = Hermano.objects.create_user(
            dni="99887766B",
            username="99887766B",
            password="password",
            nombre="Mario",
            primer_apellido="Sánchez",
            segundo_apellido="Navas",
            email="mario@example.com",
            telefono="600333444",
            estado_civil=Hermano.EstadoCivil.CASADO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1004,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1991-03-03",
            esAdmin=False,
        )

        # ---------------------------------------------------------------------
        # Cuotas (NUEVO: al corriente hasta el año anterior)
        # ---------------------------------------------------------------------
        anio_actual = self.ahora.date().year
        anio_limite = anio_actual - 1

        Cuota.objects.create(
            hermano=self.hermano_junta,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe=30.00,
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=self.ahora.date(),
        )

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe=30.00,
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=self.ahora.date(),
        )

        Cuota.objects.create(
            hermano=self.hermano_sin_cuerpos,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe=30.00,
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=self.ahora.date(),
        )

        Cuota.objects.create(
            hermano=self.hermano_baja,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe=30.00,
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=self.ahora.date(),
        )

        Cuota.objects.create(
            hermano=self.hermano_no_permitido,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe=30.00,
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=self.ahora.date(),
        )

        # ---------------------------------------------------------------------
        # Tipos de acto / Actos
        # ---------------------------------------------------------------------
        self.tipo_acto_con_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True,
        )
        self.tipo_acto_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False,
        )

        self.acto_tradicional_en_plazo = Acto.objects.create(
            nombre="Estación de Penitencia",
            descripcion="Acto principal",
            fecha=self.ahora + timedelta(days=30),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto_con_papeleta,
            inicio_solicitud=self.ahora - timedelta(hours=1),
            fin_solicitud=self.ahora + timedelta(hours=1),
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None,
        )

        self.acto_tradicional_limite_inicio = Acto.objects.create(
            nombre="Vía Crucis (inicio exacto)",
            descripcion="Límite inicio",
            fecha=self.ahora + timedelta(days=20),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto_con_papeleta,
            inicio_solicitud=self.ahora,
            fin_solicitud=self.ahora + timedelta(hours=1),
        )

        self.acto_tradicional_limite_fin = Acto.objects.create(
            nombre="Quinario (fin exacto)",
            descripcion="Límite fin",
            fecha=self.ahora + timedelta(days=15),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto_con_papeleta,
            inicio_solicitud=self.ahora - timedelta(hours=1),
            fin_solicitud=self.ahora,
        )

        self.acto_unificado = Acto.objects.create(
            nombre="Cabildo (Unificado)",
            descripcion="Acto unificado",
            fecha=self.ahora + timedelta(days=10),
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            tipo_acto=self.tipo_acto_con_papeleta,
            inicio_solicitud=self.ahora - timedelta(hours=1),
            fin_solicitud=self.ahora + timedelta(hours=1),
        )

        self.acto_tradicional_fuera_plazo = Acto.objects.create(
            nombre="Rosario (fuera plazo)",
            descripcion="Fuera de plazo",
            fecha=self.ahora + timedelta(days=12),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto_con_papeleta,
            inicio_solicitud=self.ahora - timedelta(days=2),
            fin_solicitud=self.ahora - timedelta(days=1),
        )

        self.acto_sin_papeleta = Acto.objects.create(
            nombre="Convivencia",
            descripcion="No admite papeleta",
            fecha=self.ahora + timedelta(days=5),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto_sin_papeleta,
            inicio_solicitud=self.ahora - timedelta(hours=1),
            fin_solicitud=self.ahora + timedelta(hours=1),
        )

        self.acto_tradicional_sin_plazo_config = Acto.objects.create(
            nombre="Triduo",
            descripcion="Sin plazo configurado",
            fecha=self.ahora + timedelta(days=8),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto_con_papeleta,
            inicio_solicitud=None,
            fin_solicitud=None,
        )

        # ---------------------------------------------------------------------
        # Tipos de puesto / Puestos
        # ---------------------------------------------------------------------
        self.tipo_puesto_insignia_solo_junta = TipoPuesto.objects.create(
            nombre_tipo="Insignia Junta",
            solo_junta_gobierno=True,
            es_insignia=True,
        )
        self.tipo_puesto_insignia = TipoPuesto.objects.create(
            nombre_tipo="Insignia",
            solo_junta_gobierno=False,
            es_insignia=True,
        )
        self.tipo_puesto_cirio = TipoPuesto.objects.create(
            nombre_tipo="Cirio",
            solo_junta_gobierno=False,
            es_insignia=False,
        )

        self.puesto_insignia_disponible_1 = Puesto.objects.create(
            nombre="Senatus",
            numero_maximo_asignaciones=1,
            disponible=True,
            lugar_citacion="Casa Hermandad",
            hora_citacion=self.ahora.time(),
            cortejo_cristo=True,
            acto=self.acto_tradicional_en_plazo,
            tipo_puesto=self.tipo_puesto_insignia,
        )

        self.puesto_insignia_disponible_2 = Puesto.objects.create(
            nombre="Bacalao",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional_en_plazo,
            tipo_puesto=self.tipo_puesto_insignia,
        )

        self.puesto_insignia_no_disponible = Puesto.objects.create(
            nombre="Bandera",
            numero_maximo_asignaciones=1,
            disponible=False,
            acto=self.acto_tradicional_en_plazo,
            tipo_puesto=self.tipo_puesto_insignia,
        )

        self.puesto_no_insignia = Puesto.objects.create(
            nombre="Cirio Grande Cristo",
            numero_maximo_asignaciones=100,
            disponible=True,
            acto=self.acto_tradicional_en_plazo,
            tipo_puesto=self.tipo_puesto_cirio,
        )

        self.puesto_insignia_otro_acto = Puesto.objects.create(
            nombre="Senatus (otro acto)",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional_fuera_plazo,
            tipo_puesto=self.tipo_puesto_insignia,
        )

        self.puesto_insignia_solo_junta = Puesto.objects.create(
            nombre="Varas Presidencia",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional_en_plazo,
            tipo_puesto=self.tipo_puesto_insignia_solo_junta,
        )

        # ---------------------------------------------------------------------
        # Preferencias
        # ---------------------------------------------------------------------
        self.preferencias_ok = [
            {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_insignia_disponible_2, "orden_prioridad": 2},
        ]

        self.preferencias_con_no_insignia = [
            {"puesto_solicitado": self.puesto_no_insignia, "orden_prioridad": 1},
        ]

        self.preferencias_con_no_disponible = [
            {"puesto_solicitado": self.puesto_insignia_no_disponible, "orden_prioridad": 1},
        ]

        self.preferencias_puesto_otro_acto = [
            {"puesto_solicitado": self.puesto_insignia_otro_acto, "orden_prioridad": 1},
        ]

        self.preferencias_prioridad_duplicada = [
            {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_insignia_disponible_2, "orden_prioridad": 1},
        ]

        self.preferencias_puesto_duplicado = [
            {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 2},
        ]

        self.preferencias_solo_junta = [
            {"puesto_solicitado": self.puesto_insignia_solo_junta, "orden_prioridad": 1},
        ]



    # def test_procesar_solicitud_insignia_tradicional_ok_con_una_preferencia(self):
    #     """
    #     Test: Crea papeleta + 1 preferencia válida
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo, hermano ALTA, cuerpo permitido,
    #         no existe papeleta previa, puesto insignia disponible
    #     When: preferencias con 1 item
    #     Then: se crea PapeletaSitio SOLICITADA, es_solicitud_insignia=True, 1 PreferenciaSolicitud
    #     """
    #     ahora_congelado = self.ahora

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         preferencias_data = [
    #             {
    #                 "puesto_solicitado": self.puesto_insignia_disponible_1,
    #                 "orden_prioridad": 1,
    #             }
    #         ]

    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)
    #     self.assertEqual(papeleta.anio, self.acto_tradicional_en_plazo.fecha.year)
    #     self.assertIsNone(papeleta.numero_papeleta)
    #     self.assertEqual(papeleta.fecha_solicitud, ahora_congelado)

    #     self.assertIsNotNone(papeleta.codigo_verificacion)
    #     self.assertEqual(len(papeleta.codigo_verificacion), 8)
    #     self.assertEqual(papeleta.codigo_verificacion, papeleta.codigo_verificacion.upper())
    #     self.assertRegex(papeleta.codigo_verificacion, r"^[0-9A-F]{8}$")

    #     prefs = PreferenciaSolicitud.objects.filter(papeleta=papeleta).order_by("orden_prioridad")
    #     self.assertEqual(prefs.count(), 1)
    #     self.assertEqual(prefs[0].puesto_solicitado, self.puesto_insignia_disponible_1)
    #     self.assertEqual(prefs[0].orden_prioridad, 1)



    # def test_procesar_solicitud_insignia_tradicional_ok_con_multiples_preferencias_validas(self):
    #     """
    #     Test: Crea papeleta + N preferencias válidas (2..N)
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo, hermano ALTA, cuerpo permitido,
    #         no existe papeleta previa, puestos insignia disponibles
    #     When: preferencias con 2..N items (prioridades distintas)
    #     Then: se crea PapeletaSitio y se crean N PreferenciaSolicitud asociadas,
    #         guardando orden_prioridad exactamente como viene (verificando orden y valores)
    #     """
    #     ahora_congelado = self.ahora

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 2},
    #         {"puesto_solicitado": self.puesto_insignia_disponible_2, "orden_prioridad": 1},
    #     ]
    #     esperado_por_prioridad = {
    #         2: self.puesto_insignia_disponible_1.id,
    #         1: self.puesto_insignia_disponible_2.id,
    #     }

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     prefs_qs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
    #     self.assertEqual(prefs_qs.count(), len(preferencias_data))

    #     prioridades_guardadas = list(prefs_qs.values_list("orden_prioridad", flat=True))
    #     self.assertCountEqual(prioridades_guardadas, [p["orden_prioridad"] for p in preferencias_data])

    #     prefs_ordenadas = list(prefs_qs.order_by("orden_prioridad").values_list("orden_prioridad", "puesto_solicitado_id"))
    #     for orden_prioridad, puesto_id in prefs_ordenadas:
    #         self.assertIn(orden_prioridad, esperado_por_prioridad)
    #         self.assertEqual(puesto_id, esperado_por_prioridad[orden_prioridad])



    # def test_procesar_solicitud_insignia_tradicional_limite_inferior_plazo_permitido(self):
    #     """
    #     Test: Límite inferior del plazo (ahora == inicio_solicitud)
    #     Given: acto TRADICIONAL, requiere_papeleta=True, ahora == inicio_solicitud,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         puesto insignia disponible DEL MISMO acto
    #     When: se solicita con 1 preferencia válida
    #     Then: está permitido (NO lanza 'Fuera del plazo de solicitud de insignias')
    #         y se crea la PapeletaSitio correctamente
    #     """
    #     acto = self.acto_tradicional_limite_inicio
    #     ahora_congelado = acto.inicio_solicitud

    #     puesto_insignia_mismo_acto = Puesto.objects.create(
    #         nombre="Insignia límite inicio",
    #         numero_maximo_asignaciones=1,
    #         disponible=True,
    #         acto=acto,
    #         tipo_puesto=self.tipo_puesto_insignia,
    #     )

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": puesto_insignia_mismo_acto,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=acto,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)
    #     self.assertEqual(papeleta.fecha_solicitud, ahora_congelado)

    #     prefs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
    #     self.assertEqual(prefs.count(), 1)
    #     self.assertEqual(prefs.first().orden_prioridad, 1)
    #     self.assertEqual(prefs.first().puesto_solicitado, puesto_insignia_mismo_acto)



    # def test_procesar_solicitud_insignia_tradicional_limite_superior_plazo_permitido(self):
    #     """
    #     Test: Límite superior del plazo (ahora == fin_solicitud)
    #     Given: acto TRADICIONAL, requiere_papeleta=True, ahora == fin_solicitud,
    #         hermano ALTA, al corriente hasta año anterior, cuerpo permitido,
    #         no existe papeleta previa, puesto insignia disponible DEL MISMO acto
    #     When: se solicita con 1 preferencia válida
    #     Then: está permitido (NO lanza 'Fuera del plazo de solicitud de insignias')
    #         y se crea la PapeletaSitio correctamente
    #     """
    #     acto = self.acto_tradicional_limite_fin
    #     ahora_congelado = acto.fin_solicitud

    #     puesto_insignia_mismo_acto = Puesto.objects.create(
    #         nombre="Insignia límite fin",
    #         numero_maximo_asignaciones=1,
    #         disponible=True,
    #         acto=acto,
    #         tipo_puesto=self.tipo_puesto_insignia,
    #     )

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": puesto_insignia_mismo_acto,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=acto,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)
    #     self.assertEqual(papeleta.fecha_solicitud, ahora_congelado)
    #     self.assertEqual(papeleta.anio, acto.fecha.year)

    #     prefs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
    #     self.assertEqual(prefs.count(), 1)
    #     self.assertEqual(prefs.first().orden_prioridad, 1)
    #     self.assertEqual(prefs.first().puesto_solicitado, puesto_insignia_mismo_acto)



    # def test_procesar_solicitud_insignia_tradicional_hermano_con_unico_cuerpo_permitido_nazarenos(self):
    #     """
    #     Test: Hermano con un único cuerpo permitido (NAZARENOS)
    #     Given: hermano en estado ALTA, al corriente de cuotas, pertenece únicamente al cuerpo NAZARENOS,
    #         acto TRADICIONAL que requiere papeleta, en plazo, sin papeleta previa,
    #         puesto insignia disponible
    #     When: solicita con 1 preferencia válida
    #     Then: está permitido y se crea correctamente la PapeletaSitio y su PreferenciaSolicitud
    #     """
    #     ahora_congelado = self.ahora

    #     cuerpos_hermano = list(
    #         self.hermano_ok.cuerpos.values_list("nombre_cuerpo", flat=True)
    #     )
    #     self.assertEqual(cuerpos_hermano, [CuerpoPertenencia.NombreCuerpo.NAZARENOS])

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_1,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)
    #     self.assertEqual(papeleta.anio, self.acto_tradicional_en_plazo.fecha.year)
    #     self.assertEqual(papeleta.fecha_solicitud, ahora_congelado)

    #     prefs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
    #     self.assertEqual(prefs.count(), 1)
    #     self.assertEqual(prefs.first().orden_prioridad, 1)
    #     self.assertEqual(prefs.first().puesto_solicitado, self.puesto_insignia_disponible_1)



    # def test_procesar_solicitud_insignia_tradicional_hermano_unico_cuerpo_priostia(self):
    #     """
    #     Test P6: Hermano con un único cuerpo permitido (PRIOSTÍA)
    #     Given: hermano ALTA, al corriente, pertenece solo a PRIOSTÍA,
    #         acto TRADICIONAL en plazo, sin papeleta previa, puesto insignia disponible
    #     When: solicita con 1 preferencia válida
    #     Then: permitido y se crea correctamente la PapeletaSitio
    #     """
    #     ahora_congelado = self.ahora

    #     HermanoCuerpo.objects.filter(hermano=self.hermano_ok).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano_ok,
    #         cuerpo=self.cuerpo_priostia,
    #         anio_ingreso=ahora_congelado.year - 5,
    #     )

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)



    # def test_procesar_solicitud_insignia_tradicional_hermano_unico_cuerpo_juventud(self):
    #     """
    #     Test P7: Hermano con un único cuerpo permitido (JUVENTUD)
    #     Given: hermano ALTA, al corriente, pertenece solo a JUVENTUD,
    #         acto TRADICIONAL en plazo, sin papeleta previa, puesto insignia disponible
    #     When: solicita con 1 preferencia válida
    #     Then: permitido y se crea correctamente la PapeletaSitio
    #     """
    #     ahora_congelado = self.ahora

    #     HermanoCuerpo.objects.filter(hermano=self.hermano_ok).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano_ok,
    #         cuerpo=self.cuerpo_juventud,
    #         anio_ingreso=ahora_congelado.year - 5,
    #     )

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)



    # def test_procesar_solicitud_insignia_tradicional_hermano_unico_cuerpo_caridad_accion_social(self):
    #     """
    #     Test P8: Hermano con un único cuerpo permitido (CARIDAD_ACCION_SOCIAL)
    #     Given: hermano ALTA, al corriente, pertenece solo a CARIDAD_ACCION_SOCIAL,
    #         acto TRADICIONAL en plazo, sin papeleta previa, puesto insignia disponible
    #     When: solicita con 1 preferencia válida
    #     Then: permitido y se crea correctamente la PapeletaSitio
    #     """
    #     ahora_congelado = self.ahora

    #     HermanoCuerpo.objects.filter(hermano=self.hermano_ok).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano_ok,
    #         cuerpo=self.cuerpo_caridad,
    #         anio_ingreso=ahora_congelado.year - 5,
    #     )

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)



    # def test_procesar_solicitud_insignia_tradicional_hermano_sin_cuerpos_permitido(self):
    #     """
    #     Test: Hermano sin cuerpos asociados
    #     Given: hermano ALTA, al corriente, sin pertenencias en HermanoCuerpo (mis_cuerpos_ids vacío),
    #         acto TRADICIONAL que requiere papeleta, en plazo, sin papeleta previa,
    #         puesto insignia disponible
    #     When: solicita con 1 preferencia válida
    #     Then: está permitido (porque _validar_pertenencia_cuerpos hace return)
    #         y se crea correctamente la PapeletaSitio
    #     """
    #     ahora_congelado = self.ahora

    #     HermanoCuerpo.objects.filter(hermano=self.hermano_ok).delete()
    #     self.assertFalse(
    #         HermanoCuerpo.objects.filter(hermano=self.hermano_ok).exists()
    #     )

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_1,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)
    #     self.assertEqual(papeleta.anio, self.acto_tradicional_en_plazo.fecha.year)
    #     self.assertEqual(papeleta.fecha_solicitud, ahora_congelado)

    #     prefs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
    #     self.assertEqual(prefs.count(), 1)
    #     self.assertEqual(prefs.first().orden_prioridad, 1)
    #     self.assertEqual(prefs.first().puesto_solicitado, self.puesto_insignia_disponible_1)



    # def test_procesar_solicitud_insignia_tradicional_cuotas_al_corriente_hasta_anio_anterior_permitido(self):
    #     """
    #     Test: Cuotas al corriente hasta el año anterior
    #     Given: hermano ALTA, existe cuota del (año_actual - 1) con estado PAGADA,
    #         acto TRADICIONAL que requiere papeleta, en plazo, cuerpo permitido,
    #         sin papeleta previa, puesto insignia disponible
    #     When: solicita con 1 preferencia válida
    #     Then: está permitido (NO lanza error por cuotas)
    #         y se crea correctamente la PapeletaSitio
    #     """
    #     ahora_congelado = self.ahora
    #     anio_actual = ahora_congelado.date().year
    #     anio_limite = anio_actual - 1

    #     self.assertTrue(
    #         Cuota.objects.filter(
    #             hermano=self.hermano_ok,
    #             anio=anio_limite,
    #             estado=Cuota.EstadoCuota.PAGADA,
    #         ).exists()
    #     )

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_1,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)
    #     self.assertEqual(papeleta.anio, self.acto_tradicional_en_plazo.fecha.year)
    #     self.assertEqual(papeleta.fecha_solicitud, ahora_congelado)

    #     prefs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
    #     self.assertEqual(prefs.count(), 1)
    #     self.assertEqual(prefs.first().orden_prioridad, 1)
    #     self.assertEqual(prefs.first().puesto_solicitado, self.puesto_insignia_disponible_1)



    # def test_procesar_solicitud_insignia_tradicional_cuota_pendiente_solo_anio_actual_no_bloquea(self):
    #     """
    #     Test: Cuotas con deuda SOLO del año actual (no debe bloquear)
    #     Given: hermano ALTA, años <= (año_actual-1) PAGADAS, pero existe cuota del año_actual en PENDIENTE,
    #         acto TRADICIONAL que requiere papeleta, en plazo, cuerpo permitido,
    #         sin papeleta previa, puesto insignia disponible
    #     When: solicita con 1 preferencia válida
    #     Then: permitido (porque la validación solo mira anio__lte anio_limite) y se crea la PapeletaSitio
    #     """
    #     ahora_congelado = self.ahora
    #     anio_actual = ahora_congelado.date().year
    #     anio_limite = anio_actual - 1

    #     self.assertFalse(
    #         self.hermano_ok.cuotas.filter(anio__lte=anio_limite).exclude(
    #             estado=Cuota.EstadoCuota.PAGADA
    #         ).exists()
    #     )

    #     Cuota.objects.create(
    #         hermano=self.hermano_ok,
    #         anio=anio_actual,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_actual}",
    #         importe=30.00,
    #         estado=Cuota.EstadoCuota.PENDIENTE,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #         fecha_pago=None,
    #     )
    #     self.assertTrue(
    #         self.hermano_ok.cuotas.filter(anio=anio_actual, estado=Cuota.EstadoCuota.PENDIENTE).exists()
    #     )

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta.es_solicitud_insignia)
    #     self.assertEqual(papeleta.fecha_solicitud, ahora_congelado)

    #     prefs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
    #     self.assertEqual(prefs.count(), 1)
    #     self.assertEqual(prefs.first().orden_prioridad, 1)
    #     self.assertEqual(prefs.first().puesto_solicitado, self.puesto_insignia_disponible_1)



    # def test_procesar_solicitud_insignia_tradicional_papeleta_previa_anulada_no_bloquea(self):
    #     """
    #     Test: Papeleta previa ANULADA no bloquea
    #     Given: existe PapeletaSitio(hermano, acto, estado=ANULADA)
    #     When: se realiza una nueva solicitud con 1 preferencia válida
    #     Then: no lanza error, crea una nueva SOLICITADA y en BD quedan 2 papeletas:
    #         - una ANULADA
    #         - una SOLICITADA (es_solicitud_insignia=True)
    #     """
    #     ahora_congelado = self.ahora

    #     papeleta_anulada = PapeletaSitio.objects.create(
    #         hermano=self.hermano_ok,
    #         acto=self.acto_tradicional_en_plazo,
    #         anio=self.acto_tradicional_en_plazo.fecha.year,
    #         fecha_solicitud=ahora_congelado - timedelta(days=1),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
    #         es_solicitud_insignia=True,
    #         numero_papeleta=None,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     self.assertIsNotNone(papeleta_anulada.id)

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         papeleta_nueva = self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertIsNotNone(papeleta_nueva.id)
    #     self.assertNotEqual(papeleta_nueva.id, papeleta_anulada.id)
    #     self.assertEqual(papeleta_nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertTrue(papeleta_nueva.es_solicitud_insignia)

    #     qs = PapeletaSitio.objects.filter(
    #         hermano=self.hermano_ok,
    #         acto=self.acto_tradicional_en_plazo,
    #     )
    #     self.assertEqual(qs.count(), 2)
    #     self.assertEqual(qs.filter(estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA).count(), 1)
    #     self.assertEqual(qs.filter(estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA).count(), 1)



    # def test_procesar_solicitud_insignia_tradicional_acto_no_admite_solicitudes(self):
    #     """
    #     Test: Acto no admite solicitudes (requiere_papeleta=False)
    #     Given: acto.tipo_acto.requiere_papeleta=False
    #     When: se intenta solicitar insignia en modalidad tradicional
    #     Then: lanza ValidationError("El acto 'X' no admite solicitudes.")
    #     """
    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with self.assertRaises(ValidationError) as ctx:
    #         self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_sin_papeleta,
    #             preferencias_data=preferencias_data,
    #         )

    #     mensaje_esperado = f"El acto '{self.acto_sin_papeleta.nombre}' no admite solicitudes."
    #     self.assertEqual(ctx.exception.messages, [mensaje_esperado])



    # def test_procesar_solicitud_insignia_tradicional_modalidad_incorrecta_unificado(self):
    #     """
    #     Test N2: Modalidad incorrecta (UNIFICADO)
    #     Given: acto.modalidad = UNIFICADO
    #     When: se intenta solicitar insignia por el endpoint TRADICIONAL
    #     Then: lanza ValidationError("Este endpoint es solo para actos de modalidad TRADICIONAL.")
    #     """
    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with self.assertRaises(ValidationError) as ctx:
    #         self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_unificado,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Este endpoint es solo para actos de modalidad TRADICIONAL."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_hermano_no_en_alta_baja(self):
    #     """
    #     Test: Hermano NO está en ALTA (BAJA)
    #     Given: hermano.estado_hermano = BAJA
    #     When: intenta solicitar papeleta de insignia en acto TRADICIONAL
    #     Then: lanza ValidationError("Solo los hermanos en estado ALTA pueden solicitar papeleta.")
    #     """
    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     self.assertEqual(self.hermano_baja.estado_hermano, Hermano.EstadoHermano.BAJA)

    #     with self.assertRaises(ValidationError) as ctx:
    #         self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_baja,
    #             acto=self.acto_tradicional_en_plazo,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Solo los hermanos en estado ALTA pueden solicitar papeleta."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_con_deuda_hasta_anio_anterior_pendiente(self):
    #     """
    #     Test: Cuotas con deuda en año <= año anterior (PENDIENTE)
    #     Given: existe Cuota(anio=anio_actual-1, estado=PENDIENTE)
    #     Then: ValidationError("No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}.")
    #     """
    #     ahora_congelado = self.ahora
    #     anio_actual = ahora_congelado.date().year
    #     anio_limite = anio_actual - 1

    #     Cuota.objects.filter(hermano=self.hermano_ok, anio=anio_limite).delete()
    #     Cuota.objects.create(
    #         hermano=self.hermano_ok,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe=30.00,
    #         estado=Cuota.EstadoCuota.PENDIENTE,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #         fecha_pago=None,
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         [f"No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}."]
    #     )


    # def test_procesar_solicitud_insignia_tradicional_con_deuda_hasta_anio_anterior_devuelta(self):
    #     """
    #     Test: Cuotas con deuda en año <= año anterior (DEVUELTA)
    #     Given: existe Cuota(anio=anio_actual-1, estado=DEVUELTA)
    #     Then: ValidationError("No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}.")
    #     """
    #     ahora_congelado = self.ahora
    #     anio_actual = ahora_congelado.date().year
    #     anio_limite = anio_actual - 1

    #     Cuota.objects.filter(hermano=self.hermano_ok, anio=anio_limite).delete()
    #     Cuota.objects.create(
    #         hermano=self.hermano_ok,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe=30.00,
    #         estado=Cuota.EstadoCuota.DEVUELTA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #         fecha_pago=None,
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         [f"No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}."]
    #     )


    # def test_procesar_solicitud_insignia_tradicional_con_deuda_hasta_anio_anterior_en_remesa(self):
    #     """
    #     Test: Cuotas con deuda en año <= año anterior (EN_REMESA)
    #     Given: existe Cuota(anio=anio_actual-1, estado=EN_REMESA)
    #     Then: ValidationError("No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}.")
    #     """
    #     ahora_congelado = self.ahora
    #     anio_actual = ahora_congelado.date().year
    #     anio_limite = anio_actual - 1

    #     Cuota.objects.filter(hermano=self.hermano_ok, anio=anio_limite).delete()
    #     Cuota.objects.create(
    #         hermano=self.hermano_ok,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe=30.00,
    #         estado=Cuota.EstadoCuota.EN_REMESA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #         fecha_pago=None,
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         [f"No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}."]
    #     )


    # def test_procesar_solicitud_insignia_tradicional_con_deuda_hasta_anio_anterior_exento(self):
    #     """
    #     Test: Cuotas con deuda en año <= año anterior (EXENTO)
    #     Given: existe Cuota(anio=anio_actual-1, estado=EXENTO)
    #     Then: ValidationError("No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}.")
    #     """
    #     ahora_congelado = self.ahora
    #     anio_actual = ahora_congelado.date().year
    #     anio_limite = anio_actual - 1

    #     Cuota.objects.filter(hermano=self.hermano_ok, anio=anio_limite).delete()
    #     Cuota.objects.create(
    #         hermano=self.hermano_ok,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe=30.00,
    #         estado=Cuota.EstadoCuota.EXENTO,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #         fecha_pago=None,
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         [f"No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_hermano_con_cuerpo_no_permitido_costaleros(self):
    #     """
    #     Test: Hermano con cuerpo NO permitido (COSTALEROS)
    #     Given: hermano ALTA, al corriente, con pertenencia a COSTALEROS,
    #         acto TRADICIONAL que requiere papeleta, en plazo,
    #         sin papeleta previa, puesto insignia disponible
    #     When: intenta solicitar insignia
    #     Then: ValidationError("Tu cuerpo de pertenencia actual no permite solicitar papeleta.")
    #     """
    #     ahora_congelado = self.ahora

    #     HermanoCuerpo.objects.filter(hermano=self.hermano_no_permitido).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano_no_permitido,
    #         cuerpo=self.cuerpo_no_permitido_costaleros,
    #         anio_ingreso=ahora_congelado.year - 3,
    #     )

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_no_permitido,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Tu cuerpo de pertenencia actual no permite solicitar papeleta."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_hermano_con_mezcla_cuerpo_permitido_y_no_permitido(self):
    #     """
    #     Test: Hermano con mezcla de cuerpos (permitido + no permitido)
    #     Given: hermano ALTA, al corriente, pertenece a NAZARENOS (permitido)
    #         y COSTALEROS (no permitido),
    #         acto TRADICIONAL que requiere papeleta, en plazo,
    #         sin papeleta previa, puesto insignia disponible
    #     When: intenta solicitar insignia
    #     Then: ValidationError("Tu cuerpo de pertenencia actual no permite solicitar papeleta.")
    #     """
    #     ahora_congelado = self.ahora

    #     HermanoCuerpo.objects.filter(hermano=self.hermano_ok).delete()
    #     HermanoCuerpo.objects.bulk_create([
    #         HermanoCuerpo(
    #             hermano=self.hermano_ok,
    #             cuerpo=self.cuerpo_nazarenos,
    #             anio_ingreso=ahora_congelado.year - 5,
    #         ),
    #         HermanoCuerpo(
    #             hermano=self.hermano_ok,
    #             cuerpo=self.cuerpo_no_permitido_costaleros,
    #             anio_ingreso=ahora_congelado.year - 3,
    #         ),
    #     ])

    #     cuerpos = set(
    #         self.hermano_ok.cuerpos.values_list("nombre_cuerpo", flat=True)
    #     )
    #     self.assertEqual(
    #         cuerpos,
    #         {
    #             CuerpoPertenencia.NombreCuerpo.NAZARENOS,
    #             CuerpoPertenencia.NombreCuerpo.COSTALEROS,
    #         }
    #     )

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Tu cuerpo de pertenencia actual no permite solicitar papeleta."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_unicidad_bloquea_si_existe_solicitada(self):
    #     """
    #     Test: Unicidad bloquea si ya existe papeleta previa NO anulada (SOLICITADA)
    #     Given: existe PapeletaSitio previa con estado SOLICITADA
    #     Then: ValidationError("Ya existe una solicitud activa para este acto.")
    #     """
    #     ahora_congelado = self.ahora

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano_ok,
    #         acto=self.acto_tradicional_en_plazo,
    #         anio=self.acto_tradicional_en_plazo.fecha.year,
    #         fecha_solicitud=ahora_congelado - timedelta(minutes=5),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         es_solicitud_insignia=True,
    #         numero_papeleta=None,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(ctx.exception.messages, ["Ya existe una solicitud activa para este acto."])


    # def test_procesar_solicitud_insignia_tradicional_unicidad_bloquea_si_existe_emitida(self):
    #     """
    #     Test: Unicidad bloquea si ya existe papeleta previa NO anulada (EMITIDA)
    #     Given: existe PapeletaSitio previa con estado EMITIDA
    #     Then: ValidationError("Ya existe una solicitud activa para este acto.")
    #     """
    #     ahora_congelado = self.ahora

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano_ok,
    #         acto=self.acto_tradicional_en_plazo,
    #         anio=self.acto_tradicional_en_plazo.fecha.year,
    #         fecha_solicitud=ahora_congelado - timedelta(days=1),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA,
    #         es_solicitud_insignia=True,
    #         numero_papeleta=10,
    #         fecha_emision=ahora_congelado.date(),
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(ctx.exception.messages, ["Ya existe una solicitud activa para este acto."])


    # def test_procesar_solicitud_insignia_tradicional_unicidad_bloquea_si_existe_recogida(self):
    #     """
    #     Test: Unicidad bloquea si ya existe papeleta previa NO anulada (RECOGIDA)
    #     Given: existe PapeletaSitio previa con estado RECOGIDA
    #     Then: ValidationError("Ya existe una solicitud activa para este acto.")
    #     """
    #     ahora_congelado = self.ahora

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano_ok,
    #         acto=self.acto_tradicional_en_plazo,
    #         anio=self.acto_tradicional_en_plazo.fecha.year,
    #         fecha_solicitud=ahora_congelado - timedelta(days=1),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.RECOGIDA,
    #         es_solicitud_insignia=True,
    #         numero_papeleta=11,
    #         fecha_emision=ahora_congelado.date(),
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(ctx.exception.messages, ["Ya existe una solicitud activa para este acto."])


    # def test_procesar_solicitud_insignia_tradicional_unicidad_bloquea_si_existe_leida(self):
    #     """
    #     Test: Unicidad bloquea si ya existe papeleta previa NO anulada (LEIDA)
    #     Given: existe PapeletaSitio previa con estado LEIDA
    #     Then: ValidationError("Ya existe una solicitud activa para este acto.")
    #     """
    #     ahora_congelado = self.ahora

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano_ok,
    #         acto=self.acto_tradicional_en_plazo,
    #         anio=self.acto_tradicional_en_plazo.fecha.year,
    #         fecha_solicitud=ahora_congelado - timedelta(days=1),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.LEIDA,
    #         es_solicitud_insignia=True,
    #         numero_papeleta=12,
    #         fecha_emision=ahora_congelado.date(),
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(ctx.exception.messages, ["Ya existe una solicitud activa para este acto."])


    # def test_procesar_solicitud_insignia_tradicional_unicidad_bloquea_si_existe_no_asignada(self):
    #     """
    #     Test: Unicidad bloquea si ya existe papeleta previa NO anulada (NO_ASIGNADA)
    #     Given: existe PapeletaSitio previa con estado NO_ASIGNADA
    #     Then: ValidationError("Ya existe una solicitud activa para este acto.")
    #     """
    #     ahora_congelado = self.ahora

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano_ok,
    #         acto=self.acto_tradicional_en_plazo,
    #         anio=self.acto_tradicional_en_plazo.fecha.year,
    #         fecha_solicitud=ahora_congelado - timedelta(days=1),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
    #         es_solicitud_insignia=True,
    #         numero_papeleta=None,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(ctx.exception.messages, ["Ya existe una solicitud activa para este acto."])

    # def test_procesar_solicitud_insignia_tradicional_plazo_no_configurado_inicio_none(self):
    #     """
    #     Test: Plazo no configurado (inicio_solicitud is None)
    #     Given: acto TRADICIONAL, requiere_papeleta=True, inicio_solicitud=None (o fin_solicitud=None),
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         puesto insignia disponible
    #     When: intenta solicitar insignia
    #     Then: ValidationError("Plazo de insignias no configurado.")
    #     """
    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with self.assertRaises(ValidationError) as ctx:
    #         self.service.procesar_solicitud_insignia_tradicional(
    #             hermano=self.hermano_ok,
    #             acto=self.acto_tradicional_sin_plazo_config,
    #             preferencias_data=preferencias_data,
    #         )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Plazo de insignias no configurado."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_plazo_no_configurado_fin_none(self):
    #     """
    #     Test: Plazo no configurado (fin_solicitud is None)
    #     Given: acto TRADICIONAL, requiere_papeleta=True, fin_solicitud=None,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         puesto insignia disponible
    #     When: intenta solicitar insignia
    #     Then: ValidationError("Plazo de insignias no configurado.")
    #     """
    #     ahora_congelado = self.ahora

    #     acto = self.acto_tradicional_sin_plazo_config
    #     self.assertIsNone(acto.fin_solicitud)

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=acto,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Plazo de insignias no configurado."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_fuera_plazo_antes_inicio(self):
    #     """
    #     Test: Fuera de plazo (antes)
    #     Given: acto TRADICIONAL, requiere_papeleta=True,
    #         ahora < inicio_solicitud (caso crítico: ahora = inicio_solicitud - 1 microsegundo),
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         puesto insignia disponible
    #     When: intenta solicitar insignia
    #     Then: ValidationError("Fuera del plazo de solicitud de insignias.")
    #     """
    #     inicio = self.acto_tradicional_en_plazo.inicio_solicitud
    #     ahora_congelado = inicio - timedelta(microseconds=1)

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Fuera del plazo de solicitud de insignias."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_fuera_plazo_despues_fin(self):
    #     """
    #     Test: Fuera de plazo (después)
    #     Given: acto TRADICIONAL, requiere_papeleta=True,
    #         ahora > fin_solicitud (caso crítico: ahora = fin_solicitud + 1 microsegundo),
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         puesto insignia disponible
    #     When: intenta solicitar insignia
    #     Then: ValidationError("Fuera del plazo de solicitud de insignias.")
    #     """
    #     fin = self.acto_tradicional_en_plazo.fin_solicitud
    #     ahora_congelado = fin + timedelta(microseconds=1)

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Fuera del plazo de solicitud de insignias."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_preferencia_con_puesto_no_insignia(self):
    #     """
    #     Test: Preferencias incluye puesto NO insignia
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         preferencia con puesto cuyo tipo_puesto.es_insignia=False
    #     When: intenta solicitar insignia
    #     Then: ValidationError("El puesto 'X' no es una insignia. En plazo tradicional, los cirios se piden aparte.")
    #     """
    #     ahora_congelado = self.ahora

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_no_insignia,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         [
    #             f"El puesto '{self.puesto_no_insignia.nombre}' no es una insignia. "
    #             "En plazo tradicional, los cirios se piden aparte."
    #         ],
    #     )



    # def test_procesar_solicitud_insignia_tradicional_preferencia_con_puesto_no_disponible(self):
    #     """
    #     Test: Preferencias incluye puesto NO disponible
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         preferencia con puesto disponible=False
    #     When: intenta solicitar insignia
    #     Then: ValidationError("El puesto 'X' no está disponible para su solicitud en este acto.")
    #     """
    #     ahora_congelado = self.ahora

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_no_disponible,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         [
    #             f"El puesto '{self.puesto_insignia_no_disponible.nombre}' "
    #             "no está disponible para su solicitud en este acto."
    #         ],
    #     )



    # def test_procesar_solicitud_insignia_tradicional_preferencias_vacias(self):
    #     """
    #     Test: Preferencias vacías
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         preferencias_data=[]
    #     When: intenta solicitar insignia sin preferencias
    #     Then: ValidationError("Debe indicar al menos una preferencia.")
    #     """
    #     ahora_congelado = self.ahora
    #     preferencias_data = []

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["Debe indicar al menos una preferencia."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_preferencia_sin_puesto_solicitado(self):
    #     """
    #     Test: Preferencias con estructura inválida (falta puesto_solicitado)
    #     Given: preferencias_data=[{"orden_prioridad": 1}]
    #     When: se intenta procesar la solicitud
    #     Then: se lanza KeyError (NO ValidationError)
    #     """
    #     ahora_congelado = self.ahora
    #     preferencias_data = [
    #         {"orden_prioridad": 1}
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(KeyError):
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )



    # def test_procesar_solicitud_insignia_tradicional_preferencia_sin_orden_prioridad(self):
    #     """
    #     Test: Preferencias con estructura inválida (falta orden_prioridad)
    #     Given: preferencias_data=[{"puesto_solicitado": puesto}]
    #     When: se intenta procesar la solicitud
    #     Then: se lanza KeyError (NO ValidationError)
    #     """
    #     ahora_congelado = self.ahora
    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_1
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(KeyError):
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )



    # def test_procesar_solicitud_insignia_tradicional_orden_prioridad_cero_bloquea(self):
    #     """
    #     Test: orden_prioridad inválido (0)
    #     Given: preferencia con orden_prioridad=0
    #     Then: ValidationError("El orden de prioridad debe ser mayor que cero.")
    #     """
    #     ahora_congelado = self.ahora
    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 0}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(ctx.exception.messages, ["El orden de prioridad debe ser mayor que cero."])


    # def test_procesar_solicitud_insignia_tradicional_orden_prioridad_negativo_bloquea(self):
    #     """
    #     Test: orden_prioridad inválido (-1)
    #     Given: preferencia con orden_prioridad=-1
    #     Then: ValidationError("El orden de prioridad debe ser mayor que cero.")
    #     """
    #     ahora_congelado = self.ahora
    #     preferencias_data = [{"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": -1}]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(ctx.exception.messages, ["El orden de prioridad debe ser mayor que cero."])



    # def test_procesar_solicitud_insignia_tradicional_prioridad_duplicada(self):
    #     """
    #     Test: orden_prioridad duplicado
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         dos preferencias con orden_prioridad=1
    #     When: intenta procesar la solicitud
    #     Then: ValidationError("No puede haber orden_prioridad duplicado.")
    #     """
    #     ahora_congelado = self.ahora

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_1,
    #             "orden_prioridad": 1,
    #         },
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_2,
    #             "orden_prioridad": 1,
    #         },
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["No puede haber orden de prioridad duplicado."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_puesto_duplicado_en_preferencias(self):
    #     """
    #     Test: Puesto duplicado en preferencias
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         mismo puesto_solicitado repetido con prioridades distintas
    #     When: intenta procesar la solicitud
    #     Then: ValidationError("No puede haber un puesto duplicado en las preferencias.")
    #     """
    #     ahora_congelado = self.ahora

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_1,
    #             "orden_prioridad": 1,
    #         },
    #         {
    #             "puesto_solicitado": self.puesto_insignia_disponible_1,
    #             "orden_prioridad": 2,
    #         },
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["No puede haber un puesto duplicado en las preferencias."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_puesto_de_otro_acto(self):
    #     """
    #     Test: Preferencia con puesto de OTRO acto
    #     Given: acto TRADICIONAL, requiere_papeleta=True, en plazo,
    #         hermano ALTA, al corriente, cuerpo permitido, sin papeleta previa,
    #         preferencia con puesto.acto != acto
    #     When: intenta procesar la solicitud
    #     Then: ValidationError("No puede seleccionar un puesto de otro acto.")
    #     """
    #     ahora_congelado = self.ahora

    #     preferencias_data = [
    #         {
    #             "puesto_solicitado": self.puesto_insignia_otro_acto,
    #             "orden_prioridad": 1,
    #         }
    #     ]

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with self.assertRaises(ValidationError) as ctx:
    #             self.service.procesar_solicitud_insignia_tradicional(
    #                 hermano=self.hermano_ok,
    #                 acto=self.acto_tradicional_en_plazo,
    #                 preferencias_data=preferencias_data,
    #             )

    #     self.assertEqual(
    #         ctx.exception.messages,
    #         ["No puede seleccionar un puesto de otro acto."]
    #     )



    # def test_procesar_solicitud_insignia_tradicional_atomicidad_si_falla_preferencia_no_queda_nada(self):
    #     """
    #     Test: A1. Atomicidad - si falla la creación de una preferencia, no queda nada
    #     Given: todo OK, preferencias con 2 items válidos (mismo acto)
    #     When: PreferenciaSolicitud.objects.create falla en la 2ª llamada (Exception("boom"))
    #     Then: rollback -> PapeletaSitio.objects.count() == 0
    #         rollback -> PreferenciaSolicitud.objects.count() == 0
    #     """
    #     ahora_congelado = self.ahora
    #     acto = self.acto_tradicional_en_plazo

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1},
    #         {"puesto_solicitado": self.puesto_insignia_disponible_2, "orden_prioridad": 2},
    #     ]

    #     self.assertEqual(PapeletaSitio.objects.count(), 0)
    #     self.assertEqual(PreferenciaSolicitud.objects.count(), 0)

    #     original_create = PreferenciaSolicitud.objects.create
    #     llamadas = {"n": 0}

    #     def create_side_effect(*args, **kwargs):
    #         llamadas["n"] += 1
    #         if llamadas["n"] == 2:
    #             raise Exception("boom")
    #         return original_create(*args, **kwargs)

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with patch.object(PreferenciaSolicitud.objects, "create", side_effect=create_side_effect):
    #             with self.assertRaises(Exception) as ctx:
    #                 self.service.procesar_solicitud_insignia_tradicional(
    #                     hermano=self.hermano_ok,
    #                     acto=acto,
    #                     preferencias_data=preferencias_data,
    #                 )

    #     self.assertEqual(str(ctx.exception), "boom")

    #     self.assertEqual(PapeletaSitio.objects.count(), 0)
    #     self.assertEqual(PreferenciaSolicitud.objects.count(), 0)



    # def test_procesar_solicitud_insignia_tradicional_atomicidad_fallo_al_guardar_papeleta(self):
    #     """
    #     Test: Atomicidad - fallo al guardar la papeleta
    #     Given: todo OK, preferencias con 2 items válidos
    #     When: PapeletaSitio.save(update_fields=...) lanza Exception("boom")
    #     Then: rollback -> PapeletaSitio.objects.count() == 0
    #         rollback -> PreferenciaSolicitud.objects.count() == 0
    #     """
    #     ahora_congelado = self.ahora
    #     acto = self.acto_tradicional_en_plazo

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1},
    #         {"puesto_solicitado": self.puesto_insignia_disponible_2, "orden_prioridad": 2},
    #     ]

    #     self.assertEqual(PapeletaSitio.objects.count(), 0)
    #     self.assertEqual(PreferenciaSolicitud.objects.count(), 0)

    #     original_save = PapeletaSitio.save

    #     def save_side_effect(self_obj, *args, **kwargs):
    #         if kwargs.get("update_fields") == ["es_solicitud_insignia"]:
    #             raise Exception("boom")
    #         return original_save(self_obj, *args, **kwargs)

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with patch.object(PapeletaSitio, "save", autospec=True, side_effect=save_side_effect):
    #             with self.assertRaises(Exception) as ctx:
    #                 self.service.procesar_solicitud_insignia_tradicional(
    #                     hermano=self.hermano_ok,
    #                     acto=acto,
    #                     preferencias_data=preferencias_data,
    #                 )

    #     self.assertEqual(str(ctx.exception), "boom")

    #     self.assertEqual(PapeletaSitio.objects.count(), 0)
    #     self.assertEqual(PreferenciaSolicitud.objects.count(), 0)



    # def test_procesar_solicitud_insignia_tradicional_atomicidad_fallo_en_crear_papeleta_base(self):
    #     """
    #     Test: Atomicidad - fallo en _crear_papeleta_base
    #     Given: todo OK, preferencias con 2 items válidos
    #     When: _crear_papeleta_base lanza Exception("boom") antes de crear la papeleta
    #     Then: 0 persistencia -> PapeletaSitio.objects.count() == 0
    #                         PreferenciaSolicitud.objects.count() == 0
    #     """
    #     ahora_congelado = self.ahora
    #     acto = self.acto_tradicional_en_plazo

    #     preferencias_data = [
    #         {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1},
    #         {"puesto_solicitado": self.puesto_insignia_disponible_2, "orden_prioridad": 2},
    #     ]

    #     self.assertEqual(PapeletaSitio.objects.count(), 0)
    #     self.assertEqual(PreferenciaSolicitud.objects.count(), 0)

    #     with patch("django.utils.timezone.now", return_value=ahora_congelado):
    #         with patch.object(self.service, "_crear_papeleta_base", side_effect=Exception("boom")):
    #             with self.assertRaises(Exception) as ctx:
    #                 self.service.procesar_solicitud_insignia_tradicional(
    #                     hermano=self.hermano_ok,
    #                     acto=acto,
    #                     preferencias_data=preferencias_data,
    #                 )

    #     self.assertEqual(str(ctx.exception), "boom")

    #     self.assertEqual(PapeletaSitio.objects.count(), 0)
    #     self.assertEqual(PreferenciaSolicitud.objects.count(), 0)



    def test_insignia_tradicional_solo_junta_ok_si_hermano_es_junta(self):
        papeleta = self.service.procesar_solicitud_insignia_tradicional(
            hermano=self.hermano_junta,
            acto=self.acto_tradicional_en_plazo,
            preferencias_data=self.preferencias_solo_junta,
        )

        self.assertIsNotNone(papeleta.id)
        self.assertTrue(papeleta.es_solicitud_insignia)

        # Se creó la preferencia
        self.assertEqual(papeleta.preferencias.count(), 1)
        pref = papeleta.preferencias.first()
        self.assertEqual(pref.puesto_solicitado_id, self.puesto_insignia_solo_junta.id)
        self.assertEqual(pref.orden_prioridad, 1)



    def test_insignia_tradicional_solo_junta_error_si_hermano_no_es_junta(self):
        with self.assertRaises(ValidationError) as ctx:
            self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional_en_plazo,
                preferencias_data=self.preferencias_solo_junta,
            )

        self.assertIn("exclusivo", str(ctx.exception))
        self.assertIn("Junta de Gobierno", str(ctx.exception))



    def test_insignia_tradicional_mixta_con_solo_junta_falla_y_no_persiste_por_atomic(self):
        preferencias_mix = [
            {"puesto_solicitado": self.puesto_insignia_disponible_1, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_insignia_solo_junta, "orden_prioridad": 2},
        ]

        with self.assertRaises(ValidationError):
            self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,  # no es junta
                acto=self.acto_tradicional_en_plazo,
                preferencias_data=preferencias_mix,
            )

        # No se creó papeleta (atomic)
        self.assertFalse(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional_en_plazo
            ).exists()
        )



    def test_insignia_tradicional_solo_junta_no_llega_si_cuerpo_no_permitido(self):
        with self.assertRaises(ValidationError) as ctx:
            self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_no_permitido,  # costaleros
                acto=self.acto_tradicional_en_plazo,
                preferencias_data=self.preferencias_solo_junta,
            )

        # Esperas error por cuerpo, no por junta
        self.assertIn("cuerpo", str(ctx.exception).lower())
