import re
from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone
from unittest import mock
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock, patch

from api.models import (
    Acto, Cuota, Hermano, PreferenciaSolicitud, TipoActo, Puesto, TipoPuesto, 
    CuerpoPertenencia, HermanoCuerpo, PapeletaSitio
)

from api.servicios.papeleta_sitio_service import PapeletaSitioService
from api.tests.factories import HermanoFactory
from api.servicios.solicitud_cirio_tradicional import SolicitudCirioTradicionalService

User = get_user_model()

class ProcesarSolicitudCirioServiceTest(TestCase):
    
    def setUp(self):
        # ---------------------------------------------------------------------
        # FECHA BASE
        # ---------------------------------------------------------------------
        self.ahora = timezone.now()

        # ---------------------------------------------------------------------
        # SERVICE
        # ---------------------------------------------------------------------
        self.service = SolicitudCirioTradicionalService()

        # ---------------------------------------------------------------------
        # CUERPOS
        # ---------------------------------------------------------------------
        self.cuerpo_nazarenos = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS
        )
        self.cuerpo_junta = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )
        self.cuerpo_costaleros = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )
        self.cuerpo_juventud = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUVENTUD
        )
        self.cuerpo_priostia = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.PRIOSTÍA
        )
        self.cuerpo_caridad_accion_social = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL
        )

        # ---------------------------------------------------------------------
        # USUARIOS
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

        self.hermano_objetivo = Hermano.objects.create_user(
            dni="11223344Z",
            username="11223344Z",
            password="password",
            nombre="Pepe",
            primer_apellido="Gómez",
            segundo_apellido="López",
            email="pepe@example.com",
            telefono="600111222",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=2000,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1990-01-01",
            direccion="Calle Objetivo",
            codigo_postal="41010",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        # ---------------------------------------------------------------------
        # PERTENENCIAS A CUERPOS
        # ---------------------------------------------------------------------
        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 5
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_objetivo,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 3
        )

        # ---------------------------------------------------------------------
        # TIPO DE ACTO
        # ---------------------------------------------------------------------
        self.tipo_con_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        # ---------------------------------------------------------------------
        # ACTO TRADICIONAL
        # ---------------------------------------------------------------------
        self.fecha_acto = self.ahora + timedelta(days=30)

        self.inicio_insignias = self.ahora - timedelta(days=10)
        self.fin_insignias = self.ahora - timedelta(days=7)

        self.inicio_cirios = self.ahora - timedelta(hours=1)
        self.fin_cirios = self.ahora + timedelta(hours=2)

        self.acto = Acto.objects.create(
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

        # ---------------------------------------------------------------------
        # TIPOS DE PUESTO + PUESTOS
        # ---------------------------------------------------------------------
        self.tipo_cirio = TipoPuesto.objects.create(
            nombre_tipo="Cirio",
            es_insignia=False,
            solo_junta_gobierno=False
        )
        self.tipo_insignia = TipoPuesto.objects.create(
            nombre_tipo="Senatus",
            es_insignia=True,
            solo_junta_gobierno=False
        )
        self.tipo_cirio_solo_junta = TipoPuesto.objects.create(
            nombre_tipo="Cirio Junta",
            es_insignia=False,
            solo_junta_gobierno=True
        )

        self.puesto_cirio_ok = Puesto.objects.create(
            nombre="Cirio Tramo 3",
            numero_maximo_asignaciones=10,
            disponible=True,
            acto=self.acto,
            tipo_puesto=self.tipo_cirio,
            cortejo_cristo=True,
        )

        self.puesto_insignia = Puesto.objects.create(
            nombre="Senatus (Insignia)",
            numero_maximo_asignaciones=1,
            disponible=True,
            acto=self.acto,
            tipo_puesto=self.tipo_insignia,
            cortejo_cristo=True,
        )

        self.puesto_cirio_no_disponible = Puesto.objects.create(
            nombre="Cirio No Disponible",
            numero_maximo_asignaciones=10,
            disponible=False,
            acto=self.acto,
            tipo_puesto=self.tipo_cirio,
            cortejo_cristo=True,
        )

        self.puesto_cirio_solo_junta = Puesto.objects.create(
            nombre="Cirio Junta (exclusivo)",
            numero_maximo_asignaciones=5,
            disponible=True,
            acto=self.acto,
            tipo_puesto=self.tipo_cirio_solo_junta,
            cortejo_cristo=True,
        )

        # ---------------------------------------------------------------------
        # CUOTAS
        # ---------------------------------------------------------------------
        anio_limite = self.ahora.date().year - 1

        Cuota.objects.create(
            hermano=self.hermano,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe="25.00",
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        Cuota.objects.create(
            hermano=self.hermano_objetivo,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe="25.00",
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        # ---------------------------------------------------------------------
        # Helpers de datos frecuentes para tests
        # ---------------------------------------------------------------------
        self.anio_acto = self.acto.fecha.year



    # def test_tradicional_cirio_solicitud_valida_crea_papeleta_solicitada_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) crea papeleta SOLICITADA.

    #     Given: hermano en ALTA, con historial de cuotas hasta año anterior (PAGADA/EXENTO),
    #         sin deuda.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA, con puesto asignado,
    #         es_solicitud_insignia=False y código verificación correcto.
    #     """
    #     now = timezone.now()

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)

    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertFalse(papeleta.es_solicitud_insignia)

    #     self.assertEqual(papeleta.anio, self.acto.fecha.year)
    #     self.assertEqual(papeleta.fecha_solicitud, now)

    #     self.assertIsNotNone(papeleta.codigo_verificacion)
    #     self.assertEqual(len(papeleta.codigo_verificacion), 8)
    #     self.assertTrue(papeleta.codigo_verificacion.isupper())



    # def test_tradicional_cirio_solicitud_valida_sin_cuerpos_pasa_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) sin pertenecer a ningún cuerpo pasa.

    #     Given: hermano en ALTA, con historial de cuotas hasta año anterior (PAGADA/EXENTO),
    #         sin deuda.
    #         hermano NO pertenece a ningún cuerpo (cuerpos_hermano_set vacío).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_hermano_nazarenos_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con hermano perteneciente a NAZARENOS.

    #     Given: hermano en ALTA, con historial de cuotas hasta año anterior (PAGADA/EXENTO),
    #         sin deuda.
    #         hermano pertenece únicamente al cuerpo NAZARENOS (cuerpo permitido).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_nazarenos,
    #         anio_ingreso=now.year - 5,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_hermano_priostia_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con hermano perteneciente a PRIOSTÍA.

    #     Given: hermano en ALTA, con historial de cuotas hasta año anterior (PAGADA/EXENTO),
    #         sin deuda.
    #         hermano pertenece únicamente al cuerpo PRIOSTÍA (cuerpo permitido).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_priostia,
    #         anio_ingreso=now.year - 5,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_hermano_juventud_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con hermano perteneciente a JUVENTUD.

    #     Given: hermano en ALTA, con historial de cuotas hasta año anterior (PAGADA/EXENTO),
    #         sin deuda.
    #         hermano pertenece únicamente al cuerpo JUVENTUD (cuerpo permitido).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_juventud,
    #         anio_ingreso=now.year - 5,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_hermano_caridad_accion_social_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con hermano perteneciente a CARIDAD_ACCION_SOCIAL.

    #     Given: hermano en ALTA, con historial de cuotas hasta año anterior (PAGADA/EXENTO),
    #         sin deuda.
    #         hermano pertenece únicamente al cuerpo CARIDAD_ACCION_SOCIAL (cuerpo permitido).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_caridad_accion_social,
    #         anio_ingreso=now.year - 5,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_hermano_junta_gobierno_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con hermano perteneciente a JUNTA_GOBIERNO.

    #     Given: hermano en ALTA, con historial de cuotas hasta año anterior (PAGADA/EXENTO),
    #         sin deuda.
    #         hermano pertenece únicamente al cuerpo JUNTA_GOBIERNO (cuerpo permitido).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_junta,
    #         anio_ingreso=now.year - 5,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_cuotas_historicas_pagadas_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con todas las cuotas históricas PAGADAS.

    #     Given: hermano en ALTA.
    #         historial completo de cuotas hasta el año anterior, todas en estado PAGADA.
    #         sin ninguna cuota PENDIENTE ni DEVUELTA.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()
    #     anio_limite = now.date().year - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     for anio in range(anio_limite - 3, anio_limite + 1):
    #         Cuota.objects.create(
    #             hermano=self.hermano,
    #             anio=anio,
    #             tipo=Cuota.TipoCuota.ORDINARIA,
    #             descripcion=f"Cuota {anio}",
    #             importe="25.00",
    #             estado=Cuota.EstadoCuota.PAGADA,
    #             metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #         )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_cuotas_historicas_exento_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con todas las cuotas históricas en estado EXENTO.

    #     Given: hermano en ALTA.
    #         historial completo de cuotas hasta el año anterior, todas en estado EXENTO.
    #         sin ninguna cuota PENDIENTE ni DEVUELTA.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()
    #     anio_limite = now.date().year - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     for anio in range(anio_limite - 3, anio_limite + 1):
    #         Cuota.objects.create(
    #             hermano=self.hermano,
    #             anio=anio,
    #             tipo=Cuota.TipoCuota.ORDINARIA,
    #             descripcion=f"Cuota {anio}",
    #             importe="0.00",
    #             estado=Cuota.EstadoCuota.EXENTO,
    #             metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #         )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_solicitud_valida_cuotas_historicas_pagada_y_exento_ok(self):
    #     """
    #     Test: Solicitud válida de cirio (TRADICIONAL) con mezcla de cuotas PAGADA + EXENTO
    #     hasta el año anterior.

    #     Given: hermano en ALTA.
    #         historial completo de cuotas hasta el año anterior con estados mixtos
    #         (PAGADA y EXENTO).
    #         sin ninguna cuota PENDIENTE ni DEVUELTA.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio en estado SOLICITADA sin errores.
    #     """
    #     now = timezone.now()
    #     anio_limite = now.date().year - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite - 2,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite - 2}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PAGADA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite - 1,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite - 1}",
    #         importe="0.00",
    #         estado=Cuota.EstadoCuota.EXENTO,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PAGADA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_cuota_anio_actual_pendiente_no_bloquea_ok(self):
    #     """
    #     Test: Cuotas del año actual en PENDIENTE NO bloquean (regla solo mira <= año anterior).

    #     Given: hermano en ALTA.
    #         existe historial de cuotas hasta año anterior y no hay deuda (PENDIENTE/DEVUELTA)
    #         en años <= año anterior.
    #         además, existe una cuota del AÑO ACTUAL en estado PENDIENTE.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: la solicitud pasa y se crea PapeletaSitio SOLICITADA.
    #     """
    #     now = timezone.now()
    #     anio_actual = now.date().year
    #     anio_limite = anio_actual - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PAGADA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_actual,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_actual}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PENDIENTE,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_cuota_anio_actual_devuelta_no_bloquea_ok(self):
    #     """
    #     Test: Cuota del año actual en DEVUELTA NO bloquea (regla solo mira <= año anterior).

    #     Given: hermano en ALTA.
    #         existe historial de cuotas hasta año anterior y no hay deuda (PENDIENTE/DEVUELTA)
    #         en años <= año anterior.
    #         además, existe una cuota del AÑO ACTUAL en estado DEVUELTA.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido: no insignia, disponible y perteneciente al acto.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: la solicitud pasa y se crea PapeletaSitio SOLICITADA.
    #     """
    #     now = timezone.now()
    #     anio_actual = now.date().year
    #     anio_limite = anio_actual - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PAGADA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_actual,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_actual}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.DEVUELTA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_plazo_inicia_en_ahora_igual_inicio_ok(self):
    #     """
    #     Test: ahora == inicio_solicitud_cirios => OK (igualdad no falla).

    #     Given: acto TRADICIONAL con inicio_solicitud_cirios exactamente igual a now,
    #         y fin_solicitud_cirios posterior.
    #         hermano en ALTA, al corriente hasta año anterior, cuerpo permitido.
    #         puesto válido.
    #     When: se procesa la solicitud con now == inicio.
    #     Then: se crea PapeletaSitio SOLICITADA.
    #     """
    #     now = timezone.now()

    #     self.acto.inicio_solicitud_cirios = now
    #     self.acto.fin_solicitud_cirios = now + timezone.timedelta(hours=2)
    #     self.acto.save(update_fields=["inicio_solicitud_cirios", "fin_solicitud_cirios"])

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.fecha_solicitud, now)



    # def test_tradicional_cirio_plazo_finaliza_en_ahora_igual_fin_ok(self):
    #     """
    #     Test: ahora == fin_solicitud_cirios => OK (igualdad no falla).

    #     Given: acto TRADICIONAL con fin_solicitud_cirios exactamente igual a now,
    #         e inicio_solicitud_cirios anterior.
    #         hermano en ALTA, al corriente hasta año anterior, cuerpo permitido.
    #         puesto válido.
    #     When: se procesa la solicitud con now == fin.
    #     Then: se crea PapeletaSitio SOLICITADA.
    #     """
    #     now = timezone.now()

    #     self.acto.inicio_solicitud_cirios = now - timezone.timedelta(hours=2)
    #     self.acto.fin_solicitud_cirios = now
    #     self.acto.save(update_fields=["inicio_solicitud_cirios", "fin_solicitud_cirios"])

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.fecha_solicitud, now)



    # def test_tradicional_cirio_plazo_con_precision_segundos_y_milisegundos_ok(self):
    #     """
    #     Test: Plazo de cirios válido considerando segundos y microsegundos (edge de timezone).

    #     Given: acto TRADICIONAL con inicio_solicitud_cirios y fin_solicitud_cirios
    #         definidos con segundos y microsegundos.
    #         now cae estrictamente dentro del rango (no igual a bordes),
    #         validando que no hay errores por precisión temporal / timezone.
    #         hermano en ALTA, al corriente hasta año anterior, cuerpo permitido.
    #         puesto válido.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea PapeletaSitio SOLICITADA sin errores.
    #     """
    #     now = timezone.now().replace(microsecond=123456)

    #     inicio = now - timedelta(seconds=30, microseconds=500000)
    #     fin = now + timedelta(seconds=30, microseconds=250000)

    #     self.acto.inicio_solicitud_cirios = inicio
    #     self.acto.fin_solicitud_cirios = fin
    #     self.acto.save(update_fields=["inicio_solicitud_cirios", "fin_solicitud_cirios"])

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.fecha_solicitud, now)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)



    # def test_tradicional_cirio_puesto_no_insignia_y_disponible_ok(self):
    #     """
    #     Test: Puesto con tipo_puesto.es_insignia=False y disponible=True => OK.

    #     Given: hermano en ALTA, al corriente hasta año anterior, cuerpo permitido.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto cuyo tipo NO es insignia y está marcado como disponible.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio SOLICITADA con el puesto asignado.
    #     """
    #     now = timezone.now()

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_puesto_no_exclusivo_junta_hermano_no_junta_ok(self):
    #     """
    #     Test: Puesto con tipo_puesto.solo_junta_gobierno=False => OK aunque el hermano no sea Junta.

    #     Given: hermano en ALTA, al corriente hasta año anterior.
    #         hermano NO pertenece a JUNTA_GOBIERNO (por ejemplo, NAZARENOS).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto cuyo tipo NO es exclusivo de Junta (solo_junta_gobierno=False).
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_nazarenos,
    #         anio_ingreso=now.year - 5,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_puesto_cortejo_cristo_ok(self):
    #     """
    #     Test: Puesto con cortejo_cristo=True (Cristo) => OK.

    #     Given: hermano en ALTA, al corriente hasta año anterior, cuerpo permitido.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido con cortejo_cristo=True (Paso de Cristo).
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_puesto_cortejo_virgen_ok(self):
    #     """
    #     Test: Puesto con cortejo_cristo=False (Virgen/Palio) => OK.

    #     Given: hermano en ALTA, al corriente hasta año anterior, cuerpo permitido.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido con cortejo_cristo=False (Paso de Virgen/Palio).
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio SOLICITADA sin errores.
    #     """
    #     now = timezone.now()

    #     puesto_virgen = Puesto.objects.create(
    #         nombre="Cirio Tramo Virgen",
    #         numero_maximo_asignaciones=10,
    #         disponible=True,
    #         acto=self.acto,
    #         tipo_puesto=self.tipo_cirio,
    #         cortejo_cristo=False,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=puesto_virgen,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, puesto_virgen.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)




    # def test_tradicional_cirio_puesto_con_cupo_unico_sin_ocupacion_previa_ok(self):
    #     """
    #     Test: Puesto con numero_maximo_asignaciones=1 (sin papeletas emitidas previas) => OK.

    #     Given: hermano en ALTA, al corriente hasta año anterior, cuerpo permitido.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido con numero_maximo_asignaciones=1 y SIN papeletas previamente emitidas
    #         (cantidad_ocupada = 0).
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea una PapeletaSitio SOLICITADA correctamente.
    #     """
    #     now = timezone.now()

    #     puesto_cupo_unico = Puesto.objects.create(
    #         nombre="Cirio Cupo Único",
    #         numero_maximo_asignaciones=1,
    #         disponible=True,
    #         acto=self.acto,
    #         tipo_puesto=self.tipo_cirio,
    #         cortejo_cristo=True,
    #     )

    #     self.assertEqual(puesto_cupo_unico.cantidad_ocupada, 0)
    #     self.assertEqual(puesto_cupo_unico.plazas_disponibles, 1)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=puesto_cupo_unico,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()
    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.hermano_id, self.hermano.id)
    #     self.assertEqual(papeleta.acto_id, self.acto.id)
    #     self.assertEqual(papeleta.puesto_id, puesto_cupo_unico.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_con_insignia_previa_solicitada_anula_insignia_y_crea_cirio_ok(self):
    #     """
    #     Test: Existe una papeleta activa de INSIGNIA del mismo acto en estado SOLICITADA =>

    #     - crea la papeleta de cirio en estado SOLICITADA
    #     - anula la insignia previa (pasa a ANULADA)
    #     - devuelve la nueva papeleta
    #     """
    #     now = timezone.now()

    #     insignia_previa = PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now - timezone.timedelta(minutes=5),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         es_solicitud_insignia=True,
    #         codigo_verificacion="INSIG001",
    #         puesto=self.puesto_insignia,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         nueva = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(nueva.id)
    #     nueva.refresh_from_db()

    #     self.assertEqual(nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertFalse(nueva.es_solicitud_insignia)
    #     self.assertEqual(nueva.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertEqual(nueva.hermano_id, self.hermano.id)
    #     self.assertEqual(nueva.acto_id, self.acto.id)

    #     insignia_previa.refresh_from_db()
    #     self.assertEqual(insignia_previa.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

    #     self.assertEqual(
    #         PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
    #         2
    #     )



    # def test_tradicional_cirio_insignia_previa_solicitada_con_puesto_se_anula_y_crea_cirio_ok(self):
    #     """
    #     Test: Insignia previa SOLICITADA con puesto asignado => se anula igualmente.

    #     Given: existe papeleta INSIGNIA (es_solicitud_insignia=True) en estado SOLICITADA
    #         para el mismo acto/hermano, y además tiene puesto asignado.
    #     When: se solicita cirio.
    #     Then: se anula la insignia previa (ANULADA) y se crea/devolver papeleta de cirio SOLICITADA.
    #     """
    #     now = timezone.now()

    #     insignia_previa = PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now - timezone.timedelta(minutes=5),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         es_solicitud_insignia=True,
    #         codigo_verificacion="INSIGPST",
    #         puesto=self.puesto_insignia,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         nueva = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(nueva.id)
    #     nueva.refresh_from_db()
    #     self.assertEqual(nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertFalse(nueva.es_solicitud_insignia)
    #     self.assertEqual(nueva.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertEqual(nueva.hermano_id, self.hermano.id)
    #     self.assertEqual(nueva.acto_id, self.acto.id)

    #     insignia_previa.refresh_from_db()
    #     self.assertEqual(insignia_previa.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)



    # def test_tradicional_cirio_insignia_previa_solicitada_sin_puesto_se_anula_y_crea_cirio_ok(self):
    #     """
    #     Test: Insignia previa SOLICITADA sin puesto asignado => se anula igualmente.

    #     Given: existe papeleta INSIGNIA (es_solicitud_insignia=True) en estado SOLICITADA
    #         para el mismo acto/hermano, y NO tiene puesto asignado.
    #     When: se solicita cirio.
    #     Then: se anula la insignia previa (ANULADA) y se crea/devolver papeleta de cirio SOLICITADA.
    #     """
    #     now = timezone.now()

    #     insignia_previa = PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now - timezone.timedelta(minutes=5),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         es_solicitud_insignia=True,
    #         codigo_verificacion="INSIGNON",
    #         puesto=None,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         nueva = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(nueva.id)
    #     nueva.refresh_from_db()
    #     self.assertEqual(nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertFalse(nueva.es_solicitud_insignia)
    #     self.assertEqual(nueva.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertEqual(nueva.hermano_id, self.hermano.id)
    #     self.assertEqual(nueva.acto_id, self.acto.id)

    #     insignia_previa.refresh_from_db()
    #     self.assertEqual(insignia_previa.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)



    # def test_tradicional_cirio_insignia_solicitada_con_otras_anulada_y_no_asignada_ignora_inactivas_anula_solo_activa_ok(self):
    #     """
    #     Test: Existe insignia SOLICITADA activa y además hay otras papeletas ANULADA/NO_ASIGNADA.
    #     Debe ignorar las inactivas, anular SOLO la insignia SOLICITADA activa y crear cirio.

    #     Given: para el mismo hermano/acto existen:
    #         - papeleta INSIGNIA SOLICITADA (activa) => debe anularse
    #         - otra papeleta ANULADA (inactiva) => se ignora
    #         - otra papeleta NO_ASIGNADA (inactiva) => se ignora
    #     When: se solicita cirio.
    #     Then:
    #         - se crea nueva papeleta de cirio SOLICITADA
    #         - la insignia SOLICITADA pasa a ANULADA
    #         - las otras papeletas permanecen igual
    #     """
    #     now = timezone.now()

    #     anulada_prev = PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now - timezone.timedelta(minutes=30),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
    #         es_solicitud_insignia=True,
    #         codigo_verificacion="ANULAD01",
    #         puesto=self.puesto_insignia,
    #     )

    #     no_asignada_prev = PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now - timezone.timedelta(minutes=20),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
    #         es_solicitud_insignia=True,
    #         codigo_verificacion="NOASIG01",
    #         puesto=self.puesto_insignia,
    #     )

    #     insignia_activa = PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now - timezone.timedelta(minutes=5),
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         es_solicitud_insignia=True,
    #         codigo_verificacion="ACTIVA01",
    #         puesto=self.puesto_insignia,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         nueva = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(nueva.id)
    #     nueva.refresh_from_db()
    #     self.assertEqual(nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertFalse(nueva.es_solicitud_insignia)
    #     self.assertEqual(nueva.puesto_id, self.puesto_cirio_ok.id)

    #     insignia_activa.refresh_from_db()
    #     self.assertEqual(insignia_activa.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

    #     anulada_prev.refresh_from_db()
    #     self.assertEqual(anulada_prev.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

    #     no_asignada_prev.refresh_from_db()
    #     self.assertEqual(no_asignada_prev.estado_papeleta, PapeletaSitio.EstadoPapeleta.NO_ASIGNADA)

    #     self.assertEqual(
    #         PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
    #         4
    #     )



    # def test_tradicional_cirio_papeleta_creada_campos_correctos_ok(self):
    #     """
    #     Test: La papeleta creada tiene los campos esperados.

    #     Then:
    #         - estado_papeleta = SOLICITADA
    #         - anio = acto.fecha.year
    #         - fecha_solicitud ~= ahora (dentro de un delta)
    #         - puesto = el puesto pasado
    #         - es_solicitud_insignia = False
    #         - vinculado_a = None
    #         - codigo_verificacion: longitud 8 y uppercase hex
    #     """
    #     now = timezone.now()
    #     delta = timedelta(seconds=1)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(papeleta.id)

    #     papeleta.refresh_from_db()

    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.anio, self.acto.fecha.year)

    #     self.assertIsNotNone(papeleta.fecha_solicitud)
    #     self.assertTrue(now - delta <= papeleta.fecha_solicitud <= now + delta)

    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)

    #     self.assertIsNone(papeleta.vinculado_a)

    #     self.assertIsNotNone(papeleta.codigo_verificacion)
    #     self.assertEqual(len(papeleta.codigo_verificacion), 8)
    #     self.assertTrue(papeleta.codigo_verificacion.isupper())

    #     self.assertTrue(all(c in "0123456789ABCDEF" for c in papeleta.codigo_verificacion))



    # def test_tradicional_cirio_crea_exactamente_una_papeleta_nueva_ok(self):
    #     """
    #     Test: Se crea exactamente 1 papeleta nueva.

    #     Given: no existe papeleta activa previa para (hermano, acto).
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: el número de PapeletaSitio para (hermano, acto) incrementa en +1.
    #     """
    #     now = timezone.now()

    #     before = PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count()

    #     with patch("django.utils.timezone.now", return_value=now):
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     after = PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count()
    #     self.assertEqual(after, before + 1)



    # def test_tradicional_cirio_no_crea_ni_modifica_preferencias_solicitud_ok(self):
    #     """
    #     Test: No se crean/modifican PreferenciaSolicitud (cirio no usa preferencias).

    #     Given: no hay PreferenciaSolicitud inicialmente.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: el conteo total de PreferenciaSolicitud no cambia.
    #     """
    #     now = timezone.now()

    #     before = PreferenciaSolicitud.objects.count()

    #     with patch("django.utils.timezone.now", return_value=now):
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     after = PreferenciaSolicitud.objects.count()
    #     self.assertEqual(after, before)



    # def test_tradicional_cirio_acto_none_validation_error_tipo_acto(self):
    #     """
    #     Test: acto is None => ValidationError con 'tipo_acto' (o similar).

    #     Given: acto=None
    #     When: se procesa solicitud de cirio tradicional
    #     Then: lanza ValidationError con error asociado a 'tipo_acto'
    #     """
    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=None,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception

    #     self.assertTrue(hasattr(err, "message_dict"))
    #     self.assertIn("tipo_acto", err.message_dict)
    #     self.assertTrue(len(err.message_dict["tipo_acto"]) >= 1)



    # def test_tradicional_cirio_acto_sin_tipo_acto_validation_error(self):
    #     """
    #     Test: acto.tipo_acto_id is None => ValidationError {'tipo_acto': 'El tipo de acto es obligatorio.'}

    #     Given: acto con tipo_acto "borrado" solo en memoria (sin persistir en BD)
    #     When: se procesa la solicitud de cirio tradicional
    #     Then: lanza ValidationError con clave 'tipo_acto' y mensaje esperado
    #     """
    #     self.acto.tipo_acto = None
    #     self.acto.tipo_acto_id = None

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertTrue(hasattr(err, "message_dict"))
    #     self.assertIn("tipo_acto", err.message_dict)
    #     self.assertIn("El tipo de acto es obligatorio.", err.message_dict["tipo_acto"])



    # def test_tradicional_cirio_acto_no_requiere_papeleta_validation_error(self):
    #     """
    #     Test: acto.tipo_acto.requiere_papeleta=False => ValidationError
    #     "El acto 'X' no admite solicitudes de papeleta."

    #     Given: acto con tipo_acto que NO requiere papeleta (sin persistir cambios que disparen clean()).
    #     When: se procesa la solicitud de cirio tradicional
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     tipo_sin_papeleta = TipoActo.objects.create(
    #         tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
    #         requiere_papeleta=False,
    #     )

    #     self.acto.tipo_acto = tipo_sin_papeleta
    #     self.acto.tipo_acto_id = tipo_sin_papeleta.id

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(f"El acto '{self.acto.nombre}' no admite solicitudes de papeleta.", err.messages)



    # def test_tradicional_cirio_acto_modalidad_unificado_validation_error(self):
    #     """
    #     Test: acto.modalidad = UNIFICADO => ValidationError
    #     "Este proceso es exclusivo para actos de modalidad TRADICIONAL."

    #     Given: acto con tipo_acto que requiere papeleta pero modalidad UNIFICADO
    #     When: se procesa la solicitud de cirio tradicional
    #     Then: lanza ValidationError con el mensaje esperado
    #     """
    #     self.acto.modalidad = Acto.ModalidadReparto.UNIFICADO

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Este proceso es exclusivo para actos de modalidad TRADICIONAL.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_acto_modalidad_none_validation_error(self):
    #     """
    #     Test: acto.modalidad = None => ValidationError
    #     "Este proceso es exclusivo para actos de modalidad TRADICIONAL."

    #     Given: acto con tipo_acto que requiere papeleta pero modalidad = None
    #     When: se procesa la solicitud de cirio tradicional
    #     Then: lanza ValidationError indicando que el proceso es exclusivo de modalidad TRADICIONAL
    #     """
    #     self.acto.modalidad = None

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Este proceso es exclusivo para actos de modalidad TRADICIONAL.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_inicio_solicitud_cirios_none_validation_error(self):
    #     """
    #     Test: inicio_solicitud_cirios is None => ValidationError
    #     "El plazo de cirios no está configurado en el acto."

    #     Given: acto TRADICIONAL que requiere papeleta,
    #         pero inicio_solicitud_cirios = None (plazo de cirios mal configurado).
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     self.acto.inicio_solicitud_cirios = None

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "El plazo de cirios no está configurado en el acto.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_fin_solicitud_cirios_none_validation_error(self):
    #     """
    #     Test: fin_solicitud_cirios is None => ValidationError
    #     "El plazo de cirios no está configurado en el acto."

    #     Given: acto TRADICIONAL que requiere papeleta,
    #         pero fin_solicitud_cirios = None (plazo de cirios mal configurado).
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     self.acto.fin_solicitud_cirios = None

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "El plazo de cirios no está configurado en el acto.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_inicio_y_fin_solicitud_cirios_none_validation_error(self):
    #     """
    #     Test: inicio_solicitud_cirios is None y fin_solicitud_cirios is None => ValidationError
    #     "El plazo de cirios no está configurado en el acto."

    #     Given: acto TRADICIONAL que requiere papeleta,
    #         pero inicio_solicitud_cirios = None y fin_solicitud_cirios = None.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     self.acto.inicio_solicitud_cirios = None
    #     self.acto.fin_solicitud_cirios = None

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "El plazo de cirios no está configurado en el acto.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_ahora_antes_inicio_solicitud_cirios_validation_error(self):
    #     """
    #     Test: ahora < inicio_solicitud_cirios => ValidationError
    #     "El plazo de solicitud de cirios aún no ha comenzado."

    #     Given: acto TRADICIONAL con inicio_solicitud_cirios en el futuro y fin posterior.
    #     When: se procesa la solicitud con now < inicio.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     now = timezone.now()

    #     self.acto.inicio_solicitud_cirios = now + timedelta(minutes=10)
    #     self.acto.fin_solicitud_cirios = now + timedelta(hours=1)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "El plazo de solicitud de cirios aún no ha comenzado.",
    #         err.messages,
    #     )


    
    # def test_tradicional_cirio_ahora_despues_fin_solicitud_cirios_validation_error(self):
    #     """
    #     Test: ahora > fin_solicitud_cirios => ValidationError
    #     "El plazo de solicitud de cirios ha finalizado."

    #     Given: acto TRADICIONAL con fin_solicitud_cirios en el pasado.
    #     When: se procesa la solicitud con now > fin.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     now = timezone.now()

    #     self.acto.inicio_solicitud_cirios = now - timedelta(hours=2)
    #     self.acto.fin_solicitud_cirios = now - timedelta(minutes=1)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "El plazo de solicitud de cirios ha finalizado.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_plazo_cirios_configuracion_absurda_inicio_mayor_que_fin_muestra_que_no_se_valida_orden_en_service(self):
    #     """
    #     Test: inicio_solicitud_cirios > fin_solicitud_cirios (configuración absurda).

    #     Objetivo del test:
    #     - Detectar que el servicio NO valida el orden inicio/fin en _validar_plazo_vigente.
    #     - El error que salga dependerá de 'ahora' (porque compara ahora<inicio y ahora>fin),
    #         y esto sirve para descubrir fixtures/BD corruptos si entran por debajo del clean().

    #     Given: acto TRADICIONAL con inicio_cirios posterior a fin_cirios (inicio > fin).
    #     When: se procesa la solicitud en un 'now' controlado.
    #     Then: lanza ValidationError, y el mensaje será uno de:
    #         - "El plazo de solicitud de cirios aún no ha comenzado." (si now < inicio)
    #         - "El plazo de solicitud de cirios ha finalizado." (si now > fin)
    #     """
    #     now = timezone.now()

    #     self.acto.inicio_solicitud_cirios = now + timedelta(hours=2)
    #     self.acto.fin_solicitud_cirios = now - timedelta(hours=2)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     msg = ctx.exception.messages[0]
    #     self.assertIn(
    #         msg,
    #         [
    #             "El plazo de solicitud de cirios aún no ha comenzado.",
    #             "El plazo de solicitud de cirios ha finalizado.",
    #         ],
    #     )



    # def test_tradicional_cirio_hermano_estado_baja_validation_error(self):
    #     """
    #     Test: hermano.estado_hermano = BAJA => ValidationError
    #     "Solo los hermanos en estado ALTA pueden solicitar papeleta."

    #     Given: hermano en estado BAJA
    #     When: se procesa la solicitud de cirio tradicional
    #     Then: lanza ValidationError con el mensaje esperado
    #     """
    #     self.hermano.estado_hermano = self.hermano.EstadoHermano.BAJA

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Solo los hermanos en estado ALTA pueden solicitar papeleta.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_hermano_estado_pendiente_ingreso_validation_error(self):
    #     """
    #     Test: hermano.estado_hermano = PENDIENTE_INGRESO => ValidationError
    #     "Solo los hermanos en estado ALTA pueden solicitar papeleta."

    #     Given: hermano en estado PENDIENTE_INGRESO
    #     When: se procesa la solicitud de cirio tradicional
    #     Then: lanza ValidationError con el mismo mensaje que para BAJA
    #     """
    #     self.hermano.estado_hermano = self.hermano.EstadoHermano.PENDIENTE_INGRESO

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Solo los hermanos en estado ALTA pueden solicitar papeleta.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_hermano_estado_none_validation_error(self):
    #     """
    #     Test: hermano.estado_hermano = None => ValidationError
    #     "Solo los hermanos en estado ALTA pueden solicitar papeleta."

    #     Given: hermano con estado_hermano = None
    #         (cualquier valor distinto de ALTA debe fallar por la comparación != ALTA)
    #     When: se procesa la solicitud de cirio tradicional
    #     Then: lanza ValidationError con el mismo mensaje contractual
    #     """
    #     self.hermano.estado_hermano = None

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Solo los hermanos en estado ALTA pueden solicitar papeleta.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_cuota_pendiente_anio_anterior_validation_error(self):
    #     """
    #     Test: Existe cuota <= año anterior en estado PENDIENTE => ValidationError con año exacto.

    #     Given: hermano en ALTA.
    #         existe al menos una cuota del año anterior (o anterior) en estado PENDIENTE.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError indicando exactamente el año de la cuota pendiente.
    #     """
    #     now = timezone.now()
    #     anio_limite = now.date().year - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     cuota_pendiente = Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PENDIENTE,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"Consta una cuota pendiente o devuelta del año {cuota_pendiente.anio}.",
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_cuota_devuelta_anio_anterior_validation_error(self):
    #     """
    #     Test: Existe cuota <= año anterior en estado DEVUELTA => ValidationError con año exacto.

    #     Given: hermano en ALTA.
    #         existe al menos una cuota del año anterior (o anterior) en estado DEVUELTA.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError indicando exactamente el año de la cuota devuelta.
    #     """
    #     now = timezone.now()
    #     anio_limite = now.date().year - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     cuota_devuelta = Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.DEVUELTA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"Consta una cuota pendiente o devuelta del año {cuota_devuelta.anio}.",
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_varias_deudas_reporta_anio_mas_antiguo_validation_error(self):
    #     """
    #     Test: existen varias deudas <= año anterior => se reporta el año más antiguo
    #     según order_by('anio').first().

    #     Given: hermano en ALTA con varias cuotas <= año anterior en estado PENDIENTE/DEVUELTA
    #         con distintos años.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError cuyo mensaje contiene el año más antiguo.
    #     """
    #     now = timezone.now()
    #     anio_limite = now.date().year - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     cuota_mas_antigua = Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite - 3,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite - 3}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.DEVUELTA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite - 1,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite - 1}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PENDIENTE,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_limite,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_limite}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PENDIENTE,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"Consta una cuota pendiente o devuelta del año {cuota_mas_antigua.anio}.",
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_sin_cuotas_hasta_anio_anterior_validation_error(self):
    #     """
    #     Test: No existe ninguna cuota con anio <= año_anterior =>
    #     ValidationError "No constan cuotas registradas hasta el año YYYY..."

    #     Given: hermano en ALTA.
    #         solo existen (o no existen) cuotas del año ACTUAL,
    #         y NO hay ninguna cuota con anio <= año_anterior.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado y el año exacto.
    #     """
    #     now = timezone.now()
    #     anio_actual = now.date().year
    #     anio_limite = anio_actual - 1

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_actual,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_actual}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PAGADA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"No constan cuotas registradas hasta el año {anio_limite}.",
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_caso_frontera_enero_anio_limite_correcto_en_mensaje(self):
    #     """
    #     Test frontera: estamos en enero, cambia el año_actual y anio_limite = anio_actual - 1.

    #     Given: now forzado a enero (10/01/2026).
    #         Plazo de cirios forzado para que now esté dentro (y no bloquee antes).
    #         No existen cuotas con anio <= anio_limite.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError cuyo mensaje usa exactamente anio_limite (= 2025).
    #     """
    #     now = timezone.make_aware(datetime(2026, 1, 10, 10, 0, 0))
    #     anio_actual = now.date().year
    #     anio_limite = anio_actual - 1

    #     self.acto.inicio_solicitud_cirios = now - timedelta(hours=1)
    #     self.acto.fin_solicitud_cirios = now + timedelta(hours=1)

    #     Cuota.objects.filter(hermano=self.hermano).delete()
    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_actual,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_actual}",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PAGADA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"No constan cuotas registradas hasta el año {anio_limite}.",
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_solo_cuotas_anio_actual_sin_historial_hasta_anio_anterior_falla(self):
    #     """
    #     Test: hay cuotas, pero todas son del año actual (anio > anio_limite) =>
    #     se considera SIN historial hasta año anterior => debe fallar.

    #     Given: now controlado y plazo de cirios vigente.
    #         hermano en ALTA.
    #         existen cuotas SOLO del año actual.
    #         no existe ninguna cuota con anio <= anio_limite.
    #     When: se procesa solicitud de cirio tradicional.
    #     Then: lanza ValidationError "No constan cuotas registradas hasta el año {anio_limite}..."
    #     """
    #     now = timezone.now()
    #     anio_actual = now.date().year
    #     anio_limite = anio_actual - 1

    #     self.acto.inicio_solicitud_cirios = now - timedelta(hours=1)
    #     self.acto.fin_solicitud_cirios = now + timedelta(hours=1)

    #     Cuota.objects.filter(hermano=self.hermano).delete()

    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_actual,
    #         tipo=Cuota.TipoCuota.ORDINARIA,
    #         descripcion=f"Cuota {anio_actual} (1)",
    #         importe="25.00",
    #         estado=Cuota.EstadoCuota.PAGADA,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )
    #     Cuota.objects.create(
    #         hermano=self.hermano,
    #         anio=anio_actual,
    #         tipo=Cuota.TipoCuota.EXTRAORDINARIA,
    #         descripcion=f"Cuota {anio_actual} (2)",
    #         importe="10.00",
    #         estado=Cuota.EstadoCuota.EXENTO,
    #         metodo_pago=Cuota.MetodoPago.DOMICILIACION,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"No constan cuotas registradas hasta el año {anio_limite}.",
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_hermano_solo_costaleros_falla_por_cuerpo_no_apto(self):
    #     """
    #     Test: Hermano pertenece SOLO a COSTALEROS => falla (no está en cuerpos permitidos).

    #     Given: hermano en ALTA, al corriente hasta año anterior.
    #         pertenencia a cuerpos = {COSTALEROS} exclusivamente.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: ValidationError indicando que COSTALEROS no permite solicitar la papeleta.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_costaleros,
    #         anio_ingreso=now.year - 2,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta:",
    #         err.messages[0],
    #     )
    #     self.assertIn(CuerpoPertenencia.NombreCuerpo.COSTALEROS.value, err.messages[0])



    # def test_tradicional_cirio_hermano_solo_acolitos_falla_por_cuerpo_no_apto(self):
    #     """
    #     Test: Hermano pertenece SOLO a ACOLITOS => falla (no está en cuerpos permitidos).

    #     Given: hermano en ALTA, al corriente hasta año anterior.
    #         pertenencia a cuerpos = {ACOLITOS} exclusivamente.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: ValidationError indicando que ACOLITOS no permite solicitar la papeleta.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_priostia,
    #         anio_ingreso=now.year - 1,
    #     )

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()

    #     cuerpo_acolitos = CuerpoPertenencia.objects.create(
    #         nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.ACOLITOS
    #     )
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=cuerpo_acolitos,
    #         anio_ingreso=now.year - 2,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta:",
    #         err.messages[0],
    #     )
    #     self.assertIn(CuerpoPertenencia.NombreCuerpo.ACOLITOS.value, err.messages[0])



    # def test_tradicional_cirio_hermano_solo_diputados_falla_por_cuerpo_no_apto(self):
    #     """
    #     Test: Hermano pertenece SOLO a DIPUTADOS => falla (no está en cuerpos permitidos).

    #     Given: hermano en ALTA, al corriente hasta año anterior.
    #         pertenencia a cuerpos = {DIPUTADOS} exclusivamente.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: ValidationError indicando que DIPUTADOS no permite solicitar la papeleta.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()

    #     cuerpo_diputados = CuerpoPertenencia.objects.create(
    #         nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.DIPUTADOS
    #     )

    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=cuerpo_diputados,
    #         anio_ingreso=now.year - 2,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta:",
    #         err.messages[0],
    #     )
    #     self.assertIn(CuerpoPertenencia.NombreCuerpo.DIPUTADOS.value, err.messages[0])



    # def test_tradicional_cirio_hermano_nazarenos_y_costaleros_falla_por_cuerpo_no_apto(self):
    #     """
    #     Test: Hermano pertenece a una mezcla NAZARENOS + COSTALEROS => falla (por COSTALEROS).

    #     Given: hermano en ALTA, al corriente hasta año anterior.
    #         pertenencia a cuerpos = {NAZARENOS, COSTALEROS}.
    #         NAZARENOS es permitido, COSTALEROS NO.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: ValidationError indicando que COSTALEROS no permite solicitar la papeleta.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()

    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_nazarenos,
    #         anio_ingreso=now.year - 5,
    #     )
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_costaleros,
    #         anio_ingreso=now.year - 3,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta:",
    #         err.messages[0],
    #     )
    #     self.assertIn(
    #         CuerpoPertenencia.NombreCuerpo.COSTALEROS.value,
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_hermano_junta_y_sanitarios_falla_por_cuerpo_no_apto(self):
    #     """
    #     Test: Hermano pertenece a JUNTA_GOBIERNO + SANITARIOS => falla (por SANITARIOS).

    #     Given: hermano en ALTA, al corriente hasta año anterior.
    #         pertenencia a cuerpos = {JUNTA_GOBIERNO, SANITARIOS}.
    #         JUNTA_GOBIERNO es permitido, SANITARIOS NO.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: ValidationError indicando que SANITARIOS no permite solicitar la papeleta.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()

    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_junta,
    #         anio_ingreso=now.year - 4,
    #     )

    #     cuerpo_sanitarios = CuerpoPertenencia.objects.create(
    #         nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.SANITARIOS
    #     )
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=cuerpo_sanitarios,
    #         anio_ingreso=now.year - 2,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta:",
    #         err.messages[0],
    #     )
    #     self.assertIn(CuerpoPertenencia.NombreCuerpo.SANITARIOS.value, err.messages[0])



    # def test_tradicional_cirio_cuerpos_no_aptos_mensaje_ordenado_determinista(self):
    #     """
    #     Test: Mensaje lista cuerpos no aptos ordenados (sorted) => orden determinista.

    #     Given: hermano con varios cuerpos NO permitidos en un orden "aleatorio".
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: ValidationError cuyo mensaje lista los cuerpos no aptos en orden alfabético (sorted).
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()

    #     cuerpo_sanitarios = CuerpoPertenencia.objects.create(
    #         nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.SANITARIOS
    #     )
    #     cuerpo_costaleros = self.cuerpo_costaleros
    #     cuerpo_diputados = CuerpoPertenencia.objects.create(
    #         nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.DIPUTADOS
    #     )

    #     HermanoCuerpo.objects.create(hermano=self.hermano, cuerpo=cuerpo_sanitarios, anio_ingreso=now.year - 1)
    #     HermanoCuerpo.objects.create(hermano=self.hermano, cuerpo=cuerpo_costaleros, anio_ingreso=now.year - 2)
    #     HermanoCuerpo.objects.create(hermano=self.hermano, cuerpo=cuerpo_diputados, anio_ingreso=now.year - 3)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     msg = ctx.exception.messages[0]

    #     prefijo = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: "
    #     self.assertTrue(msg.startswith(prefijo))

    #     esperados_ordenados = sorted([
    #         CuerpoPertenencia.NombreCuerpo.SANITARIOS.value,
    #         CuerpoPertenencia.NombreCuerpo.COSTALEROS.value,
    #         CuerpoPertenencia.NombreCuerpo.DIPUTADOS.value,
    #     ])

    #     self.assertEqual(
    #         msg,
    #         prefijo + ", ".join(esperados_ordenados)
    #     )



    # def test_tradicional_cirio_data_mismatch_cuerpo_priostia_con_tilde_falla(self):
    #     """
    #     Test: Caso típico de data mismatch.
    #     cuerpos_hermano_set viene como strings (values_list), y si uno viene con tilde/valor distinto
    #     (ej. "PRIOSTÍA" vs "PRIOSTIA"), no coincide con los .value permitidos => debe fallar.

    #     Objetivo: detectar inconsistencias de datos/choices/carga (fixtures antiguas, migraciones, etc.)
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()

    #     cuerpo_priostia_mal = CuerpoPertenencia.objects.create(
    #         nombre_cuerpo="PRIOSTÍA"
    #     )

    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=cuerpo_priostia_mal,
    #         anio_ingreso=now.year - 2,
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     msg = ctx.exception.messages[0]
    #     self.assertIn(
    #         "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta:",
    #         msg,
    #     )
    #     self.assertIn("PRIOSTÍA", msg)



    # def test_tradicional_cirio_puesto_none_validation_error(self):
    #     """
    #     Test: puesto is None => ValidationError
    #     "Debe seleccionar un puesto válido."

    #     Given: acto TRADICIONAL con plazo de cirios vigente,
    #         hermano en ALTA y al corriente.
    #         puesto = None.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=None,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Debe seleccionar un puesto válido.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_puesto_no_pertenece_al_acto_validation_error(self):
    #     """
    #     Test: puesto.acto_id != acto.id => ValidationError
    #     "El puesto no pertenece a este acto."

    #     Given: existe un puesto válido pero asociado a OTRO acto distinto.
    #         hermano en ALTA, al corriente.
    #         acto TRADICIONAL con plazo de cirios vigente.
    #     When: se procesa la solicitud de cirio tradicional usando un puesto de otro acto.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     otro_acto = Acto.objects.create(
    #         nombre="Otro acto distinto",
    #         descripcion="Acto diferente",
    #         fecha=self.acto.fecha,
    #         tipo_acto=self.tipo_con_papeleta,
    #         modalidad=Acto.ModalidadReparto.TRADICIONAL,
    #         inicio_solicitud=self.acto.inicio_solicitud,
    #         fin_solicitud=self.acto.fin_solicitud,
    #         inicio_solicitud_cirios=self.acto.inicio_solicitud_cirios,
    #         fin_solicitud_cirios=self.acto.fin_solicitud_cirios,
    #     )

    #     puesto_otro_acto = Puesto.objects.create(
    #         nombre="Cirio de otro acto",
    #         numero_maximo_asignaciones=5,
    #         disponible=True,
    #         acto=otro_acto,
    #         tipo_puesto=self.tipo_cirio,
    #         cortejo_cristo=True,
    #     )

    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=puesto_otro_acto,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         "El puesto no pertenece a este acto.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_puesto_es_insignia_validation_error(self):
    #     """
    #     Test: puesto.tipo_puesto.es_insignia = True =>
    #     ValidationError "El puesto 'X' es una Insignia. No puede solicitarse en este formulario."

    #     Given: acto TRADICIONAL con plazo de cirios vigente.
    #         hermano en ALTA y al corriente.
    #         puesto cuyo tipo_puesto está marcado como es_insignia=True.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_insignia,
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"El puesto '{self.puesto_insignia.nombre}' es una Insignia. No puede solicitarse en este formulario.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_puesto_no_disponible_validation_error(self):
    #     """
    #     Test: puesto.disponible = False =>
    #     ValidationError "El puesto 'X' no está marcado como disponible."

    #     Given: acto TRADICIONAL con plazo de cirios vigente.
    #         hermano en ALTA y al corriente.
    #         puesto existente del acto pero marcado como disponible=False.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     with self.assertRaises(DjangoValidationError) as ctx:
    #         self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_no_disponible, 
    #         )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"El puesto '{self.puesto_cirio_no_disponible.nombre}' no está marcado como disponible.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_puesto_solo_junta_y_hermano_no_junta_validation_error(self):
    #     """
    #     Test: puesto.tipo_puesto.solo_junta_gobierno = True y el hermano NO pertenece a JUNTA_GOBIERNO
    #     => ValidationError "El puesto 'X' es exclusivo para Junta de Gobierno."

    #     Given: acto TRADICIONAL con plazo de cirios vigente.
    #         puesto cuyo tipo_puesto es solo_junta_gobierno=True.
    #         hermano en ALTA, al corriente, pero SIN cuerpo JUNTA_GOBIERNO.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: lanza ValidationError con el mensaje esperado.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).exclude(
    #         cuerpo=self.cuerpo_nazarenos
    #     ).delete()

    #     cuerpos = set(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True))
    #     self.assertNotIn(CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value, cuerpos)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_solo_junta,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         f"El puesto '{self.puesto_cirio_solo_junta.nombre}' es exclusivo para Junta de Gobierno.",
    #         err.messages[0],
    #     )



    # def test_tradicional_cirio_puesto_solo_junta_y_hermano_es_junta_ok(self):
    #     """
    #     Test (contraste positivo): puesto.tipo_puesto.solo_junta_gobierno = True
    #     y el hermano SÍ pertenece a JUNTA_GOBIERNO => debe pasar.

    #     Given: acto TRADICIONAL con plazo de cirios vigente.
    #         puesto exclusivo de Junta de Gobierno.
    #         hermano en ALTA, al corriente y con cuerpo JUNTA_GOBIERNO.
    #     When: se procesa la solicitud de cirio tradicional.
    #     Then: se crea papeleta SOLICITADA correctamente.
    #     """
    #     now = timezone.now()

    #     HermanoCuerpo.objects.filter(hermano=self.hermano).delete()
    #     HermanoCuerpo.objects.create(
    #         hermano=self.hermano,
    #         cuerpo=self.cuerpo_junta,
    #         anio_ingreso=now.year - 3,
    #     )

    #     cuerpos = set(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True))
    #     self.assertIn(CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value, cuerpos)

    #     with patch("django.utils.timezone.now", return_value=now):
    #         papeleta = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_solo_junta,
    #         )

    #     self.assertIsNotNone(papeleta.id)
    #     papeleta.refresh_from_db()

    #     self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(papeleta.puesto_id, self.puesto_cirio_solo_junta.id)
    #     self.assertFalse(papeleta.es_solicitud_insignia)



    # def test_tradicional_cirio_con_insignia_activa_emitida_falla(self):
    #     """
    #     Test: Existe papeleta activa es_solicitud_insignia=True y estado=EMITIDA =>
    #     ValidationError "Ya tienes asignada una Insignia..."

    #     Given: hermano tiene una papeleta de insignia activa (EMITIDA) para el mismo acto.
    #     When: intenta solicitar cirio.
    #     Then: falla con el mensaje esperado.
    #     """
    #     now = timezone.now()

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA,
    #         es_solicitud_insignia=True,
    #         puesto=self.puesto_insignia,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_con_insignia_activa_recogida_falla(self):
    #     """
    #     Test: Existe papeleta activa es_solicitud_insignia=True y estado=RECOGIDA =>
    #     ValidationError "Ya tienes asignada una Insignia..."

    #     Given: hermano tiene una papeleta de insignia activa (RECOGIDA) para el mismo acto.
    #     When: intenta solicitar cirio.
    #     Then: falla con el mensaje esperado.
    #     """
    #     now = timezone.now()

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.RECOGIDA,
    #         es_solicitud_insignia=True,
    #         puesto=self.puesto_insignia,
    #         codigo_verificacion="ABCDEF34",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_con_insignia_activa_leida_falla(self):
    #     """
    #     Test: Existe papeleta activa es_solicitud_insignia=True y estado=LEIDA =>
    #     ValidationError "Ya tienes asignada una Insignia..."

    #     Given: hermano tiene una papeleta de insignia activa (LEIDA) para el mismo acto.
    #     When: intenta solicitar cirio.
    #     Then: falla con el mensaje esperado.
    #     """
    #     now = timezone.now()

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.LEIDA,
    #         es_solicitud_insignia=True,
    #         puesto=self.puesto_insignia,
    #         codigo_verificacion="ABCDEF56",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     err = ctx.exception
    #     self.assertIn(
    #         "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente.",
    #         err.messages,
    #     )



    # def test_tradicional_cirio_con_papeleta_activa_no_insignia_mismo_tipo_falla_mensaje_especifico(self):
    #     """
    #     Test: existe papeleta activa es_solicitud_insignia=False y MISMO tipo_puesto que el nuevo =>
    #     falla con: "Ya tienes una solicitud activa para 'tipo'."

    #     Se prueba para estados activos: SOLICITADA/EMITIDA/RECOGIDA/LEIDA.
    #     """
    #     now = timezone.now()

    #     estados_activos = [
    #         PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         PapeletaSitio.EstadoPapeleta.EMITIDA,
    #         PapeletaSitio.EstadoPapeleta.RECOGIDA,
    #         PapeletaSitio.EstadoPapeleta.LEIDA,
    #     ]

    #     for estado in estados_activos:
    #         with self.subTest(estado=estado):
    #             PapeletaSitio.objects.all().delete()

    #             PapeletaSitio.objects.create(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 anio=self.acto.fecha.year,
    #                 fecha_solicitud=now,
    #                 estado_papeleta=estado,
    #                 es_solicitud_insignia=False,
    #                 puesto=self.puesto_cirio_ok,
    #                 codigo_verificacion="ABCDEF12",
    #             )

    #             with patch("django.utils.timezone.now", return_value=now):
    #                 with self.assertRaises(DjangoValidationError) as ctx:
    #                     self.service.procesar_solicitud_cirio_tradicional(
    #                         hermano=self.hermano,
    #                         acto=self.acto,
    #                         puesto=self.puesto_cirio_ok,
    #                     )

    #             msg = ctx.exception.messages[0]
    #             self.assertEqual(
    #                 msg,
    #                 f"Ya tienes una solicitud activa para '{self.tipo_cirio.nombre_tipo}'."
    #             )



    # def test_tradicional_cirio_con_papeleta_activa_no_insignia_tipo_distinto_falla_mensaje_generico(self):
    #     """
    #     Test: existe papeleta activa es_solicitud_insignia=False y tipo_puesto DISTINTO al nuevo =>
    #     falla con: "Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez)."

    #     Se prueba para estados activos: SOLICITADA/EMITIDA/RECOGIDA/LEIDA.
    #     """
    #     now = timezone.now()

    #     tipo_penitente = TipoPuesto.objects.create(
    #         nombre_tipo="Penitente",
    #         es_insignia=False,
    #         solo_junta_gobierno=False,
    #     )
    #     puesto_penitente = Puesto.objects.create(
    #         nombre="Cruz de penitente",
    #         numero_maximo_asignaciones=50,
    #         disponible=True,
    #         acto=self.acto,
    #         tipo_puesto=tipo_penitente,
    #         cortejo_cristo=True,
    #     )

    #     estados_activos = [
    #         PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         PapeletaSitio.EstadoPapeleta.EMITIDA,
    #         PapeletaSitio.EstadoPapeleta.RECOGIDA,
    #         PapeletaSitio.EstadoPapeleta.LEIDA,
    #     ]

    #     for estado in estados_activos:
    #         with self.subTest(estado=estado):
    #             PapeletaSitio.objects.all().delete()

    #             PapeletaSitio.objects.create(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 anio=self.acto.fecha.year,
    #                 fecha_solicitud=now,
    #                 estado_papeleta=estado,
    #                 es_solicitud_insignia=False,
    #                 puesto=puesto_penitente,
    #                 codigo_verificacion="ABCDEF34",
    #             )

    #             with patch("django.utils.timezone.now", return_value=now):
    #                 with self.assertRaises(DjangoValidationError) as ctx:
    #                     self.service.procesar_solicitud_cirio_tradicional(
    #                         hermano=self.hermano,
    #                         acto=self.acto,
    #                         puesto=self.puesto_cirio_ok,
    #                     )

    #             msg = ctx.exception.messages[0]
    #             self.assertEqual(
    #                 msg,
    #                 "Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez)."
    #             )



    # def test_tradicional_cirio_mismo_tipo_puesto_distinto_falla_ya_tienes_solicitud_activa_para_tipo(self):
    #     """
    #     Caso "mismo tipo": ya existe papeleta activa con puesto tipo "Cirio",
    #     y se intenta pedir OTRO puesto distinto pero también tipo "Cirio" =>
    #     falla: "Ya tienes una solicitud activa para 'Cirio'."
    #     """
    #     now = timezone.now()

    #     otro_puesto_cirio = Puesto.objects.create(
    #         nombre="Cirio Tramo 7",
    #         numero_maximo_asignaciones=10,
    #         disponible=True,
    #         acto=self.acto,
    #         tipo_puesto=self.tipo_cirio,
    #         cortejo_cristo=True,
    #     )

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         es_solicitud_insignia=False,
    #         puesto=self.puesto_cirio_ok,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=otro_puesto_cirio,
    #             )

    #     msg = ctx.exception.messages[0]
    #     self.assertEqual(
    #         msg,
    #         f"Ya tienes una solicitud activa para '{self.tipo_cirio.nombre_tipo}'."
    #     )



    # def test_tradicional_cirio_tipo_distinto_existente_penitente_falla_mensaje_generico(self):
    #     """
    #     Caso "tipo distinto": existe papeleta activa con tipo 'Penitente'
    #     y se intenta solicitar 'Cirio' ⇒ falla con:
    #     "Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez)."
    #     """
    #     now = timezone.now()

    #     tipo_penitente = TipoPuesto.objects.create(
    #         nombre_tipo="Penitente",
    #         es_insignia=False,
    #         solo_junta_gobierno=False,
    #     )
    #     puesto_penitente = Puesto.objects.create(
    #         nombre="Cruz de penitente",
    #         numero_maximo_asignaciones=30,
    #         disponible=True,
    #         acto=self.acto,
    #         tipo_puesto=tipo_penitente,
    #         cortejo_cristo=True,
    #     )

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
    #         es_solicitud_insignia=False,
    #         puesto=puesto_penitente,
    #         codigo_verificacion="ABCDEF99",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         with self.assertRaises(DjangoValidationError) as ctx:
    #             self.service.procesar_solicitud_cirio_tradicional(
    #                 hermano=self.hermano,
    #                 acto=self.acto,
    #                 puesto=self.puesto_cirio_ok,
    #             )

    #     msg = ctx.exception.messages[0]
    #     self.assertEqual(
    #         msg,
    #         "Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez)."
    #     )



    # def test_tradicional_cirio_con_papeleta_prev_anu_lada_no_bloquea_y_permite_crear_nueva(self):
    #     """
    #     Test: Existe papeleta previa ANULADA (cirio) => NO bloquea => permite crear nueva.

    #     Given: hermano tiene una papeleta ANULADA para el mismo acto (es_solicitud_insignia=False).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido.
    #     When: se procesa una nueva solicitud de cirio tradicional.
    #     Then: se crea una nueva papeleta SOLICITADA y el total de papeletas para (hermano, acto)
    #         pasa a 2 (la anulada + la nueva).
    #     """
    #     now = timezone.now()

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
    #         es_solicitud_insignia=False,
    #         puesto=self.puesto_cirio_ok,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         nueva = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(nueva.id)
    #     nueva.refresh_from_db()

    #     self.assertEqual(nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(nueva.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(nueva.es_solicitud_insignia)

    #     total = PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count()
    #     self.assertEqual(total, 2)

    #     activas = PapeletaSitio.objects.exclude(
    #         estado_papeleta__in=[PapeletaSitio.EstadoPapeleta.ANULADA, PapeletaSitio.EstadoPapeleta.NO_ASIGNADA]
    #     ).filter(hermano=self.hermano, acto=self.acto).count()
    #     self.assertEqual(activas, 1)



    # def test_tradicional_cirio_con_papeleta_prev_no_asignada_no_bloquea_y_permite_crear_nueva(self):
    #     """
    #     Test: Existe papeleta previa NO_ASIGNADA => NO bloquea => permite crear nueva.

    #     Given: hermano tiene una papeleta NO_ASIGNADA para el mismo acto (es_solicitud_insignia=False).
    #         acto TRADICIONAL con plazo de cirios vigente.
    #         puesto válido.
    #     When: se procesa una nueva solicitud de cirio tradicional.
    #     Then: se crea una nueva papeleta SOLICITADA y el total de papeletas para (hermano, acto)
    #         pasa a 2 (la NO_ASIGNADA + la nueva).
    #     """
    #     now = timezone.now()

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
    #         es_solicitud_insignia=False,
    #         puesto=self.puesto_cirio_ok,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         nueva = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(nueva.id)
    #     nueva.refresh_from_db()

    #     self.assertEqual(nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(nueva.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(nueva.es_solicitud_insignia)

    #     total = PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count()
    #     self.assertEqual(total, 2)

    #     activas = PapeletaSitio.objects.exclude(
    #         estado_papeleta__in=[PapeletaSitio.EstadoPapeleta.ANULADA, PapeletaSitio.EstadoPapeleta.NO_ASIGNADA]
    #     ).filter(hermano=self.hermano, acto=self.acto).count()
    #     self.assertEqual(activas, 1)



    # def test_tradicional_cirio_con_mezcla_anulada_y_no_asignada_no_bloquea_y_permite_crear_nueva(self):
    #     """
    #     Test: Existe mezcla de papeletas previas ANULADA y NO_ASIGNADA => NO bloquea => permite crear nueva.

    #     Given: hermano tiene 2 papeletas previas para el mismo acto:
    #         - una ANULADA
    #         - una NO_ASIGNADA
    #         (ambas son estados NO activos según el service/constraint)
    #     When: se procesa una nueva solicitud de cirio tradicional.
    #     Then: se crea una nueva papeleta SOLICITADA sin bloqueo.
    #     """
    #     now = timezone.now()

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
    #         es_solicitud_insignia=False,
    #         puesto=self.puesto_cirio_ok,
    #         codigo_verificacion="ABCDEF12",
    #     )

    #     PapeletaSitio.objects.create(
    #         hermano=self.hermano,
    #         acto=self.acto,
    #         anio=self.acto.fecha.year,
    #         fecha_solicitud=now,
    #         estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
    #         es_solicitud_insignia=False,
    #         puesto=self.puesto_cirio_ok,
    #         codigo_verificacion="ABCDEF34",
    #     )

    #     with patch("django.utils.timezone.now", return_value=now):
    #         nueva = self.service.procesar_solicitud_cirio_tradicional(
    #             hermano=self.hermano,
    #             acto=self.acto,
    #             puesto=self.puesto_cirio_ok,
    #         )

    #     self.assertIsNotNone(nueva.id)
    #     nueva.refresh_from_db()

    #     self.assertEqual(nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
    #     self.assertEqual(nueva.puesto_id, self.puesto_cirio_ok.id)
    #     self.assertFalse(nueva.es_solicitud_insignia)

    #     total = PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count()
    #     self.assertEqual(total, 3)

    #     activas = PapeletaSitio.objects.exclude(
    #         estado_papeleta__in=[PapeletaSitio.EstadoPapeleta.ANULADA, PapeletaSitio.EstadoPapeleta.NO_ASIGNADA]
    #     ).filter(hermano=self.hermano, acto=self.acto).count()
    #     self.assertEqual(activas, 1)



    def test_tradicional_cirio_integrity_error_en_crear_papeleta_base_traduce_a_validation_error_doble_click(self):
        """
        Test: se produce IntegrityError al crear la papeleta base (constraint unique)
        ⇒ el service debe capturarlo y relanzar ValidationError con el mensaje de
        "doble click / recarga".

        Este test simula una condición de carrera (dos peticiones simultáneas)
        y valida que el error de BD se traduce correctamente a un mensaje de dominio.
        """
        now = timezone.now()

        with patch("django.utils.timezone.now", return_value=now), \
            patch.object(
                self.service,
                "_crear_papeleta_base",
                side_effect=IntegrityError("unique_papeleta_activa_hermano_acto")
            ):

            with self.assertRaises(DjangoValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                )

        err = ctx.exception

        self.assertEqual(
            err.messages,
            [
                "Ya existe una papeleta activa para este acto. "
                "Si has pulsado dos veces, espera unos segundos y recarga."
            ],
        )