"""Render a 40-slide comic with each still held for its matching Persian narration."""
from __future__ import annotations
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
from renderer.validate_manifest import validate_manifest

def run(cmd:list[str])->None: subprocess.run(cmd,check=True)

def render(manifest_path:Path,output_path:Path)->None:
    m=json.loads(manifest_path.read_text(encoding="utf-8")); base=manifest_path.resolve().parent
    if not isinstance(m,dict): raise ValueError("Manifest root must be an object.")
    errors=validate_manifest(m,base)
    if errors: raise ValueError("Manifest validation failed:\\n- "+"\\n- ".join(errors))
    ff=shutil.which("ffmpeg"); probe=shutil.which("ffprobe")
    if not ff or not probe: raise RuntimeError("FFmpeg and ffprobe required.")
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="audio-comic-") as td:
        tmp=Path(td); clips=[]
        for i,p in enumerate(m["panels"],1):
            image=(base/p["image"]).resolve(); audio=(base/p["narrationAudio"]).resolve()
            q=subprocess.run([probe,"-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)],check=True,capture_output=True,text=True)
            duration=float(q.stdout.strip())
            if not 0<duration<=90: raise ValueError(f"Panel {i:02d} audio duration invalid.")
            clip=tmp/f"slide_{i:02d}.mp4"; clips.append(clip)
            run([ff,"-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",str(image),"-i",str(audio),"-vf","scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p","-t",f"{duration:.3f}","-r","24","-c:v","libx264","-preset","veryfast","-crf","22","-c:a","aac","-b:a","128k","-ar","48000","-ac","2","-shortest","-movflags","+faststart",str(clip)])
        concat=tmp/"slides.ffconcat"; lines=["ffconcat version 1.0"]
        for c in clips: lines.append("file '"+str(c.resolve()).replace("'","'\\''")+"'")
        concat.write_text("\n".join(lines)+"\n",encoding="utf-8")
        run([ff,"-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(output_path.resolve())])
    if not output_path.is_file() or output_path.stat().st_size==0: raise RuntimeError("No output MP4.")

def main()->int:
    a=argparse.ArgumentParser(); a.add_argument("manifest",type=Path); a.add_argument("--output",type=Path,required=True); x=a.parse_args()
    try: render(x.manifest,x.output)
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError,json.JSONDecodeError) as ex: print(f"RENDER FAILED: {ex}"); return 1
    print(f"Audio comic complete: {x.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
