#!/usr/bin/env python3
"""Instala o runtime da Briefaria em um workspace."""
import argparse
from pathlib import Path
import shutil
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "assets" / "workspace"
    target = args.workspace.expanduser().resolve()
    if target.is_relative_to(source):
        parser.error("Escolha um workspace fora da pasta de assets da skill.")
    entries = sorted(source.iterdir())
    names = {entry.name for entry in entries} - {"gitignore.template"}
    names.update({".gitignore", "LICENSE-briefaria"})
    conflicts = sorted(name for name in names
                       if (target / name).exists() or (target / name).is_symlink())
    if conflicts:
        parser.error("O workspace já tem estes caminhos: " + ", ".join(conflicts))
    if target.exists() and not target.is_dir():
        parser.error("O workspace precisa ser um diretório.")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".maquina-install-", dir=target.parent) as temp:
        staged = Path(temp) / "workspace"
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
        (staged / "gitignore.template").rename(staged / ".gitignore")
        shutil.copy2(source.parents[1] / "LICENSE", staged / "LICENSE-briefaria")
        if not target.exists():
            staged.rename(target)
        else:
            for entry in sorted(staged.iterdir()):
                entry.rename(target / entry.name)
    print(f"Workspace pronto em {target}")
    print(f"Manual: {target / 'MANUAL.md'}")


if __name__ == "__main__":
    main()
