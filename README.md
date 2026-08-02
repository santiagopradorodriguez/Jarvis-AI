# 🚀 Jarvis Assistant

Jarvis Assistant es un panel de control interactivo construido en Python y PyQt6 para interactuar con modelos de IA. Permite alternar entre un modelo rápido local (Gemma 3) para charlar offline y sin latencia, y el potente motor en la nube de Google (Gemini) para ejecutar tareas de programación avanzadas, ejecutar comandos en Bash y leer archivos completos.

## ✨ Características Principales
- **Sistema Dual de IA**: 
  - *Modo Rápido*: Usa modelos locales de Ollama (ej. gemma3:4b).
  - *Modo Agente*: Usa Google Gemini (ej. gemini-3.1-pro-preview).
- **Control de Terminal**: Gemini puede ejecutar comandos de Linux (`bash`) directamente en tu sistema para manipular archivos.
- **Fallbacks Automáticos**: Si la API de Google Cloud excede la cuota gratuita o presenta errores, Jarvis se redirige automáticamente al agente local sin interrumpir la conversación.
- **Procesamiento de Voz Offline**: Integra `faster-whisper` (tamaños `tiny` a `medium`) para un dictado instantáneo e independiente de internet.

## 🛠️ Instalación y Dependencias
Se recomienda ejecutar el proyecto dentro de un entorno virtual (ej. `~/.jarvis-env/`).

```bash
pip install -r requirements.txt
```

## 🚀 Uso
1. Para lanzar la interfaz gráfica, simplemente haz doble clic en el acceso directo de tu Escritorio o ejecuta:
```bash
python3 jarvis_gui.py
```
2. Selecciona tus modelos preferidos de la nube y locales.
3. Presiona el micrófono en pantalla (o invoca el acceso directo de voz) y dale instrucciones a tu IA.
