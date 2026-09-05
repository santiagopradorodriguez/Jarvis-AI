#!/usr/bin/env python3
import os
import sys
import time
import signal
import subprocess

LOCK_FILE = "/tmp/tars_speaking.lock"
AUDIO_FILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/antigravity_response.mp3"
CHIME_FILE = "/home/santiago/.gemini/config/gemini_chime.wav"

def mute_mic(mute=True):
    val = "1" if mute else "0"
    try:
        subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", val],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", val],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def cleanup(signum=None, frame=None):
    mute_mic(False)
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass
    if signum is not None:
        sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
            
        mute_mic(True)
        
        # Only play chime if it's the main antigravity response
        if AUDIO_FILE == "/tmp/antigravity_response.mp3" and os.path.exists(CHIME_FILE):
            subprocess.run(["paplay", CHIME_FILE],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.1)
            
        if os.path.exists(AUDIO_FILE):
            # Usar paplay si es WAV, ffplay si es mp3
            if AUDIO_FILE.endswith(".wav"):
                subprocess.run(["paplay", AUDIO_FILE],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", AUDIO_FILE],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        if AUDIO_FILE == "/tmp/antigravity_response.mp3":
            turn_cue = "/home/santiago/.gemini/config/tars_your_turn.wav"
            if os.path.exists(turn_cue):
                subprocess.run(["paplay", turn_cue],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        cleanup()

if __name__ == "__main__":
    main()
