#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw

def create_circle_icon(path, color, size=64):
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw an antialiased circle
    # Leave a small 2-pixel padding
    margin = 2
    bbox = [margin, margin, size - margin, size - margin]
    
    draw.ellipse(bbox, fill=color, outline=(0, 0, 0, 100), width=1)
    
    # Save the icon
    image.save(path)
    print(f"Icon created: {path}")

def main():
    config_dir = "/home/santiago/.gemini/config"
    
    # Verde (Escucha automatica)
    create_circle_icon(os.path.join(config_dir, "tars_green.png"), (46, 204, 113, 255))
    
    # Amarillo (Solo boton)
    create_circle_icon(os.path.join(config_dir, "tars_yellow.png"), (241, 196, 15, 255))
    
    # Rojo (Apagado / Privacidad)
    create_circle_icon(os.path.join(config_dir, "tars_red.png"), (231, 76, 60, 255))

if __name__ == "__main__":
    main()
