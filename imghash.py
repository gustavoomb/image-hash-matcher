from PIL import Image, ImageSequence
import imagehash
import os

def carregar_primeiro_frame(caminho_imagem):
    if caminho_imagem.lower().endswith(".gif"):
        with Image.open(caminho_imagem) as im:
            for frame in ImageSequence.Iterator(im):
                return frame.convert('RGB')
    else:
        with Image.open(caminho_imagem) as im:
            return im.convert('RGB')

def buscar_gif_similar(imagem_consulta, pasta_gifs):
    frame_consulta = carregar_primeiro_frame(imagem_consulta)
    hash_consulta = imagehash.average_hash(frame_consulta)

    melhor_match = None
    menor_distancia = float('inf')

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

# Execução automática
if __name__ == "__main__":
    imagem = "a.jpg"  # pode ser .jpg ou .gif
    resultado, dist = buscar_gif_similar(imagem, "gifs")
    print(f"GIF mais parecido: {resultado} (distância: {dist})")
