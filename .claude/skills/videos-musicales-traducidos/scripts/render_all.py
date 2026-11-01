"""Render (background Blender, video only) + mux (ffmpeg, audio once) for the requested piece/formats.

Usage: python render_all.py <blend> piece:fmt [piece:fmt ...]
Each render runs in its own background Blender process, so the interactive Blender is not touched;
a crashed render is retried once.
"""
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()   # project folder: pieces/, media/, subs/, ...
BLENDER = os.environ.get("BLENDER") or shutil.which("blender") or r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
SCENE_SUFFIX = {"vertical": "VERTICAL", "horizontal": "YOUTUBE_16x9"}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    blend = sys.argv[1]
    for job in sys.argv[2:]:
        name, fmt = job.split(":")
        piece = json.load(open(os.path.join(ROOT, "pieces", name + ".json"), encoding="utf-8"))
        scene = f"{piece['scene']}_{SCENE_SUFFIX[fmt]}"
        t = time.time()
        for attempt in (1, 2):
            p = subprocess.run([BLENDER, "-b", blend, "-S", scene, "-a"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if p.returncode == 0:
                break
            print(f"{scene}: render failed (attempt {attempt}): {p.stderr[-400:]}", flush=True)
        else:
            continue
        print(f"{scene}: rendered in {time.time() - t:.0f} s", flush=True)
        m = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mux.py"), name, fmt],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(m.stdout.strip() or m.stderr[-600:], flush=True)


if __name__ == "__main__":
    main()
