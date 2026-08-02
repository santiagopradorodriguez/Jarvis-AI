#!/usr/bin/env python3
import sys
import re
import unicodedata

def clean_latex(text):
    text = unicodedata.normalize('NFC', text)

    text = re.sub(r'([a-zA-ZáéíóúÁÉÍÓÚñÑ])-\s*\n\s*([a-zA-ZáéíóúÁÉÍÓÚñÑ])', r'\1\2', text)
    text = re.sub(r'([a-zA-ZáéíóúÁÉÍÓÚñÑ])-\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ])', r'\1\2', text)
    
    def replace_accent(match):
        vowel = match.group(2).lower()
        accents = {'a':'á', 'e':'é', 'i':'í', 'o':'ó', 'u':'ú'}
        if vowel in accents:
            suffix = match.group(3) if match.group(3) else ''
            return match.group(1) + accents[vowel] + suffix
        return match.group(0)
    
    text = re.sub(r'([a-zA-Z])\s*\?+\s*([aeiouAEIOU])([a-zA-Z]?)', replace_accent, text)

    # Arreglos para MathML a texto en inglés y OCR roto
    ocr_fixes = {
        r'F\s*\?\s*\?sica': 'física',
        r'Cu\s*\?antica': 'cuántica',
        r'cap\s*\?\?tulo': 'capítulo',
        r'simetr\s*\?\?a': 'simetría',
        r'vac\s*\?\?o': 'vacío',
        r'teor\s*\?\?a': 'teoría',
        r'energ\s*\?\?a': 'energía',
        r'part\s*\?\?cula': 'partícula',
        
        # OCR Math English
        r'vector between\s*([A-Za-z])': r'vector \1',
        r'vector\s*([A-Za-z])\s*vector\s*([A-Za-z])\s*vector\s*gradient of\s*\?': r'vector \1 se transforma en el vector \2 más el gradiente de lambda',
        r'y\s*\?\s*\?\s*partial derivative\s*\?\s*partial derivative\s*t': r'y el potencial fi se transforma en fi menos la derivada parcial de lambda respecto al tiempo',
        r'partial derivative\s*\?\s*partial derivative\s*([A-Za-z])': r'derivada parcial de lambda respecto a \1',
        r'gradient of\s*\?': 'gradiente de lambda',
        
        r'\?\s*f': 'omega f',
        r'cos\s*\?t': 'coseno de omega t',
        r'sin\s*\?t': 'seno de omega t',
        r'square root': 'raíz cuadrada de',
        r'\?\s*x': 'delta x',
    }
    for k, v in ocr_fixes.items():
        text = re.sub(k, v, text, flags=re.IGNORECASE)

    text = text.replace(r'\sin', ' seno ')
    text = text.replace(r'\cos', ' coseno ')
    text = text.replace(r'\tan', ' tangente ')
    text = text.replace(r'\ln', ' logaritmo natural ')
    text = text.replace(r'\log', ' logaritmo ')
    text = text.replace(r'\exp', ' exponencial de ')

    unicode_math = {
        '∫': ' integral de ',
        '∑': ' sumatoria de ',
        '∏': ' productoria de ',
        '∂': ' derivada parcial de ',
        '∇': ' nabla ',
        '∞': ' infinito ',
        '≈': ' aproximadamente igual a ',
        '≠': ' distinto de ',
        '≡': ' equivalente a ',
        '≤': ' menor o igual a ',
        '≥': ' mayor o igual a ',
        '±': ' mas menos ',
        '×': ' por ',
        '÷': ' dividido ',
        '∝': ' proporcional a ',
        'ℏ': ' hache barra ',
        '⟨': ' valor medio de ',
        '⟩': ' ',
        '=': ' igual a ',
        '+': ' mas ',
    }
    
    unicode_greek = {
        'α': 'alfa', 'β': 'beta', 'γ': 'gamma', 'Γ': 'Gamma',
        'δ': 'delta', 'Δ': 'Delta', 'ε': 'épsilon', 'ζ': 'zeta',
        'η': 'eta', 'θ': 'theta', 'Θ': 'Theta', 'ι': 'iota',
        'κ': 'kappa', 'λ': 'lambda', 'Λ': 'Lambda', 'μ': 'mu',
        'ν': 'nu', 'ξ': 'xi', 'Ξ': 'Xi', 'π': 'pi', 'Π': 'Pi',
        'ρ': 'rho', 'σ': 'sigma', 'Σ': 'Sigma', 'τ': 'tau',
        'υ': 'upsilon', 'φ': 'fi', 'Φ': 'Fi', 'χ': 'chi',
        'ψ': 'psi', 'Ψ': 'Psi', 'ω': 'omega', 'Ω': 'Omega'
    }

    for k, v in unicode_math.items():
        text = text.replace(k, v)
    for k, v in unicode_greek.items():
        text = text.replace(k, v)

    greek = {
        r'\alpha': 'alfa', r'\beta': 'beta', r'\gamma': 'gamma', r'\Gamma': 'Gamma',
        r'\delta': 'delta', r'\Delta': 'Delta', r'\epsilon': 'épsilon', r'\varepsilon': 'épsilon',
        r'\zeta': 'zeta', r'\eta': 'eta', r'\theta': 'theta', r'\Theta': 'Theta',
        r'\iota': 'iota', r'\kappa': 'kappa', r'\lambda': 'lambda', r'\Lambda': 'Lambda',
        r'\mu': 'mu', r'\nu': 'nu', r'\xi': 'xi', r'\Xi': 'Xi',
        r'\pi': 'pi', r'\Pi': 'Pi', r'\rho': 'rho', r'\sigma': 'sigma', r'\Sigma': 'Sigma',
        r'\tau': 'tau', r'\upsilon': 'upsilon', r'\phi': 'fi', r'\Phi': 'Fi', r'\varphi': 'fi',
        r'\chi': 'chi', r'\psi': 'psi', r'\Psi': 'Psi', r'\omega': 'omega', r'\Omega': 'Omega'
    }
    
    for k, v in greek.items():
        text = text.replace(k, v)
        
    text = re.sub(r'\b([fghxyvpa])\(([tx])\)', r'\1 de \2', text)
        
    text = text.replace(r'\hbar', 'hache barra')
    text = text.replace(r'\partial', 'derivada parcial de')
    text = text.replace(r'\infty', 'infinito')
    text = text.replace(r'\nabla', 'nabla')
    text = text.replace(r'\cdot', 'por')
    text = text.replace(r'\times', 'por')
    text = text.replace(r'\rightarrow', 'tiende a')
    text = text.replace(r'\to', 'tiende a')
    text = text.replace(r'\approx', 'aproximadamente igual a')
    text = text.replace(r'\neq', 'distinto de')
    text = text.replace(r'\equiv', 'equivalente a')
    
    text = re.sub(r'\\ket\{([^\}]+)\}', r' ket \1 ', text)
    text = re.sub(r'\\bra\{([^\}]+)\}', r' bra \1 ', text)
    text = re.sub(r'\\braket\{([^\}]+)\}\{([^\}]+)\}', r' braket de \1 con \2 ', text)
    text = re.sub(r'\\langle([^\>]+)\\rangle', r' valor medio de \1 ', text)
    
    text = re.sub(r'\\hat\{([^\}]+)\}', r' \1 sombrero ', text)
    text = re.sub(r'\\vec\{([^\}]+)\}', r' vector \1 ', text)
    text = re.sub(r'\\mathbf\{([^\}]+)\}', r' vector \1 ', text)
    
    text = re.sub(r'\\frac\{([^\}]+)\}\{([^\}]+)\}', r' \1 sobre \2 ', text)
    
    text = re.sub(r'\^\{?2\}?', ' al cuadrado ', text)
    text = re.sub(r'\^\{?3\}?', ' al cubo ', text)
    text = re.sub(r'\^\{([^\}]+)\}', r' a la \1 ', text)
    
    text = re.sub(r'\\int_\{?([a-zA-Z0-9\-\\]+)\}?\^\{?([a-zA-Z0-9\-\\]+)\}?', r' integral desde \1 hasta \2 de ', text)
    text = re.sub(r'\\int', ' integral de ', text)
    
    text = re.sub(r'\\sum_\{?([a-zA-Z0-9\-\\]+)\}?\^\{?([a-zA-Z0-9\-\\]+)\}?', r' sumatoria desde \1 hasta \2 de ', text)
    text = re.sub(r'\\sum', ' sumatoria de ', text)
    
    text = re.sub(r'_\{([^\}]+)\}', r' sub \1 ', text)
    
    text = text.replace(r'\left(', ' abro paréntesis ')
    text = text.replace(r'\right)', ' cierro paréntesis ')
    text = text.replace(r'\left[', ' abro corchete ')
    text = text.replace(r'\right]', ' cierro corchete ')
    text = text.replace(r'\{', ' abro llave ')
    text = text.replace(r'\}', ' cierro llave ')
    
    text = text.replace('$$', ' ')
    text = text.replace('$', ' ')
    text = text.replace(r'\[', ' ')
    text = text.replace(r'\]', ' ')
    
    text = text.replace('-', ' menos ')
    text = re.sub(r'\s+menos\s+', ' menos ', text)

    text = text.replace('?', '')
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
    input_text = sys.stdin.read()
    print(clean_latex(input_text))
