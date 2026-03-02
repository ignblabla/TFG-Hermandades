import threading
from django.conf import settings
from google import genai
from google.genai import types
from api.models import Comunicado

def generar_y_guardar_embedding_async(comunicado_id):
    """
    Se ejecuta en segundo plano. Obtiene el texto del comunicado,
    llama a Gemini y actualiza el vector en la base de datos.
    """
    def _run():
        try:
            comunicado = Comunicado.objects.get(pk=comunicado_id)
            texto = f"Título: {comunicado.titulo}\nContenido: {comunicado.contenido}"

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resultado = client.models.embed_content(
                model='gemini-embedding-001',
                contents=texto,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )

            Comunicado.objects.filter(pk=comunicado_id).update(
                embedding=resultado.embeddings[0].values
            )
            print(f"✅ Embedding generado para el comunicado {comunicado_id}")
            
        except Comunicado.DoesNotExist:
            print(f"⚠️ Comunicado {comunicado_id} no encontrado para embedding.")
        except Exception as e:
            print(f"⚠️ Error generando embedding para comunicado {comunicado_id}: {e}")

    thread = threading.Thread(target=_run)
    thread.start()