#!/bin/bash
# High-quality re-render of the 4 final TikTok edits (CRF 10, AAC 320k).
U=/root/.claude/uploads/480cac19-f757-5011-8fdd-e51c6b3a7776
E=/home/user/JackPiero15/export
job() { # renderer piece audio gain_db out_name
  local tmp=/home/user/hq_$5.mp4
  CRF=10 python3 "$1" "$2" "$tmp" > /home/user/hq_$5.log 2>&1 || { echo "FAIL render $5"; return; }
  ffmpeg -y -loglevel error -i "$tmp" -i "$3" -map 0:v -map 1:a -c:v copy \
    -af "volume=$4dB,alimiter=limit=0.89:level=false,afade=t=out:st=$(python3 -c "import subprocess;d=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','$tmp'],capture_output=True,text=True).stdout);print(round(d-0.45,2))"):d=0.45" \
    -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$E/$5.mp4" && echo "OK $5" || echo "FAIL mux $5"
}
job /home/user/confident/tools/render3.py /home/user/tiktok_audio/pieces/justin.json $U/2beb89f0-JUSTIN_TIKTOK.mp3 -5.1 Confident_ES_TikTok_HD &
job /home/user/toomuch/tools/render3.py /home/user/tiktok_audio/pieces/laroi.json $U/1c135941-KIDLAROI.mp3 -5.1 TooMuch_ES_TikTok_HD &
wait
job /home/user/downforreal/tools/render3.py /home/user/downforreal/pieces/dfr.json /home/user/downforreal/work/frag.wav -4.6 DownForReal_ES_TikTok_HD &
job /home/user/dinero/tools/render3.py /home/user/dinero/pieces/dinero.json /home/user/dinero/media/dinero.mp3 -6.4 Dinero_ES_TikTok_HD &
wait
echo ALLDONE
