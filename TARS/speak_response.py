#!/usr/bin/env python3
import sys
import json
import os
import re
import subprocess
import asyncio
import certifi
import edge_tts
os.environ["SSL_CERT_FILE"] = certifi.where()

VOICE = "es-AR-TomasNeural"
OUTPUT_FILE = "/tmp/antigravity_response.mp3"

def clean_text_for_speech(text):
    if not text:
        return ""
        
    # 1. Remove multiline code blocks
    text = re.sub(r'```[\s\S]*?```', ' [código en pantalla] ', text)
    
    # 2. Replace display math blocks ($$...$$ or \[...\]) with clean indicator
    text = re.sub(r'\$\$[\s\S]*?\$\$', ' [fórmula en pantalla] ', text)
    text = re.sub(r'\\\[[\s\S]*?\\\]', ' [fórmula en pantalla] ', text)
    
    # 3. Handle file:// links and markdown links
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[(.*?)\]\(file://[^\)]+\)', r'\1', text)
    text = re.sub(r'\[(.*?)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'file://[^\s)]+', '', text)
    
    # 4. Remove inline code backticks while preserving content
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # 5. Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # 6. Convert common LaTeX and math symbols to natural Spanish speech BEFORE stripping symbols
    # Arrows
    text = re.sub(r'\\(?:to|rightarrow|longrightarrow|Rightarrow)\b', ' a ', text)
    text = re.sub(r'\\(?:leftarrow|longleftarrow|Leftarrow)\b', ' desde ', text)
    text = re.sub(r'\s*-->\s*|\s*->\s*|\s*=>\s*', ' a ', text)
    
    # Comparators and math operators
    text = re.sub(r'\\approx\b', ' aproximadamente ', text)
    text = re.sub(r'\\(?:neq|ne)\b', ' distinto de ', text)
    text = re.sub(r'\\(?:leq|le)\b', ' menor o igual a ', text)
    text = re.sub(r'\\(?:geq|ge)\b', ' mayor o igual a ', text)
    text = re.sub(r'\\times\b', ' por ', text)
    text = re.sub(r'\\pm\b', ' más o menos ', text)
    text = re.sub(r'\\cdot\b', ' ', text)
    text = re.sub(r'\\sim\b', ' similar a ', text)
    
    # Greek letters
    text = re.sub(r'\\alpha\b', ' alfa ', text)
    text = re.sub(r'\\beta\b', ' beta ', text)
    text = re.sub(r'\\gamma\b', ' gamma ', text)
    text = re.sub(r'\\delta\b', ' delta ', text)
    text = re.sub(r'\\theta\b', ' tita ', text)
    text = re.sub(r'\\mu\b', ' micro ', text)
    text = re.sub(r'\\pi\b', ' pi ', text)
    text = re.sub(r'\\sigma\b', ' sigma ', text)
    text = re.sub(r'\\tau\b', ' tau ', text)
    
    # Common LaTeX wrappers: \text{...}, \mathbf{...}, \mathit{...}, \mathrm{...}
    text = re.sub(r'\\(?:text|mathbf|mathit|mathrm|mathcal)\{([^}]*)\}', r'\1', text)
    
    # LaTeX sub/superscripts
    text = re.sub(r'[_^]\{([^}]*)\}', r' sub \1 ', text)
    text = re.sub(r'_([a-zA-Z0-9])', r' sub \1 ', text)
    
    # 7. Units pronunciation
    text = re.sub(r'\bkHz\b', ' kilohertz ', text)
    text = re.sub(r'\bHz\b', ' hertz ', text)
    text = re.sub(r'\bms\b', ' milisegundos ', text)
    text = re.sub(r'\bseg\b', ' segundos ', text)
    text = re.sub(r'\b(\d+)\s*s\b', r'\1 segundos ', text)
    text = re.sub(r'\buV\b|\bµV\b', ' microvoltios ', text)
    text = re.sub(r'\bMB\b', ' megabytes ', text)
    text = re.sub(r'\bGB\b', ' gigabytes ', text)
    
    # 8. Symbols translation to natural speech
    text = re.sub(r'%', ' por ciento ', text)
    text = re.sub(r'&', ' y ', text)
    text = re.sub(r'\+', ' más ', text)
    text = re.sub(r'=', ' es igual a ', text)
    
    # 9. Strip LaTeX inline delimiters ($ and \(\)) and stray LaTeX commands
    text = re.sub(r'\\\(|\\\)', ' ', text)
    text = re.sub(r'\\?\$', ' ', text)  # Strip ALL dollar signs!
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)  # Any remaining \command
    
    # 10. Phonetic slashes like /a/, /e/, /i/
    text = re.sub(r'/([a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]+)/', r'\1', text)
    
    # 11. Command flags: e.g. --user, -nodisp -> user, nodisp
    text = re.sub(r'(?<=\s)--?([a-zA-Z])', r'\1', text)
    
    # 12. Strip markdown headers, bullets, formatting
    text = re.sub(r'^[#*>\-\s]+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[*_~`#^]', ' ', text)
    
    # 13. Remove slashes, backslashes, pipes, brackets, quotes
    text = re.sub(r'[/\\|]', ' ', text)
    text = re.sub(r'[(){}\[\]]', ', ', text)
    text = re.sub(r'["\'«»“”]', '', text)
    
    # 14. Prevent assistant from vocalizing the exact closing trigger word
    text = re.sub(r'\b[Cc]ambio\b', 'cierre', text)
    
    # 15. Normalize punctuation and spaces
    text = re.sub(r'\s*,\s*', ', ', text)
    text = re.sub(r'\s*\.\s*', '. ', text)
    text = re.sub(r'[,.]\s*[,.]+', '.', text)
    
    # 16. Split by paragraphs to insert natural breathing pauses
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    paced_paragraphs = []
    for p in paragraphs:
        if not p.endswith(('.', ':', '!', '?', ';')):
            p += '.'
        paced_paragraphs.append(p)
    
    # Use ellipsis with space to prompt neural voice into a distinct pause
    text = ' ... '.join(paced_paragraphs)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def generate_speech(text):
    # -5% rate creates a calmer, more human conversational pace
    communicate = edge_tts.Communicate(text, VOICE, rate="-5%")
    await communicate.save(OUTPUT_FILE)

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print("{}")
            return
            
        payload = json.loads(input_data)
        transcript_path = payload.get("transcriptPath")
        if not transcript_path or not os.path.exists(transcript_path):
            print("{}")
            return

        last_content = ""
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    step = json.loads(line)
                    if step.get("type") == "PLANNER_RESPONSE" and step.get("source") == "MODEL":
                        c = step.get("content", "")
                        if c:
                            last_content = c
                except Exception:
                    pass

        if last_content:
            clean = clean_text_for_speech(last_content)
            if clean:
                # Limit length to ~1000 characters so it doesn't speak for 10 minutes on huge responses
                if len(clean) > 1000:
                    cut = clean[:1000]
                    last_period = cut.rfind('.')
                    if last_period != -1:
                        clean = cut[:last_period+1] + " ... El resto de la respuesta está en pantalla."
                    else:
                        clean = cut + " ... El resto de la respuesta está en pantalla."
                
                # Kill previous playback immediately so it stops talking right away
                subprocess.run(["pkill", "-9", "-f", "ffplay.*antigravity_response"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["pkill", "-9", "-f", "tars_player.py"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                asyncio.run(generate_speech(clean))
                
                # Convertir a WAV para usar paplay que es mucho más estable que ffplay
                wav_file = OUTPUT_FILE.replace(".mp3", ".wav")
                subprocess.run(["ffmpeg", "-y", "-i", OUTPUT_FILE, wav_file], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                               
                # Launch tars_player to mute mic, play chime, speak, and unmute mic
                subprocess.Popen(["/home/santiago/.gemini/tts_venv/bin/python", 
                                  "/home/santiago/.gemini/config/tars_player.py", wav_file], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                                 start_new_session=True)
    except Exception:
        pass

    # Always output empty JSON to fulfill Stop hook contract
    print("{}")

if __name__ == "__main__":
    main()
