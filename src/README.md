# Código Fuente

El código del proyecto se divide en dos partes principales: **Raspberry Pi 5** y **Arduino Nano**. Ambas trabajan en conjunto, comunicándose por Serial para completar exitosamente el desafío.

---

## Arduino Nano

- **Funciones principales:**
  - Captura valores del giroscopio (MPU6050) y sensor de proximidad (ultrasónico).
  - Controla el motor y el servo de dirección.
- **Flujo de trabajo:**
  1. Al encenderse, espera la orden `"START"` por Serial.
  2. Al recibir `"START"`, calibra el giroscopio durante 2 segundos para estimar el sesgo y mejorar la precisión.
  3. En el loop principal:
     - Lee comandos recibidos por Serial y ejecuta acciones (mover, girar, detener).
     - Captura valores de sensores y los envía por Serial a la Raspberry Pi.

---

## Raspberry Pi 5

- **Funciones principales:**
  - Realiza el análisis de imagen y la lógica de decisión usando visión por computadora (OpenCV).
  - Recibe la imagen de la cámara y determina la dirección que debe tomar el robot.
  - Se conecta al Serial y envía el mensaje `"START"` al Arduino Nano.
  - Espera la calibración del giroscopio y la presión del botón para iniciar.
  - Lee valores de sensores enviados por Serial.
- **Lógica de movimiento:**
  - Determina la dirección basada en el color predominante (azul o naranja) de la pista.
  - Si detecta bloques, mueve el servo según el color del bloque.
  - Si el valor absoluto del giroscopio supera 1100 (≈ 3 vueltas completas), detiene el programa y el motor.
- **Ajuste de colores:**
  - Permite guardar y cargar configuraciones de ajuste de colores para facilitar la adaptación a diferentes entornos.


## Resumen

- **La Raspberry Pi** toma decisiones usando visión artificial y sensores.
- **El Arduino Nano** ejecuta los movimientos y reporta datos de sensores.
- Ambos se comunican por Serial para coordinar el funcionamiento del robot.

