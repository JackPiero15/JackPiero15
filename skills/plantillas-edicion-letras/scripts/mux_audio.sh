#!/bin/bash
# Une el video renderizado (sin audio) con el audio: ganancia, limitador -1 dBTP aprox., fade-out final de 0.45 s, AAC 320k.
# Mismo comando que hq_batch.sh de los edits originales.
# Uso: mux_audio.sh video.mp4 audio.(mp3|wav|mp4) ganancia_db salida.mp4 [inicio_audio_s]
set -euo pipefail
V=$1; A=$2; G=$3; O=$4; SS=${5:-0}
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
ST=$(python3 -c "print(round($D-0.45,2))")
ffmpeg -y -loglevel error -i "$V" -ss "$SS" -i "$A" -map 0:v -map 1:a -c:v copy \
  -af "volume=${G}dB,alimiter=limit=0.89:level=false,afade=t=out:st=$ST:d=0.45" \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$O"
echo "OK $O"
