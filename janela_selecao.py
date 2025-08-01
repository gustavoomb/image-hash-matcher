import tkinter as tk
from tkinter import Canvas, Button, Frame, Label, Scrollbar
import io
import os
from PIL import Image, ImageTk

from janela_controle import JanelaControle


class JanelaSelecaoGIF:
    def __init__(self, top_matches, imagem_capturada, parent=None, janela_controle=None):
        self.top_matches = top_matches
        self.imagem_capturada = imagem_capturada
        self.gif_selecionado = None
        self.parent = parent
        self.janela_controle = janela_controle  # Usa a referência passada
        self.root = tk.Toplevel() if parent else tk.Tk()
        self.setup_janela()
        
    def setup_janela(self):
        """Configura a janela de seleção"""
        self.root.title("Seleção Manual de GIF")
        self.root.attributes('-topmost', True)

        largura = 800
        altura = 750
        self.root.geometry(f"{largura}x{altura}")

        # Centraliza
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.root.winfo_screenheight() // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")
        
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
        matches_label = Label(main_frame, text="🏆 TOP 3 MATCHES ENCONTRADOS:", 
                             font=('Arial', 12, 'bold'), fg='yellow', bg='#2d2d2d')
        matches_label.pack(pady=(0, 10))
        
        # Canvas e scrollbar para os matches
        canvas_frame = Frame(main_frame, bg='#2d2d2d')
        canvas_frame.pack(fill='both', expand=True)
        
        self.canvas_scroll = Canvas(canvas_frame, bg='#2d2d2d', highlightthickness=0)
        #scrollbar = Scrollbar(canvas_frame, orient="vertical", command=self.canvas_scroll.yview)
        self.scrollable_frame = Frame(self.canvas_scroll, bg='#2d2d2d')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))
        )
        
        self.canvas_scroll.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        #self.canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        # Adiciona os matches
        self.criar_matches()
        
        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        #scrollbar.pack(side="right", fill="y")
        
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
        """Cria os cards dos matches em layout horizontal"""
        # Frame horizontal para os cards
        cards_frame = Frame(self.scrollable_frame, bg='#2d2d2d')
        cards_frame.pack(fill='x', padx=10, pady=10)
        
        for i, (caminho, distancia, arquivo) in enumerate(self.top_matches):
            # Frame do match (agora lado a lado)
            match_frame = Frame(cards_frame, bg='#3d3d3d', relief='raised', bd=2, width=240, height=320)
            match_frame.pack_propagate(False)  # Impede que o conteúdo altere o tamanho
            match_frame.pack(side='left', padx=5, pady=5)
                        
            # Frame interno
            inner_frame = Frame(match_frame, bg='#3d3d3d', padx=10, pady=10)
            inner_frame.pack(fill='both', expand=True)
            
            # Ranking e distância
            rank_text = f"#{i+1}\nDist: {distancia:.1f}"
            rank_colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#4CAF50', '#2196F3']
            rank_color = rank_colors[i] if i < len(rank_colors) else '#FFFFFF'
            
            Label(inner_frame, text=rank_text, font=('Arial', 9, 'bold'),
                  fg=rank_color, bg='#3d3d3d').pack()
            
            # Preview do GIF (primeiro frame)
            # try:
            #     img_preview = carregar_primeiro_frame(caminho)
            #     img_preview.thumbnail((150, 150), Image.Resampling.LANCZOS)
                
            #     photo = self.pil_to_photoimage(img_preview)

            #     preview_canvas = Canvas(inner_frame, width=150, height=150, bg='black')
            #     preview_canvas.pack(pady=5)
            #     preview_canvas.create_image(75, 75, image=photo)
            #     preview_canvas.image = photo
                
            # except Exception as e:
            #     Label(inner_frame, text="❌\nPreview\nindisponível", 
            #           fg='red', bg='#3d3d3d', width=12, height=3).pack(pady=5)
            

            try:
                nome_base = os.path.basename(caminho).split("_frame")[0]
                caminho_gif = os.path.join("gifs", f"{nome_base}")

                if self.janela_controle:
                    self.janela_controle.adicionar_log(f"🧠 Path do gif: {caminho_gif}", "info")


                pil_img = Image.open(caminho_gif)
                pil_img = pil_img.resize((180, 180), Image.Resampling.LANCZOS)  # ajuste o tamanho como quiser

                photo = ImageTk.PhotoImage(pil_img)

                gif_label = Label(inner_frame, image=photo, bg='black')
                gif_label.image = photo
                gif_label.pack(pady=5)
            except Exception as e:
                Label(inner_frame, text="❌\nGIF inválido", 
                    fg='red', bg='#3d3d3d', width=12, height=3).pack(pady=5)


            # Nome do arquivo (truncado)
            nome_curto = arquivo[:15] + "..." if len(arquivo) > 15 else arquivo
            Label(inner_frame, text=nome_curto, font=('Arial', 8),
                  fg='white', bg='#3d3d3d').pack(pady=2)
            
            # Botão selecionar
            btn_selecionar = Button(inner_frame, 
                                   text="✅ ESCOLHER",
                                   command=lambda c=caminho, d=distancia: self.selecionar_gif(c, d),
                                   font=('Arial', 8, 'bold'),
                                   bg='#4CAF50', fg='white',
                                   width=12, height=2)
            btn_selecionar.pack(pady=5)
            
            # Tooltip com caminho completo
            self.criar_tooltip(btn_selecionar, f"Arquivo: {arquivo}\nCaminho: {caminho}")

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
