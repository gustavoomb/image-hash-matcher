# Salva todos os frames de todos os GIFs da pasta "gifs" em "frames_extraidos"
import os
from PIL import Image, ImageSequence

pasta_gifs = "gifs"
pasta_frames = "frames_extraidos"
os.makedirs(pasta_frames, exist_ok=True)

for gif_nome in os.listdir(pasta_gifs):
    if gif_nome.lower().endswith(".gif"):
        caminho_gif = os.path.join(pasta_gifs, gif_nome)
        with Image.open(caminho_gif) as im:
            for i, frame in enumerate(ImageSequence.Iterator(im)):
                frame_path = os.path.join(
                    pasta_frames, f"{os.path.splitext(gif_nome)[0]}_frame_{i+1}.png"
                )
                frame.convert("RGB").save(frame_path)
                print(f"Salvo: {frame_path}")