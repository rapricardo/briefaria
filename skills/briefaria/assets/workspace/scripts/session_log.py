#!/usr/bin/env python3
"""
Session log — registra atividades de produção no projeto.

Mantém um arquivo session-log.md acumulativo na raiz do projeto.
Cada entrada tem timestamp, fase, ação e detalhes.

Uso pelo agente:
  python scripts/session_log.py --project clientes/slug/producao/_ativo \
    --fase storyboard --action "Criado storyboard com 50 shots" \
    --details "Seções: hook, conflito, virada, resolução, CTA. 8 shots > 7s precisam extension."

  python scripts/session_log.py --project clientes/slug/producao/_ativo \
    --fase imagens --action "Geradas 50 keyframe images + 8 extensions" \
    --details "Extensions para shots 9, 36, 41, 42, 44, 46, 47, 48 com ângulos diferentes."

  # Ler log existente (para início de sessão nova)
  python scripts/session_log.py --project clientes/slug/producao/_ativo --read

  # Ler apenas últimas N entradas
  python scripts/session_log.py --project clientes/slug/producao/_ativo --read --last 5
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def read_log(proj: Path, last: int = None) -> str:
    """Lê o session-log.md e retorna conteúdo (opcionalmente últimas N entradas)."""
    log_path = proj / "session-log.md"
    if not log_path.exists():
        return "(nenhum log anterior)"

    content = log_path.read_text(encoding="utf-8")

    if last and last > 0:
        # Cada entrada começa com "### "
        entries = content.split("\n### ")
        if len(entries) > 1:
            # Primeiro elemento é o header
            header = entries[0]
            entries = entries[1:]
            recent = entries[-last:]
            return header + "\n### " + "\n### ".join(recent)

    return content


def append_log(proj: Path, fase: str, action: str, details: str = None):
    """Adiciona entrada ao session-log.md."""
    log_path = proj / "session-log.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not log_path.exists():
        # Criar com header
        header = f"# Session Log\n\nProjeto: {proj.name}\n\n"
        log_path.write_text(header, encoding="utf-8")

    entry = f"\n### [{now}] {fase}\n\n**{action}**\n"
    if details:
        entry += f"\n{details}\n"
    entry += "\n---\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"📝 Log registrado: [{fase}] {action}")


def main():
    parser = argparse.ArgumentParser(description="Session log — registra atividades de produção")
    parser.add_argument("--project", required=True, help="Caminho do projeto")
    parser.add_argument("--fase", help="Fase do pipeline")
    parser.add_argument("--action", help="Descrição da ação realizada")
    parser.add_argument("--details", help="Detalhes adicionais (decisões, problemas, etc.)")
    parser.add_argument("--read", action="store_true", help="Apenas ler o log existente")
    parser.add_argument("--last", type=int, help="Com --read, mostrar apenas últimas N entradas")
    args = parser.parse_args()

    proj = Path(args.project).resolve()
    if not proj.exists():
        print(f"❌ Projeto não encontrado: {proj}")
        sys.exit(1)

    if args.read:
        content = read_log(proj, last=args.last)
        print(content)
    elif args.fase and args.action:
        append_log(proj, args.fase, args.action, args.details)
    else:
        parser.error("Use --read para ler, ou --fase + --action para registrar")


if __name__ == "__main__":
    main()
