---
name: render
description: Compõe e exporta vídeos com HyperFrames como padrão para novas composições; preserva Remotion, FFmpeg e FCPXML existentes.
---

# render

Escolha pelo resultado solicitado e pelos inputs disponíveis.

- Novas composições com motion, interfaces, diagramas e montagem visual: [integração HyperFrames](references/hyperframes.md). Direção artística: [direção](references/direcao-artistica.md).
- Projeto existente: preserve o motor e o brief; migração apenas quando solicitada. Montagem simples continua em FFmpeg.
- Manifest, animatic e Remotion: [Remotion](references/remotion.md). Para editar código Remotion, leia [a skill oficial do Remotion](https://github.com/remotion-dev/skills).
- Montagem simples: [FFmpeg](references/assembly.md), script `workflows/render/scripts/assemble.py`.
- Edição manual e paths de sandbox: [DaVinci](references/davinci.md).

Um preview é a entrega quando solicitado; um render final deve seguir até o arquivo final dentro do escopo aprovado. Atualize a fase existente (`compor`, `fcpxml` ou outra já usada), preservando seu schema. Não exija edit_decisions de um vídeo gerado cujo input já seja manifest ou storyboard.
