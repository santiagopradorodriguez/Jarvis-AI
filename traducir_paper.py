#!/usr/bin/env /home/santiago/.jarvis-env/bin/python3
import os
import sys
import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv

if len(sys.argv) < 2:
    print("Uso: traducir_paper.py <ruta_al_pdf>")
    sys.exit(1)

pdf_path = sys.argv[1]
if not os.path.isfile(pdf_path):
    print(f"Error: No se encontró el archivo {pdf_path}")
    sys.exit(1)

# Configurar API
load_dotenv(os.path.expanduser("~/.env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-latest')

output_path = pdf_path.replace('.pdf', '_traducido.md')
doc = fitz.open(pdf_path)

print(f"\n[TRADUCTOR CIENTÍFICO INICIADO]")
print(f"Paper: {os.path.basename(pdf_path)}")
print(f"Páginas totales: {doc.page_count}")
print(f"El resultado se irá guardando progresivamente en: {output_path}")

with open(output_path, "w", encoding="utf-8") as f:
    f.write(f"# Traducción de {os.path.basename(pdf_path)}\n\n")

chunk_text = ""
for i, page in enumerate(doc):
    chunk_text += f"\n<!-- Inicio Página {i+1} -->\n" + page.get_text("text")
    
    # Traducimos de a 3 páginas para no saturar el límite de respuesta
    if (i + 1) % 3 == 0 or i == doc.page_count - 1:
        print(f"-> Traduciendo páginas hasta la {i+1} con Inteligencia Artificial...")
        
        prompt = f"""Sos un experto traductor de literatura científica en física e ingeniería.
Voy a darte un bloque de texto extraído de un PDF (por lo que los saltos de línea pueden estar rotos o mezclados).
Tu tarea:
1. Traducir todo el texto al español de forma natural pero técnicamente impecable.
2. Arreglar el formato (uní oraciones rotas).
3. No resumas el texto, traducí de forma completa.
4. Mantené formato Markdown básico.
Respondé ÚNICAMENTE con la traducción pura.

Texto a traducir:
{chunk_text}
"""
        try:
            response = model.generate_content(prompt)
            with open(output_path, "a", encoding="utf-8") as f:
                f.write(response.text + "\n\n")
            chunk_text = ""  # Limpiar para el siguiente bloque
        except Exception as e:
            print(f"\nError en la traducción de este bloque: {e}")
            sys.exit(1)

print("\n¡Traducción completada exitosamente!")
print(f"El paper traducido está disponible en: {output_path}")
