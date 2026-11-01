#!/bin/bash
# Crea la estructura de un proyecto nuevo y copia renderizadores, constructor y tipografías.
# Uso: nuevo_proyecto.sh <carpeta_proyecto>
set -euo pipefail
K="$(cd "$(dirname "$0")/.." && pwd)"
P=$1
mkdir -p "$P"/{tools,fonts,media,pieces,work,out}
cp "$K"/scripts/*.py "$K"/scripts/mux_audio.sh "$P/tools/"
cp "$K"/assets/fonts/*.ttf "$P/fonts/"
[ -f "$P/lineas.json" ] || cp "$K/assets/plantilla_lineas.json" "$P/lineas.json"
echo "Proyecto listo en $P (tools/ fonts/ media/ pieces/ work/ out/ lineas.json)"
