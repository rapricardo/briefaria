#!/usr/bin/env python3
"""
Montagem final de video a partir de manifest.json via FFmpeg.

Le o manifest do projeto, analisa coverage (audio vs visual),
reporta gaps, e monta o video final concatenando clips/imagens
sincronizados com o voiceover.

Modos:
  --analyze    Analisa coverage: compara duracao do VO com footage disponivel
  --assemble   Monta o video final via FFmpeg
  --dry-run    Mostra o plano de montagem sem gerar video

Uso:
    # Analisar se tem footage suficiente
    python assemble.py --manifest manifest.json --analyze

    # Montar video final
    python assemble.py --manifest manifest.json --output render/final.mp4

    # Ver plano sem executar
    python assemble.py --manifest manifest.json --output render/final.mp4 --dry-run
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def check_deps():
    """Verifica FFmpeg e ffprobe."""
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"ERRO: {tool} nao encontrado. Instale com: brew install ffmpeg", file=sys.stderr)
            sys.exit(1)


def get_duration(path: str) -> float:
    """Retorna duracao de audio/video em segundos."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def format_ts(seconds: float) -> str:
    """Formata segundos como MM:SS.s"""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:04.1f}"


def load_manifest(path: str) -> dict:
    """Carrega e valida manifest.json."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "scenes" not in data:
        print("ERRO: manifest.json nao tem campo 'scenes'", file=sys.stderr)
        sys.exit(1)
    return data


def collect_beats(manifest: dict, base_dir: str) -> list:
    """
    Extrai lista ordenada de beats com info de assets.
    Retorna: [{id, duration_s, audio_file, audio_duration, visual_file, visual_type, visual_duration, caption}]
    """
    beats = []
    for scene in manifest.get("scenes", []):
        for beat in scene.get("beats", []):
            beat_id = beat.get("id", "?")
            planned_dur = beat.get("duration_s", 3)

            # Audio
            audio_file = beat.get("audio_file")
            audio_dur = 0.0
            if audio_file:
                audio_path = os.path.join(base_dir, audio_file)
                if os.path.isfile(audio_path):
                    audio_dur = get_duration(audio_path)
                    audio_file = audio_path
                else:
                    audio_file = None

            # Visual: preferir clip > keyframe
            clip_file = beat.get("clip_file")
            keyframes = beat.get("keyframes", [])
            visual_file = None
            visual_type = None
            visual_dur = 0.0

            if clip_file:
                clip_path = os.path.join(base_dir, clip_file)
                if os.path.isfile(clip_path):
                    visual_file = clip_path
                    visual_type = "clip"
                    visual_dur = get_duration(clip_path)

            if not visual_file and keyframes:
                kf_path = os.path.join(base_dir, keyframes[0])
                if os.path.isfile(kf_path):
                    visual_file = kf_path
                    visual_type = "keyframe"
                    # Imagem estatica: duracao sera definida pelo audio ou planned
                    visual_dur = 0.0  # sem duracao propria

            # Duracao efetiva do beat: audio > clip > planned
            if audio_dur > 0:
                effective_dur = audio_dur
            elif visual_type == "clip" and visual_dur > 0:
                effective_dur = visual_dur
            else:
                effective_dur = planned_dur

            beats.append({
                "id": beat_id,
                "planned_s": planned_dur,
                "effective_s": round(effective_dur, 2),
                "audio_file": audio_file,
                "audio_dur": round(audio_dur, 2),
                "visual_file": visual_file,
                "visual_type": visual_type,
                "visual_dur": round(visual_dur, 2),
                "caption": beat.get("caption"),
                "type": beat.get("type", "scene"),
            })

    return beats


def analyze(beats: list, manifest: dict):
    """Analisa coverage e reporta gaps."""
    settings = manifest.get("settings", {})
    planned_total = settings.get("duration_total_s", 0)

    total_audio = sum(b["audio_dur"] for b in beats if b["audio_dur"] > 0)
    total_effective = sum(b["effective_s"] for b in beats)
    total_clips = sum(b["visual_dur"] for b in beats if b["visual_type"] == "clip")
    n_keyframes = sum(1 for b in beats if b["visual_type"] == "keyframe")
    n_clips = sum(1 for b in beats if b["visual_type"] == "clip")
    n_no_visual = sum(1 for b in beats if not b["visual_file"])
    n_no_audio = sum(1 for b in beats if not b["audio_file"])

    print("=" * 60)
    print(f"ANALISE DE COVERAGE — {manifest.get('project', '?')}")
    print("=" * 60)
    print()
    print(f"  Beats: {len(beats)}")
    print(f"  Duracao planejada: {format_ts(planned_total)} ({planned_total}s)")
    print(f"  Duracao efetiva:   {format_ts(total_effective)} ({total_effective:.1f}s)")
    print(f"  Audio total:       {format_ts(total_audio)} ({total_audio:.1f}s)")
    print()

    print("VISUAL:")
    print(f"  Clips de video:    {n_clips} ({format_ts(total_clips)})")
    print(f"  Keyframes (img):   {n_keyframes} (duracao depende do audio/planned)")
    print(f"  Sem visual:        {n_no_visual}")
    print()

    print("AUDIO:")
    audio_beats = [b for b in beats if b["audio_dur"] > 0]
    silent_beats = [b for b in beats if not b["audio_file"]]
    print(f"  Com audio:         {len(audio_beats)}")
    print(f"  Silenciosos:       {len(silent_beats)}")
    print()

    # Tabela beat a beat
    print(f"{'Beat':<12} {'Tipo':<10} {'Plan':>5} {'Efet':>5} {'Audio':>6} {'Visual':<10} {'VDur':>5} {'Status'}")
    print("-" * 75)
    for b in beats:
        status = ""
        if not b["visual_file"]:
            status = "SEM VISUAL"
        elif b["visual_type"] == "keyframe":
            status = "img (Ken Burns)"
        elif b["visual_type"] == "clip":
            if b["audio_dur"] > 0 and b["visual_dur"] < b["audio_dur"] - 0.5:
                status = f"CLIP CURTO ({b['audio_dur'] - b['visual_dur']:.1f}s faltam)"
            else:
                status = "OK"

        audio_str = f"{b['audio_dur']:.1f}s" if b["audio_dur"] > 0 else "—"
        vdur_str = f"{b['visual_dur']:.1f}s" if b["visual_dur"] > 0 else "—"
        vtype_str = b["visual_type"] or "—"

        print(f"  {b['id']:<10} {b['type']:<10} {b['planned_s']:>4.0f}s {b['effective_s']:>4.1f}s {audio_str:>6} {vtype_str:<10} {vdur_str:>5} {status}")

    # Gaps
    print()
    gaps = [b for b in beats if not b["visual_file"]]
    short_clips = [b for b in beats if b["visual_type"] == "clip" and b["audio_dur"] > 0 and b["visual_dur"] < b["audio_dur"] - 0.5]

    if gaps or short_clips:
        print("GAPS:")
        for b in gaps:
            print(f"  {b['id']}: sem visual — precisa gerar keyframe ou clip")
        for b in short_clips:
            deficit = b["audio_dur"] - b["visual_dur"]
            print(f"  {b['id']}: clip {b['visual_dur']:.1f}s < audio {b['audio_dur']:.1f}s — faltam {deficit:.1f}s")
    else:
        print("SEM GAPS — coverage completa.")

    # Veredicto
    print()
    if gaps or short_clips:
        print(f"VEREDICTO: Faltam {len(gaps) + len(short_clips)} beats. Gere footage antes de montar.")
    else:
        print("VEREDICTO: Pronto para montar. Use --output render/final.mp4")


def build_segment(beat: dict, tmpdir: str, idx: int, settings: dict) -> str:
    """Gera um segmento .ts para um beat."""
    w = settings.get("width", 1080)
    h = settings.get("height", 1920)
    fps = settings.get("fps", 30)
    dur = beat["effective_s"]
    out_path = os.path.join(tmpdir, f"seg_{idx:04d}.ts")

    if beat["visual_type"] == "clip" and beat["visual_file"]:
        # Clip de video — redimensionar e ajustar duracao
        if beat["audio_file"]:
            # Clip + audio: usar audio como track, ajustar visual
            subprocess.run([
                "ffmpeg", "-v", "warning", "-y",
                "-i", beat["visual_file"],
                "-i", beat["audio_file"],
                "-t", str(dur),
                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-r", str(fps),
                "-shortest",
                out_path,
            ], check=True)
        else:
            # Clip sem audio
            subprocess.run([
                "ffmpeg", "-v", "warning", "-y",
                "-i", beat["visual_file"],
                "-t", str(dur),
                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-c:v", "libx264", "-preset", "fast",
                "-an",
                "-r", str(fps),
                out_path,
            ], check=True)

    elif beat["visual_type"] == "keyframe" and beat["visual_file"]:
        # Imagem estatica — Ken Burns simples (zoom lento)
        if beat["audio_file"]:
            subprocess.run([
                "ffmpeg", "-v", "warning", "-y",
                "-loop", "1", "-i", beat["visual_file"],
                "-i", beat["audio_file"],
                "-t", str(dur),
                "-vf", (
                    f"scale={w*2}:{h*2},"
                    f"zoompan=z='1+0.001*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*fps)}:s={w}x{h}:fps={fps},"
                    f"setsar=1"
                ),
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                out_path,
            ], check=True)
        else:
            subprocess.run([
                "ffmpeg", "-v", "warning", "-y",
                "-loop", "1", "-i", beat["visual_file"],
                "-t", str(dur),
                "-vf", (
                    f"scale={w*2}:{h*2},"
                    f"zoompan=z='1+0.001*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*fps)}:s={w}x{h}:fps={fps},"
                    f"setsar=1"
                ),
                "-c:v", "libx264", "-preset", "fast",
                "-an",
                "-pix_fmt", "yuv420p",
                out_path,
            ], check=True)
    else:
        # Sem visual — tela preta com audio (se houver)
        if beat["audio_file"]:
            subprocess.run([
                "ffmpeg", "-v", "warning", "-y",
                "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={fps}:d={dur}",
                "-i", beat["audio_file"],
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                out_path,
            ], check=True)
        else:
            subprocess.run([
                "ffmpeg", "-v", "warning", "-y",
                "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={fps}:d={dur}",
                "-c:v", "libx264", "-preset", "fast",
                "-an",
                out_path,
            ], check=True)

    return out_path


def assemble(beats: list, manifest: dict, output_path: str, dry_run: bool = False):
    """Monta video final concatenando segmentos."""
    settings = manifest.get("settings", {})

    # Plano de montagem
    print(f"Plano de montagem ({len(beats)} beats):")
    print()
    cursor = 0.0
    for b in beats:
        vtype = b["visual_type"] or "black"
        audio = "+" if b["audio_file"] else " "
        cap = f' [{b["caption"]}]' if b["caption"] else ""
        print(f"  {format_ts(cursor)} | {b['id']:<10} | {b['effective_s']:>4.1f}s | {vtype:<8} | audio:{audio}{cap}")
        cursor += b["effective_s"]
    print(f"\n  Total: {format_ts(cursor)} ({cursor:.1f}s)")

    if dry_run:
        print("\n(dry-run — nenhum video gerado)")
        return

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        segments = []
        for i, beat in enumerate(beats):
            print(f"  [{i+1}/{len(beats)}] {beat['id']}...", end=" ", flush=True)
            seg = build_segment(beat, tmpdir, i, settings)
            segments.append(seg)
            print("OK")

        # Concat
        concat_file = os.path.join(tmpdir, "concat.txt")
        with open(concat_file, "w") as f:
            for s in segments:
                f.write(f"file '{s}'\n")

        print(f"\nConcatenando {len(segments)} segmentos...")
        subprocess.run([
            "ffmpeg", "-v", "warning", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_path,
        ], check=True)

        final_dur = get_duration(output_path)
        print(f"\nVideo gerado: {output_path}")
        print(f"Duracao: {format_ts(final_dur)} ({final_dur:.1f}s)")


def main():
    parser = argparse.ArgumentParser(
        description="Montagem de video a partir de manifest.json via FFmpeg"
    )
    parser.add_argument(
        "--manifest", required=True,
        help="manifest.json do projeto",
    )
    parser.add_argument(
        "--output", default=None,
        help="Caminho do video de saida (ex: render/final.mp4)",
    )
    parser.add_argument(
        "--analyze", action="store_true",
        help="Analisa coverage: audio vs footage disponivel",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra plano de montagem sem gerar video",
    )
    args = parser.parse_args()

    check_deps()

    if not os.path.isfile(args.manifest):
        print(f"ERRO: manifest nao encontrado: {args.manifest}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(args.manifest)
    base_dir = os.path.dirname(os.path.abspath(args.manifest))
    beats = collect_beats(manifest, base_dir)

    if not beats:
        print("Nenhum beat encontrado no manifest.")
        return

    if args.analyze:
        analyze(beats, manifest)
        return

    output = args.output or os.path.join(base_dir, "render", "final.mp4")
    assemble(beats, manifest, output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
