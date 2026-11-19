#!/usr/bin/env python3
"""
ElevenLabs Voice-Over Generator - Skill Script
Gera áudio de narração via ElevenLabs Text-to-Speech API.

Modos:
  dry-run     - Mostra texto parseado sem gerar
  voices      - Lista vozes disponíveis
  full        - Gera 1 MP3 de texto livre
  from-script - Parse vo_script.txt → 1 MP3
  per-act     - Parse vo_script.txt → 1 MP3 por ato
  per-beat    - Parse manifest.json → 1 MP3 por beat

Requer: ELEVENLABS_API_KEY como variável de ambiente.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_multilingual_v2"


def load_dotenv():
    """Carrega variáveis de um arquivo .env se existir."""
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


def get_api_key():
    """Retorna ELEVENLABS_API_KEY ou falha."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        print("ERROR: ELEVENLABS_API_KEY não encontrada.")
        print('Configure com: export ELEVENLABS_API_KEY="sua-chave"')
        sys.exit(1)
    return key


def parse_vo_script(script_path):
    """Parse vo_script.txt → lista de atos com texto.

    Returns:
        list of dict: [{"act": 1, "label": "CONFLITO", "duration": "07s", "text": "..."}]
    """
    if not os.path.exists(script_path):
        print(f"ERROR: Script não encontrado: {script_path}")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern: [ATO N — LABEL — DURATIONs]
    act_pattern = re.compile(
        r"\[ATO\s+(\d+)\s*[—–-]\s*([^—–\]]+?)\s*[—–-]\s*(\d+s)\]",
        re.IGNORECASE,
    )

    acts = []
    parts = act_pattern.split(content)

    # parts: [header, act_num, label, duration, text, act_num, label, duration, text, ...]
    i = 1
    while i < len(parts) - 3:
        act_num = int(parts[i])
        label = parts[i + 1].strip()
        duration = parts[i + 2].strip()
        text_block = parts[i + 3]

        # Limpar o texto: remover [PAUSA ...], separadores, notas de direção
        # Cortar tudo a partir de "NOTAS DE DIREÇÃO" ou separador final
        text = re.split(r"NOTAS DE DIREÇÃO|={5,}", text_block)[0]
        text = re.sub(r"\[PAUSA[^\]]*\]", "", text)
        text = text.strip()

        # Só adicionar se tiver texto
        if text:
            acts.append({
                "act": act_num,
                "label": label,
                "duration": duration,
                "text": text,
            })

        i += 4

    return acts


def get_full_text(acts):
    """Combina todos os atos em texto contínuo com pausas."""
    parts = []
    for act in acts:
        parts.append(act["text"])
    return " ... ".join(parts)  # "..." cria pausa natural no TTS


def generate_speech(text, voice_id, api_key, model=DEFAULT_MODEL, output_format="mp3_44100_128"):
    """Gera áudio via ElevenLabs TTS. Retorna bytes."""
    url = f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}?output_format={output_format}"

    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"ElevenLabs API error ({e.code}): {error_body}")


def save_audio(audio_bytes, output_path):
    """Salva bytes de áudio em arquivo."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    size_kb = len(audio_bytes) / 1024
    print(f"  💾 Salvo: {output_path} ({size_kb:.0f}KB)")


def list_voices(api_key):
    """Lista vozes disponíveis na conta."""
    url = f"{ELEVENLABS_API_BASE}/voices"

    req = urllib.request.Request(
        url,
        headers={
            "xi-api-key": api_key,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("voices", [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"ElevenLabs API error ({e.code}): {error_body}")


def load_manifest(manifest_path):
    """Load manifest.json and extract beats with audio_text."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    beats = []
    for scene in manifest["scenes"]:
        for beat in scene["beats"]:
            if beat.get("audio_text"):
                beats.append(beat)

    return manifest, beats


def generate_per_beat(manifest_path, output_dir, voice_override=None, dry_run=False):
    """Generate 1 MP3 per beat that has audio_text."""
    manifest, beats = load_manifest(manifest_path)
    characters = manifest.get("characters", {})

    os.makedirs(output_dir, exist_ok=True)

    if not dry_run:
        api_key = get_api_key()

    results = []
    for beat in beats:
        who = beat["who"]
        voice_id = voice_override or characters.get(who, {}).get("voice_id")

        filename = f"{who}_{beat['id']}.mp3"
        output_path = os.path.join(output_dir, filename)

        if dry_run:
            print(f"  [DRY-RUN] {filename} ({who}: \"{beat['audio_text'][:50]}\")")
            results.append((beat["id"], "DRY", filename))
            continue

        if not voice_id:
            print(f"  WARN: No voice_id for '{who}', skipping beat {beat['id']}")
            results.append((beat["id"], "SKIP", f"no voice_id for {who}"))
            continue

        print(f"  Gerando: {filename} ({who}: \"{beat['audio_text'][:50]}\")")
        try:
            audio_data = generate_speech(beat["audio_text"], voice_id, api_key)
            with open(output_path, "wb") as f:
                f.write(audio_data)

            beat["audio_file"] = f"audio/{filename}"
            size_kb = len(audio_data) / 1024
            print(f"  Salvo: {output_path} ({size_kb:.0f}KB)")
            results.append((beat["id"], "OK", output_path))
        except Exception as e:
            print(f"  Erro: {e}")
            results.append((beat["id"], "FAIL", str(e)))

    # Save updated manifest (only if not dry-run)
    if not dry_run:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"\nManifest atualizado: {manifest_path}")

    # Summary
    print(f"\nResumo:")
    for beat_id, status, detail in results:
        print(f"  [{status}] {beat_id}: {detail}")


# === CLI Commands ===


def cmd_dry_run(args):
    """Mostra texto parseado do vo_script.txt."""
    acts = parse_vo_script(args.script)

    print(f"📋 Script: {args.script}")
    print(f"📊 Total de atos: {len(acts)}")
    print()

    for act in acts:
        print(f"--- Ato {act['act']} — {act['label']} ({act['duration']}) ---")
        print(f"  {act['text']}")
        print(f"  Caracteres: {len(act['text'])}")
        print()

    full_text = get_full_text(acts)
    print(f"📝 Texto completo ({len(full_text)} chars):")
    print(f"  {full_text}")


def cmd_voices(args):
    """Lista vozes disponíveis."""
    api_key = get_api_key()
    voices = list_voices(api_key)

    print(f"🎙️  {len(voices)} vozes disponíveis:\n")
    print(f"{'ID':<28} {'Nome':<20} {'Categoria':<12} {'Labels'}")
    print("-" * 80)

    for v in voices:
        voice_id = v.get("voice_id", "")
        name = v.get("name", "")
        category = v.get("category", "")
        labels = v.get("labels", {})
        label_str = ", ".join(f"{k}: {val}" for k, val in labels.items()) if labels else ""
        print(f"{voice_id:<28} {name:<20} {category:<12} {label_str}")


def cmd_full(args):
    """Gera 1 MP3 de texto livre."""
    api_key = get_api_key()
    voice_id = args.voice_id
    model = args.model or DEFAULT_MODEL
    output = args.output or "vo_output.mp3"

    print(f"🎙️  Gerando VO...")
    print(f"  Voz: {voice_id}")
    print(f"  Modelo: {model}")
    print(f"  Texto: {len(args.text)} chars")

    audio = generate_speech(args.text, voice_id, api_key, model)
    save_audio(audio, output)
    print(f"\n🎉 Voice-over gerado com sucesso!")


def cmd_from_script(args):
    """Parse vo_script.txt → 1 MP3 contínuo."""
    api_key = get_api_key()
    voice_id = args.voice_id
    model = args.model or DEFAULT_MODEL

    acts = parse_vo_script(args.script)
    full_text = get_full_text(acts)

    output = args.output or os.path.join(os.path.dirname(args.script), "vo_full.mp3")

    print(f"🎙️  Gerando VO do script completo...")
    print(f"  Voz: {voice_id}")
    print(f"  Modelo: {model}")
    print(f"  Atos: {len(acts)}")
    print(f"  Texto: {len(full_text)} chars")

    audio = generate_speech(full_text, voice_id, api_key, model)
    save_audio(audio, output)
    print(f"\n🎉 Voice-over gerado com sucesso!")


def cmd_per_act(args):
    """Parse vo_script.txt → 1 MP3 por ato."""
    api_key = get_api_key()
    voice_id = args.voice_id
    model = args.model or DEFAULT_MODEL

    acts = parse_vo_script(args.script)
    output_dir = args.output_dir or os.path.dirname(args.script)

    print(f"🎙️  Gerando VO por ato...")
    print(f"  Voz: {voice_id}")
    print(f"  Modelo: {model}")
    print(f"  Atos: {len(acts)}")

    results = []
    for act in acts:
        act_num = act["act"]
        label = act["label"]
        print(f"\n  🎤 Ato {act_num} — {label} ({len(act['text'])} chars)...")

        try:
            audio = generate_speech(act["text"], voice_id, api_key, model)
            output_path = os.path.join(output_dir, f"vo_ato_{act_num:02d}.mp3")
            save_audio(audio, output_path)
            results.append((act_num, "✅", output_path))
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            results.append((act_num, "❌", str(e)))

    print(f"\n{'='*40}")
    print(f"📊 Resumo")
    for act_num, status, detail in results:
        print(f"  {status} Ato {act_num}: {detail}")

    success = sum(1 for _, s, _ in results if s == "✅")
    print(f"\n{success}/{len(results)} atos gerados com sucesso.")


def cmd_per_beat(args):
    """Parse manifest.json → 1 MP3 por beat."""
    print(f"Manifest: {args.manifest}")
    print(f"Output dir: {args.output_dir}")
    if args.dry_run:
        print("DRY RUN - nenhuma chamada de API")
    print()
    generate_per_beat(
        args.manifest,
        args.output_dir,
        voice_override=args.voice_override,
        dry_run=args.dry_run,
    )


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Gera voice-overs via ElevenLabs TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python elevenlabs_vo.py voices
  python elevenlabs_vo.py dry-run --script voiceover/vo_script.txt
  python elevenlabs_vo.py from-script --script voiceover/vo_script.txt --voice-id ID
  python elevenlabs_vo.py per-act --script voiceover/vo_script.txt --voice-id ID
  python elevenlabs_vo.py per-beat --manifest manifest.json --output-dir audio/ --dry-run
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Modo de operação")

    # dry-run
    p_dry = subparsers.add_parser("dry-run", help="Mostra texto parseado")
    p_dry.add_argument("--script", required=True, help="Caminho para vo_script.txt")

    # voices
    subparsers.add_parser("voices", help="Lista vozes disponíveis")

    # full
    p_full = subparsers.add_parser("full", help="Gera MP3 de texto livre")
    p_full.add_argument("--text", required=True, help="Texto para gerar")
    p_full.add_argument("--voice-id", required=True, help="ID da voz")
    p_full.add_argument("--output", help="Caminho de saída (default: vo_output.mp3)")
    p_full.add_argument("--model", help=f"Modelo (default: {DEFAULT_MODEL})")

    # from-script
    p_script = subparsers.add_parser("from-script", help="Parse script → 1 MP3")
    p_script.add_argument("--script", required=True, help="Caminho para vo_script.txt")
    p_script.add_argument("--voice-id", required=True, help="ID da voz")
    p_script.add_argument("--output", help="Caminho de saída (default: vo_full.mp3)")
    p_script.add_argument("--model", help=f"Modelo (default: {DEFAULT_MODEL})")

    # per-act
    p_act = subparsers.add_parser("per-act", help="Parse script → 1 MP3 por ato")
    p_act.add_argument("--script", required=True, help="Caminho para vo_script.txt")
    p_act.add_argument("--voice-id", required=True, help="ID da voz")
    p_act.add_argument("--output-dir", help="Pasta de saída")
    p_act.add_argument("--model", help=f"Modelo (default: {DEFAULT_MODEL})")

    # per-beat
    p_beat = subparsers.add_parser("per-beat", help="Parse manifest → 1 MP3 por beat")
    p_beat.add_argument("--manifest", required=True, help="Caminho para manifest.json")
    p_beat.add_argument("--output-dir", required=True, help="Pasta de saída para os MP3s")
    p_beat.add_argument("--voice-override", help="Voice ID override (ignora manifest)")
    p_beat.add_argument("--model", help=f"Modelo (default: {DEFAULT_MODEL})")
    p_beat.add_argument("--dry-run", action="store_true", help="Mostra o que seria gerado sem chamar API")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "dry-run":
        cmd_dry_run(args)
    elif args.command == "voices":
        cmd_voices(args)
    elif args.command == "full":
        cmd_full(args)
    elif args.command == "from-script":
        cmd_from_script(args)
    elif args.command == "per-act":
        cmd_per_act(args)
    elif args.command == "per-beat":
        cmd_per_beat(args)


if __name__ == "__main__":
    main()
