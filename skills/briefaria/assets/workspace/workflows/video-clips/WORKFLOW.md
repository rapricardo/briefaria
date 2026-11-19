---
name: video-clips
description: Gera clips a partir de keyframes e video-spec.json usando as engines disponíveis no projeto.
---

# video-clips

Script mantido: `workflows/video-clips/scripts/fal_video.py`.

- Planejar engine e campos dos jobs: [engines](references/engines.md).
- Executar single, batch, dry-run ou manifest: [comandos](references/commands.md).
- Criar video-spec e dimensionar duração: [spec](references/spec.md).

Preserve engine já definida e o formato do projeto. Custos e suporte citados nas referências são estimativas históricas; confirme informação atual quando afetar a escolha ou o gasto. Para dialogue, preserve voz e personagem e os limites da engine escolhida.

Atualize `pipeline.clips` no formato existente: `in_progress` ao iniciar, `done` após os outputs esperados. Se falhar, registre a falha e preserve os clips concluídos para retomada.
