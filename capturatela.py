from PIL import Image, ImageSequence
import imagehash
import os
import pyautogui
import time

def capturar_area_da_tela(bbox=None, salvar_como="captura.png"):
    # Espera 3 segundos para o usuário posicionar a tela
    # print("Captura em 3 segundos...")
    # time.sleep(3)
    bbox = (70, 591, 450, 348)
    screenshot = pyautogui.screenshot(region=bbox)  # bbox = (x, y, width, height)
    screenshot.save(salvar_como)
    return salvar_como

def carregar_primeiro_frame(caminho_imagem):
    with Image.open(caminho_imagem) as im:
        if getattr(im, "is_animated", False):
            return next(ImageSequence.Iterator(im)).convert("RGB")
        else:
            return im.convert("RGB")

def buscar_gif_similar(imagem_consulta, pasta_gifs):
    frame_consulta = carregar_primeiro_frame(imagem_consulta)
    hash_consulta = imagehash.average_hash(frame_consulta)

    melhor_match = None
    menor_distancia = float("inf")

    for arquivo in os.listdir(pasta_gifs):
        if arquivo.lower().endswith(".gif"):
            caminho = os.path.join(pasta_gifs, arquivo)
            frame_atual = carregar_primeiro_frame(caminho)
            hash_atual = imagehash.average_hash(frame_atual)

            distancia = hash_consulta - hash_atual
            if distancia < menor_distancia:
                menor_distancia = distancia
                melhor_match = arquivo

    return melhor_match, menor_distancia

# Execução principal
if __name__ == "__main__":
    caminho_captura = capturar_area_da_tela()
    resultado, dist = buscar_gif_similar(caminho_captura, "gifs")
    print(f"GIF mais parecido: {resultado} (distância: {dist})")
