from datetime import date, timedelta
from unittest.mock import patch
from django.forms import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, models

from api.models import Acto, CuerpoPertenencia, Cuota, Hermano, HermanoCuerpo, PapeletaSitio, PreferenciaSolicitud, Puesto, TipoActo, TipoPuesto
from api.servicios.solicitud_insignia_service import SolicitudInsigniaService
from api.serializers import SolicitudInsigniaSerializer


class ProcesarSolicitudInsigniaTradicionalServiceTest(TestCase):
    def setUp(self):
        self.service = SolicitudInsigniaService()
        self.ahora = timezone.now()

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
            fecha_nacimiento=date(self.ahora.year - 30, 1, 1),
            esAdmin=False,
        )

        self.hermano_junta = Hermano.objects.create_user(
            dni="11111111H",
            username="11111111H",
            password="password",
            nombre="Juan",
            primer_apellido="Junta",
            segundo_apellido="Gobierno",
            email="junta@example.com",
            telefono="600111111",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=2001,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento=date(self.ahora.year - 35, 1, 1),
            esAdmin=False,
        )

        self.cuerpo_nazarenos = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS
        )
        self.cuerpo_junta = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )

        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 5
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_junta,
            cuerpo=self.cuerpo_junta,
            anio_ingreso=self.ahora.year - 10
        )

        self.anio_actual = self.ahora.date().year
        self.anio_limite = self.anio_actual - 1

        for anio in range(self.anio_limite - 2, self.anio_limite + 1):
            Cuota.objects.create(
                hermano=self.hermano_ok,
                anio=anio,
                tipo=Cuota.TipoCuota.ORDINARIA,
                descripcion=f"Cuota {anio}",
                importe="30.00",
                estado=Cuota.EstadoCuota.PAGADA,
                metodo_pago=Cuota.MetodoPago.DOMICILIACION,
                fecha_pago=self.ahora.date(),
            )

        for anio in range(self.anio_limite - 2, self.anio_limite + 1):
            Cuota.objects.create(
                hermano=self.hermano_junta,
                anio=anio,
                tipo=Cuota.TipoCuota.ORDINARIA,
                descripcion=f"Cuota {anio}",
                importe="30.00",
                estado=Cuota.EstadoCuota.PAGADA,
                metodo_pago=Cuota.MetodoPago.DOMICILIACION,
                fecha_pago=self.ahora.date(),
            )

        self.tipo_con_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        self.fecha_acto = self.ahora + timedelta(days=30)

        self.inicio_insignias = self.ahora - timedelta(hours=1)
        self.fin_insignias = self.ahora + timedelta(hours=2)

        self.inicio_cirios = self.fin_insignias + timedelta(hours=1)
        self.fin_cirios = self.inicio_cirios + timedelta(days=2)

        self.acto_tradicional = Acto.objects.create(
            nombre="Estación de Penitencia 2026",
            descripcion="Acto con reparto tradicional",
            fecha=self.fecha_acto,
            tipo_acto=self.tipo_con_papeleta,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            inicio_solicitud=self.inicio_insignias,
            fin_solicitud=self.fin_insignias,
            inicio_solicitud_cirios=self.inicio_cirios,
            fin_solicitud_cirios=self.fin_cirios,
        )

        self.tipo_insignia = TipoPuesto.objects.create(
            nombre_tipo="Insignia genérica",
            solo_junta_gobierno=False,
            es_insignia=True
        )
        self.tipo_insignia_solo_junta = TipoPuesto.objects.create(
            nombre_tipo="Insignia Junta",
            solo_junta_gobierno=True,
            es_insignia=True
        )
        self.tipo_no_insignia = TipoPuesto.objects.create(
            nombre_tipo="Puesto normal",
            solo_junta_gobierno=False,
            es_insignia=False
        )

        self.puesto_ok_1 = Puesto.objects.create(
            nombre="Senatus",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia
        )
        self.puesto_ok_2 = Puesto.objects.create(
            nombre="Bacalao",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia
        )
        self.puesto_solo_junta = Puesto.objects.create(
            nombre="Varas Junta",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia_solo_junta
        )
        self.puesto_no_insignia = Puesto.objects.create(
            nombre="Cirio normal (no insignia)",
            numero_maximo_asignaciones=10,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_no_insignia
        )
        self.puesto_no_disponible = Puesto.objects.create(
            nombre="Insignia bloqueada",
            numero_maximo_asignaciones=1,
            disponible=False,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia
        )

        self.preferencias_ok = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 2},
        ]



    def test_tradicional_solicitud_insignia_valida_minima_1_preferencia_ok(self):
        """
        Test: Solicitud válida mínima (TRADICIONAL - INSIGNIAS) con 1 preferencia

        Given: hermano en ALTA, al corriente hasta año anterior, con cuerpo permitido.
            acto TRADICIONAL con plazo de insignias vigente.
            1 preferencia a un puesto insignia disponible del acto.
        When: se procesa la solicitud de insignia tradicional con 1 preferencia.
        Then: devuelve PapeletaSitio creada.
            estado_papeleta = SOLICITADA.
            es_solicitud_insignia = True.
            anio = acto.fecha.year.
            fecha_solicitud coincide con timezone.now() (freeze).
            se crea 1 PreferenciaSolicitud.
        """
        now = timezone.now()

        preferencias_minimas = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_minimas,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_ok)
        self.assertEqual(papeleta.acto, self.acto_tradicional)

        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)
        self.assertEqual(papeleta.anio, self.acto_tradicional.fecha.year)

        self.assertEqual(papeleta.fecha_solicitud, now)

        self.assertEqual(PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(), 1)

        pref = PreferenciaSolicitud.objects.get(papeleta=papeleta)
        self.assertEqual(pref.orden_prioridad, 1)
        self.assertEqual(pref.puesto_solicitado, self.puesto_ok_1)



    def test_tradicional_solicitud_insignia_valida_varias_preferencias_3_ok(self):
        """
        Test: Solicitud válida con varias preferencias (3)

        Given: hermano en ALTA, al corriente hasta año anterior, con cuerpo permitido.
            acto TRADICIONAL con plazo de insignias vigente.
            3 preferencias a puestos insignia disponibles del acto.
        When: se procesa la solicitud de insignia tradicional con 3 preferencias.
        Then: devuelve PapeletaSitio creada y se crean 3 PreferenciaSolicitud
            con orden_prioridad = 1..3.
        """
        now = timezone.now()

        puesto_ok_3 = Puesto.objects.create(
            nombre="3ª Insignia",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia,
        )

        preferencias_3 = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 2},
            {"puesto_solicitado": puesto_ok_3.id, "orden_prioridad": 3},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_3,
            )

        self.assertIsNotNone(papeleta.id)

        prefs = list(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta)
            .select_related("puesto_solicitado")
            .order_by("orden_prioridad")
        )
        self.assertEqual(len(prefs), 3)

        self.assertEqual([p.orden_prioridad for p in prefs], [1, 2, 3])

        self.assertEqual(
            [p.puesto_solicitado_id for p in prefs],
            [self.puesto_ok_1.id, self.puesto_ok_2.id, puesto_ok_3.id],
        )



    def test_tradicional_solicitud_insignia_preferencias_pasando_ids_int_ok(self):
        """
        Test: Preferencias pasando IDs (int)

        Given: preferencias_data=[{"puesto_solicitado": puesto.id, "orden_prioridad": 1}]
            El puesto existe, es insignia y pertenece al acto.
        When: se procesa la solicitud de insignia tradicional.
        Then: el servicio resuelve masivamente los IDs a instancias de Puesto
            y se guarda correctamente la PreferenciaSolicitud.
        """
        now = timezone.now()

        preferencias_ids = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_ids,
            )

        self.assertIsNotNone(papeleta.id)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )

        pref = PreferenciaSolicitud.objects.get(papeleta=papeleta)

        self.assertIsInstance(pref.puesto_solicitado, Puesto)
        self.assertEqual(pref.puesto_solicitado.id, self.puesto_ok_1.id)

        self.assertEqual(pref.orden_prioridad, 1)



    def test_tradicional_solicitud_insignia_preferencias_pasando_ids_string_numerico_ok(self):
        """
        Test: Preferencias pasando IDs como string numérico

        Given: preferencias_data=[{"puesto_solicitado": "123", "orden_prioridad": 1}]
            donde el ID existe en BD.
        When: se procesa la solicitud de insignia tradicional.
        Then: el servicio resuelve correctamente el ID string → int,
            obtiene la instancia de Puesto y guarda la PreferenciaSolicitud.
        """
        now = timezone.now()

        preferencias_ids_str = [
            {"puesto_solicitado": str(self.puesto_ok_1.id), "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_ids_str,
            )

        self.assertIsNotNone(papeleta.id)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )

        pref = PreferenciaSolicitud.objects.get(papeleta=papeleta)

        self.assertIsInstance(pref.puesto_solicitado, Puesto)
        self.assertEqual(pref.puesto_solicitado.id, self.puesto_ok_1.id)

        self.assertEqual(pref.orden_prioridad, 1)



    def test_tradicional_solicitud_insignia_preferencias_pasando_instancias_puesto_ok(self):
        """
        Test: Preferencias pasando instancias Puesto

        Given: preferencias_data=[{"puesto_solicitado": <Puesto>, "orden_prioridad": 1}]
            (instancia ya resuelta).
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, no necesita resolver IDs; se guarda PreferenciaSolicitud correctamente.
        """
        now = timezone.now()

        preferencias_instancias = [
            {"puesto_solicitado": self.puesto_ok_1, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2, "orden_prioridad": 2},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_instancias,
            )

        self.assertIsNotNone(papeleta.id)

        prefs = list(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta)
            .select_related("puesto_solicitado")
            .order_by("orden_prioridad")
        )
        self.assertEqual(len(prefs), 2)

        self.assertEqual([p.orden_prioridad for p in prefs], [1, 2])
        self.assertEqual([p.puesto_solicitado_id for p in prefs], [self.puesto_ok_1.id, self.puesto_ok_2.id])



    def test_tradicional_solicitud_insignia_hermano_cuerpo_permitido_nazarenos_ok(self):
        """
        Test: Hermano perteneciente a un cuerpo permitido (NAZARENOS)

        Given: hermano en estado ALTA, al corriente de cuotas,
            perteneciente al cuerpo NAZARENOS (permitido).
            acto TRADICIONAL con plazo de insignias vigente.
            1 preferencia válida a un puesto insignia disponible.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio sin error.
        """
        now = timezone.now()

        cuerpos_hermano = set(
            self.hermano_ok.cuerpos.values_list("nombre_cuerpo", flat=True)
        )
        self.assertIn(
            CuerpoPertenencia.NombreCuerpo.NAZARENOS,
            cuerpos_hermano
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_ok)
        self.assertEqual(papeleta.acto, self.acto_tradicional)
        self.assertEqual(
            papeleta.estado_papeleta,
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )
        self.assertTrue(papeleta.es_solicitud_insignia)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )



    def test_tradicional_solicitud_insignia_hermano_varios_cuerpos_permitidos_ok(self):
        """
        Test: Hermano con varios cuerpos permitidos (NAZARENOS + JUVENTUD)

        Given: hermano en ALTA, al corriente, y perteneciente a dos cuerpos permitidos:
            NAZARENOS y JUVENTUD.
            acto TRADICIONAL con plazo de insignias vigente.
            1 preferencia válida a un puesto insignia disponible.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio sin error.
        """
        now = timezone.now()

        cuerpo_juventud = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUVENTUD
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=cuerpo_juventud,
            anio_ingreso=self.ahora.year - 2
        )

        cuerpos_hermano = set(
            self.hermano_ok.cuerpos.values_list("nombre_cuerpo", flat=True)
        )
        self.assertIn(CuerpoPertenencia.NombreCuerpo.NAZARENOS, cuerpos_hermano)
        self.assertIn(CuerpoPertenencia.NombreCuerpo.JUVENTUD, cuerpos_hermano)

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_ok)
        self.assertEqual(papeleta.acto, self.acto_tradicional)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )



    def test_tradicional_solicitud_insignia_puesto_exclusivo_junta_y_hermano_de_junta_ok(self):
        """
        Test: Puesto exclusivo Junta + hermano de Junta

        Given: tipo_puesto.solo_junta_gobierno=True (puesto exclusivo).
            hermano pertenece al cuerpo JUNTA_GOBIERNO.
            acto TRADICIONAL con plazo de insignias vigente.
            1 preferencia al puesto exclusivo.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio y la PreferenciaSolicitud.
        """
        now = timezone.now()

        cuerpos_hermano = set(
            self.hermano_junta.cuerpos.values_list("nombre_cuerpo", flat=True)
        )
        self.assertIn(CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO, cuerpos_hermano)

        preferencias = [
            {"puesto_solicitado": self.puesto_solo_junta.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_junta,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_junta)
        self.assertEqual(papeleta.acto, self.acto_tradicional)

        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )
        pref = PreferenciaSolicitud.objects.get(papeleta=papeleta)
        self.assertEqual(pref.puesto_solicitado, self.puesto_solo_junta)
        self.assertEqual(pref.orden_prioridad, 1)



    def test_tradicional_solicitud_insignia_historial_cuotas_hasta_anio_anterior_pagado_o_exento_ok(self):
        """
        Test: Historial de cuotas existente hasta año anterior (todo pagado/exento)

        Given: hermano en ALTA, con historial de cuotas hasta el año anterior inclusive,
            sin cuotas PENDIENTE/DEVUELTA (solo PAGADA o EXENTO).
            acto TRADICIONAL con plazo de insignias vigente.
            1 preferencia válida.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio.
        """
        now = timezone.now()

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=self.anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {self.anio_limite} (exento)",
            importe="0.00",
            estado=Cuota.EstadoCuota.EXENTO,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=now.date(),
        )

        self.assertTrue(self.hermano_ok.cuotas.filter(anio__lte=self.anio_limite).exists())
        self.assertFalse(
            self.hermano_ok.cuotas.filter(
                anio__lte=self.anio_limite,
                estado__in=[Cuota.EstadoCuota.PENDIENTE, Cuota.EstadoCuota.DEVUELTA],
            ).exists()
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_ok)
        self.assertEqual(papeleta.acto, self.acto_tradicional)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)



    def test_tradicional_solicitud_insignia_plazo_vigente_borde_ahora_igual_inicio_ok(self):
        """
        Test: Plazo vigente en borde (ahora == inicio_solicitud)

        Given: acto TRADICIONAL con inicio_solicitud == now y fin_solicitud > now.
        When: se procesa solicitud de insignia tradicional.
        Then: OK (tu check es ahora < inicio).
        """
        now = timezone.now()

        self.acto_tradicional.inicio_solicitud = now
        self.acto_tradicional.fin_solicitud = now + timedelta(hours=1)
        self.acto_tradicional.save()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)


    def test_tradicional_solicitud_insignia_plazo_vigente_borde_ahora_igual_fin_ok(self):
        """
        Test: Plazo vigente en borde (ahora == fin_solicitud)

        Given: acto TRADICIONAL con inicio_solicitud < now y fin_solicitud == now.
        When: se procesa solicitud de insignia tradicional.
        Then: OK (tu check es ahora > fin).
        """
        now = timezone.now()

        self.acto_tradicional.inicio_solicitud = now - timedelta(hours=1)
        self.acto_tradicional.fin_solicitud = now
        self.acto_tradicional.save()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)



    def test_tradicional_solicitud_insignia_existe_papeleta_anulada_previa_permita_nueva_ok(self):
        """
        Test: Existe papeleta anterior ANULADA para el mismo acto

        Given: ya existe una PapeletaSitio ANULADA para (hermano, acto).
        When: se procesa una nueva solicitud de insignia tradicional para el mismo acto.
        Then: OK, se permite crear una nueva papeleta (no bloquea por unicidad lógica del servicio).
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(days=1),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
            es_solicitud_insignia=True,
            codigo_verificacion="ANULAD01",
        )

        self.assertTrue(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
            ).exists()
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta_nueva = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta_nueva.id)
        self.assertEqual(papeleta_nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta_nueva.es_solicitud_insignia)

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano_ok, acto=self.acto_tradicional).count(),
            2
        )
        self.assertTrue(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
            ).exists()
        )



    def test_tradicional_solicitud_insignia_existe_papeleta_no_asignada_previa_permita_nueva_ok(self):
        """
        Test: Existe papeleta anterior NO_ASIGNADA para el mismo acto

        Given: ya existe una PapeletaSitio NO_ASIGNADA para (hermano, acto).
        When: se procesa una nueva solicitud de insignia tradicional para el mismo acto.
        Then: OK, se permite crear una nueva papeleta (no bloquea por unicidad lógica del servicio).
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(days=1),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
            es_solicitud_insignia=True,
            codigo_verificacion="NOASIG01",
        )

        self.assertTrue(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA
            ).exists()
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta_nueva = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta_nueva.id)
        self.assertEqual(
            papeleta_nueva.estado_papeleta,
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )
        self.assertTrue(papeleta_nueva.es_solicitud_insignia)

        self.assertEqual(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional
            ).count(),
            2
        )
        self.assertTrue(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
            ).exists()
        )



    def test_tradicional_solicitud_insignia_edad_18_cumplidos_justo_antes_inicio_ok(self):
        """
        Test: acto.inicio_solicitud presente y hermano cumple 18 justo antes

        Given: acto con inicio_solicitud definido.
            hermano cumple 18 años el día anterior al inicio del plazo.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, supera la validación de edad mínima.
        """
        now = timezone.now()

        inicio = now
        self.acto_tradicional.inicio_solicitud = inicio
        self.acto_tradicional.fin_solicitud = inicio + timedelta(hours=2)
        self.acto_tradicional.save()

        fecha_nacimiento = inicio.date().replace(year=inicio.year - 18) - timedelta(days=1)
        self.hermano_ok.fecha_nacimiento = fecha_nacimiento
        self.hermano_ok.save()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(
            papeleta.estado_papeleta,
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )
        self.assertTrue(papeleta.es_solicitud_insignia)



    def test_tradicional_solicitud_insignia_edad_18_cumple_el_mismo_dia_inicio_ok(self):
        """
        Test: acto.inicio_solicitud presente y hermano cumple 18 el mismo día

        Given: acto con inicio_solicitud definido.
            hermano cumple 18 años exactamente el mismo día del inicio del plazo.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, según el cálculo de edad (>= 18).
        """
        now = timezone.now()

        inicio = now
        self.acto_tradicional.inicio_solicitud = inicio
        self.acto_tradicional.fin_solicitud = inicio + timedelta(hours=2)
        self.acto_tradicional.save()

        # Cumple 18 el MISMO día del inicio (edad = 18)
        fecha_nacimiento = inicio.date().replace(year=inicio.year - 18)
        self.hermano_ok.fecha_nacimiento = fecha_nacimiento
        self.hermano_ok.save()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)



    def test_tradicional_solicitud_insignia_atomicidad_crea_papeleta_y_preferencias_ok(self):
        """
        Test: Atomicidad (éxito) crea papeleta y preferencias en una sola transacción

        Given: acto TRADICIONAL con plazo vigente y hermano apto.
            preferencias válidas (2).
        When: se procesa la solicitud de insignia tradicional.
        Then: tras éxito, existen en BD la PapeletaSitio (SOLICITADA, es_solicitud_insignia=True)
            y sus PreferenciaSolicitud asociadas (2).
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 2},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertTrue(PapeletaSitio.objects.filter(id=papeleta.id).exists())

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)
        self.assertEqual(papeleta_db.hermano, self.hermano_ok)
        self.assertEqual(papeleta_db.acto, self.acto_tradicional)
        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta_db.es_solicitud_insignia)

        prefs_qs = PreferenciaSolicitud.objects.filter(papeleta=papeleta_db).order_by("orden_prioridad")
        self.assertEqual(prefs_qs.count(), 2)
        self.assertEqual(list(prefs_qs.values_list("orden_prioridad", flat=True)), [1, 2])
        self.assertEqual(
            list(prefs_qs.values_list("puesto_solicitado_id", flat=True)),
            [self.puesto_ok_1.id, self.puesto_ok_2.id],
        )



    def test_tradicional_solicitud_insignia_con_vinculado_a_falla(self):
        """
        Test: Si vinculado_a no es None

        Given: se intenta procesar una solicitud de insignia tradicional
            pasando un hermano en el parámetro vinculado_a.
        When: se llama al servicio.
        Then: ValidationError con mensaje exacto:
            “Las solicitudes de insignia no permiten vincularse con otro hermano.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                    vinculado_a=self.hermano_junta,
                )

        self.assertEqual(
            str(ctx.exception),
            "['Las solicitudes de insignia no permiten vincularse con otro hermano.']"
        )

        self.assertFalse(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional
            ).exists()
        )



    def test_tradicional_solicitud_insignia_acto_none_falla(self):
        """
        Test: acto is None

        Given: acto=None.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError con dict exacto:
            {"tipo_acto": "El tipo de acto es obligatorio."}
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=None,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.message_dict,
            {"tipo_acto": ["El tipo de acto es obligatorio."]}
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_acto_con_tipo_acto_none_falla(self):
        """
        Test: acto.tipo_acto is None

        Given: acto con tipo_acto_id=None (sin persistir).
        When: se procesa la solicitud.
        Then: ValidationError dict exacto {"tipo_acto": "El tipo de acto es obligatorio."}
        """
        now = timezone.now()

        self.acto_tradicional.tipo_acto_id = None

        preferencias = [{"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1}]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.message_dict, {"tipo_acto": ["El tipo de acto es obligatorio."]})



    def test_tradicional_solicitud_insignia_acto_no_requiere_papeleta_falla(self):
        """
        Test: acto.tipo_acto.requiere_papeleta = False

        Given: acto cuyo tipo_acto no requiere papeleta (acto persistido coherente: sin modalidad ni fechas).
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError con mensaje:
            “El acto '<nombre>' no admite solicitudes de papeleta.”
        """
        now = timezone.now()

        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CABILDO_GENERAL,
            requiere_papeleta=False
        )

        self.acto_tradicional.tipo_acto = tipo_sin_papeleta
        self.acto_tradicional.modalidad = None
        self.acto_tradicional.inicio_solicitud = None
        self.acto_tradicional.fin_solicitud = None
        self.acto_tradicional.inicio_solicitud_cirios = None
        self.acto_tradicional.fin_solicitud_cirios = None
        self.acto_tradicional.save(
            update_fields=[
                "tipo_acto",
                "modalidad",
                "inicio_solicitud",
                "fin_solicitud",
                "inicio_solicitud_cirios",
                "fin_solicitud_cirios",
            ]
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [f"El acto '{self.acto_tradicional.nombre}' no admite solicitudes de papeleta."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_acto_modalidad_unificado_falla(self):
        """
        Test: acto.modalidad != TRADICIONAL (Given: UNIFICADO)

        Given: acto cuyo tipo_acto requiere papeleta,
            pero con modalidad UNIFICADO (acto persistido coherente).
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError:
            “Este proceso es exclusivo para actos de modalidad TRADICIONAL.”
        """
        now = timezone.now()

        self.acto_tradicional.modalidad = Acto.ModalidadReparto.UNIFICADO
        self.acto_tradicional.inicio_solicitud_cirios = None
        self.acto_tradicional.fin_solicitud_cirios = None
        self.acto_tradicional.save(
            update_fields=[
                "modalidad",
                "inicio_solicitud_cirios",
                "fin_solicitud_cirios",
            ]
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["Este proceso es exclusivo para actos de modalidad TRADICIONAL."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_plazo_no_configurado_inicio_none_falla(self):
        """
        Test: Plazo no configurado (inicio_solicitud=None)

        Given: acto TRADICIONAL con inicio_solicitud=None (sin persistir, porque el modelo lo prohíbe).
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El plazo de insignias no está configurado en el acto.”
        """
        now = timezone.now()

        self.acto_tradicional.inicio_solicitud = None

        preferencias = [{"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1}]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.messages, ["El plazo de insignias no está configurado en el acto."])
        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_plazo_no_configurado_fin_none_falla(self):
        """
        Test: Plazo no configurado (fin_solicitud=None)

        Given: acto TRADICIONAL con fin_solicitud=None (sin persistir, porque el modelo lo prohíbe).
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El plazo de insignias no está configurado en el acto.”
        """
        now = timezone.now()

        self.acto_tradicional.fin_solicitud = None

        preferencias = [{"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1}]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.messages, ["El plazo de insignias no está configurado en el acto."])
        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_plazo_aun_no_ha_comenzado_falla(self):
        """
        Test: Aún no ha comenzado (ahora < inicio_solicitud)

        Given: acto TRADICIONAL con inicio_solicitud en el futuro y fin_solicitud válido.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El plazo de solicitud de insignias aún no ha comenzado.”
        """
        now = timezone.now()

        self.acto_tradicional.inicio_solicitud = now + timedelta(minutes=5)
        self.acto_tradicional.fin_solicitud = now + timedelta(hours=1)
        self.acto_tradicional.save(update_fields=["inicio_solicitud", "fin_solicitud"])

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["El plazo de solicitud de insignias aún no ha comenzado."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_plazo_finalizado_falla(self):
        """
        Test: Plazo finalizado (ahora > fin_solicitud)

        Given: acto TRADICIONAL con inicio_solicitud y fin_solicitud configurados,
            y ahora es posterior a fin_solicitud.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El plazo de solicitud de insignias ha finalizado.”
        """
        now = timezone.now()

        self.acto_tradicional.inicio_solicitud = now - timedelta(hours=2)
        self.acto_tradicional.fin_solicitud = now - timedelta(minutes=1)
        self.acto_tradicional.save(update_fields=["inicio_solicitud", "fin_solicitud"])

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["El plazo de solicitud de insignias ha finalizado."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_hermano_no_alta_pendiente_ingreso_falla(self):
        """
        Test: Hermano no ALTA (PENDIENTE_INGRESO)

        Given: hermano con estado PENDIENTE_INGRESO.
            acto TRADICIONAL con plazo de insignias vigente.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Solo los hermanos en estado ALTA pueden solicitar papeleta.”
        """
        now = timezone.now()

        self.hermano_ok.estado_hermano = Hermano.EstadoHermano.PENDIENTE_INGRESO
        self.hermano_ok.save(update_fields=["estado_hermano"])

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["Solo los hermanos en estado ALTA pueden solicitar papeleta."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_hermano_no_alta_baja_falla(self):
        """
        Test: Hermano no ALTA (BAJA)

        Given: hermano con estado BAJA.
            acto TRADICIONAL con plazo de insignias vigente.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Solo los hermanos en estado ALTA pueden solicitar papeleta.”
        """
        now = timezone.now()

        self.hermano_ok.estado_hermano = Hermano.EstadoHermano.BAJA
        self.hermano_ok.fecha_baja_corporacion = now.date()
        self.hermano_ok.save(update_fields=["estado_hermano", "fecha_baja_corporacion"])

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["Solo los hermanos en estado ALTA pueden solicitar papeleta."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_deuda_pendiente_en_anio_limite_falla(self):
        """
        Test: Deuda PENDIENTE en el año límite (anio_actual=2026 → límite=2025)

        Given: hermano en ALTA con una cuota PENDIENTE en el año 2025.
            acto TRADICIONAL con plazo de insignias vigente.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError menciona explícitamente el año 2025.
        """
        now = timezone.now()

        anio_actual = now.year
        anio_limite = anio_actual - 1

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite} pendiente",
            importe="30.00",
            estado=Cuota.EstadoCuota.PENDIENTE,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [
                f"Consta una cuota pendiente o devuelta del año {anio_limite}. "
                "Por favor, contacte con tesorería para regularizar su situación."
            ]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_deuda_devuelta_en_2024_falla(self):
        """
        Test: Deuda DEVUELTA en 2024 (anio_actual=2026 → límite=2025)

        Given: hermano en ALTA con una cuota DEVUELTA en el año 2024
            y sin deuda en 2025.
            acto TRADICIONAL con plazo de insignias vigente.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError menciona explícitamente el año 2024 (no 2025).
        """
        now = timezone.now()

        anio_actual = now.year
        anio_limite = anio_actual - 1

        self.hermano_ok.cuotas.filter(anio=anio_limite).delete()

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=anio_limite - 1,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion="Cuota 2024 devuelta",
            importe="30.00",
            estado=Cuota.EstadoCuota.DEVUELTA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [
                f"Consta una cuota pendiente o devuelta del año {anio_limite - 1}. "
                "Por favor, contacte con tesorería para regularizar su situación."
            ]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_deuda_en_anio_actual_no_bloquea_ok(self):
        """
        Test: Deuda en año actual (2026) pero no en <=2025

        Given: anio_actual=2026, límite=2025.
            hermano NO tiene deuda (PENDIENTE/DEVUELTA) en anios <= 2025,
            pero SÍ tiene una cuota PENDIENTE en 2026.
            acto TRADICIONAL con plazo de insignias vigente.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK (la lógica solo bloquea deudas hasta el año anterior inclusive).
        """
        now = timezone.now()

        anio_actual = now.year
        anio_limite = anio_actual - 1

        self.hermano_ok.cuotas.filter(
            anio__lte=anio_limite,
            estado__in=[Cuota.EstadoCuota.PENDIENTE, Cuota.EstadoCuota.DEVUELTA],
        ).delete()

        for anio in range(anio_limite - 2, anio_limite + 1):
            Cuota.objects.update_or_create(
                hermano=self.hermano_ok,
                anio=anio,
                tipo=Cuota.TipoCuota.ORDINARIA,
                defaults={
                    "descripcion": f"Cuota {anio} pagada",
                    "importe": "30.00",
                    "estado": Cuota.EstadoCuota.PAGADA,
                    "metodo_pago": Cuota.MetodoPago.DOMICILIACION,
                    "fecha_pago": now.date(),
                }
            )

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=anio_actual,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_actual} pendiente",
            importe="30.00",
            estado=Cuota.EstadoCuota.PENDIENTE,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )



    def test_tradicional_solicitud_insignia_sin_historial_cuotas_hasta_anio_limite_falla(self):
        """
        Test: No hay historial de cuotas hasta el año límite

        Given: anio_actual=2026, límite=2025.
            hermano en ALTA sin ninguna cuota registrada en anios <= 2025.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “No constan cuotas registradas hasta el año 2025…”
        """
        now = timezone.now()

        anio_actual = now.year
        anio_limite = anio_actual - 1

        self.hermano_ok.cuotas.filter(anio__lte=anio_limite).delete()

        self.assertFalse(
            self.hermano_ok.cuotas.filter(anio__lte=anio_limite).exists()
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [
                f"No constan cuotas registradas hasta el año {anio_limite}. "
                "Contacte con secretaría para verificar su ficha."
            ]
        )

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_historial_existe_sin_deuda_bloqueante_ok(self):
        """
        Test: Historial existe y no hay deuda (PAGADA / EXENTO / EN_REMESA)

        Given: anio_actual=2026, límite=2025.
            hermano en ALTA con historial de cuotas hasta 2025 inclusive,
            sin ninguna cuota en estado PENDIENTE o DEVUELTA.
            (solo PAGADA / EXENTO / EN_REMESA).
            acto TRADICIONAL con plazo de insignias vigente.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio.
        """
        now = timezone.now()

        anio_actual = now.year
        anio_limite = anio_actual - 1

        self.hermano_ok.cuotas.filter(
            anio__lte=anio_limite,
            estado__in=[Cuota.EstadoCuota.PENDIENTE, Cuota.EstadoCuota.DEVUELTA],
        ).delete()

        self.hermano_ok.cuotas.filter(anio__lte=anio_limite).delete()

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=anio_limite - 2,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite - 2} pagada",
            importe="30.00",
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=now.date(),
        )

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=anio_limite - 1,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite - 1} exenta",
            importe="0.00",
            estado=Cuota.EstadoCuota.EXENTO,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        Cuota.objects.create(
            hermano=self.hermano_ok,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite} en remesa",
            importe="30.00",
            estado=Cuota.EstadoCuota.EN_REMESA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(
            papeleta.estado_papeleta,
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )
        self.assertTrue(papeleta.es_solicitud_insignia)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )



    def test_tradicional_solicitud_insignia_hermano_sin_cuerpos_ok(self):
        """
        Test: Hermano sin cuerpos

        Given: hermano en ALTA, al corriente de cuotas,
            SIN ningún cuerpo asociado.
            acto TRADICIONAL con plazo de insignias vigente.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK (la validación de cuerpos retorna sin bloquear).
        """
        now = timezone.now()

        self.hermano_ok.pertenencias_cuerpos.all().delete()

        self.assertFalse(self.hermano_ok.cuerpos.exists())

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(
            papeleta.estado_papeleta,
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )
        self.assertTrue(papeleta.es_solicitud_insignia)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )



    def test_tradicional_solicitud_insignia_hermano_con_solo_cuerpos_permitidos_ok(self):
        """
        Test: Hermano con solo cuerpos permitidos

        Given: hermano en ALTA, al corriente de cuotas,
            con cuerpos dentro del set permitido (p.ej. NAZARENOS + JUVENTUD).
            acto TRADICIONAL con plazo de insignias vigente.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio.
        """
        now = timezone.now()

        self.hermano_ok.pertenencias_cuerpos.all().delete()

        cuerpo_juventud, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUVENTUD
        )

        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=now.year - 5
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=cuerpo_juventud,
            anio_ingreso=now.year - 2
        )

        self.assertTrue(self.hermano_ok.cuerpos.filter(nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS).exists())
        self.assertTrue(self.hermano_ok.cuerpos.filter(nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUVENTUD).exists())

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )



    def test_tradicional_solicitud_insignia_hermano_con_cuerpo_no_permitido_costaleros_falla(self):
        """
        Test: Hermano con un cuerpo no permitido (COSTALEROS)

        Given: hermano en ALTA, al corriente de cuotas,
            con cuerpo COSTALEROS (no permitido).
            acto TRADICIONAL con plazo de insignias vigente.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError y el mensaje contiene “COSTALEROS”.
        """
        now = timezone.now()

        self.hermano_ok.pertenencias_cuerpos.all().delete()

        cuerpo_costaleros, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )

        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=cuerpo_costaleros,
            anio_ingreso=now.year - 3
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(len(ctx.exception.messages), 1)
        self.assertIn("COSTALEROS", ctx.exception.messages[0])
        self.assertIn("no permite solicitar esta papeleta", ctx.exception.messages[0])

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_hermano_mezcla_cuerpos_permitido_y_no_permitido_falla(self):
        """
        Test: Mezcla de cuerpos permitido + no permitido

        Given: hermano en ALTA, al corriente de cuotas,
            con cuerpos NAZARENOS (permitido) + COSTALEROS (no permitido).
            acto TRADICIONAL con plazo de insignias vigente.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError y el mensaje lista SOLO los cuerpos no aptos (COSTALEROS).
        """
        now = timezone.now()

        self.hermano_ok.pertenencias_cuerpos.all().delete()

        cuerpo_costaleros, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )

        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=now.year - 5
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_ok,
            cuerpo=cuerpo_costaleros,
            anio_ingreso=now.year - 3
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(len(ctx.exception.messages), 1)
        mensaje = ctx.exception.messages[0]

        self.assertIn("COSTALEROS", mensaje)
        self.assertNotIn("NAZARENOS", mensaje)
        self.assertIn("no permite solicitar esta papeleta", mensaje)

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_varios_cuerpos_no_permitidos_falla(self):
        """
        Test: Varios no permitidos

        Given: hermano en ALTA, al corriente de cuotas,
            con varios cuerpos NO permitidos (p.ej. COSTALEROS + DIPUTADOS + BRAZALETES).
            acto TRADICIONAL con plazo de insignias vigente.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError incluye todos los no aptos (sin asumir orden).
        """
        now = timezone.now()

        self.hermano_ok.pertenencias_cuerpos.all().delete()

        cuerpo_costaleros, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )
        cuerpo_diputados, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.DIPUTADOS
        )
        cuerpo_brazaletes, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.BRAZALETES
        )

        HermanoCuerpo.objects.create(hermano=self.hermano_ok, cuerpo=cuerpo_costaleros, anio_ingreso=now.year - 3)
        HermanoCuerpo.objects.create(hermano=self.hermano_ok, cuerpo=cuerpo_diputados, anio_ingreso=now.year - 4)
        HermanoCuerpo.objects.create(hermano=self.hermano_ok, cuerpo=cuerpo_brazaletes, anio_ingreso=now.year - 2)

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(len(ctx.exception.messages), 1)
        mensaje = ctx.exception.messages[0]

        self.assertIn("COSTALEROS", mensaje)
        self.assertIn("DIPUTADOS", mensaje)
        self.assertIn("BRAZALETES", mensaje)

        self.assertFalse(PapeletaSitio.objects.exists())



    def test_tradicional_solicitud_insignia_cuerpos_como_strings_permitidos_ok(self):
        """
        Test (defensivo): cuerpos vienen como strings

        Given: hermano con cuerpo NAZARENOS (values_list devuelve strings).
        When: se procesa la solicitud de insignia tradicional.
        Then: OK.
        """
        now = timezone.now()

        cuerpos_set = set(self.hermano_ok.cuerpos.values_list("nombre_cuerpo", flat=True))
        self.assertIn(CuerpoPertenencia.NombreCuerpo.NAZARENOS.value, cuerpos_set)

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)
        self.assertEqual(PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(), 1)



    def test_tradicional_solicitud_insignia_sin_preferencias_falla(self):
        """
        Test: 0 preferencias

        Given: preferencias_data vacío.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Debe indicar al menos una preferencia.”
        """
        now = timezone.now()

        preferencias = []

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.messages, ["Debe indicar al menos una preferencia."])
        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_una_preferencia_ok(self):
        """
        Test: 1 preferencia

        Given: preferencias_data con una única preferencia válida.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio y 1 PreferenciaSolicitud.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(
            papeleta.estado_papeleta,
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )
        self.assertTrue(papeleta.es_solicitud_insignia)
        self.assertEqual(papeleta.anio, self.acto_tradicional.fecha.year)

        self.assertEqual(papeleta.fecha_solicitud, now)

        self.assertEqual(
            PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(),
            1
        )

        pref = PreferenciaSolicitud.objects.get(papeleta=papeleta)
        self.assertEqual(pref.puesto_solicitado, self.puesto_ok_1)
        self.assertEqual(pref.orden_prioridad, 1)



    def test_tradicional_solicitud_insignia_20_preferencias_limite_ok(self):
        """
        Test: 20 preferencias (límite exacto)

        Given: preferencias_data con exactamente 20 preferencias válidas.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio y 20 PreferenciaSolicitud.
        """
        now = timezone.now()

        puestos = []
        for i in range(20):
            puestos.append(
                Puesto.objects.create(
                    nombre=f"Insignia {i+1}",
                    numero_maximo_asignaciones=1,
                    disponible=True,
                    acto=self.acto_tradicional,
                    tipo_puesto=self.tipo_insignia,
                )
            )

        preferencias = [
            {"puesto_solicitado": puestos[i].id, "orden_prioridad": i + 1}
            for i in range(20)
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(
            papeleta.estado_papeleta,
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )
        self.assertTrue(papeleta.es_solicitud_insignia)

        qs = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
        self.assertEqual(qs.count(), 20)

        prioridades = list(qs.order_by("orden_prioridad").values_list("orden_prioridad", flat=True))
        self.assertEqual(prioridades, list(range(1, 21)))



    def test_tradicional_solicitud_insignia_21_preferencias_supera_limite_falla(self):
        """
        Test: 21 preferencias (supera el límite)

        Given: preferencias_data con 21 preferencias.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “No puede solicitar más de 20 puestos.”
        """
        now = timezone.now()

        puestos = []
        for i in range(21):
            puestos.append(
                Puesto.objects.create(
                    nombre=f"Insignia {i+1}",
                    numero_maximo_asignaciones=1,
                    disponible=True,
                    acto=self.acto_tradicional,
                    tipo_puesto=self.tipo_insignia,
                )
            )

        preferencias = [
            {"puesto_solicitado": puestos[i].id, "orden_prioridad": i + 1}
            for i in range(21)
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["No puede solicitar más de 20 puestos."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_id_puesto_inexistente_falla(self):
        """
        Test: ID de puesto inexistente

        Given: preferencias_data contiene un puesto_solicitado con ID que no existe.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Los siguientes IDs de puesto no existen: …”
        """
        now = timezone.now()

        max_id = Puesto.objects.aggregate(models.Max("id"))["id__max"] or 0
        id_inexistente = max_id + 9999

        preferencias = [
            {"puesto_solicitado": id_inexistente, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(len(ctx.exception.messages), 1)
        self.assertIn("Los siguientes IDs de puesto no existen:", ctx.exception.messages[0])
        self.assertIn(str(id_inexistente), ctx.exception.messages[0])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_formato_puesto_invalido_falla(self):
        """
        Test: Formato inválido de puesto

        Given: preferencias_data con puesto_solicitado="12a" (string no numérico).
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Formato de puesto inválido”.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": "12a", "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(len(ctx.exception.messages), 1)
        self.assertIn("Formato de puesto inválido", ctx.exception.messages[0])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_formato_puesto_dict_invalido_falla(self):
        """
        Test: Formato inválido de puesto (dict)

        Given: preferencias_data con puesto_solicitado={"id": 1}.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Formato de puesto inválido”.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": {"id": 1}, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(len(ctx.exception.messages), 1)
        self.assertIn("Formato de puesto inválido", ctx.exception.messages[0])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_formato_puesto_list_invalido_falla(self):
        """
        Test: Formato inválido de puesto (list)

        Given: preferencias_data con puesto_solicitado=[1].
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Formato de puesto inválido”.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": [1], "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(len(ctx.exception.messages), 1)
        self.assertIn("Formato de puesto inválido", ctx.exception.messages[0])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_mezcla_ids_e_instancias_ok(self):
        """
        Test: Mezcla IDs + instancias

        Given: preferencias_data mezcla puesto_solicitado como ID y como instancia Puesto.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio y las PreferenciaSolicitud correctamente.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2, "orden_prioridad": 2},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)

        qs = PreferenciaSolicitud.objects.filter(papeleta=papeleta).order_by("orden_prioridad")
        self.assertEqual(qs.count(), 2)

        self.assertEqual(qs[0].puesto_solicitado, self.puesto_ok_1)
        self.assertEqual(qs[1].puesto_solicitado, self.puesto_ok_2)



    def test_tradicional_solicitud_insignia_puesto_solicitado_none_falla_por_datos_incompletos(self):
        """
        Test: puesto_solicitado=None en algún item

        Given: preferencias_data contiene un item con puesto_solicitado=None.
            El resolver lo ignora, pero luego al validar debe fallar.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Datos de preferencia incompletos.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": None, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.messages, ["Datos de preferencia incompletos."])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_item_sin_puesto_solicitado_falla_por_datos_incompletos(self):
        """
        Test: Item sin puesto_solicitado

        Given: preferencias_data contiene un item sin la clave 'puesto_solicitado'.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Datos de preferencia incompletos.”
        """
        now = timezone.now()

        preferencias = [
            {"orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.messages, ["Datos de preferencia incompletos."])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_item_sin_orden_prioridad_falla_por_datos_incompletos(self):
        """
        Test: Item sin orden_prioridad

        Given: preferencias_data contiene un item sin la clave 'orden_prioridad'.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Datos de preferencia incompletos.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.messages, ["Datos de preferencia incompletos."])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_orden_prioridad_none_falla_por_datos_incompletos(self):
        """
        Test: orden_prioridad=None

        Given: preferencias_data contiene un item con orden_prioridad=None.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “Datos de preferencia incompletos.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": None},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(ctx.exception.messages, ["Datos de preferencia incompletos."])

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_serializer_normaliza_orden_prioridad_string_a_int_ok(self):
        """
        Test: orden_prioridad llega como string "1"

        Given: payload con orden_prioridad="1" y puesto_id (según PreferenciaSolicitudSerializer).
        When: serializer.is_valid().
        Then: validated_data['preferencias'][0]['orden_prioridad'] es int (1).
        """
        payload = {
            "acto_id": self.acto_tradicional.id,
            "preferencias": [
                {"puesto_id": self.puesto_ok_1.id, "orden_prioridad": "1"},
            ],
        }

        ser = SolicitudInsigniaSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)

        self.assertIn("preferencias", ser.validated_data)
        self.assertIn("puesto_solicitado", ser.validated_data["preferencias"][0])

        orden = ser.validated_data["preferencias"][0]["orden_prioridad"]
        self.assertIsInstance(orden, int)
        self.assertEqual(orden, 1)



    def test_tradicional_solicitud_insignia_prioridades_duplicadas_falla(self):
        """
        Test: Prioridades duplicadas [1,1]

        Given: preferencias_data con orden_prioridad duplicado.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “No puede haber orden de prioridad duplicado.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["No puede haber orden de prioridad duplicado."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_prioridad_cero_falla(self):
        """
        Test: Prioridad 0 [0,1]

        Given: preferencias_data con un orden_prioridad igual a 0.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El orden de prioridad debe ser mayor que cero.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 0},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["El orden de prioridad debe ser mayor que cero."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_prioridad_negativa_falla(self):
        """
        Test: Prioridades negativas [-1, 1]

        Given: preferencias_data con un orden_prioridad negativo.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El orden de prioridad debe ser mayor que cero.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": -1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["El orden de prioridad debe ser mayor que cero."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_prioridades_no_consecutivas_falla(self):
        """
        Test: Prioridades no consecutivas [1, 3]

        Given: preferencias_data con orden_prioridad no consecutivo.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El orden de prioridad debe ser consecutivo empezando por 1.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 3},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["El orden de prioridad debe ser consecutivo empezando por 1."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_prioridades_no_empieza_por_uno_falla(self):
        """
        Test: Prioridades no empiezan por 1 [2, 3]

        Given: preferencias_data con orden_prioridad que no comienza en 1.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El orden de prioridad debe ser consecutivo empezando por 1.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 2},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 3},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["El orden de prioridad debe ser consecutivo empezando por 1."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_prioridades_consecutivas_ok(self):
        """
        Test: Prioridades correctas [1, 2, 3]

        Given: preferencias_data con orden_prioridad consecutivo empezando por 1.
        When: se procesa la solicitud de insignia tradicional.
        Then: OK, se crea la PapeletaSitio y 3 PreferenciaSolicitud.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 2},
            {"puesto_solicitado": self.puesto_ok_1.id + 9999, "orden_prioridad": 3},
        ]

        puesto_extra = Puesto.objects.create(
            nombre="Insignia Extra",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia,
        )
        preferencias[2]["puesto_solicitado"] = puesto_extra.id

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)

        qs = PreferenciaSolicitud.objects.filter(papeleta=papeleta).order_by("orden_prioridad")
        self.assertEqual(qs.count(), 3)

        self.assertEqual(
            list(qs.values_list("orden_prioridad", flat=True)),
            [1, 2, 3]
        )



    def test_tradicional_solicitud_insignia_mismo_puesto_repetido_instancia_falla(self):
        """
        Test: Mismo puesto repetido (instancia)

        Given: preferencias_data contiene el MISMO objeto Puesto repetido.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “No puede solicitar el mismo puesto varias veces.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_1, "orden_prioridad": 2},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["No puede solicitar el mismo puesto varias veces."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_mismo_puesto_repetido_id_falla(self):
        """
        Test: Mismo puesto repetido pasando IDs

        Given: preferencias_data contiene el mismo ID de Puesto repetido.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: tras resolver IDs → ValidationError “No puede solicitar el mismo puesto varias veces.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 2},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["No puede solicitar el mismo puesto varias veces."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_mismo_puesto_mezcla_id_y_instancia_falla(self):
        """
        Test: Mismo puesto repetido mezclando ID + instancia

        Given: preferencias_data contiene el mismo Puesto una vez como ID y otra como instancia.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: tras resolver → ValidationError “No puede solicitar el mismo puesto varias veces.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_1, "orden_prioridad": 2},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["No puede solicitar el mismo puesto varias veces."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_puesto_de_otro_acto_falla(self):
        """
        Test: Puesto pertenece a otro acto

        Given: un puesto de insignia que pertenece a un acto distinto.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El puesto '<nombre>' no pertenece a este acto.”
        """
        now = timezone.now()

        otro_acto = Acto.objects.create(
            nombre="Otro acto con papeleta",
            descripcion="Acto distinto",
            fecha=self.fecha_acto + timedelta(days=10),
            tipo_acto=self.tipo_con_papeleta,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            inicio_solicitud=self.inicio_insignias,
            fin_solicitud=self.fin_insignias,
            inicio_solicitud_cirios=self.inicio_cirios,
            fin_solicitud_cirios=self.fin_cirios,
        )

        puesto_de_otro_acto = Puesto.objects.create(
            nombre="Insignia de otro acto",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=otro_acto,
            tipo_puesto=self.tipo_insignia,
        )

        preferencias = [
            {"puesto_solicitado": puesto_de_otro_acto.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [f"El puesto '{puesto_de_otro_acto.nombre}' no pertenece a este acto."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_puesto_no_es_insignia_falla(self):
        """
        Test: Puesto cuyo tipo_puesto.es_insignia = False

        Given: un puesto perteneciente al acto pero marcado como NO insignia.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El puesto '<nombre>' no es una insignia.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_no_insignia.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [f"El puesto '{self.puesto_no_insignia.nombre}' no es una insignia."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_puesto_no_disponible_falla(self):
        """
        Test: Puesto con disponible = False

        Given: un puesto de insignia perteneciente al acto pero marcado como no disponible.
        When: se intenta procesar la solicitud de insignia tradicional.
        Then: ValidationError “El puesto '<nombre>' no está marcado como disponible.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_no_disponible.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [f"El puesto '{self.puesto_no_disponible.nombre}' no está marcado como disponible."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_puesto_exclusivo_junta_hermano_no_junta_falla(self):
        """
        Test: Puesto exclusivo para Junta de Gobierno solicitado por hermano NO Junta

        Given:
            - Puesto con tipo_puesto.solo_junta_gobierno = True.
            - Hermano que NO pertenece al cuerpo JUNTA_GOBIERNO.
        When:
            - Se intenta procesar la solicitud de insignia tradicional.
        Then:
            - ValidationError “El puesto '<nombre>' es exclusivo para Junta de Gobierno.”
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_solo_junta.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            [f"El puesto '{self.puesto_solo_junta.nombre}' es exclusivo para Junta de Gobierno."]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_puesto_no_exclusivo_junta_hermano_no_junta_ok(self):
        """
        Test: Puesto NO exclusivo de Junta solicitado por hermano NO Junta

        Given:
            - Puesto con tipo_puesto.solo_junta_gobierno = False.
            - Hermano que NO pertenece a Junta de Gobierno.
        When:
            - Se procesa la solicitud de insignia tradicional.
        Then:
            - La solicitud es válida y se crea la papeleta y sus preferencias.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_ok)
        self.assertEqual(papeleta.acto, self.acto_tradicional)

        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertTrue(papeleta.es_solicitud_insignia)
        self.assertEqual(papeleta.anio, self.acto_tradicional.fecha.year)
        self.assertEqual(papeleta.fecha_solicitud, now)

        preferencias_db = PreferenciaSolicitud.objects.filter(papeleta=papeleta)
        self.assertEqual(preferencias_db.count(), 1)

        pref = preferencias_db.first()
        self.assertEqual(pref.puesto_solicitado, self.puesto_ok_1)
        self.assertEqual(pref.orden_prioridad, 1)



    def test_tradicional_solicitud_insignia_ya_existe_papeleta_activa_falla(self):
        """
        Test: Ya existe papeleta activa (SOLICITADA)

        Given:
            - Existe una PapeletaSitio previa para el mismo hermano y acto
            con estado SOLICITADA (papeleta "viva").
        When:
            - Se intenta procesar una nueva solicitud de insignia tradicional.
        Then:
            - ValidationError “Ya existe una solicitud activa (en proceso o asignada) para este acto.”
            - No se crea ninguna papeleta ni preferencias nuevas.
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(minutes=5),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            codigo_verificacion="TEST1234"
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["Ya existe una solicitud activa (en proceso o asignada) para este acto."]
        )

        self.assertEqual(PapeletaSitio.objects.count(), 1)
        self.assertFalse(
            PreferenciaSolicitud.objects.exists(),
            "No deben crearse preferencias si la unicidad falla"
        )



    def test_tradicional_solicitud_insignia_ya_existe_papeleta_activa_emitida_falla(self):
        """
        Test: Ya existe papeleta activa (EMITIDA)

        Given: existe una PapeletaSitio previa EMITIDA para el mismo hermano y acto.
        When: se intenta procesar una nueva solicitud de insignia tradicional.
        Then: ValidationError “Ya existe una solicitud activa…”
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(minutes=5),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA,
            es_solicitud_insignia=True,
            codigo_verificacion="TEST1234"
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["Ya existe una solicitud activa (en proceso o asignada) para este acto."]
        )

        self.assertEqual(PapeletaSitio.objects.count(), 1)
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_ya_existe_papeleta_activa_recogida_falla(self):
        """
        Test: Ya existe papeleta activa (RECOGIDA)
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(minutes=5),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.RECOGIDA,
            es_solicitud_insignia=True,
            codigo_verificacion="TEST1234"
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["Ya existe una solicitud activa (en proceso o asignada) para este acto."]
        )

        self.assertEqual(PapeletaSitio.objects.count(), 1)
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_ya_existe_papeleta_activa_leida_falla(self):
        """
        Test: Ya existe papeleta activa (LEIDA)
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(minutes=5),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.LEIDA,
            es_solicitud_insignia=True,
            codigo_verificacion="TEST1234"
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["Ya existe una solicitud activa (en proceso o asignada) para este acto."]
        )

        self.assertEqual(PapeletaSitio.objects.count(), 1)
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_existe_papeleta_anulada_no_bloquea_ok(self):
        """
        Test: Existe papeleta ANULADA (no bloquea)

        Given: existe una PapeletaSitio previa ANULADA para el mismo hermano y acto.
        When: se procesa una nueva solicitud de insignia tradicional.
        Then: OK, se crea una nueva papeleta y sus preferencias.
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(days=1),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
            es_solicitud_insignia=True,
            codigo_verificacion="ANUL1234"
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(PapeletaSitio.objects.count(), 2)
        self.assertEqual(PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(), 1)



    def test_tradicional_solicitud_insignia_existe_papeleta_no_asignada_no_bloquea_ok(self):
        """
        Test: Existe papeleta NO_ASIGNADA (no bloquea)

        Given: existe una PapeletaSitio previa NO_ASIGNADA para el mismo hermano y acto.
        When: se procesa una nueva solicitud de insignia tradicional.
        Then: OK, se crea una nueva papeleta y sus preferencias.
        """
        now = timezone.now()

        PapeletaSitio.objects.create(
            hermano=self.hermano_ok,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=now - timedelta(days=1),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
            es_solicitud_insignia=True,
            codigo_verificacion="NOAS1234"
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(PapeletaSitio.objects.count(), 2)
        self.assertEqual(PreferenciaSolicitud.objects.filter(papeleta=papeleta).count(), 1)



    def test_tradicional_solicitud_insignia_integrity_error_doble_click_falla(self):
        """
        Test: Condición de carrera / doble click

        Given:
            - Durante la creación de la papeleta se produce un IntegrityError
            (simulando doble envío o condición de carrera).
        When:
            - Se procesa la solicitud de insignia tradicional.
        Then:
            - ValidationError con mensaje:
            “Ya existe una solicitud activa tramitada para este hermano.
            Por favor, no haga doble clic en el botón de enviar.”
            - No se persiste ninguna papeleta ni preferencias.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with patch.object(
                SolicitudInsigniaService,
                "_crear_papeleta_base",
                side_effect=IntegrityError("simulated race condition")
            ):
                with self.assertRaises(ValidationError) as ctx:
                    self.service.procesar_solicitud_insignia_tradicional(
                        hermano=self.hermano_ok,
                        acto=self.acto_tradicional,
                        preferencias_data=preferencias,
                    )

        self.assertEqual(
            ctx.exception.messages,
            [
                "Ya existe una solicitud activa tramitada para este hermano. "
                "Por favor, no haga doble clic en el botón de enviar."
            ]
        )

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_falla_antes_de_crear_no_persiste_nada(self):
        """
        Test: Falla antes de crear papeleta (plazo fuera)

        Given:
            - El plazo de solicitud de insignias ya ha finalizado.
        When:
            - Se intenta procesar la solicitud de insignia tradicional.
        Then:
            - ValidationError lanzado.
            - NO se crea ninguna PapeletaSitio ni PreferenciaSolicitud.
        """
        now = self.fin_insignias + timedelta(seconds=1)

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_insignia_tradicional(
                    hermano=self.hermano_ok,
                    acto=self.acto_tradicional,
                    preferencias_data=preferencias,
                )

        self.assertEqual(
            ctx.exception.messages,
            ["El plazo de solicitud de insignias ha finalizado."]
        )

        self.assertFalse(
            PapeletaSitio.objects.exists(),
            "No debe crearse papeleta si la validación falla antes de la creación"
        )
        self.assertFalse(
            PreferenciaSolicitud.objects.exists(),
            "No deben crearse preferencias si la validación falla antes de la creación"
        )



    def test_tradicional_solicitud_insignia_falla_al_guardar_preferencias_rollback_no_queda_papeleta(self):
        """
        Test: Falla después de crear papeleta pero antes de guardar preferencias

        Given: la creación de papeleta se realiza, pero _guardar_preferencias lanza excepción.
        When: se procesa la solicitud de insignia tradicional.
        Then: rollback completo (transacción): no queda PapeletaSitio ni PreferenciaSolicitud.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with patch.object(
                SolicitudInsigniaService,
                "_guardar_preferencias",
                side_effect=Exception("boom")
            ):
                with self.assertRaises(Exception) as ctx:
                    self.service.procesar_solicitud_insignia_tradicional(
                        hermano=self.hermano_ok,
                        acto=self.acto_tradicional,
                        preferencias_data=preferencias,
                    )

        self.assertEqual(str(ctx.exception), "boom")

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_falla_bulk_create_preferencias_rollback_total(self):
        """
        Test: Falla el bulk_create de preferencias → rollback total

        Given: se crea la papeleta, pero el bulk_create de PreferenciaSolicitud falla.
        When: se procesa la solicitud de insignia tradicional.
        Then: rollback completo: no queda PapeletaSitio ni PreferenciaSolicitud.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            with patch.object(
                SolicitudInsigniaService,
                "_guardar_preferencias",
                side_effect=IntegrityError("bulk_create failed")
            ):
                with self.assertRaises(IntegrityError) as ctx:
                    self.service.procesar_solicitud_insignia_tradicional(
                        hermano=self.hermano_ok,
                        acto=self.acto_tradicional,
                        preferencias_data=preferencias,
                    )

        self.assertIn("bulk_create failed", str(ctx.exception))

        self.assertFalse(PapeletaSitio.objects.exists())
        self.assertFalse(PreferenciaSolicitud.objects.exists())



    def test_tradicional_solicitud_insignia_tras_exito_num_preferencias_coincide_ok(self):
        """
        Test: Tras éxito, papeleta.preferencias.count() == len(preferencias_data)

        Given: solicitud válida con N preferencias.
        When: se procesa la solicitud de insignia tradicional.
        Then: se crean exactamente N PreferenciaSolicitud asociadas a la papeleta.
        """
        now = timezone.now()

        puesto_extra = Puesto.objects.create(
            nombre="Insignia Extra",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia,
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 2},
            {"puesto_solicitado": puesto_extra.id, "orden_prioridad": 3},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertEqual(papeleta.preferencias.count(), len(preferencias))



    def test_tradicional_solicitud_insignia_orden_prioridad_guardado_coincide_con_entrada_ok(self):
        """
        Test: Los orden_prioridad guardados coinciden con los de entrada

        Given: solicitud válida con varias preferencias.
        When: se procesa la solicitud de insignia tradicional.
        Then: los orden_prioridad persistidos coinciden con los de entrada (por puesto_id).
        """
        now = timezone.now()

        puesto_extra = Puesto.objects.create(
            nombre="Insignia Extra",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_insignia,
        )

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
            {"puesto_solicitado": self.puesto_ok_2.id, "orden_prioridad": 2},
            {"puesto_solicitado": puesto_extra.id, "orden_prioridad": 3},
        ]

        def _to_puesto_id(val):
            if isinstance(val, Puesto):
                return val.id
            return int(val)

        ordenes_entrada = {
            _to_puesto_id(item["puesto_solicitado"]): item["orden_prioridad"]
            for item in preferencias
        }

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        ordenes_bd = {
            pref.puesto_solicitado.id: pref.orden_prioridad
            for pref in papeleta.preferencias.all()
        }

        self.assertEqual(ordenes_bd, ordenes_entrada)



    def test_tradicional_solicitud_insignia_codigo_verificacion_longitud_8_y_uppercase_ok(self):
        """
        Test: codigo_verificacion longitud 8 y en uppercase

        Given: solicitud válida.
        When: se procesa la solicitud de insignia tradicional.
        Then: codigo_verificacion tiene longitud 8 y está en mayúsculas.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNotNone(papeleta.codigo_verificacion)
        self.assertEqual(len(papeleta.codigo_verificacion), 8)
        self.assertTrue(papeleta.codigo_verificacion.isupper())



    def test_tradicional_solicitud_insignia_es_solicitud_insignia_persistido_en_db_ok(self):
        """
        Test: es_solicitud_insignia guardado en DB (refresh_from_db)

        Given: solicitud válida.
        When: se procesa la solicitud de insignia tradicional.
        Then: es_solicitud_insignia queda persistido en BD (refrescando instancia).
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        papeleta.refresh_from_db()

        self.assertTrue(papeleta.es_solicitud_insignia)



    def test_tradicional_solicitud_insignia_vinculado_a_es_none_siempre_ok(self):
        """
        Test: vinculado_a queda siempre None en solicitudes de insignia

        Given: solicitud válida de insignia tradicional.
        When: se procesa la solicitud.
        Then: vinculado_a es None tanto en memoria como en BD.
        """
        now = timezone.now()

        preferencias = [
            {"puesto_solicitado": self.puesto_ok_1.id, "orden_prioridad": 1},
        ]

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_ok,
                acto=self.acto_tradicional,
                preferencias_data=preferencias,
            )

        self.assertIsNone(papeleta.vinculado_a)

        papeleta.refresh_from_db()
        self.assertIsNone(papeleta.vinculado_a)