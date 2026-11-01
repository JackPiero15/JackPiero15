# Transcripción, verificación y traducción

## Por qué tanto cuidado
Whisper sobre voz cantada acierta mucho pero inventa con seguridad: oye «foreign animation» donde se canta «a foreign and a mansion», «You inspire» donde hay «You been …», emojis y «Thanks for watching» en los instrumentales. Una traducción bonita de una línea mal oída es peor que una línea omitida. Claude además no puede escuchar: lo que dice «verificado» debe significar «varias pasadas independientes coinciden» o «coincide con la letra oficial incrustada», nunca «lo escuché».

## Escalera de verificación (de barato a caro)
1. `transcribe.py song.wav out.json medium` — primera pasada con tiempos por palabra (audio decodificado con PyAV a numpy: el `av.open` interno de faster-whisper falla con PyAV 19).
2. `recheck_lines.py song.wav t0 t1 out.json` — canal central filtrado 150–6000 Hz + dynaudnorm, modelos medium y small; lista palabras de baja confianza. Úsalo sobre la canción completa y sobre el tramo vertical.
3. `nbest.py song.wav medium a-b c-d …` — 6 hipótesis por ventana corta (una línea). Las líneas dudosas se resuelven comparando hipótesis, no eligiendo la primera.
4. **Repeticiones**: un coro que se repite 3–4 veces es la mejor prueba. Compara la misma línea en cada vuelta; si cambia, probablemente ninguna vuelta está bien oída → marca BAJA y traduce solo lo común.
5. **Letra incrustada en el propio video** (lyric videos): `locate_text_color.py` + `read_burned_lyrics.py` → hojas con cada rótulo y su segundo de aparición. Es letra oficial sincronizada: resuelve casi todo.
6. **Fonética + contexto**: «foreign animation/intervention» ≈ /fɒrɪn ən ə mænʃən/ → «a foreign and a mansion»; «Harlequin … like Pablo» encaja con una canción llamada «Picasso». Documenta el razonamiento y deja confianza «media».
7. Las adaptaciones de referencia que traiga el usuario son de tono, no evidencia. Si el resto de la referencia coincide muy bien con el audio, puede inclinar una duda (p. ej. «Ya casi no me hablas» → *quiet*), pero dilo.

Si tras todo esto una media línea sigue sin entenderse: traduce solo la parte segura (o deja la línea sin subtítulo) y lístala como pendiente en `letras/cambios_traduccion.md` y en el informe. Nunca `[…]` ni notas en el MP4.

## Tiempos
- Inicio de subtítulo = inicio de la primera palabra (whisper word start, o aparición del rótulo oficial −0,06 s). Final = fin de la frase + `hold` (0,25 s por defecto), recortado 2 fotogramas antes del siguiente.
- Nunca repartir la duración entre frases. Nunca adelantar una frase que aún no se canta.
- Coros repetidos: copia la traducción del primer coro con el desfase **medido** palabra a palabra en cada vuelta (no asumas compases exactos: en un tema salieron +51,45 / +85,66 / +102,81 s, no múltiplos limpios).
- `beats.py song.wav t0 t1 ventana…` da tempo y rejilla; úsala para cortes de montaje y para elegir bordes del fragmento, no para mover subtítulos.

## Reglas de adaptación (español latino)
- Conserva quién habla, a quién, negaciones y metáforas. «get even» → «pagar con la misma moneda / desquitarse»; «settle» → «sentar cabeza»; «I'm on something» → «ando volando».
- Groserías: las del original, al mismo nivel («give a damn» → «me importa un carajo»; «piss me off» → «encabronarme»). No añadas otras (una referencia convirtió «I don't care about the fame» en «me importa una mierda»: se corrigió).
- Insultos raciales: no se traducen; anótalo en las notas.
- Slang de rap: «smoke» = pelea, «blicky» = pistola, «throwing fits» = vestirse con estilo, «GOAT» = el mejor, «foreign» = carro importado, «Great White North» = Canadá.
- «baby/babe» → «amor» / «bebé»; «girl» → «nena». Mantén la misma elección en toda la canción.

## Legibilidad
- Máximo 2 líneas; vertical ≤ 34 caracteres por línea (en la práctica ≤ 27–31 a 56–64 px para caber en x 100–900), horizontal ≤ 42.
- Objetivo 12–17 caracteres/s; revisa todo lo que pase de 20. En rap rápido: condensa sin perder sentido («Solo me quieres para presumirme con tus amigos» → «Me quieres para presumirme / con tus amigos»), parte en bloques por palabras, o alarga `hold` si después hay hueco.
- Divide por sentido: no separes artículo/sustantivo, «no» de su verbo, ni «desde / que».
- Un solo color de acento por pieza, en una palabra clave (título o idea central), marcado `*palabra*`.

## Tabla y entregables de texto
- `pieces/<song>.json` → `subs` es la **tabla maestra de la canción completa** (tiempos de la fuente). Los formatos derivan sus tiempos restando su `in`. Misma traducción en lo compartido.
- `make_subs.py` escribe además `subs/<id>/<id>_alineacion_maestra.csv/.json` (fuente, inglés, español, tiempos vertical y horizontal, confianza) y un SRT por formato con tiempos relativos al MP4.
- `gen_letras.py` → letras completas en Markdown con secciones, selección vertical y notas.
- `letras/cambios_traduccion.md` (a mano): tabla «Referencia | Ahora | Motivo» por canción, con las dudas pendientes en negrita.
