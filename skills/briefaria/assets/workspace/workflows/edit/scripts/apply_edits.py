#!/usr/bin/env python3
"""
Aplica edit_decisions.json a um vídeo usando FFmpeg.

Lê as decisões de edição e gera um vídeo cortado sem modificar o original.
Suporta: cut_silence, remove_segment, insert_broll, insert_image.

Uso:
    python apply_edits.py --input recordings/screen.mkv \
        --decisions transcript/edit_decisions.json \
        --output render/rascunho.mp4

    # Preview: só lista os cortes sem gerar vídeo
    python apply_edits.py --input recordings/screen.mkv \
        --decisions transcript/edit_decisions.json \
        --dry-run

    # Exportar EDL para DaVinci Resolve
    python apply_edits.py --input recordings/screen.mkv \
        --decisions transcript/edit_decisions.json \
        --export-edl render/timeline.edl
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def check_ffmpeg():
    """Verifica se FFmpeg está instalado."""
    if not shutil.which("ffmpeg"):
        print(
            "ERRO: ffmpeg não encontrado no PATH.\n"
            "Instale com: brew install ffmpeg",
            file=sys.stderr,
        )
        sys.exit(1)
    if not shutil.which("ffprobe"):
        print(
            "ERRO: ffprobe não encontrado no PATH.\n"
            "Instale com: brew install ffmpeg",
            file=sys.stderr,
        )
        sys.exit(1)


def get_video_duration(path: str) -> float:
    """Retorna duração do vídeo em segundos via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            path,
        ],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def parse_timestamp(ts: str) -> float:
    """Converte timestamp 'HH:MM:SS.mmm' para segundos."""
    parts = ts.replace(",", ".").split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(parts[0])


def format_timestamp(seconds: float) -> str:
    """Formata segundos como HH:MM:SS.mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def detect_format_version(data: dict) -> int:
    """
    Detecta o formato do edit_decisions.json.
    v2: tem campo "version": 2 e decisions com "start"/"end" (floats)
    v1: decisions com "from"/"to" (timestamps string)
    """
    if data.get("version") == 2:
        return 2
    decisions = data.get("decisions", [])
    if decisions and "start" in decisions[0] and "end" in decisions[0]:
        return 2
    return 1


def compute_keep_segments(decisions: list, total_duration: float, format_version: int = 1) -> list:
    """
    Calcula os segmentos a MANTER.
    v1: inverte remocoes (cut_silence/remove_segment com from/to)
    v2: usa diretamente os keeps (keep/cut com start/end)
    Retorna lista de (start, end) em segundos.
    """
    if format_version == 2:
        # v2: ler keeps diretamente
        keeps = []
        for d in decisions:
            if d.get("type") == "keep":
                keeps.append((float(d["start"]), float(d["end"])))
        if not keeps:
            return [(0, total_duration)]
        keeps.sort()
        return keeps

    # v1: coletar remocoes e inverter
    removals = []
    for d in decisions:
        dtype = d.get("type", "")
        if dtype in ("cut_silence", "remove_segment"):
            start = parse_timestamp(d["from"])
            end = parse_timestamp(d["to"])
            removals.append((start, end))

    if not removals:
        return [(0, total_duration)]

    # Ordenar e merge de intervalos sobrepostos
    removals.sort()
    merged = [removals[0]]
    for start, end in removals[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Calcular segmentos a manter (inverso dos removidos)
    keeps = []
    cursor = 0.0
    for rm_start, rm_end in merged:
        if cursor < rm_start:
            keeps.append((cursor, rm_start))
        cursor = rm_end
    if cursor < total_duration:
        keeps.append((cursor, total_duration))

    return keeps


def compute_inserts(decisions: list) -> list:
    """Extrai inserções de b-roll e imagem."""
    inserts = []
    for d in decisions:
        dtype = d.get("type", "")
        if dtype == "insert_broll":
            inserts.append({
                "type": "video",
                "at": parse_timestamp(d["at"]),
                "duration": d.get("duration_s", 4),
                "asset": d["asset"],
                "description": d.get("description", ""),
            })
        elif dtype == "insert_image":
            inserts.append({
                "type": "image",
                "at": parse_timestamp(d["at"]),
                "duration": d.get("duration_s", 3),
                "asset": d["asset"],
                "description": d.get("description", ""),
            })
    return sorted(inserts, key=lambda x: x["at"])


def dry_run(input_path: str, decisions: list, total_duration: float, format_version: int = 1):
    """Mostra preview dos cortes sem gerar vídeo."""
    keeps = compute_keep_segments(decisions, total_duration, format_version)
    inserts = compute_inserts(decisions)

    removed_total = 0.0
    if format_version == 2:
        for d in decisions:
            if d.get("type") == "cut":
                removed_total += float(d["end"]) - float(d["start"])
    else:
        for d in decisions:
            if d.get("type") in ("cut_silence", "remove_segment"):
                start = parse_timestamp(d["from"])
                end = parse_timestamp(d["to"])
                removed_total += end - start

    print(f"Arquivo: {input_path}")
    print(f"Duração original: {format_timestamp(total_duration)} ({total_duration:.1f}s)")
    print(f"Tempo removido: {format_timestamp(removed_total)} ({removed_total:.1f}s)")
    print(f"Duração estimada: {format_timestamp(total_duration - removed_total)} ({total_duration - removed_total:.1f}s)")
    print()

    print(f"Segmentos mantidos ({len(keeps)}):")
    for i, (start, end) in enumerate(keeps, 1):
        dur = end - start
        print(f"  {i}. {format_timestamp(start)} → {format_timestamp(end)} ({dur:.1f}s)")

    if inserts:
        print(f"\nInserções ({len(inserts)}):")
        for ins in inserts:
            print(f"  {ins['type']} em {format_timestamp(ins['at'])}: {ins['description']} ({ins['duration']}s) → {ins['asset']}")

    # Verificar assets existentes
    missing = [ins["asset"] for ins in inserts if not os.path.isfile(ins["asset"])]
    if missing:
        print(f"\n⚠ Assets não encontrados:")
        for m in missing:
            print(f"  {m}")


def probe_streams(path: str) -> list:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,width,height,avg_frame_rate", "-of", "json", path,
    ], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)["streams"]


def apply_with_ffmpeg(input_path: str, decisions: list, total_duration: float, output_path: str, format_version: int = 1):
    """Codifica cortes exatos e normaliza inserções antes de concatenar."""
    keeps = compute_keep_segments(decisions, total_duration, format_version)
    inserts = compute_inserts(decisions)

    if not keeps:
        print("Nenhum segmento para manter. Nada a fazer.")
        return
    if os.path.realpath(input_path) == os.path.realpath(output_path) or (
        os.path.exists(output_path) and os.path.samefile(input_path, output_path)
    ):
        raise SystemExit("O arquivo de saída precisa ser diferente do original.")

    source_streams = probe_streams(input_path)
    video = next((stream for stream in source_streams if stream["codec_type"] == "video"), None)
    if video is None:
        raise SystemExit("O arquivo de entrada precisa ter uma faixa de vídeo.")
    width = (video["width"] + 1) // 2 * 2
    height = (video["height"] + 1) // 2 * 2
    fps = video["avg_frame_rate"] if video.get("avg_frame_rate") not in (None, "0/0") else "30"
    audio_available = {input_path: any(s["codec_type"] == "audio" for s in source_streams)}
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )

    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir) as tmpdir:
        parts = []

        def append_segment(path, start, duration, is_image=False):
            part = os.path.join(tmpdir, f"part_{len(parts):04d}.mp4")
            command = ["ffmpeg", "-v", "error", "-y"]
            if is_image:
                command.extend(["-loop", "1"])
                audio_available[path] = False
            if start:
                command.extend(["-ss", str(start)])
            command.extend(["-i", path])
            if path not in audio_available:
                audio_available[path] = any(s["codec_type"] == "audio" for s in probe_streams(path))
            if audio_available[path]:
                command.extend(["-map", "0:v:0", "-map", "0:a:0", "-af", "apad"])
            else:
                command.extend(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                                "-map", "0:v:0", "-map", "1:a:0"])
            command.extend([
                "-t", str(duration), "-shortest", "-vf", video_filter, "-r", fps,
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "48000", "-ac", "2", part,
            ])
            subprocess.run(command, check=True)
            parts.append(part)

        insert_idx = 0
        for keep_start, keep_end in keeps:
            while insert_idx < len(inserts) and inserts[insert_idx]["at"] <= keep_end:
                ins = inserts[insert_idx]
                if ins["at"] > keep_start:
                    append_segment(input_path, keep_start, ins["at"] - keep_start)
                    keep_start = ins["at"]
                if os.path.isfile(ins["asset"]):
                    append_segment(ins["asset"], 0, ins["duration"], is_image=ins["type"] == "image")
                else:
                    print(f"⚠ Asset não encontrado, pulando: {ins['asset']}")
                insert_idx += 1

            if keep_start < keep_end:
                append_segment(input_path, keep_start, keep_end - keep_start)

        concat_file = os.path.join(tmpdir, "concat.txt")
        with open(concat_file, "w") as f:
            for part in parts:
                f.write(f"file '{os.path.basename(part)}'\n")

        staged_output = os.path.join(tmpdir, "render" + os.path.splitext(output_path)[1])
        print(f"Concatenando {len(parts)} segmentos...")
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "1",
            "-i", concat_file, "-c", "copy", "-movflags", "+faststart", staged_output,
        ], check=True)
        final_duration = get_video_duration(staged_output)
        os.replace(staged_output, output_path)

    print(f"Vídeo gerado: {output_path}")
    print(f"Duração original: {total_duration:.1f}s → Final: {final_duration:.1f}s")
    print(f"Removido: {total_duration - final_duration:.1f}s")


def export_edl(input_path: str, decisions: list, total_duration: float, edl_path: str, format_version: int = 1):
    """Exporta timeline como EDL (CMX 3600) para DaVinci Resolve."""
    keeps = compute_keep_segments(decisions, total_duration, format_version)
    filename = os.path.basename(input_path)

    os.makedirs(os.path.dirname(edl_path) or ".", exist_ok=True)

    lines = [
        "TITLE: Edit Decisions",
        "FCM: NON-DROP FRAME",
        "",
    ]

    # Record timeline cursor
    record_cursor = 0.0

    for i, (src_start, src_end) in enumerate(keeps, 1):
        dur = src_end - src_start
        record_end = record_cursor + dur

        # EDL usa formato HH:MM:SS:FF (frames a 30fps)
        def to_tc(s):
            h = int(s // 3600)
            m = int((s % 3600) // 60)
            sec = int(s % 60)
            fr = int((s % 1) * 30)
            return f"{h:02d}:{m:02d}:{sec:02d}:{fr:02d}"

        lines.append(
            f"{i:03d}  {filename:<32s} V     C        "
            f"{to_tc(src_start)} {to_tc(src_end)} "
            f"{to_tc(record_cursor)} {to_tc(record_end)}"
        )
        lines.append("")
        record_cursor = record_end

    with open(edl_path, "w") as f:
        f.write("\n".join(lines))

    print(f"EDL exportado: {edl_path}")
    print(f"{len(keeps)} segmentos, duração estimada: {format_timestamp(record_cursor)}")


def main():
    parser = argparse.ArgumentParser(
        description="Aplica edit_decisions.json a um vídeo via FFmpeg"
    )
    parser.add_argument(
        "--input", required=True,
        help="Vídeo original (recordings/*.mkv)",
    )
    parser.add_argument(
        "--decisions", required=True,
        help="Arquivo edit_decisions.json",
    )
    parser.add_argument(
        "--output", default=None,
        help="Caminho do vídeo de saída (default: render/rascunho.mp4)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra preview dos cortes sem gerar vídeo",
    )
    parser.add_argument(
        "--export-edl", default=None,
        help="Exportar EDL para DaVinci Resolve",
    )
    args = parser.parse_args()

    check_ffmpeg()

    # Validar inputs
    if not os.path.isfile(args.input):
        print(f"ERRO: vídeo não encontrado: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.decisions):
        print(f"ERRO: edit_decisions.json não encontrado: {args.decisions}", file=sys.stderr)
        sys.exit(1)

    # Ler decisões
    with open(args.decisions, "r", encoding="utf-8") as f:
        data = json.load(f)
    decisions = data.get("decisions", [])

    if not decisions:
        print("Nenhuma decisão de edição encontrada.")
        return

    # Detectar formato (v1: remove_segment com from/to, v2: keep/cut com start/end)
    fmt = detect_format_version(data)
    if fmt == 2:
        print(f"Formato v2 detectado ({len([d for d in decisions if d.get('type') == 'keep'])} keeps, "
              f"{len([d for d in decisions if d.get('type') == 'cut'])} cuts)")

    # Obter duração do vídeo
    total_duration = get_video_duration(args.input)

    if args.dry_run:
        dry_run(args.input, decisions, total_duration, fmt)
        return

    if args.export_edl:
        export_edl(args.input, decisions, total_duration, args.export_edl, fmt)
        return

    # Aplicar edições
    output = args.output or "render/rascunho.mp4"
    apply_with_ffmpeg(args.input, decisions, total_duration, output, fmt)


if __name__ == "__main__":
    main()
