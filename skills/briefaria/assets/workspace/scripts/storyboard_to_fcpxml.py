#!/usr/bin/env python3
"""
Gera FCPXML a partir de storyboard.json para DaVinci Resolve.

Dois modos:
  --clips-dir: usa clips .mp4 gerados via fal.ai (extensions para shots longos)
  Sem --clips-dir: usa imagens stills com duração exata + voiceover como connected clip

Flags para Veo (clips com áudio embutido):
  --clip-duration 8    - Duração nativa dos clips (5 para Kling, 8 para Veo)
  --has-clip-audio     - Clips contêm áudio (Veo gera SFX ambiente automaticamente)
  --skip-sfx           - Pula inclusão de SFX separados na timeline

Uso:
  # Com stills (animatic)
  python scripts/storyboard_to_fcpxml.py \
    --storyboard storyboard.json --images-dir imagens/ --output animatic.fcpxml

  # Com clips Kling (5s, sem áudio)
  python scripts/storyboard_to_fcpxml.py \
    --storyboard storyboard.json --clips-dir clips/ --output timeline.fcpxml

  # Com clips Veo (8s, com áudio)
  python scripts/storyboard_to_fcpxml.py \
    --storyboard storyboard.json --clips-dir clips/ \
    --clip-duration 8 --has-clip-audio --skip-sfx \
    --output timeline.fcpxml

  # Com voice-over e base-path para Mac
  python scripts/storyboard_to_fcpxml.py \
    --storyboard storyboard.json --clips-dir clips/ \
    --voiceover audio/voice-over.wav \
    --sfx-spec sfx-spec.json --sfx-dir sfx/ \
    --base-path /caminho/do/workspace \
    --output timeline.fcpxml
"""

import argparse
import json
import re
import sys
from pathlib import Path


FPS = 24
FRAME_DUR = "100/2400s"  # 1 frame = 100/2400s a 24fps
DEFAULT_CLIP_DURATION = 5.0  # Kling=5s, Veo=8s (configuravel via --clip-duration)

# Dimensoes por formato
FORMATO_DIMS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1":  (1080, 1080),
}


def seconds_to_rational(seconds: float) -> str:
    """Converte segundos para formato racional FCPXML (frames * 100 / 2400)."""
    frames = round(seconds * FPS)
    return f"{frames * 100}/2400s"


def generate_fcpxml(storyboard_path: str, output_path: str,
                    images_dir: str = None, clips_dir: str = None,
                    voiceover_path: str = None,
                    sfx_spec: str = None, sfx_dir: str = None,
                    base_path: str = None,
                    clip_duration: float = None,
                    has_clip_audio: bool = False,
                    skip_sfx: bool = False,
                    formato: str = None):
    # Duração nativa dos clips: configurável para suportar Veo (8s) vs Kling (5s)
    native_dur = clip_duration if clip_duration else DEFAULT_CLIP_DURATION

    with open(storyboard_path, 'r', encoding='utf-8') as f:
        sb = json.load(f)

    # Resolver formato: flag > status.json do mesmo diretorio > default 16:9
    if not formato:
        status_path = Path(storyboard_path).parent / "status.json"
        if status_path.exists():
            with open(status_path, 'r', encoding='utf-8') as f:
                status = json.load(f)
            formato = status.get("formato", "16:9")
        else:
            formato = "16:9"
    width, height = FORMATO_DIMS.get(formato, (1920, 1080))

    shots = sb.get("shots", [])
    total_duration = sb.get("total_duration", 0)
    use_clips = clips_dir is not None

    # Carregar SFX spec se fornecido (pular se --skip-sfx)
    sfx_list = []
    if sfx_spec and not skip_sfx:
        with open(sfx_spec, 'r', encoding='utf-8') as f:
            sfx_list = json.load(f)

    # Resolver paths
    sb_dir = Path(storyboard_path).parent.resolve()
    media_path = Path(clips_dir).resolve() if use_clips else Path(images_dir).resolve()
    sfx_path = Path(sfx_dir).resolve() if sfx_dir else None

    # Remap de caminhos sandbox → caminho real no Mac
    if base_path:
        sandbox_mount = None
        resolved_str = str(sb_dir)
        m = re.match(r'(/sessions/[^/]+/mnt/[^/]+)', resolved_str)
        if m:
            sandbox_mount = m.group(1)

        def remap(p) -> str:
            s = str(p)
            if sandbox_mount and sandbox_mount in s:
                return s.replace(sandbox_mount, base_path.rstrip('/'))
            return s
    else:
        def remap(p) -> str:
            return str(p)

    # Voice-over
    if voiceover_path:
        vo_abs = (sb_dir / voiceover_path).resolve()
        vo_url = f"file://{remap(vo_abs)}"
    else:
        vo_url = None

    # Calcular duração total da timeline (em frames para evitar rounding errors)
    if total_duration > 0:
        timeline_dur = total_duration
    else:
        timeline_dur = sum(s.get("duracao", 0) for s in shots)

    timeline_dur_frames = sum(round(s.get("duracao", 0) * FPS) for s in shots)
    timeline_dur_rat = f"{timeline_dur_frames * 100}/2400s"
    project_name = sb_dir.name

    # ─── Detectar extension clips disponíveis ───
    ext_clips = set()
    if use_clips:
        for f in media_path.iterdir():
            if f.name.endswith('_ext.mp4'):
                ext_clips.add(f.name.replace('.mp4', ''))

    # ─── Resources (assets) ───
    resources = [
        f'        <format id="r1" name="FFVideoFormat1080p{FPS}" '
        f'frameDuration="{FRAME_DUR}" width="{width}" height="{height}"/>'
    ]

    for shot in shots:
        sid = shot["id"]

        if use_clips:
            # Clip principal (5s nativo) — tenta clip_XX.mp4 e shot_XX.mp4
            clip_file = media_path / f"clip_{sid:02d}.mp4"
            if not clip_file.exists():
                alt = media_path / f"shot_{sid:02d}.mp4"
                if alt.exists():
                    clip_file = alt
            file_url = f"file://{remap(clip_file)}"
            has_audio_val = "1" if has_clip_audio else "0"
            asset_dur = seconds_to_rational(native_dur)
            resources.append(
                f'        <asset id="clip_{sid:02d}" name="clip_{sid:02d}" '
                f'src="{file_url}" start="0s" duration="{asset_dur}" '
                f'hasVideo="1" hasAudio="{has_audio_val}" format="r1"/>'
            )

            # Extension clip se existir
            ext_name = f"clip_{sid:02d}_ext"
            if ext_name in ext_clips:
                ext_file = media_path / f"{ext_name}.mp4"
                ext_url = f"file://{remap(ext_file)}"
                resources.append(
                    f'        <asset id="{ext_name}" name="{ext_name}" '
                    f'src="{ext_url}" start="0s" duration="{asset_dur}" '
                    f'hasVideo="1" hasAudio="{has_audio_val}" format="r1"/>'
                )
        else:
            img_file = media_path / f"shot_{sid:02d}.png"
            file_url = f"file://{remap(img_file)}"
            resources.append(
                f'        <asset id="shot_{sid:02d}" name="shot_{sid:02d}" '
                f'src="{file_url}" start="0s" duration="0s" '
                f'hasVideo="1" hasAudio="0" format="r1"/>'
            )

    # Voice-over asset
    if vo_url:
        vo_dur_rat = timeline_dur_rat
        resources.append(
            f'        <asset id="voiceover" name="voiceover" '
            f'src="{vo_url}" start="0/2400s" duration="{vo_dur_rat}" '
            f'hasAudio="1" audioSources="1" audioChannels="2"/>'
        )

    # SFX assets
    for sfx in sfx_list:
        sfx_id = sfx["id"]
        sfx_file = sfx_path / f"{sfx_id}.mp3" if sfx_path else None
        if sfx_file and sfx_file.exists():
            sfx_dur = seconds_to_rational(sfx.get("duration", 5))
            resources.append(
                f'        <asset id="{sfx_id}" name="{sfx_id}" '
                f'src="file://{remap(sfx_file)}" start="0/2400s" duration="{sfx_dur}" '
                f'hasAudio="1" audioSources="1" audioChannels="1"/>'
            )

    # Indexar SFX por shot
    sfx_by_shot = {}
    for sfx in sfx_list:
        shot_id = sfx.get("shot")
        if shot_id:
            sfx_by_shot.setdefault(shot_id, []).append(sfx)

    # ─── Spine (timeline principal) ───
    spine_clips = []
    offset_frames = 0  # Acumular em frames (inteiros) para evitar rounding errors
    ext_count = 0

    def frames_to_rational(frames: int) -> str:
        return f"{frames * 100}/2400s"

    for shot in shots:
        sid = shot["id"]
        dur = shot.get("duracao", 5)
        dur_frames = round(dur * FPS)
        offset_rat = frames_to_rational(offset_frames)
        secao = shot.get("secao", "")
        ext_name = f"clip_{sid:02d}_ext"
        has_ext = ext_name in ext_clips

        if use_clips and dur > native_dur and has_ext:
            # ── Shot com extensão: clip principal (5s) + extension (restante) ──
            native_frames = round(native_dur * FPS)
            clip_dur_rat = frames_to_rational(native_frames)
            ext_frames = dur_frames - native_frames
            ext_dur_rat = frames_to_rational(ext_frames)
            ext_offset_rat = frames_to_rational(offset_frames + native_frames)

            # SFX ficam no clip principal
            shot_sfx = sfx_by_shot.get(sid, [])
            inner = ""
            for sfx in shot_sfx:
                sfx_id = sfx["id"]
                sfx_dur = seconds_to_rational(sfx.get("duration", dur))
                inner += (
                    f'\n                            <asset-clip ref="{sfx_id}" '
                    f'lane="-1" name="{sfx_id}" '
                    f'offset="0/2400s" duration="{sfx_dur}" tcFormat="NDF"/>'
                )

            if inner:
                spine_clips.append(
                    f'                        <asset-clip ref="clip_{sid:02d}" '
                    f'name="Shot {sid:02d}a — {secao}" '
                    f'offset="{offset_rat}" duration="{clip_dur_rat}" tcFormat="NDF">'
                    f'{inner}\n'
                    f'                        </asset-clip>'
                )
            else:
                spine_clips.append(
                    f'                        <asset-clip ref="clip_{sid:02d}" '
                    f'name="Shot {sid:02d}a — {secao}" '
                    f'offset="{offset_rat}" duration="{clip_dur_rat}" tcFormat="NDF"/>'
                )

            # Extension clip
            spine_clips.append(
                f'                        <asset-clip ref="{ext_name}" '
                f'name="Shot {sid:02d}b — {secao}" '
                f'offset="{ext_offset_rat}" duration="{ext_dur_rat}" tcFormat="NDF"/>'
            )
            ext_count += 1

        elif use_clips and dur > native_dur:
            # ── Shot > 5s sem extensão: usar clip de 5s com speed change ──
            # DaVinci vai esticar o clip. Registramos a duração real.
            dur_rat = frames_to_rational(dur_frames)
            shot_sfx = sfx_by_shot.get(sid, [])
            inner = ""
            for sfx in shot_sfx:
                sfx_id = sfx["id"]
                sfx_dur = seconds_to_rational(sfx.get("duration", dur))
                inner += (
                    f'\n                            <asset-clip ref="{sfx_id}" '
                    f'lane="-1" name="{sfx_id}" '
                    f'offset="0/2400s" duration="{sfx_dur}" tcFormat="NDF"/>'
                )

            if inner:
                spine_clips.append(
                    f'                        <asset-clip ref="clip_{sid:02d}" '
                    f'name="Shot {sid:02d} — {secao}" '
                    f'offset="{offset_rat}" duration="{dur_rat}" tcFormat="NDF">'
                    f'{inner}\n'
                    f'                        </asset-clip>'
                )
            else:
                spine_clips.append(
                    f'                        <asset-clip ref="clip_{sid:02d}" '
                    f'name="Shot {sid:02d} — {secao}" '
                    f'offset="{offset_rat}" duration="{dur_rat}" tcFormat="NDF"/>'
                )

        else:
            # ── Shot ≤ 5s: clip normal, trim direto ──
            dur_rat = frames_to_rational(dur_frames)
            shot_sfx = sfx_by_shot.get(sid, [])
            inner = ""
            for sfx in shot_sfx:
                sfx_id = sfx["id"]
                sfx_dur = seconds_to_rational(sfx.get("duration", dur))
                inner += (
                    f'\n                            <asset-clip ref="{sfx_id}" '
                    f'lane="-1" name="{sfx_id}" '
                    f'offset="0/2400s" duration="{sfx_dur}" tcFormat="NDF"/>'
                )

            if use_clips:
                ref = f"clip_{sid:02d}"
            else:
                ref = f"shot_{sid:02d}"

            if inner:
                spine_clips.append(
                    f'                        <asset-clip ref="{ref}" '
                    f'name="Shot {sid:02d} — {secao}" '
                    f'offset="{offset_rat}" duration="{dur_rat}" tcFormat="NDF">'
                    f'{inner}\n'
                    f'                        </asset-clip>'
                )
            else:
                spine_clips.append(
                    f'                        <asset-clip ref="{ref}" '
                    f'name="Shot {sid:02d} — {secao}" '
                    f'offset="{offset_rat}" duration="{dur_rat}" tcFormat="NDF"/>'
                )

        offset_frames += dur_frames

    # ── Voice-over como connected clip no primeiro shot (lane -2 = abaixo de tudo) ──
    if vo_url:
        # Reescrever primeiro clip para incluir voiceover como connected clip
        first_shot = shots[0]
        sid = first_shot["id"]
        dur = first_shot.get("duracao", 5)
        secao = first_shot.get("secao", "")

        if use_clips:
            ref = f"clip_{sid:02d}"
        else:
            ref = f"shot_{sid:02d}"

        # Determinar duração do primeiro elemento no spine
        ext_name = f"clip_{sid:02d}_ext"
        has_ext = ext_name in ext_clips
        first_dur_frames = round(dur * FPS)
        if use_clips and dur > native_dur and has_ext:
            first_dur_rat = frames_to_rational(round(native_dur * FPS))
            clip_name = f"Shot {sid:02d}a — {secao}"
        else:
            first_dur_rat = frames_to_rational(first_dur_frames)
            clip_name = f"Shot {sid:02d} — {secao}"

        # Extrair connected clips existentes (SFX) do primeiro spine clip
        existing_inner = ""
        first_clip_str = spine_clips[0]
        if ">" in first_clip_str and "</asset-clip>" in first_clip_str:
            # Já tem connected clips — extrair o inner
            start_idx = first_clip_str.index(">") + 1
            end_idx = first_clip_str.rindex("</asset-clip>")
            existing_inner = first_clip_str[start_idx:end_idx].rstrip()

        vo_connected = (
            f'\n                            <asset-clip ref="voiceover" '
            f'lane="-2" name="Voice-Over" '
            f'offset="0/2400s" duration="{timeline_dur_rat}" '
            f'tcFormat="NDF"/>'
        )

        spine_clips[0] = (
            f'                        <asset-clip ref="{ref}" '
            f'name="{clip_name}" '
            f'offset="0/2400s" duration="{first_dur_rat}" tcFormat="NDF">'
            f'{existing_inner}'
            f'{vo_connected}\n'
            f'                        </asset-clip>'
        )

    # ─── Montar XML ───
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
    <resources>
{chr(10).join(resources)}
    </resources>
    <library>
        <event name="{project_name}">
            <project name="{project_name} — {len(shots)} shots">
                <sequence format="r1" duration="{timeline_dur_rat}" tcStart="0/2400s" tcFormat="NDF">
                    <spine>
{chr(10).join(spine_clips)}
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>
"""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(xml, encoding='utf-8')

    print(f"FCPXML gerado: {output}")
    print(f"  Shots: {len(shots)}")
    print(f"  Duração: {timeline_dur:.1f}s")
    print(f"  Formato: {formato} ({width}x{height})")
    print(f"  Voice-over: {'sim' if vo_url else 'não'}")
    mode = "clips" if use_clips else "stills"
    print(f"  Modo: {mode}")
    print(f"  Media: {media_path}")
    if ext_count:
        print(f"  Extensions: {ext_count} clips de extensão")
    if sfx_list:
        print(f"  SFX: {len(sfx_list)} efeitos sonoros")


def main():
    parser = argparse.ArgumentParser(description="Gera FCPXML a partir de storyboard.json")
    parser.add_argument("--storyboard", required=True, help="Caminho para storyboard.json")
    parser.add_argument("--images-dir", help="Pasta com shot_XX.png (modo stills)")
    parser.add_argument("--clips-dir", help="Pasta com clip_XX.mp4 (modo clips)")
    parser.add_argument("--voiceover", help="Caminho para voice-over (relativo ao storyboard)")
    parser.add_argument("--sfx-spec", help="Caminho para sfx-spec.json")
    parser.add_argument("--sfx-dir", help="Pasta com SFX .mp3")
    parser.add_argument("--base-path", help="Caminho real no Mac para remapear paths do sandbox")
    parser.add_argument("--clip-duration", type=float, default=None,
                        help="Duração nativa dos clips em segundos (5 para Kling, 8 para Veo). Default: 5")
    parser.add_argument("--has-clip-audio", action="store_true",
                        help="Clips contêm áudio embutido (Veo gera SFX ambiente)")
    parser.add_argument("--skip-sfx", action="store_true",
                        help="Pular inclusão de SFX separados (quando clips já têm áudio)")
    parser.add_argument("--formato", choices=["16:9", "9:16", "1:1"], default=None,
                        help="Formato do video (default: le de status.json ou 16:9)")
    parser.add_argument("--output", required=True, help="Caminho de saída .fcpxml")
    args = parser.parse_args()

    if not args.images_dir and not args.clips_dir:
        parser.error("Precisa de --images-dir ou --clips-dir")

    # Detectar sandbox e avisar se --base-path não foi fornecido
    sb_resolved = str(Path(args.storyboard).resolve())
    is_sandbox = bool(re.match(r'/sessions/[^/]+/mnt/', sb_resolved))
    if is_sandbox and not args.base_path:
        print("⚠️  AVISO: Executando em sandbox sem --base-path!")
        print("   O FCPXML vai conter paths /sessions/... que não existem no Mac.")
        print("   Use --base-path /caminho/do/workspace (ou equivalente)")
        print()
        resp = input("Continuar mesmo assim? [s/N] ").strip().lower()
        if resp != 's':
            print("Abortado. Use --base-path para remapear os paths.")
            sys.exit(1)

    generate_fcpxml(args.storyboard, args.output,
                    images_dir=args.images_dir, clips_dir=args.clips_dir,
                    voiceover_path=args.voiceover,
                    sfx_spec=args.sfx_spec, sfx_dir=args.sfx_dir,
                    base_path=args.base_path,
                    clip_duration=args.clip_duration,
                    has_clip_audio=args.has_clip_audio,
                    skip_sfx=args.skip_sfx,
                    formato=args.formato)


if __name__ == "__main__":
    main()
