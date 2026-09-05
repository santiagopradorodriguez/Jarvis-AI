#!/usr/bin/env python3
import time
import os
import json
import subprocess
import threading
from pynput import keyboard

STATE_FILE = "/home/santiago/.gemini/config/tars_state.json"
CANCEL_TONE = "/home/santiago/.gemini/config/tars_cancel_tone.wav"
RECORD_START_TONE = "/home/santiago/.gemini/config/tars_record_start.wav"
RECORD_END_TONE = "/home/santiago/.gemini/config/tars_record_end.wav"
CHIME_FILE = "/home/santiago/.gemini/config/gemini_chime.wav"
DICTATING_LOCK = "/tmp/tars_dictating.lock"
SPEAKING_LOCK = "/tmp/tars_speaking.lock"

def play_sound(path, fallback=CHIME_FILE):
    target = path if os.path.exists(path) else fallback
    if os.path.exists(target):
        subprocess.Popen(["paplay", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_mode():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                if "mode" in data:
                    return data["mode"]
                return "auto" if data.get("enabled", True) else "off"
    except Exception:
        pass
    return "auto"

def set_mode(mode):
    with open(STATE_FILE, "w") as f:
        json.dump({"mode": mode}, f)

key_pressed_time = None
long_press_triggered = False
press_lock = threading.Lock()

def is_target_key(key):
    vk = getattr(key, 'vk', None)
    return key in (keyboard.Key.f12, keyboard.Key.insert) or vk == 269025090 or str(key) == '<269025090>'

def send_ctrl_m():
    controller = keyboard.Controller()
    time.sleep(0.04)
    controller.press(keyboard.Key.ctrl_l)
    time.sleep(0.03)
    controller.press('m')
    time.sleep(0.03)
    controller.release('m')
    time.sleep(0.03)
    controller.release(keyboard.Key.ctrl_l)

def send_enter():
    controller = keyboard.Controller()
    time.sleep(0.05)
    controller.press(keyboard.Key.enter)
    time.sleep(0.05)
    controller.release(keyboard.Key.enter)

def trigger_short_action():
    # Stop assistant speech instantly
    subprocess.run(["pkill", "-9", "-f", "ffplay.*antigravity_response"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "tars_player.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if os.path.exists(SPEAKING_LOCK):
            os.remove(SPEAKING_LOCK)
    except Exception:
        pass
    subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Check if we were dictating
    if os.path.exists(DICTATING_LOCK):
        # We were dictating -> Stop and SEND
        try:
            os.remove(DICTATING_LOCK)
        except Exception:
            pass
        play_sound(RECORD_END_TONE)
        send_ctrl_m()
        time.sleep(0.15)
        send_enter()
    else:
        # We were NOT dictating -> Start dictating
        with open(DICTATING_LOCK, "w") as f:
            f.write("1")
        
        # If in "off", wake up to "button"
        if get_mode() == "off":
            set_mode("button")
            
        play_sound(RECORD_START_TONE)
        send_ctrl_m()

def trigger_killswitch():
    subprocess.run(["pkill", "-9", "-f", "ffplay.*antigravity_response"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "tars_player.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if os.path.exists(SPEAKING_LOCK):
            os.remove(SPEAKING_LOCK)
        if os.path.exists(DICTATING_LOCK):
            os.remove(DICTATING_LOCK)
    except Exception:
        pass
    subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    set_mode("off")
    play_sound(CANCEL_TONE)

def monitor_long_press():
    global long_press_triggered, key_pressed_time
    time.sleep(4.5)  # 4.5 to 5.0 seconds hold
    with press_lock:
        if key_pressed_time is not None:
            long_press_triggered = True
            trigger_killswitch()

def on_press(key):
    global key_pressed_time, long_press_triggered
    if not is_target_key(key):
        return

    with press_lock:
        if key_pressed_time is None:
            key_pressed_time = time.time()
            long_press_triggered = False
            threading.Thread(target=monitor_long_press, daemon=True).start()

def on_release(key):
    global key_pressed_time, long_press_triggered
    if not is_target_key(key):
        return

    with press_lock:
        if key_pressed_time is not None:
            duration = time.time() - key_pressed_time
            key_pressed_time = None
            if not long_press_triggered and duration < 3.0:
                trigger_short_action()
            long_press_triggered = False

def main():
    try:
        if os.path.exists(DICTATING_LOCK):
            os.remove(DICTATING_LOCK)
    except Exception:
        pass
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
