import time
import random
from setup.matrix_setup import matrix
from PIL import Image, ImageDraw

def run_start_sequence():
    image = Image.new('RGB', (64, 32), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 1. Load F1 Logo (Top)
    logo = Image.open('assets/images/f1/league/f1.png').convert('RGBA')
    logo = logo.resize((30, 12), Image.Resampling.LANCZOS)
    image.paste(logo, (17, 2), logo)

    # 2. Starting Lights Logic
    # Centers for 5 lights across the middle
    light_centers = [12, 22, 32, 42, 52]

    # Light up red dots one by one
    for i in range(5):
        # Draw red circle (filled)
        draw.ellipse([light_centers[i]-4, 18, light_centers[i]+4, 26], fill=(255, 0, 0))
        matrix.SetImage(image)
        time.sleep(1.0) # 1 second per light

    # 3. Random delay before "Lights Out" (0.5 to 3 seconds)
    time.sleep(random.uniform(0.5, 3.0))

    # 4. Clear lights and flash "GO!" or just Black
    draw.rectangle([0, 18, 64, 32], fill=(0, 0, 0))
    matrix.SetImage(image)
