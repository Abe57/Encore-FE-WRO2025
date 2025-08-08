Encore | WRO-Futuros Ingenieros 2025 | PAN 
==== 

Este es el repositorio oficial del equipo Encore. Somos representantes del colegio La Salle-Margarita en las regionales de Colón, Panamá de la World Robot Olympiad (WRO) 2025 en la categoría de Futuros Ingenieros.  

La categoría de futuros ingenieros está enfocada en el diseño y la implementación de vehículos autónomos a escala. El desafío consiste en desarrollar un sistema capaz de navegar un circuito predefinido, identificando y superando obstáculos de forma autónoma mediante el procesamiento de datos de su entorno.  

Esta disciplina está directamente alineada con las tendencias actuales y futuras de la industria automotriz, específicamente con el desarrollo de Sistemas Avanzados de Asistencia al Conductor (ADAS) y tecnologías de conducción autónoma. El proyecto de desarrollo exige una aplicación práctica de conceptos en áreas como la percepción ambiental, algoritmos de control y ingeniería de sistemas.  


Nuestro proceso de desarrollo comenzó estratégicamente con un chasis prefabricado. Esta decisión nos permitió enfocarnos inicialmente en la integración de la electrónica y el desarrollo del software de control, sin la necesidad de conocimientos avanzados en diseño 3D. Sin embargo, pronto descubrimos que este punto de partida era solo el comienzo.

El verdadero desafío de ingeniería consistió en identificar sistemáticamente las limitaciones del diseño base y rediseñar cada subsistema para cumplir con nuestras exigentes expectativas de rendimiento. Desde la optimización del peso y la mecánica hasta la re-arquitectura completa del sistema eléctrico y de control, este robot es el resultado de un ciclo continuo de pruebas, diagnósticos y mejoras.

**Revise `docs` para ver la documentación completa y detallada, este `README.md` solo presenta un resumen de cada etapa del proyecto.**

## Equipo
Foto del equipo, de izquierda a derecha **José Heráldez, Abel Herrera y Pablo González**.
![Foto equipo](t-photos/Foto%20Grupal.jpg)






## Contenido del Repositorio
* `docs` Contiene todos los documentos del equipo y el diario de ingeniería.
* `other` Otros archivos relacionados al desarollo del robot.
* `schemes` Contiene los esquemas electromecánicos del vehículo y otros diagramas.
* `src` Contiene todos los programas que se estarán usando en la competencia.
* `t-photos` Contiene 2 fotos grupales (una formal y una divertida) y las fotos individuales.
* `v-photos` Contiene las 6 fotos desde todos los ángulos.
* `video` Contiene el video de demostración del funcionamiento del robot.


## Generalidades del robot
## Fotos del robot
### Frontal: 
![imagen](<v-photos/frontal2.jpg> "imagen")
### Trasera: 
![imagen](<v-photos/trasera2.jpg> "imagen")
### Superior (Segundo nivel): 
![imagen](<v-photos/Superior2.jpg> "imagen")
### Inferior: 
![imagen](<v-photos/Inferior2.jpg> "imagen")
### Lateral 1: 
![imagen](<v-photos/lateral21.jpg> "imagen")
### Lateral 2: 
![imagen](<v-photos/lateral22.jpg> "imagen")

### Configuración general 
El desarrollo del robot partió de un chasis Ackerman prefabricado para establecer una base mecánica sólida y acelerar el prototipado. Sin embargo, este punto de partida se convirtió en el primer desafío de ingeniería, ya que el diseño original presentaba problemas significativos de peso y una configuración de propulsión y dirección que requería un rediseño completo para cumplir con los objetivos de rendimiento del equipo.

### Descripción del chasis 
El chasis original de metal, aunque resistente, elevaba el peso total del robot a 1700 g, una masa excesiva que limitaba la agilidad y sobrecargaba el sistema de propulsión. Para resolver esto, se llevó a cabo un proceso de optimización de materiales, reemplazando las placas de metal por láminas de acrílico cortadas a medida. Esta modificación fue un éxito, reduciendo el peso total a 1217 g y permitiendo un diseño más limpio y optimizado con perforaciones específicas para nuestros componentes. La estructura se mantuvo en dos niveles para aislar la electrónica de las vibraciones mecánicas.
### Sistema de dirección 
Para lograr una navegación precisa, se implementó una geometría de dirección Ackerman. Este sistema, que minimiza el deslizamiento de las ruedas en las curvas, fue un diseño a medida del equipo. A través de un proceso de investigación y prototipado, se fabricaron soportes y se calibraron las varillas de acoplamiento para emular la cinemática ideal. El sistema es accionado por un servomotor de alto torque, asegurando que la dirección sea firme y responda con precisión a los comandos.

### Sistema de propulsión 
El diseño inicial del sistema de propulsión priorizaba la velocidad con una relación de engranajes de 9:7 (sobremarcha). Sin embargo, las pruebas demostraron que el torque resultante era insuficiente para vencer la inercia y la fricción estática, impidiendo que el robot se moviera por sí solo. Tras diagnosticar el problema, se tomó la decisión de ingeniería de invertir la relación a una de reducción 7:9. Aunque esto sacrificó la velocidad máxima, multiplicó el torque, proporcionando la fuerza de arranque necesaria para un funcionamiento autónomo y fiable.
### Diseño Eléctrico 
La arquitectura eléctrica evolucionó a un sistema de control distribuido para maximizar la eficiencia y la fiabilidad.

* Raspberry Pi 5 (Cerebro Principal): Se encarga de las tareas de alta carga computacional, como el procesamiento de imágenes de la webcam y la ejecución de la lógica de decisión principal.

* Arduino Nano (Co-procesador de Tiempo Real): Se añadió para gestionar todas las tareas de bajo nivel que requieren una temporización precisa. El Nano controla directamente el driver de motores L298N, el servomotor, el sensor ultrasónico HC-SR04 y el giroscopio MPU6050, ejecutando los comandos que recibe de la Pi.
![imagen](<schemes/ENCORE-DIAGRAMA-ESQUEMATICO.png> "imagen")

### Gestión de la energía 
La estabilidad energética fue un desafío crítico. Inicialmente, al alimentar el Arduino Nano desde el puerto USB de la Raspberry Pi, la demanda de corriente combinada provocaba caídas de voltaje que reiniciaban la Pi. La solución fue diseñar un sistema de alimentación dual e independiente:

* Una power bank de 10000mAh se dedica exclusivamente a la Raspberry Pi.

* Dos baterías de 9V en paralelo alimentan el driver L298N, y la salida regulada de 5V de este mismo driver se utiliza para alimentar el Arduino y sus periféricos. Esta configuración aísla los componentes y garantiza un funcionamiento estable.
### Demostración
Después de un arduo ciclo de desarrollo y pruebas, el robot es capaz de cumplir con los requisitos de la primera ronda, demostrando una navegación autónoma y la capacidad de detectar y esquivar obstáculos. El siguiente video muestra el funcionamiento actual del robot.


### Características por mejorar
Basado en los resultados de la primera competencia y las pruebas continuas, el equipo ha identificado las siguientes áreas clave para el desarrollo futuro:

* Reducir la Latencia del Bucle de Control: Optimizar el código y la comunicación serie entre la Pi y el Arduino para lograr reacciones más rápidas y una navegación más fluida.

* Mejorar la Fiabilidad de las Conexiones: Migrar las conexiones del protoboard a una solución más permanente, como una PCB diseñada a medida o una protoboard soldada, para eliminar los falsos contactos.

* Optimizar la Velocidad y el Control: Una vez que la fiabilidad esté garantizada, se trabajará en aumentar la velocidad máxima del robot y en refinar los algoritmos de control para una mayor precisión en el seguimiento de la trayectoria.