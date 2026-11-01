# Skills propias

Copia de las 9 skills creadas por el usuario, más `plantillas-edicion-letras` (origen `plugin` en el manifiesto de skills sincronizadas, fecha de copia 2026-11-01). Se excluyen las skills de Anthropic (`docx`, `xlsx`, `pptx`, `pdf`, `docs`, `skill-creator`, `import-memory`, `morning`, `google-workspace`).

| Skill | Ámbito | Última actualización |
|---|---|---|
| `blender-tiktok-es-latam` | Edits narrativos/musicales/producto en Blender para TikTok, español latino | 2026-10-30 |
| `blender-motion-graphics` | Motion graphics en Blender (3D + VSE + compositor) por MCP | 2026-10-29 |
| `videos-musicales-traducidos` | Canciones con subtítulos traducidos al español, 9:16 y 16:9 | 2026-10-29 |
| `blender-video-editor` | Edición VSE + FFmpeg para YouTube/TikTok | 2026-10-26 |
| `tiktok-roblox` | Grabaciones OBS de Roblox a TikToks de humor | 2026-10-26 |
| `mentor-entrevistas` | Preparación de entrevistas de trabajo | 2026-10-25 |
| `mentor-ecommerce-contraentrega` | E-commerce contraentrega Perú/LatAm | 2026-10-25 |
| `tap-certus` | TAP de CERTUS (Word, Excel, exposición) | 2026-10-25 |
| `excel-profesional` | Formato profesional de libros .xlsx | 2026-10-05 |
| `plantillas-edicion-letras` | Plantilla de los edits de letra tecleada (Confident v3, Too Much, Justin, Laroi, Down For Real, Dinero); `.zip` listo para subir: `plantillas-edicion-letras.zip` | 2026-11-01 |

## Plantillas de edición

Plantillas reutilizables incluidas en las skills:

| Archivo | Uso |
|---|---|
| `videos-musicales-traducidos/assets/piece_template.json` | Plantilla de pieza (fuente, fps, in/out, encuadres, cutaways) |
| `videos-musicales-traducidos/assets/montage_example.json` | Ejemplo de montaje por beat con pools de tomas |
| `videos-musicales-traducidos/assets/Inter.woff2` | Tipografía de subtítulos |
| `blender-motion-graphics/assets/theme.py` | Tema único: colores, fuentes, easings, tiempos |
| `blender-motion-graphics/assets/mograph.py` | Librería bpy: escena, textos, entradas/salidas, captions, compositor, render |
| `tiktok-roblox/scripts/blender_vse_helpers.py` | Helpers de VSE (Blender 5.x por MCP): escenas, canales de voz, video, memes, subtítulos, música y efectos |
| `mentor-entrevistas/references/plantillas.md` | Correo de agradecimiento y otras plantillas de entrevista |
| `mentor-ecommerce-contraentrega/references/plantillas.md` | Prompts de IA, speech de llamada, seguimiento, upsell, cobranza, brief UGC, reclutamiento |
| `excel-profesional/scripts/estilo_excel.py` | Estilos openpyxl reutilizables |

Plantilla de letra tecleada empaquetada como skill: `plantillas-edicion-letras/` (renderizador, constructor de línea de tiempo, tipografía, piezas de ejemplo).

Proyectos de edición ya realizados (configuraciones de pieza y renderizadores): `../export/proyecto*/`.

## Instalación

- Claude Code: copiar la carpeta de la skill a `~/.claude/skills/<nombre>/` (personal) o `.claude/skills/<nombre>/` (proyecto).
- claude.ai: comprimir la carpeta de la skill en `.zip` (con `SKILL.md` en la raíz de la carpeta) y subirla en Configuración → Capacidades → Skills.
