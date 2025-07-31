# ImageHash - Sistema de Reconhecimento de Exercícios

Sistema automático para captura de tela, reconhecimento de exercícios e organização de GIFs baseado em hash de imagens e OCR.

## 📋 Funcionalidades

- **Captura automática de tela** com coordenadas específicas
- **Reconhecimento de imagens** usando hash perceptual
- **OCR (Reconhecimento de texto)** para extrair nomes de exercícios
- **Renomeação automática** de arquivos GIF baseada no texto extraído
- **Sistema de hotkey** para automação (Ctrl+0)

## 🛠️ Pré-requisitos

### Tesseract OCR

Faça o download e instale o Tesseract OCR:

- **Download**: [Tesseract OCR para Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- **Versão recomendada**: 5.5.0 ou superior
- **Instale** o programa e anote o caminho de instalação (geralmente `C:\Program Files\Tesseract-OCR\tesseract.exe`)

### Python

- Python 3.8 ou superior

## 📦 Instalação

1. Clone o repositório:

```bash
git clone <url-do-repositorio>
cd imagehash
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure o caminho do Tesseract no código (linha 9 do `print_nome.py`):

```python
pytesseract.pytesseract.tesseract_cmd = r"CAMINHO_PARA_SEU_TESSERACT\tesseract.exe"
```

## 📁 Estrutura do Projeto

```
imagehash/
├── print_nome.py      # Script principal com automação
├── imghash.py         # Funções de hash de imagem
├── capturatela.py     # Captura de tela simples
├── coordenadas.py     # Utilitário para capturar coordenadas
├── gifs/             # Pasta com GIFs de exercícios
├── exemplos/         # Imagens de exemplo
└── requirements.txt  # Dependências Python
```

## 🚀 Como Usar

### 1. Captura Automática (print_nome.py)

```bash
python print_nome.py
```

- Pressione **Ctrl+0** a qualquer momento para capturar e processar
- O sistema irá:
  1. Capturar a área da imagem do exercício
  2. Capturar o texto do nome do exercício
  3. Encontrar o GIF mais similar
  4. Renomear o GIF com o nome extraído

### 2. Busca por Similaridade (imghash.py)

```bash
python imghash.py
```

Compara uma imagem com todos os GIFs da pasta e encontra o mais similar.

### 3. Captura Manual (capturatela.py)

```bash
python capturatela.py
```

Captura uma área específica da tela e busca por GIFs similares.

### 4. Definir Coordenadas (coordenadas.py)

```bash
python coordenadas.py
```

Utilitário para descobrir as coordenadas de uma área da tela.

## ⚙️ Configuração

### Ajustar Coordenadas de Captura

No arquivo `print_nome.py`, ajuste as coordenadas conforme necessário:

```python
# Captura da imagem do exercício (x, y, largura, altura)
imagem_capturada = capturar_area((277, 457, 485, 377), "imagem.png")

# Captura do nome do exercício
texto_capturado = capturar_area((261, 289, 369, 50), "texto.png")
```

### Configurar Idioma do OCR

Para melhor reconhecimento de texto em português:

```python
texto = pytesseract.image_to_string(imagem, lang='por')
```

## 📋 Dependências

- **Pillow** (>=10.0.0) - Manipulação de imagens
- **imagehash** (>=4.3.1) - Hash perceptual de imagens
- **pytesseract** (>=0.3.10) - OCR (Reconhecimento de texto)
- **pyautogui** (>=0.9.54) - Automação de interface
- **pynput** (>=1.7.6) - Captura de eventos do mouse
- **keyboard** (>=0.13.5) - Captura de teclas

## 📄 Licença

Este projeto está sob licença MIT - veja o arquivo LICENSE para detalhes.

## 🔗 Links Úteis

- [Tesseract OCR Wiki](https://github.com/UB-Mannheim/tesseract/wiki)
- [Documentação do ImageHash](https://pypi.org/project/ImageHash/)
- [PyTesseract Documentation](https://pypi.org/project/pytesseract/)
