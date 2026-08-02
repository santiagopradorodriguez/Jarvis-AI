#!/usr/bin/env /home/santiago/.jarvis-env/bin/python3
import os
import sys
import subprocess
import requests
import speech_recognition as sr
from faster_whisper import WhisperModel
import google.generativeai as genai
from dotenv import load_dotenv

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPalette, QColor

# --- Cargar entorno ---
load_dotenv(os.path.expanduser("~/.env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class JarvisWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    
    def __init__(self, main_model_name, whisper_model_name, fast_model_name):
        super().__init__()
        self.main_model_name = main_model_name
        self.whisper_model_name = whisper_model_name
        self.fast_model_name = fast_model_name
        self.running = True
        self.current_mode = "agente"
        self.mic_source = None

    def play_sound(self, sound_type):
        if sound_type == "listen":
            subprocess.run(["pw-play", "/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"], stderr=subprocess.DEVNULL)
        elif sound_type == "think":
            subprocess.run(["pw-play", "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga"], stderr=subprocess.DEVNULL)

    def speak(self, text):
        subprocess.run(["/home/santiago/.local/bin/piper-tts-wrapper", text])

    def run_bash_command(self, command: str) -> str:
        self.log_signal.emit(f"⚠️ JARVIS EJECUTARÁ: {command}")
        
        safe_commands = ["ls", "pwd", "whoami", "cat", "grep", "find"]
        is_safe = any(command.strip().startswith(c) for c in safe_commands)
        
        if not is_safe:
            if self.mic_source is None:
                return "Permiso denegado por seguridad (no hay micrófono)."
            else:
                self.speak("Necesito tu permiso para ejecutar este comando. Decime sí o no.")
                self.play_sound("listen")
                self.status_signal.emit("Esperando Confirmación de Voz...")
                try:
                    audio = self.recognizer.listen(self.mic_source, phrase_time_limit=5)
                    self.play_sound("think")
                    with open("/tmp/jarvis_confirm.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    segments, _ = self.whisper_model.transcribe("/tmp/jarvis_confirm.wav", beam_size=5, language="es")
                    text = "".join([s.text for s in segments]).strip().lower()
                    self.log_signal.emit(f"Confirmación: {text}")
                    
                    words = text.replace(",", "").replace(".", "").replace("!", "").split()
                    allow_words = {"sí", "si", "dale", "ok", "autorizado", "bueno", "mandale", "yes", "s", "obvio", "claro", "metele"}
                    if not any(w in allow_words for w in words):
                        return "El usuario denegó el permiso."
                except Exception as e:
                    return "Error escuchando confirmación, permiso denegado."
                
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
            return output.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return f"Error ejecutando comando: {e.output.decode('utf-8')}"
        except subprocess.TimeoutExpired:
            return "Comando ejecutado. Asumo éxito (no devolvió salida en 10s)."
        except Exception as e:
            return f"Excepción general: {str(e)}"

    def delegate_to_local_agent(self, task_description: str) -> str:
        self.log_signal.emit(f"🤖 DELEGANDO A GEMMA LOCAL: {task_description[:50]}...")
        system_prompt = "Sos un sub-agente rápido y local. Cumplí la siguiente tarea de forma directa, concisa y sin rodeos: "
        data = {
            "model": self.fast_model_name,
            "prompt": system_prompt + task_description,
            "stream": False
        }
        try:
            response = requests.post("http://127.0.0.1:11434/api/generate", json=data)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error en el sub-agente local: {e}"

    def fallback_to_gemma(self, prompt):
        system_prompt = "Sos Jarvis. Respondé rápido, conciso y conversacional en español rioplatense. NO uses markdown ni asteriscos. Consulta: " + prompt
        data = {
            "model": self.fast_model_name,
            "prompt": system_prompt,
            "stream": False
        }
        try:
            response = requests.post("http://127.0.0.1:11434/api/generate", json=data)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return "Disculpame, hubo un error conectándome al motor local también."

    def generate_response(self, prompt):
        if self.current_mode == "agente":
            try:
                response = self.agent_chat.send_message(prompt)
                return response.text
            except Exception as e:
                self.log_signal.emit(f"Error de API Gemini: {str(e)}")
                self.log_signal.emit("⚠️ FALLBACK: La API falló. Derivando a Gemma local por seguridad...")
                return self.fallback_to_gemma(prompt)
        else:
            return self.fallback_to_gemma(prompt)

    def stop(self):
        self.running = False

    def run(self):
        if not GEMINI_API_KEY:
            self.log_signal.emit("ERROR: No se encontró GEMINI_API_KEY en ~/.env")
            return
            
        genai.configure(api_key=GEMINI_API_KEY)
        self.agent_model = genai.GenerativeModel(
            self.main_model_name,
            tools=[self.run_bash_command, self.delegate_to_local_agent],
            system_instruction="Sos Jarvis, IA Agente autónoma. Tenés permisos bash en Linux. Delegá a Gemma subtareas si sirve. Hablá fluido español rioplatense."
        )
        self.agent_chat = self.agent_model.start_chat(enable_automatic_function_calling=True)

        self.status_signal.emit("Cargando Whisper...")
        self.whisper_model = WhisperModel(self.whisper_model_name, device="cpu", compute_type="int8")
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.6
        
        self.status_signal.emit("Calibrando Micrófono...")
        with sr.Microphone() as source:
            self.mic_source = source
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            
            self.status_signal.emit("Esperando")
            self.log_signal.emit(f"🚀 Jarvis Iniciado - Whisper: {self.whisper_model_name}, Gemma: {self.fast_model_name}")
            self.speak("Sistemas en línea.")
            
            while self.running:
                try:
                    self.status_signal.emit(f"Escuchando ({self.current_mode.upper()})")
                    self.play_sound("listen")
                    audio = self.recognizer.listen(source, phrase_time_limit=15)
                    
                    if not self.running: break
                    
                    self.status_signal.emit("Procesando Voz")
                    self.play_sound("think")
                    with open("/tmp/jarvis_audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    segments, _ = self.whisper_model.transcribe("/tmp/jarvis_audio.wav", beam_size=5, language="es")
                    text = "".join([segment.text for segment in segments]).strip()
                    
                    if not text or len(text) < 4:
                        continue
                        
                    self.log_signal.emit(f"Tú: {text}")
                    text_lower = text.lower()
                    
                    if "apágate" in text_lower or "apagate" in text_lower or "cerrar sistema" in text_lower:
                        self.log_signal.emit(">> Orden de apagado recibida.")
                        self.speak("Apagando. Nos vemos.")
                        break
                        
                    if "modo agente" in text_lower and self.current_mode != "agente":
                        self.current_mode = "agente"
                        self.log_signal.emit(">> Modo Agente Persistente activado.")
                        self.speak("Modo Agente en línea.")
                        continue
                    elif ("modo rápido" in text_lower or "modo normal" in text_lower) and self.current_mode != "rapido":
                        self.current_mode = "rapido"
                        self.log_signal.emit(">> Volviendo a Modo Rápido (Local).")
                        self.speak("Volvemos al chat normal.")
                        continue
                        
                    self.status_signal.emit(f"Pensando ({self.current_mode.upper()})")
                    reply = self.generate_response(text)
                    reply = reply.replace("*", "").replace("#", "")
                    
                    self.log_signal.emit(f"Jarvis: {reply}")
                    self.status_signal.emit("Hablando")
                    self.speak(reply)
                    
                except Exception as e:
                    self.log_signal.emit(f"Error: {e}")
                    
        self.status_signal.emit("Detenido")

class JarvisGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis AI Control Panel")
        self.resize(500, 600)
        self.setup_dark_theme()
        
        self.worker = None
        
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        # Headers
        layout.addWidget(QLabel("Main Model (Cloud AI):"))
        self.combo_main = QComboBox()
        self.combo_main.addItems(["gemini-3.1-pro-preview", "gemini-pro-latest", "gemini-flash-latest", "gemini-3.6-flash", "gemini-2.5-pro"])
        self.combo_main.setCurrentText("gemini-3.1-pro-preview")
        layout.addWidget(self.combo_main)
        
        layout.addWidget(QLabel("Whisper Model (Voice Speed):"))
        self.combo_whisper = QComboBox()
        self.combo_whisper.addItems(["tiny", "base", "small", "medium"])
        self.combo_whisper.setCurrentText("small")
        layout.addWidget(self.combo_whisper)
        
        layout.addWidget(QLabel("Fast Model (Local AI):"))
        self.combo_fast = QComboBox()
        self.combo_fast.addItems(["gemma3:4b", "gemma2:2b", "gemma3:12b"])
        self.combo_fast.setCurrentText("gemma3:4b")
        layout.addWidget(self.combo_fast)
        
        self.btn_toggle = QPushButton("INICIAR JARVIS")
        self.btn_toggle.setFixedHeight(50)
        self.btn_toggle.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold; font-size: 14px; border-radius: 5px;")
        self.btn_toggle.clicked.connect(self.toggle_jarvis)
        layout.addWidget(self.btn_toggle)
        
        self.lbl_status = QLabel("Estado: Detenido")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; margin: 10px;")
        layout.addWidget(self.lbl_status)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.txt_log)

    def setup_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)
        
    def toggle_jarvis(self):
        if self.worker is None or not self.worker.isRunning():
            # Iniciar
            main_mod = self.combo_main.currentText()
            whisper_mod = self.combo_whisper.currentText()
            fast_mod = self.combo_fast.currentText()
            
            self.txt_log.append(f"\n--- INICIANDO SISTEMA ---")
            self.btn_toggle.setText("DETENER JARVIS")
            self.btn_toggle.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; font-size: 14px; border-radius: 5px;")
            
            self.worker = JarvisWorker(main_mod, whisper_mod, fast_mod)
            self.worker.log_signal.connect(self.append_log)
            self.worker.status_signal.connect(self.update_status)
            self.worker.start()
        else:
            # Detener
            self.worker.stop()
            self.worker.terminate() # Forzamos cierre porque recognizer.listen() es bloqueante
            self.btn_toggle.setText("INICIAR JARVIS")
            self.btn_toggle.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold; font-size: 14px; border-radius: 5px;")
            self.update_status("Detenido")
            self.append_log("Jarvis forzado a detenerse por el usuario.")

    def update_status(self, text):
        self.lbl_status.setText(f"Estado: {text}")
        if text == "Detenido":
            self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; margin: 10px;")
        elif "Escuchando" in text:
            self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db; margin: 10px;")
        elif "Pensando" in text or "Cargando" in text:
            self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f; margin: 10px;")
        else:
            self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #2ecc71; margin: 10px;")

    def append_log(self, text):
        self.txt_log.append(text)
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    gui = JarvisGUI()
    gui.show()
    sys.exit(app.exec())
