#!/usr/bin/env /home/santiago/.jarvis-env/bin/python3
import os
import sys
import subprocess
import requests
import speech_recognition as sr
from faster_whisper import WhisperModel
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar la API key desde ~/.env
load_dotenv(os.path.expanduser("~/.env"))
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("ERROR: No se encontró GEMINI_API_KEY en ~/.env")
    sys.exit(1)

genai.configure(api_key=gemini_api_key)

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
# Usamos el nuevo motor optimizado para CPU: Gemma 3 de 4B
FAST_MODEL = "gemma3:4b" 

print("Cargando modelo de voz Whisper (100% offline)... esto toma unos segundos...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
recognizer = sr.Recognizer()
# Reducir el nivel de silencio para que corte más rápido
recognizer.pause_threshold = 0.6 

def play_sound(sound_type):
    if sound_type == "listen":
        subprocess.run(["pw-play", "/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"], stderr=subprocess.DEVNULL)
    elif sound_type == "think":
        subprocess.run(["pw-play", "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga"], stderr=subprocess.DEVNULL)

def speak(text):
    subprocess.run(["/home/santiago/.local/bin/piper-tts-wrapper", text])

# Estado global para acceso al micrófono desde la tool
mic_source = None

# --- TOOL PARA EL AGENTE ---
def run_bash_command(command: str) -> str:
    """Ejecuta un comando de Linux en la computadora del usuario. Útil para abrir programas, leer archivos, etc.
    NO ejecutes comandos muy peligrosos. Para abrir aplicaciones gráficas (como spotify, firefox), usa 'comando &' para no bloquear."""
    
    print(f"\n[⚠️  JARVIS QUIERE EJECUTAR: {command} ]")
    # Autoconfirmacion para comandos seguros
    safe_commands = ["ls", "pwd", "whoami", "cat", "grep", "find"]
    is_safe = any(command.strip().startswith(c) for c in safe_commands)
    
    if not is_safe:
        global mic_source
        if mic_source is None:
            # Fallback a teclado si el micrófono no está listo
            res = input("¿Permitir ejecución? [S/n]: ")
            if res.lower() == 'n':
                return "El usuario denegó el permiso para ejecutar este comando."
        else:
            # Confirmación por voz
            speak("Necesito tu permiso para ejecutar este comando sensible. Decime sí o no.")
            play_sound("listen")
            try:
                audio = recognizer.listen(mic_source, phrase_time_limit=5)
                play_sound("think")
                with open("/tmp/jarvis_confirm.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                segments, info = whisper_model.transcribe("/tmp/jarvis_confirm.wav", beam_size=5, language="es")
                text = "".join([segment.text for segment in segments]).strip().lower()
                print(f"[Confirmación por voz]: {text}")
                
                # Buscamos palabras sueltas que indiquen afirmación
                words = text.replace(",", "").replace(".", "").replace("!", "").split()
                allow_words = {"sí", "si", "dale", "ok", "autorizado", "bueno", "mandale", "yes", "s", "obvio", "claro", "metele"}
                if not any(word in allow_words for word in words):
                    return "El usuario denegó el permiso verbalmente o no se entendió la respuesta."
            except Exception as e:
                print(f"Error escuchando confirmación: {e}")
                return "Hubo un error al escuchar la confirmación, permiso denegado por seguridad."
            
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando comando (exit code {e.returncode}): {e.output.decode('utf-8')}"
    except subprocess.TimeoutExpired:
        return "El comando se ejecutó pero no devolvió salida en 10 segundos. Asumí que funcionó correctamente (especialmente si es una app gráfica)."
    except Exception as e:
        return f"Excepción general: {str(e)}"

def delegate_to_local_agent(task_description: str) -> str:
    """Delega una tarea cognitiva sencilla a tu sub-agente local (Gemma 3). 
    Útil para redactar borradores, resumir textos o procesar información secundaria sin esfuerzo, delegándolo al motor de IA rápido y local."""
    print(f"\n[🤖  JARVIS DELEGANDO A GEMMA LOCAL: {task_description[:60]}... ]")
    
    system_prompt = "Sos un sub-agente rápido y local. Cumplí la siguiente tarea de forma directa, concisa y sin rodeos: "
    data = {
        "model": FAST_MODEL,
        "prompt": system_prompt + task_description,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=data)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"Error en el sub-agente local: {e}"

# Inicializar sesión de Agente con Gemini
agent_model = genai.GenerativeModel(
    'gemini-3.1-pro',
    tools=[run_bash_command, delegate_to_local_agent],
    system_instruction="Sos Jarvis, el asistente e IA Agente del usuario. Tenés permisos para ejecutar comandos bash en su máquina Linux para ayudarle a cumplir objetivos. Además, podés delegar subtareas de redacción o procesamiento a tu sub-agente local mediante delegate_to_local_agent. Hablá siempre en español rioplatense conciso, al grano, sin markdown ni asteriscos. Tus repuestas serán pasadas por un motor de texto a voz, así que escribí fluido."
)
# El enable_automatic_function_calling hace que la SDK corra la función y siga charlando sola.
agent_chat = agent_model.start_chat(enable_automatic_function_calling=True)

# Estado persistente
current_mode = "agente" # Puede ser "rapido" o "agente"

def generate_response(prompt):
    global current_mode
    
    if current_mode == "agente":
        try:
            response = agent_chat.send_message(prompt)
            return response.text
        except Exception as e:
            print(f"Error conectando a Gemini: {e}")
            return "Hubo un error de conexión con la red neuronal principal."
    else:
        # Modo Rápido (Local)
        system_prompt = "Sos Jarvis. Respondé rápido, conciso y conversacional en español rioplatense. NO uses markdown ni asteriscos. Consulta: " + prompt
        data = {
            "model": FAST_MODEL,
            "prompt": system_prompt,
            "stream": False
        }
        
        try:
            response = requests.post(OLLAMA_API_URL, json=data)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"Error conectando a Ollama: {e}")
            return "Disculpame, hubo un error conectándome al motor local."

print("Calibrando micrófono...")
with sr.Microphone() as source:
    global mic_source
    mic_source = source
    recognizer.adjust_for_ambient_noise(source, duration=2)
    os.system('clear')
    print("="*50)
    print("🚀 ¡JARVIS AUTÓNOMO EN LÍNEA! 🚀")
    print("="*50)
    print(" - Pide 'modo agente' para persistencia con Control de Terminal")
    print(" - Pide 'modo rápido' para volver a charlar normal local")
    print("="*50)
    
    speak("Sistemas autónomos en línea. Te escucho.")
    
    while True:
        try:
            print(f"\n[Escuchando...] (Modo actual: {current_mode.upper()})")
            play_sound("listen")
            
            # Escucha hasta que haya un silencio
            audio = recognizer.listen(source, phrase_time_limit=15)
            
            print("[Procesando voz...]")
            play_sound("think")
            
            with open("/tmp/jarvis_audio.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            segments, info = whisper_model.transcribe("/tmp/jarvis_audio.wav", beam_size=5, language="es")
            text = "".join([segment.text for segment in segments]).strip()
            
            if not text or len(text) < 4:
                continue
                
            print(f"Tú: {text}")
            
            text_lower = text.lower()
            
            # Comando de apagado
            if "apágate" in text_lower or "apagate" in text_lower or "cerrar sistema" in text_lower:
                print(">> [SISTEMA] Recibida orden de apagado.")
                speak("Apagando todos los sistemas. Nos vemos.")
                break
            
            # Interpretar cambios de estado
            if "modo agente" in text_lower:
                if current_mode != "agente":
                    current_mode = "agente"
                    print(">> [CAMBIO DE ESTADO] Entrando en Modo Agente Persistente...")
                    speak("Entendido. Modo Agente en línea. Tengo acceso a la terminal de tu computadora.")
                    continue
            elif "modo rápido" in text_lower or "modo normal" in text_lower:
                if current_mode != "rapido":
                    current_mode = "rapido"
                    print(">> [CAMBIO DE ESTADO] Volviendo a Modo Rápido (Local)...")
                    speak("Cortando conexión de herramientas. Volvemos al chat normal.")
                    continue
                
            print(f"Pensando con {'Gemini 1.5 Flash (Agente)' if current_mode == 'agente' else FAST_MODEL + ' (Rápido)'}...")
            
            reply = generate_response(text)
            
            # Limpiar markdown por las dudas si Gemini devuelve asteriscos
            reply = reply.replace("*", "").replace("#", "")
            
            print(f"Jarvis: {reply}")
            
            speak(reply)
            
        except KeyboardInterrupt:
            print("\nApagando sistema...")
            break
        except Exception as e:
            print(f"Error: {e}")
