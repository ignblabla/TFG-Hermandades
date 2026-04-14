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
                if intento == max_reintentos - 1:
                    raise Exception("Límite de cuota (429) excedido tras todos los reintentos.")
                time.sleep(15 * (intento + 1))
                continue
                
            if respuesta.status_code in [503, 500]:
                if intento == max_reintentos - 1:
                    raise Exception(f"Servidor caído ({respuesta.status_code}) tras todos los reintentos.")
                time.sleep(2 ** intento)
                continue 
                
            respuesta.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            if intento == max_reintentos - 1:
                raise Exception(f"Fallo de red: {e}")
            time.sleep(2 ** intento)
            
    # Seguro de vida: si el bucle termina por cualquier motivo, lanzamos error
    raise Exception("No se pudo obtener respuesta de la API tras varios intentos.")

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
            
            # Asignamos las nuevas voces STUDIO de alta fidelidad
            # es-ES-Studio-C es Femenina (Carmen)
            # es-ES-Studio-F es Masculina (Antonio)
            if locutor == "Carmen":
                nombre_voz = "es-ES-Studio-C"
            else:
                nombre_voz = "es-ES-Studio-F"
            
            audio_bytes = generar_audio_cloud_tts(texto, nombre_voz)
            
            if audio_bytes:
                segmento = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
                audio_final += segmento
                
                # Pausa natural de medio segundo entre locutores para que no se pisen
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
    # Definimos la URL principal
    url_principal = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # ¡NUEVO PLAN B! Usamos la versión "Lite" actual, que sí está activa y tiene límites de cuota más permisivos
    url_respaldo = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
    
    prompt = f"""
    Eres el guionista de un programa de radio de la Hermandad. Toma este comunicado 
    y conviértelo en una conversación súper natural, amena y cercana entre dos locutores reales: Antonio y Carmen.
    
    Reglas de naturalidad:
    1. Usa un tono cálido y respetuoso pero coloquial.
    2. Deben saludarse y despedirse de los oyentes.
    3. Incluye expresiones humanas, pausas naturales marcadas con puntos suspensivos (...) y reacciones breves (ej. "Claro", "Así es, Antonio", "Qué maravilla").
    4. NO leas el texto de forma robótica, explícalo como si se lo contaras a un amigo.
    
    Título del comunicado: {comunicado.titulo}
    Contenido original: {comunicado.contenido}
    
    Devuelve ÚNICAMENTE un JSON válido con esta estructura:
    {{"dialogos": [{{"locutor": "Carmen", "texto": "..."}}, {{"locutor": "Antonio", "texto": "..."}}]}}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        # 1. Intentamos con el modelo principal
        respuesta = _hacer_peticion_con_reintentos(url_principal, payload)
    except Exception as e:
        print(f"⚠️ El modelo principal falló ({e}). Activando Plan B con gemini-2.5-flash-lite...")
        try:
            # 2. Si el principal falla, disparamos el modelo Lite de respaldo
            respuesta = _hacer_peticion_con_reintentos(url_respaldo, payload, max_reintentos=2)
        except Exception as e_respaldo:
            # 3. Si ambos están caídos, lanzamos el error
            raise Exception(f"Ambos modelos de Gemini están caídos. Error final: {e_respaldo}")
    
    if not respuesta:
        raise ValueError("La API de Gemini no devolvió ninguna respuesta.")
        
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