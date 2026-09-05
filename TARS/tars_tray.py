#!/usr/bin/env python3
import os
import json
import time
import subprocess
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item

STATE_FILE = "/home/santiago/.gemini/config/tars_state.json"
ICON_GREEN = "/home/santiago/.gemini/config/tars_green.png"
ICON_YELLOW = "/home/santiago/.gemini/config/tars_yellow.png"
ICON_RED = "/home/santiago/.gemini/config/tars_red.png"

START_CHIME = "/home/santiago/.gemini/config/tars_record_start.wav"
END_CHIME = "/home/santiago/.gemini/config/tars_record_end.wav"
CANCEL_TONE = "/home/santiago/.gemini/config/tars_cancel_tone.wav"

def get_mode():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                if "mode" in data:
                    return data["mode"]
                # Fallback for old state
                return "auto" if data.get("enabled", True) else "off"
    except Exception:
        pass
    return "auto"

def set_mode(mode):
    with open(STATE_FILE, "w") as f:
        json.dump({"mode": mode}, f)
    
    # Audio cue when toggled
    sound = None
    if mode == "auto":
        sound = START_CHIME
    elif mode == "button":
        sound = END_CHIME
    elif mode == "off":
        sound = CANCEL_TONE
        
    if sound and os.path.exists(sound):
        subprocess.Popen(["paplay", sound], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def cycle_mode(icon, item=None):
    current = get_mode()
    if current == "auto":
        new_mode = "button"
    elif current == "button":
        new_mode = "off"
    else:
        new_mode = "auto"
    
    set_mode(new_mode)
    update_icon(icon)

def set_mode_auto(icon, item=None):
    set_mode("auto")
    update_icon(icon)

def set_mode_button(icon, item=None):
    set_mode("button")
    update_icon(icon)

def set_mode_off(icon, item=None):
    set_mode("off")
    update_icon(icon)

def update_icon(icon):
    mode = get_mode()
    if mode == "auto":
        icon_path = ICON_GREEN
        icon.title = "TARS: Escucha Automática (Hola TARS + botón)"
    elif mode == "button":
        icon_path = ICON_YELLOW
        icon.title = "TARS: Modo Manual (Solo botón)"
    else:
        icon_path = ICON_RED
        icon.title = "TARS: Apagado (Privacidad total)"
        
    if os.path.exists(icon_path):
        icon.icon = Image.open(icon_path)
    
    icon.menu = get_menu()

def exit_tray(icon, item=None):
    icon.stop()

def get_menu():
    mode = get_mode()
    return pystray.Menu(
        item(f"Estado actual: {mode.upper()}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        item("🟢 Modo Escucha Automática (Manos Libres)", set_mode_auto, checked=lambda item: mode == "auto", radio=True),
        item("🟡 Modo Solo Botón (Push-to-Talk)", set_mode_button, checked=lambda item: mode == "button", radio=True),
        item("🔴 Apagar TARS", set_mode_off, checked=lambda item: mode == "off", radio=True),
        pystray.Menu.SEPARATOR,
        item("Salir", exit_tray)
    )

def state_watcher(icon):
    last_mode = get_mode()
    while True:
        time.sleep(0.5)
        curr = get_mode()
        if curr != last_mode:
            last_mode = curr
            update_icon(icon)

def main():
    initial_mode = get_mode()
    
    if initial_mode == "auto":
        img_path = ICON_GREEN
    elif initial_mode == "button":
        img_path = ICON_YELLOW
    else:
        img_path = ICON_RED
        
    # Create fallback image if files don't exist yet
    if os.path.exists(img_path):
        img = Image.open(img_path)
    else:
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    
    icon = pystray.Icon(
        name="TARS",
        icon=img,
        title="TARS",
        menu=get_menu()
    )
    
    icon.on_activate = cycle_mode
    threading.Thread(target=state_watcher, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    main()
