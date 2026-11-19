---
name: setup
description: Cria clientes e projetos e verifica dependências usando os scripts deste repositório.
---

# Setup do projeto

Para novas composições visuais, use `--compositor hyperframes`; preserve o motor de projetos existentes. O flag cria `composition/` e pipeline sem exigir clips gerados ou DaVinci. A [integração](../render/references/hyperframes.md) define contexto e responsabilidades. Sem o flag, o CLI mantém os pipelines anteriores.

Use para cadastro, criação de projeto ou diagnóstico do ambiente. Para estratégia e conteúdo, use `marketing-os`; para retomar produção solicitada, `pipeline-operator`.

Extraia nome, cliente, tipo e formato da conversa e dos arquivos existentes. Pergunte somente pelo que impede a criação correta. Use os scripts a partir da raiz:

```bash
python3 scripts/setup-project.py new-client --name "Nome"
python3 scripts/setup-project.py new-project --client slug --type marketing --name "campanha"
python3 scripts/setup-project.py new-project --client slug --type video --name "tema" --formato 16:9
python3 scripts/setup-project.py new-project --client slug --type video --name "motion" --formato 16:9 --compositor hyperframes --no-activate
python3 scripts/setup-project.py check-env
```

Tipos: `marketing`, `gravado`, `carrossel`, `video` e `video-dialogo`. Marketing usa `multi`; mídia exige proporção concreta. Ao cadastrar cliente, o script cria `config.json` (identidade e operação), `brand-context.md`, `aprendizados.md` e `branding.json` a partir de `templates/`. Preencha o brand-context com o método da skill `marketing-os`, sem criar outros arquivos de identidade, e confira com `python3 scripts/validar_cliente.py --client {slug}`.

`new-project` atualiza `_ativo` por padrão. Para peça vinculada a campanha ou trabalho que deva preservar o ativo, acrescente `--no-activate`. A ligação entre campanha e peça fica nos briefs conforme [operações](../marketing-os/references/operations.md).

Arquive apenas quando solicitado, usando `python3 scripts/setup-project.py archive --client slug --project nome-do-projeto`. Preserve dados e referências.

Não instale dependências como rotina. `check-env` é para diagnóstico solicitado ou erro que indique dependência ausente; consulte as dependências por fase em `MANUAL.md`. O diagnóstico legado lista todas as integrações; confira apenas as usadas no projeto.
