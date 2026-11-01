# Subir a TikTok Studio (navegador integrado)

Publicar es una acción pública: el usuario tiene que haber aprobado en el chat la descripción, los hashtags y la portada de **esta** subida. Una aprobación para otra cuenta u otro video no vale.

1. `navigate` a `https://www.tiktok.com/tiktokstudio/upload`. Si pide iniciar sesión, la sesión es del usuario: no escribas contraseñas.
2. Identifica la cuenta. En `…/tiktokstudio/content` se ven sus publicaciones; úsalo para distinguir cuentas y para no publicar dos veces.
3. Pulsa **"Seleccionar vídeo"**. Se abre la ventana de archivos de Windows, que **no puedes manejar**: pide al usuario que elija `edicion\export\<nombre>_FINAL.mp4` o que lo arrastre al recuadro. Espera a que diga que ya lo cargó y comprueba que aparezca "Cargado (xx MB)" y 1080P.
4. **Descripción.** Haz clic en el editor por su `ref` (`find` con el nombre del archivo, que es el texto inicial). Comprueba con JS que `document.activeElement.isContentEditable` sea verdadero **antes** de `ctrl+a`; si no, `ctrl+a` selecciona toda la página. Luego `Delete` y escribe.
   - El autocompletado de hashtags puede borrar lo escrito antes. Escribe los hashtags, pulsa `ctrl+Home` y escribe la frase. Verifica con `[...document.querySelectorAll('[contenteditable="true"]')].map(e => e.innerText)`.
   - Plantilla que se usó: `Momentos incómodos en el podcast de Roblox 😭🦭 ¿Cuál fue el peor? 👇 #roblox #robloxpodcast #podcastroblox #robloxespañol #robloxmemes #robloxhumor #momentosincomodos #humor #parati #fyp`. Usa hashtags de nicho más algunos generales. La pregunta final invita a comentar.
5. **Portada:** abre "Editar portada" y arrastra el selector de la barra de fotogramas a la intro (~0:02), donde ya se ve el título completo.
   - El arrastre solo funciona con el tamaño normal del panel. Usa movimientos pequeños: la barra entera es el video completo, unos 2.4 px por segundo.
   - El botón **"Guardar"** queda fuera de vista. Amplía con `resize_window` a 1440×900, haz `find("Guardar")` y pulsa por `ref`; con coordenadas de la captura no funciona.
   - Comprueba que la miniatura de "Portada" muestre el título. Al terminar, vuelve con `resize_window` preset `desktop`.
6. Revisa los ajustes: "Ahora", "Todo el mundo", "Cargas en alta calidad" activado, y las comprobaciones (copyright y contenido). Si la revisión de contenido sigue en curso, se puede publicar igual. Si muestra un aviso de restricción **visible**, cuéntaselo al usuario antes de publicar.
7. Pulsa **"Publicar"** (`find("Publicar")`, la ref del botón, no "Cuándo publicar"). Comprueba en Publicaciones que hay una sola publicación nueva, con la descripción correcta, y su estado.
8. Informa al usuario del estado. Es normal que salga "Contenido en revisión" y que la privacidad se vea en "Solo yo" un rato. Si algo cambia sin que lo hayas tocado (por ejemplo, el usuario publicó desde el panel), dilo tal cual.

Archivos de más de 30 MB no llegan al móvil por SendUserFile. Dile al usuario que lo pase como documento (cable, Drive o WhatsApp como archivo) para que no se comprima.
