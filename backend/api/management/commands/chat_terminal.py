import sys
from django.core.management.base import BaseCommand
from ...servicios.comunicado.comunicado_rag_service import ComunicadoRAGService

class Command(BaseCommand):
    help = 'Prueba el chat RAG de comunicados directamente desde la terminal'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('==========================================='))
        self.stdout.write(self.style.SUCCESS('   🤖 CHATBOT DE LA HERMANDAD (TEST CLI)   '))
        self.stdout.write(self.style.SUCCESS('==========================================='))
        self.stdout.write('Escribe "salir" para terminar la conversación.\n')
        
        try:
            servicio_rag = ComunicadoRAGService()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al inicializar el servicio: {e}'))
            return

        while True:
            pregunta = input('\n👤 Tú: ')

            if pregunta.strip().lower() in ['salir', 'exit', 'quit']:
                self.stdout.write(self.style.WARNING('\nSaliendo del chat... ¡Hasta pronto!'))
                sys.exit(0)
                
            if not pregunta.strip():
                continue
                
            self.stdout.write(self.style.NOTICE('🤖 Asistente pensando...'))
            
            try:
                respuesta = servicio_rag.preguntar_a_comunicados(pregunta)
                self.stdout.write(self.style.SUCCESS(f'\n🤖 Asistente:\n{respuesta}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))