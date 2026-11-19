#!/usr/bin/env python3
"""
Valida storyboard.json antes de enviar para o pipeline de produção.
Detecta erros comuns que causaram problemas na produção do Curso 01.

Uso:
  python scripts/validate-storyboard.py --spec storyboard.json
  python scripts/validate-storyboard.py --spec storyboard.json --transcript transcript/transcript.json
  python scripts/validate-storyboard.py --spec storyboard.json --video-spec video-spec.json --clips-dir clips/
"""

import argparse
import json
import sys
from pathlib import Path


# Campos obrigatórios em cada shot
REQUIRED_FIELDS = ["id", "secao", "start", "end", "duracao", "vo", "cena", "keyframe"]

# Nomes errados comuns → nome correto
FIELD_ALIASES = {
    "fala": "vo",
    "falas": "vo",
    "narracao": "vo",
    "narração": "vo",
    "texto": "vo",
    "text": "vo",
    "duration": "duracao",
    "section": "secao",
    "scene": "cena",
}

# Duração nativa dos clips Kling
CLIP_NATIVE_DURATION = 5.0

# Threshold para recomendar extension
EXTENSION_THRESHOLD = 7.0


class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, msg):
        self.errors.append(f"❌ ERROR: {msg}")

    def warning(self, msg):
        self.warnings.append(f"⚠️  WARNING: {msg}")

    def info_msg(self, msg):
        self.info.append(f"ℹ️  {msg}")

    def print_report(self):
        print("\n" + "=" * 60)
        print("VALIDAÇÃO DO STORYBOARD")
        print("=" * 60)

        if self.info:
            print("\n--- Info ---")
            for m in self.info:
                print(f"  {m}")

        if self.warnings:
            print("\n--- Warnings ---")
            for m in self.warnings:
                print(f"  {m}")

        if self.errors:
            print("\n--- Errors ---")
            for m in self.errors:
                print(f"  {m}")

        print("\n" + "-" * 60)
        print(f"Resultado: {len(self.errors)} erros, {len(self.warnings)} warnings")

        if self.errors:
            print("🔴 FALHOU — corrija os erros antes de prosseguir")
            return False
        elif self.warnings:
            print("🟡 OK COM WARNINGS — revise antes de prosseguir")
            return True
        else:
            print("🟢 VÁLIDO — pode prosseguir com o pipeline")
            return True


def validate_storyboard(spec_path: str, transcript_path: str = None,
                        video_spec_path: str = None, clips_dir: str = None):
    result = ValidationResult()

    # ── Carregar storyboard ──
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            sb = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        result.error(f"Não consegui ler {spec_path}: {e}")
        result.print_report()
        return False

    shots = sb.get("shots", [])
    if not shots:
        result.error("storyboard.json não tem shots")
        result.print_report()
        return False

    result.info_msg(f"Storyboard: {len(shots)} shots")

    # ── Validar style_reference ──
    if not sb.get("style_reference"):
        result.warning("Falta style_reference no root do storyboard")

    # ── Validar characters ──
    characters = sb.get("characters", {})
    if characters:
        spec_dir = Path(spec_path).parent
        for char_name, char_path in characters.items():
            resolved = spec_dir / char_path
            if not resolved.exists():
                # Tentar a partir do diretório do cliente
                parts = spec_dir.parts
                try:
                    # Subir até clientes/{slug}/
                    client_idx = parts.index("clientes") + 2
                    client_dir = Path(*parts[:client_idx])
                    alt_resolved = client_dir / char_path
                    if alt_resolved.exists():
                        result.warning(
                            f"Character '{char_name}': path '{char_path}' resolve "
                            f"relativo ao cliente, não ao storyboard. "
                            f"Funciona, mas considere usar path relativo ao storyboard."
                        )
                    else:
                        result.error(
                            f"Character '{char_name}': arquivo não encontrado em "
                            f"'{resolved}' nem em '{alt_resolved}'"
                        )
                except (ValueError, IndexError):
                    result.error(
                        f"Character '{char_name}': arquivo não encontrado: '{resolved}'"
                    )
    else:
        result.info_msg("Sem characters definidos")

    # ── Validar cada shot ──
    seen_ids = set()
    total_duration = 0
    needs_extension = []

    for i, shot in enumerate(shots):
        sid = shot.get("id", f"(index {i})")
        prefix = f"Shot {sid}"

        # ID único
        if sid in seen_ids:
            result.error(f"{prefix}: ID duplicado")
        seen_ids.add(sid)

        # Campos obrigatórios
        for field in REQUIRED_FIELDS:
            if field not in shot or shot[field] is None or shot[field] == "":
                result.error(f"{prefix}: campo obrigatório '{field}' ausente ou vazio")

        # Campos com nomes errados
        for wrong_name, correct_name in FIELD_ALIASES.items():
            if wrong_name in shot:
                result.error(
                    f"{prefix}: usa '{wrong_name}' — renomear para '{correct_name}'"
                )

        # Validar timing
        start = shot.get("start", 0)
        end = shot.get("end", 0)
        duracao = shot.get("duracao")

        if end <= start:
            result.error(f"{prefix}: end ({end}) <= start ({start})")

        if duracao is not None:
            expected = round(end - start, 2)
            if abs(duracao - expected) > 0.05:
                result.error(
                    f"{prefix}: duracao={duracao} mas end-start={expected} "
                    f"(diferença: {abs(duracao - expected):.2f}s)"
                )
            total_duration += duracao

            # Verificar se precisa extension
            if duracao > EXTENSION_THRESHOLD:
                needs_extension.append((sid, duracao))
            elif duracao > CLIP_NATIVE_DURATION:
                result.info_msg(
                    f"{prefix}: duracao={duracao:.1f}s > 5s — "
                    f"DaVinci pode ajustar velocidade ({duracao/5*100:.0f}%)"
                )

        # Validar keyframe não vazio e com tamanho razoável
        keyframe = shot.get("keyframe", "")
        if len(keyframe) < 30:
            result.warning(f"{prefix}: keyframe muito curto ({len(keyframe)} chars) — descreva a composição visual completa")

        # Validar vo
        vo = shot.get("vo", "")
        if not vo:
            result.warning(f"{prefix}: vo vazio — cena muda?")

        # Validar personagem referencia characters
        personagem = shot.get("personagem")
        if personagem and personagem not in characters:
            result.warning(f"{prefix}: personagem '{personagem}' não está no dict characters")

    # ── Validar sequência de IDs ──
    ids = [s.get("id") for s in shots]
    expected_ids = list(range(1, len(shots) + 1))
    if ids != expected_ids:
        result.warning(f"IDs não são sequenciais 1..{len(shots)}: {ids[:5]}...{ids[-3:]}")

    # ── Validar continuidade de timing ──
    for i in range(1, len(shots)):
        prev_end = shots[i - 1].get("end", 0)
        curr_start = shots[i].get("start", 0)
        gap = abs(curr_start - prev_end)
        if gap > 0.1:
            result.warning(
                f"Shot {shots[i].get('id')}: gap de {gap:.2f}s entre "
                f"end do shot anterior ({prev_end:.2f}) e start ({curr_start:.2f})"
            )

    # ── Validar total_duration ──
    sb_total = sb.get("total_duration")
    if sb_total:
        if abs(sb_total - total_duration) > 0.5:
            result.warning(
                f"total_duration no root ({sb_total:.1f}s) difere da soma dos shots "
                f"({total_duration:.1f}s)"
            )
    else:
        result.warning("Falta total_duration no root do storyboard")

    result.info_msg(f"Duração total: {total_duration:.1f}s ({total_duration/60:.1f}min)")

    # ── Extensions necessárias ──
    if needs_extension:
        result.warning(
            f"{len(needs_extension)} shots precisam de extension (>{EXTENSION_THRESHOLD}s): "
            f"{[f'shot {s[0]} ({s[1]:.1f}s)' for s in needs_extension]}"
        )

    # ── Cruzar com transcript ──
    if transcript_path:
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = json.load(f)
            segments = transcript.get("segments", transcript if isinstance(transcript, list) else [])
            if segments:
                t_duration = max(s.get("end", 0) for s in segments)
                result.info_msg(f"Transcript: {len(segments)} segmentos, {t_duration:.1f}s")
                if abs(total_duration - t_duration) > 5:
                    result.warning(
                        f"Duração do storyboard ({total_duration:.1f}s) difere do "
                        f"transcript ({t_duration:.1f}s) em {abs(total_duration - t_duration):.1f}s"
                    )
        except Exception as e:
            result.warning(f"Não consegui ler transcript: {e}")

    # ── Cruzar com video-spec ──
    if video_spec_path:
        try:
            with open(video_spec_path, 'r', encoding='utf-8') as f:
                vs = json.load(f)
            jobs = vs.get("jobs", [])
            result.info_msg(f"Video-spec: {len(jobs)} jobs")

            if len(jobs) != len(shots):
                result.warning(
                    f"video-spec tem {len(jobs)} jobs mas storyboard tem {len(shots)} shots"
                )

            # Verificar imagens duplicadas em jobs diferentes
            seen_images = {}
            for job in jobs:
                img = job.get("image", "")
                if img in seen_images:
                    result.warning(
                        f"Jobs '{seen_images[img]}' e '{job['id']}' usam mesma imagem '{img}' — "
                        f"extension clips precisam de imagens DIFERENTES (gerar via Gemini)"
                    )
                seen_images[img] = job["id"]
        except Exception as e:
            result.warning(f"Não consegui ler video-spec: {e}")

    # ── Verificar clips existentes ──
    if clips_dir:
        clips_path = Path(clips_dir)
        if clips_path.exists():
            existing = set(f.stem for f in clips_path.glob("*.mp4"))
            for shot in shots:
                sid = shot.get("id")
                clip_name = f"clip_{sid:02d}"
                shot_name = f"shot_{sid:02d}"
                if clip_name not in existing and shot_name not in existing:
                    result.warning(f"Shot {sid}: clip não encontrado ({clip_name}.mp4 ou {shot_name}.mp4)")

            # Verificar extensions
            for sid, dur in needs_extension:
                ext_name = f"clip_{sid:02d}_ext"
                shot_ext = f"shot_{sid:02d}_ext"
                if ext_name not in existing and shot_ext not in existing:
                    result.warning(f"Shot {sid} ({dur:.1f}s): extension clip não encontrado")

    # ── Resultado ──
    return result.print_report()


def main():
    parser = argparse.ArgumentParser(description="Valida storyboard.json")
    parser.add_argument("--spec", required=True, help="Caminho para storyboard.json")
    parser.add_argument("--transcript", help="Caminho para transcript.json (opcional)")
    parser.add_argument("--video-spec", help="Caminho para video-spec.json (opcional)")
    parser.add_argument("--clips-dir", help="Pasta com clips .mp4 (opcional)")
    args = parser.parse_args()

    ok = validate_storyboard(args.spec, args.transcript, args.video_spec, args.clips_dir)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
