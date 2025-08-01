from PIL import Image, ImageSequence
import imagehash
import pytesseract
import os
import pyautogui
import time
import re
import keyboard
import json
import tkinter as tk
from tkinter import Canvas, Button, Frame, Label, Text, Scrollbar
import threading
import queue
import io
import base64
import cv2
import numpy as np
import shutil

# Caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\gusta\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Captura de área com base no bbox
def capturar_area(bbox, salvar_como):
    screenshot = pyautogui.screenshot(region=bbox)
    screenshot.save(salvar_como)
    return salvar_como

# Pré-processa imagem para melhor comparação
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

# Carrega o primeiro frame do GIF
def carregar_primeiro_frame(caminho_imagem):
    with Image.open(caminho_imagem) as im:
        if getattr(im, "is_animated", False):
            frame = next(ImageSequence.Iterator(im)).convert("RGB")
        else:
            frame = im.convert("RGB")
        
        # Aplica pré-processamento
        return preprocessar_imagem(frame)

# Busca o GIF mais parecido
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

def buscar_top_matches(imagem_consulta, pasta_gifs, top_n=5):
    frame_consulta = carregar_primeiro_frame(imagem_consulta)
    hash_consulta = imagehash.average_hash(frame_consulta)
    
    matches = []
    
    for arquivo in os.listdir(pasta_gifs):
        if arquivo.lower().endswith(".gif"):
            caminho = os.path.join(pasta_gifs, arquivo)
            frame_atual = carregar_primeiro_frame(caminho)
            hash_atual = imagehash.average_hash(frame_atual)
            
            distancia = hash_consulta - hash_atual
            matches.append((caminho, distancia, arquivo))
    
    # Ordena por distância
    matches.sort(key=lambda x: x[1])
    
    return matches[:top_n]  # Retorna top 5

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
            # Aplica pré-processamento também nos frames
            # frame_atual = preprocessar_imagem(Image.open(caminho).convert("RGB"))
            frame_atual = (Image.open(caminho).convert("RGB"))
            
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
                gif_origem = arquivo.split("_frame_")[0] + ".gif"
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
            
            gif_origem = arquivo.split("_frame_")[0] + ".gif"
            matches.append((os.path.join("gifs", gif_origem), pontuacao, arquivo))
    
    matches.sort(key=lambda x: x[1])
    return matches[:top_n]


# OCR do nome
def extrair_texto(caminho_imagem):
    imagem = Image.open(caminho_imagem)
    texto = pytesseract.image_to_string(imagem, lang='por')
    return texto.strip()

# Limpa nome do arquivo
def limpar_nome_arquivo(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-zA-Z0-9 ]", "", texto)
    texto = "_".join(texto.split())
    return texto[:50]

# Captura pontos com clique do mouse
def capturar_bbox_com_cliques(descricao):
    pontos = []
    overlay_root = None
    mouse_listener = None
    key_listener = None
    
    def criar_overlay():
        """Cria uma janela semi-transparente sobre toda a tela"""
        nonlocal overlay_root
        overlay_root = tk.Tk()
        overlay_root.title(f"Selecionando área: {descricao}")
        
        # Pega as dimensões da tela
        screen_width = overlay_root.winfo_screenwidth()
        screen_height = overlay_root.winfo_screenheight()
        
        # Configura a janela para cobrir toda a tela
        overlay_root.geometry(f"{screen_width}x{screen_height}+0+0")
        overlay_root.attributes('-topmost', True)  # Sempre no topo
        overlay_root.attributes('-alpha', 0.4)     # Semi-transparente
        overlay_root.configure(bg='black')
        overlay_root.overrideredirect(True)  # Remove bordas da janela
        
        canvas = Canvas(overlay_root, width=screen_width, height=screen_height, 
                       bg='black', highlightthickness=0)
        canvas.pack()
        
        # Instruções na tela
        canvas.create_text(screen_width//2, 50, 
                          text=f"SELECIONANDO ÁREA: {descricao.upper()}", 
                          fill='white', font=('Arial', 24, 'bold'))
        canvas.create_text(screen_width//2, 100, 
                          text="🖱️ Clique no CANTO SUPERIOR ESQUERDO da área", 
                          fill='cyan', font=('Arial', 16, 'bold'))
        canvas.create_text(screen_width//2, 130, 
                          text="🖱️ Depois clique no CANTO INFERIOR DIREITO da área", 
                          fill='yellow', font=('Arial', 16, 'bold'))
        
        # Contador de cliques
        canvas.create_text(screen_width//2, screen_height - 100, 
                          text=f"Cliques restantes: 2", 
                          fill='lime', font=('Arial', 18, 'bold'), tags='contador')
        
        # Linha de fuga
        canvas.create_text(screen_width//2, screen_height - 50, 
                          text="Pressione ESC para cancelar", 
                          fill='red', font=('Arial', 12))
        
        return canvas

    def atualizar_contador(canvas, restantes):
        """Atualiza o contador de cliques na tela"""
        screen_width = canvas.winfo_width()
        screen_height = canvas.winfo_height()
        canvas.delete('contador')
        canvas.create_text(screen_width//2, screen_height - 100, 
                          text=f"Cliques restantes: {restantes}", 
                          fill='lime', font=('Arial', 18, 'bold'), tags='contador')
        if restantes == 1:
            canvas.delete('instrucao')
            canvas.create_text(screen_width//2, 130, 
                              text="🖱️ Agora clique no CANTO INFERIOR DIREITO da área", 
                              fill='yellow', font=('Arial', 16, 'bold'), tags='instrucao')

    def marcar_ponto(canvas, x, y, numero):
        """Marca visualmente um ponto clicado"""
        radius = 10
        cor = 'cyan' if numero == 1 else 'yellow'
        canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                          fill=cor, outline='white', width=3, tags='ponto')
        canvas.create_text(x, y-25, text=f"PONTO {numero}", 
                          fill=cor, font=('Arial', 12, 'bold'), tags='ponto')

    def parar_listeners():
        """Para todos os listeners"""
        nonlocal mouse_listener, key_listener
        try:
            if mouse_listener:
                mouse_listener.stop()
            if key_listener:
                key_listener.stop()
        except:
            pass

    def fechar_overlay():
        """Fecha a janela overlay"""
        parar_listeners()
        if overlay_root:
            overlay_root.quit()
            overlay_root.destroy()

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            print(f"Clique {len(pontos)+1} detectado em: x={x}, y={y}")
            pontos.append((x, y))
            
            # Marca o ponto visualmente
            if overlay_root:
                try:
                    canvas = overlay_root.children['!canvas']
                    marcar_ponto(canvas, x, y, len(pontos))
                    atualizar_contador(canvas, 2 - len(pontos))
                    overlay_root.update()
                except:
                    pass
            
            # Se temos 2 cliques, fecha após um delay
            if len(pontos) == 2:
                overlay_root.after(1000, fechar_overlay)

    def on_key(key):
        """Cancela a seleção com ESC"""
        try:
            if key == pynput_keyboard.Key.esc:
                print("Seleção cancelada pelo usuário")
                fechar_overlay()
        except:
            pass

    # Cria a janela overlay
    canvas = criar_overlay()
    
    print(f"\n🖱️ Clique duas vezes para marcar a área do {descricao}:")
    print("   1º clique: Canto superior esquerdo")
    print("   2º clique: Canto inferior direito")
    print("   ESC: Cancelar")
    
    # Configura os listeners
    mouse_listener = mouse.Listener(on_click=on_click)
    key_listener = pynput_keyboard.Listener(on_press=on_key)
    
    # Inicia os listeners
    mouse_listener.start()
    key_listener.start()
    
    # Protocol para fechar janela
    def on_closing():
        fechar_overlay()
    
    overlay_root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Loop principal do tkinter (substitui o mouse_listener.join())
    try:
        overlay_root.mainloop()
    except:
        pass
    finally:
        parar_listeners()
    
    # Verifica se temos os 2 pontos necessários
    if len(pontos) != 2:
        print("❌ Seleção cancelada ou incompleta")
        return None
    
    # Calcula o bounding box
    (x1, y1), (x2, y2) = pontos
    x_min, y_min = min(x1, x2), min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    bbox = (x_min, y_min, width, height)

    print(f"📦 Bounding box do {descricao}: {bbox}")
    return bbox

# Versão simplificada da captura usando apenas Tkinter
def capturar_bbox_com_cliques_tkinter(descricao):
    """Captura bbox usando apenas Tkinter - thread safe"""
    pontos = []
    resultado = None
    
    def criar_janela_captura():
        root = tk.Toplevel()
        root.title(f"Selecionando área: {descricao}")
        
        # Pega as dimensões da tela
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Configura a janela para cobrir toda a tela
        root.geometry(f"{screen_width}x{screen_height}+0+0")
        root.attributes('-topmost', True)
        root.attributes('-alpha', 0.4)
        root.configure(bg='black')
        root.overrideredirect(True)
        
        canvas = Canvas(root, width=screen_width, height=screen_height, 
                       bg='black', highlightthickness=0)
        canvas.pack()
        
        # Instruções na tela
        canvas.create_text(screen_width//2, 50, 
                          text=f"SELECIONANDO ÁREA: {descricao.upper()}", 
                          fill='white', font=('Arial', 24, 'bold'))
        canvas.create_text(screen_width//2, 100, 
                          text="🖱️ Clique no CANTO SUPERIOR ESQUERDO da área", 
                          fill='cyan', font=('Arial', 16, 'bold'))
        canvas.create_text(screen_width//2, 130, 
                          text="🖱️ Depois clique no CANTO INFERIOR DIREITO da área", 
                          fill='yellow', font=('Arial', 16, 'bold'))
        
        # Contador de cliques
        contador_id = canvas.create_text(screen_width//2, screen_height - 100, 
                          text="Cliques restantes: 2", 
                          fill='lime', font=('Arial', 18, 'bold'))
        
        # Linha de fuga
        canvas.create_text(screen_width//2, screen_height - 50, 
                          text="Pressione ESC para cancelar", 
                          fill='red', font=('Arial', 12))
        
        def atualizar_contador(restantes):
            canvas.itemconfig(contador_id, text=f"Cliques restantes: {restantes}")
            
        def marcar_ponto(x, y, numero):
            radius = 10
            cor = 'cyan' if numero == 1 else 'yellow'
            canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                              fill=cor, outline='white', width=3)
            canvas.create_text(x, y-25, text=f"PONTO {numero}", 
                              fill=cor, font=('Arial', 12, 'bold'))
        
        def on_click(event):
            nonlocal pontos, resultado
            print(f"Clique {len(pontos)+1} detectado em: x={event.x}, y={event.y}")
            pontos.append((event.x, event.y))
            
            marcar_ponto(event.x, event.y, len(pontos))
            atualizar_contador(2 - len(pontos))
            
            if len(pontos) == 2:
                # Calcula o bounding box
                (x1, y1), (x2, y2) = pontos
                x_min, y_min = min(x1, x2), min(y1, y2)
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                resultado = (x_min, y_min, width, height)
                
                # Fecha após 1 segundo
                root.after(1000, root.destroy)
        
        def on_key(event):
            nonlocal resultado
            if event.keysym == 'Escape':
                print("Seleção cancelada pelo usuário")
                resultado = None
                root.destroy()
        
        # Bind dos eventos
        canvas.bind("<Button-1>", on_click)
        root.bind("<Key>", on_key)
        root.focus_set()
        
        return root
    
    # Cria e executa a janela
    janela = criar_janela_captura()
    janela.wait_window()  # Aguarda a janela ser fechada
    
    if resultado:
        print(f"📦 Bounding box do {descricao}: {resultado}")
    else:
        print("❌ Seleção cancelada ou incompleta")
    
    return resultado

# Nova função para mostrar os pontos (simplificada)
def mostrar_pontos_captura(area_texto, area_imagem):
    """Mostra os pontos de captura usando Tkinter puro"""
    root = tk.Toplevel()
    root.title("Áreas de Captura")
    
    # Configurações da janela
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.3)
    root.configure(bg='black')
    root.overrideredirect(True)
    
    canvas = Canvas(root, width=screen_width, height=screen_height, 
                   bg='black', highlightthickness=0)
    canvas.pack()
    
    # Função para desenhar área
    def desenhar_area(bbox, cor, label):
        x, y, width, height = bbox
        
        # Retângulo
        canvas.create_rectangle(x, y, x + width, y + height, 
                              outline=cor, width=3, fill='')
        
        # 4 pontos nos cantos
        radius = 8
        pontos = [
            (x, y),  # Superior esquerdo
            (x + width, y),  # Superior direito
            (x, y + height),  # Inferior esquerdo
            (x + width, y + height)  # Inferior direito
        ]
        
        for px, py in pontos:
            canvas.create_oval(px-radius, py-radius, px+radius, py+radius, 
                              fill=cor, outline='white', width=2)
        
        # Label
        canvas.create_text(x + width//2, y - 20, text=label, 
                          fill=cor, font=('Arial', 14, 'bold'))
    
    # Desenha as áreas
    desenhar_area(area_texto, 'cyan', 'ÁREA DO TEXTO')
    desenhar_area(area_imagem, 'yellow', 'ÁREA DA IMAGEM')
    
    # Instruções
    canvas.create_text(screen_width//2, 50, 
                      text="ÁREAS DE CAPTURA CONFIGURADAS", 
                      fill='white', font=('Arial', 20, 'bold'))
    canvas.create_text(screen_width//2, 80, 
                      text="Pressione qualquer tecla para fechar", 
                      fill='white', font=('Arial', 12))
    
    # Coordenadas detalhadas
    info_y = screen_height - 100
    canvas.create_text(20, info_y, anchor='w',
                      text=f"🔵 TEXTO: x={area_texto[0]}, y={area_texto[1]}, w={area_texto[2]}, h={area_texto[3]}", 
                      fill='cyan', font=('Arial', 12, 'bold'))
    canvas.create_text(20, info_y + 25, anchor='w',
                      text=f"🟡 IMAGEM: x={area_imagem[0]}, y={area_imagem[1]}, w={area_imagem[2]}, h={area_imagem[3]}", 
                      fill='yellow', font=('Arial', 12, 'bold'))
    
    # Fecha com qualquer tecla
    def fechar(event):
        root.destroy()
    
    root.bind('<Key>', fechar)
    root.focus_set()
    
    # Auto-fechar após 5 segundos
    root.after(2000, root.destroy)
    
    root.wait_window()  # Aguarda fechar

# Classe da janela de controle com logs
class JanelaControle:
    def __init__(self, area_texto, area_imagem):
        self.area_texto = area_texto
        self.area_imagem = area_imagem
        self.root = tk.Tk()
        self.setup_janela()
        
    def setup_janela(self):
        """Configura a janela de controle"""
        self.root.title("🎯 ImageHash Control")
        self.root.geometry("500x650")
        
        # Posição no canto superior direito
        screen_width = self.root.winfo_screenwidth()
        x = screen_width - 520
        y = 50
        self.root.geometry(f"500x650+{x}+{y}")
        
        # Configurações da janela
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#2d2d2d')
        self.root.resizable(True, True)
        
        # Frame principal
        main_frame = Frame(self.root, bg='#2d2d2d', padx=10, pady=10)
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = Label(main_frame, text="🎯 ImageHash Control", 
                           font=('Arial', 14, 'bold'), 
                           fg='white', bg='#2d2d2d')
        title_label.pack(pady=(0, 15))
        
        # Frame dos botões principais
        buttons_frame = Frame(main_frame, bg='#2d2d2d')
        buttons_frame.pack(fill='x', pady=(0, 10))
        
        # Botão Capturar Automático
        self.btn_capturar_auto = Button(buttons_frame, text="🤖 AUTO", 
                                       command=self.capturar_auto_clicked,
                                       font=('Arial', 9, 'bold'),
                                       bg='#4CAF50', fg='white',
                                       width=12, height=2,
                                       relief='raised', bd=3)
        self.btn_capturar_auto.pack(side='left', padx=2)
        
        # Botão Capturar Manual
        self.btn_capturar_manual = Button(buttons_frame, text="👤 MANUAL", 
                                         command=self.capturar_manual_clicked,
                                         font=('Arial', 9, 'bold'),
                                         bg='#2196F3', fg='white',
                                         width=12, height=2,
                                         relief='raised', bd=3)
        self.btn_capturar_manual.pack(side='left', padx=2)
        
        # Botão Visualizar
        self.btn_visualizar = Button(buttons_frame, text="👁️ VER", 
                                    command=self.visualizar_clicked,
                                    font=('Arial', 9, 'bold'),
                                    bg='#9C27B0', fg='white',
                                    width=12, height=2,
                                    relief='raised', bd=3)
        self.btn_visualizar.pack(side='left', padx=2)
        
        # Botão Reconfigurar
        self.btn_reconfig = Button(buttons_frame, text="⚙️ CONFIG", 
                                  command=self.reconfigurar_clicked,
                                  font=('Arial', 9, 'bold'),
                                  bg='#FF9800', fg='white',
                                  width=12, height=2,
                                  relief='raised', bd=3)
        self.btn_reconfig.pack(side='left', padx=2)
        
        # Legenda dos botões
        legenda_frame = Frame(main_frame, bg='#2d2d2d')
        legenda_frame.pack(fill='x', pady=(0, 10))
        
        Label(legenda_frame, text="🤖 AUTO: Seleciona automaticamente o melhor match", 
              font=('Arial', 8), fg='#888888', bg='#2d2d2d').pack(anchor='w')
        Label(legenda_frame, text="👤 MANUAL: Mostra top 5 para você escolher", 
              font=('Arial', 8), fg='#888888', bg='#2d2d2d').pack(anchor='w')
        
        # Status
        self.status_label = Label(main_frame, text="Aguardando comando...", 
                                 font=('Arial', 10, 'bold'), 
                                 fg='#00ff00', bg='#2d2d2d')
        self.status_label.pack(pady=(0, 10))
        
        # Separador
        separator = Frame(main_frame, height=2, bg='#555555')
        separator.pack(fill='x', pady=5)
        
        # Label dos logs
        log_label = Label(main_frame, text="📋 LOGS DO SISTEMA", 
                         font=('Arial', 12, 'bold'), 
                         fg='white', bg='#2d2d2d')
        log_label.pack(pady=(10, 5))
        
        # Frame para a área de logs
        log_frame = Frame(main_frame, bg='#2d2d2d')
        log_frame.pack(fill='both', expand=True)
        
        # Área de texto para logs com scrollbar
        self.log_text = Text(log_frame, 
                            bg='#1e1e1e', 
                            fg='#ffffff',
                            font=('Consolas', 9),
                            wrap='word',
                            state='disabled',
                            height=20)
        
        # Scrollbar para os logs
        scrollbar = Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Pack da área de logs
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Frame dos botões inferiores
        bottom_frame = Frame(main_frame, bg='#2d2d2d')
        bottom_frame.pack(fill='x', pady=(10, 0))
        
        # Botão Limpar Logs
        btn_clear = Button(bottom_frame, text="🗑️ LIMPAR LOGS", 
                          command=self.limpar_logs,
                          font=('Arial', 9),
                          bg='#607D8B', fg='white',
                          width=15, height=1)
        btn_clear.pack(side='left')
        
        # Botão Fechar
        btn_fechar = Button(bottom_frame, text="❌ FECHAR", 
                           command=self.fechar_clicked,
                           font=('Arial', 9, 'bold'),
                           bg='#f44336', fg='white',
                           width=15, height=1)
        btn_fechar.pack(side='right')
        
        # Configuração de cores para os logs
        self.log_text.tag_configure("info", foreground="#00ff00")
        self.log_text.tag_configure("warning", foreground="#ffaa00")
        self.log_text.tag_configure("error", foreground="#ff0000")
        self.log_text.tag_configure("success", foreground="#00ffaa")
        self.log_text.tag_configure("process", foreground="#00aaff")
        
        # Protocol de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.fechar_clicked)
        
        # Log inicial
        self.adicionar_log("🎮 Interface de controle iniciada", "info")
        self.adicionar_log(f"📍 Área do texto: {self.area_texto}", "info")
        self.adicionar_log(f"📍 Área da imagem: {self.area_imagem}", "info")
        
    def adicionar_log(self, mensagem, tipo="info"):
        """Adiciona uma mensagem aos logs com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {mensagem}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert('end', log_message, tipo)
        self.log_text.config(state='disabled')
        self.log_text.see('end')
        self.root.update()
        
    def limpar_logs(self):
        """Limpa a área de logs"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.config(state='disabled')
        self.adicionar_log("🗑️ Logs limpos", "info")
        
    def atualizar_status(self, texto, cor="#00ff00"):
        """Atualiza o status"""
        self.status_label.config(text=texto, fg=cor)
        self.root.update()
        
    def capturar_auto_clicked(self):
        """Executa a captura automática"""
        self.btn_capturar_auto.config(state='disabled')
        self.btn_capturar_manual.config(state='disabled')
        self.atualizar_status("🤖 Processando automaticamente...", "#ffaa00")
        self.adicionar_log("🤖 Iniciando captura automática...", "process")
        
        try:
            processar(self.area_texto, self.area_imagem, self, modo="auto")
        except Exception as e:
            error_msg = f"❌ Erro: {str(e)}"
            self.atualizar_status(error_msg[:50] + "...", "#ff0000")
            self.adicionar_log(error_msg, "error")
        finally:
            self.btn_capturar_auto.config(state='normal')
            self.btn_capturar_manual.config(state='normal')
            
    def capturar_manual_clicked(self):
        """Executa a captura manual"""
        self.btn_capturar_auto.config(state='disabled')
        self.btn_capturar_manual.config(state='disabled')
        self.atualizar_status("👤 Processando manualmente...", "#ffaa00")
        self.adicionar_log("👤 Iniciando captura manual...", "process")
        
        try:
            processar(self.area_texto, self.area_imagem, self, modo="manual")
        except Exception as e:
            error_msg = f"❌ Erro: {str(e)}"
            self.atualizar_status(error_msg[:50] + "...", "#ff0000")
            self.adicionar_log(error_msg, "error")
        finally:
            self.btn_capturar_auto.config(state='normal')
            self.btn_capturar_manual.config(state='normal')
            
    def visualizar_clicked(self):
        """Mostra as áreas de captura"""
        self.atualizar_status("👁️ Mostrando áreas...", "#00aaff")
        self.adicionar_log("👁️ Exibindo áreas de captura", "info")
        mostrar_pontos_captura(self.area_texto, self.area_imagem)
        self.atualizar_status("Aguardando comando...")
        
    def reconfigurar_clicked(self):
        """Reconfigura as áreas de captura"""
        self.btn_reconfig.config(state='disabled')
        self.atualizar_status("⚙️ Reconfigurando...", "#ffaa00")
        self.adicionar_log("⚙️ Iniciando reconfiguração das áreas", "process")
        
        try:
            # Captura nova área do texto
            self.adicionar_log("📝 Configurando área do texto...", "process")
            nova_area_texto = capturar_bbox_com_cliques_tkinter("texto do nome")
            if nova_area_texto is None:
                self.atualizar_status("❌ Reconfiguração cancelada", "#ff0000")
                self.adicionar_log("❌ Configuração do texto cancelada", "warning")
                return
            
            # Captura nova área da imagem
            self.adicionar_log("🖼️ Configurando área da imagem...", "process")
            nova_area_imagem = capturar_bbox_com_cliques_tkinter("imagem do exercício")
            if nova_area_imagem is None:
                self.atualizar_status("❌ Reconfiguração cancelada", "#ff0000")
                self.adicionar_log("❌ Configuração da imagem cancelada", "warning")
                return
            
            # Atualiza as áreas
            self.area_texto = nova_area_texto
            self.area_imagem = nova_area_imagem
            
            # Salva as novas coordenadas
            with open("coords.txt", "w") as f:
                json.dump({"area_texto": self.area_texto, "area_imagem": self.area_imagem}, f)
            
            self.atualizar_status("✅ Áreas reconfiguradas!", "#00ffaa")
            self.adicionar_log("✅ Áreas reconfiguradas com sucesso", "success")
            self.adicionar_log(f"📍 Nova área do texto: {self.area_texto}", "info")
            self.adicionar_log(f"📍 Nova área da imagem: {self.area_imagem}", "info")
            
        except Exception as e:
            error_msg = f"❌ Erro na reconfiguração: {str(e)}"
            self.atualizar_status("❌ Erro na reconfiguração", "#ff0000")
            self.adicionar_log(error_msg, "error")
        finally:
            self.btn_reconfig.config(state='normal')
            
    def fechar_clicked(self):
        """Fecha a aplicação"""
        self.adicionar_log("👋 Fechando aplicação...", "info")
        self.root.quit()
        self.root.destroy()
        
    def executar(self):
        """Inicia o loop principal da janela"""
        self.root.mainloop()

# ================================
# Função principal do processo (atualizada)
# ================================
def processar(area_texto, area_imagem, janela_controle=None, modo="auto"):
    if janela_controle:
        janela_controle.atualizar_status("📸 Capturando imagem...")
        janela_controle.adicionar_log("⏺️ Capturando imagem do exercício...", "process")
    print("\n⏺️ Capturando imagem do exercício...")
    imagem_capturada = capturar_area(area_imagem, "imagem.png")

    if janela_controle:
        janela_controle.atualizar_status("🔡 Capturando texto...")
        janela_controle.adicionar_log("🔡 Capturando nome do exercício...", "process")
    print("🔡 Capturando nome do exercício...")
    texto_capturado = capturar_area(area_texto, "texto.png")

    if janela_controle:
        janela_controle.atualizar_status("🧠 Extraindo texto...")
        janela_controle.adicionar_log("🧠 Extraindo texto...", "process")
    print("🧠 Extraindo texto...")
    texto_extraido = extrair_texto(texto_capturado)
    print("📝 Texto extraído:", texto_extraido)
    
    if janela_controle:
        janela_controle.adicionar_log(f"📝 Texto extraído: {texto_extraido}", "info")

    # Busca baseada no modo
    if modo == "manual":
        if janela_controle:
            janela_controle.atualizar_status("🔍 Buscando top 5 matches...", "#00aaff")
            janela_controle.adicionar_log("🔍 Buscando top 5 GIFs mais parecidos...", "process")
        print("🔍 Buscando top 5 GIFs mais parecidos...")
        
        top_matches = buscar_top_matches_frames(imagem_capturada, "frames_extraidos", 5)
        
        if not top_matches:
            if janela_controle:
                janela_controle.atualizar_status("❌ Nenhum GIF encontrado", "#ff0000")
                janela_controle.adicionar_log("❌ Nenhum GIF encontrado na pasta", "error")
            return
        
        if janela_controle:
            janela_controle.adicionar_log(f"✅ Encontrados {len(top_matches)} matches", "success")
            janela_controle.atualizar_status("👤 Aguardando seleção manual...", "#ffaa00")
            
        # Abre janela de seleção
        janela_selecao = JanelaSelecaoGIF(top_matches, imagem_capturada, janela_controle.root)
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
        print("🔍 Buscando GIF mais parecido...")
        resultado, dist = buscar_gif_similar_frames(imagem_capturada, "frames_extraidos")
    
    # Processamento do resultado
    if resultado:
        gif_nome = os.path.basename(resultado)
        print(f"🎯 GIF selecionado: {gif_nome} (distância: {dist})")
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
                shutil.move(resultado, novo_caminho)
                print(f"✅ GIF copiado para: ./identificados/{novo_nome}")
                if janela_controle:
                    janela_controle.atualizar_status(f"✅ Copiado: {novo_nome[:20]}...", "#00ffaa")
                    janela_controle.adicionar_log(f"✅ GIF copiado para: ./identificados/{novo_nome}", "success")
            else:
                print(f"⚠️ Arquivo './identificados/{novo_nome}' já existe.")
                if janela_controle:
                    janela_controle.atualizar_status("⚠️ Arquivo já existe", "#ffaa00")
                    janela_controle.adicionar_log(f"⚠️ Arquivo './identificados/{novo_nome}' já existe", "warning")
        else:
            if janela_controle:
                janela_controle.atualizar_status("❌ Texto não extraído", "#ff0000")
                janela_controle.adicionar_log("❌ Nenhum texto foi extraído", "error")
    else:
        print("❌ Nenhum GIF encontrado")
        if janela_controle:
            janela_controle.atualizar_status("❌ Nenhum GIF encontrado", "#ff0000")
            janela_controle.adicionar_log("❌ Nenhum GIF encontrado na pasta", "error")

    # Volta ao status padrão após 3 segundos
    if janela_controle:
        def reset_status():
            janela_controle.atualizar_status("Aguardando comando...")
        janela_controle.root.after(3000, reset_status)

# Nova janela para seleção manual dos GIFs
class JanelaSelecaoGIF:
    def __init__(self, top_matches, imagem_capturada, parent=None):
        self.top_matches = top_matches
        self.imagem_capturada = imagem_capturada
        self.gif_selecionado = None
        self.parent = parent
        self.root = tk.Toplevel() if parent else tk.Tk()
        self.setup_janela()
        
    def setup_janela(self):
        """Configura a janela de seleção"""
        self.root.title("🎯 Seleção Manual de GIF")
        self.root.geometry("800x600")
        self.root.configure(bg='#2d2d2d')
        self.root.attributes('-topmost', True)
        
        # Centraliza a janela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")
        
        # Frame principal
        main_frame = Frame(self.root, bg='#2d2d2d', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = Label(main_frame, text="🎯 SELECIONE O GIF CORRETO", 
                           font=('Arial', 16, 'bold'), 
                           fg='white', bg='#2d2d2d')
        title_label.pack(pady=(0, 20))
        
        # Frame para a imagem capturada
        capture_frame = Frame(main_frame, bg='#2d2d2d')
        capture_frame.pack(fill='x', pady=(0, 20))
        
        Label(capture_frame, text="📸 IMAGEM CAPTURADA:", 
              font=('Arial', 12, 'bold'), fg='cyan', bg='#2d2d2d').pack()
        
        try:
            # Carrega e redimensiona a imagem capturada
            img_cap = Image.open(self.imagem_capturada)
            img_cap.thumbnail((200, 150), Image.Resampling.LANCZOS)
            
            # Converte para PhotoImage usando método interno
            self.photo_capturada = self.pil_to_photoimage(img_cap)
            
            canvas_cap = Canvas(capture_frame, width=200, height=150, bg='black')
            canvas_cap.pack()
            canvas_cap.create_image(100, 75, image=self.photo_capturada)
            
        except Exception as e:
            Label(capture_frame, text=f"❌ Erro ao carregar imagem: {str(e)}", 
                  fg='red', bg='#2d2d2d').pack()
        
        # Separador
        separator = Frame(main_frame, height=2, bg='#555555')
        separator.pack(fill='x', pady=10)
        
        # Frame para os matches
        matches_label = Label(main_frame, text="🏆 TOP 5 MATCHES ENCONTRADOS:", 
                             font=('Arial', 12, 'bold'), fg='yellow', bg='#2d2d2d')
        matches_label.pack(pady=(0, 10))
        
        # Canvas e scrollbar para os matches
        canvas_frame = Frame(main_frame, bg='#2d2d2d')
        canvas_frame.pack(fill='both', expand=True)
        
        self.canvas_scroll = Canvas(canvas_frame, bg='#2d2d2d', highlightthickness=0)
        scrollbar = Scrollbar(canvas_frame, orient="vertical", command=self.canvas_scroll.yview)
        self.scrollable_frame = Frame(self.canvas_scroll, bg='#2d2d2d')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))
        )
        
        self.canvas_scroll.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        # Adiciona os matches
        self.criar_matches()
        
        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botões inferiores
        button_frame = Frame(main_frame, bg='#2d2d2d')
        button_frame.pack(fill='x', pady=(20, 0))
        
        Button(button_frame, text="❌ CANCELAR", command=self.cancelar,
               font=('Arial', 10, 'bold'), bg='#f44336', fg='white',
               width=15, height=2).pack(side='left')
        
        Button(button_frame, text="🔄 BUSCAR NOVAMENTE", command=self.buscar_novamente,
               font=('Arial', 10, 'bold'), bg='#FF9800', fg='white',
               width=20, height=2).pack(side='right')
        
        # Protocol de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.cancelar)
        
    def pil_to_photoimage(self, pil_image):
        """Converte PIL Image para PhotoImage do Tkinter"""
        # Salva a imagem em buffer de memória
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Carrega como PhotoImage
        return tk.PhotoImage(data=buffer.getvalue())
        
    def criar_matches(self):
        """Cria os cards dos matches"""
        for i, (caminho, distancia, arquivo) in enumerate(self.top_matches):
            # Frame do match
            match_frame = Frame(self.scrollable_frame, bg='#3d3d3d', relief='raised', bd=2)
            match_frame.pack(fill='x', padx=10, pady=5)
            
            # Frame interno
            inner_frame = Frame(match_frame, bg='#3d3d3d', padx=15, pady=10)
            inner_frame.pack(fill='both', expand=True)
            
            # Ranking e distância
            rank_text = f"#{i+1} - Distância: {distancia}"
            rank_colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#4CAF50', '#2196F3']
            rank_color = rank_colors[i] if i < len(rank_colors) else '#FFFFFF'
            
            Label(inner_frame, text=rank_text, font=('Arial', 11, 'bold'),
                  fg=rank_color, bg='#3d3d3d').pack(anchor='w')
            
            # Nome do arquivo
            Label(inner_frame, text=f"📁 {arquivo}", font=('Arial', 10),
                  fg='white', bg='#3d3d3d').pack(anchor='w', pady=(2, 5))
            
            # Frame para preview e botão
            content_frame = Frame(inner_frame, bg='#3d3d3d')
            content_frame.pack(fill='x')
            
            # Preview do GIF (primeiro frame)
            try:
                img_preview = carregar_primeiro_frame(caminho)
                img_preview.thumbnail((120, 90), Image.Resampling.LANCZOS)
                
                # Converte para PhotoImage
                photo = self.pil_to_photoimage(img_preview)
                
                preview_canvas = Canvas(content_frame, width=120, height=90, bg='black')
                preview_canvas.pack(side='left', padx=(0, 15))
                preview_canvas.create_image(60, 45, image=photo)
                
                # Guarda referência da imagem para evitar garbage collection
                preview_canvas.image = photo
                
            except Exception as e:
                Label(content_frame, text="❌ Preview\nindisponível", 
                      fg='red', bg='#3d3d3d', width=15, height=4).pack(side='left', padx=(0, 15))
            
            # Botão selecionar
            btn_selecionar = Button(content_frame, 
                                   text=f"✅ SELECIONAR\nESTE GIF",
                                   command=lambda c=caminho, d=distancia: self.selecionar_gif(c, d),
                                   font=('Arial', 10, 'bold'),
                                   bg='#4CAF50', fg='white',
                                   width=15, height=3)
            btn_selecionar.pack(side='right')
            
            # Tooltip com caminho completo
            self.criar_tooltip(btn_selecionar, f"Caminho: {caminho}")
    
    def criar_tooltip(self, widget, text):
        """Cria tooltip para o widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = Label(tooltip, text=text, background='yellow', 
                         font=('Arial', 8), relief='solid', borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def selecionar_gif(self, caminho, distancia):
        """Seleciona um GIF"""
        self.gif_selecionado = (caminho, distancia)
        self.root.destroy()
        
    def cancelar(self):
        """Cancela a seleção"""
        self.gif_selecionado = None
        self.root.destroy()
        
    def buscar_novamente(self):
        """Fecha e permite nova busca"""
        self.gif_selecionado = "retry"
        self.root.destroy()
        
    def obter_selecao(self):
        """Retorna a seleção do usuário"""
        self.root.wait_window()
        return self.gif_selecionado

# ===================================
# Código principal (simplificado)
# ===================================
if __name__ == "__main__":
    resposta = input("\nDeseja capturar as áreas do nome e imagem do exercício? (s/n): ")
    if resposta.lower() == "s":
        print("\n🎯 Modo de captura de áreas ativado!")
        print("💡 Dica: Posicione a janela do exercício visível antes de começar")
        input("Pressione ENTER para começar a capturar a área do TEXTO...")
        
        # Cria uma janela root temporária para as capturas
        temp_root = tk.Tk()
        temp_root.withdraw()  # Esconde a janela
        
        area_texto = capturar_bbox_com_cliques_tkinter("texto do nome")
        if area_texto is None:
            print("❌ Captura do texto cancelada. Usando valores padrão.")
            area_texto = (100, 100, 300, 50)
        
        print("\n🎯 Agora vamos capturar a área da IMAGEM do exercício...")
        input("Pressione ENTER para continuar...")
        
        area_imagem = capturar_bbox_com_cliques_tkinter("imagem do exercício")
        if area_imagem is None:
            print("❌ Captura da imagem cancelada. Usando valores padrão.")
            area_imagem = (100, 200, 400, 300)
        
        temp_root.destroy()  # Destrói a janela temporária
        
        # Salva as coordenadas
        with open("coords.txt", "w") as f:
            json.dump({"area_texto": area_texto, "area_imagem": area_imagem}, f)
        print("✅ Coordenadas salvas em coords.txt")
    else:
        # Carrega coordenadas existentes
        try:
            with open("coords.txt", "r") as f:
                coords = json.load(f)
                area_texto = tuple(coords["area_texto"])
                area_imagem = tuple(coords["area_imagem"])
            print("✅ Coordenadas carregadas de coords.txt")
        except Exception:
            area_texto = (100, 100, 300, 50)
            area_imagem = (100, 200, 400, 300)
            print("⚠️ Usando coordenadas padrão")

    # Mostra as áreas configuradas
    print("\n👁️ Mostrando áreas de captura na tela...")
    temp_root = tk.Tk()
    temp_root.withdraw()
    mostrar_pontos_captura(area_texto, area_imagem)
    temp_root.destroy()

    # Inicia a janela de controle
    print("\n🎮 Iniciando interface de controle...")
    janela_controle = JanelaControle(area_texto, area_imagem)
    janela_controle.executar()
