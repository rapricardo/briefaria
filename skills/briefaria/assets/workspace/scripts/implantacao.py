#!/usr/bin/env python3
"""Lê o checklist de implantação de um cliente e mostra progresso e próximas etapas.

Método: workflows/marketing-os/references/implantacao.md
Checklist: clientes/{slug}/implantacao.md

Uso:
  python3 scripts/implantacao.py --client estudio-exemplo
  python3 scripts/implantacao.py --client estudio-exemplo --dependentes E2
  python3 scripts/implantacao.py --all
  python3 scripts/implantacao.py --resumo   # uma linha por cliente (hook de início de sessão)
"""
from __future__ import annotations

import argparse
import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTES = ROOT / "clientes"
STATUS = {"pendente", "em andamento", "parcial", "feito", "n/a", "bloqueado"}
CONCLUIDO = {"feito", "n/a"}
LINHA = re.compile(r"^\|\s*([A-Z]\d)\s*\|")


@dataclass
class Etapa:
    id: str
    fase: str
    nome: str
    deps: list[str]
    status: str
    nota: str
    atualizado: str
    evidencias: list[str] = field(default_factory=list)


def ler(path: Path) -> list[Etapa]:
    etapas = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not LINHA.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cells += [""] * (7 - len(cells))
        eid, fase, nome, deps, status, nota, atualizado = cells[:7]
        dep_ids = [] if deps in ("", "—", "-") else [d.strip() for d in deps.split(",")]
        evid = re.findall(r"`([^`\s]+)`", nota)
        etapas.append(Etapa(eid, fase, nome, dep_ids, status.lower(), nota, atualizado, evid))
    return etapas


def status_frontmatter(p: Path) -> str | None:
    if p.suffix != ".md" or not p.is_file():
        return None
    m = re.match(r"^---\n(.*?)\n---", p.read_text(encoding="utf-8", errors="ignore"), re.S)
    if not m:
        return None
    s = re.search(r"^status:\s*(.+)$", m.group(1), re.M)
    return s.group(1).strip() if s else None


def dependentes(etapas: list[Etapa], alvo: str) -> list[str]:
    filhos: dict[str, list[str]] = {}
    for e in etapas:
        for d in e.deps:
            filhos.setdefault(d, []).append(e.id)
    vistos, fila = [], [alvo]
    while fila:
        atual = fila.pop(0)
        for f in filhos.get(atual, []):
            if f not in vistos:
                vistos.append(f)
                fila.append(f)
    return vistos


def analisar(slug: str, dep_alvo: str | None = None) -> bool:
    client = CLIENTES / slug
    path = client / "implantacao.md"
    print("=" * 64)
    print(f"IMPLANTAÇÃO: {slug}")
    print("=" * 64)
    if not path.exists():
        print("[ERRO] implantacao.md ausente (templates/cliente/implantacao.md)")
        return False
    etapas = ler(path)
    por_id = {e.id: e for e in etapas}
    erros, avisos = [], []

    for e in etapas:
        if e.status not in STATUS:
            erros.append(f"{e.id}: status inválido '{e.status}'")
        for d in e.deps:
            if d not in por_id:
                erros.append(f"{e.id}: dependência desconhecida {d}")
        if e.status == "feito" and not e.evidencias:
            erros.append(f"{e.id}: 'feito' sem evidência entre crases")
        for ev in e.evidencias:
            alvo = (client / ev).resolve()
            if not alvo.exists():
                if e.status == "feito":
                    erros.append(f"{e.id}: evidência inexistente: {ev}")
                else:
                    avisos.append(f"{e.id}: caminho citado não existe: {ev}")
            elif e.status == "feito" and status_frontmatter(alvo) in {"substituído", "proposta"}:
                avisos.append(f"{e.id}: evidência {ev} com status '{status_frontmatter(alvo)}'")
        if e.status in {"n/a", "bloqueado"} and not e.nota:
            erros.append(f"{e.id}: '{e.status}' sem motivo")
    fora_de_ordem = []
    for e in etapas:
        if e.status == "feito":
            abertas = [d for d in e.deps if d in por_id and por_id[d].status not in CONCLUIDO]
            if abertas:
                fora_de_ordem.append(f"{e.id} (antes de {', '.join(abertas)})")

    # Progresso por fase
    fases: dict[str, list[Etapa]] = {}
    for e in etapas:
        fases.setdefault(e.fase, []).append(e)
    print("\nProgresso")
    for fase, lst in fases.items():
        feitos = sum(1 for e in lst if e.status in CONCLUIDO)
        parciais = sum(1 for e in lst if e.status in {"parcial", "em andamento"})
        barra = "".join("■" if e.status in CONCLUIDO else "◧" if e.status in {"parcial", "em andamento"} else "□" for e in lst)
        print(f"  {fase:<16} {barra:<9} {feitos}/{len(lst)} concluídas, {parciais} parciais")

    prontas = [e for e in etapas if e.status in {"pendente", "parcial"} and all(por_id.get(d) and por_id[d].status in CONCLUIDO for d in e.deps)]
    andamento = [e for e in etapas if e.status == "em andamento"]
    bloqueadas = [e for e in etapas if e.status == "bloqueado"]

    if andamento:
        print("\nEm andamento")
        for e in andamento:
            print(f"  {e.id} {e.nome}")
    print("\nProntas para começar (dependências concluídas), na ordem do método")
    for e in prontas or []:
        print(f"  {e.id} {e.nome} [{e.status}]")
    if not prontas:
        print("  nenhuma")
    if bloqueadas:
        print("\nBloqueadas")
        for e in bloqueadas:
            print(f"  {e.id} {e.nome}: {e.nota}")
    if dep_alvo:
        print(f"\nEtapas que dependem de {dep_alvo} (revisar se {dep_alvo} mudar)")
        ordem = {e.id: i for i, e in enumerate(etapas)}
        deps = sorted(dependentes(etapas, dep_alvo), key=lambda x: ordem.get(x, 999))
        print("  " + (", ".join(deps) or "nenhuma"))
    if fora_de_ordem:
        print("\nConcluídas antes das dependências (revisar quando elas concluírem)")
        print("  " + " · ".join(fora_de_ordem))
    for a in avisos:
        print(f"[AVISO] {a}")
    for x in erros:
        print(f"[ERRO] {x}")
    return not erros


def contrato_ok(slug: str) -> bool | None:
    spec = importlib.util.spec_from_file_location("validar_cliente", ROOT / "scripts" / "validar_cliente.py")
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return mod.validate(slug)[0]
    except Exception:  # noqa: BLE001
        return None


def resumo() -> int:
    linhas, sem_cadastro = [], []
    for client in sorted(p for p in CLIENTES.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        slug = client.name
        path = client / "implantacao.md"
        if not path.exists():
            if not (client / "config.json").exists():
                sem_cadastro.append(slug)
            else:
                linhas.append(f"  {slug:<22} sem implantacao.md: criar_cliente.py --slug {slug} --normalize")
            continue
        etapas = ler(path)
        por_id = {e.id: e for e in etapas}
        feitas = sum(1 for e in etapas if e.status in CONCLUIDO)
        fase = next((e.fase for e in etapas if e.status not in CONCLUIDO), "concluída")
        prontas = [e.id for e in etapas if e.status in {"pendente", "parcial"}
                   and all(por_id.get(d) and por_id[d].status in CONCLUIDO for d in e.deps)]
        contrato = {True: "ok", False: "pendente", None: "?"}[contrato_ok(slug)]
        levantamento = "" if any(e.status != "pendente" for e in etapas) else " · levantamento pendente"
        linhas.append(f"  {slug:<22} {feitas:>2}/{len(etapas)} · fase {fase} · próximas: {', '.join(prontas[:4]) or '—'} · contrato {contrato}{levantamento}")
    print("Implantação dos clientes (detalhe: python3 scripts/implantacao.py --client {slug})")
    print("\n".join(linhas) if linhas else "  nenhum cliente")
    if sem_cadastro:
        print(f"  Pastas sem cadastro (sem config.json): {', '.join(sem_cadastro)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dependentes", metavar="ID")
    ap.add_argument("--resumo", action="store_true")
    args = ap.parse_args()
    if args.resumo:
        return resumo()
    if not args.client and not args.all:
        ap.error("use --client SLUG ou --all")
    slugs = sorted(p.name for p in CLIENTES.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))) if args.all else [args.client]
    ok = True
    for slug in slugs:
        ok = analisar(slug, args.dependentes) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
