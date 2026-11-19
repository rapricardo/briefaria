## Timing: storyboard vs clips (extensions)

O storyboard tem duracoes variaveis; cada engine tem um range nativo (ver tabela de engines). Shots mais longos que a duracao nativa precisam de **extension** — um segundo clip que continua o shot:

1. **Gerar imagem NOVA com angulo diferente** via imagen.py — overhead, low angle, close-up, etc.
2. **Depois** gerar o clip de extension a partir da imagem nova
3. **NUNCA** reenviar a mesma imagem com prompt diferente — a engine so anima a imagem que recebe, nao muda o angulo. Sem imagens duplicadas em jobs diferentes.

## Impacto no Pipeline

Com Gemini Omni Flash ou Veo (clips com audio nativo, sem necessidade de SFX externo):
- **Extensions**: maioria dos shots (3-8s) nao precisa de extension (Kling precisava a partir de 5s)
- **SFX**: clips ja vem com audio ambiente — fase `sfx` pode ser marcada `skip` no status.json
- **FCPXML**: usar `--clip-duration 8 --has-clip-audio --skip-sfx` no storyboard_to_fcpxml.py

## video-spec.json Esperado

```json
{
    "project": "nome_do_projeto",
    "default_settings": {
        "engine": "gemini-omni",
        "duration": 8,
        "aspect_ratio": "9:16"
    },
    "jobs": [
        {
            "id": "clip_01",
            "type": "single_frame",
            "image": "shot_01.png",
            "prompt": "slow zoom in on subject in office, warm light"
        },
        {
            "id": "clip_02",
            "type": "dialogue",
            "image": "shot_02.png",
            "prompt": "medium shot of CEO",
            "vo": "Vamos bater essa meta.",
            "voice": "in a deep baritone with a São Paulo accent",
            "sfx": "leather chair creaking",
            "ambient": "quiet office hum"
        },
        {
            "id": "clip_03_transition",
            "type": "start_end_frame",
            "engine": "seedance",
            "start_image": "shot_03_start.png",
            "end_image": "shot_03_end.png",
            "prompt": "dolly zoom from wide to close-up",
            "duration": 6
        },
        {
            "id": "clip_04_long",
            "type": "single_frame",
            "engine": "happy-horse",
            "image": "shot_04.png",
            "prompt": "character walking through corridor",
            "duration": 12,
            "resolution": "1080p"
        },
        {
            "id": "clip_05_cinematic",
            "type": "single_frame",
            "engine": "kling-v3",
            "image": "shot_05.png",
            "prompt": "hero shot of product on marble surface, cinematic lighting",
            "duration": 10,
            "negative_prompt": "blur, distort, low quality, watermark",
            "cfg_scale": 0.6
        },
        {
            "id": "clip_06_cheap_seedance",
            "type": "single_frame",
            "engine": "seedance-fast",
            "image": "shot_06.png",
            "prompt": "slow pan across factory floor"
        }
    ]
}
```

**Campo `engine` por job:** opcional. Sobrescreve `default_settings.engine` apenas para aquele shot.
**Campos especificos por engine** (`resolution`, `aspect_ratio`, `generate_audio`, `seed`, `negative_prompt`, `cfg_scale`, `bitrate_mode`): tambem podem ser definidos no `default_settings`.

## Saida

Clips salvos como `{job_id}.mp4` na pasta `--output-dir` (default: `clips/` ao lado do spec).
