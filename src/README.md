## Estructura del Código

El sistema se divide en dos componentes principales: el software de alto nivel que se ejecuta en la Raspberry Pi (`cv.py`) y el firmware de bajo nivel que se ejecuta en la Arduino Nano (`NanoCode.ino`).

### Raspberry Pi (Procesamiento)

La Raspberry Pi se encarga de:
* **Visión por Computadora:** Capturar video de una cámara, procesar los fotogramas utilizando OpenCV para detectar líneas y bloques de colores específicos.
* **Lógica de Navegación:** Tomar decisiones de alto nivel basadas en la información visual (p. ej., "girar a la derecha porque se detectó un bloque rojo").
* **Comunicación Serial:** Enviar comandos a la Arduino Nano para controlar el movimiento del robot.

### Arduino Nano (Controlador)

La Arduino Nano actúa como un controlador en tiempo real para:
* **Control de Motores:** Manejar el motor de corriente continua para el movimiento hacia adelante, hacia atrás y la detención.
* **Control de Dirección:** Ajustar un servomotor para dirigir el robot.
* **Lectura de Sensores:**
    * **Sensores de Proximidad:** Utiliza tres sensores ultrasónicos HC-SR04 (izquierdo, central y derecho) para medir la distancia a los obstáculos.
    * **Unidad de Medición Inercial (IMU):** Emplea un MPU6050 para medir la orientación del robot, específicamente el ángulo de guiñada (yaw)
* **Ejecución de Comandos:** Recibir y ejecutar los comandos enviados desde la Raspberry Pi a través de la comunicación serial.

## Comunicación entre Raspberry Pi y Arduino Nano

La comunicación entre ambos dispositivos es un pilar fundamental del proyecto y se realiza a través de una conexión **serial USB**.

1.  **Inicio y Sincronización:**
    * La Arduino Nano inicia primero y espera recibir el comando `"START"` desde la Raspberry Pi a través del puerto serial (`/dev/ttyUSB0`).
      * Al recibir `"START"`, la Nano comienza la calibración del giroscopio y completa su configuración inicial.
      * El envío del comando `"START"` se activa en la Raspberry Pi al presionar un botón físico conectado a sus pines GPIO.
      * Una vez que la Nano termina la calibración, responde con `"Started!"` y se prepara para recibir comandos de movimiento.

2.  **Flujo de Datos:**
    * **De la Nano a la Pi:** La Arduino Nano envía continuamente datos de los sensores a la Raspberry Pi. Estos datos incluyen las distancias de los tres sensores de proximidad (`PROX_L`, `PROX_C`, `PROX_R`) y el ángulo de guiñada (`YAW`). La frecuencia de envío de estos datos está limitada a cada 100 milisegundos para no saturar la comunicación.
    * **De la Pi a la Nano:** La Raspberry Pi, después de procesar un fotograma de la cámara y decidir qué acción tomar, envía comandos a la Nano. Los comandos pueden ser:
        * `FW`: Moverse hacia adelante.
        * `BW`: Moverse hacia atrás.
        * `STOP`: Detener los motores.
        * `SERVO<angulo>`: Ajustar el servomotor de dirección a un ángulo específico (entre -45 y 45 grados).

    El script de la Pi puede enviar múltiples comandos a la vez, separados por un punto y coma (`;`), que la Nano procesa en secuencia.

## Reconocimiento de Bloques y Líneas con OpenCV

El corazón de la lógica de navegación reside en la capacidad del script de Python para "ver" y entender el entorno. Esto se logra mediante varias etapas de procesamiento de imágenes con la biblioteca OpenCV.

### 1. Calibración de Color

Para que el robot pueda identificar colores de manera fiable bajo diferentes condiciones de iluminación, es necesario calibrarlos.
* **Archivo de Calibración (`color_tune.txt`):** Este archivo almacena los rangos de color **HSV (Hue, Saturation, Value - Tono, Saturación, Valor)** para cada color que el robot debe reconocer (Rojo, Verde, Azul, Naranja)
* **Modo de Ajuste (`tune = True`):** El script `cv.py` se puede ejecutar en un modo de "ajuste". En este modo, se muestra una ventana con controles deslizantes (trackbars) que permiten al usuario ajustar los valores HSV mínimos y máximos para un color específico (`toTune`) en tiempo real.
* **Guardado de la Calibración:** Una vez que los colores se aíslan correctamente, los valores HSV se pueden guardar en el archivo `color_tune.txt` para su uso futuro.

### 2. Procesamiento de la Imagen

Cada fotograma capturado por la cámara pasa por el siguiente pipeline:
1.  **Redimensionamiento y Rotación:** La imagen se ajusta a una resolución definida (640x360) y se rota 180 grados para corregir la orientación de la cámara.
2.  **Reducción de Ruido:** Se aplican filtros como el desenfoque Gaussiano y el desenfoque de mediana para suavizar la imagen y eliminar imperfecciones que podrían interferir con la detección de colores.
3.  **Conversión a HSV:** La imagen se convierte del espacio de color BGR (usado por OpenCV) al espacio de color HSV. El espacio HSV es mucho más robusto para la detección de colores que el espacio RGB, ya que separa la intensidad de la luz (Valor) del color en sí (Tono y Saturación).

### 3. Detección de Colores y Contornos

Para cada color definido en el archivo de calibración:
1.  **Creación de Máscara:** Se crea una máscara binaria (blanco y negro) utilizando la función `cv.inRange()`. Esta función toma los rangos HSV mínimo y máximo para un color y genera una imagen donde los píxeles que caen dentro de ese rango son blancos y el resto son negros.
2.  **Operaciones Morfológicas:** Se aplican transformaciones morfológicas a la máscara para eliminar pequeños ruidos (puntos blancos aislados) y rellenar agujeros dentro de las áreas detectadas.
3.  **Búsqueda de Contornos:** Se utiliza la función `cv.findContours()` sobre la máscara para encontrar los contornos, que son esencialmente las siluetas de los objetos de color detectados.

### 4. Clasificación y Toma de Decisiones

Una vez que se tienen los contornos de todos los colores:
* **Clasificación:**
    * Los contornos de color **Rojo (R)** y **Verde (G)** se clasifican como **bloques**.
    * Los contornos de color **Azul (B)** y **Naranja (O)** se clasifican como **líneas**.
* **Ordenamiento:**
    * Los **bloques** se ordenan por tamaño (área) de mayor a menor.
    * Las **líneas** se ordenan por su posición vertical (coordenada 'y') de arriba hacia abajo.
* **Lógica de Dirección:**
    * El robot busca el **bloque más grande** que no esté demasiado cerca de los bordes de la imagen.
    * El color de este bloque determina la dirección:
        * **Rojo (R):** Girar a la derecha (`direction = 1`).
        * **Verde (G):** Girar a la izquierda (`direction = -1`).
    * Si no se detecta ningún bloque, el robot utiliza la información de las líneas o los sensores de proximidad para decidir su siguiente movimiento. La primera vez que detecta las líneas azul y naranja, establece una dirección de rotación preferida (`cw` o `ccw`) basada en cuál está encima de la otra.

Este ciclo de captura, procesamiento y acción se repite continuamente, permitiendo al robot navegar de forma autónoma a través de su entorno.