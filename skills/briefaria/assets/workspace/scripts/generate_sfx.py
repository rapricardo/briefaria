#!/usr/bin/env python3
"""
Gera efeitos sonoros via ElevenLabs Sound Generation API.
Lê sfx-spec.json e gera MP3 para cada efeito.

Uso:
  python scripts/generate_sfx.py \
    --spec clientes/.../sfx-spec.json \
    --output-dir clientes/.../sfx/
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"


def load_dotenv():
    search_dir = os.getcwd()
    for _ in range(5):
        env_path = os.path.join(search_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ[key] = value
            return
        parent = os.path.dirname(search_dir)
        if parent == search_dir:
            break
        search_dir = parent


def generate_sfx(text: str, duration: float, prompt_influence: float,
                 api_key: str, output_format: str = "mp3_44100_128") -> bytes:
    url = f"{ELEVENLABS_API_BASE}/sound-generation"
    payload = {
        "text": text,
        "duration_seconds": min(duration, 30.0),
        "prompt_influence": prompt_influence,
        "output_format": output_format,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"ElevenLabs API error {e.code}: {body}")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Gera SFX via ElevenLabs")
    parser.add_argument("--spec", required=True, help="Caminho para sfx-spec.json")
    parser.add_argument("--output-dir", required=True, help="Pasta de saída para MP3")
    parser.add_argument("--dry-run", action="store_true", help="Mostra spec sem gerar")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key and not args.dry_run:
        print("Erro: ELEVENLABS_API_KEY não encontrada", file=sys.stderr)
        sys.exit(1)

    with open(args.spec, "r", encoding="utf-8") as f:
        sfx_list = json.load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"SFX spec: {len(sfx_list)} efeitos")

    results = []
    for i, sfx in enumerate(sfx_list):
        sfx_id = sfx["id"]
        duration = sfx.get("duration", 5.0)
        prompt = sfx["prompt"]
        influence = sfx.get("prompt_influence", 0.3)
        shot = sfx.get("shot", "?")
        start = sfx.get("start", 0)

        print(f"\n[{i+1}/{len(sfx_list)}] {sfx_id} (shot {shot}, {start:.1f}s, {duration:.1f}s)")
        print(f"  Prompt: {prompt[:80]}...")

        if args.dry_run:
            results.append({"id": sfx_id, "status": "dry-run"})
            continue

        try:
            audio_data = generate_sfx(prompt, duration, influence, api_key)
            out_path = output_dir / f"{sfx_id}.mp3"
            out_path.write_bytes(audio_data)
            size_kb = len(audio_data) / 1024
            print(f"  OK: {out_path} ({size_kb:.0f}KB)")
            results.append({"id": sfx_id, "status": "ok", "path": str(out_path),
                           "size_bytes": len(audio_data)})
        except Exception as e:
            print(f"  ERRO: {e}", file=sys.stderr)
            results.append({"id": sfx_id, "status": "error", "error": str(e)})

    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"\n{'='*40}")
    print(f"Resultado: {ok}/{len(sfx_list)} gerados com sucesso")

    output = {
        "success": ok == len(sfx_list),
        "total": len(sfx_list),
        "generated": ok,
        "results": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
