# SPEC-LAB-001 — El Laberinto del Fantasma

| Campo | Valor |
|---|---|
| Versión | 1.3 (lista para implementar) |
| Autor | Diego León Arcila Herrera |
| Fecha | 2026-10-16 |
| Metodología | Spec Driven Development (SDD): esta especificación es la fuente de verdad; el código y las pruebas se derivan de ella |
| Lenguaje | Python 3.10+ |
| Librería gráfica | pygame 2.x (única dependencia externa del juego) |

### Historial de cambios
| Versión | Cambio |
|---|---|
| 1.0 | Primera versión. |
| 1.1 | El jugador puede terminar su turno antes (`ENTER`). Se confirma que cruzarse cuenta como captura. El fantasma aparece en una casilla al azar. Se agrega el **visualizador de backtracking** (pila en forma de tarro + recorrido sobre el tablero), sección 8. |
| 1.2 | El fantasma aparece a **6 pasos o más** del jugador. El laberinto de cada partida es **al azar**: uno de los 5 predefinidos o uno **generado nuevo** con backtracking (4.3). Se agrega la simulación HTML de referencia (sección 18). |
| 1.3 | Se cierran los huecos: generador aparte para la animación del dado (D-6), `ESC` vuelve al menú o sale (10.4), respaldo si `laberintos.json` falla (4.3), cierre de ventana (10.4). Calidad: cobertura ≥ 80 % (14). Definición de terminado (19). Ejecución solo con `python main.py`. La dificultad actual se aprueba sin cambios. |

---

## 1. Resumen

Juego de mesa digital por turnos para un jugador. Un **personaje** debe cruzar un laberinto de 15×15 casillas desde la **entrada** hasta la **meta**. En cada turno tira **un dado** y avanza hasta tantas casillas como indique. Después de su primera jugada aparece un **fantasma** en una **casilla al azar**. El fantasma también tira el dado y persigue al jugador usando **backtracking**. Al lado del tablero, un **tarro (pila)** muestra paso a paso cómo el backtracking apila y desapila casillas mientras el fantasma busca al jugador.

- **Gana** el jugador si llega a la meta antes de ser alcanzado → mensaje **"¡HAS GANADO!"**.
- **Pierde** si el fantasma lo alcanza o se cruzan → mensaje **"GAME OVER"**.

Objetivo didáctico: servir de material para el curso de Estructuras de Datos, mostrando la **pila** y la **recursión con retroceso** en un caso visual.

## 2. Alcance

### 2.1 Incluido
- Un jugador humano contra el fantasma (controlado por el programa).
- Laberinto al azar en cada partida: uno de los 5 predefinidos de `laberintos.json` o uno generado en el momento con backtracking.
- Dado de 6 caras con animación.
- Visualizador de backtracking: pila animada y recorrido marcado sobre el tablero.
- Pantalla de inicio, partida, pantalla de victoria y de derrota, reinicio.

### 2.2 Excluido (fuera de esta versión)
- Multijugador, sonido, guardado de partidas, niveles de dificultad, imágenes externas (sprites). Todo se dibuja con primitivas de pygame.

## 3. Glosario

| Término | Definición |
|---|---|
| Casilla (celda) | Unidad del tablero. Coordenada `(col, fila)`, ambas en `0..14`. `(0,0)` es arriba-izquierda. |
| Paso | Movimiento de una casilla a una casilla vecina (arriba, abajo, izquierda, derecha) sin cruzar pared. No hay movimiento en diagonal. |
| Entrada | Casilla `(0,0)`. Su pared izquierda está abierta. |
| Meta | Casilla `(14,14)`. Su pared derecha está abierta. |
| Turno | Tirada del dado + movimiento de un actor (jugador o fantasma). |
| Ronda | Turno del jugador seguido del turno del fantasma. |
| Captura | El actor que se mueve entra a la casilla donde está el otro actor (ver 6.4). |
| Pila | Estructura LIFO donde el backtracking guarda el camino que está explorando. Se dibuja como un tarro. |
| Apilar / Desapilar | Meter una casilla en la cima de la pila / sacar la casilla de la cima (retroceso). |
| Traza | Lista ordenada de eventos (apilar, desapilar, encontrado) que produce la búsqueda. Se usa para animar el visualizador. |

## 4. El tablero y la ventana

### 4.1 Dimensiones (valores fijos, definidos como constantes en `config.py`)

| Constante | Valor | Descripción |
|---|---|---|
| `N` | 15 | Casillas por lado |
| `TAM_CELDA` | 40 px | Lado de cada casilla |
| `GROSOR_PARED` | 4 px | Grosor de las líneas del laberinto |
| `MARGEN` | 20 px | Espacio blanco alrededor del laberinto |
| `ANCHO_PANEL_PILA` | 280 px | Panel derecho del visualizador de backtracking |
| `ALTO_PANEL` | 100 px | Panel inferior de información (HUD), a todo lo ancho |
| Área del laberinto | 600 × 600 px | `N × TAM_CELDA`, con origen en `(20, 20)` |
| Ventana | **920 × 740 px** | ancho `640 + 280`; alto `640 + 100` |
| `FPS` | 60 | Cuadros por segundo |

Distribución:
```
┌──────────────────────────────┬──────────────┐
│                              │  Panel pila  │
│   Laberinto 600×600          │  (tarro +    │
│   (+ margen 20 px)           │  contadores) │
│        640 × 640             │   280 × 640  │
├──────────────────────────────┴──────────────┤
│  HUD: turno, dados, estado      920 × 100   │
└─────────────────────────────────────────────┘
```

Posición en pantalla de la esquina superior izquierda de la casilla `(c, f)`:
`x = MARGEN + c × TAM_CELDA`, `y = MARGEN + f × TAM_CELDA`.

### 4.2 Colores

| Elemento | Color (RGB) |
|---|---|
| Fondo | Blanco `(255, 255, 255)` |
| Paredes | Negro `(0, 0, 0)` |
| Entrada (relleno de casilla) | Azul claro `(210, 225, 255)` |
| Meta (relleno de casilla) | Verde claro `(200, 240, 200)` con texto "META" |
| Personaje | Azul `(30, 90, 220)` |
| Fantasma | Morado `(140, 60, 200)` |
| Casilla **en la pila** (camino que se explora) | Naranja `(255, 190, 90)` |
| Casilla **descartada** (se retrocedió desde ella) | Gris rosado `(230, 200, 200)` |
| Casilla que **se explora ahora** (cima de la pila) | Borde naranja oscuro `(220, 110, 0)`, 3 px |
| Camino **encontrado** | Naranja intenso `(255, 150, 30)` |
| Tarro (contorno) | Gris `(120, 120, 120)`, 3 px |
| Texto | Negro |

### 4.3 Origen del laberinto (al azar en cada partida)

Cada partida usa un laberinto elegido **al azar**. En la pantalla de inicio, la tecla `G` alterna entre dos modos:

| Modo | Comportamiento | Por defecto |
|---|---|---|
| **Generado** | Se genera un laberinto nuevo de 15×15 con **backtracking recursivo** (el mismo algoritmo del laberinto #1). Prácticamente nunca se repite. | **Sí** |
| **Predefinido** | Se elige al azar (uniforme) uno de los 5 laberintos de `laberintos.json`. | No |

- Al reiniciar con `R` se elige **otro** laberinto al azar con el mismo modo. En modo predefinido no se repite el laberinto inmediatamente anterior.
- El HUD muestra el origen: `Laberinto: generado #<semilla>` o `Laberinto: predefinido 3 (Kruskal)`.
- **Generación (contrato):** `generar_backtracking(rnd: random.Random) -> Laberinto`. Empieza en `(0,0)`, usa una pila explícita y en cada paso elige un vecino no visitado al azar; si no hay vecinos libres, desapila. Así resultan exactamente `N×N − 1 = 224` pasos abiertos (laberinto perfecto). Debe tardar menos de 50 ms.
- El código de generación se reutiliza de `generar_laberintos.py` (función `backtracker`), movido a `laberinto.py`. El script generador lo importa desde ahí.

**Respaldo si `laberintos.json` falla:**
- Al iniciar, el juego valida el archivo. Una entrada es válida si su `grid` tiene 31 filas de 31 caracteres, solo usa `'#'` y `' '`, y forma un laberinto perfecto (224 pasos abiertos y todas las casillas conectadas). Las entradas inválidas se ignoran.
- Si el archivo no existe, no es JSON válido o no queda ninguna entrada válida:
  - el modo **predefinido** se desactiva y `G` deja de alternar;
  - el juego usa siempre el modo **generado**;
  - la pantalla de inicio muestra en rojo: `"No se pudo leer laberintos.json: se usarán laberintos generados"`.
- El juego **nunca** se cierra por este motivo.

**Formato de los predefinidos:**
- El juego **carga** `laberintos.json` (ya existe). Cada entrada tiene `grid`: 31 cadenas de 31 caracteres, `'#'` = pared y `' '` = camino. Un laberinto generado se convierte al mismo formato `grid`, así que el resto del juego no distingue el origen.
- Correspondencia casilla ↔ grid: la casilla `(c, f)` está en `grid[2f+1][2c+1]`.
- Hay pared entre dos casillas vecinas `A` y `B` si `grid[fA+fB+1][cA+cB+1] == '#'`.
- Al dibujar, cada `'#'` que separa dos casillas se pinta como una línea negra de `GROSOR_PARED` px sobre el borde compartido (mismo estilo que las imágenes PNG).
- Todos los laberintos (predefinidos y generados) son **perfectos**: entre dos casillas cualesquiera existe **un único camino** sin repetir casillas. Esta propiedad es la que hace correcto el algoritmo del fantasma (sección 7).

## 5. Personajes

### 5.1 Personaje (jugador)
- **Forma:** círculo azul de radio 14 px, centrado en su casilla, con dos ojos blancos (radio 3 px) y pupilas negras.
- **Posición inicial:** la entrada `(0,0)`.
- **Control:** flechas del teclado ↑ ↓ ← →.

### 5.2 Fantasma
- **Forma:** cuerpo morado de 30 × 32 px centrado en la casilla: semicírculo superior (cabeza) + rectángulo + borde inferior ondulado de 3 picos. Dos ojos blancos con pupilas que **miran hacia la dirección de su último paso**.
- **Aparición:** **no existe** al inicio. Aparece cuando termina el **primer turno del jugador**, en una **casilla elegida al azar** (uniforme) entre todas las casillas del tablero, **excepto**:
  - toda casilla a **menos de 6 pasos** del jugador, medidos por el camino del laberinto (no en línea recta). Esto incluye la casilla del jugador y evita que lo atrape en la primera tirada sin opción de reaccionar. La constante es `DISTANCIA_MIN_FANTASMA = 6` en `config.py`;
  - la meta `(14,14)` (si el fantasma se quedara ahí, el jugador no podría ganar).
- La distancia se calcula con un recorrido en anchura (BFS) desde el jugador. Las casillas válidas son las de distancia ≥ 6, sin la meta. En un laberinto perfecto de 225 casillas siempre existen casillas válidas.
- Al aparecer se muestra durante 1 s el mensaje "¡Apareció el fantasma!" con un destello en su casilla. Luego juega su primer turno.
- **Control:** automático (IA con backtracking, sección 7).

## 6. Reglas del juego

### 6.1 Flujo de una partida
1. El jugador está en la entrada; el fantasma aún no aparece.
2. **Turno del jugador:** pulsa `ESPACIO` para tirar el dado → obtiene `d ∈ {1..6}`.
3. El jugador mueve su personaje paso a paso con las flechas. Cada paso válido descuenta 1 de los pasos restantes.
4. El turno termina cuando los pasos restantes llegan a 0 **o** cuando el jugador pulsa `ENTER`.
5. Si era el primer turno del jugador, **aparece el fantasma** en una casilla al azar (5.2).
6. **Turno del fantasma:** tira el dado, busca al jugador con backtracking (mostrado en el visualizador) y avanza.
7. Se repite desde el paso 2 hasta que haya victoria o derrota.

### 6.2 Reglas de movimiento del jugador
- **RJ-1** Solo puede moverse a una casilla vecina sin pared de por medio. Un intento contra una pared se ignora y **no** descuenta pasos.
- **RJ-2** Puede usar **entre 0 y `d`** pasos. Termina su turno antes de tiempo con `ENTER` (solo después de tirar el dado). Puede devolverse y pisar casillas ya visitadas.
- **RJ-3** No puede salir del tablero, salvo por la meta, que termina la partida.
- **RJ-4** Si llega a la **meta** aunque le sobren pasos → **gana inmediatamente**.
- **RJ-5** Si entra a la casilla donde está el fantasma → **pierde inmediatamente** (captura).

### 6.3 Reglas de movimiento del fantasma
- **RF-1** El fantasma tira el dado y obtiene `d ∈ {1..6}`.
- **RF-2** Calcula, con backtracking, el camino desde su casilla hasta la casilla **actual** del jugador. La búsqueda se anima en el visualizador (sección 8) antes de moverse.
- **RF-3** Avanza `min(d, longitud_del_camino)` pasos por ese camino, un paso cada `0.25 s` (animado). El fantasma siempre usa todos sus pasos disponibles.
- **RF-4** Si en cualquiera de sus pasos entra a la casilla del jugador → **captura → GAME OVER**, aunque le sobren puntos del dado.
- **RF-5** El fantasma respeta las paredes igual que el jugador (no las atraviesa).

### 6.4 Captura y cruce (decisión confirmada)
- Los actores se mueven **por turnos**: mientras uno se mueve, el otro está quieto.
- **Cruzarse cuenta como captura.** Como el otro actor está quieto, cruzarse equivale a que el actor que se mueve **pase por** la casilla del otro en cualquier paso, no solo en el último. Ejemplo: el fantasma saca 6, el jugador está a 2 casillas → captura en el paso 2.
- Esto aplica en los dos sentidos: RJ-5 (el jugador se mete al fantasma) y RF-4 (el fantasma alcanza al jugador).
- La comprobación se hace **después de cada paso individual**, no al final del turno.

### 6.5 Condiciones de fin
| Resultado | Condición | Mensaje |
|---|---|---|
| Victoria | El jugador entra a la casilla meta `(14,14)` | **"¡HAS GANADO!"** + "Llegaste a la meta en X turnos" |
| Derrota | Captura (6.4) | **"GAME OVER"** + "El fantasma te atrapó" |

En ambas pantallas: `R` = jugar de nuevo (**nuevo laberinto al azar**, sección 4.3), `M` = volver al menú, `ESC` = salir.

## 7. Algoritmo del fantasma: backtracking

### 7.1 Idea
Búsqueda en profundidad desde la casilla del fantasma, guardando el camino actual en una **pila**:
- **Apilar:** avanzar a un vecino accesible no visitado.
- **Desapilar (retroceder):** si la casilla de la cima no tiene más vecinos por probar (callejón sin salida o ramas ya agotadas), se saca de la pila y se vuelve a la anterior.
- **Encontrado:** cuando la cima es la casilla del jugador, el contenido de la pila (de abajo hacia arriba) **es** el camino.

Como el laberinto es perfecto, el camino encontrado es el único posible y por lo tanto el más corto.

### 7.2 Contrato

```python
from typing import Literal, NamedTuple

Casilla = tuple[int, int]

class Evento(NamedTuple):
    tipo: Literal["apilar", "desapilar", "encontrado"]
    casilla: Casilla          # casilla apilada / desapilada / destino
    pila: tuple[Casilla, ...] # copia de la pila DESPUÉS del evento (de base a cima)

def buscar_camino_con_traza(laberinto, origen: Casilla, destino: Casilla
                            ) -> tuple[list[Casilla], list[Evento]]:
    """Devuelve (camino, traza).
    camino: casillas desde el paso siguiente a `origen` hasta `destino` (incluido);
            [] si origen == destino.
    traza:  eventos en orden; el primero es apilar(origen) y el último es encontrado(destino).
    Lanza ValueError si no existe camino (no debe ocurrir en un laberinto perfecto)."""

def buscar_camino(laberinto, origen: Casilla, destino: Casilla) -> list[Casilla]:
    """Atajo: devuelve solo el camino."""
```

### 7.3 Pseudocódigo (versión iterativa con pila explícita)

Se usa **pila explícita** en vez de recursión, porque así la pila que se dibuja en el tarro es literalmente la estructura del algoritmo. Es equivalente a la versión recursiva: la pila de llamadas se vuelve visible.

```
pila      ← [origen];  visitados ← {origen};  registrar apilar(origen)
mientras pila no esté vacía:
    actual ← cima(pila)
    si actual == destino:
        registrar encontrado(destino);  retornar pila[1:]
    vecino ← primer vecino accesible de actual NO visitado
             (orden fijo: arriba, derecha, abajo, izquierda)
    si existe vecino:
        apilar(vecino);  visitados += {vecino};  registrar apilar(vecino)
    si no:
        desapilar();  registrar desapilar(actual)          # <- backtracking
lanzar ValueError
```

- Tamaño máximo de la pila: 225 casillas.
- El camino se recalcula **en cada turno** del fantasma, porque el jugador se mueve.
- El orden fijo de vecinos hace la traza **determinista**: misma posición = misma animación (útil para explicar en clase).

## 8. Visualizador de backtracking (nuevo en 1.1)

### 8.1 Concepto
Se usan **dos vistas sincronizadas** de la misma traza:
1. **El tarro (panel derecho):** la pila dibujada como un frasco vertical de vidrio. Cada casilla apilada cae al tarro como un bloque con su coordenada. Al retroceder, el bloque de la cima sale por arriba.
2. **El tablero:** cada casilla se colorea según su estado en la búsqueda (en la pila, descartada, explorándose ahora). Así se ve **dónde** está cada elemento de la pila.

Los dos se animan con el mismo reloj: cada evento de la traza actualiza el tarro y el tablero a la vez.

### 8.2 El tarro (panel derecho, x = 640..920)

| Elemento | Especificación |
|---|---|
| Título | "Pila del backtracking" en y = 20, centrado en el panel |
| Tarro | Contorno gris de 3 px, 160 px de ancho × 460 px de alto, centrado en el panel, de y = 60 a y = 520. Lados y fondo con esquinas inferiores redondeadas (radio 16 px) y boca abierta arriba con un borde ligeramente más ancho (180 px). |
| Bloques | Rectángulos de 140 × 20 px con 2 px de separación, apilados **de abajo hacia arriba**. Texto centrado `(c,f)`. Caben **20 bloques** visibles. |
| Base de la pila | El primer bloque (la casilla del fantasma) lleva el texto `(c,f) 👻` o la etiqueta "inicio". |
| Cima | Borde naranja oscuro de 3 px y una flecha `← cima` a la derecha del tarro. |
| Desbordamiento | Si la pila tiene más de 20 elementos, se dibujan los 19 de arriba y el bloque inferior muestra `… +K más` en gris. |
| Animación apilar | El bloque nuevo aparece arriba de la boca del tarro y **cae** a su posición en 0.12 s. |
| Animación desapilar | El bloque de la cima se pone rojo claro y **sube** fuera del tarro, desvaneciéndose en 0.12 s. |
| Encontrado | Todos los bloques del tarro se pintan de naranja intenso y parpadean 2 veces. |

Debajo del tarro (y = 530..640), contadores y mensaje:
- `Apilados: A`  `Desapilados (retrocesos): R`
- `Profundidad actual: P`  `Máxima: M`
- Mensaje del último evento, por ejemplo:
  - `Apilar (4,2): avanzo a un vecino libre`
  - `Desapilar (6,3): callejón sin salida, retrocedo`
  - `¡Encontrado! Camino de L pasos`

Cuando no hay búsqueda en curso (turno del jugador antes de que aparezca el fantasma), el panel muestra el tarro vacío y el texto "Esperando al fantasma…".

### 8.3 Marcas sobre el tablero
Durante la animación, en cada evento:
- Casillas **en la pila** → relleno naranja.
- Casillas **desapiladas** → relleno gris rosado (zona descartada).
- **Cima** → borde naranja oscuro.
- Al terminar: el camino encontrado queda en naranja intenso mientras el fantasma camina por él. Las casillas descartadas siguen visibles.
- Las marcas se **borran** cuando el jugador tira el dado en su siguiente turno.
- Las marcas se dibujan **debajo** de las paredes, el jugador y el fantasma (no tapan nada).

### 8.4 Velocidad y controles del visualizador
Una búsqueda puede tener cientos de eventos, así que la velocidad se adapta:
- Intervalo entre eventos: `max(0.03 s, 4.0 s / número_de_eventos)`, con un **tope de ~4 s** por búsqueda en velocidad normal y un mínimo de 30 ms por evento para que se alcance a ver.
- Teclas, activas solo durante la animación de la búsqueda:

| Tecla | Acción |
|---|---|
| `+` / `-` | Duplicar / reducir a la mitad la velocidad (×0.25 … ×4) |
| `P` | Pausar / reanudar |
| `N` | Con la animación pausada: avanzar **un** evento (modo paso a paso para explicar en clase) |
| `S` | Saltar la animación (mostrar el resultado final de inmediato) |

- Opción en la pantalla de inicio: `V` activa/desactiva el visualizador (por defecto **activado**). Desactivado, el panel sigue visible pero la búsqueda no se anima: muestra directamente el estado final.

### 8.5 Separación de responsabilidades
- `fantasma_ia.py` genera la traza (lógica pura, sin pygame, se prueba con pytest).
- `visualizador.py` tiene la clase `ReproductorTraza`: recibe la traza y, según el tiempo transcurrido, expone `evento_actual`, `pila_visible`, el estado de cada casilla (`"en_pila" | "descartada" | None`) y los contadores. No dibuja; se puede probar sin ventana.
- `dibujo.py` solo pinta lo que expone `ReproductorTraza`.

### 8.6 Otras ideas consideradas
| Idea | Decisión |
|---|---|
| **Árbol de recursión** (cada llamada es un nodo y las ramas descartadas quedan tachadas) | Descartada para v1.1: con 225 casillas el árbol no cabe en 280 px. Queda como mejora futura con zoom. |
| **Mostrar solo el tablero coloreado** | Insuficiente: no muestra la estructura LIFO, que es el punto didáctico. |
| **Tarro + tablero sincronizados** | **Elegida**: el tarro enseña la estructura (pila) y el tablero enseña su significado (el camino en el laberinto). |

## 9. El dado

- **D-1** Valores enteros uniformes en `1..6` (`random.randint(1, 6)`).
- **D-2** Se dibuja en el panel inferior: cuadrado blanco de 60 × 60 px con borde negro de 3 px y puntos negros según la cara.
- **D-3** Animación de tirada: durante `0.6 s` se muestran caras aleatorias cambiando cada `0.06 s`; luego se fija el valor.
- **D-4** Hay un dado por actor, con la etiqueta "Jugador" o "Fantasma", para que se vea la última tirada de cada uno.
- **D-5** Se puede pasar una semilla por línea de comandos (`--semilla 123`) para partidas reproducibles (necesario para pruebas). La misma semilla controla el laberinto elegido o generado, los dados y la casilla de aparición del fantasma. Hay un único `random.Random(semilla)` compartido para la lógica; sin semilla se usa una aleatoria.
- **D-6** Las caras que giran durante la animación (D-3) son solo visuales y salen de un **generador aparte** (`random.Random()` sin semilla). Nunca consumen números del generador de la lógica, así que la animación no cambia los resultados de una partida con semilla.

## 10. Interfaz y pantallas

### 10.1 Pantalla de inicio
- Título "El Laberinto del Fantasma".
- Texto "G: laberinto [GENERADO / PREDEFINIDO AL AZAR]" (por defecto GENERADO).
- Texto "V: visualizador de backtracking [ACTIVADO/DESACTIVADO]".
- Texto "ENTER para comenzar".
- Sin vista previa: el laberinto es sorpresa y se elige al pulsar ENTER.

### 10.2 Pantalla de juego
- Laberinto, entrada, meta, marcas de la búsqueda, personaje y (si ya apareció) fantasma.
- Panel derecho: visualizador (sección 8).
- **Panel inferior (HUD)**, de izquierda a derecha:
  - `Turno: N`
  - Dado del jugador y dado del fantasma (última tirada).
  - Estado:
    - `"Tu turno: pulsa ESPACIO para tirar"`
    - `"Mueve con las flechas: quedan X pasos · ENTER para terminar"`
    - `"¡Apareció el fantasma!"` (1 s)
    - `"El fantasma busca tu rastro…  (P pausa · N paso · S saltar · +/- velocidad)"`
    - `"El fantasma avanza…"`

### 10.3 Pantallas finales
- Capa semitransparente sobre el tablero (negro con alfa 160) y mensaje centrado:
  - Victoria: **"¡HAS GANADO!"** en verde, fuente de 64 px.
  - Derrota: **"GAME OVER"** en rojo, fuente de 64 px.
- Subtítulo con la cantidad de turnos y las instrucciones `R / M / ESC`.

### 10.4 Controles

| Tecla | Acción | Activa en |
|---|---|---|
| `G` | Alternar origen del laberinto (generado / predefinido al azar) | Inicio |
| `V` | Activar/desactivar visualizador | Inicio |
| `ENTER` | Comenzar partida | Inicio |
| `ESPACIO` | Tirar el dado | Turno del jugador (antes de tirar) |
| `↑ ↓ ← →` | Mover un paso | Turno del jugador (con pasos restantes) |
| `ENTER` | Terminar el turno antes de tiempo | Turno del jugador (después de tirar) |
| `P` / `N` / `S` / `+` / `-` | Controles del visualizador (8.4) | Búsqueda del fantasma |
| `R` | Reiniciar | Fin de partida |
| `M` | Volver al menú | Fin de partida |
| `ESC` | Volver al menú (la partida en curso se abandona sin confirmar) | Partida y pantallas finales |
| `ESC` | Salir del juego | Inicio |
| Cerrar ventana (X) | Salir de inmediato, sin confirmar (no hay nada que guardar) | Siempre |

Las teclas que no correspondan al estado actual se ignoran (por ejemplo, flechas mientras se mueve el fantasma).

## 11. Máquina de estados

```
INICIO --ENTER (elige/genera laberinto al azar)--> JUGADOR_TIRAR
JUGADOR_TIRAR --ESPACIO--> DADO_JUGADOR (0.6 s) --> JUGADOR_MOVER
JUGADOR_MOVER --llega a meta--> VICTORIA
JUGADOR_MOVER --entra a la casilla del fantasma--> DERROTA
JUGADOR_MOVER --pasos=0 o ENTER, turno 1--> APARECE_FANTASMA (1 s) --> DADO_FANTASMA
JUGADOR_MOVER --pasos=0 o ENTER, turno>1--> DADO_FANTASMA
DADO_FANTASMA (0.6 s) --> FANTASMA_BUSCA
FANTASMA_BUSCA (animación de la traza; S la salta) --> FANTASMA_MOVER
FANTASMA_MOVER (0.25 s/paso) --alcanza al jugador--> DERROTA
FANTASMA_MOVER --termina pasos--> JUGADOR_TIRAR (turno + 1)
VICTORIA / DERROTA --R (nuevo laberinto al azar)--> JUGADOR_TIRAR | --M o ESC--> INICIO
(cualquier estado de partida) --ESC--> INICIO
INICIO --ESC--> salir
(cualquier estado) --cerrar ventana--> salir
```

## 12. Arquitectura (archivos)

```
Laberinto/
├── SPEC.md                  # este documento
├── generar_laberintos.py    # ya existe: genera laberintos.json y PNG
├── laberintos.json          # ya existe: datos de los 5 laberintos
├── config.py                # constantes de las secciones 4.1, 4.2 y 8
├── laberinto.py             # clase Laberinto: carga JSON, generar_backtracking(), elegir_al_azar(), hay_pared(), vecinos_accesibles(), distancias_desde()
├── simulacion.html          # prototipo visual de referencia (sección 18), no es parte del juego Python
├── fantasma_ia.py           # buscar_camino_con_traza() / buscar_camino() (sección 7)
├── visualizador.py          # ReproductorTraza: reproduce la traza en el tiempo (sección 8.5)
├── dado.py                  # clase Dado: tirar(), estado de animación
├── juego.py                 # lógica pura: estado, turnos, reglas, aparición del fantasma
├── dibujo.py                # todo el render con pygame (tablero, tarro, HUD, pantallas)
├── main.py                  # bucle principal, eventos de teclado, argumento --semilla
├── requirements.txt         # pygame, pytest, pytest-cov
└── tests/
    ├── test_laberinto.py
    ├── test_fantasma_ia.py
    ├── test_visualizador.py
    ├── test_dado.py
    └── test_juego.py
```

**Regla de diseño:** `juego.py`, `laberinto.py`, `fantasma_ia.py`, `visualizador.py` y `dado.py` **no importan pygame**, así que se pueden probar con `pytest` sin abrir ventana. Solo `dibujo.py` y `main.py` usan pygame.

**Ejecución (única forma de distribución):**
```
pip install -r requirements.txt
python main.py [--semilla N]
```
No se empaqueta como ejecutable.

**Pruebas:**
```
pytest --cov=laberinto --cov=fantasma_ia --cov=visualizador --cov=dado --cov=juego --cov-report=term-missing --cov-fail-under=80
```

## 13. Criterios de aceptación (verificables con pytest)

| ID | Criterio |
|---|---|
| CA-01 | `Laberinto` carga los 5 laberintos del JSON; cada uno tiene 15×15 casillas. |
| CA-02 | `vecinos_accesibles((0,0))` del laberinto 1 coincide con las paredes del `grid`. |
| CA-03 | `buscar_camino` devuelve un camino donde cada par de casillas consecutivas es vecino sin pared, empieza junto al origen y termina en el destino. |
| CA-04 | `buscar_camino(a, a)` devuelve `[]`. |
| CA-05 | Desde `(0,0)` hasta `(14,14)` existe camino en los 5 laberintos. |
| CA-06 | 10 000 tiradas de `Dado` producen solo valores en `1..6` y aparecen las 6 caras. |
| CA-07 | Un movimiento del jugador contra una pared no cambia su posición ni los pasos restantes. |
| CA-08 | El jugador no puede moverse con 0 pasos restantes. |
| CA-09 | El fantasma **no existe** antes de que termine el primer turno del jugador y aparece justo después. |
| CA-10 | En 10 000 apariciones simuladas (jugador en posiciones al azar), el fantasma **nunca** aparece a menos de 6 pasos del jugador ni en la meta. |
| CA-11 | Con el jugador a distancia 3 del fantasma y un dado de 5, el fantasma lo captura **en su 3.er paso** y el estado pasa a `DERROTA` (cruce = captura). |
| CA-12 | Con el jugador a distancia 8 y un dado de 4, el fantasma avanza exactamente 4 casillas por el camino y no hay captura. |
| CA-13 | Si el jugador entra a `(14,14)` con pasos de sobra, el estado pasa a `VICTORIA`. |
| CA-14 | Si el jugador entra a la casilla del fantasma, el estado pasa a `DERROTA` aunque le queden pasos. |
| CA-15 | Tras tirar un 5 y moverse 2 pasos, `ENTER` termina el turno y pasa al fantasma. `ENTER` antes de tirar el dado no hace nada. |
| CA-16 | Con la misma `--semilla`, la secuencia de dados y la casilla de aparición del fantasma son idénticas. |
| CA-17 | La traza empieza con `apilar(origen)` y termina con `encontrado(destino)`; la pila del último evento, sin el origen, es igual al camino devuelto. |
| CA-18 | En la traza, `#apilar − #desapilar = len(camino) + 1`, y nunca se desapila con la pila vacía. |
| CA-19 | Cada `desapilar(c)` en la traza ocurre cuando `c` es la cima y ya no tiene vecinos accesibles sin visitar. |
| CA-20 | Para el mismo laberinto, origen y destino, la traza es idéntica en dos ejecuciones (determinista). |
| CA-21 | `ReproductorTraza` en el instante `t` expone una `pila_visible` igual a la pila del último evento reproducido hasta `t`, y contadores coherentes con esos eventos. |
| CA-22 | `ReproductorTraza.saltar()` deja el estado igual al del último evento de la traza. |
| CA-23 | La ventana mide 920 × 740 px, las paredes se dibujan con 4 px y el tarro muestra como máximo 20 bloques con indicador `… +K más`. **Revisión visual manual** (ver 13.1). |
| CA-24 | `R` reinicia: jugador en `(0,0)`, sin fantasma, sin marcas de búsqueda, turno 1, y un laberinto nuevo elegido al azar. |
| CA-25 | 100 laberintos generados con `generar_backtracking` tienen exactamente 224 pasos abiertos, todas las casillas conectadas y camino de `(0,0)` a `(14,14)`. Cada uno se genera en menos de 50 ms. |
| CA-26 | En modo predefinido, 1 000 elecciones al azar usan los 5 laberintos y nunca repiten dos veces seguidas el mismo. |
| CA-27 | `distancias_desde(c)` da 0 en `c` y, para cada casilla, el mismo valor que `len(buscar_camino(c, casilla))`. |

## 14. Requisitos no funcionales
- **RNF-1** El juego corre a 60 FPS en un portátil normal (macOS, Windows o Linux), también durante la animación del tarro.
- **RNF-2** El código, los textos de la interfaz y los comentarios están en español.
- **RNF-3** Sin recursos externos (imágenes, sonidos ni fuentes descargadas): fuente por defecto de pygame. Si el emoji 👻 no se ve con la fuente por defecto, se usa la etiqueta "inicio".
- **RNF-4** `buscar_camino_con_traza` responde en menos de 10 ms en un laberinto de 15×15.

## 15. Mejoras futuras (no implementar en v1.1)
- Resaltar en amarillo las casillas alcanzables con el dado actual del jugador.
- Dificultad: el fantasma con dado de 1–4 (fácil) o 1–8 (difícil).
- Comparar en el visualizador backtracking contra BFS (cola en vez de pila).
- Árbol de recursión con zoom (8.6).
- Varios fantasmas, objetos (bonus de pasos, trampas), sonido.
- Mostrar en el tarro la **generación** del laberinto al inicio de la partida (la generación también usa una pila).

## 16. Decisiones resueltas
| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿El jugador puede terminar su turno sin usar todos los pasos? | **Sí**, con `ENTER` (RJ-2). |
| 2 | ¿Cruzarse cuenta como captura? | **Sí** (6.4). |
| 3 | ¿Dónde aparece el fantasma? | **Casilla al azar**, excepto la del jugador y la meta (5.2). |
| 4 | ¿Cómo se muestra el backtracking? | **Tarro (pila) + tablero coloreado, sincronizados** (sección 8). |
| 5 | ¿Distancia mínima de aparición del fantasma? | **Sí, 6 pasos** por el camino del laberinto (5.2). |
| 6 | ¿Qué laberinto se juega? | **Al azar**: generado nuevo (por defecto) o uno de los 5 predefinidos (4.3). |

## 17. Decisiones abiertas
Ninguna.

## 18. Simulación de referencia
`simulacion.html` es un prototipo jugable en el navegador. Implementa esta spec (tablero, dado, fantasma, captura, tarro y marcas en el tablero) para validar la experiencia **antes** de escribir el código Python. No es el entregable: si la simulación y esta spec no coinciden, **manda la spec**. Cualquier cambio que surja al probar la simulación se registra primero aquí (nueva versión) y después se aplica.
