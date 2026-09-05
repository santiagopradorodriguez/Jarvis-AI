# 🚀 Plan de Trabajo y Acción (TARS Assistant)

Este documento detalla la hoja de ruta y las próximas integraciones clave para el asistente inteligente TARS, con el objetivo de convertirlo en un sistema domótico e interactivo completo (Open Source).

## 🛠 Fase 1: Consolidación Core (Completada)
- [x] Reconocimiento de voz offline (Vosk).
- [x] Lógica de dictado automático (Antigravity).
- [x] Semáforo de privacidad (3 modos: Automático, Botón, Apagado).
- [x] Walkie-Talkie Mode (Push-To-Talk) mediante F12.
- [x] Feedback acústico sin auto-escucha (tonos generados y silenciamiento del OS).
- [x] Limpieza avanzada de respuestas (eliminación de LaTeX y código para TTS).
- [x] Interceptación nativa de notificaciones de WhatsApp (ZapZap) por DBus.

## 🎵 Fase 2: Control Multimedia (Spotify)
**Objetivo:** Control absoluto de la reproducción de música usando comandos de voz.
*   **Lectura del estado:** Integración con DBus (MPRIS) para saber qué canción está sonando.
*   **Comandos básicos:** Pausar, reproducir, siguiente, anterior, subir/bajar volumen.
*   **Búsqueda avanzada:** Permitir que el usuario diga "TARS, poné X canción en Spotify" e interaccionar con la API de escritorio o CLI (ej. `spt`).

## 💻 Fase 3: Monitorización de Tareas (Terminal)
**Objetivo:** Integración directa con scripts de desarrollo (ej. entrenamiento de redes neuronales, builds largos).
*   **`tars-run`:** Un script wrapper que ejecuta cualquier comando en la terminal (ej. `tars-run python train.py`).
*   **Aviso vocal:** Al terminar el comando, TARS anunciará en voz alta: *"El entrenamiento finalizó exitosamente. Tiempo total: X minutos"*.
*   **Lectura de métricas:** Capacidad de inyectarle a TARS un archivo JSON de resultados para que los lea por voz.

## 📱 Fase 4: Expansión Móvil (App Android - Red Local)
**Objetivo:** Llevar a TARS por toda la casa sin depender de la proximidad a la PC.
*   **Aplicación nativa ligera:** Una app de Android sencilla que funcione como un micrófono/parlante remoto.
*   **Conexión por Red Local (WLAN):** Comunicación por WebSockets con un servidor en Python corriendo en la PC principal.
*   **Casos de uso:**
    *   Hablar con TARS desde la cocina (usando el teléfono) y que la respuesta de Antigravity se procese en la PC pero el audio se envíe directamente al celular para ser reproducido.
    *   Convertir a TARS en un asistente omnipresente en el hogar, manteniendo todo el procesamiento seguro y local en la PC principal, preservando la filosofía Open Source.

## 🌍 Visión a Futuro
*   Integración con Home Assistant / Dispositivos IoT.
*   Distribución universal del repositorio para que cualquier usuario de Linux pueda clonar y tener su propio "Jarvis" personalizable.
