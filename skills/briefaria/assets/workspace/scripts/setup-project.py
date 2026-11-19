#!/usr/bin/env python3
"""
Setup de projetos para a Maquina de Producao.

Comandos:
  check-env     Verifica dependencias do ambiente
  new-client    Cria estrutura de pastas e config.json para novo cliente
  new-project   Cria projeto de producao (com symlink _ativo)
  archive       Arquiva o projeto ativo de um cliente

Uso:
    python scripts/setup-project.py check-env

    python scripts/setup-project.py new-client --name "Estúdio Exemplo"

    python scripts/setup-project.py new-project \
      --client estudio-exemplo \
      --type carrossel \
      --name "dor-cronica-educativo"

    python scripts/setup-project.py archive --client estudio-exemplo
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Converte texto em slug: lowercase, hifens, sem acentos."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def print_header(title: str):
    print("=" * 60)
    print(title)
    print("=" * 60)


# ---------------------------------------------------------------------------
# check-env
# ---------------------------------------------------------------------------

def check_env() -> bool:
    """Verifica todas as dependencias do ambiente."""
    checks = []

    # Python
    try:
        r = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        checks.append(("Python", r.stdout.strip(), True))
    except FileNotFoundError:
        checks.append(("Python", "nao encontrado", False))

    # Node.js
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True)
        checks.append(("Node.js", r.stdout.strip(), True))
    except FileNotFoundError:
        checks.append(("Node.js", "nao encontrado — brew install node", False))

    # FFmpeg
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        line = r.stdout.split("\n")[0] if r.stdout else "?"
        checks.append(("FFmpeg", line, True))
    except FileNotFoundError:
        checks.append(("FFmpeg", "nao encontrado — brew install ffmpeg", False))

    # whisper-cli
    if shutil.which("whisper-cli"):
        checks.append(("whisper-cli", "instalado", True))
    else:
        checks.append(("whisper-cli", "nao encontrado — brew install whisper-cpp", False))

    # Modelo whisper
    model_path = os.path.join(ROOT, "models", "ggml-medium.bin")
    if os.path.isfile(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        checks.append(("Modelo whisper", f"ggml-medium.bin ({size_mb:.0f}MB)", True))
    else:
        checks.append(("Modelo whisper", "nao encontrado — ver README", False))

    # Pacotes Python
    pkgs = [
        ("google-genai", "google.genai"),
        ("elevenlabs", "elevenlabs"),
        ("fal-client", "fal_client"),
        ("Pillow", "PIL"),
    ]
    for pkg_name, import_name in pkgs:
        try:
            __import__(import_name.split(".")[0])
            checks.append((pkg_name, "instalado", True))
        except ImportError:
            checks.append((pkg_name, f"pip install {pkg_name}", False))

    # .env
    env_path = os.path.join(ROOT, ".env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            env_content = f.read()
        for key in ["GEMINI_API_KEY", "ELEVENLABS_API_KEY", "FAL_KEY"]:
            lines = [l for l in env_content.splitlines() if l.startswith(key)]
            has_value = any("=" in l and l.split("=", 1)[1].strip().strip('"') for l in lines)
            if has_value:
                checks.append((key, "configurado", True))
            else:
                checks.append((key, "vazio ou ausente no .env", False))
    else:
        checks.append((".env", "arquivo nao encontrado — cp .env.example .env", False))

    # Remotion
    remotion_modules = os.path.join(ROOT, "remotion", "node_modules")
    if os.path.isdir(remotion_modules):
        checks.append(("Remotion", "node_modules OK", True))
    else:
        checks.append(("Remotion", "cd remotion && npm install", False))

    # Report
    print_header("VERIFICACAO DE AMBIENTE")
    print()
    ok = sum(1 for _, _, p in checks if p)
    fail = sum(1 for _, _, p in checks if not p)

    for name, status, passed in checks:
        icon = "[OK]" if passed else "[!!]"
        print(f"  {icon} {name:<20} {status}")

    print()
    if fail == 0:
        print(f"Tudo OK ({ok}/{ok}). Pronto para produzir.")
    else:
        print(f"{ok} OK, {fail} pendente(s). Corrija os itens acima.")

    return fail == 0


# ---------------------------------------------------------------------------
# new-client
# ---------------------------------------------------------------------------

def new_client(name: str, slug: str = None) -> str:
    """Cria estrutura de pastas e config.json para novo cliente."""
    if not slug:
        slug = slugify(name)

    client_dir = os.path.join(ROOT, "clientes", slug)

    if os.path.exists(client_dir):
        print(f"ERRO: Cliente ja existe: {client_dir}", file=sys.stderr)
        sys.exit(1)

    # Pastas
    for subdir in [
        "assets/logos",
        "assets/model-sheets",
        "assets/references",
        "estrategia",
        "entregas",
        "_arquivo",
        "producao",
    ]:
        os.makedirs(os.path.join(client_dir, subdir), exist_ok=True)

    # config.json — usar template se existir
    template_path = os.path.join(ROOT, "templates", "config-cliente.json")
    if os.path.isfile(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["nome"] = name
        config["slug"] = slug
    else:
        config = {
            "nome": name,
            "slug": slug,
            "descricao": "",
            "setor": "",
            "site": "",
            "slogan": "",
            "cores": {"primaria": "", "secundaria": "", "acento": "", "texto": "#252527", "fundo": "#FFFFFF"},
            "fontes": {"titulo": "", "corpo": ""},
            "tom_de_voz": "",
            "estilo_visual": "",
            "style_reference": "",
            "palavras_chave": [],
            "palavras_proibidas": [],
            "proposta_de_valor": "",
            "produtos": {},
            "personas": {},
            "concorrentes": [],
            "canais": {},
            "links": {},
            "personagens": {},
        }
    config_path = os.path.join(client_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Contrato de contexto do Marketing OS: brand-context.md, aprendizados.md, branding.json
    hoje = date.today().isoformat()
    for nome_tpl, destino in [
        (os.path.join("cliente", "brand-context.md"), "brand-context.md"),
        (os.path.join("cliente", "aprendizados.md"), "aprendizados.md"),
        (os.path.join("cliente", "mandato.md"), "mandato.md"),
        (os.path.join("cliente", "implantacao.md"), "implantacao.md"),
        (os.path.join("cliente", "decisoes.md"), "decisoes.md"),
        ("branding.json", "branding.json"),
    ]:
        tpl = os.path.join(ROOT, "templates", nome_tpl)
        if not os.path.isfile(tpl):
            continue
        with open(tpl, "r", encoding="utf-8") as f:
            texto = f.read()
        texto = texto.replace("{{SLUG}}", slug).replace("{{CLIENTE}}", name).replace("{{AAAA-MM-DD}}", hoje)
        with open(os.path.join(client_dir, destino), "w", encoding="utf-8") as f:
            f.write(texto)

    print(f"Cliente criado: clientes/{slug}/")
    print("  config.json      identidade e operação")
    print("  brand-context.md contrato de contexto (preencher)")
    print("  aprendizados.md  padrões confirmados por resultado")
    print("  mandato.md       objetivo, escopo, autonomia, acessos (F0)")
    print("  implantacao.md   checklist de implantação do marketing")
    print("  branding.json    identidade visual (preencher)")
    print("  estrategia/  entregas/  _arquivo/  assets/  producao/")
    print()
    print("Proximos passos:")
    print("  1. Seguir a implantacao (marketing-os): python3 scripts/implantacao.py --client %s" % slug)
    print("  2. Validar: python3 scripts/validar_cliente.py --client %s" % slug)
    print("  3. Criar projeto: new-project --client %s --type <tipo> --name <desc>" % slug)

    return client_dir


# ---------------------------------------------------------------------------
# new-project
# ---------------------------------------------------------------------------

# Formatos de video/imagem suportados
FORMATOS = {
    "16:9": {"aspect_ratio": "16:9", "width": 1920, "height": 1080, "label": "horizontal (YouTube)"},
    "9:16": {"aspect_ratio": "9:16", "width": 1080, "height": 1920, "label": "vertical (Reels/TikTok)"},
    "1:1":  {"aspect_ratio": "1:1",  "width": 1080, "height": 1080, "label": "quadrado (Instagram feed)"},
}

# Formato padrao por tipo de projeto
DEFAULT_FORMATO = {
    "gravado": "16:9",
    "carrossel": "1:1",
    "video": "16:9",
    "video-dialogo": "9:16",
    "marketing": "multi",
}

# Pipelines por tipo de projeto
PIPELINES = {
    "gravado": {
        "gravar": "pending",
        "transcrever": "pending",
        "editar": "pending",
        "assets": "pending",
        "compor": "pending",
        "publicar": "pending",
    },
    "carrossel": {
        "roteiro": "pending",
        "imagens": "pending",
        "publicar": "pending",
    },
    "video": {
        "roteiro": "pending",
        "voiceover": "pending",
        "transcrever": "pending",
        "storyboard": "pending",
        "imagens": "pending",
        "clips": "pending",
        "sfx": "pending",
        "fcpxml": "pending",
        "davinci": "pending",
    },
    "video-dialogo": {
        "roteiro": "pending",
        "storyboard": "pending",
        "imagens": "pending",
        "clips": "pending",
        "fcpxml": "pending",
        "davinci": "pending",
    },
    "marketing": {
        "fundacao": "pending",
        "estrategia": "pending",
        "conteudo": "pending",
        "distribuicao": "pending",
        "analise": "pending",
    },
}

# Subpastas por tipo de projeto
DIRS = {
    "gravado": ["recordings", "transcript", "imagens", "audio", "clips", "render", "publish"],
    "carrossel": ["imagens", "publish"],
    "video": ["imagens", "audio", "clips", "sfx", "render", "publish"],
    "video-dialogo": ["imagens", "clips", "render", "publish"],
    "marketing": ["conteudo", "ads", "relatorios", "assets"],
}


def new_project(client_slug: str, project_type: str, name: str, task_id: str = None, formato: str = None, activate: bool = True, compositor: str = None) -> str:
    """Cria estrutura de pastas e status.json para novo projeto."""
    client_dir = os.path.join(ROOT, "clientes", client_slug)

    if not os.path.isdir(client_dir):
        print(f"ERRO: Cliente nao encontrado: clientes/{client_slug}/", file=sys.stderr)
        print(f"Crie primeiro: python scripts/setup-project.py new-client --name \"Nome\"", file=sys.stderr)
        sys.exit(1)

    # Verificar config.json ou branding.json
    has_config = os.path.isfile(os.path.join(client_dir, "config.json"))
    has_branding = os.path.isfile(os.path.join(client_dir, "branding.json"))
    if not has_config and not has_branding:
        print(f"AVISO: Nenhum config.json ou branding.json em clientes/{client_slug}/", file=sys.stderr)

    # Gerar slug do projeto
    today = date.today().strftime("%Y-%m-%d")
    name_slug = slugify(name)

    if task_id:
        project_slug = f"{task_id}-{name_slug}" if name_slug else task_id
    else:
        project_slug = f"{today}_{name_slug}"

    project_dir = os.path.join(client_dir, "producao", project_slug)

    if os.path.exists(project_dir):
        print(f"ERRO: Projeto ja existe: {project_dir}", file=sys.stderr)
        sys.exit(1)

    if project_type not in PIPELINES:
        print(f"ERRO: Tipo invalido: {project_type}. Use: gravado, carrossel, video", file=sys.stderr)
        sys.exit(1)

    if compositor is not None and (compositor != "hyperframes" or project_type not in {"video", "video-dialogo", "gravado"}):
        print("ERRO: --compositor hyperframes exige tipo video, video-dialogo ou gravado", file=sys.stderr)
        sys.exit(1)
    pipeline = PIPELINES[project_type].copy()
    if compositor == "hyperframes" and project_type != "gravado":
        pipeline = dict.fromkeys(["roteiro", "assets", "compor", "publicar"], "pending")

    # Criar subpastas
    for d in DIRS[project_type]:
        os.makedirs(os.path.join(project_dir, d), exist_ok=True)
    if compositor == "hyperframes":
        os.makedirs(os.path.join(project_dir, "composition"), exist_ok=True)

    # Resolver formato
    if not formato:
        formato = DEFAULT_FORMATO.get(project_type, "16:9")
    if formato == "multi":
        fmt = {"aspect_ratio": "multi", "width": 0, "height": 0, "label": "multi-formato (marketing)"}
    elif formato not in FORMATOS:
        print(f"ERRO: Formato invalido: {formato}. Use: {', '.join(FORMATOS.keys())}", file=sys.stderr)
        sys.exit(1)
    else:
        fmt = FORMATOS[formato]

    # Criar brief.md
    tipo_label = project_type
    brief = f"""# Brief — {name}

| Campo | Valor |
|-------|-------|
| **Projeto** | {name} |
| **Cliente** | {client_slug} |
| **Tipo** | {tipo_label} |
| **Formato** | {formato} ({fmt['label']}) |
| **Objetivo** | |
| **Publico** | |
| **Plataformas** | |

## Notas

-
"""
    with open(os.path.join(project_dir, "brief.md"), "w", encoding="utf-8") as f:
        f.write(brief)
        if compositor == "hyperframes":
            f.write("\n## Composição\n\nHyperFrames em `composition/`; outputs em `render/`. "
                    "Contexto de marca: `../../brand-context.md` e `../../branding.json`. "
                    "Reutilizar assets; acrescentar fases específicas de geração apenas quando necessárias.\n")

    # Criar status.json — marketing usa template rico, outros usam pipeline simples
    if project_type == "marketing":
        mkt_template = os.path.join(ROOT, "templates", "status-marketing.json")
        if os.path.isfile(mkt_template):
            with open(mkt_template, "r", encoding="utf-8") as f:
                status = json.load(f)
            status["cliente"] = client_slug
            status["projeto"] = project_slug
            status["created"] = today
            status["descricao"] = name
        else:
            status = {
                "tipo": project_type,
                "formato": formato,
                "cliente": client_slug,
                "projeto": project_slug,
                "created": today,
                "pipeline": PIPELINES[project_type].copy(),
            }
    else:
        status = {
            "tipo": project_type,
            "formato": formato,
            "cliente": client_slug,
            "projeto": project_slug,
            "created": today,
            "pipeline": pipeline,
        }
    with open(os.path.join(project_dir, "status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Criar/atualizar symlink _ativo
    producao_dir = os.path.join(client_dir, "producao")
    ativo_link = os.path.join(producao_dir, "_ativo")
    if activate:
        if os.path.islink(ativo_link):
            os.unlink(ativo_link)
        os.symlink(project_slug, ativo_link)

    # Report
    rel_path = os.path.relpath(project_dir, ROOT)
    print(f"Projeto criado: {rel_path}/")
    print(f"  Tipo: {project_type}")
    print(f"  Formato: {formato} ({fmt['label']}) — {fmt['width']}x{fmt['height']}")
    print(f"  Pipeline: {' > '.join(pipeline.keys())}")
    print(f"  status.json: {rel_path}/status.json")
    print(f"  brief.md: {rel_path}/brief.md")
    print(f"  _ativo → {project_slug}" if activate else "  _ativo preservado")
    print()

    if project_type == "gravado":
        print("Proximo passo:")
        print(f"  Gravar e salvar em: {rel_path}/recordings/")
        print("  Depois, pedir ao agente para transcrever.")
    elif project_type == "carrossel":
        print("Proximo passo:")
        print("  Criar roteiro.json com os slides do carrossel.")
    elif project_type == "marketing":
        print("Proximo passo:")
        print("  Fase fundacao: preencher brand-context.md e analise competitiva.")
        print("  Skill do projeto: workflows/marketing-os/WORKFLOW.md")
    else:
        print("Proximo passo:")
        print("  Criar roteiro com cenas e beats do video.")

    return project_dir


# ---------------------------------------------------------------------------
# archive
# ---------------------------------------------------------------------------

def archive_project(client_slug: str, project_slug: str = None):
    """Arquiva o projeto ativo (ou especificado) de um cliente."""
    client_dir = os.path.join(ROOT, "clientes", client_slug)
    producao_dir = os.path.join(client_dir, "producao")

    if not os.path.isdir(client_dir):
        print(f"ERRO: Cliente nao encontrado: clientes/{client_slug}/", file=sys.stderr)
        sys.exit(1)

    # Determinar qual projeto arquivar
    if project_slug:
        project_dir = os.path.join(producao_dir, project_slug)
        if not os.path.isdir(project_dir):
            print(f"ERRO: Projeto nao encontrado: {project_slug}", file=sys.stderr)
            sys.exit(1)
    else:
        # Usar _ativo symlink
        ativo_link = os.path.join(producao_dir, "_ativo")
        if not os.path.islink(ativo_link):
            print(f"ERRO: Nenhum projeto ativo (symlink _ativo nao existe)", file=sys.stderr)
            print(f"  Use --project para especificar qual projeto arquivar", file=sys.stderr)
            sys.exit(1)
        project_slug = os.readlink(ativo_link)
        project_dir = os.path.join(producao_dir, project_slug)

    # Criar pasta arquivo/
    arquivo_dir = os.path.join(producao_dir, "arquivo")
    os.makedirs(arquivo_dir, exist_ok=True)

    # Mover projeto
    dest = os.path.join(arquivo_dir, project_slug)
    if os.path.exists(dest):
        print(f"ERRO: Destino ja existe: arquivo/{project_slug}", file=sys.stderr)
        sys.exit(1)

    shutil.move(project_dir, dest)

    # Remover symlink _ativo se apontava para este projeto
    ativo_link = os.path.join(producao_dir, "_ativo")
    if os.path.islink(ativo_link):
        linked = os.readlink(ativo_link)
        if linked == project_slug:
            os.unlink(ativo_link)

    print(f"Projeto arquivado: {project_slug}")
    print(f"  De: producao/{project_slug}/")
    print(f"  Para: producao/arquivo/{project_slug}/")
    if not os.path.islink(ativo_link):
        print(f"  Symlink _ativo removido")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Setup de projetos para a Maquina de Producao",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s check-env
  %(prog)s new-client --name "Estúdio Exemplo"
  %(prog)s new-project --client estudio-exemplo --type carrossel --name "dor-cronica"
  %(prog)s new-project --client estudio-exemplo --type gravado --name "como-uso-agentes"
  %(prog)s new-project --client estudio-exemplo --type video --name "rochinha" --task-id EXEMPLO
""",
    )
    sub = parser.add_subparsers(dest="command")

    # check-env
    sub.add_parser("check-env", help="Verificar dependencias do ambiente")

    # new-client
    nc = sub.add_parser("new-client", help="Criar novo cliente")
    nc.add_argument("--name", required=True, help="Nome do cliente")
    nc.add_argument("--slug", help="Slug customizado (default: gerado do nome)")

    # new-project
    np_cmd = sub.add_parser("new-project", help="Criar novo projeto de producao")
    np_cmd.add_argument("--client", required=True, help="Slug do cliente")
    np_cmd.add_argument(
        "--type", required=True, choices=["gravado", "carrossel", "video", "video-dialogo", "marketing"],
        help="Tipo: gravado, carrossel, video, video-dialogo, marketing (campanha multi-canal)",
    )
    np_cmd.add_argument("--name", required=True, help="Descricao curta do projeto")
    np_cmd.add_argument("--task-id", help="ID da task para usar no slug do projeto")
    np_cmd.add_argument("--no-activate", action="store_true", help="Criar peça sem alterar o projeto _ativo")
    np_cmd.add_argument("--compositor", choices=["hyperframes"], help="Criar composição HyperFrames sem exigir geração de clips ou DaVinci; omitir preserva pipeline legado")
    np_cmd.add_argument(
        "--formato", choices=["16:9", "9:16", "1:1"],
        help="Formato de saida: 16:9 (YouTube), 9:16 (Reels/TikTok), 1:1 (feed). Default depende do tipo.",
    )

    # archive
    ar = sub.add_parser("archive", help="Arquivar projeto ativo de um cliente")
    ar.add_argument("--client", required=True, help="Slug do cliente")
    ar.add_argument("--project", help="Slug do projeto (default: projeto _ativo)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "check-env":
        ok = check_env()
        sys.exit(0 if ok else 1)
    elif args.command == "new-client":
        new_client(args.name, args.slug)
    elif args.command == "new-project":
        new_project(args.client, args.type, args.name, args.task_id, getattr(args, 'formato', None), not args.no_activate, args.compositor)
    elif args.command == "archive":
        archive_project(args.client, getattr(args, 'project', None))


if __name__ == "__main__":
    main()
