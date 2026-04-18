import os
import math
from google import genai
from google.genai import types
from django.conf import settings
from django.core.cache import cache
from api.models import Comunicado

class ComunicadoRAGService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.ruta_pdf_horarios = os.path.join(settings.BASE_DIR, 'media', 'documentos', 'horarios.pdf')



    def _recuperar_contexto_semantico(self, pregunta: str) -> str:
        try:
            resultado = self.client.models.embed_content(
                model='gemini-embedding-001',
                contents=pregunta,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            vector_pregunta = resultado.embeddings[0].values
        except Exception as e:
            print(f"Error vectorizando la pregunta: {e}")
            return ""

        comunicados = Comunicado.objects.filter(embedding__isnull=False).only('titulo', 'contenido', 'fecha_emision', 'embedding')
        
        resultados_puntuados = []
        for com in comunicados:
            similitud = self._calcular_similitud_coseno(vector_pregunta, com.embedding)
            resultados_puntuados.append((similitud, com))
            
        resultados_puntuados.sort(key=lambda x: x[0], reverse=True)
        top_comunicados = [item[1] for item in resultados_puntuados[:3]]

        contexto = ""
        for com in top_comunicados:
            contexto += f"--- COMUNICADO: {com.titulo} (Fecha: {com.fecha_emision.strftime('%d/%m/%Y')}) ---\n"
            contexto += f"{com.contenido}\n\n"
            
        return contexto



    def _calcular_similitud_coseno(self, vec1: list[float], vec2: list[float]) -> float:
        if not vec1 or not vec2: return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        if not magnitude1 or not magnitude2: return 0.0
        return dot_product / (magnitude1 * magnitude2)



    def _obtener_o_subir_pdf(self):
        """Sube el PDF a Gemini y cachea su referencia durante 24 horas."""
        file_name = cache.get('gemini_horarios_pdf_name')
        
        if file_name:
            try:
                archivo_en_nube = self.client.files.get(name=file_name)
                return archivo_en_nube
            except Exception:
                cache.delete('gemini_horarios_pdf_name')

        if os.path.exists(self.ruta_pdf_horarios):
            try:
                archivo_subido = self.client.files.upload(file=self.ruta_pdf_horarios)
                cache.set('gemini_horarios_pdf_name', archivo_subido.name, 86400)
                return archivo_subido
            except Exception as e:
                print(f"Error subiendo el PDF a Gemini: {e}")
                return None
        else:
            print(f"Advertencia: No se encontró el PDF en {self.ruta_pdf_horarios}")
            return None



    def preguntar_a_comunicados(self, pregunta_usuario: str) -> str:
        contexto_textual = self._recuperar_contexto_semantico(pregunta_usuario)
        
        prompt_estricto = f"""
        Eres el asistente virtual oficial de la Hermandad. 
        Tu tarea es responder a la pregunta del hermano utilizando ÚNICAMENTE la información proporcionada en:
        A) El bloque "COMUNICADOS OFICIALES" detallado abajo.
        B) El documento PDF adjunto que contiene los horarios e información de las cofradías.

        Si la respuesta no se encuentra en el PDF ni en el texto proporcionado, responde EXACTAMENTE: "Lo siento, no encuentro información sobre esa consulta en los comunicados oficiales ni en los horarios."

        COMUNICADOS OFICIALES:
        {contexto_textual if contexto_textual.strip() else "No hay comunicados relevantes para esta consulta."}

        PREGUNTA DEL HERMANO:
        {pregunta_usuario}
        """

        try:
            contenidos = []

            archivo_pdf = self._obtener_o_subir_pdf()
            
            if archivo_pdf:
                contenidos.append(archivo_pdf)

            contenidos.append(prompt_estricto)

            respuesta = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contenidos
            )
            
            return respuesta.text
            
        except Exception as e:
            raise Exception(f"Error al generar la respuesta con la IA: {str(e)}")