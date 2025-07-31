from PIL import Image, ImageSequence
import imagehash
import pytesseract
import os
import pyautogui
import time
import re
import keyboard  # <- Para capturar teclas

# Caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\gusta\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

def capturar_area(bbox, salvar_como):
    screenshot = pyautogui.screenshot(region=bbox)
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
                melhor_match = caminho

    return melhor_match, menor_distancia

def extrair_texto(caminho_imagem):
    imagem = Image.open(caminho_imagem)
    texto = pytesseract.image_to_string(imagem, lang='por')
    return texto.strip()

def limpar_nome_arquivo(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-zA-Z0-9 ]", "", texto)
    texto = "_".join(texto.split())
    return texto[:50]

# ================================
# Função principal do processo
# ================================
def processar():
    print("\n⏺️ Capturando imagem do exercício...")
    imagem_capturada = capturar_area((277, 457, 485, 377), "imagem.png")

    print("🔡 Capturando nome do exercício...")
    texto_capturado = capturar_area((261, 289, 369, 50), "texto.png")

    print("🧠 Extraindo texto...")
    texto_extraido = extrair_texto(texto_capturado)
    print("📝 Texto extraído:", texto_extraido)

    print("🔍 Buscando GIF mais parecido...")
    resultado, dist = buscar_gif_similar(imagem_capturada, "gifs")
    print(f"🎯 GIF mais parecido: {os.path.basename(resultado)} (distância: {dist})")

    if resultado and texto_extraido:
        novo_nome = limpar_nome_arquivo(texto_extraido) + ".gif"
        novo_caminho = os.path.join("gifs", novo_nome)

        if not os.path.exists(novo_caminho):
            os.rename(resultado, novo_caminho)
            print(f"✅ GIF renomeado para: {novo_nome}")
        else:
            print(f"⚠️ Arquivo com nome '{novo_nome}' já existe.")

# ================================
# Loop principal aguardando tecla
# ================================
print("💡 Pressione Ctrl + 0 a qualquer momento para capturar e renomear o GIF... (Ctrl + C para sair)")
while True:
    try:
        if keyboard.is_pressed('ctrl+0'):
            processar()
            time.sleep(1)  # Evita múltiplas execuções com um único pressionamento
    except KeyboardInterrupt:
        print("\nEncerrado.")
        break
