---
name: transcribe
description: Transcreve gravações e narração com whisper-cpp local, produzindo texto e timestamps.
---

# transcribe

Use `workflows/transcribe/scripts/transcribe.py`. Leia [comandos e dependências](references/commands.md) conforme o input. O projeto usa whisper-cpp; não substitua por openai-whisper.

Preserve o áudio/vídeo original e salve a transcrição no projeto. Revise erros relevantes ao pedido e atualize `pipeline.transcrever` mantendo strings ou objetos existentes.
