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

class ProcesarSolicitudCirioConVinculacionServiceTest(TestCase):
    def setUp(self):
        """
        Setup mínimo y reutilizable SOLO para tests de _procesar_vinculacion.

        Objetivo:
        - Tener 2 hermanos: "antiguo" (puede vincularse) y "nuevo" (objetivo).
        - Acto TRADICIONAL y que requiere papeleta.
        - Tipos y puestos coherentes para validar el matching por tipo y sección (Cristo/Virgen).
        - Papeleta del objetivo ya existente y activa (no ANULADA), y NO insignia.
        - Papeleta del solicitante (mi_papeleta) ya creada, con mi_puesto.
        - Cuotas pagadas hasta año anterior (para no ensuciar otros tests si llamas al flujo completo).
        """
        self.service = PapeletaSitioService()
        self.ahora = timezone.now()

        # ------------------------------------------------------------
        # Cuerpos (por si algún test usa flujo completo)
        # ------------------------------------------------------------
        self.cuerpo_nazarenos = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS
        )

        # ------------------------------------------------------------
        # Hermanos (create_user para evitar error de password en blanco)
        # ------------------------------------------------------------
        self.hermano_antiguo = Hermano.objects.create_user(
            dni="11111111A",
            username="11111111A",
            password="password",
            nombre="Antonio",
            primer_apellido="Antiguo",
            segundo_apellido="López",
            email="antiguo@example.com",
            telefono="600000001",
            estado_civil=Hermano.EstadoCivil.CASADO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1000,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1980-01-01",
            direccion="Calle A",
            codigo_postal="41001",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        self.hermano_nuevo = Hermano.objects.create_user(
            dni="22222222B",
            username="22222222B",
            password="password",
            nombre="Nicolás",
            primer_apellido="Nuevo",
            segundo_apellido="Pérez",
            email="nuevo@example.com",
            telefono="600000002",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=2000,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1990-01-01",
            direccion="Calle B",
            codigo_postal="41002",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        HermanoCuerpo.objects.create(
            hermano=self.hermano_antiguo,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 10,
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_nuevo,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=self.ahora.year - 2,
        )

        # ------------------------------------------------------------
        # Cuotas: pagadas hasta año anterior (por si se testea también el flujo completo)
        # ------------------------------------------------------------
        anio_actual = self.ahora.date().year
        for hermano in (self.hermano_antiguo, self.hermano_nuevo):
            Cuota.objects.create(
                hermano=hermano,
                anio=anio_actual - 1,
                tipo=Cuota.TipoCuota.ORDINARIA,
                descripcion=f"Cuota {anio_actual - 1}",
                importe="30.00",
                estado=Cuota.EstadoCuota.PAGADA,
                metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            )

        # ------------------------------------------------------------
        # Acto TRADICIONAL con papeleta
        # ------------------------------------------------------------
        self.tipo_acto = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True,
        )

        self.acto = Acto.objects.create(
            nombre="Estación de Penitencia",
            descripcion="Test vinculación",
            fecha=self.ahora + timedelta(days=30),
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            tipo_acto=self.tipo_acto,
            inicio_solicitud=self.ahora - timedelta(days=10),
            fin_solicitud=self.ahora - timedelta(days=5),
            inicio_solicitud_cirios=self.ahora - timedelta(days=2),
            fin_solicitud_cirios=self.ahora + timedelta(days=2),
        )

        # ------------------------------------------------------------
        # Tipos y puestos (Cirio) y control de sección (Cristo/Virgen)
        # ------------------------------------------------------------
        self.tipo_cirio = TipoPuesto.objects.create(
            nombre_tipo="CIRIO",
            es_insignia=False,
            solo_junta_gobierno=False,
        )

        self.mi_puesto_cirio_cristo = Puesto.objects.create(
            nombre="Cirio Cristo 1",
            acto=self.acto,
            tipo_puesto=self.tipo_cirio,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=True,
        )

        self.puesto_objetivo_cirio_cristo = Puesto.objects.create(
            nombre="Cirio Cristo 2",
            acto=self.acto,
            tipo_puesto=self.tipo_cirio,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=True,
        )

        self.puesto_objetivo_cirio_virgen = Puesto.objects.create(
            nombre="Cirio Virgen 1",
            acto=self.acto,
            tipo_puesto=self.tipo_cirio,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=False,
        )

        self.tipo_cruz = TipoPuesto.objects.create(
            nombre_tipo="CRUZ PENITENTE",
            es_insignia=False,
            solo_junta_gobierno=False,
        )
        self.mi_puesto_cruz_cristo = Puesto.objects.create(
            nombre="Cruz Cristo 1",
            acto=self.acto,
            tipo_puesto=self.tipo_cruz,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=True,
        )

        # ------------------------------------------------------------
        # Papeletas base para _procesar_vinculacion
        # ------------------------------------------------------------
        self.mi_papeleta = PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=self.mi_puesto_cirio_cristo,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ABCDEFGH",
        )

        self.papeleta_objetivo_ok = PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=self.puesto_objetivo_cirio_cristo,
            fecha_solicitud=self.ahora,
            codigo_verificacion="HGFEDCBA",
        )



    def test_procesar_vinculacion_valida_basica_asigna_vinculado_a(self):
        """
        Test: Vinculación válida básica

        Given:
        - Hermano A (antiguo) y Hermano B (nuevo)
        - Ambos tienen papeleta activa del mismo acto
        - Ambos solicitan el mismo tipo de puesto (CIRIO)
        - Ambos en la misma sección (cortejo_cristo igual)
        - B es más nuevo (A.numero_registro < B.numero_registro)
        When:
        - A solicita vincularse con B
        Then:
        - mi_papeleta.vinculado_a = hermano_objetivo (B)
        """
        hermano = self.hermano_antiguo
        acto = self.acto
        mi_papeleta = self.mi_papeleta
        mi_puesto = self.mi_puesto_cirio_cristo
        numero_objetivo = self.hermano_nuevo.numero_registro

        self.assertLess(hermano.numero_registro, self.hermano_nuevo.numero_registro)
        self.assertEqual(mi_papeleta.acto_id, acto.id)
        self.assertFalse(mi_papeleta.es_solicitud_insignia)
        self.assertEqual(mi_papeleta.puesto.tipo_puesto.nombre_tipo, "CIRIO")
        self.assertTrue(mi_puesto.cortejo_cristo)
        self.assertTrue(self.papeleta_objetivo_ok.puesto.cortejo_cristo)

        self.service._procesar_vinculacion(
            hermano=hermano,
            acto=acto,
            mi_papeleta=mi_papeleta,
            mi_puesto=mi_puesto,
            numero_objetivo=numero_objetivo,
        )

        mi_papeleta.refresh_from_db()
        self.assertIsNotNone(mi_papeleta.vinculado_a)
        self.assertEqual(mi_papeleta.vinculado_a_id, self.hermano_nuevo.id)

        self.papeleta_objetivo_ok.refresh_from_db()
        self.assertIsNone(self.papeleta_objetivo_ok.vinculado_a)



    def test_procesar_vinculacion_objetivo_con_papeleta_emitida_permitido(self):
        """
        Test: Objetivo con papeleta EMITIDA

        Given:
        - Hermano objetivo tiene papeleta activa en estado EMITIDA
        - Cumple el resto de condiciones (mismo acto, mismo tipo, misma sección, objetivo más nuevo, no insignia)
        When:
        - Hermano antiguo intenta vincularse al objetivo
        Then:
        - Permitido (la query excluye solo ANULADA), se asigna vinculado_a correctamente
        """
        self.papeleta_objetivo_ok.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
        self.papeleta_objetivo_ok.save(update_fields=["estado_papeleta"])

        hermano = self.hermano_antiguo
        acto = self.acto
        mi_papeleta = self.mi_papeleta
        mi_puesto = self.mi_puesto_cirio_cristo
        numero_objetivo = self.hermano_nuevo.numero_registro

        self.assertEqual(self.papeleta_objetivo_ok.estado_papeleta, PapeletaSitio.EstadoPapeleta.EMITIDA)
        self.assertNotEqual(self.papeleta_objetivo_ok.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)
        self.assertFalse(self.papeleta_objetivo_ok.es_solicitud_insignia)

        self.service._procesar_vinculacion(
            hermano=hermano,
            acto=acto,
            mi_papeleta=mi_papeleta,
            mi_puesto=mi_puesto,
            numero_objetivo=numero_objetivo,
        )

        mi_papeleta.refresh_from_db()
        self.assertEqual(mi_papeleta.vinculado_a_id, self.hermano_nuevo.id)



    def test_procesar_vinculacion_valida_en_virgen_permitido(self):
        """
        Test: Vinculación válida en Virgen

        Given:
        - Ambos puestos con cortejo_cristo=False
        - Mismo tipo de puesto (CIRIO)
        - Objetivo más nuevo
        Then:
        - Permitido: mi_papeleta.vinculado_a = hermano_objetivo
        """
        hermano = self.hermano_antiguo
        acto = self.acto
        numero_objetivo = self.hermano_nuevo.numero_registro

        self.mi_papeleta.puesto = self.puesto_objetivo_cirio_virgen
        self.mi_papeleta.save(update_fields=["puesto"])
        mi_puesto = self.puesto_objetivo_cirio_virgen

        self.papeleta_objetivo_ok.puesto = self.puesto_objetivo_cirio_virgen
        self.papeleta_objetivo_ok.save(update_fields=["puesto"])

        self.assertFalse(mi_puesto.cortejo_cristo)
        self.assertFalse(self.papeleta_objetivo_ok.puesto.cortejo_cristo)

        self.assertEqual(mi_puesto.tipo_puesto.nombre_tipo, "CIRIO")
        self.assertEqual(self.papeleta_objetivo_ok.puesto.tipo_puesto.nombre_tipo, "CIRIO")

        self.assertLess(self.hermano_antiguo.numero_registro, self.hermano_nuevo.numero_registro)

        self.service._procesar_vinculacion(
            hermano=hermano,
            acto=acto,
            mi_papeleta=self.mi_papeleta,
            mi_puesto=mi_puesto,
            numero_objetivo=numero_objetivo,
        )

        self.mi_papeleta.refresh_from_db()
        self.assertEqual(self.mi_papeleta.vinculado_a_id, self.hermano_nuevo.id)



    def test_procesar_vinculacion_valida_solicitante_pierde_antiguedad_permitido(self):
        """
        Test: Vinculación válida cuando el solicitante pierde antigüedad

        Given:
        - Hermano solicitante es el ANTIGUO (numero_registro menor)
        - Hermano objetivo es el NUEVO (numero_registro mayor)
        - Objetivo tiene papeleta activa del mismo acto, no ANULADA
        - Ambos tienen puesto seleccionado
        - Mismo tipo de puesto (ej: CIRIO)
        - Misma sección (cortejo_cristo igual)
        When:
        - El hermano antiguo se vincula al nuevo
        Then:
        - Permitido: mi_papeleta.vinculado_a queda apuntando al hermano objetivo.
        - (La "pérdida de antigüedad" es implícita, no hay un campo extra que verificar aquí)
        """

        hermano_antiguo = self.hermano_antiguo
        hermano_nuevo = self.hermano_nuevo

        self.assertLess(hermano_antiguo.numero_registro, hermano_nuevo.numero_registro)

        self.assertNotEqual(self.papeleta_objetivo_ok.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)
        self.assertFalse(self.papeleta_objetivo_ok.es_solicitud_insignia)
        self.assertIsNotNone(self.papeleta_objetivo_ok.puesto)

        self.assertEqual(self.mi_puesto_cirio_cristo.tipo_puesto.nombre_tipo, self.papeleta_objetivo_ok.puesto.tipo_puesto.nombre_tipo)
        self.assertEqual(self.mi_puesto_cirio_cristo.cortejo_cristo, self.papeleta_objetivo_ok.puesto.cortejo_cristo)

        self.service._procesar_vinculacion(
            hermano=hermano_antiguo,
            acto=self.acto,
            mi_papeleta=self.mi_papeleta,
            mi_puesto=self.mi_puesto_cirio_cristo,
            numero_objetivo=hermano_nuevo.numero_registro,
        )

        self.mi_papeleta.refresh_from_db()
        self.assertEqual(self.mi_papeleta.vinculado_a_id, hermano_nuevo.id)



    def test_procesar_vinculacion_acto_no_tradicional_lanza_error(self):
        """
        Test: Acto no TRADICIONAL

        Given: acto.modalidad != TRADICIONAL
        When: se intenta vincular
        Then: ValidationError("La vinculación solo está disponible en modalidad TRADICIONAL.")
        """
        self.acto.modalidad = Acto.ModalidadReparto.UNIFICADO
        self.acto.save(update_fields=["modalidad"])

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=self.hermano_nuevo.numero_registro,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            "La vinculación solo está disponible en modalidad TRADICIONAL."
        )



    def test_procesar_vinculacion_objetivo_no_existe_lanza_error(self):
        """
        Test: Hermano objetivo no existe

        Given: numero_registro_objetivo no corresponde a ningún hermano
        When: se intenta vincular
        Then: ValidationError("No existe hermano con Nº X.")
        """
        numero_inexistente = 999999

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_inexistente,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            f"No existe hermano con Nº {numero_inexistente}."
        )



    def test_procesar_vinculacion_consigo_mismo_lanza_error(self):
        """
        Test: Intentar vincularse consigo mismo

        Given:
        - El número de registro objetivo es el mismo que el del hermano solicitante
        When:
        - Se intenta realizar la vinculación
        Then:
        - Lanza ValidationError("No puedes vincularte contigo mismo.")
        """
        hermano = self.hermano_antiguo
        numero_objetivo = hermano.numero_registro

        self.assertEqual(hermano.numero_registro, numero_objetivo)

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=hermano,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            "No puedes vincularte contigo mismo."
        )



    def test_procesar_vinculacion_objetivo_sin_solicitud_activa_solo_anuladas_lanza_error(self):
        """
        Test: Hermano objetivo sin solicitud activa

        Given:
        - El hermano objetivo NO tiene ninguna papeleta activa para el acto
            (solo tiene papeletas ANULADAS)
        When:
        - El hermano antiguo intenta vincularse al objetivo
        Then:
        - ValidationError("El hermano Nº X no tiene solicitud activa.")
        """

        numero_objetivo = self.hermano_nuevo.numero_registro

        self.papeleta_objetivo_ok.estado_papeleta = PapeletaSitio.EstadoPapeleta.ANULADA
        self.papeleta_objetivo_ok.save(update_fields=["estado_papeleta"])

        self.assertFalse(
            PapeletaSitio.objects.filter(
                hermano=self.hermano_nuevo,
                acto=self.acto
            ).exclude(
                estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
            ).exists()
        )

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            f"El hermano Nº {numero_objetivo} no tiene solicitud activa."
        )



    def test_procesar_vinculacion_objetivo_solicita_insignia_por_flag_lanza_error(self):
        """
        Test: Hermano objetivo solicitando insignia (flag)

        Given:
        - La papeleta del objetivo tiene es_solicitud_insignia=True
        - (y sigue siendo activa, no ANULADA)
        When:
        - Se intenta vincular
        Then:
        - ValidationError("No puedes vincularte a un hermano que solicita Insignia.")
        """
        numero_objetivo = self.hermano_nuevo.numero_registro

        self.papeleta_objetivo_ok.es_solicitud_insignia = True
        self.papeleta_objetivo_ok.save(update_fields=["es_solicitud_insignia"])

        self.assertTrue(self.papeleta_objetivo_ok.es_solicitud_insignia)
        self.assertNotEqual(self.papeleta_objetivo_ok.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            "No puedes vincularte a un hermano que solicita Insignia."
        )



    def test_procesar_vinculacion_objetivo_con_puesto_insignia_lanza_error(self):
        """
        Test: Hermano objetivo con puesto insignia

        Given:
        - papeleta_objetivo.es_solicitud_insignia = False
        - pero papeleta_objetivo.puesto.tipo_puesto.es_insignia = True
        Then:
        - ValidationError("No puedes vincularte a un hermano que solicita Insignia.")
        """
        numero_objetivo = self.hermano_nuevo.numero_registro

        self.papeleta_objetivo_ok.es_solicitud_insignia = False
        self.papeleta_objetivo_ok.save(update_fields=["es_solicitud_insignia"])

        tipo_puesto_insignia = TipoPuesto.objects.create(
            nombre_tipo="INSIGNIA TEST",
            es_insignia=True,
            solo_junta_gobierno=False,
        )
        puesto_insignia = Puesto.objects.create(
            nombre="Vara Insignia Test",
            acto=self.acto,
            tipo_puesto=tipo_puesto_insignia,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=True,
        )

        self.papeleta_objetivo_ok.puesto = puesto_insignia
        self.papeleta_objetivo_ok.save(update_fields=["puesto"])

        self.assertFalse(self.papeleta_objetivo_ok.es_solicitud_insignia)
        self.assertTrue(self.papeleta_objetivo_ok.puesto.tipo_puesto.es_insignia)

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            "No puedes vincularte a un hermano que solicita Insignia."
        )



    def test_procesar_vinculacion_objetivo_sin_puesto_asignado_lanza_error(self):
        """
        Test: Hermano objetivo sin puesto asignado

        Given:
        - El hermano objetivo tiene papeleta activa para el acto (no ANULADA)
        - Pero su papeleta NO tiene puesto asignado (puesto=None)
        When:
        - El hermano antiguo intenta vincularse al objetivo
        Then:
        - ValidationError("El hermano Nº X no tiene puesto seleccionado.")
        """
        numero_objetivo = self.hermano_nuevo.numero_registro

        self.papeleta_objetivo_ok.puesto = None
        self.papeleta_objetivo_ok.save(update_fields=["puesto"])

        self.assertIsNone(self.papeleta_objetivo_ok.puesto)
        self.assertNotEqual(self.papeleta_objetivo_ok.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            f"El hermano Nº {numero_objetivo} no tiene puesto seleccionado."
        )



    def test_procesar_vinculacion_tipo_puesto_distinto_lanza_error(self):
        """
        Test: Tipo de puesto distinto

        Ejemplo:
        - Solicitante solicita CIRIO
        - Objetivo solicita CRUZ PENITENTE
        Resultado:
        - ValidationError("Ambos deben solicitar el mismo tipo de puesto (ej: ambos Cirio).")
        """
        numero_objetivo = self.hermano_nuevo.numero_registro

        puesto_objetivo_cruz = Puesto.objects.create(
            nombre="Cruz Objetivo",
            acto=self.acto,
            tipo_puesto=self.tipo_cruz,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=self.mi_puesto_cirio_cristo.cortejo_cristo,
        )

        self.papeleta_objetivo_ok.puesto = puesto_objetivo_cruz
        self.papeleta_objetivo_ok.save(update_fields=["puesto"])

        self.assertEqual(self.mi_puesto_cirio_cristo.tipo_puesto.nombre_tipo, "CIRIO")
        self.assertEqual(self.papeleta_objetivo_ok.puesto.tipo_puesto.nombre_tipo, "CRUZ PENITENTE")

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            "Ambos deben solicitar el mismo tipo de puesto (ej: ambos Cirio)."
        )



    def test_procesar_vinculacion_conflicto_seccion_cristo_vs_virgen_lanza_error(self):
        """
        Test: Conflicto de sección (Cristo vs Virgen)

        Given:
        - Mismo tipo de puesto (CIRIO)
        - Pero mi_puesto.cortejo_cristo != puesto_objetivo.cortejo_cristo
        When:
        - Se intenta vincular
        Then:
        - ValidationError("Conflicto de sección: Uno va en Cristo y otro en Virgen.")
        """
        numero_objetivo = self.hermano_nuevo.numero_registro

        self.assertTrue(self.mi_puesto_cirio_cristo.cortejo_cristo)

        self.papeleta_objetivo_ok.puesto = self.puesto_objetivo_cirio_virgen
        self.papeleta_objetivo_ok.save(update_fields=["puesto"])

        self.assertEqual(self.mi_puesto_cirio_cristo.tipo_puesto.nombre_tipo, "CIRIO")
        self.assertEqual(self.papeleta_objetivo_ok.puesto.tipo_puesto.nombre_tipo, "CIRIO")
        self.assertNotEqual(self.mi_puesto_cirio_cristo.cortejo_cristo, self.papeleta_objetivo_ok.puesto.cortejo_cristo)

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            "Conflicto de sección: Uno va en Cristo y otro en Virgen."
        )



    def test_procesar_vinculacion_nuevo_intenta_vincularse_al_antiguo_lanza_error(self):
        """
        Test: El nuevo intenta vincularse al antiguo

        Given:
        - Hermano solicitante es MÁS NUEVO que el objetivo:
            hermano.numero_registro > hermano_objetivo.numero_registro
        - Resto de condiciones OK (mismo acto, objetivo con papeleta activa, mismo tipo, misma sección)
        When:
        - El nuevo intenta vincularse al antiguo
        Then:
        - Lanza ValidationError con el mensaje esperado.
        """
        hermano_nuevo = self.hermano_nuevo
        hermano_antiguo = self.hermano_antiguo

        self.assertGreater(hermano_nuevo.numero_registro, hermano_antiguo.numero_registro)

        papeleta_objetivo_antiguo = self.mi_papeleta

        mi_papeleta_nuevo = PapeletaSitio.objects.create(
            hermano=hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=self.mi_puesto_cirio_cristo,
            fecha_solicitud=self.ahora,
            codigo_verificacion="AAAABBBB",
        )

        numero_objetivo = hermano_antiguo.numero_registro

        self.assertEqual(mi_papeleta_nuevo.puesto.tipo_puesto.nombre_tipo, papeleta_objetivo_antiguo.puesto.tipo_puesto.nombre_tipo)
        self.assertEqual(mi_papeleta_nuevo.puesto.cortejo_cristo, papeleta_objetivo_antiguo.puesto.cortejo_cristo)

        with self.assertRaises(ValidationError) as ctx:
            self.service._procesar_vinculacion(
                hermano=hermano_nuevo,
                acto=self.acto,
                mi_papeleta=mi_papeleta_nuevo,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.assertEqual(
            ctx.exception.messages[0],
            (
                f"Tú (Nº {hermano_nuevo.numero_registro}) eres más nuevo que el Nº {hermano_antiguo.numero_registro}. "
                "Solo el hermano antiguo puede vincularse al nuevo (perdiendo antigüedad)."
            )
        )



    def test_procesar_vinculacion_objetivo_con_multiples_papeletas_activas_comportamiento_no_determinista(self):
        """
        Test: Objetivo con múltiples papeletas activas (comportamiento NO determinista)

        Given:
        - El hermano objetivo tiene DOS papeletas activas para el mismo acto
        - Ambas NO están ANULADAS
        - Cada una tiene un puesto distinto (pero ambos válidos para vinculación)
        When:
        - Se intenta procesar la vinculación
        - El código usa `.first()` sin `order_by()`
        Then:
        - El resultado depende del orden interno de la query
        - Este test NO asegura un resultado concreto, solo detecta el riesgo
        """
        numero_objetivo = self.hermano_nuevo.numero_registro

        puesto_alternativo = Puesto.objects.create(
            nombre="Cirio alternativo",
            acto=self.acto,
            tipo_puesto=self.mi_puesto_cirio_cristo.tipo_puesto,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=self.mi_puesto_cirio_cristo.cortejo_cristo,
        )

        segunda_papeleta_objetivo = PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=False,
            puesto=puesto_alternativo,
            fecha_solicitud=self.ahora,
            codigo_verificacion="ZZZZ9999",
        )

        papeletas_activas = PapeletaSitio.objects.filter(
            hermano=self.hermano_nuevo,
            acto=self.acto
        ).exclude(
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
        )

        self.assertEqual(papeletas_activas.count(), 2)

        self.service._procesar_vinculacion(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            mi_papeleta=self.mi_papeleta,
            mi_puesto=self.mi_puesto_cirio_cristo,
            numero_objetivo=numero_objetivo,
        )

        self.mi_papeleta.refresh_from_db()

        self.assertIsNotNone(self.mi_papeleta.vinculado_a)
        self.assertEqual(self.mi_papeleta.vinculado_a, self.hermano_nuevo)



    def test_procesar_vinculacion_comparacion_por_nombre_tipo_permite_erroneamente_con_mock(self):
        """
        Test: Comparación por nombre_tipo (fragilidad) sin violar UNIQUE

        Dado:
        - El objetivo usa un TipoPuesto distinto en BD (ID distinto) con nombre distinto ("CIRIO_DUP")
        Cuando:
        - MOCKEAMOS el acceso a 'nombre_tipo' para que, en runtime, ese tipo "parezca" "CIRIO"
        Entonces:
        - La vinculación se permite (porque el servicio compara por nombre_tipo en vez de por id)
        """
        numero_objetivo = self.hermano_nuevo.numero_registro

        tipo_distinto = TipoPuesto.objects.create(
            nombre_tipo="CIRIO_DUP",
            es_insignia=False,
            solo_junta_gobierno=False,
        )

        puesto_objetivo_tipo_distinto = Puesto.objects.create(
            nombre="Cirio objetivo (tipo distinto)",
            acto=self.acto,
            tipo_puesto=tipo_distinto,
            disponible=True,
            numero_maximo_asignaciones=1,
            cortejo_cristo=self.mi_puesto_cirio_cristo.cortejo_cristo,
        )

        self.papeleta_objetivo_ok.puesto = puesto_objetivo_tipo_distinto
        self.papeleta_objetivo_ok.save(update_fields=["puesto"])

        self.assertNotEqual(self.mi_puesto_cirio_cristo.tipo_puesto_id, tipo_distinto.id)
        self.assertNotEqual(self.mi_puesto_cirio_cristo.tipo_puesto.nombre_tipo, tipo_distinto.nombre_tipo)

        original_getattribute = TipoPuesto.__getattribute__

        def fake_getattribute(obj, name):
            if name == "nombre_tipo" and getattr(obj, "id", None) == tipo_distinto.id:
                return "CIRIO"
            return original_getattribute(obj, name)

        with patch.object(TipoPuesto, "__getattribute__", fake_getattribute):
            self.service._procesar_vinculacion(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                mi_papeleta=self.mi_papeleta,
                mi_puesto=self.mi_puesto_cirio_cristo,
                numero_objetivo=numero_objetivo,
            )

        self.mi_papeleta.refresh_from_db()
        self.assertEqual(self.mi_papeleta.vinculado_a_id, self.hermano_nuevo.id)