#!/usr/bin/env python3
import subprocess
import os
import re
import time
import asyncio
import edge_tts

PYTHON_BIN = "/home/santiago/.gemini/tts_venv/bin/python"
TARS_PLAYER = "/home/santiago/.gemini/config/tars_player.py"
DEFAULT_SOUND = "/home/santiago/.gemini/config/tenes_un_mensaje_de_whatsapp.wav"
VOICE = "es-AR-TomasNeural"

recent_senders = {}
COOLDOWN_SECONDS = 30  # 30 segundos de silencio para la misma persona

async def generate_speech(text, mp3_path):
    communicate = edge_tts.Communicate(text, VOICE, rate="-5%")
    await communicate.save(mp3_path)

def announce_message(sender_name):
    # Limpiar nombre del remitente
    clean_sender = re.sub(r'[^\w\s]', '', sender_name).strip()
    if not clean_sender:
        clean_sender = "WhatsApp"

    text = f"Mensaje de {clean_sender}"
    mp3_file = "/tmp/wa_msg.mp3"
    wav_file = "/tmp/wa_msg.wav"

    try:
        # Generar TTS directo en memoria
        asyncio.run(generate_speech(text, mp3_file))
        if os.path.exists(mp3_file):
            subprocess.run(["ffmpeg", "-y", "-i", mp3_file, wav_file],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(wav_file):
                subprocess.run([PYTHON_BIN, TARS_PLAYER, wav_file],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
    except Exception as e:
        print(f"Error en TTS de WhatsApp: {e}", flush=True)

    # Fallback si no hay internet o falla Edge-TTS: reproducir sonido base
    if os.path.exists(DEFAULT_SOUND):
        subprocess.run([PYTHON_BIN, TARS_PLAYER, DEFAULT_SOUND],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print("Iniciando ZapZap Listener robusto...", flush=True)
    cmd = ["dbus-monitor", "type='method_call',interface='org.freedesktop.Notifications',member='Notify'"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)

    in_call = False
    call_lines = []
    strings = []

    for raw_line in proc.stdout:
        line = raw_line.strip()
        if line.startswith("method call"):
            # Procesar la llamada anterior si la había
            if in_call and call_lines:
                process_notification(call_lines, strings)
            in_call = True
            call_lines = [line]
            strings = []
            continue

        if in_call:
            call_lines.append(line)
            # Extraer strings
            match = re.search(r'string\s+"(.*?)"', line)
            if match:
                strings.append(match.group(1))
            # El último parámetro del método Notify es siempre int32 expire_timeout
            if line.startswith("int32"):
                process_notification(call_lines, strings)
                in_call = False
                call_lines = []
                strings = []

def process_notification(call_lines, strings):
    # Si TARS está en modo apagado (Rojo), silencio absoluto
    try:
        state_f = "/home/santiago/.gemini/config/tars_state.json"
        if os.path.exists(state_f):
            import json
            with open(state_f, "r") as sf:
                if json.load(sf).get("mode") == "off":
                    return
    except Exception:
        pass

    full_text = "\n".join(call_lines)
    # Detectar si la notificación proviene de ZapZap o WhatsApp en cualquier campo
    is_zapzap = bool(re.search(r'(?:ZapZap|zapzap|com\.rtosta\.zapzap|WhatsApp)', full_text, re.IGNORECASE))
    if not is_zapzap:
        return

    # En la firma de Notify:
    # strings[0] = app_name (ej. "ZapZap" o "")
    # strings[1] = app_icon (ej. "")
    # strings[2] = summary (nombre del remitente o grupo)
    # strings[3] = body (texto del mensaje)
    summary = ""
    if len(strings) >= 3:
        summary = strings[2].strip()
    elif len(strings) >= 1:
        summary = strings[0].strip()

    if not summary or summary.lower() in ("zapzap", "whatsapp"):
        # Si el summary no tiene el nombre, buscar en body si existe
        if len(strings) >= 4 and strings[3].strip():
            # A veces el formato es "Remitente: Mensaje"
            parts = strings[3].split(":", 1)
            summary = parts[0].strip() if len(parts) > 1 else summary

    sender = summary if summary else "WhatsApp"
    now = time.time()
    last_time = recent_senders.get(sender, 0)

    # Ventana de cooldown para no spamear si mandan muchos mensajes juntos
    if now - last_time > COOLDOWN_SECONDS:
        print(f"Notificando mensaje de: {sender}", flush=True)
        recent_senders[sender] = now
        announce_message(sender)
    else:
        print(f"Mensaje en cooldown de: {sender}", flush=True)
        recent_senders[sender] = now

if __name__ == "__main__":
    main()
