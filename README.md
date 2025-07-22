Encore | WRO-Futuros Ingenieros 2025 | PAN 
==== 

Este es el repositorio oficial del equipo Encore. Somos representantes del colegio La Salle-Margarita en las regionales de Colón, Panamá de la World robot olimpiad (WRO) 2025 en la categoría de Futuros Ingenieros.  

La categoría de futuros ingenieros está enfocada en el diseño y la implementación de vehículos autónomos a escala. El desafío consiste en desarrollar un sistema capaz de navegar un circuito predefinido, identificando y superando obstáculos de forma autónoma mediante el procesamiento de datos de su entorno.  

Esta disciplina está directamente alineada con las tendencias actuales y futuras de la industria automotriz, específicamente con el desarrollo de Sistemas Avanzados de Asistencia al Conductor (ADAS) y tecnologías de conducción autónoma. El proyecto de desarrollo exige una aplicación práctica de conceptos en áreas como la percepción ambiental, algoritmos de control y ingeniería de sistemas.  

En este repositorio encontrará toda la información sobre el equipo Encore y su desarrollo. Elegimos participar en futuros ingenieros con el proposito de dar lo mejor de nosotros en busca del mejor resultado. 


En el desarrollo del robot se eligió usar como base un chasis prefabricado, facilitando el desarrollo, considerando que no tenemos conocimientos en diseño 3D, este fue altamente modificado para que cumpliera con nuestras espectativas. 


****Revise `docs` para ver la documentación completa, este `README.md` solo presenta un resumen de cada sección.**** 

## Equipo
Foto del equipo, de izquierda a derecha **José Heráldez, Abel Herrera y Pablo González**.
![Foto equipo](t-photos/Foto%20Grupal.jpg)






## Contenido del Repositorio
* `Componentes` Contiene todos los componentes utilizados en el proyecto.
* `docs` Contiene todos los documentos del equipo y el diario de ingeniería.
* `other` Otros archivos relacionados al desarollo del robot.
* `schemes` Contiene los esquemas electromecánicos del vehículo y otros diagramas.
* `src` Contiene todos los programas que se estarán usando en la competencia.
* `t-photos` Contiene 2 fotos grupales (una formal y una divertida) y las fotos individuales.
* `v-photos` Contiene las 6 fotos desde todos los ángulos.
* `video` Contiene el video de demostración del funcionamiento del robot.


## Generalidades del robot

### Foto del robot
![imagen](<v-photos/Lateral-1.jpg> "imagen")

### Configuración general 
El robot parte de un chasis Ackerman prefabricado como base para acelerar el desarrollo. Sin embargo, este punto de partida presentó desafíos significativos, como el exceso de peso y la necesidad de rediseñar sistemas clave como la propulsión y la dirección.

### Descripción del chasis 
El chasis original de metal (1700 g) se reemplazó con placas de acrílico cortadas a medida para solucionar el problema de peso. Esta modificación redujo el peso total a 1217 g y permitió optimizar el diseño con perforaciones específicas para los componentes. La estructura es de dos niveles para separar la electrónica de los componentes mecánicos.
### Sistema de dirección 
Se implementó una geometría de dirección Ackerman para lograr giros estables y precisos, minimizando el deslizamiento de las ruedas. El mecanismo fue un diseño a medida del equipo, desarrollado a través de investigación, prototipado y calibración, y es accionado por un servomotor de alto torque para asegurar una respuesta firme.

### Sistema de propulsión 
El diseño inicial priorizaba la velocidad con una relación de engranajes de 9:7, pero carecía del torque necesario para mover el robot desde cero. La solución fue invertir la relación a una de reducción 7:9, sacrificando velocidad máxima para obtener fuerza.
### Diseño Eléctrico 
El sistema es controlado por una Raspberry Pi 5. Un controlador L298N se encarga de los motores, elegido por ser el único disponible para el equipo a pesar de sus conocidas ineficiencias. La percepción del entorno combina una webcam para identificar color y posición, y un sensor ultrasónico HC-SR04 para medir la distancia
### Gestión de la energía 
El plan inicial de usar una sola power bank de 5V falló, ya que el controlador L298N consumía 2V, dejando solo 3V insuficientes para el motor. Se implementó un sistema dual: la power bank de 10000mAh alimenta exclusivamente a la Raspberry Pi, mientras que dos baterías de 9V en paralelo se dedican a los motores.
### Demostración
En las pruebas, diversos desperfectos electrónicos causaron retrasos que impidieron completar el reto de las 3 vueltas antes de la primera competencia (22 de julio).

### Características por mejorar
El equipo ha identificado tres áreas clave para el futuro desarrollo: mejorar el tiempo de reacción del robot, que es lento debido a los sensores; aumentar la velocidad general; y optimizar la gestión de cables para evitar falsos contactos.