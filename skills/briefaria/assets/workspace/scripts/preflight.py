#!/usr/bin/env python3
"""
Preflight check — valida pré-requisitos antes de executar cada fase do pipeline.

Lê o status.json do projeto, identifica a próxima fase pendente, e verifica
se todos os arquivos e condições necessárias estão satisfeitos.

Uso:
  # Verifica próxima fase automaticamente
  python scripts/preflight.py --project clientes/slug/producao/_ativo

  # Verifica fase específica
  python scripts/preflight.py --project clientes/slug/producao/_ativo --fase imagens

  # Mostra todas as fases e seus status
  python scripts/preflight.py --project clientes/slug/producao/_ativo --all

Retorna exit code 0 se OK, 1 se há erros bloqueantes.
"""

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent


# ── Pipelines por tipo de projeto ──────────────────────────────────────────

PIPELINES = {
    "video": ["roteiro", "voiceover", "transcrever", "storyboard", "imagens", "clips", "sfx", "fcpxml", "davinci"],
    "video-dialogo": ["roteiro", "storyboard", "imagens", "clips", "fcpxml", "davinci"],
    "gravado": ["gravar", "transcrever", "editar", "assets", "compor", "fragmentar", "publicar"],
    "carrossel": ["roteiro", "imagens", "publicar"],
    "marketing": ["fundacao", "estrategia", "conteudo", "distribuicao", "analise"],
}


# ── Checks por fase ───────────────────────────────────────────────────────

def check_roteiro(proj: Path, status: dict) -> tuple[list, list]:
    """Pré: branding.json existe. Pós: roteiro.md ou roteiro.json existe e não está vazio."""
    errors, warnings = [], []
    client_dir = proj.parent.parent  # clientes/{slug}/
    branding = client_dir / "branding.json"
    if not branding.exists():
        errors.append(f"branding.json não encontrado em {client_dir}")
    elif "???" in branding.read_text(encoding="utf-8", errors="ignore"):
        errors.append(f"branding.json em {client_dir} ainda tem campos do template (???)")

    brief = proj / "brief.md"
    if not brief.exists():
        warnings.append("brief.md não existe — o roteiro pode ficar genérico")

    # Se fase já done, verificar output
    if status.get("roteiro") == "done":
        roteiro = proj / "roteiro.md"
        roteiro_json = proj / "roteiro.json"
        if not roteiro.exists() and not roteiro_json.exists():
            errors.append("Fase 'roteiro' marcada como done mas roteiro.md/roteiro.json não existe")
        else:
            output = roteiro if roteiro.exists() else roteiro_json
            if output.stat().st_size < 50:
                warnings.append(f"{output.name} parece muito curto (< 50 bytes)")

    return errors, warnings


def check_voiceover(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    if status.get("roteiro") != "done":
        errors.append("Fase 'roteiro' precisa estar done antes de voiceover")

    roteiro = proj / "roteiro.md"
    if not roteiro.exists():
        errors.append("roteiro.md não encontrado")

    # Se já done, verificar output
    if status.get("voiceover") == "done":
        audio_dir = proj / "audio"
        vo_files = list(audio_dir.glob("voice-over.*")) if audio_dir.exists() else []
        if not vo_files:
            # Verificar recordings como alternativa (gravação manual)
            rec_dir = proj / "recordings"
            rec_files = list(rec_dir.glob("*.*")) if rec_dir.exists() else []
            if not rec_files:
                errors.append("Fase 'voiceover' done mas nenhum áudio encontrado em audio/ ou recordings/")

    return errors, warnings


def check_transcrever(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    if status.get("voiceover") != "done":
        errors.append("Fase 'voiceover' precisa estar done antes de transcrever")

    # Verificar que há áudio para transcrever
    audio_dir = proj / "audio"
    rec_dir = proj / "recordings"
    has_audio = False
    for d in [audio_dir, rec_dir]:
        if d.exists():
            for ext in ["*.wav", "*.mp3", "*.m4a", "*.mkv", "*.mov", "*.mp4"]:
                if list(d.glob(ext)):
                    has_audio = True
                    break
    if not has_audio:
        errors.append("Nenhum áudio/vídeo encontrado em audio/ ou recordings/")

    # Se já done, verificar output
    if status.get("transcrever") == "done":
        transcript_dir = proj / "transcript"
        if not transcript_dir.exists():
            errors.append("Fase 'transcrever' done mas pasta transcript/ não existe")
        else:
            json_files = list(transcript_dir.glob("*.json"))
            txt_files = list(transcript_dir.glob("*.txt"))
            if not json_files and not txt_files:
                errors.append("transcript/ existe mas está vazia — sem .json nem .txt")

    return errors, warnings


def check_storyboard(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    if status.get("transcrever") != "done":
        errors.append("Fase 'transcrever' precisa estar done antes de storyboard")

    transcript_dir = proj / "transcript"
    if not transcript_dir.exists() or not list(transcript_dir.glob("*")):
        errors.append("Pasta transcript/ vazia ou inexistente")

    client_dir = proj.parent.parent
    branding = client_dir / "branding.json"
    if not branding.exists():
        warnings.append("branding.json não encontrado — storyboard sem referência visual")
    elif "???" in branding.read_text(encoding="utf-8", errors="ignore"):
        warnings.append("branding.json com campos do template (???) — storyboard sem referência visual")

    # Se já done, verificar output
    if status.get("storyboard") == "done":
        sb = proj / "storyboard.json"
        if not sb.exists():
            errors.append("Fase 'storyboard' done mas storyboard.json não existe")
        else:
            # Validação básica (o validate-storyboard.py faz a completa)
            try:
                with open(sb) as f:
                    data = json.load(f)
                shots = data.get("shots", [])
                if len(shots) == 0:
                    errors.append("storyboard.json tem 0 shots")
                else:
                    # Verificar campos obrigatórios do primeiro shot
                    required = ["id", "secao", "start", "end", "duracao", "vo", "cena", "keyframe"]
                    missing = [k for k in required if k not in shots[0]]
                    if missing:
                        errors.append(f"Shot 1 sem campos obrigatórios: {missing}")
            except json.JSONDecodeError as e:
                errors.append(f"storyboard.json inválido: {e}")

    return errors, warnings


def check_imagens(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    roteiro_path = proj / "roteiro.json"
    if roteiro_path.exists():
        if status.get("roteiro") != "done":
            errors.append("Fase 'roteiro' precisa estar done antes de imagens")
            return errors, warnings

        try:
            with open(roteiro_path) as f:
                roteiro = json.load(f)
            slides = roteiro.get("slides", [])
            if not slides:
                errors.append("roteiro.json tem 0 slides")
                return errors, warnings
            missing_assets = [str(slide.get("id", "?")) for slide in slides if not slide.get("asset")]
            if missing_assets:
                errors.append(f"Slides sem campo asset: {', '.join(missing_assets)}")
        except json.JSONDecodeError as e:
            errors.append(f"roteiro.json inválido: {e}")
            return errors, warnings

        if status.get("imagens") == "done":
            img_dir = proj / "imagens"
            pngs = sorted(img_dir.glob("*.png")) if img_dir.exists() else []
            if len(pngs) < len(slides):
                warnings.append(f"Esperado {len(slides)} imagens, encontrado {len(pngs)}")
        return errors, warnings

    if status.get("storyboard") != "done":
        errors.append("Fase 'storyboard' precisa estar done antes de imagens")

    sb_path = proj / "storyboard.json"
    if not sb_path.exists():
        errors.append("storyboard.json não encontrado")
        return errors, warnings

    try:
        with open(sb_path) as f:
            sb = json.load(f)
        num_shots = len(sb.get("shots", []))

        # Verificar characters paths
        characters = sb.get("characters", {})
        for name, path in characters.items():
            char_path = sb_path.parent / path
            if not char_path.exists():
                # Tentar relativo ao cliente
                client_dir = proj.parent.parent
                alt_path = client_dir / path.lstrip("../../")
                if not alt_path.exists():
                    errors.append(f"Model sheet '{name}': não encontrado em {path}")
    except json.JSONDecodeError:
        errors.append("storyboard.json inválido")
        return errors, warnings

    # Se já done, verificar output
    if status.get("imagens") == "done":
        img_dir = proj / "imagens"
        if not img_dir.exists():
            errors.append("Fase 'imagens' done mas pasta imagens/ não existe")
        else:
            pngs = sorted(img_dir.glob("shot_*.png"))
            if len(pngs) < num_shots:
                warnings.append(f"Esperado {num_shots} imagens, encontrado {len(pngs)}")

    return errors, warnings


def check_clips(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    if status.get("imagens") != "done":
        errors.append("Fase 'imagens' precisa estar done antes de clips")

    img_dir = proj / "imagens"
    if not img_dir.exists() or not list(img_dir.glob("shot_*.png")):
        errors.append("Nenhuma imagem shot_XX.png encontrada em imagens/")

    # Verificar video-spec.json
    vspec = proj / "video-spec.json"
    if not vspec.exists():
        warnings.append("video-spec.json não existe — precisa ser criado antes de gerar clips")

    # Verificar extensions necessárias
    sb_path = proj / "storyboard.json"
    if sb_path.exists():
        try:
            with open(sb_path) as f:
                sb = json.load(f)
            long_shots = [s for s in sb.get("shots", []) if s.get("duracao", 0) > 7.0]
            if long_shots:
                ext_dir = proj / "imagens-ext"
                if not ext_dir.exists() and status.get("clips") != "done":
                    warnings.append(
                        f"{len(long_shots)} shots > 7s precisam de extension images. "
                        f"Gerar imagens novas com ângulos diferentes antes dos clips."
                    )
        except json.JSONDecodeError:
            pass

    # Se já done, verificar output
    if status.get("clips") == "done":
        clips_dir = proj / "clips"
        if not clips_dir.exists():
            errors.append("Fase 'clips' done mas pasta clips/ não existe")
        else:
            clips = sorted(clips_dir.glob("clip_*.mp4"))
            if len(clips) == 0:
                # Fallback: shot_XX.mp4
                clips = sorted(clips_dir.glob("shot_*.mp4"))
            if len(clips) == 0:
                errors.append("clips/ existe mas sem .mp4")

    return errors, warnings


def check_sfx(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []

    sfx_spec = proj / "sfx-spec.json"
    if not sfx_spec.exists():
        warnings.append("sfx-spec.json não existe — precisa ser criado para gerar SFX")

    # Se já done, verificar output
    if status.get("sfx") == "done":
        sfx_dir = proj / "sfx"
        if sfx_spec.exists():
            try:
                with open(sfx_spec) as f:
                    spec = json.load(f)
                expected = len(spec)
                actual = len(list(sfx_dir.glob("*.mp3"))) if sfx_dir.exists() else 0
                if actual < expected:
                    warnings.append(f"SFX: {actual}/{expected} gerados")
            except json.JSONDecodeError:
                pass

    return errors, warnings


def check_fcpxml(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    if status.get("clips") != "done":
        errors.append("Fase 'clips' precisa estar done antes de fcpxml")

    clips_dir = proj / "clips"
    if not clips_dir.exists() or not list(clips_dir.glob("*.mp4")):
        errors.append("Nenhum clip .mp4 encontrado em clips/")

    # Verificar voice-over para inclusão na timeline
    audio_dir = proj / "audio"
    if audio_dir.exists():
        vo_files = list(audio_dir.glob("voice-over.*"))
        if not vo_files:
            warnings.append("Nenhum voice-over.wav em audio/ — FCPXML ficará sem narração")

    # Aviso sobre base-path no sandbox
    resolved = str(proj.resolve())
    if "/sessions/" in resolved:
        warnings.append(
            "Executando em sandbox — usar --base-path no storyboard_to_fcpxml.py "
            "para remapear paths para o Mac"
        )

    # Se já done
    if status.get("fcpxml") == "done":
        fcpxml_files = list(proj.glob("*.fcpxml"))
        if not fcpxml_files:
            errors.append("Fase 'fcpxml' done mas nenhum .fcpxml encontrado")

    return errors, warnings


def check_davinci(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    if status.get("fcpxml") != "done":
        errors.append("Fase 'fcpxml' precisa estar done antes de davinci")

    fcpxml_files = list(proj.glob("*.fcpxml"))
    if not fcpxml_files:
        errors.append("Nenhum .fcpxml encontrado no projeto")

    return errors, warnings


def check_gravar(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    brief = proj / "brief.md"
    if not brief.exists():
        warnings.append("brief.md não existe — gravação sem referência de briefing")

    if status.get("gravar") == "done":
        rec_dir = proj / "recordings"
        if not rec_dir.exists() or not list(rec_dir.glob("*")):
            errors.append("Fase 'gravar' done mas recordings/ vazia ou inexistente")

    return errors, warnings


def check_editar(proj: Path, status: dict) -> tuple[list, list]:
    errors, warnings = [], []
    if status.get("transcrever") != "done":
        errors.append("Fase 'transcrever' precisa estar done antes de editar")
    return errors, warnings


def check_assets(proj: Path, status: dict) -> tuple[list, list]:
    return [], []


def check_compor(proj: Path, status: dict) -> tuple[list, list]:
    return [], []


def check_fragmentar(proj: Path, status: dict) -> tuple[list, list]:
    return [], []


def check_publicar(proj: Path, status: dict) -> tuple[list, list]:
    return [], []


# ── Mapa de checks ────────────────────────────────────────────────────────

CHECKS = {
    "roteiro": check_roteiro,
    "voiceover": check_voiceover,
    "transcrever": check_transcrever,
    "storyboard": check_storyboard,
    "imagens": check_imagens,
    "clips": check_clips,
    "sfx": check_sfx,
    "fcpxml": check_fcpxml,
    "davinci": check_davinci,
    "gravar": check_gravar,
    "editar": check_editar,
    "assets": check_assets,
    "compor": check_compor,
    "fragmentar": check_fragmentar,
    "publicar": check_publicar,
}


# ── Lógica principal ──────────────────────────────────────────────────────

def load_status(proj: Path) -> dict:
    status_path = proj / "status.json"
    if not status_path.exists():
        print(f"❌ status.json não encontrado em {proj}")
        sys.exit(1)
    with open(status_path) as f:
        status = json.load(f)
    if not isinstance(status, dict) or status.get("tipo") not in PIPELINES:
        raise ValueError("Tipo de projeto ausente ou inválido")
    phases = status.get("pipeline")
    if not isinstance(phases, dict) or not phases:
        raise ValueError("pipeline deve conter fases")
    valid = {"pending", "in_progress", "running", "blocked", "failed", "waiting", "done", "skip", "skipped"}
    for name, phase in phases.items():
        value = phase.get("status") if isinstance(phase, dict) else phase
        if not isinstance(value, str) or value not in valid:
            raise ValueError(f"Estado inválido na fase '{name}': {value!r}")
    return status


def phase_states(status: dict) -> dict:
    """Normaliza apenas para leitura; preserva metadata e formato no arquivo."""
    return {name: phase.get("status") if isinstance(phase, dict) else phase
            for name, phase in status["pipeline"].items()}


def next_pending_phase(status: dict) -> str | None:
    phases = phase_states(status)
    for phase, state in phases.items():
        if state not in {"done", "skip", "skipped"}:
            return phase
    return None


def run_check(proj: Path, fase: str, status: dict) -> tuple[list, list]:
    phases = phase_states(status)
    if fase not in phases:
        return [f"Fase '{fase}' não existe no projeto"], []
    state = phases[fase]
    if state in {"skip", "skipped"}:
        return [], []
    if state in {"blocked", "failed", "waiting"}:
        return [f"Fase '{fase}' está {state}; resolver a condição registrada no projeto"], []
    if status["tipo"] == "marketing" and fase in PIPELINES["marketing"]:
        return [], ["Estado lido; insumos e autorizações devem ser avaliados pela skill marketing-os para a tarefa solicitada"]
    check_fn = CHECKS.get(fase)
    if not check_fn:
        return [], [f"Sem checks definidos para fase '{fase}'"]
    return check_fn(proj, phases)


def print_phase_status(proj: Path, status: dict):
    """Mostra todas as fases com status e resultado do check."""
    tipo = status.get("tipo", "video")
    phases = phase_states(status)
    pipeline = phases
    total_errors = 0

    print(f"\n{'='*60}")
    print(f"Projeto: {status.get('cliente')}/{status.get('projeto')}")
    print(f"Tipo: {tipo}")
    print(f"{'='*60}\n")

    icons = {"done": "✅", "pending": "⏳", "in_progress": "🔄", "skip": "⏭️"}

    for phase in pipeline:
        phase_status = phases.get(phase, "pending")
        icon = icons.get(phase_status, "❓")
        errors, warnings = run_check(proj, phase, status)
        total_errors += len(errors)

        status_str = f"{icon} {phase:<15} [{phase_status:>11}]"
        if errors:
            status_str += f"  ❌ {len(errors)} erro(s)"
        if warnings:
            status_str += f"  ⚠️  {len(warnings)} aviso(s)"
        if not errors and not warnings:
            status_str += "  ✓"

        print(status_str)

    print()
    return total_errors


def main():
    parser = argparse.ArgumentParser(
        description="Preflight check — valida pré-requisitos de cada fase do pipeline"
    )
    parser.add_argument("--project", required=True,
                        help="Caminho do projeto (ex: clientes/slug/producao/_ativo)")
    parser.add_argument("--fase", help="Fase específica para verificar (default: próxima pendente)")
    parser.add_argument("--all", action="store_true", help="Mostra status de todas as fases")
    args = parser.parse_args()

    proj = Path(args.project).resolve()
    if proj.is_symlink():
        proj = proj.resolve()

    try:
        status = load_status(proj)
    except (ValueError, OSError) as error:
        print(f"❌ status.json inválido: {error}")
        sys.exit(1)

    if args.all:
        sys.exit(1 if print_phase_status(proj, status) else 0)

    fase = args.fase or next_pending_phase(status)
    if not fase:
        print("✅ Todas as fases registradas estão encerradas (done/skip). Outputs não revalidados nesta consulta.")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"PREFLIGHT: {fase}")
    print(f"Projeto: {status.get('cliente')}/{status.get('projeto')}")
    print(f"{'='*60}\n")

    errors, warnings = run_check(proj, fase, status)

    if warnings:
        print("--- Warnings ---")
        for w in warnings:
            print(f"  ⚠️  {w}")
        print()

    if errors:
        print("--- Erros bloqueantes ---")
        for e in errors:
            print(f"  ❌ {e}")
        print(f"\n{'-'*60}")
        print(f"🔴 PREFLIGHT FALHOU — {len(errors)} erro(s), {len(warnings)} warning(s)")
        print(f"   Corrija os erros antes de executar a fase '{fase}'")
        sys.exit(1)
    else:
        print(f"{'-'*60}")
        if status["tipo"] == "marketing":
            print(f"🟢 Estado válido — fase '{fase}': {phase_states(status)[fase]}; prontidão depende dos insumos e do escopo autorizado")
        else:
            print(f"🟢 PREFLIGHT OK — fase '{fase}' pronta para executar")
        if warnings:
            print(f"   ({len(warnings)} warning(s) — revise se necessário)")
        sys.exit(0)


if __name__ == "__main__":
    main()
