# ImageHash - Sistema de Reconhecimento de Imagens

Sistema para captura de tela, reconhecimento de imagens e identificação de GIFs usando hash de imagens e OCR.

## 🎯 Funcionalidades

- **Interface gráfica** com captura automática e manual
- **Reconhecimento de imagens** com múltiplos algoritmos de hash
- **OCR** para extrair texto em português
- **Comparação inteligente** com biblioteca de GIFs pré-extraídos
- **Sistema de seleção manual** para casos duvidosos

## 📦 Instalação

1. **Instale o Tesseract OCR**:

   - Download: [Tesseract v5.5.0+](https://github.com/UB-Mannheim/tesseract/wiki)
   - Configure o caminho no código se necessário

2. **Instale as dependências**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare os frames**:
   ```bash
   python extrai_frame.py
   ```

## � Como Usar

### Interface Principal

```bash
python janela_controle.py
```

**Modos de captura:**

- **🤖 AUTO**: Seleciona automaticamente o melhor match
- **👤 MANUAL**: Mostra top 3 para seleção manual
- **👁 CONFIG**: Ajusta áreas de captura na tela

### Configuração das Áreas

1. Clique em **CONFIG** para definir:
   - Área do texto da imagem
   - Área da imagem principal
2. Arraste para mover, redimensione pelos vértices
3. Pressione **ENTER** para salvar

## 📁 Estrutura

```
imagehash/
├── janela_controle.py     # Interface principal
├── janela_selecao.py      # Seleção manual de GIFs
├── image_classifier.py    # Motor de reconhecimento
├── extrai_frame.py        # Extração de frames dos GIFs
├── gifs/                  # Biblioteca de GIFs
├── frames_extraidos/      # Frames para comparação
└── requirements.txt       # Dependências
```
