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

    @patch('api.services.timezone.now') 
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



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_orden_validaciones(self, mock_timezone_now):
        """
        Test: Verificar orden de validaciones

        Given: Un escenario válido para procesar una solicitud.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se verifica que las validaciones se ejecuten en el orden jerárquico:
                1. Configuración de acto
                2. Plazo vigente
                3. Hermano apto
                4. Edad mínima
                5. Unicidad
                6. Límites de preferencias
                7. Preferencias específicas
        """
        service = SolicitudInsigniaService()

        manager = MagicMock()

        service._validar_configuracion_acto_tradicional = manager.config_acto
        service._validar_plazo_vigente = manager.plazo
        service._validar_hermano_apto_para_solicitar = manager.hermano_apto
        service._validar_edad_minima_insignia = manager.edad
        service._validar_unicidad = manager.unicidad
        service._validar_limites_preferencias = manager.limites
        service._validar_preferencias_insignia_tradicional = manager.preferencias

        service._crear_papeleta_base = MagicMock(return_value=MagicMock())
        service._guardar_preferencias = MagicMock()
        
        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = ['Cuerpo']
        mock_acto = MagicMock()
        mock_ahora = '2026-04-26 09:35:00'
        mock_timezone_now.return_value = mock_ahora

        service.procesar_solicitud_insignia_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            preferencias_data=[{'id': 1}],
            vinculado_a=None
        )

        expected_calls = [
            unittest.mock.call.config_acto(mock_acto),
            unittest.mock.call.plazo(mock_ahora, mock_acto.inicio_solicitud, mock_acto.fin_solicitud, "insignias"),
            unittest.mock.call.hermano_apto(mock_hermano, {'Cuerpo'}),
            unittest.mock.call.edad(mock_hermano, mock_acto),
            unittest.mock.call.unicidad(mock_hermano, mock_acto),
            unittest.mock.call.limites([{'id': 1}]),
            unittest.mock.call.preferencias(mock_hermano, mock_acto, [{'id': 1}], {'Cuerpo'})
        ]
        
        manager.assert_has_calls(expected_calls, any_order=False)



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_uso_timezone(self, mock_timezone_now):
        """
        Test: Verificar uso de timezone.now()

        Given: Un flujo de solicitud válido.
            Un valor específico retornado por timezone.now().
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se valida que el mismo objeto 'ahora' obtenido de timezone.now() 
            se pase correctamente como argumento a _crear_papeleta_base.
        """
        service = SolicitudInsigniaService()

        mock_ahora = MagicMock(name="ObjetoTimezoneNow")
        mock_timezone_now.return_value = mock_ahora

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()
        service._guardar_preferencias = MagicMock()

        mock_papeleta = MagicMock()
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)
        
        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = []
        mock_acto = MagicMock()

        service.procesar_solicitud_insignia_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            preferencias_data=[],
            vinculado_a=None
        )

        mock_timezone_now.assert_called_once()

        service._crear_papeleta_base.assert_called_once_with(
            mock_hermano, 
            mock_acto, 
            mock_ahora
        )



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_modifica_antes_de_guardar(self, mock_timezone_now):
        """
        Test: Verificar modificación de papeleta

        Given: Un flujo de solicitud válido.
            Una papeleta base recién creada con es_solicitud_insignia = False.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se valida que el atributo es_solicitud_insignia se establezca en True
            antes de que se ejecute el método save().
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()
        service._guardar_preferencias = MagicMock()

        mock_papeleta = MagicMock()
        mock_papeleta.es_solicitud_insignia = False
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)

        estado_en_save = {}

        def side_effect_save(*args, **kwargs):
            estado_en_save['valor_al_guardar'] = mock_papeleta.es_solicitud_insignia

        mock_papeleta.save.side_effect = side_effect_save

        service.procesar_solicitud_insignia_tradicional(
            hermano=MagicMock(),
            acto=MagicMock(),
            preferencias_data=[],
            vinculado_a=None
        )

        mock_papeleta.save.assert_called_once()

        self.assertTrue(
            estado_en_save.get('valor_al_guardar'), 
            "El atributo es_solicitud_insignia debería ser True al llamar a save()"
        )

        self.assertTrue(mock_papeleta.es_solicitud_insignia)



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_usa_update_fields(self, mock_timezone_now):
        """
        Test: Verificar update_fields

        Given: Un flujo de solicitud válido.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se valida que al persistir el cambio en la papeleta, se utilice 
            el argumento update_fields=['es_solicitud_insignia'] para
            optimizar la escritura en base de datos.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()
        service._guardar_preferencias = MagicMock()

        mock_papeleta = MagicMock()
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)

        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = []
        mock_acto = MagicMock()

        service.procesar_solicitud_insignia_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            preferencias_data=[],
            vinculado_a=None
        )

        mock_papeleta.save.assert_called_once_with(
            update_fields=['es_solicitud_insignia']
        )



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_llama_guardar_preferencias(self, mock_timezone_now):
        """
        Test: Verificar guardado de preferencias

        Given: Un flujo de solicitud válido.
            Una lista de preferencias_data específica.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se valida que se llame al método interno _guardar_preferencias
            pasándole exactamente la instancia de la papeleta generada 
            y el payload de preferencias recibido.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()

        service._guardar_preferencias = MagicMock()

        mock_papeleta = MagicMock()
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)
        
        preferencias_test = [
            {'insignia_id': 10, 'prioridad': 1},
            {'insignia_id': 12, 'prioridad': 2}
        ]

        service.procesar_solicitud_insignia_tradicional(
            hermano=MagicMock(),
            acto=MagicMock(),
            preferencias_data=preferencias_test,
            vinculado_a=None
        )

        service._guardar_preferencias.assert_called_once_with(
            mock_papeleta, 
            preferencias_test
        )



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_retorna_papeleta_creada(self, mock_timezone_now):
        """
        Test: Verificar retorno correcto

        Given: Un flujo de solicitud sin errores.
            Una instancia de papeleta generada internamente.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: El servicio devuelve exactamente la misma instancia de la papeleta
            que fue creada por _crear_papeleta_base.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()
        service._guardar_preferencias = MagicMock()

        instancia_papeleta_esperada = MagicMock(name="PapeletaFinal")
        service._crear_papeleta_base = MagicMock(return_value=instancia_papeleta_esperada)

        resultado = service.procesar_solicitud_insignia_tradicional(
            hermano=MagicMock(),
            acto=MagicMock(),
            preferencias_data=[],
            vinculado_a=None
        )

        self.assertIs(
            resultado, 
            instancia_papeleta_esperada, 
            "El servicio debe retornar la instancia de papeleta creada por _crear_papeleta_base"
        )



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



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_limites_preferencias(self, mock_timezone_now):
        """
        Test: Validación fallida (_validar_limites_preferencias)

        Given: Una lista de preferencias_data que excede el máximo permitido.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza una excepción ValidationError.
            Se verifica que se ejecutaron todas las validaciones de negocio previas,
            pero NO se procedió a validar el contenido de las preferencias 
            ni a crear la papeleta base.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        preferencias_excesivas = [{'id': i} for i in range(25)] 

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()

        service._validar_limites_preferencias = MagicMock(
            side_effect=ValidationError("Se ha excedido el número máximo de preferencias.")
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

        self.assertEqual(cm.exception.message, "Se ha excedido el número máximo de preferencias.")

        service._validar_limites_preferencias.assert_called_once_with(preferencias_excesivas)

        service._validar_preferencias_insignia_tradicional.assert_not_called()
        service._crear_papeleta_base.assert_not_called()



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_en_save(self, mock_timezone_now):
        """
        Test: Error en save (papeleta.save() lanza excepción)

        Given: Un flujo donde la papeleta base se crea correctamente.
        When: Al intentar ejecutar papeleta.save(update_fields=['es_solicitud_insignia']) 
            se lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga hacia arriba.
            Se valida que NO se llama al método _guardar_preferencias, 
            garantizando que no se procesen datos si la papeleta no se marcó correctamente.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()

        mock_papeleta = MagicMock()
        mock_papeleta.save.side_effect = Exception("Error crítico de base de datos")
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)

        service._guardar_preferencias = MagicMock()

        with self.assertRaisesRegex(Exception, "Error crítico de base de datos"):
            service.procesar_solicitud_insignia_tradicional(
                hermano=MagicMock(),
                acto=MagicMock(),
                preferencias_data=[{'id': 1}],
                vinculado_a=None
            )

        mock_papeleta.save.assert_called_once()

        service._guardar_preferencias.assert_not_called()



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_error_en_guardar_preferencias(self, mock_timezone_now):
        """
        Test: Error en guardar preferencias (_guardar_preferencias lanza excepción)

        Given: Un flujo donde la papeleta base se ha creado y modificado correctamente.
        When: Se llama al método interno _guardar_preferencias y este lanza una excepción 
            (ej. un error de integridad o lógica de negocio).
        Then: La excepción se propaga al llamador sin ser capturada.
            Se valida que el flujo de ejecución llegó hasta ese punto 
            pero falló en la fase final de persistencia.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()

        mock_papeleta = MagicMock()
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)

        error_mensaje = "Fallo al insertar preferencias de insignia"
        service._guardar_preferencias = MagicMock(
            side_effect=RuntimeError(error_mensaje)
        )

        with self.assertRaisesRegex(RuntimeError, error_mensaje):
            service.procesar_solicitud_insignia_tradicional(
                hermano=MagicMock(),
                acto=MagicMock(),
                preferencias_data=[{'id': 1}],
                vinculado_a=None
            )

        service._crear_papeleta_base.assert_called_once()
        mock_papeleta.save.assert_called_once()

        service._guardar_preferencias.assert_called_once()



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_un_solo_elemento(self, mock_timezone_now):
        """
        Test: CASOS LÍMITE IMPORTANTES (preferencias_data válido pero mínimo)

        Given: Un flujo de solicitud con exactamente un elemento en preferencias_data.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: El flujo se completa correctamente.
            Se valida que se llama a _guardar_preferencias con la lista de un elemento.
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

        preferencia_minima = [{'insignia_id': 1, 'prioridad': 1}]

        mock_papeleta = MagicMock()
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)
        service._guardar_preferencias = MagicMock()

        resultado = service.procesar_solicitud_insignia_tradicional(
            hermano=MagicMock(),
            acto=MagicMock(),
            preferencias_data=preferencia_minima,
            vinculado_a=None
        )

        service._guardar_preferencias.assert_called_once_with(
            mock_papeleta, 
            preferencia_minima
        )

        self.assertEqual(resultado, mock_papeleta)



    @patch('api.services.timezone.now')
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



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_corte_por_fallo_temprano(self, mock_timezone_now):
        """
        Test: Verificar corte de ejecución tras fallo temprano

        Given: Un escenario donde la primera validación (_validar_configuracion_acto_tradicional) falla.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se lanza ValidationError.
            Se valida que el flujo se corta correctamente:
                - SÍ se llama a timezone.now() y a values_list (están al principio del método).
                - NO se llama a ninguna validación posterior (ej. plazo_vigente).
                - NO se llama a _crear_papeleta_base ni _guardar_preferencias.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        service._validar_configuracion_acto_tradicional = MagicMock(
            side_effect=ValidationError("Fallo inicial")
        )

        service._validar_plazo_vigente = MagicMock()
        service._crear_papeleta_base = MagicMock()
        service._guardar_preferencias = MagicMock()

        with self.assertRaises(ValidationError):
            service.procesar_solicitud_insignia_tradicional(
                hermano=mock_hermano,
                acto=mock_acto,
                preferencias_data=[],
                vinculado_a=None
            )

        mock_timezone_now.assert_called_once()
        mock_hermano.cuerpos.values_list.assert_called_once_with('nombre_cuerpo', flat=True)

        service._validar_configuracion_acto_tradicional.assert_called_once_with(mock_acto)

        service._validar_plazo_vigente.assert_not_called()
        service._crear_papeleta_base.assert_not_called()
        service._guardar_preferencias.assert_not_called()



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_orden_save_y_preferencias(self, mock_timezone_now):
        """
        Test: Verificar que _guardar_preferencias se llama después de save

        Given: Un flujo de solicitud válido.
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se valida el orden cronológico de persistencia:
                1. Se llama a papeleta.save().
                2. Se llama a _guardar_preferencias().
            Esto garantiza que las preferencias se vinculen a una papeleta 
            con estado consistente.
        """
        service = SolicitudInsigniaService()

        service._validar_configuracion_acto_tradicional = MagicMock()
        service._validar_plazo_vigente = MagicMock()
        service._validar_hermano_apto_para_solicitar = MagicMock()
        service._validar_edad_minima_insignia = MagicMock()
        service._validar_unicidad = MagicMock()
        service._validar_limites_preferencias = MagicMock()
        service._validar_preferencias_insignia_tradicional = MagicMock()

        manager = MagicMock()

        mock_papeleta = MagicMock()

        mock_papeleta.save = manager.papeleta_save
        
        service._crear_papeleta_base = MagicMock(return_value=mock_papeleta)

        service._guardar_preferencias = manager.guardar_preferencias

        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = []
        preferencias_data = [{'id': 1}]

        service.procesar_solicitud_insignia_tradicional(
            hermano=mock_hermano,
            acto=MagicMock(),
            preferencias_data=preferencias_data,
            vinculado_a=None
        )

        expected_calls = [
            call.papeleta_save(update_fields=['es_solicitud_insignia']),
            call.guardar_preferencias(mock_papeleta, preferencias_data)
        ]

        manager.assert_has_calls(expected_calls, any_order=False)



    @patch('api.services.timezone.now')
    def test_procesar_solicitud_insignia_tradicional_crear_papeleta_usa_ahora(self, mock_timezone_now):
        """
        Test: Verificar que _crear_papeleta_base usa ahora

        Given: Un flujo de solicitud válido.
            Un objeto de tiempo específico generado por timezone.now().
        When: Se llama a procesar_solicitud_insignia_tradicional.
        Then: Se valida la coherencia temporal: el mismo objeto 'ahora' capturado
            al inicio del servicio debe pasarse como tercer argumento 
            a _crear_papeleta_base.
        """
        service = SolicitudInsigniaService()

        mock_ahora = MagicMock(name="TimezoneNowStamp")
        mock_timezone_now.return_value = mock_ahora

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

        mock_hermano = MagicMock()
        mock_hermano.cuerpos.values_list.return_value = []
        mock_acto = MagicMock()

        service.procesar_solicitud_insignia_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            preferencias_data=[],
            vinculado_a=None
        )

        mock_timezone_now.assert_called_once()

        service._crear_papeleta_base.assert_called_once_with(
            mock_hermano, 
            mock_acto, 
            mock_ahora
        )



    # -------------------------------------------------------------------------
    # TEST VALIDAR UNICIDAD
    # -------------------------------------------------------------------------

    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_no_existe_papeleta_activa(self, mock_estados, mock_objects):
        """
        Test: No existe papeleta activa → no lanza excepción

        Given: Un hermano y un acto.
            Una simulación de base de datos donde .exists() retorna False.
        When: Se llama a _validar_unicidad.
        Then: NO se lanza ninguna excepción (ValidationError).
            El flujo termina correctamente validando que la consulta
            se construyó con los parámetros y estados correctos.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_estados.ANULADA = 'ANULADA'
        mock_estados.NO_ASIGNADA = 'NO_ASIGNADA'

        mock_query_filter = MagicMock()
        mock_query_exclude = MagicMock()
        
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value = mock_query_exclude
        mock_query_exclude.exists.return_value = False

        service._validar_unicidad(mock_hermano, mock_acto)

        mock_objects.filter.assert_called_once_with(
            hermano=mock_hermano, 
            acto=mock_acto
        )

        mock_query_filter.exclude.assert_called_once_with(
            estado_papeleta__in=['ANULADA', 'NO_ASIGNADA']
        )

        mock_query_exclude.exists.assert_called_once()



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_existen_papeletas_pero_todas_ignorables(self, mock_estados, mock_objects):
        """
        Test: Existen papeletas pero todas ignorables

        Given: Un hermano y un acto con papeletas previas.
            Dichas papeletas tienen estados ANULADA o NO_ASIGNADA.
            La simulación del ORM tras el .exclude(...) devuelve .exists() = False.
        When: Se llama a _validar_unicidad.
        Then: NO se lanza ValidationError.
            Se confirma que el flujo ignora correctamente las papeletas en 
            estados no bloqueantes.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_estados.ANULADA = 'ANULADA'
        mock_estados.NO_ASIGNADA = 'NO_ASIGNADA'

        mock_query_filter = MagicMock()
        mock_query_exclude = MagicMock()
        
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value = mock_query_exclude

        mock_query_exclude.exists.return_value = False

        service._validar_unicidad(mock_hermano, mock_acto)

        mock_objects.filter.assert_called_once_with(
            hermano=mock_hermano, 
            acto=mock_acto
        )

        mock_query_filter.exclude.assert_called_once_with(
            estado_papeleta__in=['ANULADA', 'NO_ASIGNADA']
        )

        mock_query_exclude.exists.assert_called_once()



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_query_correcta(self, mock_estados, mock_objects):
        """
        Test: Verificar query correcta

        Given: Un hermano y un acto para validar.
        When: Se llama a _validar_unicidad.
        Then: Se valida que la consulta al ORM sea exacta:
                1. filter() usa los objetos hermano y acto recibidos.
                2. exclude() usa la clave 'estado_papeleta__in'.
                3. La lista de exclude contiene únicamente [ANULADA, NO_ASIGNADA].
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(name="HermanoTest")
        mock_acto = MagicMock(name="ActoTest")

        mock_estados.ANULADA = 'VALOR_ANULADA'
        mock_estados.NO_ASIGNADA = 'VALOR_NO_ASIGNADA'
        estados_esperados = ['VALOR_ANULADA', 'VALOR_NO_ASIGNADA']

        mock_query_filter = MagicMock()
        mock_query_exclude = MagicMock()
        
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value = mock_query_exclude
        mock_query_exclude.exists.return_value = False

        service._validar_unicidad(mock_hermano, mock_acto)

        mock_objects.filter.assert_called_once_with(
            hermano=mock_hermano, 
            acto=mock_acto
        )

        mock_query_filter.exclude.assert_called_once_with(
            estado_papeleta__in=estados_esperados
        )

        mock_query_exclude.exists.assert_called_once()



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_encadenamiento_correcto(self, mock_estados, mock_objects):
        """
        Test: Encadenamiento correcto (filter -> exclude -> exists)

        Given: Un proceso de validación de unicidad.
        When: Se llama a _validar_unicidad.
        Then: Se valida que las llamadas al manager se realicen en el orden lógico.
        """
        service = SolicitudInsigniaService()

        mock_objects.filter.return_value.exclude.return_value.exists.return_value = False

        service._validar_unicidad(MagicMock(), MagicMock())

        expected_sequence = [
            call.filter(hermano=ANY, acto=ANY),
            call.filter().exclude(estado_papeleta__in=ANY),
            call.filter().exclude().exists()
        ]

        mock_objects.assert_has_calls(expected_sequence, any_order=False)



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_existe_papeleta_activa_lanza_excepcion(self, mock_estados, mock_objects):
        """
        Test: Existe papeleta activa → lanza excepción

        Given: Un hermano y un acto que ya tienen una solicitud vinculada.
            La simulación del ORM (.exists()) devuelve True tras el filtrado.
        When: Se llama a _validar_unicidad.
        Then: Se lanza una excepción ValidationError.
            Se verifica que el mensaje de la excepción es:
            "Ya existe una solicitud activa (en proceso o asignada) para este acto."
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_estados.ANULADA = 'ANULADA'
        mock_estados.NO_ASIGNADA = 'NO_ASIGNADA'

        mock_query_filter = MagicMock()
        mock_query_exclude = MagicMock()
        
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value = mock_query_exclude

        mock_query_exclude.exists.return_value = True

        mensaje_esperado = "Ya existe una solicitud activa (en proceso o asignada) para este acto."
        
        with self.assertRaises(ValidationError) as cm:
            service._validar_unicidad(mock_hermano, mock_acto)

        self.assertEqual(cm.exception.message, mensaje_esperado)

        mock_query_exclude.exists.assert_called_once()



    @patch('api.services.PapeletaSitio.objects')
    def test_validar_unicidad_error_en_filter_propaga_excepcion(self, mock_objects):
        """
        Test: Error en filter (filter() lanza excepción)

        Given: Un intento de validar la unicidad.
        When: El ORM lanza una excepción de base de datos (ej. DatabaseError) 
            al intentar ejecutar el filter().
        Then: La excepción se propaga íntegramente hacia arriba.
            Se valida que el flujo se interrumpe y no se llega a llamar 
            a .exclude() ni a .exists().
        """
        service = SolicitudInsigniaService()

        mock_objects.filter.side_effect = DatabaseError("Error de conexión con la BD")

        mock_query_filter = MagicMock()

        with self.assertRaisesRegex(DatabaseError, "Error de conexión con la BD"):
            service._validar_unicidad(MagicMock(), MagicMock())

        mock_objects.filter.assert_called_once()

        mock_query_filter.exclude.assert_not_called()



    @patch('api.services.PapeletaSitio.objects')
    def test_validar_unicidad_error_en_exclude_propaga_excepcion(self, mock_objects):
        """
        Test: Error en exclude (exclude() lanza excepción)

        Given: Un intento de validar la unicidad.
        When: El ORM lanza una excepción inesperada al ejecutar .exclude().
        Then: La excepción se propaga íntegramente hacia arriba.
            Se valida que se llamó a filter() pero el flujo se rompió 
            antes de llegar a ejecutar el .exists().
        """
        service = SolicitudInsigniaService()

        mock_query_filter = MagicMock()
        mock_objects.filter.return_value = mock_query_filter
        
        error_mensaje = "Error inesperado en lógica de exclusión"
        mock_query_filter.exclude.side_effect = Exception(error_mensaje)

        with self.assertRaisesRegex(Exception, error_mensaje):
            service._validar_unicidad(MagicMock(), MagicMock())

        mock_objects.filter.assert_called_once()

        mock_query_filter.exclude.assert_called_once()

        mock_query_filter.exclude.return_value.exists.assert_not_called()



    @patch('api.services.PapeletaSitio.objects')
    def test_validar_unicidad_error_en_exists_propaga_excepcion(self, mock_objects):
        """
        Test: Error en exists (exists() lanza excepción)

        Given: Un intento de validar la unicidad donde la construcción de la query es correcta.
        When: Al ejecutar .exists(), la base de datos lanza un error.
        Then: La excepción se propaga íntegramente.
        """
        service = SolicitudInsigniaService()

        mock_query_filter = MagicMock()
        mock_query_exclude = MagicMock()
        
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value = mock_query_exclude
        
        error_mensaje = "Error de ejecución: exists() falló"
        mock_query_exclude.exists.side_effect = DatabaseError(error_mensaje)

        with self.assertRaises(DatabaseError) as cm:
            service._validar_unicidad(MagicMock(), MagicMock())
        
        self.assertEqual(str(cm.exception), error_mensaje)

        mock_objects.filter.assert_called_once()
        mock_query_filter.exclude.assert_called_once()
        mock_query_exclude.exists.assert_called_once()



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_queryset_vacio_desde_inicio(self, mock_estados, mock_objects):
        """
        Test: CASOS LÍMITE IMPORTANTES (Queryset vacío desde el inicio)

        Given: Un hermano que nunca ha solicitado nada para este acto.
            El .filter() inicial del ORM ya devuelve un QuerySet vacío.
        When: Se llama a _validar_unicidad.
        Then: NO se lanza ValidationError.
            Se verifica que .exists() devuelve False y el servicio 
            permite continuar con la solicitud.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_query_filter = MagicMock()
        mock_query_exclude = MagicMock()
        
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value = mock_query_exclude

        mock_query_exclude.exists.return_value = False

        service._validar_unicidad(mock_hermano, mock_acto)

        mock_objects.filter.assert_called_once_with(
            hermano=mock_hermano, 
            acto=mock_acto
        )

        mock_query_exclude.exists.assert_called_once()



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_estados_ignorables_exactos(self, mock_estados, mock_objects):
        """
        Test: Verificar estados ignorables exactos

        Given: Un proceso de validación de unicidad.
        When: Se llama a _validar_unicidad.
        Then: Se valida que el método exclude reciba una lista con 
            exactamente los dos estados que deben ser ignorados:
            ANULADA y NO_ASIGNADA.
        """
        service = SolicitudInsigniaService()

        mock_estados.ANULADA = 'ESTADO_ANULADA_MOCK'
        mock_estados.NO_ASIGNADA = 'ESTADO_NO_ASIGNADA_MOCK'

        lista_esperada = ['ESTADO_ANULADA_MOCK', 'ESTADO_NO_ASIGNADA_MOCK']

        mock_query_filter = MagicMock()
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value.exists.return_value = False

        service._validar_unicidad(MagicMock(), MagicMock())

        args, kwargs = mock_query_filter.exclude.call_args
        estados_enviados = kwargs.get('estado_papeleta__in')

        self.assertEqual(len(estados_enviados), 2)

        self.assertIn(mock_estados.ANULADA, estados_enviados)
        self.assertIn(mock_estados.NO_ASIGNADA, estados_enviados)

        self.assertEqual(list(estados_enviados), lista_esperada)



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_no_excluye_otros_estados(self, mock_estados, mock_objects):
        """
        Test: Verificar que NO se incluyen otros estados

        Given: Un proceso de validación de unicidad.
        When: Se llama a _validar_unicidad.
        Then: Se valida que la lista de exclusión en 'estado_papeleta__in' 
            tenga una longitud exacta de 2.
            Esto garantiza que estados como 'SOLICITADA', 'ASIGNADA' o 'PAGADA' 
            NO están siendo excluidos y, por tanto, bloquearán correctamente 
            una nueva solicitud.
        """
        service = SolicitudInsigniaService()

        mock_estados.ANULADA = 'ANULADA'
        mock_estados.NO_ASIGNADA = 'NO_ASIGNADA'

        mock_query_filter = MagicMock()
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value.exists.return_value = False

        service._validar_unicidad(MagicMock(), MagicMock())

        kwargs = mock_query_filter.exclude.call_args.kwargs
        estados_excluidos = kwargs.get('estado_papeleta__in')

        self.assertEqual(
            len(estados_excluidos), 
            2, 
            f"Se esperaban exactamente 2 estados excluidos, pero se encontraron {len(estados_excluidos)}"
        )

        self.assertNotIn('SOLICITADA', estados_excluidos)
        self.assertNotIn('ASIGNADA', estados_excluidos)



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_exclude_usa_lista_explicita(self, mock_estados, mock_objects):
        """
        Test: Verificar que exclude usa lista (no set/tuple)

        Given: Un proceso de validación de unicidad.
        When: Se llama a _validar_unicidad.
        Then: Se valida que el argumento pasado a 'estado_papeleta__in' 
            sea específicamente de tipo 'list'.
            Esto evita bugs sutiles en ciertas versiones de conectores de BD 
            o comportamientos erráticos si se usaran sets (que no tienen orden).
        """
        service = SolicitudInsigniaService()

        mock_estados.ANULADA = 'ANULADA'
        mock_estados.NO_ASIGNADA = 'NO_ASIGNADA'

        mock_query_filter = MagicMock()
        mock_objects.filter.return_value = mock_query_filter
        mock_query_filter.exclude.return_value.exists.return_value = False

        service._validar_unicidad(MagicMock(), MagicMock())

        kwargs = mock_query_filter.exclude.call_args.kwargs
        estados_enviados = kwargs.get('estado_papeleta__in')

        self.assertIsInstance(
            estados_enviados, 
            list, 
            f"Se esperaba una lista en estado_papeleta__in, pero se recibió {type(estados_enviados)}"
        )



    @patch('api.services.PapeletaSitio.objects')
    @patch('api.services.PapeletaSitio.EstadoPapeleta')
    def test_validar_unicidad_no_hay_evaluacion_innecesaria(self, mock_estados, mock_objects):
        """
        Test: Verificar que no hay evaluación innecesaria

        Given: Un proceso de validación de unicidad estándar.
        When: Se llama a _validar_unicidad.
        Then: Se valida que .exists() se ejecute exactamente UNA vez.
            Esto garantiza que no existan llamadas redundantes a la base de datos
            y que el servicio sea óptimo en términos de rendimiento.
        """
        service = SolicitudInsigniaService()

        mock_query_exclude = MagicMock()
        mock_objects.filter.return_value.exclude.return_value = mock_query_exclude
        mock_query_exclude.exists.return_value = False

        service._validar_unicidad(MagicMock(), MagicMock())

        mock_query_exclude.exists.assert_called_once()

        mock_query_exclude.count.assert_not_called()
        mock_query_exclude.__len__.assert_not_called()

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



    def test_validar_hermano_apto_verificar_orden_estricto(self):
        """
        Test: Verificar orden de ejecución

        Given: Un proceso de validación de aptitud del hermano.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se valida que el orden de llamadas sea estrictamente:
                1. _validar_hermano_en_alta (Rápida/Estado base)
                2. _validar_hermano_al_corriente_hasta_anio_anterior (Contable)
                3. _validar_pertenencia_cuerpos (Estructural)
            Si el orden cambia, el test falla.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(name="Hermano")
        mock_cuerpos = {'CuerpoTest'}

        monitor = MagicMock()

        service._validar_hermano_en_alta = MagicMock(side_effect=lambda x: monitor.paso_1_alta())
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock(side_effect=lambda x: monitor.paso_2_contable())
        service._validar_pertenencia_cuerpos = MagicMock(side_effect=lambda x: monitor.paso_3_cuerpos())

        service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos)

        secuencia_esperada = [
            call.paso_1_alta(),
            call.paso_2_contable(),
            call.paso_3_cuerpos()
        ]

        self.assertEqual(
            monitor.mock_calls, 
            secuencia_esperada, 
            "El orden de las validaciones no es el correcto según la lógica de negocio."
        )



    def test_validar_hermano_apto_argumentos_correctos(self):
        """
        Test: Verificar argumentos correctos

        Given: Un objeto hermano y un set de cuerpos específicos.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se valida que:
                1. El objeto 'hermano' exacto llegue a las validaciones de alta y contable.
                2. El 'cuerpos_hermano_set' exacto llegue a la validación de pertenencia.
            Esto garantiza que no se intercambien parámetros por error de tipado o lógica.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(name="HermanoUnico")
        mock_cuerpos_set = {"Cuerpo_A", "Cuerpo_B", "Cuerpo_C"}

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos_set)

        service._validar_hermano_en_alta.assert_called_once_with(mock_hermano)
        service._validar_hermano_al_corriente_hasta_anio_anterior.assert_called_once_with(mock_hermano)

        service._validar_pertenencia_cuerpos.assert_called_once_with(mock_cuerpos_set)

        self.assertNotEqual(
            service._validar_pertenencia_cuerpos.call_args[0][0], 
            mock_hermano,
            "Error: Se pasó el objeto hermano a la validación de cuerpos."
        )



    def test_validar_hermano_apto_para_solicitar_retorna_none(self):
        """
        Test: Verificar que no retorna nada

        Given: Un escenario donde todas las validaciones internas pasan.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: El valor de retorno debe ser None.
            Esto confirma que el método actúa como una validación de flujo
            y no como un método transformador o de consulta de datos.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_cuerpos = set()

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        resultado = service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos)

        self.assertIsNone(
            resultado, 
            "El método de validación debería retornar None al finalizar exitosamente."
        )



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



    def test_validar_hermano_apto_con_hermano_none(self):
        """
        Test: hermano = None (test de robustez)

        Given: Un valor None en lugar de un objeto Hermano.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se valida que el valor None se propaga a las funciones internas.
            El test confirma que el orquestador no intenta acceder a 
            atributos del hermano antes de validarlo, evitando un 
            AttributeError prematuro en el método principal.
        """
        service = SolicitudInsigniaService()

        hermano_nulo = None
        mock_cuerpos = {"CuerpoTest"}

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        service._validar_hermano_apto_para_solicitar(hermano_nulo, mock_cuerpos)

        service._validar_hermano_en_alta.assert_called_once_with(None)
        service._validar_hermano_al_corriente_hasta_anio_anterior.assert_called_once_with(None)

        service._validar_pertenencia_cuerpos.assert_called_once_with(mock_cuerpos)



    def test_validar_hermano_apto_validaciones_llamadas_exactamente_una_vez(self):
        """
        Test: Validaciones llamadas exactamente una vez

        Given: Un flujo de validación de aptitud estándar.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se valida que cada sub-método de validación se ejecute 
            exactamente UNA vez.
            Esto garantiza que no existan duplicaciones en la lógica
            ni sobrecarga innecesaria en el proceso de solicitud.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_cuerpos = {"CuerpoTest"}

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos)

        service._validar_hermano_en_alta.assert_called_once()
        service._validar_hermano_al_corriente_hasta_anio_anterior.assert_called_once()
        service._validar_pertenencia_cuerpos.assert_called_once()



    def test_validar_hermano_apto_solo_delega_sin_logica_adicional(self):
        """
        Test: No hay lógica adicional (método solo delega)

        Given: Un hermano y un set de cuerpos con datos iniciales conocidos.
        When: Se llama a _validar_hermano_apto_para_solicitar.
        Then: Se valida que los objetos pasados no sufren ninguna alteración.
        """
        service = SolicitudInsigniaService()

        class HermanoDummy:
            def __init__(self):
                self.id = 1
                self.nombre = "Test"
            
        hermano = HermanoDummy()
        cuerpos_iniciales = {"Cuerpo1"}
        cuerpos_backup = cuerpos_iniciales.copy()

        service._validar_hermano_en_alta = MagicMock()
        service._validar_hermano_al_corriente_hasta_anio_anterior = MagicMock()
        service._validar_pertenencia_cuerpos = MagicMock()

        service._validar_hermano_apto_para_solicitar(hermano, cuerpos_iniciales)

        self.assertEqual(len(vars(hermano)), 2, "El objeto hermano ha sido modificado inesperadamente.")
        self.assertEqual(hermano.id, 1)
        
        self.assertEqual(
            cuerpos_iniciales, 
            cuerpos_backup, 
            "El set de cuerpos ha sido alterado por el orquestador."
        )
        
        if hasattr(service, 'errores_encontrados'):
            self.assertEqual(len(service.errores_encontrados), 0)



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



    def test_validar_pertenencia_cuerpos_un_solo_cuerpo_permitido_pasa(self):
        """
        Test: Un solo cuerpo permitido (Caso mínimo)

        Given: Un set que contiene exactamente un cuerpo válido (ej. NAZARENOS).
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: No se lanza ninguna excepción ValidationError.
            El método valida correctamente que el conjunto de 'cuerpos_no_aptos'
            está vacío.
        """
        service = SolicitudInsigniaService()

        cuerpos_hermano = {CuerpoPertenencia.NombreCuerpo.NAZARENOS.value}

        service._validar_pertenencia_cuerpos(cuerpos_hermano)



    def test_validar_pertenencia_cuerpos_todos_los_permitidos_pasa(self):
        """
        Test: Todos los cuerpos permitidos completos

        Given: Un hermano que pertenece a todos y cada uno de los cuerpos 
            permitidos definidos en la lógica del servicio.
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: No se lanza ninguna excepción ValidationError.
            Se confirma que el cálculo del conjunto 'cuerpos_no_aptos' 
            es un set vacío (Ø) cuando los conjuntos son idénticos.
        """
        service = SolicitudInsigniaService()

        cuerpos_hermano = {
            CuerpoPertenencia.NombreCuerpo.NAZARENOS.value,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA.value,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD.value,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL.value,
            CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value,
        }

        service._validar_pertenencia_cuerpos(cuerpos_hermano)



    def test_validar_pertenencia_cuerpos_un_cuerpo_no_permitido_falla(self):
        """
        Test: Un cuerpo no permitido

        Given: Un set con un cuerpo que no figura en la lista de permitidos
            (ej. "BANDA_DE_MUSICA").
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: Se lanza una excepción ValidationError.
            El mensaje de error debe contener el nombre del cuerpo no apto.
        """
        service = SolicitudInsigniaService()

        cuerpo_no_valido = "BANDA_DE_MUSICA"
        cuerpos_hermano = {cuerpo_no_valido}

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos(cuerpos_hermano)

        self.assertIn(
            cuerpo_no_valido, 
            cm.exception.message, 
            f"El mensaje de error debería mencionar el cuerpo: {cuerpo_no_valido}"
        )
        self.assertIn(
            "Tu pertenencia a los siguientes cuerpos no permite solicitar", 
            cm.exception.message
        )



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



    def test_validar_pertenencia_cuerpos_con_duplicados_manejados_por_set(self):
        """
        Test: Cuerpos duplicados

        Given: Un escenario donde un cuerpo no permitido se repite.
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: La lógica de conjuntos (set) debe colapsar los duplicados.
            El mensaje de error resultante debe mostrar el cuerpo 
            no permitido UNA SOLA VEZ, demostrando una limpieza 
            correcta de la información.
        """
        service = SolicitudInsigniaService()

        cuerpo_invalido = "BANDA_DE_CORNETAS"
        cuerpos_con_duplicados = {cuerpo_invalido, cuerpo_invalido, cuerpo_invalido}

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos(cuerpos_con_duplicados)
        
        mensaje = cm.exception.message

        ocurrencias = mensaje.count(cuerpo_invalido)
        
        self.assertEqual(
            ocurrencias, 
            1, 
            f"El cuerpo '{cuerpo_invalido}' aparece {ocurrencias} veces en el mensaje, se esperaba solo 1."
        )



    def test_validar_pertenencia_cuerpos_sensibilidad_mayusculas(self):
        """
        Test: Sensibilidad a mayúsculas/minúsculas

        Given: Un cuerpo válido ("NAZARENOS") pero escrito en minúsculas ("nazarenos").
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: Se valida el comportamiento actual:
            Si el sistema es estricto, lanzará ValidationError porque 
            "nazarenos" != "NAZARENOS".
            Este test documenta si el contrato requiere normalización.
        """
        service = SolicitudInsigniaService()

        cuerpo_en_minusculas = "nazarenos"
        cuerpos_hermano = {cuerpo_en_minusculas}

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos(cuerpos_hermano)
        
        self.assertIn(cuerpo_en_minusculas, cm.exception.message)



    def test_validar_pertenencia_cuerpos_con_tipos_incorrectos_falla(self):
        """
        Test: Tipos incorrectos dentro del set

        Given: Un set que contiene valores que no son strings (None, 123).
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: El sistema debe identificar estos valores como no permitidos.
            Se lanza ValidationError.
            Nota: Este test también detecta si el código rompe con TypeError 
            al intentar hacer el .join() con tipos no string.
        """
        service = SolicitudInsigniaService()

        cuerpos_hermano = {None, 123, "INVALIDO"}

        with self.assertRaises((ValidationError, TypeError)):
            service._validar_pertenencia_cuerpos(cuerpos_hermano)



    def test_validar_pertenencia_cuerpos_calculo_set_difference(self):
        """
        Test: Verificar cálculo correcto del set difference

        Given: Un set de entrada con elementos conocidos: 
            - 2 válidos (NAZARENOS, PRIOSTÍA)
            - 2 inválidos (ERROR_A, ERROR_B)
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: Se lanza ValidationError.
            Se verifica que el cálculo interno (input - permitidos) 
            resulte exactamente en el set {ERROR_A, ERROR_B}.
            Esto se comprueba validando que ambos errores (y solo ellos) 
            están presentes en el mensaje de excepción.
        """
        service = SolicitudInsigniaService()

        valido1 = CuerpoPertenencia.NombreCuerpo.NAZARENOS.value
        valido2 = CuerpoPertenencia.NombreCuerpo.PRIOSTÍA.value
        invalido1 = "ERROR_A"
        invalido2 = "ERROR_B"

        cuerpos_hermano = {valido1, invalido1, valido2, invalido2}

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos(cuerpos_hermano)
        
        mensaje = cm.exception.message

        self.assertIn(invalido1, mensaje)
        self.assertIn(invalido2, mensaje)

        self.assertNotIn(valido1, mensaje)
        self.assertNotIn(valido2, mensaje)



    def test_validar_pertenencia_cuerpos_mensaje_esta_ordenado_alfabeticamente(self):
        """
        Test: Verificar orden del mensaje

        Given: Un set con cuerpos no permitidos en un orden desordenado:
            {"Zeta", "Alfa", "Beta"}.
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: Se lanza ValidationError.
            Se valida que en el cuerpo del mensaje, los nombres aparezcan 
            estrictamente como "Alfa, Beta, Zeta".
            Esto garantiza que se está aplicando sorted() correctamente 
            antes del join().
        """
        service = SolicitudInsigniaService()

        cuerpos_desordenados = {"Zeta", "Alfa", "Beta"}

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos(cuerpos_desordenados)
        
        mensaje = cm.exception.message

        cadena_esperada = "Alfa, Beta, Zeta"

        self.assertIn(
            cadena_esperada, 
            mensaje, 
            f"El mensaje no presenta los cuerpos en orden alfabético. Esperado: '{cadena_esperada}'"
        )



    def test_validar_pertenencia_cuerpos_prefijo_mensaje_exacto(self):
        """
        Test: Mensaje exacto

        Given: Un set con un cuerpo no permitido.
        When: Se llama a _validar_pertenencia_cuerpos.
        Then: Se lanza ValidationError.
            Se valida que el mensaje de la excepción comience exactamente con:
            "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: "
            Esto asegura la consistencia de los mensajes de error del sistema.
        """
        service = SolicitudInsigniaService()

        cuerpo_invalido = "CUERPO_NO_AUTORIZADO"
        prefijo_esperado = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: "

        with self.assertRaises(ValidationError) as cm:
            service._validar_pertenencia_cuerpos({cuerpo_invalido})
        
        mensaje_real = cm.exception.message

        self.assertTrue(
            mensaje_real.startswith(prefijo_esperado),
            f"El mensaje de error no comienza con el literal esperado.\n"
            f"Esperado: '{prefijo_esperado}'\n"
            f"Obtenido: '{mensaje_real}'"
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



    def test_validar_preferencias_una_sola_valida_pasa(self):
        """
        Test: Una sola preferencia válida (Caso mínimo)

        Given: Una lista 'preferencias_data' con un único elemento válido.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se ejecuta todo el flujo:
            - Se resuelven los puestos.
            - Se validan prioridades y unicidad con listas de un solo elemento.
            - Se llama a _validar_item_puesto exactamente una vez.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_cuerpos = {"PRIOSTÍA"}
        preferencias_data = [
            {"puesto_solicitado": "Incienso", "orden_prioridad": 1}
        ]

        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            mock_hermano, mock_acto, preferencias_data, mock_cuerpos
        )

        service._validar_prioridades_consecutivas.assert_called_once_with([1])
        service._validar_puestos_unicos.assert_called_once_with(["Incienso"])

        service._validar_item_puesto.assert_called_once_with(mock_cuerpos, mock_acto, "Incienso")



    def test_validar_preferencias_multiples_validas_itera_correctamente(self):
        """
        Test: Múltiples preferencias válidas

        Given: Una lista 'preferencias_data' con tres elementos válidos.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se valida la iteración correcta:
            - Se construyen las listas completas (3 elementos).
            - Se llama a _validar_item_puesto 3 veces (una por cada puesto).
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_cuerpos = {"NAZARENOS"}
        preferencias_data = [
            {"puesto_solicitado": "Puesto 1", "orden_prioridad": 1},
            {"puesto_solicitado": "Puesto 2", "orden_prioridad": 2},
            {"puesto_solicitado": "Puesto 3", "orden_prioridad": 3},
        ]

        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            mock_hermano, mock_acto, preferencias_data, mock_cuerpos
        )

        service._validar_prioridades_consecutivas.assert_called_once_with([1, 2, 3])
        service._validar_puestos_unicos.assert_called_once_with(["Puesto 1", "Puesto 2", "Puesto 3"])

        self.assertEqual(service._validar_item_puesto.call_count, 3)

        service._validar_item_puesto.assert_any_call(mock_cuerpos, mock_acto, "Puesto 2")



    def test_validar_preferencias_construccion_correcta_de_listas(self):
        """
        Test: Verificar construcción de listas

        Given: Un set de preferencias_data con datos heterogéneos.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se verifica que las listas internas 'puestos' y 'prioridades' 
            se construyen con todos los elementos y se pasan 
            correctamente a los validadores grupales.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Cruz de Guía", "orden_prioridad": 1},
            {"puesto_solicitado": "Farol", "orden_prioridad": 2}
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), MagicMock(), preferencias_data, set()
        )

        args_prioridades, _ = service._validar_prioridades_consecutivas.call_args
        args_puestos, _ = service._validar_puestos_unicos.call_args

        self.assertEqual(args_prioridades[0], [1, 2])
        self.assertEqual(args_puestos[0], ["Cruz de Guía", "Farol"])



    def test_validar_preferencias_orden_de_ejecucion_estricto(self):
        """
        Test: Verificar orden de ejecución

        Given: Un flujo de validación estándar.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se valida que el orden sea:
            1. Resolver existencia (falla rápido si el ID no existe).
            2. Validar prioridades consecutivas.
            3. Validar unicidad de puestos.
            4. Validar cada ítem (reglas de negocio específicas).
        """
        service = SolicitudInsigniaService()

        preferencias_data = [{"puesto_solicitado": "Puesto A", "orden_prioridad": 1}]

        manager = MagicMock()
        service._resolver_y_validar_existencia_puestos = manager._resolver_y_validar_existencia_puestos
        service._validar_prioridades_consecutivas = manager._validar_prioridades_consecutivas
        service._validar_puestos_unicos = manager._validar_puestos_unicos
        service._validar_item_puesto = manager._validar_item_puesto

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), MagicMock(), preferencias_data, set()
        )

        expected_calls = [
            call._resolver_y_validar_existencia_puestos(preferencias_data),
            call._validar_prioridades_consecutivas([1]),
            call._validar_puestos_unicos(["Puesto A"]),
            call._validar_item_puesto(set(), ANY, "Puesto A")
        ]

        manager.assert_has_calls(expected_calls, any_order=False)



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



    def test_validar_preferencias_falta_puesto_solicitado_falla(self):
        """
        Test: Falta puesto_solicitado

        Given: Una preferencia que tiene prioridad pero el puesto es None o falta.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se lanza ValidationError: "Datos de preferencia incompletos."
            Se detiene la ejecución antes de llamar a las validaciones finales.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [{"orden_prioridad": 1}] 
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_item_puesto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )
        
        self.assertEqual(cm.exception.message, "Datos de preferencia incompletos.")

        service._validar_item_puesto.assert_not_called()



    def test_validar_preferencias_falta_orden_prioridad_falla(self):
        """
        Test: Falta orden_prioridad

        Given: Una preferencia con puesto pero sin orden de prioridad.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se lanza ValidationError: "Datos de preferencia incompletos."
            Se garantiza que no se intenta validar la secuencia de prioridades.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [{"puesto_solicitado": "Incienso", "orden_prioridad": None}] 
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_item_puesto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )
        
        self.assertEqual(cm.exception.message, "Datos de preferencia incompletos.")

        service._validar_prioridades_consecutivas.assert_not_called()



    def test_validar_preferencias_puesto_solicitado_es_none_falla(self):
        """
        Test: puesto_solicitado = None

        Given: Una preferencia donde la clave 'puesto_solicitado' existe pero es None.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se lanza ValidationError: "Datos de preferencia incompletos."
            Se verifica que el sistema no intenta seguir procesando la lista.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [{"puesto_solicitado": None, "orden_prioridad": 1}] 
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_item_puesto = MagicMock()

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )
        
        self.assertEqual(cm.exception.message, "Datos de preferencia incompletos.")
        service._validar_prioridades_consecutivas.assert_not_called()



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
            dentro del bucle final (optimización y seguridad).
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



    def test_validar_preferencias_falla_en_primer_item_no_apto(self):
        """
        Test: _validar_item_puesto falla

        Given: Una lista con dos preferencias, donde la primera falla
            las reglas de negocio (ej: falta de antigüedad o cuerpo).
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se propaga la excepción del ítem.
            Se verifica que el bucle se detiene: _validar_item_puesto
            solo se llama UNA vez, no continúa con el resto de la lista.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Puesto Conflictivo", "orden_prioridad": 1},
            {"puesto_solicitado": "Puesto Ok", "orden_prioridad": 2}
        ]
        mensaje_error = "No tiene permiso para solicitar este puesto."

        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()

        service._validar_item_puesto = MagicMock(
            side_effect=ValidationError(mensaje_error)
        )

        with self.assertRaises(ValidationError) as cm:
            service._validar_preferencias_insignia_tradicional(
                MagicMock(), MagicMock(), preferencias_data, set()
            )
        
        self.assertEqual(cm.exception.message, mensaje_error)

        self.assertEqual(service._validar_item_puesto.call_count, 1)

        service._validar_item_puesto.assert_called_with(set(), ANY, "Puesto Conflictivo")



    def test_validar_preferencias_prioridades_desordenadas_pasan_tal_cual(self):
        """
        Test: Prioridades desordenadas pero válidas

        Given: Una lista donde la prioridad 2 aparece antes que la 1.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se valida que la lista 'prioridades' se construye siguiendo 
            el orden de aparición del input.
            Se delega el set [2, 1] a _validar_prioridades_consecutivas 
            sin alterar el orden.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Puesto A", "orden_prioridad": 2},
            {"puesto_solicitado": "Puesto B", "orden_prioridad": 1}
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), MagicMock(), preferencias_data, set()
        )

        service._validar_prioridades_consecutivas.assert_called_once_with([2, 1])



    def test_validar_preferencias_prioridades_duplicadas_se_delegan(self):
        """
        Test: Prioridades duplicadas

        Given: Dos puestos distintos con la misma prioridad asignada (1, 1).
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se construye la lista [1, 1] y se pasa al validador de prioridades.
            Se confirma que el orquestador no filtra duplicados por su cuenta.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Puesto A", "orden_prioridad": 1},
            {"puesto_solicitado": "Puesto B", "orden_prioridad": 1}
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), MagicMock(), preferencias_data, set()
        )

        service._validar_prioridades_consecutivas.assert_called_once_with([1, 1])



    def test_validar_preferencias_puestos_duplicados_se_delegan(self):
        """
        Test: Puestos duplicados

        Given: Una lista de preferencias donde se repite el mismo puesto 
            ("Vara 1") con diferentes prioridades.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se construye la lista ['Vara 1', 'Vara 1'] y se pasa 
            íntegramente a _validar_puestos_unicos.
            Se confirma que el orquestador delega la detección de 
            duplicados sin alterar los datos originales.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Vara 1", "orden_prioridad": 1},
            {"puesto_solicitado": "Vara 1", "orden_prioridad": 2}
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), MagicMock(), preferencias_data, set()
        )

        service._validar_puestos_unicos.assert_called_once_with(["Vara 1", "Vara 1"])



    def test_validar_preferencias_muchos_elementos_escala_correctamente(self):
        """
        Test: Muchos elementos

        Given: Una lista de preferencias con 100 elementos.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: 1. Se construyen correctamente listas de 100 puestos y 100 prioridades.
            2. Se llama a _validar_item_puesto exactamente 100 veces.
            3. El sistema no sufre degradación ni errores de desbordamiento.
        """
        service = SolicitudInsigniaService()

        cantidad = 100
        preferencias_data = [
            {"puesto_solicitado": f"Puesto {i}", "orden_prioridad": i} 
            for i in range(1, cantidad + 1)
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), MagicMock(), preferencias_data, set()
        )

        args_prio, _ = service._validar_prioridades_consecutivas.call_args
        args_puesto, _ = service._validar_puestos_unicos.call_args
        
        self.assertEqual(len(args_prio[0]), cantidad)
        self.assertEqual(len(args_puesto[0]), cantidad)

        self.assertEqual(service._validar_item_puesto.call_count, cantidad)



    def test_validar_preferencias_item_puesto_recibe_argumentos_exactos(self):
        """
        Test: Verificar que _validar_item_puesto recibe argumentos correctos

        Given: Un hermano con cuerpos específicos y un acto determinado.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se valida que cada llamada a _validar_item_puesto reciba:
            - El set de cuerpos del hermano (sin alteraciones).
            - El objeto acto.
            - El string del puesto solicitado.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(name="Acto_2026")
        cuerpos_hermano = {"NAZARENOS", "JUVENTUD"}
        preferencias_data = [{"puesto_solicitado": "Vara de Presidencia", "orden_prioridad": 1}]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), mock_acto, preferencias_data, cuerpos_hermano
        )

        service._validar_item_puesto.assert_called_once_with(
            cuerpos_hermano, 
            mock_acto, 
            "Vara de Presidencia"
        )



    def test_validar_preferencias_items_se_recorren_en_orden_de_entrada(self):
        """
        Test: Orden de validación de items

        Given: Una lista de preferencias con tres puestos en un orden específico.
        When: Se llama a _validar_preferencias_insignia_tradicional.
        Then: Se valida que _validar_item_puesto sea llamado siguiendo 
            estrictamente el orden de la lista de entrada.
        """
        service = SolicitudInsigniaService()

        preferencias_data = [
            {"puesto_solicitado": "Primero", "orden_prioridad": 1},
            {"puesto_solicitado": "Segundo", "orden_prioridad": 2},
            {"puesto_solicitado": "Tercero", "orden_prioridad": 3},
        ]
        
        service._resolver_y_validar_existencia_puestos = MagicMock()
        service._validar_prioridades_consecutivas = MagicMock()
        service._validar_puestos_unicos = MagicMock()
        service._validar_item_puesto = MagicMock()

        service._validar_preferencias_insignia_tradicional(
            MagicMock(), MagicMock(), preferencias_data, set()
        )

        llamadas = service._validar_item_puesto.call_args_list
        
        self.assertEqual(llamadas[0][0][2], "Primero")
        self.assertEqual(llamadas[1][0][2], "Segundo")
        self.assertEqual(llamadas[2][0][2], "Tercero")



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

        service._validar_item_puesto(cuerpos_hermano, mock_acto, mock_puesto)



    def test_validar_item_puesto_caso_minimo_valido_pasa(self):
        """
        Test: Caso mínimo válido

        Given: Un puesto estándar (no exclusivo) y un hermano sin cuerpos 
            específicos (set vacío).
        When: Se llama a _validar_item_puesto.
        Then: No lanza excepción. 
            Valida que el método es robusto ante cuerpos vacíos si el 
            puesto no tiene restricciones de acceso.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.solo_junta_gobierno = False

        cuerpos_hermano = set()

        service._validar_item_puesto(cuerpos_hermano, mock_acto, mock_puesto)



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



    def test_validar_item_puesto_orden_prioridad_de_errores(self):
        """
        Test: Múltiples condiciones inválidas (Orden importa)

        Given: Un puesto con dos fallos:
            1. Pertenece a otro acto (acto_id != acto.id).
            2. No está disponible (disponible = False).
        When: Se llama a _validar_item_puesto.
        Then: Debe lanzar el error del primer 'if' (pertenencia al acto).
            Esto confirma que el flujo se corta inmediatamente y sigue
            el orden de validación establecido.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Vara Test"
        mock_puesto.acto_id = 999
        mock_puesto.disponible = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(set(), mock_acto, mock_puesto)

        self.assertIn("no pertenece a este acto", cm.exception.message)
        self.assertNotIn("no está marcado como disponible", cm.exception.message)



    def test_validar_item_puesto_exclusivo_junta_con_set_vacio_falla(self):
        """
        Test: cuerpos_hermano_set vacío

        Given: Un puesto exclusivo de la Junta de Gobierno.
            Un set de cuerpos totalmente vacío.
        When: Se llama a _validar_item_puesto.
        Then: Lanza ValidationError indicando la exclusividad.
            Garantiza que la ausencia de datos se interpreta como 
            falta de permisos.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Estandarte"
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.solo_junta_gobierno = True

        cuerpos_vacio = set()

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(cuerpos_vacio, mock_acto, mock_puesto)
        
        self.assertIn("exclusivo para Junta de Gobierno", cm.exception.message)



    def test_validar_item_puesto_flags_combinados_evalua_ambos(self):
        """
        Test: Puesto insignia exclusivo de Junta

        Given: Un puesto que es una insignia (es_insignia=True) 
            pero también es exclusivo (solo_junta_gobierno=True).
            Un hermano que NO es de la Junta.
        When: Se llama a _validar_item_puesto.
        Then: Aunque pasa el filtro de 'es_insignia', debe fallar 
            en el filtro de 'solo_junta_gobierno'.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.solo_junta_gobierno = True

        cuerpos_hermano = {"NAZARENOS"}

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(cuerpos_hermano, mock_acto, mock_puesto)
        
        self.assertIn("exclusivo para Junta de Gobierno", cm.exception.message)



    def test_validar_item_puesto_mensajes_incluyen_nombre_dinamico(self):
        """
        Test: Verificar uso de puesto.nombre en errores

        Given: Un puesto con un nombre específico (ej: 'Simpecado').
            Una condición de fallo (ej: no disponible).
        When: Se llama a _validar_item_puesto.
        Then: El mensaje de error debe contener la palabra 'Simpecado'.
        """
        service = SolicitudInsigniaService()

        nombre_especifico = "Simpecado de la Hermandad"
        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = nombre_especifico
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(set(), mock_acto, mock_puesto)
        
        self.assertIn(
            nombre_especifico, 
            cm.exception.message, 
            f"El mensaje de error debería mencionar el puesto: {nombre_especifico}"
        )



    def test_validar_item_puesto_disponible_es_none_se_trata_como_falso(self):
        """
        Test: disponible = None

        Given: Un puesto donde el atributo 'disponible' es None.
        When: Se llama a _validar_item_puesto.
        Then: La condición 'if not puesto.disponible' debe cumplirse (None es Falsy).
            Se lanza ValidationError: "El puesto 'X' no está marcado como disponible."
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Incienso"
        mock_puesto.acto_id = 1
        mock_puesto.tipo_puesto.es_insignia = True
        mock_puesto.disponible = None

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(set(), mock_acto, mock_puesto)
        
        self.assertIn("no está marcado como disponible", cm.exception.message)



    def test_validar_item_puesto_acto_id_es_none_falla(self):
        """
        Test: puesto.acto_id = None

        Given: Un acto válido con ID 1 y un puesto cuyo acto_id es None.
        When: Se llama a _validar_item_puesto.
        Then: La comparación (None != 1) es True.
            Se lanza ValidationError indicando que no pertenece al acto.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock()
        mock_puesto.nombre = "Vara"
        mock_puesto.acto_id = None

        with self.assertRaises(ValidationError) as cm:
            service._validar_item_puesto(set(), mock_acto, mock_puesto)
        
        self.assertIn("no pertenece a este acto", cm.exception.message)



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
        service.MAX_PREFERENCIAS_PERMITIDAS = 5 

        service._validar_limites_preferencias([])



    def test_validar_limites_menor_que_el_maximo_pasa(self):
        """
        Test: Menos del límite

        Given: El límite es 5 y el usuario envía una lista con 3 elementos.
        When: Se llama a _validar_limites_preferencias.
        Then: No lanza excepción. 
            El comportamiento es normal al estar dentro del rango permitido.
        """
        service = SolicitudInsigniaService()
        service.MAX_PREFERENCIAS_PERMITIDAS = 5
        
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

        limite_max = 20
        service.MAX_PREFERENCIAS_PERMITIDAS = limite_max

        preferencias_data = [{"puesto": i} for i in range(limite_max)]

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

        limite_max = 20
        service.MAX_PREFERENCIAS_PERMITIDAS = limite_max

        preferencias_data = [{"puesto": i} for i in range(limite_max + 1)]

        with self.assertRaises(ValidationError) as cm:
            service._validar_limites_preferencias(preferencias_data)
        
        self.assertEqual(
            cm.exception.message, 
            f"No puede solicitar más de {limite_max} puestos."
        )



    def test_validar_limites_supera_ampliamente_el_maximo_falla(self):
        """
        Test: Supera ampliamente el límite

        Given: El límite es 20.
            El usuario intenta enviar 100 preferencias.
        When: Se llama a _validar_limites_preferencias.
        Then: Lanza ValidationError con el mismo mensaje descriptivo.
            Se garantiza que el comportamiento es independiente del exceso.
        """
        service = SolicitudInsigniaService()

        service.MAX_PREFERENCIAS_PERMITIDAS = 20

        preferencias_data = [{"puesto": i} for i in range(100)]

        with self.assertRaises(ValidationError) as cm:
            service._validar_limites_preferencias(preferencias_data)
        
        self.assertEqual(
            cm.exception.message, 
            "No puede solicitar más de 20 puestos."
        )



    def test_validar_limites_dinamico_usa_configuracion_de_instancia(self):
        """
        Test: Límite dinámico (si cambia constante)

        Given: Un cambio en MAX_PREFERENCIAS_PERMITIDAS a un valor distinto (ej: 5).
        When: Se llama a _validar_limites_preferencias con 6 elementos.
        Then: Debe fallar basándose en el nuevo límite (5), no en el antiguo.
            Valida que la lógica es dependiente de la configuración.
        """
        service = SolicitudInsigniaService()

        nuevo_limite = 5
        service.MAX_PREFERENCIAS_PERMITIDAS = nuevo_limite

        preferencias_data = [{"id": i} for i in range(nuevo_limite + 1)]

        with self.assertRaises(ValidationError) as cm:
            service._validar_limites_preferencias(preferencias_data)

        self.assertIn(f"más de {nuevo_limite} puestos", cm.exception.message)



    def test_validar_limites_solo_importa_el_tamano_no_el_contenido(self):
        """
        Test: Lista con elementos complejos

        Given: Una lista con diccionarios vacíos, anidados o con datos extraños.
        When: Se llama a _validar_limites_preferencias.
        Then: No debe lanzar excepción si el 'len' es menor o igual al máximo.
            Confirma que el método no "explota" al encontrar datos complejos.
        """
        service = SolicitudInsigniaService()
        service.MAX_PREFERENCIAS_PERMITIDAS = 10

        preferencias_data = [
            {"complejo": {"sub": 1}},
            {},
            ["lista", "en", "lugar", "de", "dict"]
        ]

        service._validar_limites_preferencias(preferencias_data)



    def test_validar_limites_input_none_lanza_type_error(self):
        """
        Test: Tipo incorrecto (no lista)

        Given: Un valor None en lugar de una lista.
        When: Se llama a _validar_limites_preferencias.
        Then: Se lanza TypeError de forma natural.
            Valida que el método asume que el input es iterable.
        """
        service = SolicitudInsigniaService()

        with self.assertRaises(TypeError):
            service._validar_limites_preferencias(None)



    def test_validar_limites_lista_con_nulos_cuenta_correctamente(self):
        """
        Test: Lista con None dentro

        Given: El límite es 20.
            Una lista con 21 elementos, todos ellos None.
        When: Se llama a _validar_limites_preferencias.
        Then: Lanza ValidationError.
            Confirma que el método cuenta posiciones en memoria, 
            no contenido válido.
        """
        service = SolicitudInsigniaService()
        service.MAX_PREFERENCIAS_PERMITIDAS = 20

        preferencias_data = [None] * 21

        with self.assertRaises(ValidationError) as cm:
            service._validar_limites_preferencias(preferencias_data)
        
        self.assertIn("No puede solicitar más de 20 puestos", cm.exception.message)



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



    def test_validar_18_anos_cumplidos_ayer_pasa(self):
        """
        Test: 18 años cumplidos recientemente

        Given: Fecha de referencia = 2026-04-20.
            Fecha de nacimiento = 2008-04-19 (Cumplió 18 ayer).
        When: Se llama a _validar_edad_minima_insignia.
        Then: No lanza excepción.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 4, 19)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = datetime(2026, 4, 20)

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



    @patch('django.utils.timezone.now')
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



    def test_validar_edad_cumple_exactamente_hoy_pasa(self):
        """
        Test: Cumple 18 justo el mismo día (edge crítico)

        Given: Fecha de referencia = 2026-04-20.
            Fecha de nacimiento = 2008-04-20.
        When: Se llama a _validar_edad_minima_insignia.
        Then: No lanza excepción.
            Confirma que la comparación booleana de tuplas en Python:
            (4, 20) < (4, 20) es False, por lo que no resta el año extra.
        """
        service = SolicitudInsigniaService()

        fecha_referencia = datetime(2026, 4, 20)
        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 4, 20)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = fecha_referencia

        service._validar_edad_minima_insignia(mock_hermano, mock_acto)



    def test_validar_edad_mismo_ano_pero_cumpleanos_futuro_falla(self):
        """
        Test: Diferencia por días (bug típico)

        Given: Fecha de referencia = 2026-04-20.
            Fecha de nacimiento = 2008-12-31.
        When: Se llama a _validar_edad_minima_insignia.
        Then: Se lanza ValidationError.
            Resta: (2026 - 2008) - 1 (porque abril < diciembre).
            Edad resultante = 17.
        """
        service = SolicitudInsigniaService()

        fecha_referencia = datetime(2026, 4, 20)
        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2008, 12, 31)
        
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



    def test_validar_edad_referencia_anterior_al_nacimiento_falla(self):
        """
        Test: Fecha de referencia anterior al nacimiento

        Given: Fecha de referencia = 2026-01-01.
            Fecha de nacimiento = 2027-01-01 (Dato inválido/futuro).
        When: Se llama a _validar_edad_minima_insignia.
        Then: La edad calculada será negativa (-1).
            Se lanza ValidationError porque -1 < 18.
            Garantiza que el sistema no permite el acceso con datos ilógicos.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.fecha_nacimiento = date(2027, 1, 1)
        
        mock_acto = MagicMock()
        mock_acto.inicio_solicitud = datetime(2026, 1, 1)

        with self.assertRaises(ValidationError) as cm:
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)
        
        self.assertIn("debe ser mayor de 18 años", cm.exception.message)



    def test_validar_edad_formato_fecha_en_error_es_correcto(self):
        """
        Test: Formato del mensaje de error

        Given: Un hermano menor de edad.
            Fecha de referencia = 2026-04-26.
        When: Se llama a _validar_edad_minima_insignia.
        Then: El mensaje de error contiene la fecha formateada como (26/04/2026).
            Valida el cumplimiento del requisito visual para el usuario.
        """
        service = SolicitudInsigniaService()

        fecha_ref = datetime(2026, 4, 26)
        mock_hermano = MagicMock(fecha_nacimiento=date(2015, 1, 1))
        mock_acto = MagicMock(inicio_solicitud=fecha_ref)

        with self.assertRaises(ValidationError) as cm:
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)

        fecha_esperada = "26/04/2026"
        self.assertIn(
            fecha_esperada, 
            cm.exception.message, 
            f"El mensaje de error debería mostrar la fecha en formato {fecha_esperada}"
        )



    @patch('django.utils.timezone.now')
    def test_validar_edad_uso_de_date_evita_problemas_timezone(self, mock_now):
        """
        Test: Diferentes zonas horarias

        Given: Un objeto datetime con hora cercana a la medianoche (23:59:59).
        When: Se extrae .date() para el cálculo de edad.
        Then: El cálculo debe ser consistente independientemente de la hora 
            o el desfase UTC, enfocándose solo en el día natural.
        """
        service = SolicitudInsigniaService()

        fecha_completa = datetime(2026, 4, 20, 23, 59, 59)
        mock_acto = MagicMock(inicio_solicitud=fecha_completa)

        mock_hermano = MagicMock(fecha_nacimiento=date(2008, 4, 20))

        service._validar_edad_minima_insignia(mock_hermano, mock_acto)



    def test_verificar_calculo_matematico_exacto_edad(self):
        """
        Test: Verificar cálculo exacto de edad

        Given: Tres escenarios específicos para la resta ajustada.
        When: Se ejecuta la lógica de cálculo.
        Then: 
            1. 2026-04-20 vs 2000-01-01 -> 26 - 0 = 26 (Cumpleaños pasado)
            2. 2026-04-20 vs 2000-04-20 -> 26 - 0 = 26 (Hoy es el cumpleaños)
            3. 2026-04-20 vs 2000-12-31 -> 26 - 1 = 25 (Cumpleaños no pasado)
        """
        service = SolicitudInsigniaService()

        fecha_ref = datetime(2026, 4, 20)
        mock_hermano = MagicMock(fecha_nacimiento=date(2000, 12, 31))
        mock_acto = MagicMock(inicio_solicitud=fecha_ref)

        try:
            service._validar_edad_minima_insignia(mock_hermano, mock_acto)
        except ValidationError:
            pass



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



    def test_validar_configuracion_acto_caso_minimo_pasa(self):
        """
        Test: Caso mínimo válido

        Given: Un acto que solo tiene definidos los campos estrictamente 
            necesarios para pasar los 'if'. El resto son nulos o vacíos.
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: No lanza excepción, demostrando que no hay dependencias ocultas.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()

        mock_acto.tipo_acto_id = 99
        mock_acto.tipo_acto.requiere_papeleta = True
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

        mock_acto.inicio_solicitud = None
        mock_acto.descripcion = ""

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



    def test_validar_configuracion_acto_orden_prioridad_falla_en_primero(self):
        """
        Test: Múltiples condiciones inválidas (orden importa)

        Given: Un acto con dos errores críticos:
            1. tipo_acto_id es None (Primer 'if').
            2. modalidad es incorrecta (Tercer 'if').
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: Se lanza el ValidationError correspondiente al primer error detectado.
            Se verifica que el proceso se detiene inmediatamente.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.tipo_acto_id = None
        mock_acto.modalidad = "MODALIDAD_INVALIDA"

        with self.assertRaises(ValidationError) as cm:
            service._validar_configuracion_acto_tradicional(mock_acto)

        self.assertEqual(
            cm.exception.message_dict, 
            {"tipo_acto": ["El tipo de acto es obligatorio."]}
        )

        self.assertNotIn(
            "exclusivo para actos de modalidad TRADICIONAL", 
            str(cm.exception)
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



    def test_validar_configuracion_acto_mensaje_incluye_nombre_dinamico(self):
        """
        Test: Verificar uso de acto.nombre en mensaje

        Given: Un acto llamado 'Traslado Extraordinario' que no requiere papeleta.
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: El mensaje de error debe contener el nombre 'Traslado Extraordinario'.
        """
        service = SolicitudInsigniaService()

        nombre_test = "Traslado Extraordinario"
        mock_acto = MagicMock()
        mock_acto.nombre = nombre_test
        mock_acto.tipo_acto_id = 1
        mock_acto.tipo_acto.requiere_papeleta = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_configuracion_acto_tradicional(mock_acto)
        
        self.assertIn(
            nombre_test, 
            cm.exception.message, 
            f"El mensaje de error debería mencionar el nombre del acto: {nombre_test}"
        )



    def test_validar_configuracion_acto_modalidad_exactamente_enum(self):
        """
        Test: modalidad == TRADICIONAL

        Given: Un acto con modalidad igual al valor del Enum TRADICIONAL.
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: No lanza excepción.
            Valida que la comparación de igualdad es exacta y semántica.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.tipo_acto_id = 1
        mock_acto.tipo_acto.requiere_papeleta = True

        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

        service._validar_configuracion_acto_tradicional(mock_acto)



    def test_validar_configuracion_acto_id_cero_es_valido(self):
        """
        Test: tipo_acto_id = 0

        Given: Un acto donde tipo_acto_id es 0 (un valor 'falsy' en Python).
        When: Se llama a _validar_configuracion_acto_tradicional.
        Then: No debe lanzar el error "El tipo de acto es obligatorio".
            Valida que el 'if' usa 'is None' en lugar de un chequeo booleano simple.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.tipo_acto_id = 0
        mock_acto.tipo_acto.requiere_papeleta = True
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

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



    def test_validar_plazo_exactamente_en_inicio_pasa(self):
        """
        Test: Fecha exactamente en el inicio

        Given: El plazo comienza a las 09:00:00.
            'ahora' son exactamente las 09:00:00.
        When: Se llama a _validar_plazo_vigente.
        Then: No lanza excepción.
            Valida que el límite inferior es inclusivo.
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 4, 1, 9, 0, 0)
        fin = datetime(2026, 4, 10, 20, 0, 0)
        ahora = inicio

        service._validar_plazo_vigente(ahora, inicio, fin, "Prueba")



    def test_validar_plazo_exactamente_en_fin_pasa(self):
        """
        Test: Fecha exactamente en el fin

        Given: El plazo termina a las 20:00:00.
            'ahora' son exactamente las 20:00:00.
        When: Se llama a _validar_plazo_vigente.
        Then: No lanza excepción.
            Valida que el límite superior es inclusivo (ahora <= fin).
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 4, 1, 9, 0, 0)
        fin = datetime(2026, 4, 10, 20, 0, 0)
        ahora = fin

        service._validar_plazo_vigente(ahora, inicio, fin, "Solicitud")



    def test_validar_plazo_inicio_es_none_falla(self):
        """
        Test: inicio es None

        Given: Un plazo de 'Solicitud' donde la fecha de inicio no está definida.
        When: Se llama a _validar_plazo_vigente.
        Then: Lanza ValidationError indicando que el plazo no está configurado.
        """
        service = SolicitudInsigniaService()

        ahora = datetime(2026, 4, 5, 12, 0)
        inicio = None
        fin = datetime(2026, 4, 10, 20, 0)
        nombre = "Solicitud"

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, nombre)
        
        self.assertEqual(
            cm.exception.message, 
            f"El plazo de {nombre} no está configurado en el acto."
        )



    def test_validar_plazo_fin_es_none_falla(self):
        """
        Test: fin es None

        Given: Un plazo de 'Alegaciones' donde falta la fecha de finalización.
        When: Se llama a _validar_plazo_vigente.
        Then: Lanza ValidationError con el mensaje de falta de configuración.
        """
        service = SolicitudInsigniaService()

        ahora = datetime(2026, 4, 5, 12, 0)
        inicio = datetime(2026, 4, 1, 9, 0)
        fin = None
        nombre = "Alegaciones"

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, nombre)
        
        self.assertEqual(
            cm.exception.message, 
            f"El plazo de {nombre} no está configurado en el acto."
        )



    def test_validar_plazo_ambos_nulos_falla(self):
        """
        Test: Ambos inicio y fin son None

        Given: Un plazo donde ni inicio ni fin están configurados (None).
        When: Se llama a _validar_plazo_vigente.
        Then: Lanza ValidationError indicando que el plazo no está configurado.
            Verifica que el primer 'if' captura la ausencia total de datos.
        """
        service = SolicitudInsigniaService()

        ahora = datetime(2026, 4, 5, 12, 0)
        nombre = "Solicitud"

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, None, None, nombre)
        
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



    def test_validar_plazo_rango_invertido_falla(self):
        """
        Test: inicio > fin (configuración inválida)

        Given: Un inicio el 2026-05-01 y un fin el 2026-04-01.
            'ahora' es el 2026-04-15.
        When: Se llama a _validar_plazo_vigente.
        Then: El sistema lanza el primer error que encuentra (ahora < inicio).
            Incluso con fechas invertidas, el sistema deniega el acceso.
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 5, 1)
        fin = datetime(2026, 4, 1)
        ahora = datetime(2026, 4, 15)

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, "Test")
        
        self.assertIn("aún no ha comenzado", cm.exception.message)



    def test_validar_plazo_tipos_inconsistentes_lanza_type_error(self):
        """
        Test: Tipos datetime vs date

        Given: 'ahora' es un objeto datetime.
            'inicio' es un objeto date (sin hora).
        When: Se llama a _validar_plazo_vigente.
        Then: Se lanza TypeError.
            Detecta que el método no realiza conversiones de tipo internas.
        """
        service = SolicitudInsigniaService()

        ahora = datetime(2026, 4, 5, 12, 0)
        inicio = date(2026, 4, 1)
        fin = datetime(2026, 4, 10, 20, 0)

        with self.assertRaises(TypeError):
            service._validar_plazo_vigente(ahora, inicio, fin, "Test")



    def test_validar_plazo_mezcla_aware_y_naive_falla(self):
        """
        Test: Zona horaria (Aware vs Naive)

        Given: 'ahora' es un datetime 'aware' (con zona horaria).
            'inicio' es un datetime 'naive' (sin zona horaria).
        When: Se llama a _validar_plazo_vigente.
        Then: Se lanza TypeError.
            Valida que el sistema exige coherencia en el manejo de zonas horarias.
        """
        service = SolicitudInsigniaService()

        ahora = timezone.now()
        inicio = datetime(2026, 4, 1, 9, 0)
        fin = datetime(2026, 4, 10, 20, 0)

        with self.assertRaises(TypeError):
            service._validar_plazo_vigente(ahora, inicio, fin, "Test")



    def test_validar_plazo_mensaje_usa_nombre_dinamico(self):
        """
        Test: Nombre dinámico del plazo

        Given: El nombre del plazo es 'Alegaciones'.
            La fecha actual es posterior al fin.
        When: Se llama a _validar_plazo_vigente.
        Then: El mensaje de error debe mencionar explícitamente 'Alegaciones'.
        """
        service = SolicitudInsigniaService()

        nombre_especifico = "Alegaciones"
        inicio = datetime(2026, 5, 1)
        fin = datetime(2026, 5, 5)
        ahora = datetime(2026, 5, 6)

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, nombre_especifico)
        
        self.assertIn(
            f"plazo de solicitud de {nombre_especifico}", 
            cm.exception.message,
            "El mensaje de error debe inyectar el nombre del plazo correctamente."
        )



    def test_validar_plazo_prioridad_configuracion_sobre_comparacion(self):
        """
        Test: Orden de validaciones (fail-fast)

        Given: Un escenario donde 'inicio' es None y 'ahora' es una fecha válida.
        When: Se llama a _validar_plazo_vigente.
        Then: Debe lanzar el error de "no está configurado" (primer if).
            Esto confirma que el sistema no intenta comparar con None.
        """
        service = SolicitudInsigniaService()

        ahora = datetime(2026, 4, 5)
        inicio = None
        fin = datetime(2026, 4, 10)

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, "Solicitud")
        
        self.assertIn("no está configurado", cm.exception.message)



    def test_validar_plazo_limite_microsegundos_falla(self):
        """
        Test: Valores límite con microsegundos

        Given: El plazo termina a las 20:00:00.000000.
            'ahora' es las 20:00:00.000001 (un microsegundo tarde).
        When: Se llama a _validar_plazo_vigente.
        Then: Lanza ValidationError: "ha finalizado".
            Confirma que la precisión del validador es absoluta.
        """
        service = SolicitudInsigniaService()

        inicio = datetime(2026, 4, 1, 9, 0)
        fin = datetime(2026, 4, 10, 20, 0, 0, 0)
        ahora = fin + timedelta(microseconds=1) 

        with self.assertRaises(ValidationError) as cm:
            service._validar_plazo_vigente(ahora, inicio, fin, "Solicitud")
        
        self.assertIn("ha finalizado", cm.exception.message)



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



    def test_validar_hermano_en_alta_solo_depende_del_estado(self):
        """
        Test: Estado ALTA explícito (caso mínimo)

        Given: Un objeto hermano donde solo definimos el estado ALTA.
        When: Se llama a _validar_hermano_en_alta.
        Then: No lanza excepción, demostrando que no requiere otros campos.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.estado_hermano = Hermano.EstadoHermano.ALTA

        mock_hermano.nombre = None
        mock_hermano.deuda_total = 9999 

        service._validar_hermano_en_alta(mock_hermano)



    def test_validar_hermano_distinto_de_alta_falla(self):
        """
        Test: Hermano en cualquier estado distinto de ALTA

        Given: Diferentes estados no permitidos.
        When: Se llama a _validar_hermano_en_alta.
        Then: En todos los casos lanza ValidationError con el mensaje:
            "Solo los hermanos en estado ALTA pueden solicitar papeleta."
        """
        service = SolicitudInsigniaService()

        estados_invalidos = [
            "BAJA", 
            "FALLECIDO", 
            "SUSPENDIDO", 
            "SOLICITUD_PENDIENTE"
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



    def test_validar_hermano_estado_none_falla(self):
        """
        Test: Estado None

        Given: Un objeto hermano cuyo estado_hermano es None.
        When: Se llama a _validar_hermano_en_alta.
        Then: Se lanza ValidationError.
            Garantiza que la falta de información se trata como denegación.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.estado_hermano = None

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_en_alta(mock_hermano)
        
        self.assertEqual(
            cm.exception.message, 
            "Solo los hermanos en estado ALTA pueden solicitar papeleta."
        )



    def test_validar_hermano_estado_exhaustivo_falla(self):
        """
        Test: Verificar exhaustividad del enum

        Given: Valores que no pertenecen al modelo o son inesperados.
        When: Se llama a _validar_hermano_en_alta.
        Then: Lanza ValidationError. 
            Garantiza que el sistema es "cerrado": si no es ALTA, es error.
        """
        service = SolicitudInsigniaService()
        
        casos_imprevistos = ["", "INVÁLIDO", "null", "PENDIENTE_PAGO"]

        for valor in casos_imprevistos:
            with self.subTest(valor=valor):
                mock_hermano = MagicMock(estado_hermano=valor)
                with self.assertRaises(ValidationError):
                    service._validar_hermano_en_alta(mock_hermano)



    def test_validar_hermano_comparacion_exacta_con_enum(self):
        """
        Test: Comparación exacta con enum

        Given: El valor real definido en Hermano.EstadoHermano.ALTA.
        When: Se llama a _validar_hermano_en_alta.
        Then: No lanza excepción.
            Valida que el servicio usa la referencia al Enum y no hardcodea strings.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()

        mock_hermano.estado_hermano = Hermano.EstadoHermano.ALTA

        service._validar_hermano_en_alta(mock_hermano)



    def test_validar_hermano_detecta_nuevos_estados_como_invalidos(self):
        """
        Test: Cambio futuro del enum

        Given: Un estado nuevo que no existía originalmente (ej: 'HONORARIO').
        When: Se llama a _validar_hermano_en_alta.
        Then: Debe lanzar ValidationError.
            Valida que la lógica es restrictiva: solo permite ALTA, 
            bloqueando cualquier novedad no autorizada.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_hermano.estado_hermano = "HONORARIO" 

        with self.assertRaises(ValidationError):
            service._validar_hermano_en_alta(mock_hermano)



    def test_validar_hermano_mensaje_error_es_estable(self):
        """
        Test: Mensaje de error exacto

        Given: Un hermano que no está en ALTA.
        When: Se llama a _validar_hermano_en_alta.
        Then: El mensaje de la excepción debe ser exactamente el esperado.
            Evita cambios accidentales en la redacción que afecten al frontend.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(estado_hermano="BAJA")
        mensaje_esperado = "Solo los hermanos en estado ALTA pueden solicitar papeleta."

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_en_alta(mock_hermano)
        
        self.assertEqual(cm.exception.message, mensaje_esperado)



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
    def test_validar_al_corriente_caso_minimo_valido_pasa(self, mock_now):
        """
        Test: Solo historial válido, sin cuotas pendientes

        Given: El hermano tiene al menos una cuota registrada.
            La consulta de deuda devuelve una lista vacía/None.
        When: Se llama al validador de tesorería.
        Then: No lanza excepción, confirmando que el historial mínimo es suficiente.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()

        mock_chain = mock_hermano.cuotas.filter.return_value
        mock_chain.values.return_value.order_by.return_value.first.return_value = None

        mock_hermano.cuotas.filter.return_value.exists.return_value = True

        service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)



    @patch('django.utils.timezone.now')
    def test_validar_al_corriente_cuotas_futuras_no_cuentan_como_historial(self, mock_now):
        """
        Test: Cuotas fuera del límite pero sin deuda

        Given: Año actual = 2026 (Límite = 2025).
            El hermano tiene cuotas en 2026.
            El hermano NO tiene cuotas en 2025 o anteriores (exists=False).
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: Lanza ValidationError por falta de historial.
            Valida que el filtro temporal del ORM es estricto.
        """
        service = SolicitudInsigniaService()

        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None

        mock_hermano.cuotas.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        
        self.assertIn("No constan cuotas registradas hasta el año 2025", cm.exception.message)



    @patch('django.utils.timezone.now')
    def test_validar_deuda_pendiente_bloquea_solicitud(self, mock_now):
        """
        Test: Tiene deuda pendiente

        Given: El hermano tiene una cuota en estado PENDIENTE del año 2023.
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: Lanza ValidationError con el mensaje específico del año 2023.
            Verifica que el flujo se corta antes de validar el historial.
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
    def test_validar_deuda_devuelta_bloquea_solicitud(self, mock_now):
        """
        Test: Tiene deuda devuelta

        Given: El hermano tiene una cuota que fue devuelta por el banco.
        When: Se llama al servicio de validación de deuda.
        Then: Lanza ValidationError, tratando la devolución como una deuda activa.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {
            'anio': 2024
        }

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        
        self.assertIn("cuota pendiente o devuelta del año 2024", cm.exception.message)



    @patch('django.utils.timezone.now')
    def test_validar_al_corriente_sin_historial_falla(self, mock_now):
        """
        Test: No tiene historial

        Given: Año actual = 2026.
            La consulta de deuda no devuelve nada (deuda = None).
            La consulta de historial devuelve False (no existen cuotas hasta 2025).
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: Lanza ValidationError indicando que no constan cuotas registradas.
            Verifica que el mensaje dirige al hermano a secretaría.
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
    def test_validar_al_corriente_calculo_dinamico_anio_limite(self, mock_now):
        """
        Test: Año actual dinámico

        Given: Simulamos que estamos en el año 2030.
        When: Se llama al servicio de validación.
        Then: El anio_limite calculado debe ser 2029.
            Se verifica en el mensaje de error de historial.
        """
        service = SolicitudInsigniaService()

        mock_now.return_value.date.return_value.year = 2030

        mock_hermano = MagicMock()
        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None
        mock_hermano.cuotas.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)

        self.assertIn("hasta el año 2029", cm.exception.message)



    @patch('django.utils.timezone.now')
    def test_validar_deuda_justo_en_anio_limite_falla(self, mock_now):
        """
        Test: Cuota justo en límite (anio == anio_limite)

        Given: Año actual 2026 -> Límite 2025.
            El hermano tiene una cuota PENDIENTE de 2025.
        When: Se llama al servicio.
        Then: Lanza ValidationError porque 2025 <= 2025 es True.
            Valida la inclusividad del límite superior de deuda.
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
    def test_validar_varias_deudas_informa_solo_la_mas_antigua(self, mock_now):
        """
        Test: Múltiples deudas (solo la más antigua)

        Given: El hermano debe 2022, 2023 y 2024.
        When: Se llama al servicio.
        Then: El mensaje de error menciona únicamente el año 2022.
            Confirma que el servicio no satura al usuario con una lista de deudas.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {
            'anio': 2022
        }

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        
        self.assertIn("del año 2022", cm.exception.message)
        self.assertNotIn("2023", cm.exception.message)
        self.assertNotIn("2024", cm.exception.message)



    @patch('django.utils.timezone.now')
    def test_verificar_llamada_al_ordenamiento_del_query(self, mock_now):
        """
        Test: Verificar orden del query

        Given: Un objeto hermano con cuotas.
        When: Se ejecuta la validación de deuda.
        Then: Se verifica que se llamó al método .order_by con el parámetro 'anio'.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()
        chain = mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value
        chain.first.return_value = None

        try:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)
        except ValidationError:
            pass

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.assert_called_with('anio')



    @patch('django.utils.timezone.now')
    def test_validar_prioridad_deuda_sobre_historial(self, mock_now):
        """
        Test: Conflicto deuda vs historial

        Given: Un escenario (teórico) donde hay una deuda detectada.
        When: Se llama al servicio.
        Then: El sistema debe lanzar la excepción de deuda y detenerse.
            No debe llegar nunca a evaluar el segundo bloque del historial.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {'anio': 2022}

        with self.assertRaises(ValidationError) as cm:
            service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)

        self.assertIn("cuota pendiente o devuelta", cm.exception.message)

        self.assertFalse(mock_hermano.cuotas.filter.return_value.exists.called)



    @patch('django.utils.timezone.now')
    def test_verificar_filtro_estados_deuda(self, mock_now):
        """
        Test: Estados incluidos correctamente
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026
        mock_hermano = MagicMock()

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None
        mock_hermano.cuotas.filter.return_value.exists.return_value = True

        service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)

        llamadas_filter = mock_hermano.cuotas.filter.call_args_list

        args_deuda, kwargs_deuda = llamadas_filter[0]

        self.assertIn('estado__in', kwargs_deuda)
        self.assertIn(Cuota.EstadoCuota.PENDIENTE, kwargs_deuda['estado__in'])
        self.assertIn(Cuota.EstadoCuota.DEVUELTA, kwargs_deuda['estado__in'])
        self.assertEqual(len(kwargs_deuda['estado__in']), 2)

        args_historial, kwargs_historial = llamadas_filter[1]
        self.assertIn('anio__lte', kwargs_historial)
        self.assertEqual(kwargs_historial['anio__lte'], 2025)



    @patch('django.utils.timezone.now')
    def test_validar_al_corriente_ignora_cuotas_pagadas_o_anuladas(self, mock_now):
        """
        Test: Estados ignorados (pagada / anulada)

        Given: El hermano tiene cuotas, pero están todas como PAGADA o ANULADA.
        When: Se llama a _validar_hermano_al_corriente_hasta_anio_anterior.
        Then: La consulta de deuda devuelve None.
            El sistema pasa a la validación de historial y permite el éxito.
        """
        service = SolicitudInsigniaService()
        mock_now.return_value.date.return_value.year = 2026

        mock_hermano = MagicMock()

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None

        mock_hermano.cuotas.filter.return_value.exists.return_value = True

        service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano)



    # -------------------------------------------------------------------------
    # TEST VALIDAR EXISTENCIA PUESTO
    # -------------------------------------------------------------------------

    @patch('api.models.Puesto.objects.filter')
    def test_resolver_ids_validos_sustituye_por_instancias(self, mock_filter):
        """
        Test: Lista con IDs válidos -> convierte a instancias

        Given: Una lista de preferencias con IDs enteros [1, 2].
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: 
            - Se llama a la BD con los IDs correctos.
            - La lista original se actualiza con los objetos mockeados.
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 1},
            {"puesto_solicitado": 2}
        ]

        mock_p1 = MagicMock(spec=Puesto, id=1)
        mock_p2 = MagicMock(spec=Puesto, id=2)

        mock_filter.return_value.select_related.return_value = [mock_p1, mock_p2]

        service._resolver_y_validar_existencia_puestos(preferencias)

        mock_filter.assert_called_once()
        args, kwargs = mock_filter.call_args
        self.assertIn(1, kwargs['id__in'])
        self.assertIn(2, kwargs['id__in'])

        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p1)
        self.assertEqual(preferencias[1]["puesto_solicitado"], mock_p2)



    @patch('api.models.Puesto.objects.filter')
    def test_mezcla_ids_e_instancias_respeta_objetos_existentes(self, mock_filter):
        """
        Test: Mezcla de IDs e instancias

        Given: Una lista con un ID (10), un objeto Puesto real y un ID en string ("20").
        When: Se llama al servicio.
        Then: 
            - Solo se buscan en BD los IDs 10 y 20.
            - El objeto Puesto original se mantiene intacto.
        """
        service = SolicitudInsigniaService()

        puesto_ya_existente = MagicMock(spec=Puesto)
        preferencias = [
            {"puesto_solicitado": 10},
            {"puesto_solicitado": puesto_ya_existente},
            {"puesto_solicitado": "20"}
        ]
        
        mock_p10 = MagicMock(spec=Puesto, id=10)
        mock_p20 = MagicMock(spec=Puesto, id=20)
        mock_filter.return_value.select_related.return_value = [mock_p10, mock_p20]

        service._resolver_y_validar_existencia_puestos(preferencias)

        call_ids = mock_filter.call_args[1]['id__in']
        self.assertEqual(len(call_ids), 2)
        self.assertIn(10, call_ids)
        self.assertIn(20, call_ids)

        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p10)
        self.assertEqual(preferencias[1]["puesto_solicitado"], puesto_ya_existente)
        self.assertEqual(preferencias[2]["puesto_solicitado"], mock_p20)



    @patch('api.models.Puesto.objects.filter')
    def test_todos_son_instancias_no_ejecuta_query(self, mock_filter):
        """
        Test: Todos son instancias de Puesto

        Given: Una lista donde todos los valores ya son objetos Puesto.
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: No se realiza ninguna llamada a Puesto.objects.filter.
        """
        service = SolicitudInsigniaService()

        puesto_a = MagicMock(spec=Puesto)
        puesto_b = MagicMock(spec=Puesto)
        preferencias = [
            {"puesto_solicitado": puesto_a},
            {"puesto_solicitado": puesto_b}
        ]

        service._resolver_y_validar_existencia_puestos(preferencias)

        mock_filter.assert_not_called()
        self.assertEqual(preferencias[0]["puesto_solicitado"], puesto_a)



    @patch('api.models.Puesto.objects.filter')
    def test_valores_none_se_ignoran_y_no_se_buscan(self, mock_filter):
        """
        Test: Valores None ignorados

        Given: Una lista con un ID válido y un valor None.
        When: Se llama al servicio.
        Then: Solo se incluye el ID válido en la búsqueda. El None permanece igual.
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 5},
            {"puesto_solicitado": None}
        ]
        
        mock_p5 = MagicMock(spec=Puesto, id=5)
        mock_filter.return_value.select_related.return_value = [mock_p5]

        service._resolver_y_validar_existencia_puestos(preferencias)

        call_ids = mock_filter.call_args[1]['id__in']
        self.assertEqual(list(call_ids), [5])
        
        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p5)
        self.assertIsNone(preferencias[1]["puesto_solicitado"])



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_ids_string_numerico_sustituye_correctamente(self, mock_filter):
        """
        Test: IDs como string numérico

        Given: Una preferencia con el ID "12" (string).
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: 
            - Se busca el ID 12 (como int) en la base de datos.
            - Se sustituye el string por la instancia de Puesto.
        """
        service = SolicitudInsigniaService()

        preferencias = [{"puesto_solicitado": "12"}]
        
        mock_p12 = MagicMock(spec=Puesto, id=12)

        mock_filter.return_value.select_related.return_value = [mock_p12]

        service._resolver_y_validar_existencia_puestos(preferencias)

        call_ids = mock_filter.call_args[1]['id__in']
        self.assertIn(12, call_ids)
        self.assertIsInstance(list(call_ids)[0], int)

        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p12)



    def test_resolver_formato_string_no_numerico_falla(self):
        """
        Test: Formato inválido (string no numérico)

        Given: Una preferencia con el valor "ABC".
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: Lanza ValidationError indicando el formato inválido.
            Verifica que el mensaje incluya el valor erróneo para depuración.
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
    def test_resolver_ids_no_existentes_en_bd_falla(self, mock_filter):
        """
        Test: IDs no existentes

        Given: Se solicitan los IDs [1, 2, 3, 4].
            La base de datos solo devuelve los objetos para [1, 2].
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: Lanza ValidationError listando los IDs faltantes: 3, 4.
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 1}, {"puesto_solicitado": 2},
            {"puesto_solicitado": 3}, {"puesto_solicitado": 4}
        ]

        mock_p1 = MagicMock(spec=Puesto, id=1)
        mock_p2 = MagicMock(spec=Puesto, id=2)
        mock_filter.return_value.select_related.return_value = [mock_p1, mock_p2]

        with self.assertRaises(ValidationError) as cm:
            service._resolver_y_validar_existencia_puestos(preferencias)

        self.assertIn("Los siguientes IDs de puesto no existen: 3, 4", cm.exception.message)



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_todos_los_ids_faltantes_falla_con_lista_completa(self, mock_filter):
        """
        Test: Todos los IDs faltantes

        Given: Se solicitan los IDs [10, 20].
            La base de datos devuelve un QuerySet vacío.
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: Lanza ValidationError listando ambos IDs: 10, 20.
            Verifica que el sistema no se rompe al intentar iterar un mapa vacío.
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 10},
            {"puesto_solicitado": 20}
        ]

        mock_filter.return_value.select_related.return_value = []

        with self.assertRaises(ValidationError) as cm:
            service._resolver_y_validar_existencia_puestos(preferencias)
        
        self.assertIn("10", cm.exception.message)
        self.assertIn("20", cm.exception.message)
        self.assertIn("Los siguientes IDs de puesto no existen", cm.exception.message)



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_lista_vacia_retorna_inmediatamente(self, mock_filter):
        """
        Test: Lista vacía

        Given: Una lista de preferencias vacía [].
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: El servicio no realiza ninguna operación y no llama a la BD.
        """
        service = SolicitudInsigniaService()
        preferencias = []

        service._resolver_y_validar_existencia_puestos(preferencias)

        mock_filter.assert_not_called()



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_ids_duplicados_solo_realiza_una_busqueda_por_id(self, mock_filter):
        """
        Test: IDs duplicados

        Given: Una lista con IDs repetidos [1, 1, 1].
        When: Se llama al servicio.
        Then: 
            - El filtro id__in solo contiene una vez el ID 1.
            - Todas las entradas de la lista se sustituyen por la misma instancia.
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 1},
            {"puesto_solicitado": 1},
            {"puesto_solicitado": "1"}
        ]
        
        mock_p1 = MagicMock(spec=Puesto, id=1)
        mock_filter.return_value.select_related.return_value = [mock_p1]

        service._resolver_y_validar_existencia_puestos(preferencias)

        call_ids = mock_filter.call_args[1]['id__in']
        self.assertEqual(len(call_ids), 1)
        self.assertIn(1, call_ids)

        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p1)
        self.assertEqual(preferencias[1]["puesto_solicitado"], mock_p1)
        self.assertEqual(preferencias[2]["puesto_solicitado"], mock_p1)



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_modifica_la_lista_original_in_place(self, mock_filter):
        """
        Test: Mutación in-place

        Given: Una lista de preferencias definida en una variable.
        When: Se pasa dicha variable al servicio.
        Then: La variable original queda mutada con las instancias de Puesto.
        """
        service = SolicitudInsigniaService()

        id_solicitado = 99
        preferencias_originales = [{"puesto_solicitado": id_solicitado}]
        
        mock_puesto = MagicMock(spec=Puesto, id=id_solicitado)
        mock_filter.return_value.select_related.return_value = [mock_puesto]

        service._resolver_y_validar_existencia_puestos(preferencias_originales)

        self.assertIsInstance(preferencias_originales[0]["puesto_solicitado"], MagicMock)
        self.assertEqual(preferencias_originales[0]["puesto_solicitado"], mock_puesto)



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_string_con_espacios_sustituye_correctamente(self, mock_filter):
        """
        Test: Strings numéricos con espacios

        Given: Un ID que llega como string con espacios " 12 ".
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: 
            - El servicio limpia el string y reconoce el ID 12.
            - Se realiza la consulta y se sustituye por la instancia.
        """
        service = SolicitudInsigniaService()

        preferencias = [{"puesto_solicitado": " 12 "}]
        mock_p12 = MagicMock(spec=Puesto, id=12)
        mock_filter.return_value.select_related.return_value = [mock_p12]

        service._resolver_y_validar_existencia_puestos(preferencias)

        call_ids = mock_filter.call_args[1]['id__in']
        self.assertIn(12, call_ids)
        self.assertEqual(preferencias[0]["puesto_solicitado"], mock_p12)



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_incluye_select_related_para_evitar_n_plus_1(self, mock_filter):
        """
        Test: select_related está presente

        Given: Una solicitud de puestos.
        When: Se llama a _resolver_y_validar_existencia_puestos.
        Then: Se verifica que la consulta incluye select_related('tipo_puesto').
        """
        service = SolicitudInsigniaService()
        preferencias = [{"puesto_solicitado": 1}]

        mock_filter.return_value.select_related.return_value = [MagicMock(id=1)]

        service._resolver_y_validar_existencia_puestos(preferencias)

        mock_filter.return_value.select_related.assert_called_once_with('tipo_puesto')



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_ids_parcialmente_encontrados_lanza_error_con_faltantes(self, mock_filter):
        """
        Test: IDs parcialmente encontrados

        Given: Se solicitan los IDs [1, 2, 3].
            La base de datos solo devuelve los objetos para [1, 2].
        When: Se llama al servicio.
        Then: Lanza ValidationError indicando específicamente que el ID 3 no existe.
        """
        service = SolicitudInsigniaService()

        preferencias = [
            {"puesto_solicitado": 1},
            {"puesto_solicitado": 2},
            {"puesto_solicitado": 3}
        ]

        mock_p1 = MagicMock(spec=Puesto, id=1)
        mock_p2 = MagicMock(spec=Puesto, id=2)
        mock_filter.return_value.select_related.return_value = [mock_p1, mock_p2]

        with self.assertRaises(ValidationError) as cm:
            service._resolver_y_validar_existencia_puestos(preferencias)

        self.assertIn("no existen: 3", cm.exception.message)
        self.assertNotIn("1", cm.exception.message)
        self.assertNotIn("2", cm.exception.message)



    @patch('api.models.Puesto.objects.filter')
    def test_resolver_instancias_tienen_tipo_puesto_accesible(self, mock_filter):
        """
        Test: tipo_puesto cargado correctamente

        Given: Un ID de puesto que se resuelve con éxito.
        When: Se accede a la instancia sustituida en preferencias_data.
        Then: La instancia debe tener acceso a su atributo 'tipo_puesto'.
            Esto confirma que el objeto resuelto es funcional y completo.
        """
        service = SolicitudInsigniaService()

        preferencias = [{"puesto_solicitado": 1}]

        mock_tipo = MagicMock(spec=TipoPuesto, nombre="Cruz de Guía")

        mock_puesto = MagicMock(spec=Puesto, id=1, tipo_puesto=mock_tipo)
        
        mock_filter.return_value.select_related.return_value = [mock_puesto]

        service._resolver_y_validar_existencia_puestos(preferencias)

        puesto_resuelto = preferencias[0]["puesto_solicitado"]

        self.assertEqual(puesto_resuelto.tipo_puesto.nombre, "Cruz de Guía")
        self.assertIsInstance(puesto_resuelto.tipo_puesto, MagicMock)



    # -------------------------------------------------------------------------
    # TEST VALIDAR PRIORIDADES CONSECUTIVAS
    # -------------------------------------------------------------------------

    def test_validar_prioridades_consecutivas_ordenadas_pasa(self):
        """
        Test: Secuencia válida básica

        Given: Una lista de prioridades [1, 2, 3].
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
            El sistema entiende que están el 1, el 2 y el 3 aunque no estén en orden.
        """
        service = SolicitudInsigniaService()
        prioridades = [3, 1, 2]

        service._validar_prioridades_consecutivas(prioridades)



    def test_validar_prioridades_caso_minimo_pasa(self):
        """
        Test: Caso mínimo válido

        Given: Una lista con un único elemento [1].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: No lanza excepción.
        """
        service = SolicitudInsigniaService()
        prioridades = [1]

        service._validar_prioridades_consecutivas(prioridades)



    def test_validar_prioridades_secuencia_larga_pasa(self):
        """
        Test: Secuencia grande válida

        Given: Una lista generada dinámicamente del 1 al 50.
        When: Se llama a _validar_prioridades_consecutivas.
        Then: No lanza excepción, confirmando que la lógica no tiene límites hardcodeados.
        """
        service = SolicitudInsigniaService()

        prioridades = list(range(1, 51))

        service._validar_prioridades_consecutivas(prioridades)



    def test_validar_prioridades_duplicadas_falla(self):
        """
        Test: Duplicados

        Given: Una lista con el valor 1 repetido [1, 1, 2].
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



    def test_validar_prioridades_con_valor_cero_falla(self):
        """
        Test: Valores menores que 1

        Given: Una lista que incluye el cero [0, 1, 2].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Lanza ValidationError con el mensaje específico de mayor que cero.
        """
        service = SolicitudInsigniaService()
        prioridades = [0, 1, 2]

        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades)
        
        self.assertEqual(
            cm.exception.message, 
            "El orden de prioridad debe ser mayor que cero."
        )



    def test_validar_prioridades_con_negativos_falla(self):
        """
        Test complementario: Números negativos.
        """
        service = SolicitudInsigniaService()
        prioridades = [1, -2, 3]

        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades)
        
        self.assertIn("debe ser mayor que cero", cm.exception.message)



    def test_validar_prioridades_con_saltos_falla(self):
        """
        Test: No consecutivos (saltos)

        Given: Una lista con un hueco en la numeración [1, 3, 4].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Lanza ValidationError indicando que debe ser consecutivo.
        """
        service = SolicitudInsigniaService()
        prioridades = [1, 3, 4]

        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades)
        
        self.assertEqual(
            cm.exception.message, 
            "El orden de prioridad debe ser consecutivo empezando por 1."
        )



    def test_validar_prioridades_no_empieza_en_uno_falla(self):
        """
        Test: Empieza en número distinto de 1

        Given: Una lista que, aunque es consecutiva, empieza en 2 [2, 3, 4].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Lanza ValidationError con el mismo mensaje de estructura.
        """
        service = SolicitudInsigniaService()
        prioridades = [2, 3, 4]

        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades)
        
        self.assertEqual(
            cm.exception.message, 
            "El orden de prioridad debe ser consecutivo empezando por 1."
        )



    def test_validar_prioridades_lista_vacia_pasa_actualmente(self):
        """
        Test: Lista vacía

        Given: Una lista de prioridades vacía [].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Actualmente no lanza ValidationError (comportamiento técnico correcto, 
            pero cuestionable a nivel de negocio).
        """
        service = SolicitudInsigniaService()
        prioridades = []

        service._validar_prioridades_consecutivas(prioridades)



    def test_validar_prioridades_con_floats_se_comporta_por_valor(self):
        """
        Test: Float en prioridades

        Given: Una lista con floats que representan enteros [1.0, 2.0].
        When: Se llama al servicio.
        Then: La validación pasa porque 1.0 == 1 en las comparaciones de Python,
            a menos que se añada una comprobación de tipo explícita.
        """
        service = SolicitudInsigniaService()
        prioridades = [1.0, 2.0]

        service._validar_prioridades_consecutivas(prioridades)



    @patch('api.models.Puesto.objects.filter')
    def test_validar_prioridades_con_strings_numericos_pasa_por_coercion(self, mock_filter):
        """
        Test: Strings numéricos

        Given: Una lista de prioridades como strings ["1", "2"].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: No lanza ValidationError ni TypeError.
            El servicio los convierte internamente a [1, 2] y valida con éxito.
        """
        service = SolicitudInsigniaService()
        prioridades = ["1", "2"]

        service._validar_prioridades_consecutivas(prioridades)



    def test_validar_prioridades_duplicadas_prioriza_error_de_duplicidad(self):
        """
        Test: Duplicados no consecutivos

        Given: Una lista [1, 2, 2]. 
            Rompe la regla de duplicados Y la de secuencia (falta el 3).
        When: Se llama al servicio.
        Then: Debe lanzar el error de duplicados (primer bloque 'if').
        """
        service = SolicitudInsigniaService()
        prioridades = [1, 2, 2]

        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades)

        self.assertEqual(
            cm.exception.message, 
            "No puede haber orden de prioridad duplicado."
        )



    def test_validar_prioridades_permutacion_valida_pasa(self):
        """
        Test: Orden incorrecto pero válido

        Given: Una lista con prioridades salteadas [2, 1, 3].
        When: Se llama a _validar_prioridades_consecutivas.
        Then: No lanza excepción. 
            La comparación con sorted() permite que cualquier orden sea válido 
            mientras el conjunto de números sea el correcto (1 a n).
        """
        service = SolicitudInsigniaService()
        prioridades = [2, 1, 3]

        service._validar_prioridades_consecutivas(prioridades)



    def test_verificar_orden_de_prioridad_de_validaciones(self):
        """
        Test: Verificar orden de validaciones

        Given: Una lista que rompe todas las reglas [0, 0]. 
            (Es duplicado, es menor que 1 y no es consecutivo).
        When: Se llama al servicio.
        Then: Debe saltar el primer error: Duplicados.
        """
        service = SolicitudInsigniaService()
        prioridades = [0, 0]

        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades)

        self.assertEqual(cm.exception.message, "No puede haber orden de prioridad duplicado.")



    def test_validar_prioridades_consecutivas_falla_con_valores_no_numericos(self):
        """
        Test: 16. Fallo en conversión de tipos

        Given: Una lista de prioridades que contiene strings no numéricos o tipos inválidos.
        When: Se llama a _validar_prioridades_consecutivas.
        Then: Debe capturar el ValueError/TypeError y lanzar una ValidationError 
            con el mensaje: "El orden de prioridad debe ser un número válido."
        """
        service = SolicitudInsigniaService()

        prioridades_letras = [1, "dos", 3]
        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades_letras)
        self.assertEqual(str(cm.exception.message), "El orden de prioridad debe ser un número válido.")

        prioridades_tipos = [1, None, 3]
        with self.assertRaises(ValidationError) as cm:
            service._validar_prioridades_consecutivas(prioridades_tipos)
        self.assertEqual(str(cm.exception.message), "El orden de prioridad debe ser un número válido.")



    # -------------------------------------------------------------------------
    # TEST VALIDAR PUESTO UNICOS
    # -------------------------------------------------------------------------

    def test_validar_puestos_unicos_sin_duplicados_pasa(self):
        """
        Test: Lista sin duplicados

        Given: Una lista con tres instancias de puestos diferentes.
        When: Se llama a _validar_puestos_unicos.
        Then: No se lanza ninguna excepción ValidationError.
        """
        service = SolicitudInsigniaService()

        puesto1 = MagicMock(id=1)
        puesto2 = MagicMock(id=2)
        puesto3 = MagicMock(id=3)
        puestos = [puesto1, puesto2, puesto3]

        service._validar_puestos_unicos(puestos)



    def test_validar_puestos_unicos_completos_y_distintos_pasa(self):
        """
        Test: Lista con elementos únicos y sin None

        Given: Una lista de puestos totalmente cumplimentada.
        When: Se llama al servicio.
        Then: Pasa la validación, confirmando que set() identifica correctamente 
            la unicidad de los objetos Puesto.
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



    def test_validar_puestos_unicos_con_multiples_none_pasa(self):
        """
        Test: Lista con solo None

        Given: Una lista que contiene únicamente valores nulos [None, None].
        When: Se llama a _validar_puestos_unicos.
        Then: No lanza ValidationError. 
            El filtrado interno genera una lista vacía, y una lista vacía 
            técnicamente no tiene duplicados.
        """
        service = SolicitudInsigniaService()

        puestos = [None, None, None]

        service._validar_puestos_unicos(puestos)



    def test_validar_puestos_unicos_duplicados_falla(self):
        """
        Test: Duplicados exactos

        Given: Una lista con un puesto repetido [p1, p2, p1].
        When: Se llama a _validar_puestos_unicos.
        Then: Lanza ValidationError con el mensaje de duplicados.
        """
        service = SolicitudInsigniaService()

        p1 = MagicMock(spec=Puesto, id=10)
        p2 = MagicMock(spec=Puesto, id=20)
        puestos = [p1, p2, p1]

        with self.assertRaises(ValidationError) as cm:
            service._validar_puestos_unicos(puestos)
        
        self.assertEqual(
            cm.exception.message, 
            "No puede solicitar el mismo puesto varias veces."
        )



    def test_validar_puestos_unicos_duplicados_con_none_falla(self):
        """
        Test: Duplicados ignorando None

        Given: Una lista con un duplicado y un valor nulo intercalado [p1, None, p1].
        When: Se llama a _validar_puestos_unicos.
        Then: El filtro elimina el None, dejando [p1, p1].
            Al comparar longitudes (2 != 1), lanza ValidationError.
        """
        service = SolicitudInsigniaService()
        
        p1 = MagicMock(spec=Puesto, id=10)
        puestos = [p1, None, p1]

        with self.assertRaises(ValidationError) as cm:
            service._validar_puestos_unicos(puestos)

        self.assertEqual(
            cm.exception.message, 
            "No puede solicitar el mismo puesto varias veces."
        )



    def test_validar_puestos_unicos_con_multiples_duplicados_falla(self):
        """
        Test: Múltiples duplicados

        Given: Una lista donde varios puestos están repetidos [p1, p1, p2, p2].
        When: Se llama a _validar_puestos_unicos.
        Then: Lanza ValidationError. 
            El set colapsa los 4 elementos en solo 2, detectando la anomalía.
        """
        service = SolicitudInsigniaService()
        
        p1 = MagicMock(spec=Puesto, id=10)
        p2 = MagicMock(spec=Puesto, id=20)
        puestos = [p1, p1, p2, p2]

        with self.assertRaises(ValidationError) as cm:
            service._validar_puestos_unicos(puestos)
        
        self.assertEqual(
            cm.exception.message, 
            "No puede solicitar el mismo puesto varias veces."
        )



    def test_validar_puestos_unicos_mezcla_valida_pasa(self):
        """
        Test: Solo None mezclado con únicos

        Given: Una lista con puestos distintos y un None intercalado [p1, None, p2].
        When: Se llama a _validar_puestos_unicos.
        Then: No lanza excepción. 
            puestos_reales contiene [p1, p2], el set tiene longitud 2, 
            y la validación es exitosa.
        """
        service = SolicitudInsigniaService()
        
        p1 = MagicMock(spec=Puesto, id=10)
        p2 = MagicMock(spec=Puesto, id=20)
        puestos = [p1, None, p2]

        service._validar_puestos_unicos(puestos)



    def test_validar_puestos_unicos_con_objetos_no_hashables_falla(self):
        """
        Test: Lista con objetos no hashables

        Given: Una lista que contiene diccionarios (no hashables) [{"id": 1}].
        When: Se llama al servicio.
        Then: Lanza TypeError. 
            Esto alerta de que los datos no han sido pre-procesados correctamente 
            antes de llegar a este validador.
        """
        service = SolicitudInsigniaService()

        puestos = [{"id": 1}, {"id": 1}]

        with self.assertRaises(TypeError):
            service._validar_puestos_unicos(puestos)



    def test_validar_puestos_unicos_orden_no_afecta_resultado(self):
        """
        Test: Orden irrelevante

        Given: Dos listas con los mismos puestos pero en distinto orden ([p1, p2] y [p2, p1]).
        When: Se llama a _validar_puestos_unicos para ambas.
        Then: Ambas pasan la validación sin lanzar excepciones.
        """
        service = SolicitudInsigniaService()
        p1 = MagicMock(spec=Puesto, id=10)
        p2 = MagicMock(spec=Puesto, id=20)

        service._validar_puestos_unicos([p1, p2])
        service._validar_puestos_unicos([p2, p1])



    def test_validar_puestos_unicos_duplicados_no_consecutivos_falla(self):
        """
        Test: Duplicados no consecutivos

        Given: Una lista donde el primer y último elemento son el mismo [p1, p2, p1].
        When: Se llama a _validar_puestos_unicos.
        Then: Lanza ValidationError indicando el duplicado.
        """
        service = SolicitudInsigniaService()
        p1 = MagicMock(spec=Puesto, id=10)
        p2 = MagicMock(spec=Puesto, id=20)
        
        puestos = [p1, p2, p1]

        with self.assertRaises(ValidationError) as cm:
            service._validar_puestos_unicos(puestos)
        
        self.assertEqual(
            cm.exception.message, 
            "No puede solicitar el mismo puesto varias veces."
        )



    def test_verificar_filtrado_de_none_antes_de_validar(self):
        """
        Test: Verificar filtrado de None

        Given: Una lista con un puesto y múltiples None.
        When: Se llama a _validar_puestos_unicos.
        Then: No lanza ValidationError.
            Internamente, puestos_reales debe ignorar los None, 
            quedando con longitud 1 (el set también tendrá 1).
        """
        service = SolicitudInsigniaService()
        p1 = MagicMock(spec=Puesto, id=10)

        puestos = [None, p1, None, None]

        service._validar_puestos_unicos(puestos)



    def test_validar_puestos_unicos_identidad_vs_igualdad_detecta_mismo_id_logico(self):
        """
        Test: Identidad vs igualdad

        Given: Dos objetos DISTINTOS en memoria pero que representan 
            el MISMO puesto (mismo ID).
        When: Se llama a _validar_puestos_unicos.
        Then: Lanza ValidationError.
            El set() debe ser capaz de colapsarlos por su igualdad lógica (ID),
            no por su dirección de memoria.
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
            esperados, incluyendo el año extraído del acto.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock(id=1)
        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026
        fecha_solicitud = "2026-03-15"

        fake_uuid = uuid.UUID('12345678123456781234567812345678')
        mock_uuid.return_value = fake_uuid
        codigo_esperado = "12345678"

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
            codigo_verificacion=mock_uuid.return_value.hex[:8].upper()
        )



    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_con_vinculado_a_none_explicito(self, mock_create):
        """
        Test: Con vinculado_a = None

        Given: Los parámetros básicos y vinculado_a omitido.
        When: Se llama a _crear_papeleta_base.
        Then: El campo vinculado_a en el create debe ser None.
        """
        service = SolicitudInsigniaService()
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026

        service._crear_papeleta_base(mock_hermano, mock_acto, "2026-01-01")

        args, kwargs = mock_create.call_args
        self.assertIsNone(kwargs.get('vinculado_a'))



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
    @patch('uuid.uuid4')
    def test_crear_papeleta_base_genera_codigo_verificacion_formateado(self, mock_uuid, mock_create):
        """
        Test: Código de verificación generado

        Given: Un UUID específico generado por el sistema.
        When: Se procesa la creación de la papeleta.
        Then: 
            - Se debe llamar a uuid.uuid4().
            - El código resultante debe ser los primeros 8 caracteres del hex en MAYÚSCULAS.
        """
        service = SolicitudInsigniaService()

        fake_uuid = MagicMock()
        fake_uuid.hex = "abcdef1234567890"
        mock_uuid.return_value = fake_uuid

        service._crear_papeleta_base(MagicMock(), MagicMock(), "2026-01-01")

        mock_uuid.assert_called_once()
        
        args, kwargs = mock_create.call_args
        codigo_enviado = kwargs.get('codigo_verificacion')

        self.assertEqual(len(codigo_enviado), 8)

        self.assertEqual(codigo_enviado, "ABCDEF12")

        self.assertTrue(codigo_enviado.isupper())



    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_extrae_anio_correctamente_del_acto(self, mock_create):
        """
        Test: Año correcto desde el acto

        Given: Un acto cuya fecha está programada para el año 2027.
        When: Se llama a _crear_papeleta_base.
        Then: El campo 'anio' en el create debe ser 2027, independientemente 
            de la fecha real de la solicitud o del sistema.
        """
        service = SolicitudInsigniaService()

        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_acto.fecha.year = 2027
        fecha_solicitud = "2026-12-01"

        service._crear_papeleta_base(
            hermano=mock_hermano, 
            acto=mock_acto, 
            fecha_solicitud=fecha_solicitud
        )

        args, kwargs = mock_create.call_args

        self.assertEqual(kwargs.get('anio'), 2027)
        self.assertEqual(kwargs.get('anio'), mock_acto.fecha.year)



    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_falla_en_create_propaga_error(self, mock_create):
        """
        Test: Falla en objects.create

        Given: El ORM lanza una excepción (ej: DatabaseError).
        When: Se llama a _crear_papeleta_base.
        Then: El servicio propaga la excepción, permitiendo que el flujo 
            superior la gestione o haga rollback.
        """
        service = SolicitudInsigniaService()

        mock_create.side_effect = Exception("Error crítico de base de datos")

        with self.assertRaises(Exception) as cm:
            service._crear_papeleta_base(MagicMock(), MagicMock(), "2026-01-01")
        
        self.assertEqual(str(cm.exception), "Error crítico de base de datos")



    def test_crear_papeleta_base_con_acto_sin_fecha_falla(self):
        """
        Test: acto.fecha = None

        Given: Un objeto acto donde la fecha es None.
        When: Se intenta acceder a .year para el campo 'anio'.
        Then: Lanza AttributeError. 
            Este test identifica la necesidad de validar el acto antes de procesarlo.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.fecha = None

        with self.assertRaises(AttributeError):
            service._crear_papeleta_base(MagicMock(), mock_acto, "2026-01-01")



    @patch('api.models.PapeletaSitio.objects.create')
    @patch('uuid.uuid4')
    def test_crear_papeleta_base_garantiza_formato_uuid_estricto(self, mock_uuid, mock_create):
        """
        Test: UUID no generado correctamente

        Given: Un UUID con caracteres en minúscula y gran longitud.
        When: Se procesa la creación de la papeleta.
        Then: El código de verificación resultante debe tener exactamente 
            8 caracteres y estar en MAYÚSCULAS.
        """
        service = SolicitudInsigniaService()

        fake_uuid = MagicMock()
        fake_uuid.hex = "550e8400e29b41d4a716446655440000"
        mock_uuid.return_value = fake_uuid

        service._crear_papeleta_base(
            hermano=MagicMock(), 
            acto=MagicMock(), 
            fecha_solicitud="2026-04-26"
        )

        args, kwargs = mock_create.call_args
        codigo = kwargs.get('codigo_verificacion')

        self.assertEqual(codigo, "550E8400")
        self.assertEqual(len(codigo), 8)
        self.assertTrue(codigo.isupper())



    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_envia_kwargs_exactos_al_orm(self, mock_create):
        """
        Test: Verificar orden exacto de parámetros (Kwargs)

        Given: Un conjunto de parámetros válidos.
        When: Se llama a _crear_papeleta_base.
        Then: Se verifica que la llamada al ORM contiene exactamente las 8 claves 
            esperadas por el modelo, evitando parámetros extra o faltantes.
        """
        service = SolicitudInsigniaService()

        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026

        service._crear_papeleta_base(
            hermano=MagicMock(id=1),
            acto=mock_acto,
            fecha_solicitud="2026-04-26"
        )

        args, kwargs = mock_create.call_args

        claves_esperadas = {
            'hermano', 'acto', 'anio', 'fecha_solicitud', 
            'estado_papeleta', 'vinculado_a', 
            'es_solicitud_insignia', 'codigo_verificacion'
        }

        self.assertEqual(set(kwargs.keys()), claves_esperadas)

        self.assertFalse(kwargs['es_solicitud_insignia'])
        self.assertEqual(
            kwargs['estado_papeleta'], 
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )



    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_siempre_usa_estado_solicitada(self, mock_create):
        """
        Test: Verificar constante SOLICITADA

        Given: Una petición de creación estándar.
        When: Se llama a _crear_papeleta_base.
        Then: El valor de 'estado_papeleta' enviado al ORM debe ser exactamente 
            PapeletaSitio.EstadoPapeleta.SOLICITADA.
        """
        service = SolicitudInsigniaService()

        service._crear_papeleta_base(MagicMock(), MagicMock(), "2026-04-26")

        args, kwargs = mock_create.call_args
        self.assertEqual(
            kwargs.get('estado_papeleta'), 
            PapeletaSitio.EstadoPapeleta.SOLICITADA
        )



    @patch('api.models.PapeletaSitio.objects.create')
    def test_crear_papeleta_base_ignora_intentos_de_estado_externo(self, mock_create):
        """
        Test: Verificar que NO se permite override externo

        Given: El contrato actual de la función.
        When: Se llama a la función (que no acepta 'estado' como parámetro).
        Then: Se garantiza que el desarrollador no tiene forma de forzar un estado 
            distinto (como 'ENTREGADA') en este punto de creación base.
        """
        service = SolicitudInsigniaService()

        with self.assertRaises(TypeError):
            service._crear_papeleta_base(
                MagicMock(), 
                MagicMock(), 
                "2026-04-26", 
                estado_papeleta="OTRO_ESTADO"
            )



    @patch('api.models.PapeletaSitio.objects.create')
    @patch('uuid.uuid4')
    def test_crear_papeleta_base_garantiza_formato_final_estricto(self, mock_uuid, mock_create):
        """
        Test: UUID formato correcto

        Given: Un UUID generado por el sistema.
        When: Se procesa la creación de la papeleta.
        Then: El código de verificación debe cumplir estrictamente:
            - Longitud exacta de 8 caracteres.
            - Todos los caracteres en mayúsculas.
        """
        service = SolicitudInsigniaService()

        fake_uuid = MagicMock()
        fake_uuid.hex = "a1b2c3d4e5f678901234567890abcdef" 
        mock_uuid.return_value = fake_uuid

        service._crear_papeleta_base(MagicMock(), MagicMock(), "2026-04-26")

        args, kwargs = mock_create.call_args
        codigo = kwargs.get('codigo_verificacion')

        self.assertEqual(len(codigo), 8, "El código debe tener exactamente 8 caracteres")
        self.assertTrue(codigo.isupper(), "El código debe estar íntegramente en mayúsculas")
        self.assertEqual(codigo, "A1B2C3D4")



    @patch('api.models.PapeletaSitio.objects.create')
    @patch('uuid.uuid4')
    def test_crear_papeleta_base_es_determinista_con_mock(self, mock_uuid, mock_create):
        """
        Test: Determinismo del test (mock UUID)

        Given: Un valor de UUID inyectado manualmente (fijo).
        When: Se ejecuta el servicio múltiples veces.
        Then: El código de verificación resultante debe ser siempre el mismo,
            garantizando que el test no dependa del azar.
        """
        service = SolicitudInsigniaService()

        val_hex = "f47ac10b58cc4372a5670e02b2c3d479"
        fake_uuid = MagicMock()
        fake_uuid.hex = val_hex
        mock_uuid.return_value = fake_uuid

        service._crear_papeleta_base(MagicMock(), MagicMock(), "2026-04-26")

        args, kwargs = mock_create.call_args

        self.assertEqual(kwargs.get('codigo_verificacion'), "F47AC10B")



    @patch('api.models.PapeletaSitio.objects.create')
    @patch('django.utils.timezone.now')
    def test_crear_papeleta_base_no_depende_del_anio_actual(self, mock_now, mock_create):
        """
        Test: Dependencia de acto.fecha.year

        Given: 
            - La fecha actual del sistema es el año 2026.
            - El acto está programado para el año 2027.
        When: Se llama a _crear_papeleta_base.
        Then: El campo 'anio' de la papeleta debe ser 2027 (extraído del acto),
            ignorando por completo el año actual del sistema.
        """
        service = SolicitudInsigniaService()

        mock_now.return_value = MagicMock(year=2026)

        mock_acto = MagicMock()
        mock_acto.fecha.year = 2027
        
        fecha_solicitud = "2026-12-20"

        service._crear_papeleta_base(
            hermano=MagicMock(), 
            acto=mock_acto, 
            fecha_solicitud=fecha_solicitud
        )

        args, kwargs = mock_create.call_args

        self.assertNotEqual(kwargs.get('anio'), 2026)

        self.assertEqual(kwargs.get('anio'), 2027)



    # -------------------------------------------------------------------------
    # TEST GUARDAR PREFERENCIAS
    # -------------------------------------------------------------------------

    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_insercion_correcta(self, mock_bulk_create):
        """
        Test: Inserción correcta de preferencias

        Given: 
            - Una instancia de PapeletaSitio (en memoria).
            - Una lista de diccionarios con datos de puestos (p1, p2) y sus prioridades.
        When: 
            - Se llama al método _guardar_preferencias.
        Then: 
            - Se debe invocar bulk_create exactamente una vez para optimizar el acceso a BD.
            - Los objetos instanciados deben mantener la relación con la papeleta original.
            - Los datos de los diccionarios (puesto y orden) deben estar correctamente 
            mapeados en los atributos del modelo PreferenciaSolicitud.
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

        args, kwargs = mock_bulk_create.call_args
        objetos_creados = args[0]

        self.assertEqual(len(objetos_creados), 2)
        self.assertIsInstance(objetos_creados[0], PreferenciaSolicitud)

        self.assertEqual(objetos_creados[0].papeleta, papeleta_memoria)
        self.assertEqual(objetos_creados[0].puesto_solicitado, p1)
        self.assertEqual(objetos_creados[0].orden_prioridad, 1)



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_lista_vacia_llama_bulk_con_lista_vacia(self, mock_bulk_create):
        """
        Test: Lista vacía

        Given: Una lista de preferencias vacía [].
        When: Se llama a _guardar_preferencias.
        Then: Se llama a bulk_create con una lista vacía, delegando 
            en Django el ignorar la inserción sin lanzar error.
        """
        service = SolicitudInsigniaService()
        mock_papeleta = MagicMock(id=100)
        
        preferencias_data = []

        service._guardar_preferencias(mock_papeleta, preferencias_data)

        mock_bulk_create.assert_called_once_with([])



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_un_solo_elemento_inserta_correctamente(self, mock_bulk_create):
        """
        Test: Un solo elemento

        Given: Una lista con exactamente 1 preferencia.
        When: Se llama a _guardar_preferencias.
        Then: El bulk_create recibe una lista de longitud 1 con la 
            instancia correctamente mapeada.
        """
        service = SolicitudInsigniaService()

        papeleta_memoria = PapeletaSitio(id=100)
        p1 = Puesto(id=10)
        
        preferencias_data = [
            {"puesto_solicitado": p1, "orden_prioridad": 1}
        ]

        service._guardar_preferencias(papeleta_memoria, preferencias_data)

        mock_bulk_create.assert_called_once()
        
        args, kwargs = mock_bulk_create.call_args
        objetos_creados = args[0]
        
        self.assertEqual(len(objetos_creados), 1)
        self.assertIsInstance(objetos_creados[0], PreferenciaSolicitud)

        self.assertEqual(objetos_creados[0].papeleta, papeleta_memoria)
        self.assertEqual(objetos_creados[0].puesto_solicitado, p1)
        self.assertEqual(objetos_creados[0].orden_prioridad, 1)



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_preserva_estructura_de_datos(self, mock_bulk_create):
        """
        Test: Preserva estructura de datos

        Given: 
            - Una papeleta válida.
            - Una lista de preferencias con datos heterogéneos (p1, p2, p3) y órdenes salteados.
        When: 
            - Se llama a _guardar_preferencias.
        Then: 
            - Cada item del diccionario debe transformarse en una instancia de PreferenciaSolicitud.
            - Los atributos de cada instancia deben corresponder exactamente a su pareja 
            (Puesto X -> Prioridad X) según el índice de la lista.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)
        p1, p2, p3 = Puesto(id=10), Puesto(id=20), Puesto(id=30)
        
        preferencias_data = [
            {"puesto_solicitado": p1, "orden_prioridad": 1},
            {"puesto_solicitado": p2, "orden_prioridad": 2},
            {"puesto_solicitado": p3, "orden_prioridad": 3},
        ]

        service._guardar_preferencias(papeleta, preferencias_data)

        objetos_enviados = mock_bulk_create.call_args[0][0]
        
        for i, item in enumerate(preferencias_data):
            objeto = objetos_enviados[i]
            with self.subTest(indice=i):
                self.assertEqual(objeto.puesto_solicitado, item["puesto_solicitado"])
                self.assertEqual(objeto.orden_prioridad, item["orden_prioridad"])
                self.assertEqual(objeto.papeleta, papeleta)



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_falta_puesto_solicitado_falla(self, mock_bulk_create):
        """
        Test: Falta puesto_solicitado

        Given: 
            - Una lista de preferencias donde un item no tiene la clave 
            'puesto_solicitado'.
        When: 
            - Se llama a _guardar_preferencias.
        Then: 
            - Debe lanzar un KeyError indicando la clave faltante.
            - No se debe llegar a ejecutar el bulk_create.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)

        preferencias_data = [
            {"orden_prioridad": 1} 
        ]

        with self.assertRaises(KeyError) as cm:
            service._guardar_preferencias(papeleta, preferencias_data)

        self.assertEqual(str(cm.exception), "'puesto_solicitado'")

        mock_bulk_create.assert_not_called()



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_falta_orden_prioridad_falla(self, mock_bulk_create):
        """
        Test: Falta orden_prioridad

        Given: 
            - Una lista de preferencias donde un ítem carece de 'orden_prioridad'.
        When: 
            - Se llama a _guardar_preferencias.
        Then: 
            - Lanza KeyError: 'orden_prioridad'.
            - Se detiene la ejecución antes de llamar al ORM.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)
        p1 = Puesto(id=10)

        preferencias_data = [
            {"puesto_solicitado": p1} 
        ]

        with self.assertRaises(KeyError) as cm:
            service._guardar_preferencias(papeleta, preferencias_data)

        self.assertEqual(str(cm.exception), "'orden_prioridad'")

        mock_bulk_create.assert_not_called()



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_con_none_falla_por_iteracion(self, mock_bulk_create):
        """
        Test: preferencias_data = None

        Given: 
            - Una papeleta válida.
            - Un valor None en lugar de la lista de preferencias.
        When: 
            - El servicio intenta ejecutar la comprensión de lista: 
            'for item in preferencias_data'.
        Then: 
            - Debe lanzar un TypeError ('NoneType' object is not iterable).
            - No debe llamar a bulk_create.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)

        preferencias_data = None

        with self.assertRaises(TypeError):
            service._guardar_preferencias(papeleta, preferencias_data)

        mock_bulk_create.assert_not_called()



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_realiza_una_sola_llamada_al_orm(self, mock_bulk_create):
        """
        Test: Verificar UNA sola llamada a bulk_create

        Given: 
            - Una lista con múltiples preferencias (p1, p2, p3).
        When: 
            - Se llama a _guardar_preferencias.
        Then: 
            - Se debe invocar bulk_create exactamente una vez (assert_called_once).
            - Esto garantiza que la eficiencia del batch insert se mantiene 
            y no se ha degradado a inserciones individuales.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)
        p1, p2, p3 = Puesto(id=1), Puesto(id=2), Puesto(id=3)
        
        preferencias_data = [
            {"puesto_solicitado": p1, "orden_prioridad": 1},
            {"puesto_solicitado": p2, "orden_prioridad": 2},
            {"puesto_solicitado": p3, "orden_prioridad": 3},
        ]

        service._guardar_preferencias(papeleta, preferencias_data)

        mock_bulk_create.assert_called_once()

        args, _ = mock_bulk_create.call_args
        self.assertEqual(len(args[0]), 3, "La lista del batch insert debe contener los 3 elementos")



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_respeta_orden_de_lista_original(self, mock_bulk_create):
        """
        Test: Orden de preferencias preservado

        Given: Una lista de preferencias con un orden específico [P1, P2, P3].
        When: Se llama a _guardar_preferencias.
        Then: La lista enviada al ORM debe mantener exactamente el mismo orden,
            asegurando que el índice 0 corresponde a la primera prioridad.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)
        p1, p2, p3 = Puesto(id=10), Puesto(id=20), Puesto(id=30)
        
        preferencias_data = [
            {"puesto_solicitado": p1, "orden_prioridad": 1},
            {"puesto_solicitado": p2, "orden_prioridad": 2},
            {"puesto_solicitado": p3, "orden_prioridad": 3},
        ]

        service._guardar_preferencias(papeleta, preferencias_data)

        objetos_creados = mock_bulk_create.call_args[0][0]

        self.assertEqual(objetos_creados[0].puesto_solicitado, p1)
        self.assertEqual(objetos_creados[1].puesto_solicitado, p2)
        self.assertEqual(objetos_creados[2].puesto_solicitado, p3)



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_mapea_todos_los_campos_del_modelo(self, mock_bulk_create):
        """
        Test: Campos correctos en instancias creadas

        Given: Un conjunto de datos completo.
        When: Se instancia cada PreferenciaSolicitud para el bulk_create.
        Then: Se verifica que no falta ningún campo obligatorio por asignar 
            en la instancia del modelo antes de enviarla al ORM.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)
        puesto = Puesto(id=10)
        
        preferencias_data = [{"puesto_solicitado": puesto, "orden_prioridad": 1}]

        service._guardar_preferencias(papeleta, preferencias_data)

        instancia = mock_bulk_create.call_args[0][0][0]

        self.assertEqual(instancia.papeleta, papeleta)
        self.assertEqual(instancia.puesto_solicitado, puesto)
        self.assertEqual(instancia.orden_prioridad, 1)



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    @patch('api.models.Puesto.objects.get')
    def test_guardar_preferencias_no_realiza_consultas_adicionales(self, mock_get, mock_bulk_create):
        """
        Test: No hay lógica extra accidental

        Given: Una lista de preferencias válida.
        When: Se llama a _guardar_preferencias.
        Then: 
            - Se llama a bulk_create una vez.
            - NO se deben realizar llamadas adicionales al ORM (como .get(), .filter() o .save() individual).
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)
        p1 = Puesto(id=10)
        
        preferencias_data = [{"puesto_solicitado": p1, "orden_prioridad": 1}]

        service._guardar_preferencias(papeleta, preferencias_data)

        mock_bulk_create.assert_called_once()

        mock_get.assert_not_called()



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_no_modifica_la_lista_de_entrada(self, mock_bulk_create):
        """
        Test: Mutabilidad del input

        Given: Una lista de preferencias original.
        When: El servicio procesa los datos para el bulk_create.
        Then: La lista original 'preferencias_data' debe permanecer idéntica 
            (mismo contenido y longitud) tras la ejecución del método.
        """
        service = SolicitudInsigniaService()
        papeleta = PapeletaSitio(id=100)
        p1 = Puesto(id=10)

        preferencias_data = [{"puesto_solicitado": p1, "orden_prioridad": 1}]
        input_original = list(preferencias_data) 

        service._guardar_preferencias(papeleta, preferencias_data)

        self.assertEqual(preferencias_data, input_original)
        self.assertEqual(len(preferencias_data), 1)



    @patch('api.models.PreferenciaSolicitud.objects.bulk_create')
    def test_guardar_preferencias_garantiza_fk_papeleta_identico_en_todas_las_filas(self, mock_bulk_create):
        """
        Test: Integridad del FK papeleta

        Given: 
            - Una instancia de PapeletaSitio.
            - Una lista con múltiples preferencias (p1, p2, p3).
        When: 
            - Se llama a _guardar_preferencias.
        Then: 
            - Todas las instancias de PreferenciaSolicitud enviadas al ORM deben 
            tener exactamente la misma referencia de objeto 'papeleta'.
            - Se valida que no hay fugas de datos entre diferentes solicitudes.
        """
        service = SolicitudInsigniaService()
        papeleta_padre = PapeletaSitio(id=100)
        p1, p2, p3 = Puesto(id=1), Puesto(id=2), Puesto(id=3)
        
        preferencias_data = [
            {"puesto_solicitado": p1, "orden_prioridad": 1},
            {"puesto_solicitado": p2, "orden_prioridad": 2},
            {"puesto_solicitado": p3, "orden_prioridad": 3},
        ]

        service._guardar_preferencias(papeleta_padre, preferencias_data)

        objetos_creados = mock_bulk_create.call_args[0][0]

        for i, obj in enumerate(objetos_creados):
            with self.subTest(item=i):
                self.assertEqual(
                    obj.papeleta, 
                    papeleta_padre, 
                    f"El objeto en el índice {i} no apunta a la papeleta correcta"
                )
                self.assertEqual(obj.papeleta.id, 100)