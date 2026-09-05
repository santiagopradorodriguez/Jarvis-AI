#!/usr/bin/env python3
import subprocess
import os
import re
import time

EDGE_TTS = "/home/santiago/.gemini/tts_venv/bin/edge-tts"
PYTHON_BIN = "/home/santiago/.gemini/tts_venv/bin/python"
TARS_PLAYER = "/home/santiago/.gemini/config/tars_player.py"
DEFAULT_SOUND = "/home/santiago/.gemini/config/tenes_un_mensaje_de_whatsapp.wav"

recent_senders = {}
COOLDOWN_SECONDS = 30  # 30s de silencio si es la misma persona

def announce_message(sender_name):
    # Generar TTS diciendo quién mandó el mensaje
    clean_sender = re.sub(r'[^\w\s]', '', sender_name).strip()
    if not clean_sender:
        clean_sender = "WhatsApp"
        
    text = f"Mensaje de {clean_sender}"
    mp3_file = "/tmp/wa_msg.mp3"
    wav_file = "/tmp/wa_msg.wav"
    
    try:
        # Generar voz con Edge-TTS
        res = subprocess.run(
            [EDGE_TTS, "--text", text, "--voice", "es-AR-TomasNeural", "--rate", "-5%", "--write-media", mp3_file],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
        )
        if res.returncode == 0 and os.path.exists(mp3_file):
            subprocess.run(["ffmpeg", "-y", "-i", mp3_file, wav_file],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(wav_file):
                subprocess.run([PYTHON_BIN, TARS_PLAYER, wav_file],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
    except Exception as e:
        pass
        
    # Fallback si falla edge-tts: reproducir el sonido por defecto una sola vez
    if os.path.exists(DEFAULT_SOUND):
        subprocess.run([PYTHON_BIN, TARS_PLAYER, DEFAULT_SOUND],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    cmd = ["dbus-monitor", "type='method_call',interface='org.freedesktop.Notifications',member='Notify'"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    
    in_method_call = False
    string_count = 0
    app_name = None
    summary = None

    for line in proc.stdout:
        line = line.strip()
        if line.startswith("method call"):
            in_method_call = True
            app_name = None
            summary = None
            string_count = 0
            continue

        if in_method_call:
            if line.startswith("string"):
                match = re.search(r'string\s+"(.*?)"', line)
                val = match.group(1) if match else ""
                string_count += 1
                if string_count == 1:
                    app_name = val
                elif string_count == 3:
                    summary = val
            elif line.startswith("array"):
                if app_name and re.search(r'(?:ZapZap|zapzap|com\.rtosta\.zapzap|WhatsApp)', app_name, re.IGNORECASE):
                    sender = summary if summary else "WhatsApp"
                    now = time.time()
                    last_time = recent_senders.get(sender, 0)
                    
                    # Evitar repetir el sonido si la misma persona manda varios mensajes seguidos
                    if now - last_time > COOLDOWN_SECONDS:
                        recent_senders[sender] = now
                        announce_message(sender)
                    else:
                        # Silencio durante el cooldown
                        recent_senders[sender] = now
                        
                in_method_call = False

if __name__ == "__main__":
    main()
