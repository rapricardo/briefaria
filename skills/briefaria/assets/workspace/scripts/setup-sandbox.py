#!/usr/bin/env python3
"""
Setup do sandbox Cowork para a Máquina de Produção.

Instala todas as dependências necessárias para rodar o pipeline completo
de vídeo dentro do ambiente sandbox do Cowork (Ubuntu Linux).

O que faz:
  1. Verifica ferramentas já disponíveis (ffmpeg, python, node)
  2. Instala cmake via pip (se necessário)
  3. Compila whisper.cpp e cacheia o binário em .cache/bin/
  4. Baixa modelo ggml-medium.bin (se necessário, ~1.4GB)
  5. Instala dependências do Remotion (npm install)
  6. Valida chaves no .env
  7. Atualiza transcribe.py para encontrar o binário cacheado

Uso:
    python scripts/setup-sandbox.py
    python scripts/setup-sandbox.py --skip-whisper    # pula compilação
    python scripts/setup-sandbox.py --skip-remotion   # pula npm install
    python scripts/setup-sandbox.py --model small      # modelo menor (faster)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

# Paths relativos à raiz do projeto
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_BIN = os.path.join(REPO_ROOT, ".cache", "bin")
CACHE_LIB = os.path.join(REPO_ROOT, ".cache", "lib")
MODELS_DIR = os.path.join(REPO_ROOT, "models")
REMOTION_DIR = os.path.join(REPO_ROOT, "remotion")
ENV_FILE = os.path.join(REPO_ROOT, ".env")

# URL base para modelos whisper.cpp
WHISPER_MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"

# Chaves obrigatórias e opcionais
REQUIRED_KEYS = []  # nenhuma é hard-required — depende do pipeline
OPTIONAL_KEYS = {
    "GEMINI_API_KEY": "Geração de imagens (imagen.py)",
    "ELEVENLABS_API_KEY": "Voice-over (elevenlabs_vo.py)",
    "FAL_KEY": "Geração de vídeo clips (fal_video.py)",
}


def log(msg: str, level: str = "info"):
    icons = {"info": "ℹ", "ok": "✓", "warn": "⚠", "error": "✗", "step": "→"}
    icon = icons.get(level, "•")
    print(f"  {icon} {msg}")


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    """Executa comando com PATH estendido."""
    env = os.environ.copy()
    env["PATH"] = f"{CACHE_BIN}:{env.get('PATH', '')}"
    if CACHE_LIB:
        env["LD_LIBRARY_PATH"] = f"{CACHE_LIB}:{env.get('LD_LIBRARY_PATH', '')}"
    return subprocess.run(cmd, env=env, **kwargs)


def check_base_tools() -> dict:
    """Verifica ferramentas base do sandbox."""
    tools = {}
    for name in ["ffmpeg", "python3", "node", "npm", "gcc", "g++", "make", "git", "curl"]:
        path = shutil.which(name)
        tools[name] = path
        if path:
            log(f"{name}: {path}", "ok")
        else:
            log(f"{name}: NÃO ENCONTRADO", "error")
    return tools


def ensure_cmake() -> str:
    """Instala cmake via pip se necessário."""
    # Verificar se já existe
    cmake = shutil.which("cmake")
    if cmake:
        log(f"cmake já disponível: {cmake}", "ok")
        return cmake

    # Verificar no pip local
    pip_bin = os.path.expanduser("~/.local/bin/cmake")
    if os.path.isfile(pip_bin):
        log(f"cmake encontrado em pip local: {pip_bin}", "ok")
        return pip_bin

    log("Instalando cmake via pip...", "step")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "cmake", "--break-system-packages", "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"Falha ao instalar cmake: {result.stderr}", "error")
        sys.exit(1)

    # Encontrar onde foi instalado
    for candidate in [pip_bin, os.path.expanduser("~/.local/bin/cmake")]:
        if os.path.isfile(candidate):
            log(f"cmake instalado: {candidate}", "ok")
            return candidate

    log("cmake instalado mas não encontrado no PATH", "error")
    sys.exit(1)


def build_whisper(cmake_path: str) -> str:
    """Compila whisper.cpp e cacheia o binário."""
    whisper_bin = os.path.join(CACHE_BIN, "whisper-cli")

    # Verificar cache
    if os.path.isfile(whisper_bin) and os.access(whisper_bin, os.X_OK):
        log("whisper-cli encontrado no cache", "ok")
        return whisper_bin

    log("Compilando whisper.cpp (pode levar ~40s)...", "step")
    t0 = time.time()

    # Clone
    build_dir = "/tmp/whisper-build"
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", "https://github.com/ggerganov/whisper.cpp.git", build_dir],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"Falha ao clonar whisper.cpp: {result.stderr}", "error")
        sys.exit(1)

    # Configure
    result = subprocess.run(
        [cmake_path, "-B", "build", "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=ON"],
        capture_output=True, text=True, cwd=build_dir
    )
    if result.returncode != 0:
        log(f"Falha no cmake configure: {result.stderr}", "error")
        sys.exit(1)

    # Build
    nproc = os.cpu_count() or 2
    result = subprocess.run(
        [cmake_path, "--build", "build", "--config", "Release", f"-j{nproc}", "--target", "whisper-cli"],
        capture_output=True, text=True, cwd=build_dir
    )
    if result.returncode != 0:
        log(f"Falha na compilação: {result.stderr}", "error")
        sys.exit(1)

    elapsed = round(time.time() - t0, 1)

    # Copiar binário e libs para cache
    os.makedirs(CACHE_BIN, exist_ok=True)
    os.makedirs(CACHE_LIB, exist_ok=True)

    src_bin = os.path.join(build_dir, "build", "bin", "whisper-cli")
    shutil.copy2(src_bin, whisper_bin)
    os.chmod(whisper_bin, 0o755)

    # Copiar shared libs necessárias + criar symlinks versionados
    for lib_dir in ["build/src", "build/ggml/src"]:
        full_dir = os.path.join(build_dir, lib_dir)
        if os.path.isdir(full_dir):
            for f in os.listdir(full_dir):
                if f.endswith(".so"):
                    dest = os.path.join(CACHE_LIB, f)
                    shutil.copy2(os.path.join(full_dir, f), dest)
                    # Criar symlink versionado (libwhisper.so -> libwhisper.so.1)
                    symlink = dest + ".1"
                    if os.path.islink(symlink):
                        os.remove(symlink)
                    os.symlink(f, symlink)

    # Cleanup
    shutil.rmtree(build_dir, ignore_errors=True)

    log(f"whisper-cli compilado em {elapsed}s → {whisper_bin}", "ok")
    return whisper_bin


def ensure_model(model_name: str) -> str:
    """Verifica se o modelo existe, oferece download se não."""
    model_file = os.path.join(MODELS_DIR, f"ggml-{model_name}.bin")

    if os.path.isfile(model_file):
        size_mb = os.path.getsize(model_file) // (1024 * 1024)
        log(f"Modelo ggml-{model_name}.bin encontrado ({size_mb}MB)", "ok")
        return model_file

    os.makedirs(MODELS_DIR, exist_ok=True)
    url = f"{WHISPER_MODEL_URL}/ggml-{model_name}.bin"
    log(f"Modelo não encontrado. Baixando ggml-{model_name}.bin...", "step")
    log(f"URL: {url}", "info")

    result = subprocess.run(
        ["curl", "-L", "--progress-bar", "-o", model_file, url]
    )
    if result.returncode != 0 or not os.path.isfile(model_file):
        log(f"Falha ao baixar modelo", "error")
        sys.exit(1)

    size_mb = os.path.getsize(model_file) // (1024 * 1024)
    log(f"Modelo baixado: {model_file} ({size_mb}MB)", "ok")
    return model_file


def setup_remotion():
    """Instala dependências do Remotion."""
    node_modules = os.path.join(REMOTION_DIR, "node_modules")

    if os.path.isdir(node_modules):
        log("Remotion node_modules já existe", "ok")
        return

    if not os.path.isfile(os.path.join(REMOTION_DIR, "package.json")):
        log("Pasta remotion/ não encontrada, pulando", "warn")
        return

    log("Instalando dependências do Remotion (npm install)...", "step")
    result = subprocess.run(
        ["npm", "install", "--prefer-offline"],
        capture_output=True, text=True, cwd=REMOTION_DIR
    )
    if result.returncode != 0:
        log(f"npm install falhou: {result.stderr}", "error")
        return

    log("Remotion pronto", "ok")


def validate_env() -> dict:
    """Valida chaves no .env."""
    found = {}

    if not os.path.isfile(ENV_FILE):
        log(f".env não encontrado em {ENV_FILE}", "warn")
        log("Crie o arquivo com suas API keys", "info")
        return found

    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value:
                found[key] = True

    for key, desc in OPTIONAL_KEYS.items():
        if key in found:
            log(f"{key}: configurada ({desc})", "ok")
        else:
            log(f"{key}: ausente — {desc} não funcionará", "warn")

    return found


def write_status(results: dict):
    """Salva resultado do setup em .cache/sandbox-status.json."""
    status_dir = os.path.join(REPO_ROOT, ".cache")
    os.makedirs(status_dir, exist_ok=True)
    status_file = os.path.join(status_dir, "sandbox-status.json")

    with open(status_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log(f"Status salvo em {status_file}", "ok")


def main():
    parser = argparse.ArgumentParser(description="Setup do sandbox Cowork")
    parser.add_argument("--skip-whisper", action="store_true", help="Pular compilação do whisper.cpp")
    parser.add_argument("--skip-remotion", action="store_true", help="Pular npm install do Remotion")
    parser.add_argument("--model", default="medium", help="Modelo whisper (default: medium)")
    args = parser.parse_args()

    print("\n🔧 Máquina de Produção — Setup do Sandbox\n")
    t0 = time.time()
    results = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "steps": {}}

    # 1. Ferramentas base
    section("1. Verificando ferramentas base")
    tools = check_base_tools()
    results["steps"]["base_tools"] = {k: bool(v) for k, v in tools.items()}

    if not tools.get("ffmpeg"):
        log("ffmpeg é obrigatório e não foi encontrado!", "error")
        sys.exit(1)

    # 2. cmake
    section("2. cmake")
    cmake_path = ensure_cmake()
    results["steps"]["cmake"] = cmake_path

    # 3. whisper.cpp
    section("3. whisper.cpp")
    if args.skip_whisper:
        log("Pulando compilação (--skip-whisper)", "warn")
        results["steps"]["whisper"] = "skipped"
    else:
        whisper_bin = build_whisper(cmake_path)
        results["steps"]["whisper"] = whisper_bin

    # 4. Modelo
    section("4. Modelo Whisper")
    if args.skip_whisper:
        log("Pulando verificação de modelo (--skip-whisper)", "warn")
        results["steps"]["model"] = "skipped"
    else:
        model_path = ensure_model(args.model)
        results["steps"]["model"] = model_path

    # 5. Remotion
    section("5. Remotion")
    if args.skip_remotion:
        log("Pulando Remotion (--skip-remotion)", "warn")
        results["steps"]["remotion"] = "skipped"
    else:
        setup_remotion()
        results["steps"]["remotion"] = os.path.isdir(os.path.join(REMOTION_DIR, "node_modules"))

    # 6. .env
    section("6. Variáveis de ambiente")
    env_keys = validate_env()
    results["steps"]["env_keys"] = list(env_keys.keys())

    # 7. Resumo
    elapsed = round(time.time() - t0, 1)
    results["total_time_s"] = elapsed

    write_status(results)

    section("Setup completo!")
    log(f"Tempo total: {elapsed}s", "ok")
    log(f"whisper-cli: {results['steps'].get('whisper', 'N/A')}", "info")
    log(f"ffmpeg: {tools.get('ffmpeg', 'N/A')}", "info")
    log(f"node: {tools.get('node', 'N/A')}", "info")
    print("\n✅ Pronto para trabalhar.\n")


if __name__ == "__main__":
    main()
