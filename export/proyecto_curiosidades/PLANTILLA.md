# Plantilla «Cuaderno de curiosidades»

Sistema para producir videos de curiosidades verticales (TikTok / Reels / Shorts) que no dependan de un prompt único de IA generativa. Claude interviene en investigación, guion, diseño de escenas y código; el render es procedural (Python + PIL + ffmpeg), por lo que cada cuadro es editable y la estética es propia.

```
proyecto_curiosidades/
├── ANALISIS.md                  análisis de la competencia (capturas)
├── PLANTILLA.md                 este documento
├── motor/cuaderno.py            motor de render
├── episodios/001_nudillos.json  episodio de ejemplo (guion + escenas + fuentes)
└── render/                      salidas (ignoradas por git)
```

## 1. Pipeline (7 pasos, en este orden)

| # | Paso | Responsable | Salida | Criterio de salida |
|---|---|---|---|---|
| 1 | Elegir tema | Tú + Claude | 1 pregunta | Pasa el filtro §2 (≥ 4/5) |
| 2 | Investigar | Claude (búsqueda web) | tabla `afirmaciones` | Cada dato con fuente primaria o institucional. Sin fuente → se elimina |
| 3 | Guion | Claude, revisas tú | `narracion` con tiempos | Estructura §3; 2,6–3,4 palabras/s |
| 4 | Storyboard | Claude | `escenas` (JSON) | Cada escena muestra un **mecanismo**, no un adorno |
| 5 | Render de prueba | motor | 4–6 fotogramas PNG | Revisión visual de zonas seguras, solapes, legibilidad |
| 6 | Voz | **Tú** (grabada) | `voz.wav` | Retemporizar `narracion` a la voz real (§6) |
| 7 | Render final + QA | motor + checklist §7 | `.mp4`, `.srt` | Checklist completo |

## 2. Filtro de tema (puntuar 0/1, producir con ≥ 4)

1. **Pregunta en segunda persona** que el espectador se ha hecho («¿por qué te…?»).
2. **Hay un mecanismo dibujable** (presión, química, órgano, física). Si solo hay un dato suelto, no sirve para este formato.
3. **Hay un personaje o caso real** (experimento, récord, historia) para el gancho.
4. **Existe fuente primaria verificable** (paper, institución).
5. **Encaja en el nicho de la serie** (no mezclar: ver ANALISIS §2.2).

Según los datos de ANALISIS §1, temas de cuerpo con componente tabú/escatológico y mascotas tuvieron los picos. Es correlación en una muestra pequeña, no regla.

## 3. Estructura narrativa (40–75 s)

| Bloque | Tiempo | Función | Regla |
|---|---|---|---|
| Gancho | 0–4 s | Caso humano + contraste visual | Sin saludo, sin título estático. Algo se mueve en el cuadro 1 |
| Tensión | 4–9 s | Por qué importa / quién dudaba | Un personaje con voz (cita, globo) |
| Pregunta | ~1,5 s | Cambio de escena con barrido | Una sola pregunta, gigante |
| Mecanismo | 15–25 s | Diagrama que se construye por capas | Etiquetar cada parte en el momento en que se nombra |
| Giro / debate | 5–8 s | Lo que la ciencia aún no cierra | Mostrar ambas posturas con su fuente |
| Resolución | 5–8 s | Volver al caso del gancho | Mismo plano del inicio (callback) |
| Honestidad | ~3 s | Límite del dato (n = 1, correlación, etc.) | Diferenciador de credibilidad |
| Cierre loop | ~3 s | Pregunta al espectador sobre sí mismo | El último plano empalma con el primero |

## 4. Sistema visual (qué lo separa de la «IA de un prompt»)

| Componente | Regla |
|---|---|
| Fondo | Papel con fibra y grano animado (3 capas alternadas a 10 fps), cuadrícula de cuaderno y margen rojo **en coordenadas de mundo**: se mueven con la cámara y dan profundidad |
| Tinta | Todo trazo tiene *line boil* (deformación suave que cambia ~10 veces/s). Imita animación a mano; un render 3D genérico no lo tiene |
| Color | Paleta fija por serie: tinta, papel, 1 acento (rojo), 1 color de contenido (azul), resaltador amarillo solo en subtítulos |
| Texturas | Trama de puntos (halftone) para fluidos y sombras; rayado a mano para volumen |
| Tipografía | Inter Display Black (títulos), Inter Bold (subtítulos), JetBrains Mono (datos y fuentes). Palabra clave entre `*asteriscos*` → color de acento |
| Fuentes en pantalla | Tarjeta mono con cinta adhesiva, entra deslizando cuando se dice el dato |
| Subtítulos | Placa de papel, palabra a palabra, resaltador detrás de la palabra actual; máx. 5 palabras por bloque |
| Sello | `CUADERNO DE CURIOSIDADES · N.º 00X` arriba a la izquierda, siempre igual |
| Cámara | Zoom/paneo/rotación con *easing*; empujar hacia el detalle cuando se nombra |
| Transición | Barrido de tinta diagonal con borde de acento + sonido «barrido» |

**Zonas seguras (1080×1920):** contenido entre y = 260 y y = 1330; subtítulos en y ≈ 1420; nada importante a la derecha de x = 940 ni debajo de y = 1500 (interfaz de TikTok).

Prohibido: personajes 3D genéricos, fondos degradados morados, títulos con «sticker» amarillo, imágenes que decoran sin explicar, voz TTS sin editar, datos sin fuente.

## 5. Formato del episodio (JSON)

Tiempos siempre **absolutos** en segundos. Cualquier número puede animarse con fotogramas clave: `[[t, valor, easing], ...]`, easing ∈ `lin, in, out, io, back`.

```jsonc
{
  "titulo": "...", "duracion": 48.0,
  "serie": {"sello": "CUADERNO DE CURIOSIDADES · N.º 001"},
  "estilo": {"paleta": {...}, "boil_fps": 10, "boil_px": 1.6, "sub_y": 1420, "sub_size": 56, "sub_palabras": 5},
  "afirmaciones": [{"dato": "...", "fuente": "...", "estado": "verificado"}],
  "narracion": [{"t": [0.2, 4.0], "txt": "...", "nota": "indicación para grabar"}],
  "sfx": [{"t": 1.0, "tipo": "crack", "vol": 0.9}],
  "escenas": [{"id": "gancho", "t": [0, 9.4], "transicion": "corte|barrido",
               "camara": {"z": ..., "cx": ..., "cy": ..., "rot": ...},
               "elementos": [ ... ]}]
}
```

### Primitivas (`elementos[].tipo`)

Comunes: `t: [entrada, salida]`, `fi`/`fo` (duración del fundido de entrada/salida), `sfx` (`pop|lapiz|crack|golpe|tick|barrido`) y `sfx_vol`.

| tipo | Parámetros | Uso |
|---|---|---|
| `texto` | `x, y, txt, size, fuente (titulo, titulo2, cuerpo, cuerpo_b, mono), color, acento, ancho, lh, entrada (pop, sube, fade), stagger, rot` | Títulos y etiquetas; `\n` = salto, `*palabra*` = acento |
| `trazo` | `pts, curva, grosor, color, flecha, punta, dibujo` | Flechas y líneas dibujándose |
| `marca` | `forma (circulo, check, cruz, subrayado), x, y, rx, ry, s, largo, grosor, color, dibujo` | Rodear, aprobar, tachar, subrayar a mano |
| `caja` | `x, y, w, h, r, relleno, trama, grosor, color, rot, entrada` | Paneles, comparaciones |
| `cita` | `x, y, w, h, cola, txt, size` | Globo de diálogo |
| `fuente` | `x, y, txt, size, etiqueta, rot` | Tarjeta de fuente |
| `contador` | `x, y, desde, hasta, cuenta: [t0, t1], prefijo, sufijo, size, ease` | Cifras que corren (con *ticks* de audio) |
| `mano` | `x, y, s, espejo, curl, marcar: [0..3], t_marca, dibujo` | Ilustración específica del episodio 001 |
| `articulacion` | `x, y, sep, burbuja, gas, t_pop` | Diagrama específico del episodio 001 |

Para un tema nuevo se agrega **una** ilustración específica (función `el_<nombre>` + entrada en `PRIM`), construida con `silhouette`, `stroke`, `fill_poly` y `halftone_fill`. Así cada episodio tiene un diagrama propio y la serie conserva el mismo trazo.

## 6. Voz (decisión de diferenciación)

La voz es el componente que más delata un video hecho en serie. Usar voz humana propia (o una voz con derechos y estilo consistente). Procedimiento:

1. Render con `narracion` estimada → genera `_locucion.txt` con cada línea, su ventana de tiempo y palabras/s.
2. Grabar mirando el video sin voz (lee la línea cuando aparece su subtítulo). Celular a 20 cm, cuarto con ropa/cortinas, sin música.
3. Ajustar `narracion[].t` a los inicios/finales reales (en Audacity/CapCut marcar cada línea) y desplazar los `t` de los elementos del mismo bloque.
4. Render final con `--voz voz.wav`: el motor baja los efectos ~55 % cuando hay voz (*ducking*).

La música va aparte: agregar en TikTok/CapCut desde la biblioteca con licencia comercial.

## 7. Checklist de QA (antes de publicar)

- [ ] Cada cifra en pantalla aparece en `afirmaciones` con fuente; las fuentes van en la descripción del video.
- [ ] Ningún texto en zona de interfaz; subtítulos no tapan el diagrama principal.
- [ ] Gancho: hay movimiento en el cuadro 1 y la promesa se entiende sin audio.
- [ ] Cada término técnico aparece etiquetado en el momento en que se dice.
- [ ] Velocidad de locución ≤ 3,4 palabras/s (ver `_locucion.txt`).
- [ ] Último plano empalma con el primero (loop).
- [ ] Revisar a velocidad normal y cuadro a cuadro las transiciones.
- [ ] Ortografía y tildes en pantalla y en `.srt`.
- [ ] Música con licencia; sin audio de terceros.
- [ ] Etiqueta de contenido IA según la política vigente de la plataforma si se usa algún elemento generado por IA.

## 8. Comandos

```bash
cd proyecto_curiosidades
# fotograma de prueba
python3 motor/cuaderno.py episodios/001_nudillos.json render/x.mp4 --fotograma 21.5 render/prueba.png
# tramo de prueba (solo 9–27 s)
python3 motor/cuaderno.py episodios/001_nudillos.json render/tramo.mp4 --desde 9 --hasta 27
# render completo (+ .srt + _locucion.txt)
python3 motor/cuaderno.py episodios/001_nudillos.json render/001_nudillos.mp4
# con voz grabada
python3 motor/cuaderno.py episodios/001_nudillos.json render/001_final.mp4 --voz voz.wav
```

Requisitos: Python 3, numpy, Pillow, ffmpeg, fuentes Inter / Inter Display / JetBrains Mono. Rendimiento medido: ~0,6–0,8 s por cuadro por núcleo (48 s ≈ 4–6 min en 4 núcleos).

## 9. Cómo usar a Claude en cada episodio

1. «Propón 10 temas del nicho X y puntúalos con el filtro §2.»
2. «Investiga el tema N: llena `afirmaciones` solo con fuentes primarias; marca lo no verificado.»
3. «Escribe `narracion` con la estructura §3, español latino, ≤ 3,4 pal/s.»
4. «Diseña `escenas` con las primitivas; crea una ilustración nueva para el mecanismo.»
5. «Renderiza fotogramas en 2, 10, 20, 30, 40 s y revisa solapes.»
6. «Retemporiza con estos tiempos de mi voz: …» → render final.
