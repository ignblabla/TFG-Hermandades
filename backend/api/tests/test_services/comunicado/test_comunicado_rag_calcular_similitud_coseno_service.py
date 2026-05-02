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

        resultado_identicos = self.servicio._calcular_similitud_coseno([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        self.assertEqual(resultado_identicos, 1.0)



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



    def test_resultado_dentro_del_rango(self):
        """
        Test: Resultado dentro del rango [-1, 1]
        
        Given: Dos vectores con valores numéricos arbitrarios.
        When: Se calcula la similitud coseno.
        Then: Se verifica que la métrica devuelta siempre se mantenga matemáticamente dentro de los límites teóricos del coseno (entre -1.0 y 1.0).
        """
        vec1 = [4.5, -2.1, 0.0, 8.8]
        vec2 = [-1.1, 9.9, -3.3, 2.2]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertTrue(-1.0 <= resultado <= 1.0, f"El resultado {resultado} está fuera del rango válido [-1, 1]")



    def test_vec1_es_none(self):
        """
        Test: vec1 es None
        
        Given: El primer vector tiene un valor nulo (None).
        When: Se intenta calcular la similitud coseno.
        Then: La función debe capturar la condición y retornar 0.0 de forma segura.
        """
        vec1 = None
        vec2 = [0.1, 0.2, 0.3]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_vec2_es_none(self):
        """
        Test: vec2 es None
        
        Given: El segundo vector tiene un valor nulo (None).
        When: Se intenta calcular la similitud coseno.
        Then: La función debe capturar la condición y retornar 0.0 de forma segura.
        """
        vec1 = [0.1, 0.2, 0.3]
        vec2 = None

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_vec1_vacio(self):
        """
        Test: vec1 vacío
        
        Given: El primer vector es una lista vacía.
        When: Se calcula la similitud.
        Then: La función debe retornar 0.0 al no haber elementos para comparar.
        """
        vec1 = []
        vec2 = [1.0, 2.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_vec2_vacio(self):
        """
        Test: vec2 vacío
        
        Given: El segundo vector es una lista vacía.
        When: Se calcula la similitud.
        Then: Se verifica que el resultado es 0.0 por falta de datos.
        """
        vec1 = [1.0, 2.0]
        vec2 = []

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_magnitud_cero_en_vec1_todo_ceros(self):
        """
        Test: Magnitud cero en vec1 (vector todo ceros)
        
        Given: Un vector vec1 que solo contiene ceros, lo que resulta en una magnitud de cero.
        When: Se realiza el cálculo matemático.
        Then: La función debe evitar la división por cero y retornar 0.0.
        """
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_magnitud_cero_en_vec2(self):
        """
        Test: Magnitud cero en vec2
        
        Given: Un segundo vector vec2 que solo contiene ceros.
        When: Se intenta calcular la similitud.
        Then: Se verifica que el sistema detecta la magnitud nula y retorna 0.0 para evitar errores matemáticos.
        """
        vec1 = [0.5, 0.5]
        vec2 = [0.0, 0.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_ambos_vectores_con_todos_ceros(self):
        """
        Test: Ambos vectores con todos ceros
        
        Given: Dos vectores que solo contienen ceros ([0.0, 0.0]).
        When: Se calcula la similitud.
        Then: La función debe retornar 0.0 de forma segura al detectar magnitudes nulas, evitando la división por cero.
        """
        vec1 = [0.0, 0.0]
        vec2 = [0.0, 0.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertEqual(resultado, 0.0)



    def test_valores_muy_grandes_overflow(self):
        """
        Test: Valores muy grandes (posible overflow)
        
        Given: Vectores con valores extremadamente grandes que podrían causar desbordamiento en potencias.
        When: Se calcula la similitud.
        Then: El sistema debe manejar los números de punto flotante de Python y retornar 1.0 (ya que son idénticos).
        """
        grande = 1e150
        vec1 = [grande, grande]
        vec2 = [grande, grande]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertAlmostEqual(resultado, 1.0, places=5)



    def test_valores_muy_pequenos_precision(self):
        """
        Test: Valores muy pequeños (precisión flotante)
        
        Given: Vectores con valores ínfimos cercanos a cero.
        When: Se realiza el cálculo.
        Then: La precisión de Python debe permitir obtener la similitud correcta sin redondear prematuramente a cero si no es necesario.
        """
        pequeno = 1e-150
        vec1 = [pequeno, 0.0]
        vec2 = [pequeno, 0.0]

        resultado = self.servicio._calcular_similitud_coseno(vec1, vec2)

        self.assertAlmostEqual(resultado, 1.0, places=5)



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



    def test_no_modifica_vectores_entrada(self):
        """
        Test: Verificar que no modifica los vectores de entrada
        
        Given: Dos listas originales que representan los vectores.
        When: Se completa el cálculo de similitud.
        Then: Las listas originales deben permanecer idénticas, asegurando que la función no tiene efectos secundarios (inmutabilidad).
        """
        original_vec1 = [1.0, 2.0, 3.0]
        original_vec2 = [4.0, 5.0, 6.0]
        vec1_copy = list(original_vec1)
        vec2_copy = list(original_vec2)

        self.servicio._calcular_similitud_coseno(vec1_copy, vec2_copy)

        self.assertEqual(vec1_copy, original_vec1)
        self.assertEqual(vec2_copy, original_vec2)