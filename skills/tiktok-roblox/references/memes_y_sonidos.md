# Memes, zooms y efectos de sonido (humor satírico / shitpost)

El objetivo es reforzar el chiste que ya está en la conversación. La voz manda: nada debe tapar una frase.

## Imágenes
- **Una imagen por frase concreta**, en el instante en que se dice. Ejemplos que funcionaron:
  - "vi una foquita ahí al fondo" → foca borrosa
  - "yo soy una foca y…" → foca con lentes ☝️
  - "mido 1.90" → monigote ">1.90m"
  - "inventé el matcha" → chico con matcha
  - "yo fui a Japón" → Bart "Me in Japan"
  - "le enseñé al Papa" → el Papa saludando
  - "mi miel" → tarro de miel
  - "amarilla" → Minions
  - "¿vives en un cerro?" → foto de cerro con casitas
  - "no te metas con mi Perú" → alpaca "pe"
  - "feminista" → burro creído
  - "mi v*rga" → pájaro con la mano en la oreja
- **Posición `top`:** encima de la cabeza del personaje, con un ancho máximo de 560 px, entrada con rebote y salida con fundido. No tapa caras ni subtítulos.
- **Posición `full`:** cierre a pantalla completa de 1 a 2 s tras el remate de cada momento. Alarga la escena para que el cierre quepa (los clips tienen 0.5 s de margen).
- Las imágenes del usuario mandan. Si te pasa una nueva para un diálogo, cópiala a `edicion/memes/` con un nombre descriptivo y colócala exactamente ahí. Si choca con otra imagen, acorta la otra (`set_image_end`) en vez de solaparlas.
- Si el usuario dice "en el segundo video, cuando dice X" y X no está en el corte, busca X en la transcripción (puede estar mal transcrito) y propón recuperar ese trozo al inicio o al final del corte.

## Sonidos
- **Dónde:** en los silencios. Mide los huecos entre bloques de subtítulos: los buenos duran ≥ 0.5 s.
- **Volumen:** mide cada archivo con `sfx_measure.py` y usa el `vol` que devuelve.
  - Efectos en silencios: ~-16 LUFS.
  - Canción de la intro: ~-15 LUFS, con fundido de 0.2 s al entrar el primer clip.
  - Risas o efectos que se pisan con la voz: bájalos a ~-27 LUFS con un `envelope`.
  - Música de fondo bajo el diálogo: ~-32 LUFS, unos 18 dB por debajo de la voz. Ejemplo: Careless Whisper bajo un momento de "seducción" cringe.
  - Archivos con picos > 0 dBFS (Voicemod los trae a menudo): el volumen calculado ya los baja. El limitador final hace el resto.
- **Ritmo:** 4-6 intervenciones cada 35 s, mezclando imagen y sonido. El cierre de cada momento suele llevar imagen a pantalla completa + sonido corto ("faaah", "get out").
- **Zooms:** punch-in de 1.0 a 1.2 en 0.2 s sobre la reacción o el remate, a menudo junto con un efecto ("huh", "holy moly", "augh"). Un zoom lento de 1.0 a 1.12 funciona en un silencio incómodo.

## Evita
- Sonidos sexuales explícitos (gemidos, intro de Pornhub, "me corro"…) y cualquier sonido que sexualice a menores ("ataque loli"). TikTok restringe el video y el humor no lo necesita. Si el usuario los pide explícitamente, avísale del riesgo.
- Saturar: si el usuario dice "falta más risa", añade 3-5 cosas y deja que escuche. Al usuario de esta sesión le sobraron las risas de rana, "muehehe" y "mwah"; quítalas sin discutir cuando lo diga.
- Tapar una palabra clave del chiste.

## Subtítulos
- Blancos, Segoe UI Black 82 px, contorno negro y sombra, a la altura y = 0.30.
- Censura groserías fuertes con asterisco ("v*rga") para no perder alcance, y avisa al usuario.
- Corrige lo que Whisper oyó mal ("miedo no noventa" → "mido 1.90") y lista al usuario lo que no puedes confirmar sin oírlo.
