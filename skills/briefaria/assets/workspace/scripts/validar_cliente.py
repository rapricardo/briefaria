#!/usr/bin/env python3
"""Valida o contrato de contexto do Marketing OS para um cliente.

Contrato: brand-context.md (entrada única) + branding.json (visual) + config.json
(identidade/operação). Documentos de estratégia só entram pelo Mapa de leitura.

Uso:
  python3 scripts/validar_cliente.py --client estudio-exemplo
  python3 scripts/validar_cliente.py --all
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTES = ROOT / "clientes"

SECOES = [
    "Restrições",
    "Produto",
    "Público",
    "Posicionamento",
    "Provas",
    "Voz",
    "Mapa de leitura",
    "Lacunas",
]
LIMITE_PALAVRAS = 2500
RECOMENDADOS = ["mandato.md", "implantacao.md", "decisoes.md", "aprendizados.md", "competitors.json"]
LEGADO = [
    "brand-voice.json",
    "brand.md",
    "design-system.md",
    "personas.md",
    "ofertas.md",
    "canais.md",
]
CAMPOS_NARRATIVOS = {"proposta_de_valor", "produtos", "personas", "objecoes", "palavras_chave"}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def secao(text: str, titulo: str) -> str:
    m = re.search(rf"^## \d+\. {re.escape(titulo)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def caminhos_do_mapa(text: str) -> list[str]:
    bloco = secao(text, "Mapa de leitura")
    paths = re.findall(r"`([^`\s]+\.(?:md|json|yaml))`", bloco)
    return [p for p in paths if "{{" not in p]


def validate(slug: str) -> tuple[bool, list[str]]:
    client = CLIENTES / slug
    msgs: list[str] = []
    ok = True
    if not client.is_dir():
        return False, [f"[ERRO] Cliente não existe: clientes/{slug}/"]

    def erro(m: str) -> None:
        nonlocal ok
        ok = False
        msgs.append(f"[ERRO] {m}")

    # config.json
    cfg = client / "config.json"
    if not cfg.exists():
        erro("ausente: config.json")
    else:
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            faltando = [k for k in ("nome", "slug") if not data.get(k) or data.get(k) == "???"]
            if faltando:
                erro(f"config.json sem {', '.join(faltando)}")
            else:
                msgs.append("[OK] config.json")
            extras = sorted(CAMPOS_NARRATIVOS & data.keys())
            if extras:
                msgs.append(f"[AVISO] config.json tem campos narrativos ({', '.join(extras)}); mover para brand-context.md")
        except Exception as e:  # noqa: BLE001
            erro(f"config.json inválido: {e}")

    # branding.json
    br = client / "branding.json"
    if not br.exists():
        erro("ausente: branding.json")
    else:
        try:
            data = json.loads(br.read_text(encoding="utf-8"))
            msgs.append("[OK] branding.json")
            extras = sorted(CAMPOS_NARRATIVOS & data.keys())
            if extras:
                msgs.append(f"[AVISO] branding.json tem campos narrativos ({', '.join(extras)}); manter só visual + tom/proibidas derivados")
        except Exception as e:  # noqa: BLE001
            erro(f"branding.json inválido: {e}")

    # brand-context.md
    bc = client / "brand-context.md"
    if not bc.exists():
        erro("ausente: brand-context.md (templates/cliente/brand-context.md)")
    else:
        text = bc.read_text(encoding="utf-8", errors="ignore")
        if "{{" in text:
            erro("brand-context.md tem campos do template sem preencher ({{...}})")
        faltam = [s for s in SECOES if not re.search(rf"^## \d+\. {re.escape(s)}\s*$", text, re.M)]
        if faltam:
            erro(f"brand-context.md sem seções: {', '.join(faltam)}")
        palavras = len(re.sub(r"<!--.*?-->", "", text, flags=re.S).split())
        if palavras > LIMITE_PALAVRAS:
            msgs.append(f"[AVISO] brand-context.md com {palavras} palavras (limite ~{LIMITE_PALAVRAS}); mover detalhe para arquivo citado no mapa")
        if not frontmatter(bc).get("atualizado"):
            msgs.append("[AVISO] brand-context.md sem 'atualizado' no frontmatter")
        if ok and not faltam:
            msgs.append(f"[OK] brand-context.md ({palavras} palavras)")

        mapa = caminhos_do_mapa(text)
        no_mapa = set()
        for rel in mapa:
            alvo = (client / rel).resolve()
            no_mapa.add(alvo)
            if not alvo.exists():
                erro(f"Mapa de leitura aponta para arquivo inexistente: {rel}")
            elif alvo.suffix == ".md" and frontmatter(alvo).get("status") == "substituído":
                erro(f"Mapa de leitura aponta para documento substituído: {rel}")

        # estrategia/
        est = client / "estrategia"
        if est.is_dir():
            for doc in sorted(est.glob("*.md")):
                if doc.name.lower() == "readme.md":
                    continue
                status = frontmatter(doc).get("status")
                rel = doc.relative_to(client)
                if not status:
                    msgs.append(f"[AVISO] {rel} sem 'status' no frontmatter")
                elif status in ("substituído", "referência"):
                    msgs.append(f"[AVISO] {rel} com status '{status}' na pasta de trabalho; mover para _arquivo/")
                elif status == "vigente" and doc.resolve() not in no_mapa:
                    msgs.append(f"[AVISO] {rel} vigente e fora do Mapa de leitura")

    for rel in RECOMENDADOS:
        if not (client / rel).exists():
            msgs.append(f"[AVISO] recomendado ausente: {rel}")
        else:
            msgs.append(f"[OK] {rel}")

    for rel in LEGADO:
        if (client / rel).exists():
            msgs.append(f"[AVISO] legado: {rel}; migrar para brand-context.md e mover para _arquivo/")

    return ok, msgs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if not args.client and not args.all:
        ap.error("use --client SLUG ou --all")

    slugs = [p.name for p in CLIENTES.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))] if args.all else [args.client]
    falhou = False
    for slug in sorted(slugs):
        ok, msgs = validate(slug)
        print("=" * 60)
        print(f"CLIENTE: {slug} — {'OK' if ok else 'PENDENTE'}")
        print("=" * 60)
        for m in msgs:
            print(m)
        falhou = falhou or not ok
    return 1 if falhou else 0


if __name__ == "__main__":
    raise SystemExit(main())
