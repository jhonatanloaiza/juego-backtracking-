"""Genera 5 laberintos de 15x15 con algoritmos distintos.

Salida:
  laberinto_N_<tipo>.png  -> imagen fondo blanco, paredes negras
  laberintos.json         -> cuadricula 31x31 ('#' pared, ' ' camino) para el juego
  todos.png               -> vista conjunta
Entrada: arriba-izquierda. Salida: abajo-derecha.
"""
import json
import random
from collections import deque
from PIL import Image, ImageDraw

N = 15          # celdas por lado
CELDA = 40      # px por celda
MARGEN = 20
SEMILLA = 2026  # fija para que los laberintos sean siempre los mismos


def vecinos(x, y):
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < N and 0 <= ny < N:
            yield nx, ny


def backtracker(rnd):
    """Pasillos largos y sinuosos, pocos callejones."""
    pasos, visit, pila = set(), {(0, 0)}, [(0, 0)]
    while pila:
        c = pila[-1]
        libres = [v for v in vecinos(*c) if v not in visit]
        if not libres:
            pila.pop()
            continue
        v = rnd.choice(libres)
        pasos.add(frozenset((c, v)))
        visit.add(v)
        pila.append(v)
    return pasos


def prim(rnd):
    """Muchas ramas cortas y callejones sin salida."""
    pasos, dentro = set(), {(0, 0)}
    frontera = [((0, 0), v) for v in vecinos(0, 0)]
    while frontera:
        a, b = frontera.pop(rnd.randrange(len(frontera)))
        if b in dentro:
            continue
        pasos.add(frozenset((a, b)))
        dentro.add(b)
        frontera += [(b, v) for v in vecinos(*b) if v not in dentro]
    return pasos


def kruskal(rnd):
    """Textura uniforme, sin dirección dominante."""
    padre = {(x, y): (x, y) for x in range(N) for y in range(N)}

    def raiz(c):
        while padre[c] != c:
            padre[c] = padre[padre[c]]
            c = padre[c]
        return c

    aristas = [((x, y), v) for x in range(N) for y in range(N)
               for v in vecinos(x, y) if v > (x, y)]
    rnd.shuffle(aristas)
    pasos = set()
    for a, b in aristas:
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[ra] = rb
            pasos.add(frozenset((a, b)))
    return pasos


def arbol_binario(rnd):
    """Sesgo diagonal: corredores abiertos en el borde superior e izquierdo."""
    pasos = set()
    for y in range(N):
        for x in range(N):
            opciones = []
            if y > 0:
                opciones.append((x, y - 1))
            if x > 0:
                opciones.append((x - 1, y))
            if opciones:
                pasos.add(frozenset(((x, y), rnd.choice(opciones))))
    return pasos


def sidewinder(rnd):
    """Corredores horizontales largos conectados hacia arriba."""
    pasos = set()
    for y in range(N):
        tramo = []
        for x in range(N):
            tramo.append((x, y))
            cerrar = x == N - 1 or (y > 0 and rnd.random() < 0.5)
            if cerrar:
                if y > 0:
                    cx, cy = rnd.choice(tramo)
                    pasos.add(frozenset(((cx, cy), (cx, cy - 1))))
                tramo = []
            else:
                pasos.add(frozenset(((x, y), (x + 1, y))))
    return pasos


def a_cuadricula(pasos):
    """Celdas+paredes -> matriz (2N+1)x(2N+1) con entrada y salida abiertas."""
    t = 2 * N + 1
    g = [['#'] * t for _ in range(t)]
    for y in range(N):
        for x in range(N):
            g[2 * y + 1][2 * x + 1] = ' '
    for p in pasos:
        (x1, y1), (x2, y2) = tuple(p)
        g[y1 + y2 + 1][x1 + x2 + 1] = ' '
    g[1][0] = ' '            # entrada
    g[t - 2][t - 1] = ' '    # salida
    return [''.join(f) for f in g]


def resoluble(grid):
    t = len(grid)
    ini, fin = (1, 0), (t - 2, t - 1)
    vistos, cola = {ini}, deque([ini])
    while cola:
        f, c = cola.popleft()
        if (f, c) == fin:
            return True
        for df, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nf, nc = f + df, c + dc
            if 0 <= nf < t and 0 <= nc < t and grid[nf][nc] == ' ' and (nf, nc) not in vistos:
                vistos.add((nf, nc))
                cola.append((nf, nc))
    return False


def dibujar(pasos, titulo):
    lado = N * CELDA + 2 * MARGEN
    img = Image.new('RGB', (lado, lado + 30), 'white')
    d = ImageDraw.Draw(img)
    d.text((MARGEN, lado + 5), titulo, fill='black')

    def linea(x1, y1, x2, y2):
        d.line([(MARGEN + x1 * CELDA, MARGEN + y1 * CELDA),
                (MARGEN + x2 * CELDA, MARGEN + y2 * CELDA)], fill='black', width=4)

    for y in range(N):
        for x in range(N):
            if y == 0:
                linea(x, 0, x + 1, 0)
            if x == 0 and y != 0:                       # hueco = entrada
                linea(0, y, 0, y + 1)
            if x == N - 1 and y != N - 1:               # hueco = salida
                linea(N, y, N, y + 1)
            elif x < N - 1 and frozenset(((x, y), (x + 1, y))) not in pasos:
                linea(x + 1, y, x + 1, y + 1)
            if frozenset(((x, y), (x, y + 1))) not in pasos:
                linea(x, y + 1, x + 1, y + 1)
    return img


TIPOS = [
    ('backtracker', backtracker, 'Backtracking recursivo - pasillos largos'),
    ('prim', prim, 'Prim - muchas ramas cortas'),
    ('kruskal', kruskal, 'Kruskal - textura uniforme'),
    ('arbol_binario', arbol_binario, 'Arbol binario - sesgo diagonal'),
    ('sidewinder', sidewinder, 'Sidewinder - corredores horizontales'),
]

if __name__ == '__main__':
    rnd = random.Random(SEMILLA)
    datos, imagenes = [], []
    for i, (clave, algoritmo, desc) in enumerate(TIPOS, 1):
        pasos = algoritmo(rnd)
        assert len(pasos) == N * N - 1, clave   # arbol de expansion: todas las celdas conectadas
        grid = a_cuadricula(pasos)
        assert resoluble(grid), clave
        img = dibujar(pasos, f'Laberinto {i}: {desc}')
        img.save(f'laberinto_{i}_{clave}.png')
        imagenes.append(img)
        datos.append({'id': i, 'tipo': clave, 'descripcion': desc,
                      'entrada': [1, 0], 'salida': [2 * N - 1, 2 * N], 'grid': grid})

    with open('laberintos.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    w, h = imagenes[0].size
    todos = Image.new('RGB', (w * 3, h * 2), 'white')
    for i, img in enumerate(imagenes):
        todos.paste(img, ((i % 3) * w, (i // 3) * h))
    todos.save('todos.png')
    print('OK: 5 laberintos generados y verificados')
