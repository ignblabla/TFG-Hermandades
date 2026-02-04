import threading
import uuid
from django.db import IntegrityError, transaction, connection
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
from api.servicios.solicitud_cirio_tradicional import SolicitudCirioTradicionalService

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
        self.service = SolicitudCirioTradicionalService()
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



    def test_tradicional_solicitud_cirio_valida_ok(self):
        """
        Test POSITIVO:
        Solicitud válida de CIRIO en acto TRADICIONAL.

        Given:
            - Acto con tipo_acto.requiere_papeleta = True
            - modalidad = TRADICIONAL
            - Plazo de cirios vigente
            - Hermano en ALTA
            - Cuotas pagadas hasta año anterior
            - Cuerpo permitido (NAZARENOS)
            - Puesto de cirio disponible y del mismo acto
        When:
            - Se procesa la solicitud de cirio tradicional
        Then:
            - Se crea una PapeletaSitio
            - Estado = SOLICITADA
            - es_solicitud_insignia = False
            - Puesto asignado correctamente
            - Fecha de solicitud correcta
        """
        self.mi_papeleta.delete()

        now = timezone.now()

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
            )

        self.assertIsNotNone(papeleta.id)

        self.assertEqual(papeleta.hermano, self.hermano_antiguo)
        self.assertEqual(papeleta.acto, self.acto)

        self.assertEqual(papeleta.estado_papeleta,PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertFalse(papeleta.es_solicitud_insignia)
        self.assertEqual(papeleta.anio, self.acto.fecha.year)
        self.assertEqual(papeleta.fecha_solicitud, now)

        self.assertEqual(papeleta.puesto, self.mi_puesto_cirio_cristo)

        self.assertEqual(PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).count(), 1)



    def test_tradicional_acto_fechas_solicitud_cirios_correctas_ok(self):
        """
        Test POSITIVO:
        Acto TRADICIONAL con fechas de solicitud de cirios correctamente configuradas.

        Given:
            - Acto requiere papeleta
            - Modalidad TRADICIONAL
            - inicio_solicitud_cirios y fin_solicitud_cirios definidos
            - now está dentro del rango
        When:
            - Se procesa una solicitud de cirio tradicional
        Then:
            - No se lanza ValidationError por fechas
            - Se crea la papeleta correctamente
        """
        self.mi_papeleta.delete()

        now = timezone.now()

        self.assertLess(self.acto.inicio_solicitud_cirios, now)
        self.assertGreater(self.acto.fin_solicitud_cirios, now)

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
            )

        self.assertIsNotNone(papeleta.id)

        self.assertEqual(papeleta.estado_papeleta,PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertEqual(papeleta.fecha_solicitud, now)
        self.assertEqual(papeleta.puesto, self.mi_puesto_cirio_cristo)



    def test_tradicional_acto_futuro_con_cierre_solicitudes_antes_del_acto_ok(self):
        """
        Test POSITIVO:
        Acto en fecha futura con solicitudes de cirios que finalizan antes del acto.

        Given:
            - Acto TRADICIONAL
            - Fecha del acto en el futuro
            - fin_solicitud_cirios < fecha del acto
            - now dentro del plazo de cirios
        When:
            - Se procesa la solicitud de cirio tradicional
        Then:
            - La solicitud se procesa correctamente
            - Se crea la papeleta sin errores
        """
        self.mi_papeleta.delete()

        now = timezone.now()

        self.assertGreater(self.acto.fecha, now)
        self.assertLess(self.acto.fin_solicitud_cirios, self.acto.fecha)
        self.assertLess(self.acto.inicio_solicitud_cirios, now)
        self.assertGreater(self.acto.fin_solicitud_cirios, now)

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
            )

        self.assertIsNotNone(papeleta.id)

        self.assertEqual(papeleta.estado_papeleta,PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertEqual(papeleta.fecha_solicitud, now)
        self.assertEqual(papeleta.puesto, self.mi_puesto_cirio_cristo)
        self.assertFalse(papeleta.es_solicitud_insignia)



    def test_tradicional_acto_con_campos_completos_ok(self):
        """
        Test POSITIVO:
        Acto TRADICIONAL con todos los campos requeridos correctamente configurados.

        Given:
            - Acto requiere papeleta
            - Modalidad TRADICIONAL
            - Todas las fechas obligatorias presentes
            - Orden cronológico correcto
        When:
            - Se procesa una solicitud de cirio tradicional
        Then:
            - No se lanza ValidationError
            - Se crea la papeleta correctamente
        """
        self.mi_papeleta.delete()

        now = timezone.now()

        self.assertEqual(self.acto.modalidad, self.acto.ModalidadReparto.TRADICIONAL)
        self.assertTrue(self.acto.tipo_acto.requiere_papeleta)

        self.assertIsNotNone(self.acto.inicio_solicitud)
        self.assertIsNotNone(self.acto.fin_solicitud)
        self.assertIsNotNone(self.acto.inicio_solicitud_cirios)
        self.assertIsNotNone(self.acto.fin_solicitud_cirios)

        self.assertLess(self.acto.inicio_solicitud, self.acto.fin_solicitud)
        self.assertLess(self.acto.fin_solicitud, self.acto.inicio_solicitud_cirios)
        self.assertLess(self.acto.inicio_solicitud_cirios, self.acto.fin_solicitud_cirios)
        self.assertLess(self.acto.fin_solicitud_cirios, self.acto.fecha)

        self.assertLess(self.acto.inicio_solicitud_cirios, now)
        self.assertGreater(self.acto.fin_solicitud_cirios, now)

        with patch("django.utils.timezone.now", return_value=now):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_antiguo)
        self.assertEqual(papeleta.acto, self.acto)

        self.assertEqual(papeleta.estado_papeleta,PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertFalse(papeleta.es_solicitud_insignia)
        self.assertEqual(papeleta.fecha_solicitud, now)
        self.assertEqual(papeleta.puesto, self.mi_puesto_cirio_cristo)



    def test_tradicional_error_acto_none(self):
        """
        Test NEGATIVO:
        El acto es None.

        Given:
            - acto = None
        When:
            - Se procesa una solicitud de cirio tradicional
        Then:
            - Se lanza ValidationError
            - No se crea ninguna papeleta
        """
        self.mi_papeleta.delete()

        with self.assertRaises(ValidationError):
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=None,
                puesto=self.mi_puesto_cirio_cristo,
            )



    def test_procesar_solicitud_cirio_acto_sin_tipo_acto_error(self):
        """
        Test: Error al procesar solicitud si el acto no tiene tipo_acto.

        Given: Un acto creado manualmente (sin save() para evitar validaciones de modelo o 
            usando update) que tiene el campo tipo_acto_id como None.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje de error indica que el tipo de acto es obligatorio.
        """
        acto_invalido = self.acto
        acto_invalido.tipo_acto = None

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=acto_invalido,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIn('tipo_acto', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['tipo_acto'][0], 
            "El tipo de acto es obligatorio."
        )



    def test_tradicional_solicitud_cirio_error_si_acto_no_requiere_papeleta(self):
        """
        Test: Error al solicitar cirio en un acto que no requiere papeleta.

        Given: Un hermano en ALTA y un acto de modalidad TRADICIONAL, 
            pero cuyo tipo_acto tiene requiere_papeleta = False.
        When: Se intenta procesar la solicitud de cirio tradicional.
        Then: Se lanza una ValidationError.
            El mensaje de error indica que el acto no admite solicitudes de papeleta.
        """
        self.tipo_acto.requiere_papeleta = False
        self.tipo_acto.save()
        
        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        expected_error = f"El acto '{self.acto.nombre}' no admite solicitudes de papeleta."
        self.assertIn(expected_error, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_modalidad_incorrecta(self):
        """
        Test: Error al procesar solicitud si la modalidad del acto no es TRADICIONAL.

        Given: Un acto con modalidad UNIFICADO.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que el proceso es exclusivo para actos de modalidad TRADICIONAL.
        """
        Acto.objects.filter(pk=self.acto.pk).update(modalidad=Acto.ModalidadReparto.UNIFICADO)
        self.acto.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIn("Este proceso es exclusivo para actos de modalidad TRADICIONAL.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_sin_inicio_solicitud(self):
        """
        Test: Error al procesar solicitud si no está configurado el inicio de solicitud de cirios.

        Given: Un acto TRADICIONAL donde inicio_solicitud_cirios es None.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que el plazo de cirios no está configurado en el acto.
        """
        Acto.objects.filter(pk=self.acto.pk).update(inicio_solicitud_cirios=None)
        self.acto.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIn("El plazo de cirios no está configurado en el acto.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_sin_fin_solicitud(self):
        """
        Test: Error al procesar solicitud si no está configurado el fin de solicitud de cirios.

        Given: Un acto TRADICIONAL donde fin_solicitud_cirios es None.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que el plazo de cirios no está configurado en el acto.
        """

        Acto.objects.filter(pk=self.acto.pk).update(fin_solicitud_cirios=None)
        self.acto.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIn("El plazo de cirios no está configurado en el acto.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_plazos_invertidos(self):
        """
        Test: Error al procesar solicitud si el inicio de cirios es posterior al fin.

        Given: Un acto TRADICIONAL donde inicio_solicitud_cirios (ej. mañana) 
            es posterior a fin_solicitud_cirios (ej. ayer).
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            Como 'ahora' no puede estar entre el futuro y el pasado, 
            el service detecta que el plazo no ha comenzado o ha finalizado.
        """
        Acto.objects.filter(pk=self.acto.pk).update(
            inicio_solicitud_cirios=self.ahora + timedelta(days=1),
            fin_solicitud_cirios=self.ahora - timedelta(days=1)
        )
        self.acto.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIn("El plazo de solicitud de cirios aún no ha comenzado.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_plazo_inicio_tras_acto(self):
        """
        Test: Error al procesar solicitud si el inicio de cirios es igual o posterior al acto.

        Given: Un acto cuya fecha es 'hoy' y el inicio de solicitudes de cirios
            se configura para 'mañana' (posterior al acto).
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El servicio detecta que el plazo aún no ha comenzado (o ha finalizado
            dependiendo del 'ahora' del test).
        """
        fecha_del_acto = self.ahora + timedelta(days=1)
        inicio_invalido = fecha_del_acto + timedelta(hours=1)
        fin_invalido = inicio_invalido + timedelta(days=1)

        Acto.objects.filter(pk=self.acto.pk).update(
            fecha=fecha_del_acto,
            inicio_solicitud_cirios=inicio_invalido,
            fin_solicitud_cirios=fin_invalido
        )
        self.acto.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIn("El plazo de solicitud de cirios aún no ha comenzado.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_fin_tras_fecha_acto(self):
        """
        Test: Error al procesar solicitud si el fin de cirios es posterior al acto.

        Given: Un acto que se celebra 'hoy' y un plazo de fin de cirios configurado
            para 'mañana' (posterior al acto).
        When: Se llama al servicio procesar_solicitud_cirio_tradicional en un momento
            donde el acto ya ha pasado pero el plazo sigue "abierto" teóricamente.
        Then: Se lanza una ValidationError.
            El mensaje indica que el plazo ha finalizado (porque el service 
            valida el momento 'ahora' contra los límites).
        """
        momento_acto = self.ahora - timedelta(hours=1)
        fin_invalido = self.ahora + timedelta(hours=5)

        Acto.objects.filter(pk=self.acto.pk).update(
            fecha=momento_acto,
            fin_solicitud_cirios=fin_invalido
        )
        self.acto.refresh_from_db()
        
        with self.assertRaises(ValidationError) as cm:
            pasado_mañana = self.ahora + timedelta(days=2)
            with patch("django.utils.timezone.now", return_value=pasado_mañana):
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        self.assertIn("El plazo de solicitud de cirios ha finalizado.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_exito(self):
        """
        Test: Solicitud de cirio exitosa dentro del plazo legal.

        Given: Un hermano en ALTA, al corriente de cuotas y con cuerpo nazareno.
            Un acto TRADICIONAL con plazos de cirios abiertos.
            Un momento 'ahora' que cae justo en medio del plazo de cirios.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se crea una PapeletaSitio en la base de datos.
            - El estado es SOLICITADA.
            - El puesto es el solicitado.
            - es_solicitud_insignia es False.
            - La fecha_solicitud coincide con el 'ahora' simulado.
        """ 
        self.mi_papeleta.delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_antiguo)
        self.assertEqual(papeleta.acto, self.acto)
        self.assertEqual(papeleta.puesto, self.mi_puesto_cirio_cristo)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(papeleta.es_solicitud_insignia)

        self.assertEqual(papeleta.fecha_solicitud, self.ahora)
        self.assertEqual(papeleta.anio, self.acto.fecha.year)
        self.assertTrue(len(papeleta.codigo_verificacion) > 0)

        self.assertTrue(PapeletaSitio.objects.filter(pk=papeleta.pk).exists())



    def test_procesar_solicitud_cirio_tradicional_error_antes_de_plazo(self):
        """
        Test: Error al solicitar cirio antes de que abra el plazo.

        Given: Un acto con inicio_solicitud_cirios en el futuro.
            Un momento 'ahora' anterior a dicho inicio.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que el plazo aún no ha comenzado.
        """

        inicio_plazo = self.ahora + timedelta(days=2)
        fin_plazo = self.ahora + timedelta(days=5)

        Acto.objects.filter(pk=self.acto.pk).update(
            inicio_solicitud_cirios=inicio_plazo,
            fin_solicitud_cirios=fin_plazo
        )
        self.acto.refresh_from_db()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        self.assertIn("El plazo de solicitud de cirios aún no ha comenzado.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_despues_de_plazo(self):
        """
        Test: Error al solicitar cirio una vez cerrado el plazo.

        Given: Un acto con fin_solicitud_cirios en el pasado.
            Un momento 'ahora' posterior a dicho cierre.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que el plazo ha finalizado.
        """
        inicio_plazo = self.ahora - timedelta(days=5)
        fin_plazo = self.ahora - timedelta(days=1)

        Acto.objects.filter(pk=self.acto.pk).update(
            inicio_solicitud_cirios=inicio_plazo,
            fin_solicitud_cirios=fin_plazo
        )
        self.acto.refresh_from_db()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        self.assertIn("El plazo de solicitud de cirios ha finalizado.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_inicio_solicitud_nulo(self):
        """
        Test: Error si el inicio del plazo de cirios es nulo.

        Given: Un acto TRADICIONAL donde inicio_solicitud_cirios es None.
        When: Se intenta procesar la solicitud.
        Then: Se lanza una ValidationError indicando que el plazo no está configurado.
        """
        Acto.objects.filter(pk=self.acto.pk).update(inicio_solicitud_cirios=None)
        self.acto.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )
            
        self.assertIn("El plazo de cirios no está configurado en el acto.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_fin_solicitud_nulo(self):
        """
        Test: Error si el fin del plazo de cirios es nulo.

        Given: Un acto TRADICIONAL donde fin_solicitud_cirios es None.
        When: Se intenta procesar la solicitud.
        Then: Se lanza una ValidationError indicando que el plazo no está configurado.
        """
        Acto.objects.filter(pk=self.acto.pk).update(
            inicio_solicitud_cirios=self.ahora - timedelta(days=1),
            fin_solicitud_cirios=None
        )
        self.acto.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )
            
        self.assertIn("El plazo de cirios no está configurado en el acto.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_hermano_en_alta_ok(self):
        """
        Test: Un hermano en estado ALTA puede solicitar papeleta.

        Given: Un hermano cuyo estado_hermano es ALTA.
            El resto de condiciones (plazos, cuotas, cuerpo) son correctas.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito y se crea la PapeletaSitio.
        """
        self.hermano_antiguo.estado_hermano = Hermano.EstadoHermano.ALTA
        self.hermano_antiguo.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano.estado_hermano, Hermano.EstadoHermano.ALTA)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)



    def test_procesar_solicitud_cirio_tradicional_cuotas_al_dia_ok(self):
        """
        Test: Hermano al corriente de pago (todas las cuotas pagadas hasta el año anterior).

        Given: Un hermano con historial de cuotas.
            Todas las cuotas de años anteriores tienen estado PAGADA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito y se crea la PapeletaSitio.
        """
        self.hermano_antiguo.cuotas.all().delete()
        
        anio_actual = self.ahora.year
        Cuota.objects.create(
            hermano=self.hermano_antiguo,
            anio=anio_actual - 1,
            tipo=Cuota.TipoCuota.ORDINARIA,
            importe="30.00",
            estado=Cuota.EstadoCuota.PAGADA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        estados_deuda = [Cuota.EstadoCuota.PENDIENTE, Cuota.EstadoCuota.DEVUELTA]
        deuda_existente = self.hermano_antiguo.cuotas.filter(
            anio__lt=anio_actual,
            estado__in=estados_deuda
        ).exists()
        self.assertFalse(deuda_existente)



    def test_procesar_solicitud_cirio_tradicional_historial_completo_ok(self):
        """
        Test: Hermano con historial de cuotas de varios años, todas correctas.

        Given: Un hermano con cuotas registradas de los últimos 3 años.
            Todas las cuotas anteriores al año actual están PAGADAS o EXENTAS.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito.
        """
        self.hermano_antiguo.cuotas.all().delete()
        anio_actual = self.ahora.year

        for i in range(1, 4):
            Cuota.objects.create(
                hermano=self.hermano_antiguo,
                anio=anio_actual - i,
                tipo=Cuota.TipoCuota.ORDINARIA,
                importe="30.00",
                estado=Cuota.EstadoCuota.PAGADA if i != 2 else Cuota.EstadoCuota.EXENTO,
                metodo_pago=Cuota.MetodoPago.DOMICILIACION,
            )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertEqual(self.hermano_antiguo.cuotas.filter(anio__lt=anio_actual).count(), 3)



    def test_procesar_solicitud_cirio_tradicional_cuerpos_permitidos_ok(self):
        """
        Test: Hermano perteneciente solo a cuerpos permitidos puede solicitar.

        Given: Un hermano que pertenece a 'NAZARENOS' y 'JUVENTUD' (ambos permitidos).
            No pertenece a ningún cuerpo restringido (como COSTALEROS).
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito y se crea la PapeletaSitio.
        """
        self.hermano_antiguo.pertenencias_cuerpos.all().delete()
        
        cuerpo_juventud = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUVENTUD
        )[0]
        
        HermanoCuerpo.objects.create(
            hermano=self.hermano_antiguo, 
            cuerpo=self.cuerpo_nazarenos, 
            anio_ingreso=2020
        )
        HermanoCuerpo.objects.create(
            hermano=self.hermano_antiguo, 
            cuerpo=cuerpo_juventud, 
            anio_ingreso=2022
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        cuerpos_actuales = set(self.hermano_antiguo.cuerpos.values_list('nombre_cuerpo', flat=True))
        cuerpos_permitidos = {
            CuerpoPertenencia.NombreCuerpo.NAZARENOS.value,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA.value,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD.value,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL.value,
            CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value,
        }
        self.assertTrue(cuerpos_actuales.issubset(cuerpos_permitidos))



    def test_procesar_solicitud_cirio_tradicional_sin_cuerpos_asignados_ok(self):
        """
        Test: Hermano sin cuerpos asignados (caso permitido por defecto).

        Given: Un hermano que no tiene registros en HermanoCuerpo.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito y se crea la PapeletaSitio.
            El service no lanza ValidationError al no haber cuerpos que validar.
        """
        self.hermano_antiguo.pertenencias_cuerpos.all().delete()

        cuerpos_actuales = self.hermano_antiguo.cuerpos.all()
        self.assertEqual(cuerpos_actuales.count(), 0)

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        
        self.assertEqual(papeleta.hermano.cuerpos.count(), 0)



    def test_procesar_solicitud_cirio_tradicional_error_hermano_en_baja(self):
        """
        Test: Un hermano en estado BAJA no puede solicitar papeleta.

        Given: Un hermano cuyo estado_hermano es BAJA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que solo los hermanos en ALTA pueden solicitar.
        """

        self.hermano_antiguo.estado_hermano = Hermano.EstadoHermano.BAJA
        self.hermano_antiguo.fecha_baja_corporacion = self.ahora.date()
        self.hermano_antiguo.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        self.assertIn("Solo los hermanos en estado ALTA pueden solicitar papeleta.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_hermano_pendiente_ingreso(self):
        """
        Test: Un hermano en estado PENDIENTE_INGRESO no puede solicitar papeleta.

        Given: Un hermano cuyo estado_hermano es PENDIENTE_INGRESO.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que solo los hermanos en ALTA pueden solicitar.
        """
        self.hermano_antiguo.estado_hermano = Hermano.EstadoHermano.PENDIENTE_INGRESO
        self.hermano_antiguo.numero_registro = None 
        self.hermano_antiguo.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        self.assertIn("Solo los hermanos en estado ALTA pueden solicitar papeleta.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_cuota_pendiente_anterior(self):
        """
        Test: Error al solicitar si existe una cuota PENDIENTE de años anteriores.

        Given: Un hermano con una cuota del año pasado en estado PENDIENTE.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica exactamente el año de la deuda y pide contactar con mayordomía.
        """
        self.hermano_antiguo.cuotas.all().delete()

        anio_deuda = self.ahora.year - 1
        Cuota.objects.create(
            hermano=self.hermano_antiguo,
            anio=anio_deuda,
            tipo=Cuota.TipoCuota.ORDINARIA,
            descripcion=f"Cuota {anio_deuda}",
            importe="30.00",
            estado=Cuota.EstadoCuota.PENDIENTE,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = (
            f"Consta una cuota pendiente o devuelta del año {anio_deuda}. "
            f"Por favor, contacte con mayordomía para regularizar su situación."
        )
        
        self.assertEqual(mensaje_esperado, str(cm.exception.messages[0]))



    def test_procesar_solicitud_cirio_tradicional_error_cuota_devuelta_anterior(self):
        """
        Test: Error al solicitar si existe una cuota DEVUELTA de años anteriores.

        Given: Un hermano con una cuota de hace 2 años en estado DEVUELTA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError con el mensaje de deuda de mayordomía.
        """
        self.hermano_antiguo.cuotas.all().delete()

        anio_deuda = self.ahora.year - 2
        Cuota.objects.create(
            hermano=self.hermano_antiguo,
            anio=anio_deuda,
            tipo=Cuota.TipoCuota.ORDINARIA,
            importe="30.00",
            estado=Cuota.EstadoCuota.DEVUELTA,
            metodo_pago=Cuota.MetodoPago.DOMICILIACION,
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = (
            f"Consta una cuota pendiente o devuelta del año {anio_deuda}. "
            f"Por favor, contacte con mayordomía para regularizar su situación."
        )
        
        self.assertEqual(mensaje_esperado, str(cm.exception.messages[0]))



    def test_procesar_solicitud_cirio_tradicional_error_sin_historial_cuotas(self):
        """
        Test: Error si el hermano no tiene cuotas registradas hasta el año anterior.

        Given: Un hermano que no tiene ningún objeto Cuota en la base de datos.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje indica que no constan cuotas registradas.
        """

        self.hermano_antiguo.cuotas.all().delete()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        anio_limite = self.ahora.year - 1
        mensaje_esperado = f"No constan cuotas registradas hasta el año {anio_limite}."
        
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_cuerpo_no_permitido(self):
        """
        Test: Error al solicitar si el hermano pertenece a un cuerpo no apto.

        Given: Un hermano que pertenece al cuerpo de COSTALEROS.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje lista los cuerpos no aptos que bloquean la solicitud.
        """
        self.hermano_antiguo.pertenencias_cuerpos.all().delete()

        cuerpo_costaleros = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )[0]

        HermanoCuerpo.objects.create(
            hermano=self.hermano_antiguo,
            cuerpo=cuerpo_costaleros,
            anio_ingreso=self.ahora.year - 5
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        expected_msg = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: COSTALEROS"
        self.assertIn(expected_msg, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_mezcla_cuerpos_permitidos_y_no_permitidos(self):
        """
        Test: Error si el hermano tiene cuerpos permitidos pero también uno NO permitido.

        Given: Un hermano que es 'NAZARENO' (permitido) pero también 'COSTALERO' (no permitido).
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError.
            El mensaje debe señalar específicamente el cuerpo no apto (COSTALEROS).
        """
        self.hermano_antiguo.pertenencias_cuerpos.all().delete()

        cuerpo_nazareno = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS
        )[0]
        cuerpo_costalero = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )[0]

        HermanoCuerpo.objects.create(hermano=self.hermano_antiguo, cuerpo=cuerpo_nazareno, anio_ingreso=2020)
        HermanoCuerpo.objects.create(hermano=self.hermano_antiguo, cuerpo=cuerpo_costalero, anio_ingreso=2024)

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: COSTALEROS"
        self.assertIn(mensaje_esperado, str(cm.exception))
        self.assertNotIn("NAZARENOS", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_puesto_valido_ok(self):
        """
        Test: Solicitud exitosa con puesto válido, disponible y del acto correcto.

        Given: Un puesto que pertenece al self.acto.
            El puesto tiene disponible=True.
            El puesto es de tipo CIRIO (no es insignia).
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito y el puesto queda asignado a la papeleta.
        """
        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.acto = self.acto
        self.mi_puesto_cirio_cristo.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.puesto, self.mi_puesto_cirio_cristo)
        self.assertEqual(papeleta.puesto.acto, self.acto)
        self.assertTrue(papeleta.puesto.disponible)
        self.assertFalse(papeleta.puesto.tipo_puesto.es_insignia)



    def test_procesar_solicitud_cirio_tradicional_puesto_no_insignia_ok(self):
        """
        Test: Un puesto que NO es insignia debe procesarse correctamente.

        Given: Un TipoPuesto con es_insignia=False.
            Un hermano apto y un acto en periodo de solicitud.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se crea la PapeletaSitio exitosamente.
        """

        self.mi_puesto_cirio_cristo.tipo_puesto.es_insignia = False
        self.mi_puesto_cirio_cristo.tipo_puesto.save()

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertFalse(papeleta.puesto.tipo_puesto.es_insignia)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)



    def test_procesar_solicitud_cirio_tradicional_puesto_no_exclusivo_jg_ok(self):
        """
        Test: Un hermano de base puede solicitar un puesto que NO es exclusivo de la JG.

        Given: Un hermano que NO pertenece al cuerpo de JUNTA_GOBIERNO.
            Un puesto cuyo tipo_puesto tiene solo_junta_gobierno=False.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito y se crea la PapeletaSitio.
        """

        self.hermano_antiguo.pertenencias_cuerpos.filter(
            cuerpo__nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        ).delete()

        self.mi_puesto_cirio_cristo.tipo_puesto.solo_junta_gobierno = False
        self.mi_puesto_cirio_cristo.tipo_puesto.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertFalse(papeleta.puesto.tipo_puesto.solo_junta_gobierno)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)



    def test_procesar_solicitud_cirio_tradicional_puesto_exclusivo_jg_por_miembro_jg_ok(self):
        """
        Test: Un miembro de la Junta de Gobierno puede solicitar un puesto exclusivo para ellos.

        Given: Un hermano que pertenece al cuerpo de JUNTA_GOBIERNO.
            Un puesto cuyo tipo_puesto tiene solo_junta_gobierno=True.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La solicitud se procesa con éxito y se crea la PapeletaSitio.
        """

        cuerpo_jg, _ = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )
        HermanoCuerpo.objects.get_or_create(
            hermano=self.hermano_antiguo,
            cuerpo=cuerpo_jg,
            anio_ingreso=self.ahora.year
        )

        self.mi_puesto_cirio_cristo.tipo_puesto.solo_junta_gobierno = True
        self.mi_puesto_cirio_cristo.tipo_puesto.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)
        self.assertTrue(papeleta.puesto.tipo_puesto.solo_junta_gobierno)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        cuerpos_hermano = self.hermano_antiguo.cuerpos.values_list('nombre_cuerpo', flat=True)
        self.assertIn(CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value, cuerpos_hermano)



    def test_procesar_solicitud_cirio_tradicional_error_puesto_none(self):
        """
        Test: Error al intentar procesar una solicitud con puesto nulo.

        Given: Un parámetro puesto=None enviado al servicio.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError indicando que debe seleccionar un puesto válido.
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=None
                )

        self.assertIn("Debe seleccionar un puesto válido.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_puesto_pertenece_a_otro_acto(self):
        """
        Test: Error si el puesto no pertenece al acto de la solicitud.

        Given: Un acto A (el de la solicitud) y un acto B (distinto).
            Un puesto que está asociado al acto B.
        When: Se intenta procesar la solicitud para el acto A usando el puesto del acto B.
        Then: Se lanza una ValidationError con mensaje genérico de pertenencia.
        """
        otro_acto = Acto.objects.create(
            nombre="Acto Secundario Diferente",
            descripcion="Descripción del acto ajeno",
            fecha=self.ahora + timedelta(days=60),
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            inicio_solicitud=self.ahora - timedelta(days=10),
            fin_solicitud=self.ahora - timedelta(days=5),
            inicio_solicitud_cirios=self.ahora - timedelta(days=2),
            fin_solicitud_cirios=self.ahora + timedelta(days=2),
        )

        puesto_ajeno = Puesto.objects.create(
            nombre="Cirio de Prueba Ajeno",
            acto=otro_acto, 
            tipo_puesto=self.mi_puesto_cirio_cristo.tipo_puesto,
            disponible=True
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=puesto_ajeno
                )

        self.assertIn("El puesto no pertenece a este acto.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_puesto_es_insignia(self):
        """
        Test: Error al intentar solicitar un puesto marcado como insignia.

        Given: Un puesto cuyo tipo de puesto tiene es_insignia=True.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError con el mensaje correspondiente.
        """
        tipo_insignia = TipoPuesto.objects.create(
            nombre_tipo="Vara de Acompañamiento",
            es_insignia=True,
            solo_junta_gobierno=False
        )

        puesto_insignia = Puesto.objects.create(
            nombre="Vara 1 - Presidencia Cristo",
            acto=self.acto,
            tipo_puesto=tipo_insignia,
            disponible=True
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=puesto_insignia
                )

        self.assertIn("es una insignia", str(cm.exception).lower())
        self.assertIn("no puede solicitarse", str(cm.exception).lower())



    def test_procesar_solicitud_cirio_tradicional_error_puesto_no_disponible(self):
        """
        Test: Error si el puesto tiene el flag disponible en False.

        Given: Un puesto que pertenece al acto correcto pero disponible=False.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError con el nombre del puesto.
        """
        self.mi_puesto_cirio_cristo.disponible = False
        self.mi_puesto_cirio_cristo.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = f"El puesto '{self.mi_puesto_cirio_cristo.nombre}' no está marcado como disponible."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_puesto_exclusivo_jg_solicitado_por_hermano_base(self):
        """
        Test: Un hermano que no es de la Junta no puede pedir puestos exclusivos (solo_junta_gobierno=True).

        Given: Un hermano sin pertenencia al cuerpo JUNTA_GOBIERNO.
            Un puesto cuyo tipo_puesto tiene solo_junta_gobierno=True.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError de restricción de acceso.
        """
        self.hermano_antiguo.pertenencias_cuerpos.filter(
            cuerpo__nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        ).delete()

        self.mi_puesto_cirio_cristo.tipo_puesto.solo_junta_gobierno = True
        self.mi_puesto_cirio_cristo.tipo_puesto.save()

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = f"El puesto '{self.mi_puesto_cirio_cristo.nombre}' es exclusivo para la Junta de Gobierno."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_puesto_tipo_insignia(self):
        """
        Test: Error al intentar solicitar una Insignia en el flujo de Cirios.

        Given: Un puesto cuyo TipoPuesto tiene es_insignia=True.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError con el mensaje dinámico del nombre del puesto.
        """
        tipo_insignia = TipoPuesto.objects.create(
            nombre_tipo="ESTANDARTE",
            es_insignia=True,
            solo_junta_gobierno=False
        )

        puesto_insignia = Puesto.objects.create(
            nombre="Estandarte Corporativo",
            acto=self.acto,
            tipo_puesto=tipo_insignia,
            disponible=True
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=puesto_insignia
                )

        mensaje_esperado = f"El puesto '{puesto_insignia.nombre}' es una Insignia. No puede solicitarse en este formulario."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_sin_papeletas_previas_ok(self):
        """
        Test: Creación exitosa cuando el hermano no tiene registros previos.

        Given: Un hermano apto y un puesto disponible.
            No existen PapeletaSitio previas para este hermano y acto.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se crea una nueva PapeletaSitio.
            El estado de la papeleta es SOLICITADA.
        """

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        self.mi_puesto_cirio_cristo.tipo_puesto.es_insignia = False
        self.mi_puesto_cirio_cristo.tipo_puesto.save()
        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id)

        self.assertEqual(papeleta.hermano, self.hermano_antiguo)
        self.assertEqual(papeleta.puesto, self.mi_puesto_cirio_cristo)

        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertEqual(PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).count(), 1)



    def test_procesar_solicitud_cirio_tradicional_con_papeleta_anulada_ok(self):
        """
        Test: Un hermano con una papeleta ANULADA puede solicitar una nueva.

        Given: Una PapeletaSitio previa para el hermano y acto en estado ANULADA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se crea una SEGUNDA PapeletaSitio en estado SOLICITADA.
            El sistema no bloquea la petición por duplicidad.
        """
        self.mi_papeleta.delete()

        PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            puesto=self.mi_puesto_cirio_cristo,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
            fecha_solicitud=self.ahora - timedelta(days=1),
            anio=self.ahora.year
        )

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(nueva_papeleta.id)
        self.assertEqual(nueva_papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        total_papeletas = PapeletaSitio.objects.filter(
            hermano=self.hermano_antiguo, 
            acto=self.acto
        ).count()
        self.assertEqual(total_papeletas, 2)



    def test_procesar_solicitud_cirio_tradicional_con_papeleta_no_asignada_ok(self):
        """
        Test: Un hermano con una papeleta NO_ASIGNADA puede realizar una nueva solicitud.

        Given: Una PapeletaSitio previa en estado NO_ASIGNADA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se crea una SEGUNDA PapeletaSitio en estado SOLICITADA.
        """
        self.mi_papeleta.delete()

        PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            puesto=self.mi_puesto_cirio_cristo,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.NO_ASIGNADA,
            fecha_solicitud=self.ahora - timedelta(days=5),
            anio=self.ahora.year
        )

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(nueva_papeleta.id)
        self.assertEqual(nueva_papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        total = PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).count()
        self.assertEqual(total, 2)



    def test_procesar_solicitud_cirio_tradicional_anula_insignia_previa_ok(self):
        """
        Test: Al solicitar un cirio, se debe anular la solicitud de insignia previa.

        Given: Una PapeletaSitio previa con es_solicitud_insignia=True y estado SOLICITADA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: La papeleta de insignia pasa a estado ANULADA.
            Se crea una nueva PapeletaSitio para el cirio en estado SOLICITADA.
        """

        papeleta_insignia = self.mi_papeleta 
        papeleta_insignia.es_solicitud_insignia = True
        papeleta_insignia.estado_papeleta = PapeletaSitio.EstadoPapeleta.SOLICITADA
        papeleta_insignia.save()

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta_cirio = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(nueva_papeleta_cirio.id)
        self.assertEqual(nueva_papeleta_cirio.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertFalse(nueva_papeleta_cirio.es_solicitud_insignia)

        papeleta_insignia.refresh_from_db()
        self.assertEqual(papeleta_insignia.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)

        total = PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).count()
        self.assertEqual(total, 2)



    def test_procesar_solicitud_cirio_tradicional_error_insignia_ya_emitida(self):
        """
        Test: Error si el hermano intenta pedir un cirio teniendo ya una insignia EMITIDA.

        Given: Una PapeletaSitio previa con es_solicitud_insignia=True y estado EMITIDA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError impidiendo la nueva solicitud.
        """
        papeleta_emitida = self.mi_papeleta 
        papeleta_emitida.es_solicitud_insignia = True
        papeleta_emitida.estado_papeleta = PapeletaSitio.EstadoPapeleta.EMITIDA
        papeleta_emitida.save()

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        self.assertIn("Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente.", str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_insignia_ya_recogida(self):
        """
        Test: Error si el hermano intenta pedir un cirio teniendo ya una insignia RECOGIDA.

        Given: Una PapeletaSitio previa con es_solicitud_insignia=True y estado RECOGIDA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError impidiendo la nueva solicitud.
        """
        papeleta_recogida = self.mi_papeleta 
        papeleta_recogida.es_solicitud_insignia = True
        papeleta_recogida.estado_papeleta = PapeletaSitio.EstadoPapeleta.RECOGIDA
        papeleta_recogida.save()

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_insignia_ya_leida(self):
        """
        Test: Error si el hermano intenta pedir un cirio teniendo ya una insignia LEIDA.

        Given: Una PapeletaSitio previa con es_solicitud_insignia=True y estado LEIDA.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se lanza una ValidationError impidiendo la nueva solicitud.
        """
        papeleta_leida = self.mi_papeleta 
        papeleta_leida.es_solicitud_insignia = True
        papeleta_leida.estado_papeleta = PapeletaSitio.EstadoPapeleta.LEIDA
        papeleta_leida.save()

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_ya_tiene_solicitud_cirio(self):
        """
        Test: Error si el hermano intenta pedir un cirio teniendo ya uno solicitado.

        Given: Una PapeletaSitio previa (no insignia) en estado SOLICITADA para el mismo acto.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional con un puesto de tipo CIRIO.
        Then: Se lanza una ValidationError indicando que ya existe una solicitud activa.
        """
        self.mi_papeleta.es_solicitud_insignia = False
        self.mi_papeleta.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.puesto_objetivo_cirio_cristo
                )

        mensaje_esperado = "Ya tienes una solicitud activa para 'CIRIO'."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_tipo_diferente_activo(self):
        """
        Test: Error si el hermano intenta pedir una Cruz teniendo ya un Cirio solicitado.

        Given: Una PapeletaSitio previa de tipo 'CIRIO' en estado SOLICITADA.
        When: Se llama al servicio para pedir un puesto de tipo 'CRUZ PENITENTE'.
        Then: Se lanza una ValidationError con el mensaje específico de incompatibilidad.
        """
        self.mi_papeleta.puesto = self.mi_puesto_cirio_cristo
        self.mi_papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.SOLICITADA
        self.mi_papeleta.es_solicitud_insignia = False
        self.mi_papeleta.save()

        puesto_cruz = self.mi_puesto_cruz_cristo 

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=puesto_cruz
                )

        mensaje_esperado = "Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez)."
        self.assertIn(mensaje_esperado, str(cm.exception))



    @patch("api.servicios.solicitud_cirio_tradicional.PapeletaSitio.objects.create")
    def test_procesar_solicitud_cirio_tradicional_error_integridad_concurrente(self, mock_create):
        """
        Test: Manejo de error de integridad (ej. doble clic simultáneo).

        Given: Un intento de creación que lanza un IntegrityError desde la base de datos.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: El servicio captura el error y lanza una ValidationError amigable con el mensaje de salvaguarda.
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        mock_create.side_effect = IntegrityError("UNIQUE constraint failed")

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = "Ya existe una papeleta activa para este acto. Si has pulsado dos veces, espera unos segundos y recarga."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_error_fallo_anulacion_insignia_por_cambio_estado(self):
        """
        Test: Error específico cuando la anulación de la insignia falla por concurrencia.
        """
        self.mi_papeleta.es_solicitud_insignia = True
        self.mi_papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.SOLICITADA
        self.mi_papeleta.save()

        with patch("django.db.models.query.QuerySet.update", return_value=0):
            with patch("django.utils.timezone.now", return_value=self.ahora):
                with self.assertRaises(ValidationError) as cm:
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano_antiguo,
                        acto=self.acto,
                        puesto=self.mi_puesto_cirio_cristo
                    )

        mensaje_esperado = "Tu solicitud de insignia cambió de estado durante el proceso. Vuelve a intentarlo o contacta con secretaría."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_creacion_ok(self):
        """
        Test: Creación exitosa de una papeleta de sitio.

        Given: Un hermano apto y un puesto de cirio disponible.
            El hermano no tiene solicitudes previas para el acto.
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se crea un nuevo registro en PapeletaSitio.
            El estado inicial es SOLICITADA.
            Se genera un código de verificación único.
        """

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(nueva_papeleta.id)
        
        self.assertEqual(nueva_papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        
        self.assertEqual(nueva_papeleta.hermano, self.hermano_antiguo)
        self.assertEqual(nueva_papeleta.puesto, self.mi_puesto_cirio_cristo)
        self.assertEqual(nueva_papeleta.acto, self.acto)
        self.assertEqual(nueva_papeleta.anio, self.ahora.year)

        self.assertTrue(len(nueva_papeleta.codigo_verificacion) > 0)
        
        count = PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).count()
        self.assertEqual(count, 1)



    def test_procesar_solicitud_cirio_tradicional_genera_codigo_verificacion_ok(self):
        """
        Test: Generación automática y única del código de verificación.

        Given: Un proceso de solicitud válido.
        When: Se crea la PapeletaSitio a través del servicio.
        Then: El campo codigo_verificacion no debe estar vacío.
            El código debe tener un formato válido (ej. longitud mínima).
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()
        self.mi_puesto_cirio_cristo.disponible = True
        self.mi_puesto_cirio_cristo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(nueva_papeleta.codigo_verificacion)
        self.assertNotEqual(nueva_papeleta.codigo_verificacion, "")

        self.assertGreaterEqual(len(nueva_papeleta.codigo_verificacion), 8)

        nueva_papeleta.refresh_from_db()
        self.assertIsNotNone(nueva_papeleta.codigo_verificacion)



    def test_procesar_solicitud_cirio_tradicional_anio_coincide_con_acto_ok(self):
        """
        Test: El año de la papeleta debe ser el mismo que el año de la fecha del acto.

        Given: Un acto programado para una fecha futura (ej. año 2026).
        When: Se procesa la solicitud de la papeleta.
        Then: El campo 'anio' de la PapeletaSitio debe ser 2026.
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        anio_acto = self.acto.fecha.year

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertEqual(nueva_papeleta.anio, anio_acto)
        
        self.assertIsNotNone(nueva_papeleta.anio)
        self.assertIsInstance(nueva_papeleta.anio, int)



    def test_procesar_solicitud_cirio_tradicional_puesto_asignado_ok(self):
        """
        Test: El puesto solicitado queda correctamente vinculado a la papeleta.

        Given: Un puesto de cirio específico y disponible.
        When: Se procesa la solicitud exitosamente.
        Then: La papeleta creada debe apuntar exactamente a ese ID de puesto.
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        puesto_elegido = self.puesto_objetivo_cirio_cristo
        puesto_elegido.disponible = True
        puesto_elegido.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=puesto_elegido
            )

        self.assertEqual(nueva_papeleta.puesto, puesto_elegido)
        self.assertEqual(nueva_papeleta.puesto.id, puesto_elegido.id)

        self.assertEqual(nueva_papeleta.puesto.tipo_puesto, self.tipo_cirio)
        
        nueva_papeleta.refresh_from_db()
        self.assertIsNotNone(nueva_papeleta.puesto)



    def test_procesar_solicitud_cirio_tradicional_transaccion_completa_ok(self):
        """
        Test: Flujo completo exitoso (Happy Path).

        Given: Un hermano sin papeletas, un puesto disponible y un acto en plazo.
        When: Se ejecuta el servicio procesar_solicitud_cirio_tradicional.
        Then: 1. Se crea la papeleta.
            2. El puesto queda correctamente asociado.
            3. No se lanzan excepciones.
            4. Los datos persistidos son íntegros.
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        puesto_objetivo = self.mi_puesto_cirio_cristo
        puesto_objetivo.disponible = True
        puesto_objetivo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            try:
                nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=puesto_objetivo
                )
            except ValidationError as e:
                self.fail(f"El servicio lanzó ValidationError inesperada: {e}")

        self.assertIsNotNone(nueva_papeleta.id)

        nueva_papeleta.refresh_from_db()
        self.assertEqual(nueva_papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)
        self.assertEqual(nueva_papeleta.hermano, self.hermano_antiguo)
        self.assertEqual(nueva_papeleta.puesto, puesto_objetivo)
        self.assertEqual(nueva_papeleta.anio, self.acto.fecha.year)

        self.assertTrue(nueva_papeleta.codigo_verificacion)

        self.assertEqual(PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).count(), 1)



    @patch("api.servicios.solicitud_cirio_tradicional.PapeletaSitio.objects.create")
    def test_procesar_solicitud_cirio_tradicional_error_unicidad_simultanea(self, mock_create):
        """
        Test: Manejo de IntegrityError por doble creación simultánea (Race Condition).

        Given: Un escenario donde la validación lógica pasa, pero la base de datos 
            lanza un IntegrityError al intentar insertar (por UniqueConstraint).
        When: Se llama al servicio procesar_solicitud_cirio_tradicional.
        Then: Se captura el IntegrityError y se lanza una ValidationError amigable.
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        mock_create.side_effect = IntegrityError("UNIQUE constraint failed: api_papeletasitio.hermano_id...")

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = "Ya existe una papeleta activa para este acto. Si has pulsado dos veces, espera unos segundos y recarga."
        self.assertIn(mensaje_esperado, str(cm.exception))



    @patch("api.models.PapeletaSitio.clean")
    def test_procesar_solicitud_cirio_tradicional_error_validacion_modelo_clean(self, mock_clean):
        """
        Test: El servicio debe propagar los errores lanzados por el clean() del modelo.

        Given: Un flujo de solicitud donde los datos violan una regla del modelo.
        When: El servicio intenta guardar la papeleta y se ejecuta el método clean().
        Then: Se lanza una ValidationError originada en el modelo.
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        mensaje_error_modelo = "Regla de negocio del modelo violada: Combinación no permitida."
        mock_clean.side_effect = ValidationError(mensaje_error_modelo)

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        self.assertIn(mensaje_error_modelo, str(cm.exception))



    def test_procesar_solicitud_cirio_tradicional_vinculacion_valida_ok(self):
        """
        Test: Vinculación exitosa entre dos hermanos.

        Given: Un hermano que solicita un cirio y proporciona el número de registro 
            de otro hermano (más nuevo) para ir vinculado.
        When: Se llama al servicio con el argumento numero_registro_vinculado.
        Then: La papeleta se crea correctamente.
            El campo vinculado_a (en el modelo) apunta al hermano objetivo.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        papeleta_objetivo = PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
                numero_registro_vinculado=self.hermano_nuevo.numero_registro
            )

        self.assertEqual(nueva_papeleta.vinculado_a, self.hermano_nuevo)

        nueva_papeleta.refresh_from_db()
        self.assertEqual(nueva_papeleta.vinculado_a.id, self.hermano_nuevo.id)



    def test_procesar_solicitud_cirio_tradicional_vinculacion_ambos_con_numero_ok(self):
        """
        Test: Vinculación válida cuando ambos tienen número de registro y 
            se respeta la jerarquía de antigüedad.

        Given: Hermano A (Nº 100) y Hermano B (Nº 500).
            El Hermano B ya tiene una solicitud activa de Cirio en el Cristo.
        When: El Hermano A solicita un Cirio en el Cristo vinculado al Hermano B.
        Then: La papeleta del Hermano A se crea vinculada_a el Hermano B.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
                numero_registro_vinculado=self.hermano_nuevo.numero_registro
            )

        self.assertEqual(nueva_papeleta.vinculado_a, self.hermano_nuevo)
        self.assertEqual(nueva_papeleta.vinculado_a.numero_registro, 500)

        nueva_papeleta.refresh_from_db()
        self.assertIsNotNone(nueva_papeleta.vinculado_a)



    def test_procesar_solicitud_cirio_tradicional_vinculacion_solicitud_unica_ok(self):
        """
        Test: Vinculación exitosa cuando el hermano objetivo tiene una única solicitud.

        Given: El Hermano A (antiguo) y el Hermano B (nuevo).
            El Hermano B tiene exactamente una papeleta SOLICITADA.
        When: El Hermano A solicita cirio vinculado al Hermano B.
        Then: La vinculación se procesa correctamente sin conflictos de multiplicidad.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 200
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 800
        self.hermano_nuevo.save()

        papeleta_objetivo = PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
                numero_registro_vinculado=self.hermano_nuevo.numero_registro
            )

        self.assertEqual(nueva_papeleta.vinculado_a, self.hermano_nuevo)

        self.assertIsNotNone(nueva_papeleta.id)



    def test_procesar_solicitud_cirio_tradicional_vinculacion_mismo_tipo_ok(self):
        """
        Test: Vinculación permitida cuando ambos hermanos piden el mismo tipo de puesto.

        Given: El Hermano B (objetivo) tiene una solicitud de 'CIRIO'.
        When: El Hermano A (solicitante) pide un puesto de tipo 'CIRIO' vinculado al B.
        Then: La vinculación se realiza con éxito.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        
        self.hermano_antiguo.numero_registro = 300
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 900
        self.hermano_nuevo.save()

        papeleta_objetivo = PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
                numero_registro_vinculado=self.hermano_nuevo.numero_registro
            )

        self.assertEqual(nueva_papeleta.vinculado_a, self.hermano_nuevo)

        self.assertEqual(nueva_papeleta.puesto.tipo_puesto_id, papeleta_objetivo.puesto.tipo_puesto_id)



    def test_procesar_solicitud_cirio_tradicional_vinculacion_mismo_cortejo_ok(self):
        """
        Test: Vinculación permitida cuando ambos hermanos van en la misma sección.

        Given: El Hermano B (objetivo) tiene una solicitud en el cortejo de Cristo.
        When: El Hermano A (solicitante) pide un puesto también en el cortejo de Cristo.
        Then: La vinculación se realiza con éxito porque no hay conflicto de sección.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 400
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 1000
        self.hermano_nuevo.save()

        papeleta_objetivo = PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
                numero_registro_vinculado=self.hermano_nuevo.numero_registro
            )

        self.assertEqual(nueva_papeleta.vinculado_a, self.hermano_nuevo)

        self.assertEqual(nueva_papeleta.puesto.cortejo_cristo, papeleta_objetivo.puesto.cortejo_cristo)



    def test_procesar_solicitud_cirio_tradicional_vinculacion_objetivo_sin_dependientes_ok(self):
        """
        Test: Vinculación permitida cuando el hermano objetivo no es el 
            punto de destino de otras vinculaciones previas.

        Given: El Hermano B (nuevo) tiene su solicitud activa.
            Nadie se ha vinculado todavía al Hermano B.
        When: El Hermano A (antiguo) solicita vincularse al Hermano B.
        Then: La vinculación se crea correctamente.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        self.assertFalse(
            PapeletaSitio.objects.filter(acto=self.acto, vinculado_a=self.hermano_nuevo).exists()
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
                numero_registro_vinculado=self.hermano_nuevo.numero_registro
            )

        self.assertEqual(nueva_papeleta.vinculado_a, self.hermano_nuevo)



    def test_procesar_solicitud_cirio_tradicional_vinculacion_persistencia_ok(self):
        """
        Test: La vinculación se guarda correctamente en el modelo PapeletaSitio.

        Given: Un escenario válido de vinculación (Antiguo -> Nuevo).
        When: Se procesa la solicitud a través del servicio.
        Then: La base de datos refleja la relación en el campo 'vinculado_a'.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        
        self.hermano_antiguo.numero_registro = 150
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 600
        self.hermano_nuevo.save()

        papeleta_objetivo = PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo,
                numero_registro_vinculado=self.hermano_nuevo.numero_registro
            )

        self.assertIsNotNone(nueva_papeleta.vinculado_a)
        self.assertEqual(nueva_papeleta.vinculado_a.id, self.hermano_nuevo.id)

        nueva_papeleta.refresh_from_db()
        self.assertEqual(nueva_papeleta.vinculado_a, self.hermano_nuevo)

        vinculaciones_recibidas = self.hermano_nuevo.papeletas_vinculadas_origen.all()
        self.assertIn(nueva_papeleta, vinculaciones_recibidas)



    def test_procesar_solicitud_vinculacion_error_hermano_no_existe(self):
        """
        Test: Error si el número de registro objetivo no existe en la base de datos.

        Given: Un número de registro (ej: 99999) que no está asignado a nadie.
        When: El hermano solicita vincularse a ese número.
        Then: Se lanza una ValidationError: "No existe hermano con Nº 99999."
        """
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        numero_inexistente = 99999

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=numero_inexistente
                )

        mensaje_esperado = f"No existe hermano con Nº {numero_inexistente}."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_consigo_mismo(self):
        """
        Test: Un hermano no puede vincularse a su propio número de registro.

        Given: El hermano_antiguo con número de registro 100.
        When: Intenta solicitar una papeleta vinculada al número 100.
        Then: Se lanza una ValidationError: "No puedes vincularte contigo mismo."
        """
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        
        PapeletaSitio.objects.filter(hermano=self.hermano_antiguo, acto=self.acto).delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=100
                )

        self.assertIn("No puedes vincularte contigo mismo.", str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_falta_numero_registro(self):
        """
        Test: La vinculación falla si el solicitante o el objetivo carecen de número.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        self.hermano_nuevo.estado_hermano = Hermano.EstadoHermano.PENDIENTE_INGRESO
        self.hermano_nuevo.numero_registro = None
        self.hermano_nuevo.save()

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with patch("api.models.Hermano.objects.get", return_value=self.hermano_nuevo):
                with self.assertRaises(ValidationError) as cm:
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano_antiguo,
                        acto=self.acto,
                        puesto=self.mi_puesto_cirio_cristo,
                        numero_registro_vinculado=999
                    )

        mensaje_esperado = "Ambos hermanos deben tener número de registro para poder vincularse."
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_jerarquia_invertida(self):
        """
        Test: Un hermano nuevo no puede vincularse a uno antiguo.

        Given: Hermano Solicitante (Nº 500) y Hermano Objetivo (Nº 100).
        When: El Nº 500 intenta vincularse al Nº 100.
        Then: Se lanza ValidationError: "Tú (Nº 500) eres más nuevo que el Nº 100..."
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 500 
        self.hermano_antiguo.save()

        self.hermano_nuevo.numero_registro = 100
        self.hermano_nuevo.save()

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=100
                )

        mensaje_esperado = "Tú (Nº 500) eres más nuevo que el Nº 100. Solo el hermano antiguo puede vincularse al nuevo"
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_objetivo_sin_solicitud(self):
        """
        Test: No se puede vincular a un hermano que no ha pedido papeleta.

        Given: El hermano_antiguo (Nº 100) y el hermano_nuevo (Nº 500).
            El hermano_nuevo NO tiene ninguna papeleta activa para el acto.
        When: El Nº 100 intenta vincularse al Nº 500.
        Then: Se lanza ValidationError: "El hermano Nº 500 no tiene solicitud activa."
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=500
                )

        mensaje_esperado = "El hermano Nº 500 no tiene solicitud activa."
        self.assertIn(mensaje_esperado, str(cm.exception))




    def test_procesar_solicitud_vinculacion_error_objetivo_multiples_solicitudes(self):
        """
        Test: El servicio detecta si el objetivo tiene múltiples solicitudes.
        
        Dado que el clean() del modelo impide crear duplicados, usamos super().save() 
        para forzar un estado de inconsistencia en la BD y probar la defensa del service.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        
        numero_objetivo = 500
        self.hermano_nuevo.numero_registro = numero_objetivo
        self.hermano_nuevo.save()

        for _ in range(2):
            p = PapeletaSitio(
                hermano=self.hermano_nuevo,
                acto=self.acto,
                anio=self.acto.fecha.year,
                estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
                puesto=self.mi_puesto_cirio_cristo,
                codigo_verificacion=f"TEST-{uuid.uuid4().hex[:4]}"
            )
            super(PapeletaSitio, p).save() 

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=numero_objetivo
                )

        mensaje_esperado = (
            f"El hermano Nº {numero_objetivo} tiene múltiples solicitudes activas para este acto. "
            "Contacte con secretaría."
        )
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_objetivo_pide_insignia(self):
        """
        Test: Bloqueo de vinculación si el hermano objetivo solicita una insignia.

        Given: El hermano_nuevo (objetivo) tiene una solicitud de tipo Insignia.
        When: El hermano_antiguo intenta vincularse a él.
        Then: Se lanza ValidationError: "No puedes vincularte a un hermano que solicita Insignia."
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            puesto=None
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=500
                )

        self.assertIn("No puedes vincularte a un hermano que solicita Insignia", str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_distinto_tipo_puesto(self):
        """
        Test: No se permite la vinculación si los tipos de puesto son diferentes.

        Given: El hermano objetivo solicita un 'Cirio'.
        When: El hermano solicitante intenta vincularse pidiendo una 'Cruz'.
        Then: Se lanza ValidationError: "Ambos deben solicitar el mismo tipo de puesto..."
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo,
            es_solicitud_insignia=False
        )

        tipo_cruz = TipoPuesto.objects.create(nombre_tipo="Cruz", es_insignia=False)
        puesto_cruz = Puesto.objects.create(
            nombre="Cruz de Penitencia 1",
            acto=self.acto,
            tipo_puesto=tipo_cruz,
            cortejo_cristo=True
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=puesto_cruz,
                    numero_registro_vinculado=500
                )

        self.assertIn("Ambos deben solicitar el mismo tipo de puesto (ej: ambos Cirio).", str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_conflicto_seccion(self):
        """
        Test: No se permite vincular hermanos si uno va en Cristo y otro en Virgen.
        
        Nota: Deben compartir el mismo tipo de puesto para superar la primera validación
        y llegar a la comprobación de sección.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        tipo_del_puesto_cristo = self.mi_puesto_cirio_cristo.tipo_puesto

        puesto_virgen = Puesto.objects.create(
            nombre="Cirio Virgen Igual Tipo",
            acto=self.acto,
            tipo_puesto=tipo_del_puesto_cristo,
            cortejo_cristo=False 
        )

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=puesto_virgen,
            es_solicitud_insignia=False
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=500
                )

        self.assertIn("Conflicto de sección: Uno va en Cristo y otro en Virgen.", str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_solicitante_con_dependientes(self):
        """
        Test: Un hermano no puede vincularse a otro si ya tiene a alguien vinculado a él.

        Given: El hermano C está vinculado al hermano A.
        When: El hermano A intenta vincularse al hermano B.
        Then: Se lanza ValidationError impidiendo la cadena A -> B -> C.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 200
        self.hermano_antiguo.save()
        
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        hermano_c = Hermano.objects.create(
            dni="11111112A",
            username="11111112A",
            password="password",
            nombre="Antonio",
            primer_apellido="Antiguo",
            segundo_apellido="López",
            email="antiguo@example.com",
            telefono="600000001",
            estado_civil=Hermano.EstadoCivil.CASADO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=150,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1980-01-01",
            direccion="Calle A",
            codigo_postal="41001",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False
        )

        papeleta_a = PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo
        )

        PapeletaSitio.objects.create(
            hermano=hermano_c,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            vinculado_a=self.hermano_antiguo,
            puesto=self.mi_puesto_cirio_cristo
        )

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            puesto=self.mi_puesto_cirio_cristo
        )

        papeleta_a.delete()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=500
                )

        mensaje_esperado = (
            "No puedes vincularte a otro hermano porque ya tienes a otros hermanos vinculados a ti. "
            "No se permiten cadenas de vinculación (A->B->C). Diles que se vinculen directamente al hermano objetivo."
        )
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_vinculacion_error_modalidad_distinta(self):
        """
        Test: No se puede vincular a un hermano cuya solicitud no sea de modalidad tradicional.

        Given: El hermano objetivo tiene una solicitud activa pero para una INSIGNIA.
        When: El hermano solicitante intenta vincularse a él mediante cirio tradicional.
        Then: Se lanza ValidationError: "Solo puedes vincularte a hermanos que participen en la modalidad tradicional."
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()
        
        self.hermano_nuevo.numero_registro = 500
        self.hermano_nuevo.save()

        PapeletaSitio.objects.create(
            hermano=self.hermano_nuevo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            puesto=None
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=500
                )

        self.assertIn(
            "No puedes vincularte a un hermano que solicita Insignia.", 
            str(cm.exception)
        )



    def test_procesar_solicitud_vinculacion_error_numero_registro_invalido(self):
        """
        Test: La vinculación falla si el número de registro es explícitamente inválido.
        
        Para que el service entre en la lógica de vinculación, el valor debe ser 
        distinto de None, 0 o "". Usamos un valor que no corresponda a un hermano.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):

            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo,
                    numero_registro_vinculado=-1 
                )

        self.assertIn(
            "No existe hermano con Nº -1.", 
            str(cm.exception)
        )



    def test_procesar_solicitud_rollback_anulacion_si_falla_creacion(self):
        """
        Test: Si la creación de la papeleta falla, la anulación de la insignia previa
        no debe persistir (Rollback).
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        insignia_previa = PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True
        )

        with patch.object(self.service, '_crear_papeleta_base', side_effect=Exception("Error fatal en BD")):
            with patch("django.utils.timezone.now", return_value=self.ahora):
                with self.assertRaises(Exception) as cm:
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano_antiguo,
                        acto=self.acto,
                        puesto=self.mi_puesto_cirio_cristo
                    )

        insignia_previa.refresh_from_db()
        self.assertEqual(
            insignia_previa.estado_papeleta, 
            PapeletaSitio.EstadoPapeleta.SOLICITADA,
            "La anulación de la insignia debería haberse revertido tras el error."
        )
        self.assertIn("Error fatal en BD", str(cm.exception))



    from django.db import transaction

    def test_procesar_solicitud_anulacion_y_creacion_en_misma_transaccion(self):
        """
        Test: Verifica que la anulación de la insignia y la creación de la nueva 
        papeleta se ejecutan dentro de un bloque atómico.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        insignia_previa = PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with transaction.atomic():
                nueva_papeleta = self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

                insignia_previa.refresh_from_db()

                self.assertEqual(insignia_previa.estado_papeleta, PapeletaSitio.EstadoPapeleta.ANULADA)
                self.assertIsNotNone(nueva_papeleta.id)
                self.assertEqual(nueva_papeleta.hermano.id, self.hermano_antiguo.id)

        self.assertTrue(PapeletaSitio.objects.filter(pk=nueva_papeleta.pk).exists())



    def test_procesar_solicitud_rollback_integral_ante_error(self):
        """
        Test: Verifica que si la creación de la papeleta falla al final,
        la anulación de la insignia previa se deshace (Rollback).

        Given: Un hermano con una solicitud de insignia activa.
        When: Se procesa el cirio pero ocurre un error al guardar el puesto.
        Then: La insignia vuelve a su estado SOLICITADA y no se crea el cirio.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        insignia_previa = PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True
        )

        with patch("api.models.PapeletaSitio.save", side_effect=Exception("Fallo crítico de base de datos")):
            with patch("django.utils.timezone.now", return_value=self.ahora):
                with self.assertRaises(Exception):
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano_antiguo,
                        acto=self.acto,
                        puesto=self.mi_puesto_cirio_cristo
                    )

        insignia_previa.refresh_from_db()
        self.assertEqual(
            insignia_previa.estado_papeleta, 
            PapeletaSitio.EstadoPapeleta.SOLICITADA,
            "La anulación de la insignia debió revertirse por el Rollback."
        )

        self.assertEqual(
            PapeletaSitio.objects.filter(es_solicitud_insignia=False).count(), 
            0,
            "No debe persistir ninguna papeleta de cirio si hubo error."
        )



    def test_procesar_solicitud_error_concurrencia_cambio_estado_insignia(self):
        """
        Test: Si la insignia a anular cambia de estado justo antes del update,
        el servicio debe detectar que no se ha actualizado nada y fallar.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        insignia_previa = PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True
        )
        
        with patch("api.models.PapeletaSitio.objects.exclude", return_value=PapeletaSitio.objects.all()):
            with patch("django.db.models.query.QuerySet.update", return_value=0):
                with patch("django.utils.timezone.now", return_value=self.ahora):
                    
                    with self.assertRaises(ValidationError) as cm:
                        self.service.procesar_solicitud_cirio_tradicional(
                            hermano=self.hermano_antiguo,
                            acto=self.acto,
                            puesto=self.mi_puesto_cirio_cristo
                        )

        self.assertIn(
            "Tu solicitud de insignia cambió de estado durante el proceso", 
            str(cm.exception)
        )



    def test_procesar_solicitud_concurrente_mismo_hermano_error(self):
        """
        Test: Verifica que el sistema gestiona el IntegrityError si dos solicitudes
        intentan persistirse casi simultáneamente.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with patch.object(PapeletaSitio, 'save', side_effect=IntegrityError("Duplicate entry")):
                
                with self.assertRaises(ValidationError) as cm:
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano_antiguo,
                        acto=self.acto,
                        puesto=self.mi_puesto_cirio_cristo
                    )

        mensaje_esperado = (
            "Ya existe una papeleta activa para este acto. "
            "Si has pulsado dos veces, espera unos segundos y recarga."
        )
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_error_condicion_carrera_anulacion_insignia(self):
        """
        Test: Controla que si la insignia cambia de estado justo antes de ser anulada
        por el service, se lance un error de concurrencia.
        
        Escenario:
        1. El service identifica que el hermano tiene una insignia SOLICITADA.
        2. Justo antes del .update(), el estado de la insignia cambia (en otro proceso).
        3. El .update() afecta a 0 filas y debe disparar la ValidationError.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.numero_registro = 100
        self.hermano_antiguo.save()

        insignia_previa = PapeletaSitio.objects.create(
            hermano=self.hermano_antiguo,
            acto=self.acto,
            anio=self.acto.fecha.year,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True
        )

        with patch("api.models.PapeletaSitio.objects.select_for_update") as mock_query:
            mock_query.return_value.filter.return_value.update.return_value = 0
            
            with patch("django.utils.timezone.now", return_value=self.ahora):
                with self.assertRaises(ValidationError) as cm:
                    self.service.procesar_solicitud_cirio_tradicional(
                        hermano=self.hermano_antiguo,
                        acto=self.acto,
                        puesto=self.mi_puesto_cirio_cristo
                    )

        mensaje_esperado = "Tu solicitud de insignia cambió de estado durante el proceso"
        self.assertIn(mensaje_esperado, str(cm.exception))



    def test_procesar_solicitud_hermano_sin_cuerpos_exito(self):
        """
        Edge Case: Un hermano sin cuerpos asignados debe poder solicitar 
        un puesto estándar si este no es restringido.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        self.hermano_antiguo.estado_hermano = Hermano.EstadoHermano.ALTA
        self.hermano_antiguo.cuerpos.clear()
        self.hermano_antiguo.save()

        Cuota.objects.create(
            hermano=self.hermano_antiguo, anio=self.ahora.year - 1, 
            importe=50, estado=Cuota.EstadoCuota.PAGADA
        )

        puesto_estandar = self.mi_puesto_cirio_cristo
        puesto_estandar.tipo_puesto.solo_junta_gobierno = False
        puesto_estandar.tipo_puesto.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=puesto_estandar
            )

        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.hermano, self.hermano_antiguo)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)



    def test_procesar_solicitud_puesto_cupo_cero_edge_case(self):
        """
        Edge Case: El puesto tiene numero_maximo_asignaciones = 0.
        Verifica que las propiedades calculadas del modelo Puesto no causen
        errores de división por cero y que el servicio se comporte según lo esperado.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        
        puesto_agotado = self.mi_puesto_cirio_cristo
        puesto_agotado.numero_maximo_asignaciones = 0
        puesto_agotado.disponible = True
        puesto_agotado.save()

        with patch("django.utils.timezone.now", return_value=self.ahora):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=puesto_agotado
            )

        self.assertIsNotNone(papeleta.id)

        self.assertEqual(puesto_agotado.plazas_disponibles, 0)
        self.assertEqual(puesto_agotado.porcentaje_ocupacion, 100)



    def test_procesar_solicitud_exito_justo_antes_cierre_plazo(self):
        """
        Positivo - Edge Case: Permite solicitar si falta 1 minuto para el cierre, 
        incluso si el acto es ese mismo día.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        
        fecha_acto = self.ahora.replace(hour=20, minute=0, second=0)
        fin_plazo = self.ahora.replace(hour=14, minute=0, second=0)
        
        self.acto.fecha = fecha_acto
        self.acto.inicio_solicitud_cirios = self.ahora - timezone.timedelta(days=1)
        self.acto.fin_solicitud_cirios = fin_plazo
        self.acto.save()

        momento_exito = fin_plazo - timezone.timedelta(minutes=1)
        
        with patch("django.utils.timezone.now", return_value=momento_exito):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )
            
        self.assertIsNotNone(papeleta.id)
        self.assertEqual(papeleta.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)



    def test_procesar_solicitud_error_justo_despues_cierre_plazo(self):
        """
        Negativo - Edge Case: Bloquea la solicitud si se intenta 1 minuto después 
        de la hora de cierre configurada.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        fin_plazo = self.ahora.replace(hour=14, minute=0, second=0, microsecond=0)
        
        self.acto.fin_solicitud_cirios = fin_plazo
        self.acto.inicio_solicitud_cirios = fin_plazo - timezone.timedelta(hours=5)
        self.acto.save()

        momento_error = fin_plazo + timezone.timedelta(minutes=1)
        
        with patch("django.utils.timezone.now", return_value=momento_error):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        nombre_plazo = "cirios"
        mensaje_esperado = f"El plazo de solicitud de {nombre_plazo} ha finalizado."
        
        self.assertEqual(str(cm.exception.messages[0]), mensaje_esperado)



    def test_procesar_solicitud_exito_momento_exacto_inicio_plazo(self):
        """
        Positivo - Edge Case: Verifica que el acceso se permite en el segundo exacto
        en que comienza el plazo de solicitud.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        
        inicio_exacto = self.ahora.replace(hour=9, minute=0, second=0, microsecond=0)
        self.acto.inicio_solicitud_cirios = inicio_exacto
        self.acto.fin_solicitud_cirios = inicio_exacto + timezone.timedelta(days=1)
        self.acto.save()

        with patch("django.utils.timezone.now", return_value=inicio_exacto):
            papeleta = self.service.procesar_solicitud_cirio_tradicional(
                hermano=self.hermano_antiguo,
                acto=self.acto,
                puesto=self.mi_puesto_cirio_cristo
            )

        self.assertIsNotNone(papeleta.id, "Debería permitir la solicitud en el segundo exacto de inicio.")



    def test_procesar_solicitud_error_justo_tras_momento_exacto_fin_plazo(self):
        """
        Negativo - Edge Case: Verifica que inmediatamente después de cumplirse 
        la hora de fin (1 segundo después), el sistema bloquea la solicitud.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()

        fin_exacto = self.ahora.replace(hour=14, minute=0, second=0, microsecond=0)
        self.acto.inicio_solicitud_cirios = fin_exacto - timezone.timedelta(days=1)
        self.acto.fin_solicitud_cirios = fin_exacto
        self.acto.save()

        un_segundo_despues = fin_exacto + timezone.timedelta(seconds=1)
        
        with patch("django.utils.timezone.now", return_value=un_segundo_despues):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        nombre_plazo = "cirios"
        mensaje_esperado = f"El plazo de solicitud de {nombre_plazo} ha finalizado."
        
        self.assertEqual(str(cm.exception.messages[0]), mensaje_esperado)



    def test_procesar_solicitud_error_hermano_solo_cuota_anio_actual(self):
        """
        Negativo - Edge Case: Un hermano que solo tiene cuotas del año en curso
        debe ser bloqueado si la lógica exige historial hasta el año anterior.
        
        Contexto: Es 2026. El hermano tiene cuota de 2026, pero ninguna de 2025 o antes.
        """
        PapeletaSitio.objects.filter(acto=self.acto).delete()
        self.hermano_antiguo.cuotas.all().delete()

        anio_actual = self.ahora.year
        anio_limite = anio_actual - 1

        Cuota.objects.create(
            hermano=self.hermano_antiguo,
            anio=anio_actual,
            importe=50,
            estado=Cuota.EstadoCuota.PAGADA,
            tipo=Cuota.TipoCuota.ORDINARIA
        )

        with patch("django.utils.timezone.now", return_value=self.ahora):
            with self.assertRaises(ValidationError) as cm:
                self.service.procesar_solicitud_cirio_tradicional(
                    hermano=self.hermano_antiguo,
                    acto=self.acto,
                    puesto=self.mi_puesto_cirio_cristo
                )

        mensaje_esperado = f"No constan cuotas registradas hasta el año {anio_limite}"
        self.assertIn(mensaje_esperado, str(cm.exception))