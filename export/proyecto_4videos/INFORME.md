# 4 videos lyric aesthetic (60 s)

Plantilla: `../plantilla_lyric/render_lyric.py` (análisis en `../plantilla_lyric/ANALISIS.md`).
Formato: 1080×1920, 60 fps, H.264 CRF 16, AAC 256 kbps 48 kHz. Duración 60.0 s.
Configuraciones: `configs/*.json`. Renders: `render/*.mp4` (no se suben a git).

## Elección de imágenes

| Video | Personaje (recorte) | Fondo | Preset | Motivo |
|---|---|---|---|---|
| 01 De Mí – Camila | 2 chica llorando (isnet-anime) | 7 campo con niebla (oscurecido 0.62, viñeta) | luna | balada de desamor; vacío gris |
| 02 Call Out My Name – The Weeknd | 1 chico chaqueta negra (BiRefNet, tubería borrada a mano) | 9 ciudad con niebla y semáforos rojos | ciudad | voz masculina nocturna; final en rojo neón como ref2 |
| 03 Forever & Again – The Kid LAROI | 3 pareja abrazada (isnet-anime) | 8 andén nevado (recorte 1.35× a la derecha para sacar el letrero) | luna | "siempre estaré ahí"; frío ("blood runs cold") |
| 04 Slow Dancing in the Dark – Joji | 4 chica en la puerta (BiRefNet) | 6 carretera borrosa (oscurecida 0.62) | luna | distancia, alguien que está con otro; imagen difusa |

Imagen 5 descartada: ningún modelo separa la camiseta blanca del papel blanco.
Imágenes enviadas solo en el chat (cuarto verde, loft morado, pareja en banca, pareja en reja, chica en cuarto,
chica fumando en azotea, chico en aula, encapuchado con perro, chico en baranda) no llegaron al contenedor: no se usaron.
Imagen 10: archivo vacío (300×150 transparente).

## Cambios respecto a la plantilla
- `text_follows_zoom: false` en los presets luna: las letras empiezan antes de 3 s y el zoom de 1.96× las sacaba del cuadro.
  El texto conserva la flotación, no el zoom.
- Halo de luz en el personaje (`rim`), como el borde iluminado de la ref1.
- Corrección solo del fondo (exposición/saturación/viñeta) para que el texto blanco sea legible.

## Tiempos de letra
Fuente: transcripción faster-whisper large-v3 con tiempos por palabra (`work/*.large-v3.json`) + letra oficial entregada por el usuario.
Cada frase entra ~0.15 s antes de la primera palabra detectada.
Correcciones de la transcripción por letra oficial: Dancing ("him", "Oh well / Can't you see? / I don't wanna slow dance"),
Forever ("Lost in your pain", "Glass in your veins", "Anger will fade"), Call Out ("I put you on top", "I claimed you so proud").

## Pendiente de verificar de oído (Claude no escucha audio)
- **De Mí**: la voz solo se detecta en 0–16 s ("De mí, de mí, de mí"); 16–56 s no tiene voz detectable y el audio
  se apaga a silencio en 56.5 s (final de la canción). En 16–56 s se muestran versos de la propia canción como citas,
  **no cantados en ese tramo**. Si el tramo sí tiene voz, hay que cambiar esas tarjetas.
- Sincronía fina de todas las frases (±0.3 s esperable en canto con whisper).
- Call Out My Name 0–2.4 s: hay voz ("…all mine", fin de una frase previa) sin subtítulo.

## Traducción (español latino; solo los versos dentro del fragmento de 60 s)
Criterios: sentido y emoción antes que literalidad, 1–3 líneas de ≤ 15 caracteres por tarjeta, sin añadir ideas.
Decisiones:
- "pit stop" → "una parada más".
- "six feet underground" → "aunque esté bajo tierra".
- "too drunk to feel a thing" → "tanto alcohol que ya no sientes nada" (evita fijar género de la persona).
- "Lost in your pain" → "Ahogándote en tu dolor" (neutro en género).
- "forever and again" → "por siempre y otra vez".
- "Oh well" → "Qué más da…".
- "Can you?" → "¿Puedes?".
- "I want you to stay" → "Quiero que te quedes" (última tarjeta en rojo neón, como el final de la ref2).

## Entregables (`final/`, fuera de git)
| Archivo | Duración | Formato | Volumen integrado | Pico real |
|---|---|---|---|---|
| 01_de_mi.mp4 | 60.01 s | 1080×1920, 60 fps | −10.3 LUFS | −1.1 dBTP |
| 02_call_out_my_name.mp4 | 60.01 s | 1080×1920, 60 fps | −8.2 LUFS | −1.2 dBTP |
| 03_forever_and_again.mp4 | 60.01 s | 1080×1920, 60 fps | −8.5 LUFS | −1.6 dBTP |
| 04_slow_dancing_in_the_dark.mp4 | 60.01 s | 1080×1920, 60 fps | −8.7 LUFS | −1.4 dBTP |

Volumen: se conserva el nivel del máster (las referencias miden −7.4/−8.3 LUFS); solo se limitaron picos que superaban 0 dBFS
(hasta +0.9 dBTP). Control: `blackdetect` sin negros; hoja de fotogramas en cada cambio de letra (`work/qa_*.png`) revisada.
