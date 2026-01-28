import re
from django.test import TestCase
from django.utils import timezone
from unittest import mock
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock, patch

from api.models import (
    Acto, Cuota, Hermano, PreferenciaSolicitud, TipoActo, Puesto, TipoPuesto, 
    CuerpoPertenencia, HermanoCuerpo, PapeletaSitio
)

from api.servicios.papeleta_sitio_service import PapeletaSitioService
from api.tests.factories import HermanoFactory

User = get_user_model()

class ProcesarSolicitudCirioServiceTest(TestCase):
    
    def setUp(self):
        """
        Setup base para pruebas de solicitud de CIRIOS (Modalidad Tradicional - Fase 2).
        Garantiza:
        - Acto requiere papeleta
        - Modalidad TRADICIONAL
        - Plazo de insignias cerrado
        - Plazo de cirios abierto (ahora dentro)
        - inicio_solicitud_cirios > fin_solicitud (cumple clean() del modelo)
        - Hermano en ALTA, con cuerpo permitido y cuotas al corriente hasta año anterior
        - Puesto de cirio válido y puesto insignia (para casos negativos)
        """
        self.service = PapeletaSitioService()
        self.ahora = timezone.now()

        # ---------------------------------------------------------------------
        # Cuerpos
        # ---------------------------------------------------------------------
        self.cuerpo_nazarenos = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS
        )
        self.cuerpo_costaleros = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )

        self.cuerpo_priostia = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.PRIOSTÍA
        )

        self.cuerpo_juventud = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUVENTUD
        )

        self.cuerpo_caridad_accion_social = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL
        )

        # ---------------------------------------------------------------------
        # Hermano (ALTA + número_registro obligatorio por clean())
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

        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 5,
        )

        # ---------------------------------------------------------------------
        # Cuotas: al corriente hasta el año anterior
        # (si existe cualquiera <= año_anterior con estado != PAGADA -> falla)
        # ---------------------------------------------------------------------
        anio_actual = self.ahora.date().year
        anio_anterior = anio_actual - 1

        Cuota.objects.create(
            hermano=self.hermano,
            anio=anio_anterior,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_anterior}",
            importe="30.00",
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            fecha_pago=self.ahora.date() - timedelta(days=10),
        )

        # ---------------------------------------------------------------------
        # TipoActo + Acto con ventanas consistentes
        # ---------------------------------------------------------------------
        self.tipo_acto = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        # Insignias: ya terminó
        self.inicio_insignias = self.ahora - timedelta(days=10)
        self.fin_insignias = self.ahora - timedelta(days=2)

        # Cirios: ahora está dentro del plazo
        # IMPORTANTE: inicio_cirios debe ser > fin_insignias (no >=)
        self.inicio_cirios = self.fin_insignias + timedelta(minutes=1)
        self.fin_cirios = self.ahora + timedelta(days=2)

        self.acto = Acto.objects.create(
            nombre="Estación de Penitencia 2026",
            descripcion="Acto principal",
            fecha=self.ahora + timedelta(days=30),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto,
            inicio_solicitud=self.inicio_insignias,
            fin_solicitud=self.fin_insignias,
            inicio_solicitud_cirios=self.inicio_cirios,
            fin_solicitud_cirios=self.fin_cirios
        )

        # ---------------------------------------------------------------------
        # Tipos de puesto + Puestos
        # ---------------------------------------------------------------------
        self.tipo_puesto_cirio = TipoPuesto.objects.create(
            nombre_tipo="CIRIO",
            es_insignia=False,
            solo_junta_gobierno=False
        )
        self.tipo_puesto_cruz = TipoPuesto.objects.create(
            nombre_tipo="CRUZ PENITENTE",
            es_insignia=False,
            solo_junta_gobierno=False
        )
        self.tipo_puesto_vara = TipoPuesto.objects.create(
            nombre_tipo="VARA",
            es_insignia=True,   # para testear el error de “es insignia”
            solo_junta_gobierno=False
        )

        self.puesto_cirio_ok = Puesto.objects.create(
            nombre="Cirio Tramo 1",
            acto=self.acto,
            tipo_puesto=self.tipo_puesto_cirio,
            disponible=True,
            numero_maximo_asignaciones=10
        )

        self.puesto_cruz_ok = Puesto.objects.create(
            nombre="Cruz Penitente Tramo 2",
            acto=self.acto,
            tipo_puesto=self.tipo_puesto_cruz,
            disponible=True,
            numero_maximo_asignaciones=5
        )

        self.puesto_insignia = Puesto.objects.create(
            nombre="Vara de Presidencia",
            acto=self.acto,
            tipo_puesto=self.tipo_puesto_vara,
            disponible=True,
            numero_maximo_asignaciones=1
        )

        self.puesto_no_disponible = Puesto.objects.create(
            nombre="Cirio Bloqueado",
            acto=self.acto,
            tipo_puesto=self.tipo_puesto_cirio,
            disponible=False,
            numero_maximo_asignaciones=10
        )

        # Puesto de OTRO acto (para validar “No puede seleccionar un puesto de otro acto”)
        self.acto_otro = Acto.objects.create(
            nombre="Otro Acto 2026",
            descripcion="Otro",
            fecha=self.ahora + timedelta(days=60),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto,
            inicio_solicitud=self.inicio_insignias,
            fin_solicitud=self.fin_insignias,
            inicio_solicitud_cirios=self.inicio_cirios,
            fin_solicitud_cirios=self.fin_cirios
        )
        self.puesto_otro_acto = Puesto.objects.create(
            nombre="Cirio de otro acto",
            acto=self.acto_otro,
            tipo_puesto=self.tipo_puesto_cirio,
            disponible=True,
            numero_maximo_asignaciones=10
        )

    # Helpers opcionales para preparar estados previos rápidamente
    def _crear_insignia_solicitada(self):
        return PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

    def _crear_insignia_emitida(self):
        return PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            fecha_emision=self.ahora.date(),
            codigo_verificacion="ABCDEFGH",
        )

    def _crear_cirio_activo(self, puesto=None, estado=PapeletaSitio.EstadoPapeleta.SOLICITADA):
        return PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=estado,
            es_solicitud_insignia=False,
            puesto=puesto or self.puesto_cirio_ok,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )
    


    def test_procesar_solicitud_cirio_tradicional_ok_crea_papeleta_cirio(self):
        """
        Test: Caso base OK (crea papeleta de cirio)

        Given: acto TRADICIONAL, requiere_papeleta=True, plazo de cirios configurado, ahora dentro de plazo,
            hermano ALTA, sin deuda hasta año anterior, cuerpo permitido (o sin cuerpos),
            puesto del mismo acto, puesto.es_insignia=False, puesto.disponible=True,
            no hay papeleta previa activa, no hay solicitud de insignia emitida.
        When: se procesa la solicitud de cirio con un puesto válido
        Then: crea PapeletaSitio con:
            - estado_papeleta=SOLICITADA
            - es_solicitud_insignia=False
            - puesto asignado
            - anio == acto.fecha.year
            - fecha_solicitud == ahora (tiempo congelado)
            - codigo_verificacion longitud 8, [0-9A-F], uppercase
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)

        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)

        self.assertIsNotNone(papeleta_db.codigo_verificacion)
        self.assertEqual(len(papeleta_db.codigo_verificacion), 8)
        self.assertRegex(papeleta_db.codigo_verificacion, r"^[0-9A-F]{8}$")
        self.assertEqual(papeleta_db.codigo_verificacion, papeleta_db.codigo_verificacion.upper())



    def test_procesar_solicitud_cirio_tradicional_con_insignia_solicitada_anula_insignia_y_crea_cirio(self):
        """
        Test: Existe solicitud de insignia SOLICITADA ⇒ se ANULA y se crea cirio

        Given: existe PapeletaSitio de insignia (es_solicitud_insignia=True) en estado SOLICITADA para (hermano, acto).
        When: solicita cirio válido.
        Then: esa papeleta pasa a ANULADA y se crea nueva papeleta de cirio SOLICITADA.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        insignia_previa = PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta_cirio = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None
            )

        insignia_previa.refresh_from_db()
        self.assertEqual(insignia_previa.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

        papeleta_cirio_db = PapeletaSitio.objects.get(id=papeleta_cirio.id)
        self.assertEqual(papeleta_cirio_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_cirio_db.es_solicitud_insignia)
        self.assertEqual(papeleta_cirio_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_cirio_db.fecha_solicitud, ahora_congelado)

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
            2
        )



    def test_procesar_solicitud_cirio_tradicional_con_insignia_anulada_no_afecta_y_crea_cirio(self):
        """
        Test: Existe solicitud de insignia ANULADA ⇒ no afecta y se crea cirio

        Given: insignia previa ANULADA (no cuenta como pendiente).
        When: solicita cirio válido.
        Then: no se modifica la insignia (sigue ANULADA) y se crea nueva papeleta de cirio SOLICITADA.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        insignia_anulada = PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta_cirio = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None
            )

        insignia_anulada.refresh_from_db()
        self.assertEqual(insignia_anulada.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

        papeleta_cirio_db = PapeletaSitio.objects.get(id=papeleta_cirio.id)
        self.assertEqual(papeleta_cirio_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_cirio_db.es_solicitud_insignia)
        self.assertEqual(papeleta_cirio_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_cirio_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_cirio_db.fecha_solicitud, ahora_congelado)

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
            2
        )



    def test_procesar_solicitud_cirio_tradicional_hermano_sin_cuerpos_permitido_crea_cirio(self):
        """
        Test: Hermano sin cuerpos asociados ⇒ permitido

        Given: hermano.cuerpos vacío.
        Then: permitido (por _validar_pertenencia_cuerpos hace return) y crea cirio.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        hermano_sin_cuerpos = Hermano.objects.create_user(
            dni="11111111H",
            username="11111111H",
            password="password",
            nombre="Pepe",
            primer_apellido="López",
            segundo_apellido="Martín",
            email="pepe@example.com",
            telefono="600111111",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=2001,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1990-01-01",
            direccion="Calle Feria",
            codigo_postal="41003",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        anio_actual = self.ahora.date().year
        anio_anterior = anio_actual - 1
        hermano_sin_cuerpos.cuotas.create(
            anio=anio_anterior,
            tipo=self.cuota_pagada_anio_anterior.tipo if hasattr(self, "cuota_pagada_anio_anterior") else "ORDINARIA",
            descripcion=f"Cuota {anio_anterior}",
            importe="30.00",
            estado="PAGADA",
            metodo_pago="DOMICILIACION",
            fecha_pago=self.ahora.date(),
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=hermano_sin_cuerpos,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)
        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.acto_id, self.acto.id)
        self.assertEqual(papeleta_db.hermano_id, hermano_sin_cuerpos.id)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)



    def test_procesar_solicitud_cirio_tradicional_cuerpo_permitido_nazarenos_ok(self):
        """
        Test: Cuerpo permitido → NAZARENOS

        Given: hermano pertenece únicamente al cuerpo NAZARENOS (cuerpo permitido),
            resto de condiciones del caso base OK.
        When: solicita cirio válido.
        Then: permitido y se crea papeleta de cirio correctamente.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.cuerpos.clear()

        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 5,
        )

        self.assertEqual(
            list(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True)),
            [CuerpoPertenencia.NombreCuerpo.NAZARENOS],
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)

        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)



    def test_procesar_solicitud_cirio_tradicional_cuerpo_permitido_priostia_ok(self):
        """
        Test: Cuerpo permitido → PRIOSTÍA

        Given: hermano pertenece únicamente al cuerpo PRIOSTÍA (cuerpo permitido),
            resto de condiciones del caso base OK.
        When: solicita cirio válido.
        Then: permitido y se crea papeleta de cirio correctamente.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.cuerpos.clear()

        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_priostia,
            anio_ingreso=self.ahora.year - 5,
        )

        self.assertEqual(
            list(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True)),
            [CuerpoPertenencia.NombreCuerpo.PRIOSTÍA],
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)

        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)



    def test_procesar_solicitud_cirio_tradicional_cuerpo_permitido_juventud_ok(self):
        """
        Test: Cuerpo permitido → JUVENTUD

        Given: hermano pertenece únicamente al cuerpo JUVENTUD (cuerpo permitido),
            resto de condiciones del caso base OK.
        When: solicita cirio válido.
        Then: permitido y se crea papeleta de cirio correctamente.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.cuerpos.clear()

        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_juventud,
            anio_ingreso=self.ahora.year - 5,
        )

        self.assertEqual(
            list(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True)),
            [CuerpoPertenencia.NombreCuerpo.JUVENTUD],
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)

        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)



    def test_procesar_solicitud_cirio_tradicional_cuerpo_permitido_caridad_accion_social_ok(self):
        """
        Test: Cuerpo permitido → CARIDAD_ACCION_SOCIAL

        Given: hermano pertenece únicamente al cuerpo CARIDAD_ACCION_SOCIAL (cuerpo permitido),
            resto de condiciones del caso base OK.
        When: solicita cirio válido.
        Then: permitido y se crea papeleta de cirio correctamente.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.cuerpos.clear()

        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_caridad_accion_social,
            anio_ingreso=self.ahora.year - 5,
        )

        self.assertEqual(
            list(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True)),
            [CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL],
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        # Then
        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)

        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)



    def test_procesar_solicitud_cirio_tradicional_limite_inferior_plazo_cirios_permitido(self):
        """
        Test: Límite inferior del plazo de cirios (ahora == inicio_solicitud_cirios)

        Given: ahora exactamente igual a acto.inicio_solicitud_cirios.
        When: solicita cirio válido.
        Then: permitido (la condición es ahora < inicio) y se crea papeleta de cirio.
        """
        ahora_congelado = self.acto.inicio_solicitud_cirios

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)

        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)



    def test_procesar_solicitud_cirio_tradicional_limite_superior_plazo_cirios_permitido(self):
        """
        Test: Límite superior del plazo de cirios (ahora == fin_solicitud_cirios)

        Given: ahora exactamente igual a acto.fin_solicitud_cirios.
        When: solicita cirio válido.
        Then: permitido (la condición es ahora > fin) y se crea papeleta de cirio.
        """
        ahora_congelado = self.acto.fin_solicitud_cirios

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)

        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.anio, self.acto.fecha.year)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)



    def test_procesar_solicitud_cirio_tradicional_papeleta_cirio_anulada_previa_no_bloquea_crea_nueva(self):
        """
        Test: Papeleta previa ANULADA de cirio no bloquea

        Given: existe papeleta de cirio para (hermano, acto) pero estado_papeleta=ANULADA.
        When: solicita cirio válido.
        Then: permitido y crea una nueva papeleta de cirio SOLICITADA.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        papeleta_anulada = PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
            es_solicitud_insignia=False,
            puesto=self.puesto_cirio_ok,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            # When
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        self.assertNotEqual(nueva_papeleta.id, papeleta_anulada.id)

        nueva_db = PapeletaSitio.objects.get(id=nueva_papeleta.id)
        self.assertEqual(nueva_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(nueva_db.es_solicitud_insignia)
        self.assertEqual(nueva_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(nueva_db.fecha_solicitud, ahora_congelado)

        papeleta_anulada.refresh_from_db()
        self.assertEqual(papeleta_anulada.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

        self.assertEqual(
            PapeletaSitio.objects.filter(
                hermano=self.hermano,
                acto=self.acto,
                es_solicitud_insignia=False
            ).count(),
            2
        )



    def test_procesar_solicitud_cirio_tradicional_acto_no_admite_solicitudes_lanza_error(self):
        """
        Test: Acto no admite solicitudes (requiere_papeleta=False)

        Then: ValidationError(f"El acto '{acto.nombre}' no admite solicitudes.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        tipo_acto_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CABILDO_GENERAL,
            requiere_papeleta=False
        )

        acto_sin_papeleta = Acto.objects.create(
            nombre="Cabildo sin papeleta",
            descripcion="No admite solicitudes",
            fecha=self.ahora + timezone.timedelta(days=30),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=tipo_acto_sin_papeleta,
            inicio_solicitud=self.inicio_insignias,
            fin_solicitud=self.fin_insignias,
            inicio_solicitud_cirios=self.inicio_cirios,
            fin_solicitud_cirios=self.fin_cirios,
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=acto_sin_papeleta,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None
                )

        self.assertEqual(
            ctx.exception.messages[0],
            f"El acto '{acto_sin_papeleta.nombre}' no admite solicitudes."
        )



    def test_procesar_solicitud_cirio_tradicional_modalidad_incorrecta_unificado_lanza_error(self):
        """
        Test: Modalidad incorrecta (acto UNIFICADO)

        Given: acto.modalidad = UNIFICADO
        When: solicita cirio
        Then: ValidationError("Este endpoint es solo para actos de modalidad TRADICIONAL.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.acto.modalidad = Acto.ModalidadReparto.UNIFICADO
        self.acto.save(update_fields=["modalidad"])

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(ctx.exception.messages[0], "Este endpoint es solo para actos de modalidad TRADICIONAL.")



    def test_procesar_solicitud_cirio_tradicional_hermano_no_en_alta_baja_lanza_error(self):
        """
        Test: Hermano NO está en ALTA (BAJA)

        Given: estado_hermano=BAJA y fecha_baja_corporacion informada (para pasar clean()).
        Then: ValidationError("Solo los hermanos en estado ALTA pueden solicitar papeleta.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.estado_hermano = Hermano.EstadoHermano.BAJA
        self.hermano.fecha_baja_corporacion = self.ahora.date()
        self.hermano.save(update_fields=["estado_hermano", "fecha_baja_corporacion"])

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "Solo los hermanos en estado ALTA pueden solicitar papeleta."
        )



    def test_procesar_solicitud_cirio_tradicional_hermano_no_en_alta_pendiente_lanza_error(self):
        """
        Test: Hermano NO está en ALTA (PENDIENTE_INGRESO)

        Then: ValidationError("Solo los hermanos en estado ALTA pueden solicitar papeleta.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.estado_hermano = Hermano.EstadoHermano.PENDIENTE_INGRESO
        self.hermano.save(update_fields=["estado_hermano"])

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "Solo los hermanos en estado ALTA pueden solicitar papeleta."
        )



    def test_procesar_solicitud_cirio_tradicional_hermano_con_deuda_hasta_anio_anterior_lanza_error(self):
        """
        Test: Hermano con deuda hasta año anterior

        Given: existe Cuota con anio <= (año_actual - 1) y estado != PAGADA.
        When: solicita cirio válido.
        Then: ValidationError(
            "No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}."
        )
        (Aunque el mensaje hable de “insignias”, en este servicio también se aplica)
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        anio_actual = ahora_congelado.date().year
        anio_limite = anio_actual - 1

        Cuota.objects.create(
            hermano=self.hermano,
            anio=anio_limite,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_limite}",
            importe="30.00",
            estado=Cuota.EstadoCuota.PENDIENTE,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            f"No puede solicitar insignias: debe estar al corriente de pago hasta {anio_limite}."
        )



    def test_procesar_solicitud_cirio_tradicional_cuerpo_no_permitido_costaleros_lanza_error(self):
        """
        Test: Hermano con cuerpo NO permitido (COSTALEROS)

        Given: hermano pertenece únicamente al cuerpo COSTALEROS (no permitido).
        When: solicita cirio válido.
        Then: ValidationError("Tu cuerpo de pertenencia actual no permite solicitar papeleta.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.cuerpos.clear()

        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_costaleros,
            anio_ingreso=self.ahora.year - 5,
        )

        self.assertEqual(
            list(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True)),
            [CuerpoPertenencia.NombreCuerpo.COSTALEROS],
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "Tu cuerpo de pertenencia actual no permite solicitar papeleta."
        )



    def test_procesar_solicitud_cirio_tradicional_mezcla_cuerpos_permitido_y_no_permitido_bloquea(self):
        """
        Test: Hermano con mezcla de cuerpos (uno permitido + uno NO permitido)

        Given: hermano pertenece a NAZARENOS (permitido) y COSTALEROS (NO permitido).
        When: solicita cirio válido.
        Then: bloquea igualmente porque existe al menos un cuerpo no permitido.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.hermano.cuerpos.clear()

        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 5,
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano,
            cuerpo=self.cuerpo_costaleros,
            anio_ingreso=self.ahora.year - 3,
        )

        self.assertCountEqual(
            list(self.hermano.cuerpos.values_list("nombre_cuerpo", flat=True)),
            [
                CuerpoPertenencia.NombreCuerpo.NAZARENOS,
                CuerpoPertenencia.NombreCuerpo.COSTALEROS,
            ],
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "Tu cuerpo de pertenencia actual no permite solicitar papeleta."
        )



    def test_procesar_solicitud_cirio_tradicional_con_insignia_emitida_lanza_error(self):
        """
        Test: Tiene insignia EMITIDA ⇒ no puede pedir cirio

        Given: existe papeleta de insignia (es_solicitud_insignia=True) con estado EMITIDA
            para (hermano, acto).
        When: solicita cirio válido.
        Then: ValidationError(
            "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio."
        )
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            fecha_emision=self.ahora.date(),
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio."
        )



    def test_procesar_solicitud_cirio_tradicional_ya_existe_cirio_activo_mismo_tipo_lanza_error(self):
        """
        Test: Ya existe papeleta de cirio activa del MISMO tipo de puesto

        Given: existe papeleta (es_solicitud_insignia=False) no ANULADA con
            puesto.tipo_puesto_id == puesto_nuevo.tipo_puesto_id
        When: solicita cirio con el mismo tipo (CIRIO)
        Then: ValidationError(
            f"Ya tienes una solicitud activa para el tipo '{puesto.tipo_puesto.nombre_tipo}'. "
            "Solo puedes solicitar un puesto de ese tipo."
        )
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=self.puesto_cirio_ok,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            f"Ya tienes una solicitud activa para el tipo '{self.puesto_cirio_ok.tipo_puesto.nombre_tipo}'. "
            "Solo puedes solicitar un puesto de ese tipo."
        )



    def test_procesar_solicitud_cirio_tradicional_ya_existe_cirio_activo_otro_tipo_lanza_error(self):
        """
        Test: Ya existe papeleta de cirio activa de OTRO tipo

        Given: existe papeleta de cirio activa (no ANULADA) con tipo_puesto_id != tipo del nuevo puesto.
        When: intenta solicitar un puesto de un tipo distinto.
        Then: ValidationError(
            "Solo puedes solicitar un único tipo de puesto en este acto (por ejemplo, CIRIO o CRUZ PENITENTE, pero no ambos)."
        )
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=self.puesto_cruz_ok,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "Solo puedes solicitar un único tipo de puesto en este acto (por ejemplo, CIRIO o CRUZ PENITENTE, pero no ambos)."
        )



    def test_procesar_solicitud_cirio_tradicional_papeleta_cirio_activa_con_puesto_null_bloquea(self):
        """
        Test: Edge case — existe papeleta de cirio activa con puesto = NULL

        Given: existe papeleta es_solicitud_insignia=False, estado != ANULADA, con puesto = None.
        When: intenta solicitar un cirio válido.
        Then: entra en tipo_existente_id = None y termina bloqueando con el error genérico
            de “Solo puedes solicitar un único tipo de puesto…”.
        (Cubre explícitamente el ternario: papeleta_cirio_activa.puesto else None)
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=None,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "Solo puedes solicitar un único tipo de puesto en este acto (por ejemplo, CIRIO o CRUZ PENITENTE, pero no ambos)."
        )



    def test_procesar_solicitud_cirio_tradicional_unicidad_existe_papeleta_activa_lanza_error(self):
        """
        Test: Unicidad — existe otra papeleta NO ANULADA para (hermano, acto)

        Given: existe papeleta activa (insignia o cirio) con estado distinto de ANULADA.
            (En este test la creamos como INSIGNIA EMITIDA pero ANULAMOS el bloqueo anterior
            usando un estado activo distinto a EMITIDA para no caer en "ya tienes insignia asignada".)
        Then: ValidationError("Ya existe una solicitud activa para este acto.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.RECOGIDA,
            es_solicitud_insignia=True,
            puesto=self.puesto_insignia,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(ctx.exception.messages[0], "Ya existe una solicitud activa para este acto.")



    def test_procesar_solicitud_cirio_tradicional_unicidad_existe_papeleta_anulada_no_bloquea(self):
        """
        Test: Unicidad — existe papeleta ANULADA para (hermano, acto)

        Given: existe una papeleta ANULADA (insignia o cirio) para (hermano, acto).
        When: solicita cirio válido.
        Then: NO debe bloquear por unicidad y se crea una nueva papeleta de cirio SOLICITADA.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
            es_solicitud_insignia=False,
            puesto=self.puesto_cirio_ok,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano,
                acto=self.acto,
                puesto=self.puesto_cirio_ok,
                numero_registro_vinculado=None,
            )

        papeleta_db = PapeletaSitio.objects.get(id=papeleta.id)
        self.assertEqual(papeleta_db.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta_db.es_solicitud_insignia)
        self.assertEqual(papeleta_db.puesto_id, self.puesto_cirio_ok.id)
        self.assertEqual(papeleta_db.fecha_solicitud, ahora_congelado)

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
            2
        )



    def test_procesar_solicitud_cirio_tradicional_plazo_cirios_no_configurado_lanza_error(self):
        """
        Test: Plazo de cirios no configurado (inicio o fin None)

        Given: acto.inicio_solicitud_cirios o acto.fin_solicitud_cirios es None
        When: solicita cirio válido
        Then: ValidationError("Plazo de cirios no configurado.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.acto.inicio_solicitud_cirios = None
        self.acto.save(update_fields=["inicio_solicitud_cirios"])

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(ctx.exception.messages[0], "Plazo de cirios no configurado.")



    def test_procesar_solicitud_cirio_tradicional_fuera_plazo_por_abajo_lanza_error(self):
        """
        Test: Fuera de plazo por abajo (ahora < inicio_solicitud_cirios)

        Given: ahora estrictamente menor que acto.inicio_solicitud_cirios
        When: solicita cirio válido
        Then: ValidationError(
            f"El plazo de cirios comienza el {acto.inicio_solicitud_cirios}."
        )
        """
        ahora_congelado = self.acto.inicio_solicitud_cirios - timezone.timedelta(seconds=1)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            f"El plazo de cirios comienza el {self.acto.inicio_solicitud_cirios}."
    )
        


    def test_procesar_solicitud_cirio_tradicional_fuera_plazo_por_arriba_lanza_error(self):
        """
        Test: Fuera de plazo por arriba (ahora > fin_solicitud_cirios)

        Given: ahora estrictamente mayor que acto.fin_solicitud_cirios
        When: solicita cirio válido
        Then: ValidationError("El plazo de solicitud de cirios ha finalizado.")
        """
        ahora_congelado = self.acto.fin_solicitud_cirios + timezone.timedelta(seconds=1)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "El plazo de solicitud de cirios ha finalizado."
        )



    def test_procesar_solicitud_cirio_tradicional_frontera_inicio_menos_un_microsegundo(self):
        """
        Test: Frontera: ahora == inicio_solicitud_cirios - 1 microsegundo

        Given: ahora es exactamente 1 microsegundo menor que inicio_solicitud_cirios
        When: solicita cirio válido
        Then: debe caer en N14 → ValidationError(
            f"El plazo de cirios comienza el {acto.inicio_solicitud_cirios}."
        )
        """
        ahora_congelado = self.acto.inicio_solicitud_cirios - timezone.timedelta(microseconds=1)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            f"El plazo de cirios comienza el {self.acto.inicio_solicitud_cirios}."
        )



    def test_procesar_solicitud_cirio_tradicional_frontera_fin_mas_un_microsegundo_cae_en_n15(self):
        """
        Test: Frontera: ahora == fin_solicitud_cirios + 1 microsegundo

        Given: ahora es exactamente 1 microsegundo mayor que fin_solicitud_cirios
        When: solicita cirio válido
        Then: debe caer en N15 → ValidationError("El plazo de solicitud de cirios ha finalizado.")
        """
        ahora_congelado = self.acto.fin_solicitud_cirios + timezone.timedelta(microseconds=1)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_cirio_ok,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "El plazo de solicitud de cirios ha finalizado."
        )



    def test_procesar_solicitud_cirio_tradicional_puesto_de_otro_acto_lanza_error(self):
        """
        Test: Puesto pertenece a otro acto

        Given: el puesto.acto_id es distinto del acto sobre el que se solicita la papeleta.
        When: solicita cirio válido.
        Then: ValidationError("No puede seleccionar un puesto de otro acto.")
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.assertNotEqual(self.puesto_otro_acto.acto_id, self.acto.id)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_otro_acto,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "No puede seleccionar un puesto de otro acto."
        )



    def test_procesar_solicitud_cirio_tradicional_puesto_es_insignia_lanza_error(self):
        """
        Test: Puesto es insignia (no puede ser cirio)

        Given: puesto.tipo_puesto.es_insignia = True
        When: solicita cirio usando un puesto de insignia
        Then: ValidationError(
            f"El puesto '{puesto.nombre}' es una insignia y no puede solicitarse como cirio."
        )
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.assertTrue(self.puesto_insignia.tipo_puesto.es_insignia)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_insignia,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            f"El puesto '{self.puesto_insignia.nombre}' es una insignia y no puede solicitarse como cirio."
        )



    def test_procesar_solicitud_cirio_tradicional_puesto_no_disponible_lanza_error(self):
        """
        Test: Puesto no disponible

        Given: puesto.disponible = False
        When: solicita cirio usando un puesto no disponible
        Then: ValidationError(
            f"El puesto '{puesto.nombre}' no está disponible para su solicitud en este acto."
        )
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        self.assertFalse(self.puesto_no_disponible.disponible)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_no_disponible,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            f"El puesto '{self.puesto_no_disponible.nombre}' no está disponible para su solicitud en este acto."
        )



    def test_procesar_solicitud_cirio_tradicional_prioridad_error_puesto_otro_acto_antes_que_insignia_y_no_disponible(self):
        """
        Test: Puesto es de otro acto y además es insignia/no disponible (prioridad de error)

        Objetivo: verificar qué mensaje sale primero.

        Given: puesto pertenece a otro acto y además:
            - puesto.tipo_puesto.es_insignia=True
            - puesto.disponible=False
        When: solicita cirio con ese puesto
        Then: debe saltar primero "No puede seleccionar un puesto de otro acto."
            (porque se chequea antes que insignia/disponible)
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        tipo_puesto_insignia = TipoPuesto.objects.create(
            nombre_tipo="INSIGNIA TEST (OTRO ACTO)",
            es_insignia=True,
            solo_junta_gobierno=False,
        )

        puesto_otro_acto_y_insignia_y_no_disponible = Puesto.objects.create(
            nombre="Puesto conflictivo",
            acto=self.acto_otro,
            tipo_puesto=tipo_puesto_insignia,
            disponible=False,
            numero_maximo_asignaciones=1,
        )

        self.assertNotEqual(puesto_otro_acto_y_insignia_y_no_disponible.acto_id, self.acto.id)
        self.assertTrue(puesto_otro_acto_y_insignia_y_no_disponible.tipo_puesto.es_insignia)
        self.assertFalse(puesto_otro_acto_y_insignia_y_no_disponible.disponible)

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=puesto_otro_acto_y_insignia_y_no_disponible,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(
            ctx.exception.messages[0],
            "No puede seleccionar un puesto de otro acto."
        )



    def test_procesar_solicitud_cirio_tradicional_si_falla_create_no_deja_insignia_anulada_por_rollback(self):
        """
        Test: Si falla la creación de la papeleta de cirio, no debe quedar insignia anulada

        Given: existe solicitud_insignia_pendiente SOLICITADA.
        When: forzamos excepción al crear la papeleta de cirio (mock a PapeletaSitio.objects.create).
        Then: rollback => la insignia sigue SOLICITADA y no existe nueva papeleta.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        insignia_pendiente = PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
            1
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with patch("api.models.PapeletaSitio.objects.create", side_effect=Exception("DB error")):
                with self.assertRaises(Exception):
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano,
                        acto=self.acto,
                        puesto=self.puesto_cirio_ok,
                        numero_registro_vinculado=None,
                    )

        insignia_pendiente.refresh_from_db()
        self.assertEqual(insignia_pendiente.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertFalse(
            PapeletaSitio.objects.filter(
                hermano=self.hermano,
                acto=self.acto,
                es_solicitud_insignia=False
            ).exists()
        )

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
            1
        )



    def test_procesar_solicitud_cirio_tradicional_si_falla_despues_de_anular_insignia_rollback_total(self):
        """
        Test: Si falla después de anular insignia pero antes de finalizar, rollback total

        Given: existe solicitud_insignia_pendiente SOLICITADA.
        When: forzamos un fallo "tardío" DESPUÉS de anular la insignia
            (simulamos que existe una papeleta_cirio_activa que provoca ValidationError).
        Then: rollback => la insignia NO queda anulada (sigue SOLICITADA) y no existe nueva papeleta de cirio.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        insignia_pendiente = PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
            1
        )

        papeleta_cirio_activa_mock = MagicMock()
        papeleta_cirio_activa_mock.puesto = MagicMock()
        papeleta_cirio_activa_mock.puesto.tipo_puesto_id = 9999

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with patch(
                "api.models.PapeletaSitio.objects.filter"
            ) as filter_mock:

                qs_insignia_emitida = MagicMock()
                qs_insignia_emitida.exists.return_value = False

                qs_insignia_pendiente = MagicMock()
                qs_insignia_pendiente.first.return_value = insignia_pendiente

                qs_cirio_activa = MagicMock()
                qs_cirio_activa.exclude.return_value.select_related.return_value.first.return_value = papeleta_cirio_activa_mock

                filter_mock.side_effect = [qs_insignia_emitida, qs_insignia_pendiente, qs_cirio_activa]

                with self.assertRaises(ValidationError):
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano,
                        acto=self.acto,
                        puesto=self.puesto_cirio_ok,
                        numero_registro_vinculado=None,
                    )

        insignia_pendiente.refresh_from_db()
        self.assertEqual(insignia_pendiente.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertFalse(
            PapeletaSitio.objects.filter(
                hermano=self.hermano,
                acto=self.acto,
                es_solicitud_insignia=False
            ).exists()
        )

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano, acto=self.acto).count(),
            1
        )



    def test_procesar_solicitud_cirio_tradicional_puesto_none_lanza_error_y_no_crea_papeleta(self):
        """
        Test: Puesto es None

        Given: se intenta procesar una solicitud de cirio con puesto=None.
        When: se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: lanza ValidationError indicando que debe seleccionarse un puesto válido
            y no se persiste ninguna PapeletaSitio en base de datos.
        """
        acto = self.acto
        hermano = self.hermano
        puesto = None

        with self.assertRaises(ValidationError) as ctx:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=hermano,
                acto=acto,
                puesto=puesto,
                numero_registro_vinculado=None
            )

        self.assertEqual(
            ctx.exception.messages[0],
            "Debe seleccionar un puesto válido."
        )

        self.assertEqual(PapeletaSitio.objects.count(), 0)



    def test_procesar_solicitud_cirio_tradicional_fallo_tardio_no_deja_insignia_anulada(self):
        """
        Test: Atomicidad específica de “anular insignia” + error posterior (cirios)

        Given: existe insignia pendiente SOLICITADA.
        When: el flujo falla por una validación tardía (puesto de otro acto).
        Then: la insignia NO debe quedar ANULADA y no debe existir papeleta de cirio.
        """
        ahora_congelado = self.inicio_cirios + timezone.timedelta(hours=1)

        insignia_pendiente = PapeletaSitio.objects.create(
            hermano=self.hermano,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        with patch("django.utils.timezone.now", return_value=ahora_congelado):
            with self.assertRaises(ValidationError) as ctx:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano,
                    acto=self.acto,
                    puesto=self.puesto_otro_acto,
                    numero_registro_vinculado=None,
                )

        self.assertEqual(ctx.exception.messages[0], "No puede seleccionar un puesto de otro acto.")

        insignia_pendiente.refresh_from_db()
        self.assertEqual(insignia_pendiente.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertFalse(
            PapeletaSitio.objects.filter(
                hermano=self.hermano,
                acto=self.acto,
                es_solicitud_insignia=False
            ).exists()
        )