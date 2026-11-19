---
name: briefaria
description: Opera uma máquina de marketing e produção por cliente. Use para cadastrar marcas, planejar e acompanhar campanhas, criar conteúdo e produzir ou retomar carrosséis e vídeos a partir dos briefs, assets e status do projeto.
---

# Briefaria

Use a raiz do workspace solicitada pelo usuário. Um workspace inicializado contém `templates/`, `workflows/`, `scripts/setup-project.py` e um [manual](assets/workspace/MANUAL.md). Se faltar o runtime, execute `python3 <pasta-da-skill>/scripts/init-workspace.py <workspace>`. Execute os comandos a partir da raiz inicializada. Se o pedido já indicar outro workspace, preserve esse destino.

| Pedido | Leia no workspace |
|---|---|
| Cadastro, novo projeto, diagnóstico do ambiente | `workflows/setup/WORKFLOW.md` |
| Implantação, estratégia, site, copy, mídia paga, campanha, resultado | `workflows/marketing-os/WORKFLOW.md` |
| Fila de ideação, tese e revisão independente | `sistema/README.md` |
| Produzir ou retomar uma peça a partir de brief e status | `workflows/pipeline-operator/WORKFLOW.md` |
| Preparar distribuição ou publicar um carrossel aprovado | `workflows/marketing-os/references/distribution.md` |

Identifique o cliente e o projeto pelo pedido. `_ativo` é um atalho por cliente. Use `brand-context.md` para o contexto comercial e `branding.json` para a produção visual. Campanhas referenciam peças com IDs estáveis. Crie as peças com `--no-activate` quando vinculadas a uma campanha que já está ativa.

Use os scripts do workspace para criar estrutura e executar fases. Preserve a forma de `status.json` e metadata existentes, registre as fases efetivamente executadas e mantenha gravações originais. HyperFrames é o padrão de novas composições visuais. Leia o workflow de render e conserve o motor de projetos existentes.

Execute geração paga, uploads, publicações, envio e mudanças de orçamento apenas no escopo autorizado. Use credenciais do usuário para a fase que as exige.
