import math
import unittest
from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService

class TestComunicadoRagServiceSimilitud(unittest.TestCase):

    def setUp(self):
        self.servicio = ComunicadoRAGService()



    def test_calcula_correctamente_similitud_coseno(self):
        """
        Test: Calcula correctamente la similitud coseno (caso normal)
        
        Given: Dos vectores numéricos válidos (ej. [3.0, 4.0] y [4.0, 3.0]).
        When: Se invoca la función para calcular su similitud.
        Then: Se verifica que el resultado devuelto corresponde al cálculo matemático correcto de la similitud coseno (0.96).
        """
        vec1 = [3.0, 4.0]
        vec2 = [4.0, 3.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertAlmostEqual(resultado, 0.96, places=5)



    def test_vectores_ortogonales_similitud_cero(self):
        """
        Test: Vectores ortogonales → similitud = 0
        
        Given: Dos vectores perpendiculares entre sí (cuyo producto punto es cero).
        When: Se calcula la similitud coseno.
        Then: Se verifica que el resultado es exactamente 0.0.
        """
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_vectores_con_valores_negativos(self):
        """
        Test: Vectores con valores negativos
        
        Given: Vectores que contienen números negativos, incluyendo vectores en direcciones opuestas.
        When: Se calcula la similitud coseno.
        Then: Se verifica que el cálculo se realiza correctamente, devolviendo -1.0 para vectores opuestos.
        """
        vec1 = [2.0, 3.0]
        vec2 = [-2.0, -3.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertAlmostEqual(resultado, -1.0, places=5)



    def test_vectores_distinta_longitud(self):
        """
        Test: Vectores de distinta longitud (usa zip)
        
        Given: Dos vectores con diferente cantidad de elementos.
        When: Se invoca la función de cálculo de similitud.
        Then: La función debe procesarlos sin lanzar error (gracias a 'zip' que trunca al más corto) y devolver un cálculo matemático válido considerando las magnitudes completas.
        """
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        esperado = 5 / (math.sqrt(14) * math.sqrt(5))
        self.assertAlmostEqual(resultado, esperado, places=5)



    def test_elementos_no_numericos_en_vectores(self):
        """
        Test: Elementos no numéricos en vectores
        
        Given: Un vector que contiene un string en lugar de un float.
        When: Se ejecuta la multiplicación de elementos.
        Then: Se verifica que el sistema lanza una excepción (TypeError) al intentar realizar operaciones matemáticas con tipos inválidos.
        """
        vec1 = [1.0, "error"]
        vec2 = [1.0, 2.0]

        with self.assertRaises(TypeError):
            self.servicio._calcular_similitud_coseno(vec1, vec2)



    def test_vectores_identicos_similitud_uno(self):
        """
        Test: Vectores idénticos → similitud = 1
        
        Given: Dos vectores numéricos exactamente iguales.
        When: Se calcula la similitud coseno entre ellos.
        Then: Se verifica que el resultado es 1.0 (o extremadamente cercano debido a la precisión de coma flotante).
        """
        vec1 = [0.5, 0.8, 1.2, 3.14]
        vec2 = [0.5, 0.8, 1.2, 3.14]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertAlmostEqual(resultado, 1.0, places=5)



    def test_vectores_con_un_solo_elemento(self):
        """
        Test: Vectores con un solo elemento
        
        Given: Dos vectores de dimensión 1.
        When: Se calcula la similitud.
        Then: El resultado debe ser 1.0 si tienen el mismo signo, o -1.0 si tienen signos opuestos.
        """
        vec1 = [5.0]
        vec2 = [10.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 1.0)



    def test_retorna_cero_con_entradas_nulas_o_vacias(self):
        """
        Test para cubrir la línea: if not vec1 or not vec2: return 0.0
        
        Given: Un vector válido y otro que es None o una lista vacía.
        When: Se intenta calcular la similitud.
        Then: El servicio debe retornar 0.0 inmediatamente.
        """
        vec_valido = [1.0, 2.0, 3.0]

        self.assertEqual(self.servicio._calcular_similitud_coseno(None, vec_valido), 0.0)

        self.assertEqual(self.servicio._calcular_similitud_coseno(vec_valido, []), 0.0)



    def test_evita_division_por_cero_con_vectores_nulos(self):
        """
        Test para cubrir la línea: if not magnitude1 or not magnitude2: return 0.0
        
        Given: Vectores que solo contienen ceros (magnitud = 0).
        When: Se realiza el cálculo matemático.
        Then: Se detecta la magnitud nula y se retorna 0.0 para evitar el ZeroDivisionError.
        """
        vec_ceros = [0.0, 0.0, 0.0]
        vec_valido = [1.0, 2.0, 3.0]

        self.assertEqual(self.servicio._calcular_similitud_coseno(vec_ceros, vec_valido), 0.0)

        self.assertEqual(self.servicio._calcular_similitud_coseno(vec_ceros, vec_ceros), 0.0)