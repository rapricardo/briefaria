---
name: voiceover
description: Gera narração com ElevenLabs para roteiros que precisam de áudio separado.
---

# voiceover

Use a fase `voiceover` nos novos projetos `video`; projetos com diálogo integrado não precisam desta etapa. Leia texto final e voz aprovada. Script mantido: `workflows/voiceover/scripts/elevenlabs_vo.py`.

[Comandos e formatos](references/commands.md) descreve `full`, `from-script`, `per-act` e `per-beat`. Escolha conforme o input existente, sem converter o projeto para outro schema.

Salve o output em `audio/`. Atualize `pipeline.voiceover` apenas após gerar o áudio solicitado. Em projeto legado com fase `audio`, preserve essa chave. Em objetos de fase, altere apenas `status` e campos de output pertinentes.
