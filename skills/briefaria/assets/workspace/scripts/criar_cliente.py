#!/usr/bin/env python3
"""Cria/normaliza pacote de cliente no contrato de contexto do Marketing OS.

Uso:
  python scripts/criar_cliente.py --name "Cliente Exemplo"
  python scripts/criar_cliente.py --slug cliente-existente --normalize
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "cliente"
CLIENTES = ROOT / "clientes"


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")


def copy_template(dst: Path, cliente: str, slug: str) -> bool:
    if dst.exists():
        return False
    src = TEMPLATES / dst.name
    if not src.exists():
        raise FileNotFoundError(f"Template ausente: {src}")
    content = (
        src.read_text(encoding="utf-8")
        .replace("{{CLIENTE}}", cliente)
        .replace("{{SLUG}}", slug)
        .replace("{{AAAA-MM-DD}}", date.today().isoformat())
    )
    dst.write_text(content, encoding="utf-8")
    return True


def ensure_dirs(client_dir: Path) -> None:
    for rel in [
        "assets/logos",
        "assets/references",
        "assets/model-sheets",
        "estrategia",
        "producao",
        "entregas",
        "_arquivo",
    ]:
        (client_dir / rel).mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help="Nome humano do cliente")
    ap.add_argument("--slug", help="Slug do cliente")
    ap.add_argument("--normalize", action="store_true", help="Normaliza cliente existente sem chamar setup-project")
    args = ap.parse_args()
    if not args.name and not args.slug:
        ap.error("use --name ou --slug")

    slug = args.slug or slugify(args.name or "")
    name = args.name or slug
    client_dir = CLIENTES / slug

    if not client_dir.exists() and not args.normalize:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "setup-project.py"), "new-client", "--name", name, "--slug", slug],
            check=True,
        )
    elif not client_dir.exists():
        client_dir.mkdir(parents=True)

    ensure_dirs(client_dir)
    created = []
    # Contrato de contexto do Marketing OS (ver workflows/marketing-os/WORKFLOW.md)
    for filename in ["mandato.md", "implantacao.md", "decisoes.md", "brand-context.md", "aprendizados.md", "briefing.md"]:
        if copy_template(client_dir / filename, name, slug):
            created.append(filename)
    branding = client_dir / "branding.json"
    if not branding.exists():
        src = ROOT / "templates" / "branding.json"
        branding.write_text(src.read_text(encoding="utf-8").replace("{{CLIENTE}}", name), encoding="utf-8")
        created.append("branding.json")

    print(f"Cliente pronto: clientes/{slug}/")
    if created:
        print("Arquivos criados:")
        for item in created:
            print(f"  - {item}")
    else:
        print("Nenhum arquivo novo; estrutura já estava normalizada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
