#!/usr/bin/env python3
import math
import struct
import wave

def generate_tone(filename, frequencies, durations, sample_rate=44100, volume=0.3):
    """
    Generates a clean, click-free harmonic tone sequence with smooth envelope.
    """
    audio_data = bytearray()
    for freq, duration in zip(frequencies, durations):
        total_samples = int(sample_rate * duration)
        for i in range(total_samples):
            t = float(i) / sample_rate
            # Smooth envelope (sinusoidal attack & decay) to eliminate clicks
            envelope = math.sin(math.pi * i / total_samples) ** 1.5
            
            # Harmonic combination for a warm, natural acoustic tone
            val = math.sin(2.0 * math.pi * freq * t) * 0.7 + \
                  math.sin(2.0 * math.pi * (freq * 2) * t) * 0.25 + \
                  math.sin(2.0 * math.pi * (freq * 3) * t) * 0.05
            
            sample = int(val * envelope * volume * 32767.0)
            sample = max(-32767, min(32767, sample))
            audio_data.extend(struct.pack('<h', sample))

    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)

def main():
    # 1. Tono al presionar grabar / abrir microfono (ascendente, dinamico y limpio)
    # D5 (587.3 Hz) -> A5 (880.0 Hz)
    generate_tone(
        "/home/santiago/.gemini/config/tars_record_start.wav",
        frequencies=[587.33, 880.0],
        durations=[0.08, 0.12],
        volume=0.25
    )
    
    # 2. Tono de envio / palabra "cambio" detectada (confirmacion suave)
    # A5 (880.0 Hz) -> D5 (587.3 Hz)
    generate_tone(
        "/home/santiago/.gemini/config/tars_record_end.wav",
        frequencies=[880.0, 587.33],
        durations=[0.07, 0.10],
        volume=0.22
    )
    
    # 3. Tono "tu turno" (apenas el asistente termina de responder, indicando microfono listo)
    # E5 (659.25 Hz) con decaimiento natural
    generate_tone(
        "/home/santiago/.gemini/config/tars_your_turn.wav",
        frequencies=[659.25],
        durations=[0.18],
        volume=0.20
    )

if __name__ == "__main__":
    main()
