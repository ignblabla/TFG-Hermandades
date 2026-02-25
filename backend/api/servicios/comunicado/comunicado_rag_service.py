import math
from google import genai
from google.genai import types
from django.conf import settings
from api.models import Comunicado

def calcular_similitud_coseno(vec1: list[float], vec2: list[float]) -> float:
    if not vec1 or not vec2: return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    if not magnitude1 or not magnitude2: return 0.0
    return dot_product / (magnitude1 * magnitude2)

class ComunicadoRAGService:
    def __init__(self):
        # Usamos el nuevo cliente
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
    def _recuperar_contexto_semantico(self, pregunta: str) -> str:
        try:
            # Nueva sintaxis para embeddings
            resultado = self.client.models.embed_content(
                model='gemini-embedding-001',
                contents=pregunta,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            # Accedemos a los valores del vector
            vector_pregunta = resultado.embeddings[0].values
        except Exception as e:
            print(f"Error vectorizando la pregunta: {e}")
            return ""

        comunicados = Comunicado.objects.filter(embedding__isnull=False).only('titulo', 'contenido', 'fecha_emision', 'embedding')
        
        resultados_puntuados = []
        for com in comunicados:
            similitud = calcular_similitud_coseno(vector_pregunta, com.embedding)
            resultados_puntuados.append((similitud, com))
            
        resultados_puntuados.sort(key=lambda x: x[0], reverse=True)
        top_comunicados = [item[1] for item in resultados_puntuados[:3]]

        contexto = ""
        for com in top_comunicados:
            contexto += f"--- COMUNICADO: {com.titulo} (Fecha: {com.fecha_emision.strftime('%d/%m/%Y')}) ---\n"
            contexto += f"{com.contenido}\n\n"
            
        return contexto

    def preguntar_a_comunicados(self, pregunta_usuario: str) -> str:
        contexto_textual = self._recuperar_contexto_semantico(pregunta_usuario)
        
        if not contexto_textual.strip():
            return "Lo siento, actualmente no hay comunicados vectorizados en la base de datos."

        prompt_estricto = f"""
        Eres el asistente virtual oficial de la Hermandad. 
        Tu tarea es responder a la pregunta del hermano utilizando ÚNICAMENTE la información proporcionada en el bloque "COMUNICADOS OFICIALES".
        Si la respuesta no se encuentra en el texto proporcionado, responde EXACTAMENTE: "Lo siento, no encuentro información sobre esa consulta en los comunicados recientes."

        COMUNICADOS OFICIALES:
        {contexto_textual}

        PREGUNTA DEL HERMANO:
        {pregunta_usuario}
        """

        try:
            # Nueva sintaxis para generar texto (usamos gemini-2.5-flash que es el más rápido y moderno)
            respuesta = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_estricto
            )
            return respuesta.text
        except Exception as e:
            raise Exception(f"Error al generar la respuesta con la IA: {str(e)}")