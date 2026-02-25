import time
from google import genai
from google.genai import types
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Comunicado

class Command(BaseCommand):
    help = 'Genera vectores semánticos (Embeddings) para los comunicados.'

    def handle(self, *args, **options):
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        comunicados_sin_vector = Comunicado.objects.filter(embedding__isnull=True)
        total = comunicados_sin_vector.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ Todos los comunicados ya tienen su vector."))
            return

        self.stdout.write(self.style.WARNING(f"⏳ Generando vectores para {total} comunicados..."))
        exitos, errores = 0, 0

        for comunicado in comunicados_sin_vector:
            texto = f"Título: {comunicado.titulo}\nContenido: {comunicado.contenido}"
            try:
                resultado = client.models.embed_content(
                    model='gemini-embedding-001',
                    contents=texto,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                comunicado.embedding = resultado.embeddings[0].values
                comunicado.save(update_fields=['embedding'])
                exitos += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Vectorizado: {comunicado.titulo}"))
                time.sleep(1) 
            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error en '{comunicado.titulo}': {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Proceso terminado: {exitos} exitosos, {errores} fallidos."))