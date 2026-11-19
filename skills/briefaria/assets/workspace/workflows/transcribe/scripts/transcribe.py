#!/usr/bin/env python3
"""
Transcricao de video/audio via whisper.cpp.

Extrai audio do video via FFmpeg, transcreve com whisper-cli (whisper.cpp),
e gera 3 outputs padronizados:
  - transcript.json: segmentos com timestamps (e palavras se disponivel)
  - transcript.srt: legendas SRT
  - transcript.txt: texto corrido

Dependencias:
  - whisper-cpp: brew install whisper-cpp
  - ffmpeg: brew install ffmpeg
  - Modelo GGML: curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin -o models/ggml-medium.bin

Uso:
    python transcribe.py --input recordings/screen.mkv --output-dir transcript/
    python transcribe.py --input recordings/screen.mkv --output-dir transcript/ --model small
    python transcribe.py --input audio.mp3 --output-dir transcript/ --language en
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time


# Caminho padrao do modelo — relativo a raiz do repo
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_MODEL_DIR = os.path.join(REPO_ROOT, "models")

# Formatos que whisper-cli aceita diretamente
NATIVE_FORMATS = {".flac", ".mp3", ".ogg", ".wav"}

# Paths conhecidos que podem nao estar no PATH (ex: sandbox do Cowork, cron, etc.)
EXTRA_PATHS = [
    os.path.join(REPO_ROOT, ".cache", "bin"),  # sandbox Cowork (compilado local)
    "/opt/homebrew/bin",                         # macOS Apple Silicon
    "/usr/local/bin",                            # macOS Intel / Linux
]

# Libs compartilhadas do whisper compilado (sandbox)
CACHE_LIB = os.path.join(REPO_ROOT, ".cache", "lib")


def find_binary(name: str, install_hint: str = "") -> str:
    """Encontra um binario no PATH, no cache do projeto, ou em paths conhecidos."""
    path = shutil.which(name)
    if path:
        return path
    for prefix in EXTRA_PATHS:
        candidate = os.path.join(prefix, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    hint = f" Instale com: {install_hint}" if install_hint else ""
    print(
        f"ERRO: {name} nao encontrado.{hint}\n"
        f"No sandbox Cowork, rode: python scripts/setup-sandbox.py",
        file=sys.stderr,
    )
    sys.exit(1)


def find_model(model_name: str, model_dir: str) -> str:
    """Encontra o arquivo .bin do modelo GGML."""
    # Tentar nome direto
    candidates = [
        os.path.join(model_dir, f"ggml-{model_name}.bin"),
        os.path.join(model_dir, f"{model_name}.bin"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    print(
        f"ERRO: modelo '{model_name}' nao encontrado em {model_dir}/\n"
        f"Baixe com:\n"
        f"  curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{model_name}.bin "
        f"-o {model_dir}/ggml-{model_name}.bin",
        file=sys.stderr,
    )
    sys.exit(1)


def extract_audio(input_path: str, output_wav: str, ffmpeg: str = "ffmpeg"):
    """Extrai audio de video para WAV 16kHz mono (formato ideal para whisper.cpp)."""
    print(f"Extraindo audio: {input_path} -> WAV 16kHz...")
    subprocess.run(
        [
            ffmpeg, "-v", "warning", "-y",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            output_wav,
        ],
        check=True,
    )


def run_whisper(whisper_cli: str, model_path: str, audio_path: str,
                language: str, output_base: str, no_gpu: bool = False) -> dict:
    """Executa whisper-cli e retorna o JSON parseado."""
    cmd = [
        whisper_cli,
        "-m", model_path,
        "-f", audio_path,
        "-l", language,
        "--output-json-full",
        "--output-srt",
        "--output-txt",
        "-of", output_base,
    ]

    if no_gpu:
        cmd.append("--no-gpu")

    # Se whisper-cli vem do cache local, precisa do LD_LIBRARY_PATH para as .so
    env = os.environ.copy()
    if os.path.isdir(CACHE_LIB):
        env["LD_LIBRARY_PATH"] = f"{CACHE_LIB}:{env.get('LD_LIBRARY_PATH', '')}"

    print(f"Transcrevendo com whisper.cpp (modelo: {os.path.basename(model_path)})...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        print(f"ERRO whisper-cli:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # whisper-cli gera: {output_base}.json, {output_base}.srt, {output_base}.txt
    json_path = output_base + ".json"
    if not os.path.isfile(json_path):
        print(f"ERRO: whisper-cli nao gerou {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_json(whisper_json: dict) -> dict:
    """
    Converte o JSON do whisper.cpp para o formato padrao do projeto.

    whisper.cpp --output-json-full gera:
    {
      "transcription": [
        {
          "timestamps": {"from": "00:00:00,000", "to": "00:00:05,000"},
          "offsets": {"from": 0, "to": 5000},
          "text": " texto aqui",
          "tokens": [{"text": "texto", "timestamps": {"from": "00:00:00,500", "to": "00:00:01,200"}, ...}]
        }
      ]
    }

    Formato padrao do projeto:
    {
      "segments": [
        {
          "id": 0,
          "start": 0.0,
          "end": 5.0,
          "text": "texto aqui",
          "words": [{"word": "texto", "start": 0.5, "end": 1.2}]
        }
      ]
    }
    """
    segments = []
    transcription = whisper_json.get("transcription", [])

    for i, seg in enumerate(transcription):
        offsets = seg.get("offsets", {})
        start_ms = offsets.get("from", 0)
        end_ms = offsets.get("to", 0)

        segment_data = {
            "id": i,
            "start": round(start_ms / 1000.0, 3),
            "end": round(end_ms / 1000.0, 3),
            "text": seg.get("text", "").strip(),
        }

        # Extrair palavras dos tokens (se disponiveis)
        tokens = seg.get("tokens", [])
        words = []
        for tok in tokens:
            tok_text = tok.get("text", "").strip()
            if not tok_text or tok_text.startswith("["):
                continue
            tok_ts = tok.get("timestamps", {})
            tok_offsets = tok.get("offsets", tok_ts)
            # tokens podem ter offsets em ms ou timestamps em string
            if "from" in tok_offsets:
                if isinstance(tok_offsets["from"], (int, float)):
                    w_start = tok_offsets["from"] / 1000.0
                    w_end = tok_offsets["to"] / 1000.0
                else:
                    w_start = parse_srt_timestamp(tok_offsets["from"])
                    w_end = parse_srt_timestamp(tok_offsets["to"])
                words.append({
                    "word": tok_text,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                })

        if words:
            segment_data["words"] = words

        segments.append(segment_data)

    return {"segments": segments}


def parse_srt_timestamp(ts: str) -> float:
    """Converte timestamp SRT '00:00:05,000' para segundos."""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(ts)


def main():
    parser = argparse.ArgumentParser(
        description="Transcricao de video/audio via whisper.cpp"
    )
    parser.add_argument(
        "--input", required=True,
        help="Arquivo de audio ou video (mkv, mov, mp4, mp3, wav, etc.)",
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Pasta de saida para os arquivos de transcricao",
    )
    parser.add_argument(
        "--model", default="medium",
        help="Nome do modelo GGML (default: medium). Opcoes: tiny, base, small, medium, large",
    )
    parser.add_argument(
        "--model-dir", default=DEFAULT_MODEL_DIR,
        help=f"Pasta com modelos GGML (default: {DEFAULT_MODEL_DIR})",
    )
    parser.add_argument(
        "--language", default="pt",
        help="Codigo do idioma (default: pt)",
    )
    parser.add_argument("--no-gpu", action="store_true", help="Executa whisper.cpp na CPU")
    args = parser.parse_args()

    # Validar input
    if not os.path.isfile(args.input):
        print(f"ERRO: arquivo nao encontrado: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Verificar dependencias
    whisper_cli = find_binary("whisper-cli", "brew install whisper-cpp")
    ffmpeg_path = find_binary("ffmpeg", "brew install ffmpeg")

    model_path = find_model(args.model, args.model_dir)

    # Criar pasta de saida
    os.makedirs(args.output_dir, exist_ok=True)

    t0 = time.time()

    with tempfile.TemporaryDirectory(prefix="whisper-audio-") as tmpdir:
        audio_path = args.input
        if os.path.splitext(args.input)[1].lower() not in NATIVE_FORMATS:
            audio_path = os.path.join(tmpdir, "audio.wav")
            extract_audio(args.input, audio_path, ffmpeg_path)

        # Output base para whisper-cli (ele adiciona .json, .srt, .txt)
        output_base = os.path.join(args.output_dir, "transcript")

        # Executar whisper.cpp
        whisper_json = run_whisper(
            whisper_cli, model_path, audio_path,
            args.language, output_base, no_gpu=args.no_gpu,
        )

        # Normalizar JSON para formato padrao do projeto
        normalized = normalize_json(whisper_json)

        # Sobrescrever o JSON com formato padronizado
        json_path = output_base + ".json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)

    elapsed = round(time.time() - t0, 1)

    # Resultado
    segments = normalized.get("segments", [])
    duration_s = round(segments[-1]["end"], 1) if segments else 0.0

    output = {
        "success": True,
        "backend": "whisper.cpp",
        "model": args.model,
        "model_path": model_path,
        "output_dir": args.output_dir,
        "segments": len(segments),
        "duration_s": duration_s,
        "processing_time_s": elapsed,
        "files": [
            json_path,
            output_base + ".srt",
            output_base + ".txt",
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
