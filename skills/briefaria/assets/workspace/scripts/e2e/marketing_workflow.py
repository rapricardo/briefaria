#!/usr/bin/env python3
"""Verifica setup → status → preflight em cópia temporária, sem APIs ou clientes reais.

Falhas cobertas: objetos de fase confundidos com conclusão; running/blocked ignorados;
estado/tipo inválido aceito; --all ocultando erros; regressão no pipeline simples;
criação de peça substituindo _ativo da campanha. Resultado repetível em JSON.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory(prefix='marketing-e2e-') as temp:
        workspace = Path(temp)
        (workspace / 'scripts').mkdir()
        for name in ('setup-project.py', 'preflight.py', 'implantacao.py', 'validar_cliente.py'):
            shutil.copy2(ROOT / 'scripts' / name, workspace / 'scripts' / name)
        shutil.copytree(ROOT / 'templates', workspace / 'templates')

        def run(name, script, arguments, code=0, contains=None):
            result = subprocess.run([sys.executable, str(workspace / 'scripts' / script), *arguments],
                                    cwd=workspace, text=True, capture_output=True)
            output = result.stdout + result.stderr
            ok = result.returncode == code and (contains is None or contains in output)
            results.append(dict(case=name, passed=ok, exit_code=result.returncode,
                                output=output.replace(str(workspace), '<workspace>')))
            return ok

        run('create-client', 'setup-project.py', ['new-client', '--name', 'E2E Marketing'])
        cliente = workspace / 'clientes' / 'e2e-marketing'
        contrato = ['config.json', 'mandato.md', 'implantacao.md', 'decisoes.md', 'brand-context.md', 'aprendizados.md', 'branding.json']
        results.append(dict(case='new-client-contract-files', passed=all((cliente / f).exists() for f in contrato)))
        run('new-client-implantacao-next-step', 'implantacao.py', ['--client', 'e2e-marketing'], 0, 'M1 Objetivo comercial')
        run('new-client-contract-pending', 'validar_cliente.py', ['--client', 'e2e-marketing'], 1, 'brand-context.md tem campos do template')
        run('resumo-lists-client', 'implantacao.py', ['--resumo'], 0, 'e2e-marketing')
        run('create-campaign', 'setup-project.py', ['new-project', '--client', 'e2e-marketing',
                                                  '--type', 'marketing', '--name', 'campanha'])
        active = workspace / 'clientes/e2e-marketing/producao/_ativo'
        project = active.resolve()
        status_path = project / 'status.json'
        original = json.loads(status_path.read_text())
        run('rich-pending', 'preflight.py', ['--project', str(project)], contains='PREFLIGHT: fundacao')
        run('rich-all', 'preflight.py', ['--project', str(project), '--all'], contains='distribuicao')
        for state, code in [('in_progress', 0), ('running', 0), ('blocked', 1), ('failed', 1),
                            ('waiting', 1), ('invalid', 1)]:
            status = json.loads(json.dumps(original))
            for phase in status['pipeline'].values():
                phase['status'] = 'done'
            status['pipeline']['analise']['status'] = state
            status_path.write_text(json.dumps(status))
            run('rich-' + state, 'preflight.py', ['--project', str(project)], code,
                'analise' if state != 'invalid' else 'inválido')
        status_path.write_text(json.dumps({'tipo': 'marketing', 'pipeline': {'fundacao': 'skip'}}))
        run('skipped-terminal', 'preflight.py', ['--project', str(project)], contains='encerradas')
        for name, payload in [('empty', {'tipo': 'marketing', 'pipeline': {}}),
                              ('unknown-type', {'tipo': 'unknown', 'pipeline': {'x': 'done'}}),
                              ('missing-status', {'tipo': 'marketing', 'pipeline': {'fundacao': {}}})]:
            status_path.write_text(json.dumps(payload))
            run(name, 'preflight.py', ['--project', str(project)], 1)
        status_path.write_text(json.dumps(original))
        run('invalid-explicit-phase', 'preflight.py', ['--project', str(project), '--fase', 'typo'], 1)
        run('create-child-preserves-active', 'setup-project.py', ['new-project', '--client', 'e2e-marketing',
            '--type', 'carrossel', '--name', 'peca', '--no-activate'])
        children = [p for p in project.parent.iterdir() if p.is_dir() and p.name.endswith('_peca')]
        results.append(dict(case='campaign-stays-active', passed=active.resolve() == project and len(children) == 1))
        if children:
            child = children[0]
            run('simple-pending-checks', 'preflight.py', ['--project', str(child)], 1,
                'branding.json')
            run('all-propagates-errors', 'preflight.py', ['--project', str(child), '--all'], 1)
            (child.parent.parent / 'branding.json').write_text('{}')
            run('simple-pending', 'preflight.py', ['--project', str(child)], contains='PREFLIGHT: roteiro')
            child_status = json.loads((child / 'status.json').read_text())
            child_status['pipeline'] = {p: 'done' for p in child_status['pipeline']}
            (child / 'status.json').write_text(json.dumps(child_status))
            run('simple-terminal', 'preflight.py', ['--project', str(child)], contains='encerradas')
        for kind in ('video', 'video-dialogo', 'gravado'):
            run('create-hyperframes-' + kind, 'setup-project.py', ['new-project', '--client', 'e2e-marketing',
                '--type', kind, '--name', 'motion-' + kind, '--compositor', 'hyperframes', '--no-activate'])
            motion = next(project.parent.glob('*_motion-' + kind))
            data = json.loads((motion / 'status.json').read_text())
            results.append(dict(case='hyperframes-structure-' + kind,
                passed=(motion / 'composition').is_dir() and 'compor' in data['pipeline']
                and 'fcpxml' not in data['pipeline'] and active.resolve() == project))
            data['pipeline'] = {k: 'skip' if k != 'compor' else {'status': 'pending', 'outputs': [], 'note': 'preserve'}
                                for k in data['pipeline']}
            (motion / 'status.json').write_text(json.dumps(data))
            before = (motion / 'status.json').read_bytes()
            run('hyperframes-next-phase-' + kind, 'preflight.py', ['--project', str(motion)], contains='PREFLIGHT: compor')
            results.append(dict(case='hyperframes-metadata-preserved-' + kind,
                                passed=(motion / 'status.json').read_bytes() == before))
        for kind in ('marketing', 'carrossel'):
            run('reject-hyperframes-' + kind, 'setup-project.py', ['new-project', '--client', 'e2e-marketing',
                '--type', kind, '--name', 'reject-' + kind, '--compositor', 'hyperframes', '--no-activate'], 1)
            results.append(dict(case='no-partial-project-' + kind,
                                passed=not list(project.parent.glob('*_reject-' + kind))))
        run('legacy-video-pipeline', 'setup-project.py', ['new-project', '--client', 'e2e-marketing',
            '--type', 'video', '--name', 'legacy-video', '--no-activate'], contains='fcpxml > davinci')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'passed': all(r['passed'] for r in results), 'cases': results},
                                     ensure_ascii=False, indent=2) + '\n')
    print(f"{sum(r['passed'] for r in results)}/{len(results)} casos passaram. Artefato: {args.output}")
    return 0 if all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
