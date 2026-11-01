# Análisis de la referencia y plantilla "doble exposición B/N + letra palabra por palabra"

Fuente: `TikVid.io_7548994381039078712.mp4` (los dos archivos subidos son idénticos: MD5 `c79eed81ff461c62cd1a27ebf647d914`).
Cobertura: los 674 cuadros decodificados y revisados en hojas de contacto (12 hojas × 60 cuadros); ampliación a
resolución completa en transiciones de texto y destellos. Mediciones con los scripts de `analisis/`
(esperan los cuadros extraídos en `/tmp/r3/f/%04d.png`; ver sección 9).

## 1. Datos técnicos

| Campo | Valor |
|---|---|
| Resolución | 768×576 (4:3) |
| FPS | 30 constante (674 cuadros, PTS regulares) |
| Duración | 22.467 s |
| Video | H.264 High, yuv420p, BT.709, ~0.87 Mb/s |
| Audio | HE-AACv2 44.1 kHz estéreo, 32 kb/s; −18.3 LUFS integrado |
| Color | gris puro (diferencia media |RGB−L| = 0.01) |

## 2. Estructura global

- **La imagen es un bucle de 242 cuadros (8.067 s) repetido ~2.8 veces.** Correlación entre el cuadro *i* y el *i+242*:
  0.916 de media (0.63 a ±1 cuadro). Las diferencias se deben al texto y al fundido final.
- **Doble exposición permanente**: capa base ("historia") + capa de destellos que cambia cada ~0.1 s.
- **Letra palabra por palabra**, centrada, sin comillas ni créditos.
- 0–2.07 s sin texto (introducción); texto hasta 20.70 s; fundido a negro 20.45 → 21.95 s; negro hasta el final.

## 3. Imagen

### 3.1 Cadencia
La imagen cambia cada 2–3 cuadros: retenciones dentro del bucle = 20 de 1 cuadro, 68 de 2, 27 de 3 (media 2.06).
Equivale a ~14 imágenes/s sobre 30 fps (efecto "posterize time"). La plantilla usa `fps_efectivo = 14`.

### 3.2 Capa de destellos (ciclo medido)
Los mismos planos reaparecen cada **32.5 cuadros (1.083 s)**: rayas blancas en 21, 53, 86, 119, 151, 184, 216;
interior de teatro en 31, 63, 96, 129, 161, 194, 226; bokeh en 14, 46, 79, 112, 144, 177, 209.
Correlación media a desfase 32–33 cuadros: 0.55–0.56. 32.5 cuadros = 2 tiempos a ~111 BPM; el tempo
estimado del audio por autocorrelación es 112.3 BPM (estimación automática, no verificada por escucha).

Orden dentro de un ciclo (desde el cuadro 42), descripción visual:

| Desfase (cuadros) | Plano |
|---|---|
| 0 | marco de puerta/columna oscura |
| 2 | bailarines entre nubes |
| 4 | bokeh de luces en diagonal |
| 6 | hombre con gorra en la playa |
| 9 | variante del anterior |
| 11 | rayas/manos blancas (fuga de luz) |
| 13 | remolino / silueta |
| 14 | figura en niebla blanca |
| 17 | transición clara |
| 21 | interior de teatro sobreexpuesto |
| 24 | remolino desenfocado blanco |
| 28 | pelo al viento |
| 31 | vuelve el marco oscuro |

### 3.3 Capa base dentro del bucle (estimación visual)

| Cuadros | s | Contenido |
|---|---|---|
| 0–59 | 0.0–2.0 | figura con brazos abiertos en baranda junto al mar |
| 60–95 | 2.0–3.2 | pareja besándose a contraluz |
| 96–120 | 3.2–4.0 | pareja + tulipán translúcido + luces de muelle |
| 121–180 | 4.0–6.0 | pareja corriendo/abrazada en calle (tulipán translúcido a la izquierda) |
| 181–241 | 6.0–8.07 | mujer con pelo al viento en playa |

El tulipán translúcido se modela como capa "fantasma" opcional (opacidad ~0.3; valor estimado).

### 3.4 Mezcla
Los mismos destellos sobre fondos distintos dan medianas de 48 a 136 y percentil 99.5 de 200 a 255: el fondo
pesa tanto como el destello. Se modela como mezcla normal al 50 %. **No hay evidencia verificable del modo
de fusión ni del porcentaje exactos.**

### 3.5 Tono y acabado

| Medida | Valor |
|---|---|
| Percentiles de luminancia (media de cuadros) p1/p5/p25/p50/p75/p95/p99 | 8 / 15 / 41 / 77 / 118 / 173 / 218 |
| Mediana por cuadro | entre 17 y 207 (cuadros muy oscuros y muy claros alternados) |
| Viñeta (luminancia media por radio) | centro 95 → esquinas 59 |
| Textura | aspecto suavizado tipo pintura, sin grano apreciable (causa no verificable) |

La plantilla aplica una curva tonal global que lleva el histograma del montaje al de la referencia
(`ref_tono.json`, intensidad 0.85), desenfoque gaussiano 0.8 px (en la escala de 768), viñeta 0.30, grano σ=4.

## 4. Texto

### 4.1 Tipografía y color

| Campo | Valor medido |
|---|---|
| Fuente | sans tipo Arial condensada (proporción ancho/alto ≈ 0.82 de Arial = Arial Narrow). Plantilla: Liberation Sans (métrica de Arial) al 82 % de ancho |
| Grosor del trazo | 8 px con em 109 (0.073 em) |
| Color | gris claro 222–225, opaco |
| Brillo / sombra / contorno | ninguno (el fondo junto al trazo mantiene su valor; borde de 1 px) |
| Caja | minúsculas tal como se cantan |

### 4.2 Composición (px en 768×576)
- Bloque alineado a la izquierda internamente, **centro de la caja de tinta en (382–384, 280–288)**.
- Interlineado 1.10–1.15 em (plantilla: 1.13).
- **Líneas con 2+ palabras justificadas al ancho de la línea más ancha** (por eso "you      in", "what        i").
  Las palabras aún no cantadas de las líneas ya abiertas reservan su sitio.
- Tamaño (em) según número de líneas visibles: 1 palabra/1 línea 109–208 (ajuste a ~262 px de ancho, tope 200);
  2 líneas 73–109 (plantilla 92); 3 líneas 66–77 (plantilla 70); ancho máximo medido del bloque 337 px.
- Dos palabras que en la frase final van en la misma línea se apilan (una por línea) si así salen ≥25 % más grandes:
  "she / knows", "and / what", "one / love" se apilan; "and I'll", "you in" quedan en una línea.

### 4.3 Transiciones (medidas cuadro a cuadro)
- **Si la composición cambia** (cambio de número de líneas, tamaño o frase): distorsión de 2 cuadros
  (moda medida; rango 1–4): ondulación horizontal suave, arrastre horizontal y doble imagen tenue;
  1.er cuadro = composición vieja distorsionada + nueva tenue; 2.º = nueva distorsionada leve; luego limpia.
- **Si solo se añade una palabra en su sitio reservado**: fundido de 3 cuadros (≈35 %, 75 %, 100 %) sin distorsión
  (ej.: "high" 240–242, "i" 384–385, "think" 453–455).
- Salida final del texto: distorsión de 2 cuadros (620–621), desaparece en 622.

### 4.4 Tiempos de palabra medidos (inicio de la transición, cuadro / s)

| Frase (composición final) | Palabras: cuadro (s) |
|---|---|
| touch / my / neck | touch 62 (2.067) · my 76 (2.533) · neck 94 (3.133) |
| and I'll / touch / yours | and 119 (3.967) · I'll 128 (4.267) · touch 139 (4.633) · yours 153 (5.100) |
| you in / those / little high | you 191 (6.367) · in 199 (6.633) · those 209 (6.967) · little 224 (7.467) · high 240 (8.000) |
| wasted / shorts / oh | "was" 256 (8.533) → "wasted" 271 (9.033) · shorts 286 (9.533) · oh 316 (10.533) |
| she knows / what i / think about | she 360 (12.000) · knows 369 (12.300) · what 379 (12.633) · i 384 (12.800) · think 388 (12.933) · about 398 (13.267) |
| and what / i think / about | and 439 (14.633) · what 446 (14.867) · i 449 (14.967) · think 453 (15.100) · about 463 (15.433) |
| one love / two / mouths | one 489 (16.300) · love 498 (16.600) · two 521 (17.367) · mouths 530 (17.667) |
| one love / one / house | one 557 (18.567) · love 565 (18.833) · one 587 (19.567) · house 593 (19.767) |

La referencia muestra "tough" en lugar de "touch" en la 1.ª frase (cuadros 96–119): se considera errata y no se
replica. La relación de estos tiempos con el inicio de cada sílaba cantada no se pudo verificar por escucha.

## 5. Final y audio

| Elemento | Medida |
|---|---|
| Fundido a negro (imagen) | 0.92 a 20.5 s, 0.49 a 20.9 s, 0.16 a 21.5 s, 0 a 21.95 s (≈lineal; desde 2.02 s antes del final hasta 0.52 s antes) |
| Audio: entrada | −55 dB → −17 dB en ~1.1 s |
| Audio: salida | −15 dB a 21.0 s → −32 dB a 22.2 s, luego silencio |
| Locución / efectos | ninguno; solo la canción |

## 6. Verificación de la plantilla (render de prueba con material provisional)

| Prueba | Resultado |
|---|---|
| Composición del texto: 24 estados comparados con máscaras de texto aisladas de la referencia (768×576) | escala media 0.98 (0.86–1.22), alto 0.99 (0.87–1.20); centro desplazado 1.1 px (x) y 4.0 px (y) de media |
| Estructura de cada estado (líneas, apilado, justificado, reserva de palabras) | igual en los 24 estados |
| Momento de cada cambio de texto | igual a la referencia cuadro a cuadro (hoja de comparación 360–399) |
| Tono (p1/p5/p25/p50/p75/p95/p99) | plantilla 4 / 10 / 41 / 79 / 126 / 184 / 220 vs referencia 8 / 15 / 41 / 77 / 118 / 173 / 218 |
| Cadencia (retenciones de 1/2/3/4 cuadros) | 2 / 69 / 14 / 9 (las de 4 se deben a imágenes fijas de prueba) vs referencia 20 / 68 / 27 / 0 |
| Bucle de 242 cuadros | correlación media 0.93 (referencia 0.916) |
| Render 1440×1080, 30 fps, 22.47 s | 2 min en 4 núcleos; −13.9 LUFS con `lufs: -14` |
| Lienzo 9:16 (barras negras) y render parcial `--desde/--hasta` | 1080×1920, duración correcta |

Material provisional usado en la prueba: cuadros sin texto de la propia referencia (cuadros 0–60, primeros 2 s) y el audio de la
referencia. No se incluye en el repositorio.

## 7. Uso

```bash
python3 render_dobleexpo.py config.json --preview 2.5,9.2,13.4
```

```bash
python3 render_dobleexpo.py config.json --out final.mp4
```

```bash
python3 render_dobleexpo.py config.json --solo-texto --preview 3.0
```

Campos de `config.json` (ver `config_plantilla.json`; `config_referencia.json` trae los tiempos medidos):

| Campo | Contenido |
|---|---|
| `duracion` | segundos del video |
| `salida` | `ancho`, `alto` (por defecto 1440×1080, 4:3 como la referencia), `fps` 30, `lienzo` `"4:3"` o `"9:16"` (4:3 con barras negras), `crf` 18 |
| `audio` | `archivo`, `inicio` (s dentro de la canción), `lufs` (−14 por defecto; `null` = sin normalizar) |
| `bucle` | duración del bloque de imagen que se repite (8.067 s como la referencia); `null` = sin repetición |
| `bpm` | opcional: ciclo de destellos = 2 tiempos; sin `bpm` se usa 32.5 cuadros |
| `base` | clips/imágenes "historia": `archivo`, `desde` (s en el bucle), `inicio_clip`, `enfoque` [x, y] |
| `destellos` | 8–13 clips/imágenes cortos; se reparten en los 13 huecos del ciclo |
| `fantasma` | opcional: `archivo`, `desde`, `hasta`, `opacidad` |
| `letra` | lista de frases: `lineas` (composición final con `\n`) y `tiempos` (uno por palabra); `"was\|wasted"` muestra una palabra parcial y luego la completa (consume 2 tiempos); `escala_1` opcional para palabras solas |
| `texto_fin` | segundo en que desaparece el texto |
| `look` | `fps_efectivo`, `mezcla_destellos`, `tono_ref`, `desenfoque`, `grano`, `vineta` |

## 8. Límites

- Modo y porcentaje de la doble exposición, valores de la capa fantasma y contenido exacto de cada plano: estimaciones visuales.
- El tamaño de palabra sola varía en la referencia (em 109–208) sin regla verificable; la plantilla usa una regla de ajuste a ancho (error ±15 %); `escala_1` permite corregir caso por caso.
- La sincronía letra–voz requiere los tiempos de la canción nueva (transcripción con marcas de tiempo + revisión).
- Las imágenes fijas no tienen movimiento interno: la plantilla aplica un acercamiento lento cuantizado; con video el resultado es más fiel.
- El render no usa Blender (no está instalado en este entorno); se genera con Python (NumPy/Pillow) + FFmpeg.

## 9. Reproducir el análisis

```bash
mkdir -p /tmp/r3/f && ffmpeg -i REFERENCIA.mp4 /tmp/r3/f/%04d.png
```

Después: `analisis/diff.py` (luminancia/diferencias), `sheet.py` (hojas de contacto), `sim.py`→`sim2.py`→`sim3.py`
(periodicidades y bucle), `pool.py` (destellos recurrentes), `holds.py` (cadencia), `tempo.py` (onsets/tempo;
requiere `/tmp/r3/a.raw`, ver encabezado), `tone.py` (tono/viñeta), `textmask.py` y `lines.py` (texto por estado),
`words.py` (aislamiento del texto restando la vuelta siguiente del bucle y detección de cambios).
