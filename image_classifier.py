from PIL import Image, ImageSequence
import imagehash
import pytesseract
import os
import pyautogui
import time
import re
import json
import tkinter as tk
from tkinter import Canvas
import io
import cv2
import numpy as np
import shutil
from unidecode import unidecode

# Caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\gusta\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Captura de área com base no bbox
def capturar_area(bbox, salvar_como):
    screenshot = pyautogui.screenshot(region=bbox)
    screenshot.save(salvar_como)
    return salvar_como

# OCR do nome
def extrair_texto(caminho_imagem):
    imagem = Image.open(caminho_imagem)
    texto = pytesseract.image_to_string(imagem, lang='por')
    return texto.strip()

# Limpa nome do arquivo
def limpar_nome_arquivo(texto):
    texto = unidecode(texto)
    texto = texto.lower()
    texto = re.sub(r"[^a-zA-Z0-9 ]", "", texto)
    texto = "_".join(texto.split())
    return texto[:50]

#! Pré-processa imagem para melhor comparação
def preprocessar_imagem(imagem):
    # Converte PIL para numpy array
    img_array = np.array(imagem)
    
    # Redimensiona para tamanho padrão
    img_resized = cv2.resize(img_array, (256, 256))
    
    # Converte para escala de cinza
    if len(img_resized.shape) == 3:
        img_gray = cv2.cvtColor(img_resized, cv2.COLOR_RGB2GRAY)
    else:
        img_gray = img_resized
    
    # Equalização do histograma
    img_eq = cv2.equalizeHist(img_gray)
    
    # Filtro gaussiano para suavizar
    img_blur = cv2.GaussianBlur(img_eq, (3, 3), 0)
    
    # Converte de volta para PIL
    return Image.fromarray(img_blur)

#! Carrega o primeiro frame do GIF ou a imagem
def carregar_primeiro_frame(caminho_imagem):
    with Image.open(caminho_imagem) as im:
        if getattr(im, "is_animated", False):
            frame = next(ImageSequence.Iterator(im)).convert("RGB")
        else:
            frame = im.convert("RGB")
        
        # Aplica pré-processamento
        return preprocessar_imagem(frame)

def buscar_gif_similar_frames(imagem_consulta, pasta_frames):
    """Busca usando frames extraídos com múltiplos hashes"""
    frame_consulta = carregar_primeiro_frame(imagem_consulta)
    
    # Múltiplos hashes para maior precisão
    hash_avg = imagehash.average_hash(frame_consulta, hash_size=16)
    hash_phash = imagehash.phash(frame_consulta, hash_size=16)  # Melhor para rotações/escalas
    hash_dhash = imagehash.dhash(frame_consulta, hash_size=16)  # Melhor para gradientes
    
    melhor_match = None
    menor_pontuacao = float("inf")
    
    for arquivo in os.listdir(pasta_frames):
        if arquivo.lower().endswith(".png"):
            caminho = os.path.join(pasta_frames, arquivo)
            frame_atual = Image.open(caminho).convert("RGB")
            
            # Calcula múltiplos hashes
            atual_avg = imagehash.average_hash(frame_atual, hash_size=16)
            atual_phash = imagehash.phash(frame_atual, hash_size=16)
            atual_dhash = imagehash.dhash(frame_atual, hash_size=16)
            
            # Pontuação combinada (pesos ajustáveis)
            pontuacao = (
                (hash_avg - atual_avg) * 0.3 +      # Average hash
                (hash_phash - atual_phash) * 0.5 +  # Perceptual hash (melhor peso)
                (hash_dhash - atual_dhash) * 0.2    # Difference hash
            )
            
            if pontuacao < menor_pontuacao:
                menor_pontuacao = pontuacao
                
                # Obtem o nome do GIF original removendo o sufixo do frame
                gif_origem = arquivo.split("_frame_")[0] + ".gif"

                # Verifica se o GIF original existe
                caminho_gif = os.path.join("gifs", gif_origem)
                if os.path.exists(caminho_gif):
                    melhor_match = caminho_gif
                else:
                    print(f"⚠️ Arquivo não encontrado: {caminho_gif}")
    
    return melhor_match, menor_pontuacao

def buscar_top_matches_frames(imagem_consulta, pasta_frames, top_n=5):
    """Busca top matches com múltiplos hashes"""
    frame_consulta = carregar_primeiro_frame(imagem_consulta)
    
    hash_avg = imagehash.average_hash(frame_consulta, hash_size=16)
    hash_phash = imagehash.phash(frame_consulta, hash_size=16)
    hash_dhash = imagehash.dhash(frame_consulta, hash_size=16)
    
    matches = []
    
    for arquivo in os.listdir(pasta_frames):
        if arquivo.lower().endswith(".png"):
            caminho = os.path.join(pasta_frames, arquivo)
            frame_atual = Image.open(caminho).convert("RGB")
            
            atual_avg = imagehash.average_hash(frame_atual, hash_size=16)
            atual_phash = imagehash.phash(frame_atual, hash_size=16)
            atual_dhash = imagehash.dhash(frame_atual, hash_size=16)
            
            pontuacao = (
                (hash_avg - atual_avg) * 0.3 +
                (hash_phash - atual_phash) * 0.5 +
                (hash_dhash - atual_dhash) * 0.2
            )
            
            # Obtem o nome do GIF original removendo o sufixo do frame
            gif_origem = arquivo.split("_frame_")[0] + ".gif"
            matches.append((os.path.join("gifs", gif_origem), pontuacao, arquivo))
    
    matches.sort(key=lambda x: x[1])
    return matches[:top_n]

# Nova função para mostrar os pontos (simplificada)
def mostrar_pontos_captura(area_texto, area_imagem):
    """Mostra os pontos de captura usando Tkinter puro com funcionalidade de arrastar e redimensionar"""
    root = tk.Toplevel()
    root.title("Áreas de Captura - Arraste para mover, redimensione pelos vértices")
    
    # Configurações da janela
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.7)
    root.configure(bg='black')
    root.overrideredirect(True)
        
    canvas = Canvas(root, width=screen_width, height=screen_height, 
                   bg='black', highlightthickness=0)
    canvas.pack()
    
    # Variáveis para controle do arraste
    drag_data = {
        "x": 0, "y": 0, "item": None, "area_type": None, 
        "drag_mode": None,  # "move", "resize_corner", "resize_edge"
        "resize_type": None  # "tl", "tr", "bl", "br", "top", "bottom", "left", "right"
    }
    
    areas_atuais = {
        "texto": list(area_texto),
        "imagem": list(area_imagem)
    }
    
    # IDs dos elementos desenhados
    elementos = {"texto": [], "imagem": []}
    
    # Função para desenhar área com handles de redimensionamento
    def desenhar_area(bbox, cor, label, area_type):
        x, y, width, height = bbox
        
        # Limpa elementos anteriores desta área
        for item_id in elementos[area_type]:
            canvas.delete(item_id)
        elementos[area_type].clear()
        
        # Retângulo principal
        rect_id = canvas.create_rectangle(x, y, x + width, y + height, 
                                        outline=cor, width=3, fill='', 
                                        tags=(area_type, "movable"))
        elementos[area_type].append(rect_id)
        
        # Handles dos vértices (quadrados maiores)
        handle_size = 12
        handles = [
            # Vértices (corners)
            (x - handle_size//2, y - handle_size//2, "tl"),  # Top-left
            (x + width - handle_size//2, y - handle_size//2, "tr"),  # Top-right
            (x - handle_size//2, y + height - handle_size//2, "bl"),  # Bottom-left
            (x + width - handle_size//2, y + height - handle_size//2, "br"),  # Bottom-right
            
            # Arestas (retângulos menores)
            (x + width//2 - handle_size//2, y - handle_size//2, "top"),  # Top edge
            (x + width//2 - handle_size//2, y + height - handle_size//2, "bottom"),  # Bottom edge
            (x - handle_size//2, y + height//2 - handle_size//2, "left"),  # Left edge
            (x + width - handle_size//2, y + height//2 - handle_size//2, "right"),  # Right edge
        ]
        
        for hx, hy, resize_type in handles:
            if resize_type in ["tl", "tr", "bl", "br"]:
                # Vértices - quadrados
                handle_id = canvas.create_rectangle(hx, hy, hx + handle_size, hy + handle_size,
                                                  fill=cor, outline='white', width=2,
                                                  tags=(area_type, "resize_corner", resize_type))
            else:
                # Arestas - retângulos menores
                if resize_type in ["top", "bottom"]:
                    handle_id = canvas.create_rectangle(hx, hy, hx + handle_size, hy + handle_size//2,
                                                      fill=cor, outline='white', width=1,
                                                      tags=(area_type, "resize_edge", resize_type))
                else:  # left, right
                    handle_id = canvas.create_rectangle(hx, hy, hx + handle_size//2, hy + handle_size,
                                                      fill=cor, outline='white', width=1,
                                                      tags=(area_type, "resize_edge", resize_type))
            elementos[area_type].append(handle_id)
        
        # Label
        label_id = canvas.create_text(x + width//2, y - 25, text=label, 
                                    fill=cor, font=('Arial', 14, 'bold'),
                                    tags=(area_type, "movable"))
        elementos[area_type].append(label_id)
        
        return elementos[area_type]
    
    # Função para atualizar coordenadas na tela
    def atualizar_info_coordenadas():
        info_y = screen_height - 120
        
        # Remove textos antigos de coordenadas
        canvas.delete("coords_info")
        
        # Adiciona novas coordenadas
        canvas.create_text(20, info_y, anchor='w',
                          text=f"🔵 TEXTO: x={areas_atuais['texto'][0]}, y={areas_atuais['texto'][1]}, w={areas_atuais['texto'][2]}, h={areas_atuais['texto'][3]}", 
                          fill='cyan', font=('Arial', 12, 'bold'),
                          tags="coords_info")
        canvas.create_text(20, info_y + 25, anchor='w',
                          text=f"🟡 IMAGEM: x={areas_atuais['imagem'][0]}, y={areas_atuais['imagem'][1]}, w={areas_atuais['imagem'][2]}, h={areas_atuais['imagem'][3]}", 
                          fill='yellow', font=('Arial', 12, 'bold'),
                          tags="coords_info")
        
        # Instruções de uso
        canvas.create_text(20, info_y + 55, anchor='w',
                          text="🖱️ ARRASTAR área = mover | ARRASTAR vértices/arestas = redimensionar", 
                          fill='lime', font=('Arial', 10),
                          tags="coords_info")
    
    # Função para determinar o cursor baseado no tipo de handle
    def get_cursor(resize_type):
        cursor_map = {
            "tl": "top_left_corner",
            "tr": "top_right_corner", 
            "bl": "bottom_left_corner",
            "br": "bottom_right_corner",
            "top": "top_side",
            "bottom": "bottom_side",
            "left": "left_side",
            "right": "right_side"
        }
        return cursor_map.get(resize_type, "fleur")
    
    # Funções de arraste
    def start_drag(event):
        # Encontra qual elemento está sendo arrastado
        item = canvas.find_closest(event.x, event.y)[0]
        tags = canvas.gettags(item)
        
        if len(tags) < 2:
            return
            
        area_type = None
        if "texto" in tags:
            area_type = "texto"
        elif "imagem" in tags:
            area_type = "imagem"
        else:
            return
            
        drag_data["area_type"] = area_type
        drag_data["x"] = event.x
        drag_data["y"] = event.y
        drag_data["item"] = item
        
        # Determina o modo de arraste
        if "resize_corner" in tags:
            drag_data["drag_mode"] = "resize_corner"
            drag_data["resize_type"] = tags[-1]  # último tag é o tipo (tl, tr, etc.)
            canvas.config(cursor=get_cursor(drag_data["resize_type"]))
        elif "resize_edge" in tags:
            drag_data["drag_mode"] = "resize_edge"
            drag_data["resize_type"] = tags[-1]
            canvas.config(cursor=get_cursor(drag_data["resize_type"]))
        elif "movable" in tags:
            drag_data["drag_mode"] = "move"
            canvas.config(cursor="fleur")
    
    def drag(event):
        if not drag_data["area_type"]:
            return
            
        area_type = drag_data["area_type"]
        dx = event.x - drag_data["x"]
        dy = event.y - drag_data["y"]
        
        x, y, width, height = areas_atuais[area_type]
        
        if drag_data["drag_mode"] == "move":
            # Movimento da área toda
            areas_atuais[area_type][0] += dx
            areas_atuais[area_type][1] += dy
            
            # Limites da tela
            areas_atuais[area_type][0] = max(0, min(areas_atuais[area_type][0], 
                                                   screen_width - areas_atuais[area_type][2]))
            areas_atuais[area_type][1] = max(0, min(areas_atuais[area_type][1], 
                                                   screen_height - areas_atuais[area_type][3]))
            
        elif drag_data["drag_mode"] == "resize_corner":
            # Redimensionamento pelos vértices
            resize_type = drag_data["resize_type"]
            
            if resize_type == "tl":  # Top-left
                new_width = width - dx
                new_height = height - dy
                if new_width > 20 and new_height > 20:
                    areas_atuais[area_type] = [x + dx, y + dy, new_width, new_height]
            elif resize_type == "tr":  # Top-right
                new_width = width + dx
                new_height = height - dy
                if new_width > 20 and new_height > 20:
                    areas_atuais[area_type] = [x, y + dy, new_width, new_height]
            elif resize_type == "bl":  # Bottom-left
                new_width = width - dx
                new_height = height + dy
                if new_width > 20 and new_height > 20:
                    areas_atuais[area_type] = [x + dx, y, new_width, new_height]
            elif resize_type == "br":  # Bottom-right
                new_width = width + dx
                new_height = height + dy
                if new_width > 20 and new_height > 20:
                    areas_atuais[area_type] = [x, y, new_width, new_height]
                    
        elif drag_data["drag_mode"] == "resize_edge":
            # Redimensionamento pelas arestas
            resize_type = drag_data["resize_type"]
            
            if resize_type == "top":
                new_height = height - dy
                if new_height > 20:
                    areas_atuais[area_type] = [x, y + dy, width, new_height]
            elif resize_type == "bottom":
                new_height = height + dy
                if new_height > 20:
                    areas_atuais[area_type] = [x, y, width, new_height]
            elif resize_type == "left":
                new_width = width - dx
                if new_width > 20:
                    areas_atuais[area_type] = [x + dx, y, new_width, height]
            elif resize_type == "right":
                new_width = width + dx
                if new_width > 20:
                    areas_atuais[area_type] = [x, y, new_width, height]
        
        # Redesenha a área
        cor = 'cyan' if area_type == 'texto' else 'yellow'
        label = 'ÁREA DO TEXTO' if area_type == 'texto' else 'ÁREA DA IMAGEM'
        desenhar_area(areas_atuais[area_type], cor, label, area_type)
        
        # Atualiza as coordenadas mostradas
        atualizar_info_coordenadas()
        
        # Atualiza posição do mouse
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    
    def stop_drag(event):
        drag_data["area_type"] = None
        drag_data["item"] = None
        drag_data["drag_mode"] = None
        drag_data["resize_type"] = None
        canvas.config(cursor="")
    
    # Evento para mudança de cursor quando passa sobre handles
    def on_motion(event):
        if drag_data["area_type"]:  # Se está arrastando, não muda cursor
            return
            
        item = canvas.find_closest(event.x, event.y)[0]
        tags = canvas.gettags(item)
        
        if "resize_corner" in tags or "resize_edge" in tags:
            resize_type = tags[-1]
            canvas.config(cursor=get_cursor(resize_type))
        elif "movable" in tags:
            canvas.config(cursor="fleur")
        else:
            canvas.config(cursor="")
    
    # Desenha as áreas iniciais
    desenhar_area(areas_atuais["texto"], 'cyan', 'ÁREA DO TEXTO', "texto")
    desenhar_area(areas_atuais["imagem"], 'yellow', 'ÁREA DA IMAGEM', "imagem")
    
    # Instruções
    canvas.create_text(screen_width//2, 50, 
                      text="ÁREAS DE CAPTURA CONFIGURADAS", 
                      fill='white', font=('Arial', 20, 'bold'))
    canvas.create_text(screen_width//2, 80, 
                      text="🖱️ ARRASTE área = mover | ARRASTE vértices/arestas = redimensionar", 
                      fill='lime', font=('Arial', 14, 'bold'))
    canvas.create_text(screen_width//2, 110, 
                      text="Pressione ENTER para salvar ou ESC para fechar", 
                      fill='white', font=('Arial', 12))
    
    # Coordenadas detalhadas iniciais
    atualizar_info_coordenadas()
    
    # Variável para resultado
    resultado_salvo = False
    
    # Função para salvar coordenadas
    def salvar_coordenadas():
        nonlocal resultado_salvo
        resultado_salvo = True
        
        # Salva no arquivo coords.txt
        try:
            coords_para_salvar = {
                "area_texto": tuple(areas_atuais["texto"]),
                "area_imagem": tuple(areas_atuais["imagem"])
            }
            
            with open("coords.txt", "w") as f:
                json.dump(coords_para_salvar, f, indent=2)
            
            # Feedback visual
            canvas.create_text(screen_width//2, 150, 
                              text="✅ COORDENADAS SALVAS!", 
                              fill='lime', font=('Arial', 16, 'bold'))
            root.after(1500, root.destroy)
            
        except Exception as e:
            canvas.create_text(screen_width//2, 150, 
                              text=f"❌ ERRO AO SALVAR: {e}", 
                              fill='red', font=('Arial', 16, 'bold'))
    
    # Fecha com teclas específicas
    def on_key(event):
        if event.keysym == 'Return':  # ENTER - salva
            salvar_coordenadas()
        elif event.keysym == 'Escape':  # ESC - fecha sem salvar
            root.destroy()
    
    # Bind dos eventos
    canvas.bind("<Button-1>", start_drag)
    canvas.bind("<B1-Motion>", drag)
    canvas.bind("<ButtonRelease-1>", stop_drag)
    canvas.bind("<Motion>", on_motion)  # Para cursor hover
    root.bind('<Key>', on_key)
    root.focus_set()
    
    # Auto-fechar após 60 segundos
    root.after(60000, root.destroy)
    
    root.wait_window()  # Aguarda fechar
    
    # Retorna as coordenadas atuais se foram salvas
    if resultado_salvo:
        return {
            "area_texto": tuple(areas_atuais["texto"]),
            "area_imagem": tuple(areas_atuais["imagem"])
        }
    else:
        return None
# ================================
# Função principal do processo (atualizada)
# ================================
def processar(area_texto, area_imagem, janela_controle=None, modo="auto"):
    if janela_controle:
        janela_controle.atualizar_status("📸 Capturando imagem...")
        janela_controle.adicionar_log("⏺️ Capturando imagem...", "process")
    imagem_capturada = capturar_area(area_imagem, "imagem.png")

    if janela_controle:
        janela_controle.atualizar_status("🔡 Capturando texto...")
        janela_controle.adicionar_log("🔡 Capturando nome...", "process")
    texto_capturado = capturar_area(area_texto, "texto.png")

    if janela_controle:
        janela_controle.atualizar_status("🧠 Extraindo texto...")
        janela_controle.adicionar_log("🧠 Extraindo texto...", "process")
    texto_extraido = extrair_texto(texto_capturado)
    
    if janela_controle:
        janela_controle.adicionar_log(f"📝 Texto extraído: {texto_extraido}", "info")

    # Busca baseada no modo
    if modo == "manual":
        if janela_controle:
            janela_controle.atualizar_status("🔍 Buscando top 5 matches...", "#00aaff")
            janela_controle.adicionar_log("🔍 Buscando top 5 GIFs mais parecidos...", "process")
        
        top_matches = buscar_top_matches_frames(imagem_capturada, "frames_extraidos", 3)
        
        if not top_matches:
            if janela_controle:
                janela_controle.atualizar_status("❌ Nenhum GIF encontrado", "#ff0000")
                janela_controle.adicionar_log("❌ Nenhum GIF encontrado na pasta", "error")
            return
        
        if janela_controle:
            janela_controle.adicionar_log(f"✅ Encontrados {len(top_matches)} matches", "success")
            janela_controle.atualizar_status("👤 Aguardando seleção manual...", "#ffaa00")
            
        from janela_selecao import JanelaSelecaoGIF

        # Abre janela de seleção
        janela_selecao = JanelaSelecaoGIF(top_matches, imagem_capturada, 
                                          janela_controle.root if janela_controle else None,
                                          janela_controle)
        selecao = janela_selecao.obter_selecao()
        
        if selecao is None:
            if janela_controle:
                janela_controle.atualizar_status("❌ Seleção cancelada", "#ff0000")
                janela_controle.adicionar_log("❌ Usuário cancelou a seleção", "warning")
            return
        elif selecao == "retry":
            if janela_controle:
                janela_controle.atualizar_status("🔄 Nova busca solicitada", "#ffaa00")
                janela_controle.adicionar_log("🔄 Usuário solicitou nova busca", "info")
            return
        
        resultado, dist = selecao
        if janela_controle:
            janela_controle.adicionar_log(f"👤 Usuário selecionou: {os.path.basename(resultado)} (distância: {dist})", "success")
            
    else:  # modo automático
        if janela_controle:
            janela_controle.atualizar_status("🔍 Buscando GIF automaticamente...")
            janela_controle.adicionar_log("🔍 Buscando GIF mais parecido automaticamente...", "process")
        resultado, dist = buscar_gif_similar_frames(imagem_capturada, "frames_extraidos")
    
    # Processamento do resultado
    if resultado:
        gif_nome = os.path.basename(resultado)
        if janela_controle:
            janela_controle.adicionar_log(f"🎯 GIF selecionado: {gif_nome} (distância: {dist})", "success")

        if texto_extraido:
            pasta_identificados = "identificados"
            if not os.path.exists(pasta_identificados):
                os.makedirs(pasta_identificados)
                if janela_controle:
                    janela_controle.adicionar_log("📂 Pasta 'identificados' criada", "info")

            novo_nome = limpar_nome_arquivo(texto_extraido) + ".gif"
            novo_caminho = os.path.join(pasta_identificados, novo_nome)

            if not os.path.exists(novo_caminho):
                # os.rename(resultado, novo_caminho)
                shutil.copy(resultado, novo_caminho)
                if janela_controle:
                    janela_controle.atualizar_status(f"✅ Copiado: {novo_nome[:20]}...", "#00ffaa")
                    janela_controle.adicionar_log(f"✅ GIF copiado para: ./identificados/{novo_nome}", "success")
            else:
                if janela_controle:
                    janela_controle.atualizar_status("⚠️ Arquivo já existe", "#ffaa00")
                    janela_controle.adicionar_log(f"⚠️ Arquivo './identificados/{novo_nome}' já existe", "warning")
        else:
            if janela_controle:
                janela_controle.atualizar_status("❌ Texto não extraído", "#ff0000")
                janela_controle.adicionar_log("❌ Nenhum texto foi extraído", "error")
    else:
        if janela_controle:
            janela_controle.atualizar_status("❌ Nenhum GIF encontrado", "#ff0000")
            janela_controle.adicionar_log("❌ Nenhum GIF encontrado na pasta", "error")

    # Volta ao status padrão após 3 segundos
    if janela_controle:
        def reset_status():
            janela_controle.atualizar_status("Aguardando comando...")
        janela_controle.root.after(3000, reset_status)

# ===================================
# Código principal (simplificado)
# ===================================
if __name__ == "__main__":
    from janela_controle import JanelaControle

    try:
        with open("coords.txt", "r") as f:
            coords = json.load(f)
            area_texto = tuple(coords["area_texto"])
            area_imagem = tuple(coords["area_imagem"])
    except Exception:
        area_texto = (100, 100, 300, 50)
        area_imagem = (100, 200, 400, 300)
        print("⚠️ Usando coordenadas padrão")

    # Inicia a janela de controle
    janela_controle = JanelaControle(area_texto, area_imagem)
    janela_controle.executar()
