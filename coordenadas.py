from pynput import mouse

pontos = []

def on_click(x, y, button, pressed):
    if pressed:
        print(f"Clique detectado em: x={x}, y={y}")
        pontos.append((x, y))
        if len(pontos) == 2:
            # Para o listener após o segundo clique
            return False

print("Clique duas vezes na tela para capturar a área (canto sup. esquerdo e inf. direito)...")

with mouse.Listener(on_click=on_click) as listener:
    listener.join()

# Processar bounding box
(x1, y1), (x2, y2) = pontos
x_min, y_min = min(x1, x2), min(y1, y2)
width = abs(x2 - x1)
height = abs(y2 - y1)
bbox = (x_min, y_min, width, height)

print(f"\nBounding Box final: {bbox}")
