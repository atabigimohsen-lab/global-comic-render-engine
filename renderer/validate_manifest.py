"""Validate a 40-panel comic manifest before rendering."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


def _validate_local_file(raw_path: Any, base_dir: Path, label: str, errors: list[str]) -> None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"{label} must be a non-empty relative file path.")
        return

    candidate = Path(raw_path)
    if candidate.is_absolute() or "\\" in raw_path or "\x00" in raw_path:
        errors.append(f"{label} must be a safe relative path inside the manifest directory.")
        return

    root = base_dir.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        errors.append(f"{label} must stay inside the manifest directory.")
        return

    if not resolved.is_file():
        errors.append(f"{label} file does not exist: {raw_path}")


def validate_manifest(manifest: dict[str, Any], base_dir: Path) -> list[str]:
    errors: list[str] = []
    panels = manifest.get("panels")

    if manifest.get("aspectRatio") != "16:9":
        errors.append("aspectRatio must be '16:9'.")

    if not isinstance(panels, list) or len(panels) != 40:
        errors.append("panels must contain exactly 40 entries.")
        return errors

    for index, panel in enumerate(panels, start=1):
        expected = f"{index:02d}"
        if not isinstance(panel, dict):
            errors.append(f"Panel {expected} must be an object.")
            continue

        if str(panel.get("seq", "")) != expected:
            errors.append(f"Panel {expected} must have seq '{expected}'.")

        if not isinstance(panel.get("artPrompt"), str) or not panel["artPrompt"].strip():
            errors.append(f"Panel {expected} is missing artPrompt.")

        _validate_local_file(panel.get("image"), base_dir, f"Panel {expected} image", errors)

        duration = panel.get("durationSeconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not 0.25 <= duration <= 30:
            errors.append(f"Panel {expected} durationSeconds must be between 0.25 and 30.")

        has_text = any(panel.get(key) for key in ("dialogue", "narration", "sfx"))
        if not has_text and panel.get("silentPanel") is not True:
            errors.append(f"Panel {expected} needs dialogue, narration, SFX, or silentPanel=true.")

    audio = manifest.get("audio")
    if audio is not None:
        if not isinstance(audio, dict):
            errors.append("audio must be an object when provided.")
        elif audio.get("narrationPath") is not None:
            _validate_local_file(audio.get("narrationPath"), base_dir, "Narration audio", errors)

    if manifest.get("isFactual") is True:
        refs = manifest.get("sourceFactRefs", [])
        domains = set()
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, dict) and isinstance(ref.get("url"), str):
                    domain = urlparse(ref["url"]).hostname
                    if domain:
                        domains.add(domain.lower().removeprefix("www."))
        if len(domains) < 2:
            errors.append("Factual stories require sourceFactRefs from at least two distinct domains.")

    if manifest.get("category") == "fiction" and not manifest.get("worldBible"):
        errors.append("Fiction manifests must include worldBible.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a 40-panel comic manifest.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Could not read manifest: {exc}")
        return 2

    if not isinstance(manifest, dict):
        print("ERROR: Manifest root must be a JSON object.")
        return 2

    errors = validate_manifest(manifest, args.manifest.resolve().parent)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Manifest valid: exactly 40 ordered panels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
