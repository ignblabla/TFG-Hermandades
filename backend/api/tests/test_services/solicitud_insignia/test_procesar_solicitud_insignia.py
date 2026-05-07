from datetime import date, datetime, timedelta
from unittest import TestCase
import unittest
from unittest.mock import ANY, MagicMock, call, patch
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone

from django.db import DatabaseError, IntegrityError
import pytest

from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService
from api.models import Acto, CuerpoPertenencia, Cuota, Hermano, PapeletaSitio, PreferenciaSolicitud, Puesto, TipoPuesto


@pytest.mark.django_db
class TestSolicitudInsigniaService(TestCase):

    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now') 
    def test_procesar_solicitud_insignia_tradicional_flujo_completo(self, mock_timezone_now):
        """
        Test: Flujo completo correcto

        Given: Un hermano y un acto válidos.
            Unas preferencias_data válidas.
            vinculado_a = None.
        When: Se llama a procesar_solicitud_insignia_tradicional del servicio.
        Then: Se llaman TODAS las validaciones en orden.
            Se llama a _crear_papeleta_base.
            Se modifica papeleta.es_solicitud_insignia = True.
            Se llama a save(update_fields=['es_solicitud_insignia']).
            Se llama a _guardar_preferencias.
            Se retorna la papeleta creada.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()

        service._crear_papeleta_base = MagicMock()
        service._guardar_preferencias = MagicMock()

        mock_papeleta = MagicMock()
        mock_papeleta.es_solicitud_insignia = False
        service._crear_papeleta_base.return_value = mock_papeleta

        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = ['Cuerpo1', 'Cuerpo2']
        cuerpos_esperados = {'Cuerpo1', 'Cuerpo2'}
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = '2026-03-01'
        mock_acto.fin_solicitud = '2026-05-01'
        
        preferencias_data = [{'id': 1, 'tipo': 'Cruz de Guía'}]

        mock_ahora = '2026-04-26 09:35:18'
        mock_timezone_now.return_value = mock_ahora

        resultado = service.procesar_solicitud_insignia_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            preferencias_data=preferencias_data,
            vinculado_a=None
        )

        mock_hermano.cuerpos.values_list.assert_called_once_with('nombre_cuerpo', flat=True)

        service._validar_configuracion_acto_tradicional.assert_called_once_with(mock_acto)
        service._validar_plazo_vigente.assert_called_once_with(
            mock_ahora, mock_acto.inicio_solicitud, mock_acto.fin_solicitud, "insignias"
        )
        service._validar_hermano_apto_para_solicitar.assert_called_once_with(mock_hermano, cuerpos_esperados)
        service._validar_edad_minima_insignia.assert_called_once_with(mock_hermano, mock_acto)
        service._validar_unicidad.assert_called_once_with(mock_hermano, mock_acto)
        service._validar_limites_preferencias.assert_called_once_with(preferencias_data)
        service._validar_preferencias_insignia_tradicional.assert_called_once_with(
            mock_hermano, mock_acto, preferencias_data, cuerpos_esperados
        )

        service._crear_papeleta_base.assert_called_once_with(mock_hermano, mock_acto, mock_ahora)

        self.assertTrue(mock_papeleta.es_solicitud_insignia)

        mock_papeleta.save.assert_called_once_with(update_fields=['es_solicitud_insignia'])

        service._guardar_preferencias.assert_called_once_with(mock_papeleta, preferencias_data)

        self.assertEqual(resultado, mock_papeleta)


    def test_procesar_solicitud_insignia_tradicional_error_vinculado_a(self):
        """
        Test: Parámetro inválido (vinculado_a no es None)

        Given: Un valor de 'vinculado_a' (ej. otro objeto Hermano).
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se valida que NO se ejecute ninguna validación posterior,
            ni la obtención de cuerpos, ni la creación de la papeleta.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        service._validar_configuracion_acto_tradicional = MagicMock()
        service._crear_papeleta_base = MagicMock()
        
        vinculado_a_no_nulo = MagicMock(name="OtroHermano")

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=MagicMock(),
                preferencias_data=[],
                vinculado_a=vinculado_a_no_nulo
            )

        self.assertEqual(
            cm.exception.message, 
            "Las solicitudes de insignia no permiten vincularse con otro hermano."
        )

        mock_hermano.cuerpos.values_list.assert_not_called()
        service._validar_configuracion_acto_tradicional.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_configuracion_acto(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_configuracion_acto_tradicional)

        Given: Un acto con configuración incorrecta.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que el flujo se corta inmediatamente:
            NO se valida el plazo, ni la aptitud del hermano, 
            ni se intenta crear la papeleta base.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_hermano = MagicMock()

        service._validar_configuracion_acto_tradicional = MagicMock(
            side_effect=ValidationError("El acto no está configurado para modalidad tradicional.")
        )

        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=mock_acto,
                preferencias_data=[],
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, "El acto no está configurado para modalidad tradicional.")

        service._validar_configuracion_acto_tradicional.assert_called_once_with(mock_acto)

        service._validar_plazo_vigente.assert_not_called()
        service._validar_hermano_apto_para_solicitar.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_plazo_vigente(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_plazo_vigente)

        Given: Un acto con configuración válida.
            Una fecha actual fuera del rango permitido de solicitud.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que se llamó a validar configuración pero NO se
            continuó con la validación del hermano ni la creación de la papeleta.
        """
        service = SolicitudInsigniaService()

        mock_ahora = '2026-04-26 09:35:00'
        mock_timezone_now.return_value = mock_ahora
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = '2026-01-01'
        mock_acto.fin_solicitud = '2026-02-01'

        service._validar_configuracion_acto_tradicional = MagicMock()

        service._validar_plazo_vigente = MagicMock(
            side_effect=ValidationError("El plazo de solicitud ha finalizado.")
        )

        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=MagicMock(),
                acto=mock_acto,
                preferencias_data=[],
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, "El plazo de solicitud ha finalizado.")
        
        service._validar_configuracion_acto_tradicional.assert_called_once()
        service._validar_plazo_vigente.assert_called_once_with(
            mock_ahora, mock_acto.inicio_solicitud, mock_acto.fin_solicitud, "insignias"
        )

        service._validar_hermano_apto_para_solicitar.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_hermano_no_apto(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_hermano_apto_para_solicitar)

        Given: Un acto válido y dentro de plazo.
            Un hermano que no cumple los requisitos de aptitud.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que se obtuvieron los cuerpos del hermano, pero el flujo 
            se detuvo antes de validar la edad o crear la papeleta.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = ['Tramo 1']
        cuerpos_esperados = {'Tramo 1'}

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()

        service._validar_hermano_apto_para_solicitar = MagicMock(
            side_effect=ValidationError("El hermano no está al corriente de sus obligaciones.")
        )

        service._validar_edad_minima_insignia = MagicMock()
        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=MagicMock(),
                preferencias_data=[],
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, "El hermano no está al corriente de sus obligaciones.")

        mock_hermano.cuerpos.values_list.assert_called_with('nombre_cuerpo', flat=True)

        service._validar_hermano_apto_para_solicitar.assert_called_once_with(mock_hermano, cuerpos_esperados)

        service._validar_edad_minima_insignia.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_edad_minima(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_edad_minima_insignia)

        Given: Un hermano apto.
            Un acto cuya configuración exige una edad mínima que el hermano no tiene.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que se ejecutaron las validaciones previas (acto, plazo, aptitud),
            pero NO se procedió a validar la unicidad ni a crear la papeleta.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()

        service._validar_edad_minima_insignia = MagicMock(
            side_effect=ValidationError("El hermano no tiene la edad mínima requerida para solicitar insignias.")
        )

        service._validar_unicidad = MagicMock()
        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=mock_acto,
                preferencias_data=[],
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, "El hermano no tiene la edad mínima requerida para solicitar insignias.")

        service._validar_edad_minima_insignia.assert_called_once_with(mock_hermano, mock_acto)

        service._validar_unicidad.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_unicidad(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_unicidad)

        Given: Un hermano que ya ha presentado una solicitud para el mismo acto.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que se ejecutaron todas las validaciones previas (acto, plazo, aptitud, edad),
            pero NO se procedió a validar los límites de preferencias ni a crear la papeleta.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()

        service._validar_unicidad = MagicMock(
            side_effect=ValidationError("Ya existe una solicitud de este hermano para este acto.")
        )

        service._validar_limites_preferencias = MagicMock()
        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=mock_acto,
                preferencias_data=[],
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, "Ya existe una solicitud de este hermano para este acto.")

        service._validar_unicidad.assert_called_once_with(mock_hermano, mock_acto)

        service._validar_limites_preferencias.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_limites_preferencias(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_limites_preferencias)

        Given: Una lista de preferencias_data que excede el máximo permitido (MAX_PREFERENCIAS_PERMITIDAS = 20).
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que se ejecutaron todas las validaciones de negocio previas,
            pero NO se procedió a validar el contenido de las preferencias 
            ni a crear la papeleta base.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        preferencias_excesivas = [{'id': i} for i in range(21)] 

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()

        service._validar_limites_preferencias = MagicMock(
            side_effect=ValidationError("Se ha excedido el número máximo de preferencias (20).")
        )

        service._validar_preferencias_insignia_tradicional = MagicMock()
        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=mock_acto,
                preferencias_data=preferencias_excesivas,
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, "Se ha excedido el número máximo de preferencias (20).")

        service._validar_limites_preferencias.assert_called_once_with(preferencias_excesivas)

        service._validar_preferencias_insignia_tradicional.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_detalle_preferencias(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_preferencias_insignia_tradicional)

        Given: Un payload de preferencias_data con datos lógicamente inválidos 
            (ej. insignias que no pertenecen a los cuerpos del hermano).
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que se ejecutaron todas las validaciones estructurales previas,
            pero NO se procedió a la creación de la papeleta base ni al guardado.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = ['Cristo']
        cuerpos_esperados = {'Cristo'}
        
        mock_acto = MagicMock()
        preferencias_invalidas = [{'insignia_id': 999}]

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()

        service._validar_preferencias_insignia_tradicional = MagicMock(
            side_effect=ValidationError("Una o más insignias seleccionadas no están disponibles para sus tramos.")
        )

        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=mock_acto,
                preferencias_data=preferencias_invalidas,
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, "Una o más insignias seleccionadas no están disponibles para sus tramos.")

        service._validar_preferencias_insignia_tradicional.assert_called_once_with(
            mock_hermano, mock_acto, preferencias_invalidas, cuerpos_esperados
        )

        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_integridad_creacion(self, mock_timezone_now):
        """
        Test: Error en creación de papeleta (_crear_papeleta_base lanza IntegrityError)

        Given: Un flujo de solicitud donde todas las validaciones previas pasan.
        When: Se llama a procesar_solicitud_insignia_tradicional pero la base de datos
            lanza un IntegrityError al intentar crear la papeleta base.
        Then: El servicio captura el IntegrityError y lanza un ValidationError.
            Se valida que el mensaje del error sea el mensaje custom sobre
            la solicitud activa o el doble clic.
            NO se intenta guardar las preferencias.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()

        service._crear_papeleta_base = MagicMock(
            side_effect=IntegrityError("Duplicate key value violates unique constraint")
        )

        service._guardar_preferencias = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=MagicMock(),
                acto=MagicMock(),
                preferencias_data=[{'id': 1}],
                vinculado_a=None
            )

        self.assertIn(
            "Ya existe una solicitud activa tramitada para este hermano.", 
            cm.exception.message
        )
        self.assertIn(
            "Por favor, no haga doble clic en el botón de enviar.", 
            cm.exception.message
        )

        service._guardar_preferencias.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_preferencias_vacias(self, mock_timezone_now):
        """
        Test: CASOS LÍMITE IMPORTANTES (preferencias_data vacío)

        Given: Un flujo de solicitud donde preferencias_data = [].
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Si la validación de límites considera que el vacío es inválido,
            se lanza un ValidationError y el flujo se detiene.
            Si es válido, el servicio debe terminar el proceso y llamar
            a _guardar_preferencias con la lista vacía.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()

        mensaje_error = "Debe seleccionar al menos una insignia."
        service._validar_limites_preferencias = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        service._validar_preferencias_insignia_tradicional = MagicMock()
        service._crear_papeleta_base = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service.procesar_solicitud_insignia_tradicional(
                hermano=MagicMock(),
                acto=MagicMock(),
                preferencias_data=[],
                vinculado_a=None
            )

        self.assertEqual(cm.exception.message, mensaje_error)
        service._validar_limites_preferencias.assert_called_once_with([])

        service._validar_preferencias_insignia_tradicional.assert_not_called()
        service._crear_papeleta_base.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_cuerpos_hermano_vacio(self, mock_timezone_now):
        """
        Test: CASOS LÍMITE IMPORTANTES (cuerpos_hermano_set vacío)

        Given: Un hermano que no pertenece a ningún cuerpo (cuerpos.values_list retorna lista vacía).
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: El servicio genera un set vacío de cuerpos.
            Se valida que se pasa el set() vacío correctamente a:
                1. _validar_hermano_apto_para_solicitar
                2. _validar_preferencias_insignia_tradicional
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = []
        set_vacio_esperado = set()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()

        mock_papeleta = MagicMock()
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)
        service._guardar_preferencias = MagicMock()
        
        mock_acto = MagicMock()

        service.procesar_solicitud_insignia_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            preferencias_data=[{'id': 1}],
            vinculado_a=None
        )

        mock_hermano.cuerpos.values_list.assert_called_with('nombre_cuerpo', flat=True)

        service._validar_hermano_apto_para_solicitar.assert_called_once_with(
            mock_hermano, 
            set_vacio_esperado
        )
        
        service._validar_preferencias_insignia_tradicional.assert_called_once_with(
            mock_hermano, 
            mock_acto, 
            [{'id': 1}], 
            set_vacio_esperado
        )



    # -------------------------------------------------------------------------
    # TEST VALIDAR UNICIDAD
    # -------------------------------------------------------------------------

    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.PapeletaSitio')
    def test_validar_unicidad_existe_papeleta_activa_lanza_excepcion(self, mock_papeleta_sitio):
        """
        Test: Verifica la unicidad cuando existe una papeleta activa.

        Given: Un hermano y un acto.
            Una consulta a la BD que indica que ya existe una papeleta activa.
        When: Se llama a _validar_unicidad.
        Then: Se lanza una excepción ValidationError.
            Se verifica que la query al ORM está correctamente construida.
        """
        service = SolicitudInsigniaService()
        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_estados = mock_papeleta_sitio.EstadoPapeleta
        mock_estados.ANULADA = 'ANULADA'
        mock_estados.NO_ASIGNADA = 'NO_ASIGNADA'

        mock_query_exclude = mock_papeleta_sitio.objects.filter.return_value.exclude.return_value
        mock_query_exclude.exists.return_value = True

        with self.assertRaises(ValidationError) as cm:
            service._validar_unicidad(mock_hermano, mock_acto)
            
        self.assertEqual(cm.exception.message, "Ya existe una solicitud activa (en proceso o asignada) para este acto.")

        mock_papeleta_sitio.objects.filter.assert_called_once_with(
            hermano=mock_hermano, 
            acto=mock_acto
        )
        mock_papeleta_sitio.objects.filter.return_value.exclude.assert_called_once_with(
            estado_papeleta__in=['ANULADA', 'NO_ASIGNADA']
        )



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.PapeletaSitio')
    def test_validar_unicidad_no_existe_papeleta_activa(self, mock_papeleta_sitio):
        """
        Test: Verifica la unicidad cuando NO existe una papeleta activa.

        Given: Un hermano y un acto.
            Una consulta a la BD que indica que no hay papeletas activas (o solo anuladas/no asignadas).
        When: Se llama a _validar_unicidad.
        Then: Pasa sin lanzar error.
            Se verifica que la query al ORM está correctamente construida.
        """
        service = SolicitudInsigniaService()
        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_estados = mock_papeleta_sitio.EstadoPapeleta
        mock_estados.ANULADA = 'ANULADA'
        mock_estados.NO_ASIGNADA = 'NO_ASIGNADA'

        mock_query_exclude = mock_papeleta_sitio.objects.filter.return_value.exclude.return_value
        mock_query_exclude.exists.return_value = False

        try:
            service._validar_unicidad(mock_hermano, mock_acto)
        except ValidationError:
            self.fail("No debería lanzar excepción si no hay papeletas activas o son ignorables.")

        mock_papeleta_sitio.objects.filter.assert_called_once_with(
            hermano=mock_hermano, 
            acto=mock_acto
        )
        mock_papeleta_sitio.objects.filter.return_value.exclude.assert_called_once_with(
            estado_papeleta__in=['ANULADA', 'NO_ASIGNADA']
        )



    # -------------------------------------------------------------------------
    # TEST VALIDAR HERMANO APTO PARA SOLICITAR
    # -------------------------------------------------------------------------

    def test_validar_hermano_apto_todas_las_validaciones_pasan(self):
        """
        Test: Todas las validaciones pasan

        Given: Un hermano y su set de cuerpos.
            Las tres validaciones internas están configuradas para no lanzar error.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se ejecutan las 3 validaciones en el orden lógico.
            Se pasan los argumentos correctos a cada una.
            El método termina sin lanzar ninguna excepción.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(name="HermanoTest")
        mock_cuerpos_set = {'Cuerpo A', 'Cuerpo B'}

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        manager = MagicMock()
        manager.attach_mock(service._validar_hermano_en_alta, 'en_alta')
        manager.attach_mock(service._validar_hermano_al_corriente_hasta_anio_anterior, 'al_corriente')
        manager.attach_mock(service._validar_pertenencia_cuerpos, 'cuerpos')

        service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos_set)

        service._validar_hermano_en_alta.assert_called_once_with(mock_hermano)
        service._validar_hermano_al_corriente_hasta_anio_anterior.assert_called_once_with(mock_hermano)
        service._validar_pertenencia_cuerpos.assert_called_once_with(mock_cuerpos_set)

        expected_calls = [
            call.en_alta(mock_hermano),
            call.al_corriente(mock_hermano),
            call.cuerpos(mock_cuerpos_set)
        ]
        self.assertEqual(manager.mock_calls, expected_calls)



    def test_validar_hermano_apto_falla_en_alta_corta_ejecucion(self):
        """
        Test: Falla _validar_hermano_en_alta

        Given: Un hermano que no está en alta.
            La validación _validar_hermano_en_alta lanza ValidationError.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se propaga la excepción ValidationError.
            Se valida que el flujo se corta inmediatamente:
                - NO se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
                - NO se llama a _validar_pertenencia_cuerpos.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_cuerpos = set()
        mensaje_error = "El hermano no está dado de alta."

        service._validar_hermano_en_alta = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos)

        self.assertEqual(cm.exception.message, mensaje_error)

        service._validar_hermano_en_alta.assert_called_once_with(mock_hermano)
        service._validar_hermano_al_corriente_hasta_anio_anterior.assert_not_called()
        service._validar_pertenencia_cuerpos.assert_not_called()



    def test_validar_hermano_apto_falla_en_contable_corta_ejecucion(self):
        """
        Test: Falla _validar_hermano_al_corriente_hasta_anio_anterior

        Given: Un hermano que está en alta pero tiene deudas.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se propaga la excepción ValidationError de la validación contable.
            Se valida el estado del flujo:
                - SÍ se llamó a _validar_hermano_en_alta.
                - NO se llamó a _validar_pertenencia_cuerpos (cortocircuito).
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_cuerpos = set()
        mensaje_error = "El hermano tiene cuotas pendientes."

        service._validar_hermano_en_alta = MagicMock()

        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        service._validar_pertenencia_cuerpos = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos)

        self.assertEqual(cm.exception.message, mensaje_error)

        service._validar_hermano_en_alta.assert_called_once_with(mock_hermano)
        service._validar_hermano_al_corriente_hasta_anio_anterior.assert_called_once_with(mock_hermano)
        service._validar_pertenencia_cuerpos.assert_not_called()



    def test_validar_hermano_apto_falla_en_pertenencia_cuerpos(self):
        """
        Test: Falla _validar_pertenencia_cuerpos

        Given: Un hermano en alta y sin deudas, pero que no pertenece 
            a los cuerpos requeridos para la insignia.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se propaga la excepción ValidationError de la validación de cuerpos.
            Se valida que se agotó toda la cadena de validación:
                - SÍ se llamó a _validar_hermano_en_alta.
                - SÍ se llamó a _validar_hermano_al_corriente_hasta_anio_anterior.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_cuerpos = {"Cuerpo Invalido"}
        mensaje_error = "El hermano no pertenece a los cuerpos necesarios."

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()

        service._validar_pertenencia_cuerpos = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos)

        self.assertEqual(cm.exception.message, mensaje_error)

        service._validar_hermano_en_alta.assert_called_once_with(mock_hermano)
        service._validar_hermano_al_corriente_hasta_anio_anterior.assert_called_once_with(mock_hermano)
        service._validar_pertenencia_cuerpos.assert_called_once_with(mock_cuerpos)



    def test_validar_hermano_apto_cuerpos_vacio_se_pasa_correctamente(self):
        """
        Test: CASOS LÍMITE IMPORTANTES (cuerpos_hermano_set vacío)

        Given: Un hermano que no pertenece a ningún cuerpo (set vacío).
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se valida que el set vacío se propaga íntegramente a la 
            validación de pertenencia.
            Esto garantiza que el orquestador no bloquea ni altera sets vacíos
            antes de que la lógica específica los evalúe.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(name="HermanoSinCuerpos")
        set_vacio = set()

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        service._validar_hermano_apto_para_solicitar(mock_hermano, set_vacio)

        service._validar_pertenencia_cuerpos.assert_called_once_with(set_vacio)

        args, _ = service._validar_pertenencia_cuerpos.call_args
        self.assertIsInstance(args[0], set)
        self.assertEqual(len(args[0]), 0)



    # -------------------------------------------------------------------------
    # TEST VALIDAR PERTENENCIA A CUERPOS
    # -------------------------------------------------------------------------

    def test_validar_pertenencia_cuerpos_vacio_pasa(self):
        """
        Test: cuerpos_hermano_set vacío

        Given: Un set vacío (el hermano no pertenece a ningún cuerpo específico).
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: El método no realiza ninguna acción y retorna None.
            No se lanza ValidationError.
        """
        service = SolicitudInsigniaService()

        cuerpos_vacio = set()

        resultado = service._validar_pertenencia_cuerpos(cuerpos_vacio)

        self.assertIsNone(resultado)


    def test_validar_pertenencia_cuerpos_permitidos_pasa(self):
        """
        Test: Todos los cuerpos permitidos

        Given: Un set de cuerpos que son subconjunto de los permitidos 
            (ej. NAZARENOS y JUNTA_GOBIERNO).
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: No se lanza ninguna excepción ValidationError.
            El método permite la solicitud ya que todos los cuerpos
            del hermano son aptos.
        """
        service = SolicitudInsigniaService()

        cuerpos_hermano = {
            CuerpoPertenencia.NombreCuerpo.NAZARENOS.value,
            CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value
        }

        try:
            service._validar_pertenencia_cuerpos(cuerpos_hermano)
        except ValidationError:
            self.fail("_validar_pertenencia_cuerpos lanzó ValidationError con cuerpos permitidos")


    def test_validar_pertenencia_cuerpos_mezcla_valido_e_invalido_falla(self):
        """
        Test: Mezcla de cuerpos válidos e inválidos

        Given: Un set con un cuerpo permitido (NAZARENOS) y uno no permitido (INVÁLIDO).
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: Se lanza una excepción ValidationError.
            El mensaje de error debe incluir el cuerpo 'INVÁLIDO'.
            El mensaje de error NO debe incluir el cuerpo 'NAZARENOS', 
            ya que este último es apto.
        """
        service = SolicitudInsigniaService()

        cuerpo_valido = CuerpoPertenencia.NombreCuerpo.NAZARENOS.value
        cuerpo_invalido = "INVÁLIDO"
        cuerpos_hermano = {cuerpo_valido, cuerpo_invalido}

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos(cuerpos_hermano)

        self.assertIn(cuerpo_invalido, cm.exception.message)

        self.assertNotIn(
            cuerpo_valido, 
            cm.exception.message,
            f"El cuerpo válido '{cuerpo_valido}' no debería aparecer en el mensaje de error."
        )


    def test_validar_pertenencia_cuerpos_multiples_no_permitidos_ordenados(self):
        """
        Test: Múltiples cuerpos no permitidos

        Given: Un set con varios cuerpos no permitidos: {"Z_CUERPO", "A_CUERPO", "M_CUERPO"}.
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: Se lanza una excepción ValidationError.
            El mensaje de error debe contener los tres cuerpos.
            Los cuerpos deben aparecer ordenados alfabéticamente en el string 
            final gracias al uso de sorted().
        """
        service = SolicitudInsigniaService()

        cuerpos_no_permitidos = {"Z_CUERPO", "A_CUERPO", "M_CUERPO"}

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos(cuerpos_no_permitidos)
        
        mensaje = cm.exception.message

        for cuerpo in cuerpos_no_permitidos:
            self.assertIn(cuerpo, mensaje)

        texto_esperado = "A_CUERPO, M_CUERPO, Z_CUERPO"
        self.assertTrue(
            mensaje.endswith(texto_esperado),
            f"Se esperaba que los cuerpos estuvieran ordenados así: '{texto_esperado}'. "
            f"Mensaje recibido: '{mensaje}'"
        )



    # -------------------------------------------------------------------------
    # TEST VALIDAR PREFERENCIA INSIGNIA
    # -------------------------------------------------------------------------

    def test_validar_preferencias_flujo_completo_correcto(self):
        """
        Test: Flujo completo correcto

        Given: Una lista de preferencias_data válida con dos puestos.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: 1. Se valida la existencia de puestos.
            2. Se extraen y validan prioridades y unicidad de puestos.
            3. Se llama a _validar_item_puesto por cada puesto en la lista.
            4. No se lanza ninguna excepción.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_cuerpos = {"NAZARENOS"}

        preferencias_data = [
            {"puesto_solicitado": "Puesto A", "orden_prioridad": 1},
            {"puesto_solicitado": "Puesto B", "orden_prioridad": 2}
        ]

        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            mock_hermano, mock_acto, preferencias_data, mock_cuerpos
        )

        service._resolver_y_validar_existencia_puestos.assert_called_once_with(preferencias_data)

        service._validar_prioridades_consecutivas.assert_called_once_with([1, 2])
        service._validar_puestos_unicos.assert_called_once_with(["Puesto A", "Puesto B"])

        esperado_llamadas = [
            call(mock_cuerpos, mock_acto, "Puesto A"),
            call(mock_cuerpos, mock_acto, "Puesto B")
        ]
        service._validar_item_puesto.assert_has_calls(esperado_llamadas, any_order=True)
        self.assertEqual(service._validar_item_puesto.call_count, 2)


    def test_validar_preferencias_vacia_falla(self):
        """
        Test: preferencias_data vacío

        Given: Una lista de preferencias vacía ([]).
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se lanza ValidationError con el mensaje específico.
            Se garantiza que NO se llama a ninguna otra validación 
            posterior (fail fast).
        """
        service = SolicitudInsigniaService()

        preferencias_vacias = []
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_vacias, set()
            )
        
        self.assertEqual(cm.exception.message, "Debe indicar al menos una preferencia.")

        service._resolver_y_validar_existencia_puestos.assert_not_called()
        service._validar_prioridades_consecutivas.assert_not_called()
        service._validar_item_puesto.assert_not_called()


    def test_validar_preferencias_falla_en_resolucion_puestos(self):
        """
        Test: _resolver_y_validar_existencia_puestos falla

        Given: Una lista de preferencias, pero el validador de existencia 
            determina que un puesto no es válido.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: La excepción ValidationError se propaga hacia arriba.
            Se verifica que NO se entra en el bucle de procesamiento de puestos
            ni se llaman a las validaciones de prioridades o unicidad.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [{"puesto_solicitado": "Puesto Fantasma", "orden_prioridad": 1}]
        mensaje_error = "Uno de los puestos solicitados no existe."

        service._resolver_y_validar_existencia_puestos = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )
        
        self.assertEqual(cm.exception.message, mensaje_error)

        service._validar_prioridades_consecutivas.assert_not_called()
        service._validar_puestos_unicos.assert_not_called()
        service._validar_item_puesto.assert_not_called()


    def test_validar_preferencias_datos_incompletos_falla(self):
        """
        Test: Datos incompletos (Falta puesto o prioridad)

        Given: Una preferencia que omite el puesto solicitado o el orden de prioridad.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se lanza ValidationError: "Datos de preferencia incompletos."
            Se detiene la ejecución antes de llamar a las validaciones finales.
        """
        service = SolicitudInsigniaService()

        casos = [
            [{"orden_prioridad": 1}],  # Falta puesto_solicitado
            [{"puesto_solicitado": "Incienso"}],  # Falta orden_prioridad
            [{"puesto_solicitado": None, "orden_prioridad": 1}],  # Puesto es None
            [{"puesto_solicitado": "Incienso", "orden_prioridad": None}],  # Prioridad es None
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_item_puesto = MagicMock()

        for preferencias_data in casos:
            with self.subTest(preferencias_data=preferencias_data):
                with self.assertRaises(ValidationError) as cm:
                    service._validar_preferencias_insignia_tradicional(
                        MagicMock(), MagicMock(), preferencias_data, set()
                    )
                self.assertEqual(cm.exception.message, "Datos de preferencia incompletos.")

        service._validar_prioridades_consecutivas.assert_not_called()
        service._validar_item_puesto.assert_not_called()


    def test_validar_preferencias_falla_en_prioridades_consecutivas(self):
        """
        Test: _validar_prioridades_consecutivas falla

        Given: Una lista de preferencias con prioridades no consecutivas (ej: 1, 3).
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se propaga la excepción de prioridades.
            Se garantiza que NO se llama a _validar_puestos_unicos ni 
            a las validaciones de ítems individuales.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Puesto 1", "orden_prioridad": 1},
            {"puesto_solicitado": "Puesto 2", "orden_prioridad": 3}
        ]
        mensaje_error = "Las prioridades deben ser consecutivas."

        service._resolver_y_validar_existencia_puestos = MagicMock()

        service._validar_prioridades_consecutivas = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )
        
        self.assertEqual(cm.exception.message, mensaje_error)

        service._validar_prioridades_consecutivas.assert_called_once()
        service._validar_puestos_unicos.assert_not_called()
        service._validar_item_puesto.assert_not_called()


    def test_validar_preferencias_falla_en_puestos_unicos(self):
        """
        Test: _validar_puestos_unicos falla

        Given: Una lista de preferencias donde se repite el mismo puesto.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se propaga la excepción de unicidad.
            Se garantiza que NO se llega a la validación de ítems individuales
            dentro del bucle final.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Vara 1", "orden_prioridad": 1},
            {"puesto_solicitado": "Vara 1", "orden_prioridad": 2}
        ]
        mensaje_error = "No puede solicitar el mismo puesto varias veces."

        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()

        service._validar_puestos_unicos = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        service._validar_item_puesto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )
        
        self.assertEqual(cm.exception.message, mensaje_error)

        service._validar_puestos_unicos.assert_called_once()
        service._validar_item_puesto.assert_not_called()


    def test_validar_preferencias_mezcla_falla_en_primer_invalido(self):
        """
        Test: Mezcla de válidos e inválidos

        Given: Una lista de preferencias donde:
            1. La primera es válida.
            2. La segunda es inválida (provocará error).
            3. La tercera es válida.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se lanza ValidationError al llegar al segundo ítem.
            Se verifica el comportamiento 'Fail-Fast': el tercer ítem 
            NUNCA llega a procesarse (la validación se detiene).
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "VÁLIDO_1", "orden_prioridad": 1},
            {"puesto_solicitado": "ERROR_AQUÍ", "orden_prioridad": 2},
            {"puesto_solicitado": "VÁLIDO_2", "orden_prioridad": 3},
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()

        def side_effect_validation(cuerpos, acto, puesto):
            if puesto == "ERROR_AQUÍ":
                raise ValidationError("Puesto no permitido")
            return None

        service._validar_item_puesto = MagicMock(side_effect=side_effect_validation)

        with self.assertRaises(ValidationError):
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )

        self.assertEqual(service._validar_item_puesto.call_count, 2)

        llamadas = [call[0][2] for call in service._validar_item_puesto.call_args_list]
        self.assertNotIn("VÁLIDO_2", llamadas, "El flujo debería haberse detenido en el error.")



    # -------------------------------------------------------------------------
    # TEST VALIDAR ITEM PUESTO
    # -------------------------------------------------------------------------

    def test_validar_item_puesto_totalmente_valido_pasa(self):
        """
        Test: Puesto completamente válido

        Given: Un puesto que:
            - Pertenece al acto correcto.
            - Es una insignia.
            - Está disponible.
            - No es exclusivo de la Junta de Gobierno.
        When: Se llama a _validar_item_puesto.
        Then: No se lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.id = 1

        mock_puesto = MagicMock()
        mock_puesto.nombre = "Vara de Acompañamiento"
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.solo_junta_gobierno = False

        cuerpos_hermano = {"NAZARENOS"}

        try:
            service._validar_item_puesto(cuerpos_hermano, mock_acto, mock_puesto)
        except ValidationError:
            self.fail("_validar_item_puesto() lanzó ValidationError con un puesto válido")


    def test_validar_item_puesto_de_otro_acto_falla(self):
        """
        Test: Puesto de otro acto

        Given: Un acto con ID 1 y un puesto que pertenece al acto con ID 99.
        When: Se llama a _validar_item_puesto.
        Then: Se lanza ValidationError con el mensaje: 
            "El puesto 'X' no pertenece a este acto."
            Se verifica que es la primera validación (fail-fast).
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Vara de Tramo 1"
        mock_puesto.acto_id = 99

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(set(), mock_acto, mock_puesto)
        
        self.assertEqual(
            cm.exception.message, 
            f"El puesto '{mock_puesto.nombre}' no pertenece a este acto."
        )


    def test_validar_item_puesto_no_es_insignia_falla(self):
        """
        Test: Puesto no es insignia

        Given: Un puesto cuyo tipo_puesto tiene es_insignia = False.
        When: Se llama a _validar_item_puesto.
        Then: Se lanza ValidationError con el mensaje:
            "El puesto 'X' no es una insignia."
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Costalero"
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(set(), mock_acto, mock_puesto)
        
        self.assertEqual(
            cm.exception.message, 
            f"El puesto '{mock_puesto.nombre}' no es una insignia."
        )


    def test_validar_item_puesto_no_disponible_falla(self):
        """
        Test: Puesto no disponible

        Given: Un puesto que existe y es una insignia, pero tiene disponible = False.
        When: Se llama a _validar_item_puesto.
        Then: Se lanza ValidationError con el mensaje:
            "El puesto 'X' no está marcado como disponible."
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Bocina 1"
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(set(), mock_acto, mock_puesto)
        
        self.assertEqual(
            cm.exception.message, 
            f"El puesto '{mock_puesto.nombre}' no está marcado como disponible."
        )


    def test_validar_item_puesto_exclusivo_junta_sin_permiso_falla(self):
        """
        Test: Puesto exclusivo de Junta sin ser Junta

        Given: Un puesto con solo_junta_gobierno = True.
            Un hermano cuyos cuerpos no incluyen 'JUNTA_GOBIERNO'.
        When: Se llama a _validar_item_puesto.
        Then: Se lanza ValidationError con el mensaje:
            "El puesto 'X' es exclusivo para Junta de Gobierno."
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Vara de Tesorero"
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.solo_junta_gobierno = True

        cuerpos_hermano = {CuerpoPertenencia.NombreCuerpo.NAZARENOS}

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(cuerpos_hermano, mock_acto, mock_puesto)
        
        self.assertEqual(
            cm.exception.message, 
            f"El puesto '{mock_puesto.nombre}' es exclusivo para Junta de Gobierno."
        )


    def test_validar_item_puesto_exclusivo_junta_con_usuario_de_junta_pasa(self):
        """
        Test: Puesto de Junta con usuario de Junta

        Given: Un puesto con solo_junta_gobierno = True.
            Un set de cuerpos que incluye JUNTA_GOBIERNO.
        When: Se llama a _validar_item_puesto.
        Then: No se lanza ninguna excepción.
            Se confirma que la validación de pertenencia es efectiva.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=10)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Vara de Hermano Mayor"
        mock_puesto.acto_id = 10
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.solo_junta_gobierno = True

        cuerpos_hermano = {CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO}

        try:
            service._validar_item_puesto(cuerpos_hermano, mock_acto, mock_puesto)
        except ValidationError:
            self.fail("_validar_item_puesto() lanzó ValidationError con un usuario apto de Junta")



    # -------------------------------------------------------------------------
    # TEST VALIDAR LIMITE PREFERENCIAS
    # -------------------------------------------------------------------------

    def test_validar_limites_lista_vacia_pasa(self):
        """
        Test: Lista vacía

        Given: Una lista de preferencias vacía ([]).
        When: Se llama a _validar_limites_preferencias.
        Then: No lanza excepción. 
            Aunque otras validaciones (como la de 'al menos una') fallen,
            este método específico solo se encarga del techo, no del suelo.
        """
        service = SolicitudInsigniaService()
        service.MAX_PREFERENCIAS_PERMITIDAS = 20

        service._validar_limites_preferencias([])

    def test_validar_limites_menor_que_el_maximo_pasa(self):
        """
        Test: Menos del límite

        Given: El límite es 20 y el usuario envía una lista con 3 elementos.
        When: Se llama a _validar_limites_preferencias.
        Then: No lanza excepción. 
            El comportamiento es normal al estar dentro del rango permitido.
        """
        service = SolicitudInsigniaService()
        service.MAX_PREFERENCIAS_PERMITIDAS = 20
        
        preferencias_data = [
            {"puesto": 1},
            {"puesto": 2},
            {"puesto": 3}
        ]

        service._validar_limites_preferencias(preferencias_data)

    def test_validar_limites_exactamente_el_maximo_pasa(self):
        """
        Test: Exactamente el límite (20)

        Given: El límite configurado es 20.
            La lista de preferencias contiene exactamente 20 elementos.
        When: Se llama a _validar_limites_preferencias.
        Then: No se lanza ninguna excepción.
            Se confirma que el límite es inclusivo (n <= MAX).
        """
        service = SolicitudInsigniaService()
        service.MAX_PREFERENCIAS_PERMITIDAS = 20

        preferencias_data = [{"puesto": i} for i in range(20)]

        service._validar_limites_preferencias(preferencias_data)

    def test_validar_limites_supera_el_maximo_por_uno_falla(self):
        """
        Test: Supera el límite por 1

        Given: El límite configurado es 20.
            La lista contiene 21 elementos.
        When: Se llama a _validar_limites_preferencias.
        Then: Se lanza ValidationError.
            Mensaje: "No puede solicitar más de 20 puestos."
        """
        service = SolicitudInsigniaService()
        service.MAX_PREFERENCIAS_PERMITIDAS = 20

        preferencias_data = [{"puesto": i} for i in range(21)]

        with self.assertRaises(ValidationError) as cm:
            service._validar_limites_preferencias(preferencias_data)
        
        self.assertEqual(
            cm.exception.message, 
            "No puede solicitar más de 20 puestos."
        )



    # -------------------------------------------------------------------------
    # TEST VALIDAR EDAD MINIMA INSIGNIA
    # -------------------------------------------------------------------------

    def test_validar_edad_mayor_a_18_pasa(self):
        """
        Test: Edad mayor a 18 (caso claro)

        Given: Fecha de referencia (inicio_solicitud) = 2026-04-01.
            Fecha de nacimiento = 2000-01-01 (Edad: 26 años).
        When: Se llama a _validar_edad_minima_insignia.
        Then: No lanza excepción.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2000, 1, 1)
        
        mock_acto = MagicMock()

        mock_acto.inicio_solicitud = datetime(2026, 4, 1)

        service._validar_edad_minima_insignia(mock_hermano, mock_acto)


    def test_validar_exactamente_18_anos_cumplidos_pasa(self):
        """
        Test: Exactamente 18 años cumplidos

        Given: Fecha de referencia = 2026-04-20.
            Fecha de nacimiento = 2008-04-20 (Cumple 18 justo el día de referencia).
        When: Se llama a _validar_edad_minima_insignia.
        Then: No lanza excepción.
            Valida que el cálculo incluye el día del cumpleaños como 'cumplido'.
        """
        service = SolicitudInsigniaService()

        fecha_referencia = datetime(2026, 4, 20)

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 4, 20)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = fecha_referencia

        service._validar_edad_minima_insignia(mock_hermano, mock_acto)


    def test_validar_edad_usa_inicio_solicitud_del_acto(self):
        """
        Test: Usa acto.inicio_solicitud como referencia

        Given: Un acto con inicio_solicitud el 2026-03-01.
            Un hermano que cumple 18 el 2026-03-05.
        When: Se llama a _validar_edad_minima_insignia.
        Then: Debe lanzar ValidationError porque a fecha de INICIO 
            de solicitud aún no tenía los 18, aunque hoy ya los tenga.
            Valida que se usa .date() del acto y no la fecha actual.
        """
        service = SolicitudInsigniaService()

        fecha_inicio = datetime(2026, 3, 1)

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 3, 5)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = fecha_inicio

        with self.assertRaises(ValidationError) as cm:
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)

        self.assertIn("01/03/2026", cm.exception.message)


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.timezone.now')
    def test_validar_edad_cae_a_timezone_now_si_no_hay_inicio(self, mock_now):
        """
        Test: Usa timezone.now() si no hay inicio

        Given: Un acto con inicio_solicitud = None.
            Simulamos que "hoy" es 2026-04-26.
            Un hermano que cumple 18 justo hoy (2008-04-26).
        When: Se llama a _validar_edad_minima_insignia.
        Then: No lanza excepción. 
            Valida que el sistema usa la fecha mockeada de timezone.now().
        """
        service = SolicitudInsigniaService()

        mock_now.return_value = datetime(2026, 4, 26, 12, 0, 0)
        
        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 4, 26)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = None

        service._validar_edad_minima_insignia(mock_hermano, mock_acto)

        mock_now.assert_called_once()


    def test_validar_edad_sin_fecha_nacimiento_falla(self):
        """
        Test: Sin fecha de nacimiento

        Given: Un hermano que no tiene informada su fecha_nacimiento (None).
        When: Se llama a _validar_edad_minima_insignia.
        Then: Se lanza ValidationError con el mensaje que indica 
            contactar con secretaría.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = None
        
        mock_acto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)
        
        self.assertEqual(
            cm.exception.message,
            "No consta su fecha de nacimiento en la base de datos. "
            "Contacte con secretaría para actualizar su ficha antes de solicitar insignia."
        )


    def test_validar_edad_menor_de_18_anos_falla(self):
        """
        Test: Menor de 18 años

        Given: Fecha de referencia = 2026-04-01.
            Fecha de nacimiento = 2008-05-01 (Tiene 17 años).
        When: Se llama a _validar_edad_minima_insignia.
        Then: Se lanza ValidationError.
            El mensaje incluye la fecha formateada '01/04/2026'.
        """
        service = SolicitudInsigniaService()

        fecha_corte = datetime(2026, 4, 1)

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 5, 1)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = fecha_corte

        with self.assertRaises(ValidationError) as cm:
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)

        self.assertIn("debe ser mayor de 18 años", cm.exception.message)
        self.assertIn("01/04/2026", cm.exception.message)


    def test_validar_edad_cumple_manana_falla(self):
        """
        Test: Cumple 18 justo después del inicio

        Given: Fecha de referencia = 2026-04-20.
            Fecha de nacimiento = 2008-04-21 (Cumple 18 mañana).
        When: Se llama a _validar_edad_minima_insignia.
        Then: Se lanza ValidationError.
            Valida que el sistema no "redondea" la edad por año,
            sino que exige el cumplimiento exacto.
        """
        service = SolicitudInsigniaService()

        fecha_referencia = datetime(2026, 4, 20)

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 4, 21)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = fecha_referencia

        with self.assertRaises(ValidationError) as cm:
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)
        
        self.assertIn("debe ser mayor de 18 años", cm.exception.message)


    def test_validar_edad_nacimiento_bisiesto_pasa(self):
        """
        Test: Año bisiesto

        Given: Fecha de nacimiento = 29 de febrero de 2008 (Año bisiesto).
            Fecha de referencia = 28 de febrero de 2026 (No bisiesto).
        When: Se llama a _validar_edad_minima_insignia.
        Then: No lanza excepción de sistema (ValueError) y calcula 17 años correctamente.
            (2026 - 2008) - 1 (porque el cumpleaños 29-Feb no ha llegado el 28-Feb).
        """
        service = SolicitudInsigniaService()

        fecha_referencia = datetime(2026, 2, 28)
        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 2, 29)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = fecha_referencia

        with self.assertRaises(ValidationError):
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)


    def test_validar_edad_nacimiento_bisiesto_cumplido_pasa(self):
        """
        Test: Año bisiesto cumplido

        Given: Fecha de nacimiento = 29 de febrero de 2008.
            Fecha de referencia = 1 de marzo de 2026.
        When: Se llama a _validar_edad_minima_insignia.
        Then: No lanza excepción.
            (2026 - 2008) - 0 (porque marzo > febrero). Edad = 18.
        """
        service = SolicitudInsigniaService()
        mock_hermano = MagicMock(fecha_nacimiento=date(2008, 2, 29))
        mock_acto = MagicMock(inicio_solicitud=datetime(2026, 3, 1))

        service._validar_edad_minima_insignia(mock_hermano, mock_acto)



    # -------------------------------------------------------------------------
    # TEST VALIDAR CONFIGURACIÓN ACTO TRADICIONAL
    # -------------------------------------------------------------------------

    def test_validar_configuracion_acto_valido_pasa(self):
        """
        Test: Acto válido completo

        Given: Un objeto Acto con:
            - tipo_acto_id presente.
            - tipo_acto.requiere_papeleta = True.
            - modalidad = Acto.ModalidadReparto.TRADICIONAL.
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: No se lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.nombre = "Salida Procesional"
        mock_acto.tipo_acto_id = 1
        mock_acto.tipo_acto.requiere_papeleta = True
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

        service._validar_configuracion_acto_tradicional(mock_acto)


    def test_validar_configuracion_acto_es_none_falla(self):
        """
        Test: Acto es None

        Given: Un valor None en lugar de una instancia de Acto.
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: Se lanza ValidationError.
            Mensaje: {"tipo_acto": "El tipo de acto es obligatorio."}
        """
        service = SolicitudInsigniaService()

        with self.assertRaises(ValidationError) as cm:
            service._validar_configuracion_acto_tradicional(None)

        self.assertEqual(
            cm.exception.message_dict, 
            {"tipo_acto": ["El tipo de acto es obligatorio."]}
        )


    def test_validar_configuracion_acto_sin_tipo_id_falla(self):
        """
        Test: tipo_acto_id es None

        Given: Un objeto Acto que existe, pero no tiene asignado un tipo_acto_id.
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: Se lanza ValidationError con el mismo mensaje de obligatoriedad.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.tipo_acto_id = None

        with self.assertRaises(ValidationError) as cm:
            service._validar_configuracion_acto_tradicional(mock_acto)
        
        self.assertEqual(
            cm.exception.message_dict, 
            {"tipo_acto": ["El tipo de acto es obligatorio."]}
        )


    def test_validar_configuracion_acto_sin_papeleta_falla(self):
        """
        Test: requiere_papeleta = False

        Given: Un acto válido pero cuyo tipo_acto tiene requiere_papeleta = False.
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: Se lanza ValidationError con el mensaje:
            "El acto 'X' no admite solicitudes de papeleta."
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.nombre = "Vía Crucis"
        mock_acto.tipo_acto_id = 1
        mock_acto.tipo_acto.requiere_papeleta = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_configuracion_acto_tradicional(mock_acto)
        
        self.assertEqual(
            cm.exception.message, 
            f"El acto '{mock_acto.nombre}' no admite solicitudes de papeleta."
        )


    def test_validar_configuracion_acto_modalidad_incorrecta_falla(self):
        """
        Test: modalidad ≠ TRADICIONAL

        Given: Un acto con modalidad diferente a TRADICIONAL (ej: SORTEO).
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: Se lanza ValidationError informando de la exclusividad del proceso.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.tipo_acto_id = 1
        mock_acto.tipo_acto.requiere_papeleta = True

        mock_acto.modalidad = "SORTEO" 

        with self.assertRaises(ValidationError) as cm:
            service._validar_configuracion_acto_tradicional(mock_acto)
        
        self.assertEqual(
            cm.exception.message, 
            "Este proceso es exclusivo para actos de modalidad TRADICIONAL."
        )


    def test_validar_configuracion_acto_tipo_acto_nulo_lanza_attribute_error(self):
        """
        Test: tipo_acto_id existe pero tipo_acto es None

        Given: Un acto con tipo_acto_id = 1, pero acto.tipo_acto es None.
        When: Se llama a _validar_configuracion_acto_tradicional e intenta 
            acceder a .requiere_papeleta.
        Then: Se lanza AttributeError. 
            Este test ayuda a identificar que la validación inicial de 
            tipo_acto_id no es suficiente si la relación no está cargada.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.tipo_acto_id = 1
        mock_acto.tipo_acto = None

        with self.assertRaises(AttributeError):
            service._validar_configuracion_acto_tradicional(mock_acto)



    # -------------------------------------------------------------------------
    # TEST VALIDAR PLAZO VIGENTE
    # -------------------------------------------------------------------------

    def test_validar_plazo_fecha_dentro_del_rango_pasa(self):
        """
        Test: Fecha dentro del rango

        Given: Un rango del 01/04 al 10/04.
            El momento actual ('ahora') es 05/04.
        When: Se llama a _validar_plazo_vigente.
        Then: No lanza ninguna excepción.
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 4, 1, 9, 0)
        fin = datetime(2026, 4, 10, 20, 0)
        ahora = datetime(2026, 4, 5, 12, 0)
        nombre = "Solicitud"

        service._validar_plazo_vigente(ahora, inicio, fin, nombre)


    def test_validar_plazo_exactamente_en_limites_pasa(self):
        """
        Test: Fechas exactamente en los límites (Inicio y Fin)

        Given: Un plazo configurado con fechas de inicio y fin.
            'ahora' coincide exactamente con el inicio o con el fin.
        When: Se llama a _validar_plazo_vigente.
        Then: No lanza excepción.
            Valida que los límites inferior y superior son inclusivos.
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 4, 1, 9, 0, 0)
        fin = datetime(2026, 4, 10, 20, 0, 0)
        
        casos = [
            ("Límite Inferior", inicio),
            ("Límite Superior", fin)
        ]

        for nombre_caso, ahora in casos:
            with self.subTest(caso=nombre_caso):
                try:
                    service._validar_plazo_vigente(ahora, inicio, fin, "Prueba")
                except ValidationError:
                    self.fail(f"_validar_plazo_vigente falló erróneamente en el caso: {nombre_caso}")


    def test_validar_plazo_configuracion_incompleta_falla(self):
        """
        Test: Configuración de plazos faltante

        Given: Un plazo de 'Solicitud' donde falta el inicio, el fin o ambos.
        When: Se llama a _validar_plazo_vigente.
        Then: Lanza ValidationError indicando que el plazo no está configurado.
        """
        service = SolicitudInsigniaService()

        ahora = datetime(2026, 4, 5, 12, 0)
        inicio_valido = datetime(2026, 4, 1, 9, 0)
        fin_valido = datetime(2026, 4, 10, 20, 0)
        nombre = "Solicitud"

        casos = [
            ("Inicio None", None, fin_valido),
            ("Fin None", inicio_valido, None),
            ("Ambos None", None, None)
        ]

        for nombre_caso, inicio, fin in casos:
            with self.subTest(caso=nombre_caso):
                with self.assertRaises(ValidationError) as cm:
                    service._validar_plazo_vigente(ahora, inicio, fin, nombre)
                
                self.assertEqual(
                    cm.exception.message, 
                    f"El plazo de {nombre} no está configurado en el acto."
                )


    def test_validar_plazo_fecha_antes_del_inicio_falla(self):
        """
        Test: Fecha antes del inicio

        Given: El plazo abre el 01/04 a las 09:00:00.
            El hermano intenta solicitar el 01/04 a las 08:59:59.
        When: Se llama a _validar_plazo_vigente.
        Then: Lanza ValidationError con el mensaje:
            "El plazo de solicitud de X aún no ha comenzado."
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 4, 1, 9, 0, 0)
        fin = datetime(2026, 4, 10, 20, 0, 0)
        ahora = datetime(2026, 4, 1, 8, 59, 59)
        nombre = "Solicitud"

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, nombre)
        
        self.assertEqual(
            cm.exception.message, 
            f"El plazo de solicitud de {nombre} aún no ha comenzado."
        )


    def test_validar_plazo_fecha_despues_del_fin_falla(self):
        """
        Test: Fecha después del fin

        Given: El plazo finaliza el 10/04 a las 20:00:00.
            El hermano intenta solicitar el 10/04 a las 20:00:01.
        When: Se llama a _validar_plazo_vigente.
        Then: Lanza ValidationError con el mensaje:
            "El plazo de solicitud de X ha finalizado."
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 4, 1, 9, 0, 0)
        fin = datetime(2026, 4, 10, 20, 0, 0)
        ahora = datetime(2026, 4, 10, 20, 0, 1)
        nombre = "Solicitud"

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, nombre)
        
        self.assertEqual(
            cm.exception.message, 
            f"El plazo de solicitud de {nombre} ha finalizado."
        )



    # -------------------------------------------------------------------------
    # TEST VALIDAR HERMANO EN ALTA
    # -------------------------------------------------------------------------

    def test_validar_hermano_en_alta_pasa(self):
        """
        Test: Hermano en estado ALTA

        Given: Un objeto hermano con estado_hermano = ALTA.
        When: Se llama a _validar_hermano_en_alta.
        Then: No se lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.estado_hermano = Hermano.EstadoHermano.ALTA

        service._validar_hermano_en_alta(mock_hermano)


    def test_validar_hermano_distinto_de_alta_falla(self):
        """
        Test: Hermano en cualquier estado distinto de ALTA

        Given: Diferentes estados no permitidos (BAJA, FALLECIDO, SUSPENDIDO, None, etc.).
        When: Se llama a _validar_hermano_en_alta.
        Then: En todos los casos lanza ValidationError con el mensaje:
            "Solo los hermanos en estado ALTA pueden solicitar papeleta."
        """
        service = SolicitudInsigniaService()

        estados_invalidos = [
            "BAJA", 
            "FALLECIDO", 
            "SUSPENDIDO", 
            "SOLICITUD_PENDIENTE",
            None
        ]

        for estado in estados_invalidos:
            with self.subTest(estado=estado):
                mock_hermano = MagicMock()
                mock_hermano.estado_hermano = estado
                
                with self.assertRaises(ValidationError) as cm:
                    service._validar_hermano_en_alta(mock_hermano)
                
                self.assertEqual(
                    cm.exception.message, 
                    "Solo los hermanos en estado ALTA pueden solicitar papeleta."
                )



    # -------------------------------------------------------------------------
    # TEST VALIDAR HERMANO AL CORRIENTE HASTA EL AÑO ANTERIOR
    # -------------------------------------------------------------------------

    @patch('django.utils.timezone.now')
    def test_validar_al_corriente_con_historial_y_sin_deuda_pasa(self, mock_now):
        """
        Test: Hermano sin deuda y con historial

        Given: Un hermano que tiene cuotas en años anteriores (exists=True).
            No se encuentran cuotas en estado PENDIENTE/DEVUELTA (deuda=None).
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: No lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()
        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None
        mock_hermano.cuotas.filter.return_value.exists.return_value = True

        service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)


    @patch('django.utils.timezone.now')
    def test_validar_deuda_activa_bloquea_solicitud(self, mock_now):
        """
        Test: Tiene deuda pendiente o devuelta

        Given: El hermano tiene una cuota en estado PENDIENTE o DEVUELTA de un año anterior.
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: Lanza ValidationError con el mensaje específico del año de la deuda.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()
        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {
            'anio': 2023
        }

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        
        self.assertIn("cuota pendiente o devuelta del año 2023", cm.exception.message)
        self.assertIn("contacte con tesorería", cm.exception.message)


    @patch('django.utils.timezone.now')
    def test_validar_deuda_justo_en_anio_limite_falla(self, mock_now):
        """
        Test: Cuota impagada justo en el año límite (anio == anio_limite)

        Given: Año actual 2026 -> Límite 2025.
            El hermano tiene una cuota PENDIENTE de 2025.
        When: Se llama al servicio.
        Then: Lanza ValidationError porque la inclusión del límite es exacta (<=).
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()
        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {
            'anio': 2025
        }

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        
        self.assertIn("del año 2025", cm.exception.message)


    @patch('django.utils.timezone.now')
    def test_validar_al_corriente_sin_historial_falla(self, mock_now):
        """
        Test: No tiene historial

        Given: Año actual = 2026.
            La consulta de deuda no devuelve nada (deuda = None).
            La consulta de historial devuelve False (no existen cuotas hasta 2025).
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: Lanza ValidationError indicando que no constan cuotas registradas.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()
        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None
        mock_hermano.cuotas.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        
        self.assertEqual(
            cm.exception.message, 
            "No constan cuotas registradas hasta el año 2025. Contacte con secretaría para verificar su ficha."
        )


    @patch('django.utils.timezone.now')
    def test_validar_al_corriente_cuotas_futuras_no_cuentan_como_historial(self, mock_now):
        """
        Test: Cuotas fuera del límite pero sin historial anterior

        Given: Año actual = 2026 (Límite = 2025).
            El hermano NO tiene cuotas en 2025 o anteriores (exists=False).
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: Lanza ValidationError por falta de historial, sin importar si 
            tuviera cuotas generadas en el año actual (2026).
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()
        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None
        mock_hermano.cuotas.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        
        self.assertIn("No constan cuotas registradas hasta el año 2025", cm.exception.message)



    # -------------------------------------------------------------------------
    # TEST VALIDAR EXISTENCIA PUESTO
    # -------------------------------------------------------------------------

    @patch('api.models.Puesto.objects.filter')
    def test_resolver_ids_validos_sustituye_por_instancias(self, mock_filter):
        """
        Test: Sustitución de IDs numéricos y strings

        Given: Una lista de preferencias con IDs enteros y strings numéricos.
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: 
            - Se llama a la BD con los IDs enteros correctos.
            - Se utiliza select_related para optimizar.
            - La lista original se actualiza in-place con las instancias Puesto.
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 1},
            {"puesto_solicitado": "2"},
            {"puesto_solicitado": " 3 "}
        ]

        mock_p1 = MagicMock(spec=Puesto, id=1)
        mock_p2 = MagicMock(spec=Puesto, id=2)
        mock_p3 = MagicMock(spec=Puesto, id=3)

        mock_filter.return_value.select_related.return_value = [mock_p1, mock_p2, mock_p3]

        service._resolver_y_validar_existencia_puestos(preferencias)

        mock_filter.assert_called_once()
        mock_filter.return_value.select_related.assert_called_once_with('tipo_puesto')
        
        args, kwargs = mock_filter.call_args
        self.assertSetEqual(set(kwargs['id__in']), {1, 2, 3})

        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p1)
        self.assertEqual(preferencias[1]["puesto_solicitado"], mock_p2)
        self.assertEqual(preferencias[2]["puesto_solicitado"], mock_p3)


    @patch('api.models.Puesto.objects.filter')
    def test_resolver_mezcla_instancias_nulos_y_duplicados(self, mock_filter):
        """
        Test: Mezcla de datos y optimización de búsqueda

        Given: Una lista con un ID duplicado, un objeto Puesto real y un valor None.
        When: Se llama al servicio.
        Then: 
            - Solo se busca en BD el ID único (ignorando duplicados, None y objetos).
            - Se sustituyen correctamente todas las apariciones del ID.
            - El objeto Puesto original y el None se mantienen intactos.
        """
        service = SolicitudInsigniaService()

        puesto_existente = MagicMock(spec=Puesto)
        preferencias = [
            {"puesto_solicitado": 10},
            {"puesto_solicitado": 10},
            {"puesto_solicitado": puesto_existente},
            {"puesto_solicitado": None}
        ]
        
        mock_p10 = MagicMock(spec=Puesto, id=10)
        mock_filter.return_value.select_related.return_value = [mock_p10]

        service._resolver_y_validar_existencia_puestos(preferencias)

        call_ids = mock_filter.call_args[1]['id__in']
        self.assertEqual(list(call_ids), [10])

        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p10)
        self.assertEqual(preferencias[1]["puesto_solicitado"], mock_p10)
        self.assertEqual(preferencias[2]["puesto_solicitado"], puesto_existente)
        self.assertIsNone(preferencias[3]["puesto_solicitado"])


    def test_resolver_formato_string_no_numerico_falla(self):
        """
        Test: Formato inválido

        Given: Una preferencia con un valor no numérico (ej. "ABC").
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: Lanza ValidationError indicando el formato inválido.
        """
        service = SolicitudInsigniaService()

        preferencias = [{"puesto_solicitado": "ABC"}]

        with self.assertRaises(ValidationError) as cm:
            service._resolver_y_validar_existencia_puestos(preferencias)
        
        self.assertEqual(
            cm.exception.message, 
            "Formato de puesto inválido: ABC"
        )


    @patch('api.models.Puesto.objects.filter')
    def test_resolver_ids_faltantes_en_bd_falla(self, mock_filter):
        """
        Test: IDs no existentes en BD

        Given: Se solicitan los IDs [1, 2, 3].
            La base de datos solo devuelve el objeto para el ID [1].
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: Lanza ValidationError listando los IDs faltantes (2, 3).
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 1},
            {"puesto_solicitado": 2},
            {"puesto_solicitado": 3}
        ]

        mock_p1 = MagicMock(spec=Puesto, id=1)
        mock_filter.return_value.select_related.return_value = [mock_p1]

        with self.assertRaises(ValidationError) as cm:
            service._resolver_y_validar_existencia_puestos(preferencias)

        self.assertIn("Los siguientes IDs de puesto no existen", cm.exception.message)
        self.assertIn("2", cm.exception.message)
        self.assertIn("3", cm.exception.message)


    @patch('api.models.Puesto.objects.filter')
    def test_resolver_sin_ids_a_buscar_no_ejecuta_query(self, mock_filter):
        """
        Test: Omisión de query por falta de IDs

        Given: Casos donde no se requieren búsquedas a BD 
            (lista vacía o lista solo con instancias ya resueltas).
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: Retorna temprano sin hacer llamadas a Puesto.objects.filter.
        """
        service = SolicitudInsigniaService()

        casos = [
            [],
            [{"puesto_solicitado": MagicMock(spec=Puesto)}]
        ]

        for preferencias in casos:
            with self.subTest(preferencias=preferencias):
                service._resolver_y_validar_existencia_puestos(preferencias)
                mock_filter.assert_not_called()



    # -------------------------------------------------------------------------
    # TEST VALIDAR PRIORIDADES CONSECUTIVAS
    # -------------------------------------------------------------------------

    def test_validar_prioridades_consecutivas_ordenadas_pasa(self):
        """
        Test: Secuencia válida básica

        Given: Una lista de prioridades ordenada [1, 2, 3].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: No se lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()
        prioridades = [1, 2, 3]

        service._validar_prioridades_consecutivas(prioridades)


    def test_validar_prioridades_desordenadas_pero_consecutivas_pasa(self):
        """
        Test: Secuencia válida desordenada

        Given: Una lista con las prioridades [3, 1, 2].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: No lanza excepción. 
            El sistema entiende que el conjunto de números es consecutivo.
        """
        service = SolicitudInsigniaService()
        prioridades = [3, 1, 2]

        service._validar_prioridades_consecutivas(prioridades)


    def test_validar_prioridades_con_strings_numericos_pasa_por_coercion(self):
        """
        Test: Strings numéricos

        Given: Una lista de prioridades como strings ["1", "2"].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: No lanza ValidationError.
            El servicio los convierte internamente a [1, 2] y valida con éxito.
        """
        service = SolicitudInsigniaService()
        prioridades = ["1", "2"]

        service._validar_prioridades_consecutivas(prioridades)


    def test_validar_prioridades_consecutivas_falla_con_valores_no_numericos(self):
        """
        Test: Fallo en conversión de tipos

        Given: Listas de prioridades que contienen strings no numéricos o tipos inválidos.
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Debe capturar el ValueError/TypeError y lanzar una ValidationError.
        """
        service = SolicitudInsigniaService()

        casos = [
            ([1, "dos", 3], "String no numérico"),
            ([1, None, 3], "Valor None")
        ]

        for prioridades, descripcion in casos:
            with self.subTest(caso=descripcion):
                with self.assertRaises(ValidationError) as cm:
                    service._validar_prioridades_consecutivas(prioridades)
                self.assertEqual(
                    str(cm.exception.message), 
                    "El orden de prioridad debe ser un número válido."
                )


    def test_validar_prioridades_duplicadas_falla(self):
        """
        Test: Duplicados

        Given: Una lista con un valor repetido [1, 1, 2].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Lanza ValidationError indicando que no puede haber duplicados.
        """
        service = SolicitudInsigniaService()
        prioridades = [1, 1, 2]

        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades)
        
        self.assertEqual(
            cm.exception.message, 
            "No puede haber orden de prioridad duplicado."
        )


    def test_validar_prioridades_menores_que_uno_falla(self):
        """
        Test: Valores menores que 1 (Cero y Negativos)

        Given: Listas que incluyen el cero o números negativos.
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Lanza ValidationError con el mensaje específico de mayor que cero.
        """
        service = SolicitudInsigniaService()
        
        casos = [
            ([0, 1, 2], "Incluye Cero"),
            ([1, -2, 3], "Incluye Negativo")
        ]

        for prioridades, descripcion in casos:
            with self.subTest(caso=descripcion):
                with self.assertRaises(ValidationError) as cm:
                    service._validar_prioridades_consecutivas(prioridades)
                
                self.assertEqual(
                    cm.exception.message, 
                    "El orden de prioridad debe ser mayor que cero."
                )


    def test_validar_prioridades_no_consecutivas_falla(self):
        """
        Test: No consecutivos (Saltos o no empezar en 1)

        Given: Listas con saltos en la numeración o que no empiezan por 1.
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Lanza ValidationError indicando que debe ser consecutivo empezando por 1.
        """
        service = SolicitudInsigniaService()
        
        casos = [
            ([1, 3, 4], "Salto en numeración"),
            ([2, 3, 4], "No empieza en 1")
        ]

        for prioridades, descripcion in casos:
            with self.subTest(caso=descripcion):
                with self.assertRaises(ValidationError) as cm:
                    service._validar_prioridades_consecutivas(prioridades)
                
                self.assertEqual(
                    cm.exception.message, 
                    "El orden de prioridad debe ser consecutivo empezando por 1."
                )



    # -------------------------------------------------------------------------
    # TEST VALIDAR PUESTO UNICOS
    # -------------------------------------------------------------------------

    def test_validar_puestos_unicos_sin_duplicados_pasa(self):
        """
        Test: Lista sin duplicados

        Given: Una lista de puestos únicos (completamente cumplimentada).
        When: Se llama a _validar_puestos_unicos.
        Then: No se lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()

        puestos = [MagicMock(id=i) for i in range(5)]

        service._validar_puestos_unicos(puestos)


    def test_validar_puestos_unicos_lista_vacia_pasa(self):
        """
        Test: Lista vacía

        Given: Una lista vacía [].
        When: Se llama a _validar_puestos_unicos.
        Then: No se lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()
        puestos = []

        service._validar_puestos_unicos(puestos)


    def test_validar_puestos_unicos_mezcla_valida_pasa(self):
        """
        Test: Puestos únicos mezclados con múltiples None

        Given: Una lista con puestos distintos y valores nulos intercalados.
        When: Se llama a _validar_puestos_unicos.
        Then: No lanza excepción. 
            El filtro interno debe ignorar los valores None, manteniendo
            solo los objetos reales y validando su unicidad.
        """
        service = SolicitudInsigniaService()
        
        p1 = MagicMock(spec=Puesto, id=10)
        p2 = MagicMock(spec=Puesto, id=20)
        puestos = [None, p1, None, p2, None]

        service._validar_puestos_unicos(puestos)


    def test_validar_puestos_unicos_duplicados_falla(self):
        """
        Test: Duplicados (con o sin Nulos)

        Given: Listas que contienen puestos duplicados (ya sea de forma consecutiva
            o separados por otros valores como None).
        When: Se llama a _validar_puestos_unicos.
        Then: Lanza ValidationError con el mensaje de duplicados.
        """
        service = SolicitudInsigniaService()
        
        p1 = MagicMock(spec=Puesto, id=10)
        p2 = MagicMock(spec=Puesto, id=20)

        casos_duplicados = [
            [p1, p1],
            [p1, p2, p1],
            [p1, None, p1],
            [p1, p1, p2, p2]
        ]

        for puestos in casos_duplicados:
            with self.subTest(puestos=puestos):
                with self.assertRaises(ValidationError) as cm:
                    service._validar_puestos_unicos(puestos)
                
                self.assertEqual(
                    cm.exception.message, 
                    "No puede solicitar el mismo puesto varias veces."
                )


    def test_validar_puestos_unicos_identidad_vs_igualdad_detecta_mismo_id_logico(self):
        """
        Test: Identidad en memoria vs Igualdad lógica

        Given: Dos objetos DISTINTOS en memoria pero que representan 
            el MISMO puesto en base de datos (tienen el mismo ID).
        When: Se llama a _validar_puestos_unicos.
        Then: Lanza ValidationError.
            El set() debe ser capaz de colapsarlos por su igualdad lógica
            (definida por Django a través del ID), no por su dirección de memoria.
        """
        service = SolicitudInsigniaService()

        p1_a = Puesto(id=50)
        p1_b = Puesto(id=50)

        self.assertIsNot(p1_a, p1_b)
        self.assertEqual(p1_a, p1_b)

        puestos = [p1_a, p1_b]

        with self.assertRaises(ValidationError) as cm:
            service._validar_puestos_unicos(puestos)
        
        self.assertEqual(
            cm.exception.message, 
            "No puede solicitar el mismo puesto varias veces."
        )



    # -------------------------------------------------------------------------
    # TEST CREAR PAPELETA BASE
    # -------------------------------------------------------------------------

    @patch('api.models.PapeletaSitio.objects.create')
    @patch('uuid.uuid4')
    def test_crear_papeleta_base_mapeo_correcto(self, mock_uuid, mock_create):
        """
        Test: Creación básica de papeleta

        Given: Un hermano, un acto con fecha en 2026 y una fecha de solicitud.
        When: Se llama a _crear_papeleta_base.
        Then: Se debe llamar a PapeletaSitio.objects.create con los valores 
            esperados, incluyendo el año extraído del acto y el UUID formateado.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(id=1)
        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026
        fecha_solicitud = "2026-03-15"

        fake_uuid = MagicMock()
        fake_uuid.hex = "abcdef1234567890"
        mock_uuid.return_value = fake_uuid

        service._crear_papeleta_base(
            hermano=mock_hermano, 
            acto=mock_acto, 
            fecha_solicitud=fecha_solicitud
        )

        mock_create.assert_called_once_with(
            hermano=mock_hermano,
            acto=mock_acto,
            anio=2026,
            fecha_solicitud=fecha_solicitud,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            vinculado_a=None,
            es_solicitud_insignia=False,
            codigo_verificacion="ABCDEF12"
        )


    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_con_vinculado_a_informado(self, mock_create):
        """
        Test: Con vinculado_a informado

        Given: Un hermano titular que actúa como vínculo (tutor).
        When: Se llama a _crear_papeleta_base pasando el tutor en 'vinculado_a'.
        Then: La llamada a create debe incluir dicho hermano en el campo correspondiente.
        """
        service = SolicitudInsigniaService()
        
        mock_hermano = MagicMock(id=1)
        mock_tutor = MagicMock(id=99)
        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026

        service._crear_papeleta_base(
            hermano=mock_hermano, 
            acto=mock_acto, 
            fecha_solicitud="2026-03-20", 
            vinculado_a=mock_tutor
        )

        args, kwargs = mock_create.call_args
        self.assertEqual(kwargs.get('vinculado_a'), mock_tutor)
        self.assertIsNotNone(kwargs.get('vinculado_a'))


    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_falla_en_create_propaga_error(self, mock_create):
        """
        Test: Falla en objects.create

        Given: El ORM lanza una excepción (ej: DatabaseError).
        When: Se llama a _crear_papeleta_base.
        Then: El servicio propaga la excepción, permitiendo que el flujo 
            superior la gestione o haga rollback de la transacción.
        """
        service = SolicitudInsigniaService()

        mock_create.side_effect = Exception("Error crítico de base de datos")

        with self.assertRaises(Exception) as cm:
            service._crear_papeleta_base(
                hermano=MagicMock(), 
                acto=MagicMock(), 
                fecha_solicitud="2026-01-01"
            )
        
        self.assertEqual(str(cm.exception), "Error crítico de base de datos")



    # -------------------------------------------------------------------------
    # TEST GUARDAR PREFERENCIAS
    # -------------------------------------------------------------------------

    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_insercion_correcta(self, mock_bulk_create):
        """
        Test: Inserción correcta de preferencias

        Given: Una instancia de PapeletaSitio y una lista de diccionarios con datos.
        When: Se llama al método _guardar_preferencias.
        Then: Se invoca bulk_create exactamente una vez con las instancias
            correctamente mapeadas manteniendo la relación con la papeleta.
        """
        service = SolicitudInsigniaService()

        papeleta_memoria = PapeletaSitio(id=100)
        p1 = Puesto(id=10)
        p2 = Puesto(id=20)
        
        preferencias_data = [
            {"puesto_solicitado": p1, "orden_prioridad": 1},
            {"puesto_solicitado": p2, "orden_prioridad": 2}
        ]

        service._guardar_preferencias(papeleta_memoria, preferencias_data)

        mock_bulk_create.assert_called_once()

        objetos_creados = mock_bulk_create.call_args[0][0]

        self.assertEqual(len(objetos_creados), 2)
        
        self.assertEqual(objetos_creados[0].papeleta, papeleta_memoria)
        self.assertEqual(objetos_creados[0].puesto_solicitado, p1)
        self.assertEqual(objetos_creados[0].orden_prioridad, 1)

        self.assertEqual(objetos_creados[1].papeleta, papeleta_memoria)
        self.assertEqual(objetos_creados[1].puesto_solicitado, p2)
        self.assertEqual(objetos_creados[1].orden_prioridad, 2)


    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_lista_vacia_pasa(self, mock_bulk_create):
        """
        Test: Lista vacía

        Given: Una lista de preferencias vacía [].
        When: Se llama a _guardar_preferencias.
        Then: Se llama a bulk_create con una lista vacía, delegando 
            en Django la optimización sin lanzar error.
        """
        service = SolicitudInsigniaService()
        mock_papeleta = MagicMock(id=100)
        
        service._guardar_preferencias(mock_papeleta, [])

        mock_bulk_create.assert_called_once_with([])


    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_datos_incompletos_falla(self, mock_bulk_create):
        """
        Test: Datos incompletos (Faltan claves requeridas)

        Given: Listas de preferencias donde faltan las claves 'puesto_solicitado' 
            u 'orden_prioridad'.
        When: Se llama a _guardar_preferencias.
        Then: Lanza KeyError antes de ejecutar la inserción en base de datos.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)

        casos = [
            ([{"orden_prioridad": 1}], "'puesto_solicitado'"),
            ([{"puesto_solicitado": Puesto(id=10)}], "'orden_prioridad'")
        ]

        for preferencias_data, clave_esperada in casos:
            with self.subTest(preferencias_data=preferencias_data):
                with self.assertRaises(KeyError) as cm:
                    service._guardar_preferencias(papeleta, preferencias_data)
                
                self.assertEqual(str(cm.exception), clave_esperada)

        mock_bulk_create.assert_not_called()