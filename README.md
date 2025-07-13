# Encore Team | WRO Future Engineers 2025 | PAN
Somos el equipo Encore, representante del Colegio La Salle-Margarita en las Olimpiadas Mundiales de Robótica (WRO) 2025, categoría futuros ingenieros en las regionales de Colón, Panamá.

## Introducción

El código se ejecuta en 2 hilos: uno para el algoritmo de Computer Vision y otro para el sensor de proximidad HC-SR04. Esto fue necesario para que el sensor de proximidad funcionara correctamente, ya que captura datos a una velocidad mucho más lenta. La webcam conectada a la Raspberry Pi es la encargada de capturar el video que alimenta el algoritmo de detección de computer vision. Utilizamos GitHub para subir el código a la Raspberry Pi clonando un repositorio con el código actualizado. Hicimos [un script](other/clone.sh) para clonar usando un PAT (Token de Acceso Personal).


