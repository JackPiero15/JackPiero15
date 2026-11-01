# Análisis de referencias y plantilla "lyric aesthetic"

Fuentes analizadas: `TIKTOK_reference_1.mp4` (ref1, "luna") y `TikTok_Reference_2.mp4` (ref2, "ciudad").
Métodos: ffprobe, diferencias por fotograma, hojas de contacto con marca de tiempo (4 fps), ajuste de escala/posición por
correlación normalizada contra el encuadre final (`../ref_analisis/tools/camfit.py`), seguimiento de elementos brillantes
(`track.py`), muestreo de color y RMS de audio por ventanas de 100 ms.

## 1. Datos técnicos

| | ref1 | ref2 |
|---|---|---|
| Resolución | 576×712 (72:89) | 576×712 (72:89) |
| FPS | 60 (VFR, media 59.97) | 59.94 |
| Duración | 30.07 s | 28.47 s |
| Audio | AAC 44.1 kHz estéreo, −8.3 LUFS integrado | AAC 44.1 kHz estéreo, −7.4 LUFS |
| Cortes | 0 (plano único) | 0 (plano único) |

La línea gris vertical en el borde derecho de ambas referencias es un artefacto de captura; la plantilla no la reproduce.
Proporción original de publicación: no hay evidencia verificable (576×712 puede ser un recorte de 9:16).

## 2. Estructura visual (idéntica en ambas)

Capas, de abajo a arriba:
1. **Fondo**: foto/video nocturno real (playa con luna / callejón urbano). En ref1 el mar se mueve (video en bucle); el cielo es estático.
2. **Personaje**: ilustración manga en blanco y negro recortada, con borde de luz blanco. Integrada en el fondo, se mueve con él.
3. **Letra**: izquierda, 1–3 palabras por línea, encima del crédito.

Todo el conjunto (fondo + personaje + texto) se mueve como un único plano.

## 3. Cámara (medida)

**Apertura ref1**: zoom-out centrado (centro ≈ 300,368 en 576×712):

| t (s) | 0.4 | 1.0 | 1.6 | 2.0 | 2.4 | 2.8 | 3.1 |
|---|---|---|---|---|---|---|---|
| escala | 1.88 | 1.64 | 1.40 | 1.24 | 1.12 | 1.04 | 1.00 |

Velocidad constante (0.4×/s) hasta 1.6 s y frenado suave hasta 3.1 s.

**Apertura ref2**: 1.17× → 1.00× entre 0.9 y 3.0 s. El "deslizamiento" del primer texto (1.3–3.0 s) es el mismo zoom-out, no una animación propia del texto.

**Flotación continua** (todo el plano): traslación diagonal senoidal, X e Y en fase, periodo 4.8 s.
- ref1: ±7.5 px X, ±6.5 px Y (en 576×712) → ±14 / ±12 px en 1080 de ancho. Mínimos en t = 6.0, 10.8, 15.6…
- ref2: ±3.5 px → ±6.5 px en 1080.

**Fundidos**: entrada desde negro 0–0.6 s (ref1) / 0–0.75 s (ref2); salida a negro en los últimos ~0.5 s.

## 4. Tipografía y texto (medido en 576×712; ×1.875 para 1080 de ancho)

| | ref1 | ref2 |
|---|---|---|
| Fuente letra | Montserrat ExtraBold (identificada por forma de a/t/h/w) | igual |
| Tamaño (em) | 29.5 px → 55 px | 32 px → 60 px |
| Interlineado | 34.5 px (1.17 em) | 41 px (1.28 em) |
| Margen izquierdo | x = 34 px → 64 px | x = 20 px → 38 px |
| Comilla `"` | misma fuente, encima de la 1.ª línea (inicio y = 167) | y = 187 |
| Crédito | Open Sans Regular ~21.5 px, "Canción - Artista" en 1 línea | ~21 px, 2 líneas ("Canción" / "-Artista") |
| Posición del crédito | fija, 51 px bajo la 3.ª línea base (no sube si la frase tiene 1–2 líneas) | 47 px |
| Color | blanco con brillo blanco difuso | blanco; al final rojo neón |

Texto de ejemplo para orientar posición: inicio de la comilla al 23.5 % de la altura.

**Rojo neón (ref2, desde 24.0 s)**: núcleo ≈ RGB(242,86,88), halo ≈ RGB(151,58,51). La comilla y el crédito siguen blancos.

**Cambios de frase** (secuenciales, no superpuestos):
- ref1: aparece la 1.ª frase a 6.0 s (con comilla y crédito); cambios a 11.0, 14.0, 19.0, 25.5, 27.5 s.
- La frase saliente se desvanece en ~0.25 s y la siguiente aparece en ~0.25 s; comilla y crédito permanecen.
- ref2: primera frase a ~1.3 s; cambios a ~4.25, 6.4, 8.8, 10.6, 13.3, 14.75, 19.35 s (±0.15 s, resolución de 4 fps); rojo a 24.0 s.

## 5. Audio

- Fundido de entrada: ~1.0–1.3 s (ref1), ~0.7 s (ref2).
- Fundido de salida: ~2 s (ref1 de −10 a −22 dB entre 28.0 y 30.0 s); ref2 ~1.5 s.
- Sin locución, sin efectos de sonido: solo la canción.
- La escucha de sincronía letra/voz no se pudo verificar (Claude no oye el audio): los tiempos de la letra se fijan con la canción del usuario.

## 6. Plantilla (`render_lyric.py`)

Reproduce los puntos 3–5 con valores medidos (presets `luna` y `ciudad`). Verificación sobre un render de prueba con material sintético:
- Zoom de apertura reajustado con el mismo método: 1.88 / 1.64 / 1.40 / 1.24 / 1.12 / 1.04 / 1.00 (idéntico a ref1).
- Flotación: amplitud 12.8 px Y × 14.8 px X (ref1: 12.6 × 16), mínimos en 6.0 y 10.8 s (igual a ref1).
- Tiempo de render: ~0.08 s/fotograma a 1080×1336, 60 fps.

Límites:
- Si el fondo es una imagen fija, no habrá movimiento interno (olas, luces); ref1/ref2 usan fondo con movimiento. Admite solo imagen; para video de fondo hay que ampliar el script.
- El personaje debe venir como PNG con transparencia; si la imagen ya trae personaje y fondo juntos, se omite `character`.
- Para que el zoom inicial de 1.96× no pierda nitidez, el fondo necesita ≥ 2160 px de ancho.

### Uso
```bash
python3 render_lyric.py config.json --preview 1,6.5,15     # fotogramas de control en preview/
python3 render_lyric.py config.json --out final.mp4
```
Campos de `config.json`: ver `config_plantilla.json`. Cada frase: `start` (s), `text` (saltos con `\n`),
opcional `style: "neon_red"`, `hold_to_end: true` en la última.
