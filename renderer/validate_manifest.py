"""Validate 40 ordered comic images and compact Persian narration."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from urllib.parse import urlparse
from typing import Any
MAX_WORDS_PER_PANEL=14
MAX_TOTAL_WORDS=480

def local_file(raw:Any,root:Path,label:str,errors:list[str])->None:
    if not isinstance(raw,str) or not raw.strip(): errors.append(f"{label} path is required."); return
    p=Path(raw)
    if p.is_absolute() or "\\" in raw or "\x00" in raw: errors.append(f"{label} path must be relative and safe."); return
    base=root.resolve(); resolved=(base/p).resolve()
    try: resolved.relative_to(base)
    except ValueError: errors.append(f"{label} escapes manifest directory."); return
    if not resolved.is_file(): errors.append(f"{label} file missing: {raw}")

def validate_manifest(m:dict[str,Any],base_dir:Path)->list[str]:
    e=[]; panels=m.get("panels")
    if m.get("aspectRatio")!="16:9": e.append("aspectRatio must be 16:9.")
    if not isinstance(m.get("title"),str) or not m["title"].strip(): e.append("title is required.")
    if not isinstance(panels,list) or len(panels)!=40: e.append("Exactly 40 panels required."); return e
    audio=m.get("audio")
    if not isinstance(audio,dict) or audio.get("narrationMode")!="per_panel_tts" or audio.get("language")!="fa-IR" or not audio.get("voice"): e.append("Audio must declare Persian per-panel TTS.")
    total_words=0
    for i,p in enumerate(panels,1):
        s=f"{i:02d}"
        if not isinstance(p,dict): e.append(f"Panel {s} must be an object."); continue
        if str(p.get("seq"))!=s: e.append(f"Panel {s} sequence mismatch.")
        if not isinstance(p.get("artPrompt"),str) or not p["artPrompt"].strip(): e.append(f"Panel {s} artPrompt missing.")
        local_file(p.get("image"),base_dir,f"Panel {s} image",e)
        narration=p.get("narration")
        if not isinstance(narration,str) or not narration.strip(): e.append(f"Panel {s} Persian narration missing.")
        else:
            words=len(narration.split()); total_words+=words
            if words>MAX_WORDS_PER_PANEL: e.append(f"Panel {s} narration is {words} words; maximum is {MAX_WORDS_PER_PANEL}.")
        local_file(p.get("narrationAudio"),base_dir,f"Panel {s} audio",e)
        if p.get("dialogue") not in ({},None) or p.get("sfx") not in ("",None): e.append(f"Panel {s} must not contain text dialogue or SFX.")
        d=p.get("durationSeconds")
        if not isinstance(d,(int,float)) or isinstance(d,bool) or not .25<=d<=30: e.append(f"Panel {s} durationSeconds invalid.")
    if total_words>MAX_TOTAL_WORDS: e.append(f"Total narration is {total_words} words; maximum is {MAX_TOTAL_WORDS}.")
    if m.get("isFactual") is True:
        refs=m.get("sourceFactRefs",[]); domains=set()
        if isinstance(refs,list):
            for r in refs:
                if not isinstance(r,dict): continue
                pub=r.get("publisher")
                if isinstance(pub,str) and pub.strip(): domains.add(pub.strip().lower().removeprefix("www.")); continue
                if isinstance(r.get("url"),str):
                    host=urlparse(r["url"]).hostname
                    if host: domains.add(host.lower().removeprefix("www."))
        if len(domains)<2: e.append("Factual stories need two distinct source domains.")
    if m.get("category")=="fiction" and not m.get("worldBible"): e.append("Fiction requires worldBible.")
    return e

def main()->int:
    a=argparse.ArgumentParser(); a.add_argument("manifest",type=Path); x=a.parse_args()
    try: m=json.loads(x.manifest.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as ex: print(f"ERROR: {ex}"); return 2
    if not isinstance(m,dict): print("ERROR: manifest root must be object"); return 2
    e=validate_manifest(m,x.manifest.resolve().parent)
    if e:
        for item in e: print("ERROR: "+item)
        return 1
    print("Valid: 40 ordered panels; narration within 480-word/4-minute target.")
    return 0
if __name__=="__main__": raise SystemExit(main())
