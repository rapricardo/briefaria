---
status: vigente
data: 2026-11-05
proposito: Integrar HyperFrames sem duplicar contexto, estado ou ferramentas.
---
# Composição HyperFrames

HyperFrames é o padrão de novas composições visuais.

## Responsabilidades

- `pipeline-operator`: projeto, estado e fases solicitadas.
- `render`: motor. HyperFrames é padrão de novas composições visuais; preserve motores existentes.
- `hyperframes`: workflow, contrato técnico e Studio. Leia a skill antes de compor.
- Scripts existentes: transcrição, cortes, imagens, narração e clips. Reutilize assets disponíveis.
- FFmpeg: processamento/montagem simples. Remotion: projetos existentes ou pedido explícito. DaVinci: finalização solicitada.

## Contexto e arquivos

1. Leia brief vigente, status e contexto do cliente. Marca vem de `brand-context.md` e `branding.json`.
2. Composição em `composition/` dentro do projeto. Estudos em subpastas próprias; preserve a versão aprovada.
3. `BRIEF.md` do HyperFrames contém campos técnicos e referências ao brief e à marca. Não repetir pesquisa, estratégia ou perguntas respondidas.
4. Direção fica no storyboard/design da composição. Campanha referencia a peça, sem copiar decisões.
5. Revisão no Studio: nota com tempo, elemento e mudança. Registrar decisões no documento existente da peça; não criar outro editor ou fila.
6. Exportar para `render/`. Atualizar somente fases/outputs executados e o `session-log.md` existente.

## Compatibilidade

Preserve schemas, IDs e fases existentes. Crie novos projetos com `setup-project.py new-project --compositor hyperframes`: vídeo/vídeo-diálogo usa `roteiro → assets → compor → publicar`; gravado preserva seu pipeline. Acrescente fases de geração apenas quando necessárias. Sem o flag, o CLI mantém os pipelines anteriores. Marketing e carrossel rejeitam esse flag. Não simular conclusão nem alterar projetos em lote. O preflight aceita `--fase compor`; leia o pipeline real do projeto.

Consumidores conferidos: `setup-project.py` cria estado; `preflight.py` percorre as fases reais e reconhece `assets`/`compor`; `pipeline-operator` lê estado; renderizadores existentes continuam recebendo seus manifests. Não acrescentar campo de engine ao schema compartilhado.

Não converter manifest Remotion em contrato universal. HyperFrames mantém arquivos nativos; assets continuam locais ao projeto com origem registrada. Sem serviço, banco ou sistema de plugins para ligar CLI e arquivos.

## Especializações sob demanda

- Argo: captura real em navegador; entrega gravação/timing, sem duplicar narração ou exportação.
- Earshot: seleção, geração e medição de som. Mixagem no HyperFrames; score não aprova gosto.
- Reanimate: estudo de referência escolhida, sem comparação pixel a pixel obrigatória.
- Explainroo, huashu-motion, take-one, video-director e rossark: referências de direção, sem instalar workflows/renderizadores paralelos.

Instale ferramentas especializadas quando utilizadas. Preserve licenças ao incorporar código; referência não autoriza copiar mídia dos exemplos.

## Instalação e comandos

Siga a [documentação do HyperFrames](https://github.com/heygen-com/hyperframes) para instalar
as skills complementares no agente. O motor usa Node.js 22+, FFmpeg e Chrome. Verifique com `npx hyperframes doctor`. Inicialize na pasta de produção com
`npx hyperframes init composition --non-interactive` se ela ainda estiver vazia. Na
pasta da composição, use:

```bash
npx hyperframes lint
npx hyperframes preview
npx hyperframes render --output ../render/final.mp4
```
