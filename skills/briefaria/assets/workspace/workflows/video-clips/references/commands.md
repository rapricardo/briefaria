## Pre-requisitos

- `FAL_KEY` como variavel de ambiente
- Keyframes gerados na pasta `imagens/` (via skill `imagen`)
- `video-spec.json` na pasta de producao do projeto

## Modos de Operacao

```bash
# 1. DRY-RUN — visualiza payloads sem gastar creditos
python workflows/video-clips/scripts/fal_video.py dry-run \
    --spec clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/video-spec.json \
    --images-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/

# 2. SINGLE — gera 1 clip especifico
python workflows/video-clips/scripts/fal_video.py single \
    --spec clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/video-spec.json \
    --job-id clip_02 \
    --images-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/ \
    --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/clips/

# 3. BATCH — gera todos os clips em sequencia
python workflows/video-clips/scripts/fal_video.py batch \
    --spec clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/video-spec.json \
    --images-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/ \
    --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/clips/
```

### from-manifest — Gera clips do manifest.json

```bash
python workflows/video-clips/scripts/fal_video.py from-manifest \
    --manifest clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/manifest.json \
    --images-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/ \
    --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/clips/ \
    [--dry-run]
```

### single-beat — Gera 1 clip de beat especifico

```bash
python workflows/video-clips/scripts/fal_video.py single-beat \
    --manifest clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/manifest.json \
    --beat-id cena_01a \
    --images-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/ \
    --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/clips/
```

## Engine de Video — flag CLI

Flag global `--engine {gemini-omni,veo,kling,kling-v3,happy-horse,seedance,seedance-fast}` (sem default fixo — usa spec ou cai em `gemini-omni`):

```bash
# Sem --engine: usa default_settings.engine do spec (ou gemini-omni se ausente)
python fal_video.py batch --spec video-spec.json --images-dir imagens/

# Override de sessao: roda TUDO como veo (mais barato)
python fal_video.py --engine veo batch --spec video-spec.json --images-dir imagens/

# Override de sessao: roda TUDO como seedance (jobs com job.engine ainda vencem)
python fal_video.py --engine seedance batch --spec video-spec.json --images-dir imagens/

# Seedance Fast — mesma qualidade, ~20% mais barato
python fal_video.py --engine seedance-fast batch --spec video-spec.json --images-dir imagens/

# Kling v3 Pro — cinematico, audio nativo, negative_prompt
python fal_video.py --engine kling-v3 batch --spec video-spec.json --images-dir imagens/

# Kling classico (retrocompat) — clips de 5s sem audio
python fal_video.py --engine kling batch --spec video-spec.json --images-dir imagens/
```
