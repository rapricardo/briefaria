---
name: pipeline-operator
description: Retoma e executa fases de produção de mídia usando o status do projeto e os scripts existentes.
---

# Operação de produção

Novas composições seguem a integração HyperFrames indicada em `render`. Reutilize brief, marca e assets; não reabra descoberta. Leia as fases reais do status; nem todo vídeo exige imagens geradas, clips ou DaVinci.

Use quando o pedido envolve executar ou retomar produção. Leia o status e o trecho recente do session-log do projeto indicado. Se houver correção recente, use o estado corrigido. Não troque de cliente ou avance uma campanha diferente por existir `_ativo`.

Execute `python3 scripts/preflight.py --project <path> --fase <fase>` antes da fase. Consulte [contratos de estado](../marketing-os/references/operations.md) para strings e objetos. `in_progress`/`running` não significam concluído. Preserve metadata ao atualizar estado.

| Trabalho | Skill e contrato |
|---|---|
| Roteiro para vídeo | [vídeo](../video-script/WORKFLOW.md) |
| Transcrever | [transcribe](../transcribe/WORKFLOW.md) |
| Cortes e EDL | [edit](../edit/WORKFLOW.md) |
| Carrossel, personagens e storyboard | [imagen](../imagen/WORKFLOW.md) |
| Narração separada | [voiceover](../voiceover/WORKFLOW.md) |
| Efeitos separados | `python3 scripts/generate_sfx.py --help` |
| Clips | [video-clips](../video-clips/WORKFLOW.md) |
| Distribuição | [publicação](../marketing-os/references/distribution.md) |
| Composição HyperFrames, montagem, Remotion e FCPXML | [render](../render/WORKFLOW.md) |

Use os scripts da fase para gerar mídia. Investigue falhas e corrija inputs ou bugs dentro do escopo autorizado. Não substitua scripts existentes por comandos improvisados nem instale alternativas ao whisper-cpp.

Antes de keyframes de storyboard, rode `python3 scripts/validate-storyboard.py --spec <storyboard.json>`; resolva erros de schema, timing e referências. Para review visual solicitado ou gate já acordado, use `scripts/generate_storyboard_review.py`. Não acrescente aprovação humana a cada etapa.

Ao concluir, confira o output necessário, atualize apenas a fase afetada e registre com `scripts/session_log.py`. Preserve recordings e assets. Publicação e novas despesas fora da autorização continuam sendo decisões do usuário.
