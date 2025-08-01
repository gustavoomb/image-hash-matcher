import tkinter as tk
from tkinter import Canvas, Button, Frame, Label, Text, Scrollbar
import time
import json
from image_classifier import processar, mostrar_pontos_captura

class JanelaControle:
    def __init__(self, area_texto, area_imagem):
        self.area_texto = area_texto
        self.area_imagem = area_imagem
        self.root = tk.Tk()
        self.setup_janela()
        
    def setup_janela(self):
        """Configura a janela de controle"""
        self.root.title("ImageHash Control")
        
        # Centraliza a janela na tela
        width = 420
        height = 575
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
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
        buttons_frame.pack(pady=(0, 10))

        # Sub-frame centralizado
        center_frame = Frame(buttons_frame, bg='#2d2d2d')
        center_frame.pack()
        
        # Botão Capturar Automático
        self.btn_capturar_auto = Button(center_frame, text="🤖 AUTO", 
                                       command=self.capturar_auto_clicked,
                                       font=('Arial', 9, 'bold'),
                                       bg='#4CAF50', fg='white',
                                       width=12, height=2,
                                       relief='raised', bd=3)
        self.btn_capturar_auto.pack(side='left', padx=2)
        
        # Botão Capturar Manual
        self.btn_capturar_manual = Button(center_frame, text="👤 MANUAL", 
                                         command=self.capturar_manual_clicked,
                                         font=('Arial', 9, 'bold'),
                                         bg='#2196F3', fg='white',
                                         width=12, height=2,
                                         relief='raised', bd=3)
        self.btn_capturar_manual.pack(side='left', padx=2)
        
        # Botão Visualizar
        self.btn_visualizar = Button(center_frame, text="👁 CONFIG.", 
                                    command=self.visualizar_clicked,
                                    font=('Arial', 9, 'bold'),
                                    bg='#9C27B0', fg='white',
                                    width=12, height=2,
                                    relief='raised', bd=3)
        self.btn_visualizar.pack(side='left', padx=2)
                
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
        
        # Chama a função e captura o resultado
        resultado = mostrar_pontos_captura(self.area_texto, self.area_imagem)
        
        # Se o usuário salvou novas coordenadas, atualiza as variáveis da classe
        if resultado:
            self.area_texto = resultado["area_texto"]
            self.area_imagem = resultado["area_imagem"]
            
            self.adicionar_log("✅ Coordenadas atualizadas na interface", "success")
            self.adicionar_log(f"📍 Nova área do texto: {self.area_texto}", "info")
            self.adicionar_log(f"📍 Nova área da imagem: {self.area_imagem}", "info")
        
        self.atualizar_status("Aguardando comando...")

            
    def fechar_clicked(self):
        """Fecha a aplicação"""
        self.adicionar_log("👋 Fechando aplicação...", "info")
        self.root.quit()
        self.root.destroy()
        
    def executar(self):
        """Inicia o loop principal da janela"""
        self.root.mainloop()

