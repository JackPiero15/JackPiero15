# Montaje, reencuadre y casos especiales

## Elegir el fragmento vertical (~1 min)
- Busca un bloque musical completo (estrofa + coro, precoro + coro…) de 55–65 s. Usa `beats.py` y los tiempos por palabra para que empiece en un pulso justo antes de la primera palabra y termine tras una frase resuelta.
- Comprueba con `nbest.py` las ventanas de borde: la de antes del inicio no debe contener voz (o te comes el final de la frase anterior) y la del final no debe contener el comienzo de la siguiente («'Cause I…»). Fundido de salida 0,4–0,9 s.
- Si el bloque coherente dura 50–55 s, es mejor que cortar una sección a la mitad: explica la diferencia en el informe. Un intro con letra puede sumar segundos si su segunda mitad es una frase con sentido.

## Modo `sync` (el video es el de la canción)
- La sincronía labial obliga a un video continuo: los planos solo cambian de encuadre (`cx`), no de tiempo.
- Cortes: `ffmpeg … select='gt(scene,0.25..0.3)'` sobre el archivo que usará Blender (el intermedio si lo hay) → lista de tiempos → `gen_sync_shots.py <song> <fmt> cuts.txt <runs_negros> <cx_defecto>`.
- **Negros del original**: `luma_runs.py video 18.5`. Huecos ≥3 fotogramas → plano ambiental del mismo video sin nadie cantando (`cutaways` en el JSON, cada uso con otro punto de entrada); 1–2 fotogramas → el plano siguiente empieza antes (vídeo adelantado ≤67 ms hasta el próximo corte). Con umbral 21,5 aparecen planos nocturnos muy oscuros: **míralos** antes de taparlos; si se ve al cantante, es contenido.
- El fundido a negro final del videoclip, mientras se apaga la música, es el cierre original: se conserva y se documenta.
- Evita como cutaway todo plano con texto sobreimpreso (títulos, frases del director).

## Modo `montage` (material de otra canción, p. ej. un visualizer)
- Silencia por completo su audio: no crees sound strips del metraje.
- Inventaría tomas limpias con `shot_sheet.py` (fotograma central de cada toma con rejilla) y `luma_runs.py` (negros y destellos blancos: umbral >200 para blancos). Excluye: texto con el título de la otra canción, labios que parezcan cantar durante la voz, destellos.
- Los visualizers suelen ser bucles repetidos: mide el desfase real de cada vuelta con la lista de cortes (en un caso la 2.ª vuelta era +48,757 s y la 3.ª +96,30 s, no el doble) y comprueba dónde se acaba (se iba a negro antes del final del archivo).
- Para la canción completa: `gen_montage.py` con secciones ancladas a su pulso (`section_k`), retornos visuales en los coros, personajes en las estrofas, primeros planos de boca solo en instrumentales, `fillers` largos para que ninguna sección se quede corta. Valida después que ningún plano cruza un corte/destello.

## Reencuadre 16:9 → 9:16
- Escala «llenar alto» (`H/src_h`) y `cx` = centro horizontal en píxeles de la fuente. `build_blend.py` lo limita para no enseñar nunca el borde del cuadro.
- Mide `cx` en `crop_sheet.py` (las etiquetas son píxeles reales). Si mides sobre una imagen reducida, reescala: un error del 20 % dejó caras cortadas en media pieza.
- Planos a dos: sigue a quien hace la sincronía labial. Personas en movimiento: elige el centro medio o un paneo lento `[desde, hasta]` (QUINT ease), nunca nervioso.
- `final_qa.py` marca como «negro» un recorte que cae sobre ropa oscura: revisa esos fotogramas y mueve `cx`.
- Caras bajas en el cuadro (pareja tumbada): pon ese subtítulo arriba (`"pos": "top"`, trae su propio degradado). Ordena los planos para que un subtítulo no cruce de un plano «arriba» a uno «abajo».
- Fuente 720p: ×2,67 en vertical. Sin enfoque artificial; dilo en el informe. Fuente 4K: hornea el recorte 9:16 desde 4K (más nítido que recortar el 1080p).

## Texto incrustado en el video (lyric videos)
- `locate_text_color.py` → caja de unión y caja típica del texto + tiempos sin texto. Si está siempre en la misma franja, una **placa opaca** localizada (`plate` en el JSON, alpha 1.0: con 0,94 el amarillo se transparentaba) que además sirve de caja para el español. No superpongas idiomas ni difumines el centro.
- Vertical: recorte centrado constante (el texto queda en una franja fija). 16:9: caja más estrecha centrada en el texto; con subtítulos en dos líneas dentro (`max_chars` ~30) en vez de una línea larga que encoge.
- Documenta la limitación (la placa tapa una franja del cuerpo/manos).

## 16:9 para YouTube
- Canción completa desde su inicio musical hasta el final (retira solo silencio técnico: `silencedetect=n=-55dB:d=0.3`). Sin bandas ni extensiones desenfocadas en material 16:9; parte del metraje original, nunca del vertical.
- Subtítulos centrados abajo: margen 120 px a los lados y 130 px abajo (cy ≈ 878 con 54 px).
- Ajusta `out` para no incluir los fotogramas negros finales del archivo si la música ya terminó.
