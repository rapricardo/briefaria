# Operar a Briefaria

Use Python 3.11+ no macOS ou Linux. Execute os comandos a partir deste workspace. Estratégia, organização de campanhas e autoria usam o agente em que a skill foi instalada. Dependências de mídia são por fase.

## Primeiro cliente

```bash
python3 scripts/setup-project.py new-client --name "Estúdio Exemplo"
python3 scripts/implantacao.py --client estudio-exemplo
python3 scripts/validar_cliente.py --client estudio-exemplo
python3 scripts/setup-project.py new-project --client estudio-exemplo \
  --type marketing --name "campanha de demonstração"
```

Preencha mandato, contexto e branding com informações da marca. O validador indica campos de exemplo ainda pendentes. A implantação lista o próximo passo liberado.

## Da campanha à peça

| Objetivo | Workflow |
|---|---|
| Diagnóstico, posicionamento, conteúdo, campanhas e aprendizado | [Marketing](workflows/marketing-os/WORKFLOW.md) |
| Ideação, mapa de teses e crítica independente | [Fila de decisão](sistema/README.md) |
| Slides com imagens geradas | [Carrossel](workflows/imagen/references/carousel.md) |
| Cortar e compor uma gravação | [Transcrição](workflows/transcribe/WORKFLOW.md), [cortes](workflows/edit/WORKFLOW.md), [render](workflows/render/WORKFLOW.md) |
| Vídeo novo, animado ou gerado por IA | [Operação de produção](workflows/pipeline-operator/WORKFLOW.md), [render](workflows/render/WORKFLOW.md) |
| Carrossel pronto para Instagram | [Distribuição](workflows/marketing-os/references/distribution.md) |

Para novas composições use `--compositor hyperframes` com tipos `gravado`, `video` ou `video-dialogo`. Para vídeo gerado com narração e FCPXML, crie o tipo `video` sem esse flag. `carrossel` usa seu próprio fluxo. Use `--no-activate` para peças vinculadas a uma campanha ativa. Para a fila de ideias, rode `bash scripts/novo-projeto-ideacao.sh estudio-exemplo descricao`.

```bash
python3 scripts/preflight.py --project "clientes/estudio-exemplo/producao/<projeto>" --all
```

Acompanhe fases e outputs pelo `status.json` do projeto e decisões pelo brief e `session-log.md`.

## Dependências por fase

| Fase | Instalação ou credencial |
|---|---|
| Cortes, montagem simples e áudio | FFmpeg e ffprobe no PATH |
| Transcrição local | FFmpeg, [whisper.cpp](https://github.com/ggml-org/whisper.cpp) e um modelo em `models/` |
| HyperFrames | Node.js 22+, FFmpeg e Chrome. Use `npx hyperframes doctor` |
| Remotion | Node.js e `npm ci --prefix remotion`. Use os assets do seu projeto |
| Imagens | `GEMINI_API_KEY` (padrão), `FAL_KEY` ou `GLM_API_KEY`/`ZAI_API_KEY`, conforme o backend |
| Clips gerados | `FAL_KEY` |
| Narração e efeitos separados | `ELEVENLABS_API_KEY` |
| Hospedagem R2 | [uv](https://docs.astral.sh/uv/getting-started/installation/) e credenciais do bucket |
| Publicador Instagram | App Meta, conta profissional e credenciais dessa conta |

Para mídia gerada, copie `.env.example` para `.env` e preencha as chaves que o fluxo usa. Configure um ID de voz do seu catálogo no ElevenLabs. Para usar o importador ClickUp do gerador de imagens, defina `CLICKUP_TOKEN` e `CLICKUP_BRANDING_FIELDS` com um objeto JSON que mapeia IDs de campos do seu workspace para chaves de branding. Os arquivos de marca locais funcionam com `--branding-file`.

Exemplo de instalação local do whisper no macOS e de download do modelo médio:

```bash
brew install ffmpeg whisper-cpp
curl -fL https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin \
  -o models/ggml-medium.bin
```

No Linux, instale FFmpeg pelo gerenciador da distribuição e siga as instruções de compilação do whisper.cpp ou use `python3 scripts/setup-sandbox.py --skip-remotion --model medium` em um ambiente compatível. Você pode escolher outro modelo com `--model` ao transcrever. Use `--no-gpu` em ambientes sem acesso à GPU.

O arquivo `sistema/fila/_ledger.md` começa vazio. Trate arquivos em `clientes/`, na fila e nas credenciais como dados da sua operação.
