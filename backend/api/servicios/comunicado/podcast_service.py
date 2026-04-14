import io
import json
import time
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from api.models import Comunicado
from pydub import AudioSegment
from google.cloud import texttospeech

def _hacer_peticion_con_reintentos(url, payload, max_reintentos=4):
    for intento in range(max_reintentos):
        try:
            respuesta = requests.post(url, json=payload, timeout=30)
            if respuesta.status_code == 200:
                return respuesta
            if respuesta.status_code == 429:
                time.sleep(15 * (intento + 1))
                continue
            if respuesta.status_code in [503, 500]:
                time.sleep(2 ** intento)
                continue 
            respuesta.raise_for_status()
        except requests.exceptions.RequestException as e:
            if intento == max_reintentos - 1:
                raise Exception(f"Fallo de red: {e}")
            time.sleep(2 ** intento)

def generar_y_guardar_podcast_async(comunicado_id):
    try:
        comunicado = Comunicado.objects.get(id=comunicado_id)
        api_key = settings.GEMINI_API_KEY
        
        guion_json = generar_guion_conversacional(comunicado, api_key)
        if not guion_json:
            raise ValueError("Gemini no pudo generar el guion conversacional.")

        audio_final = AudioSegment.empty()

        for linea in guion_json.get("dialogos", []):
            locutor = linea.get("locutor")
            texto = linea.get("texto")
            
            nombre_voz = "es-ES-Neural2-A" if locutor == "Host 1" else "es-ES-Neural2-B"
            audio_bytes = generar_audio_cloud_tts(texto, nombre_voz)
            
            if audio_bytes:
                segmento = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
                audio_final += segmento
                audio_final += AudioSegment.silent(duration=500)

        if len(audio_final) > 0:
            buffer_salida = io.BytesIO()
            audio_final.export(buffer_salida, format="mp3", bitrate="128k")
            
            nombre_archivo = f"podcast_comunicado_{comunicado.id}.mp3"
            # Guardamos directamente el archivo
            comunicado.archivo_podcast.save(nombre_archivo, ContentFile(buffer_salida.getvalue()), save=True)

    except Exception as e:
        print(f"Error generando podcast para comunicado {comunicado_id}: {e}")


def generar_guion_conversacional(comunicado, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    prompt = f"""
    Eres un guionista de podcasts. Toma este comunicado y conviértelo en una 
    conversación breve y dinámica entre dos presentadores (Host 1 y Host 2).
    Título: {comunicado.titulo}
    Contenido: {comunicado.contenido}
    
    Devuelve ÚNICAMENTE un JSON válido:
    {{"dialogos": [{{"locutor": "Host 1", "texto": "..."}}, {{"locutor": "Host 2", "texto": "..."}}]}}
    """
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    respuesta = _hacer_peticion_con_reintentos(url, payload)
    return json.loads(respuesta.json()["candidates"][0]["content"]["parts"][0]["text"])


def generar_audio_cloud_tts(texto, nombre_voz):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=texto)
    voice = texttospeech.VoiceSelectionParams(language_code="es-ES", name=nombre_voz)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    try:
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return response.audio_content
    except Exception as e:
        print(f"Error en Google Cloud TTS: {e}")
        return None