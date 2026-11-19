#!/usr/bin/env python3
"""Aplica um corte entre keyframes e verifica a mídia e o original."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_EDITOR = ROOT / "workflows/edit/scripts/apply_edits.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--editor", type=Path, default=WORKSPACE_EDITOR)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="edicao-e2e-") as temp:
        workspace = Path(temp)
        original = workspace / "original.mp4"
        output = workspace / "editado.mp4"
        decisions = workspace / "edit_decisions.json"
        subprocess.run([
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "3",
            "-c:v", "libx264", "-g", "240", "-c:a", "aac", str(original),
        ], check=True)
        before = hashlib.sha256(original.read_bytes()).digest()
        decisions.write_text(json.dumps({"decisions": [{
            "type": "remove_segment", "from": "00:00:01", "to": "00:00:02",
        }]}), encoding="utf-8")
        subprocess.run([
            sys.executable, str(args.editor), "--input", str(original), "--decisions",
            str(decisions), "--output", str(output),
        ], check=True)
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,nb_frames:format=duration", "-of", "json", str(output),
        ], text=True))
        streams = {stream["codec_type"]: stream for stream in probe["streams"]}
        unchanged = before == hashlib.sha256(original.read_bytes()).digest()
        duration = float(probe["format"]["duration"])
        video_frames = int(streams.get("video", {}).get("nb_frames", "0"))
        passed = unchanged and "audio" in streams and video_frames == 48 and 2 <= duration < 2.1
        result = {
            "passed": passed,
            "original_preservado": unchanged,
            "quadros": video_frames,
            "duracao_s": duration,
            "faixas": sorted(streams),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Resultado: {args.output}")
        return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
