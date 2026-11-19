## Engines suportadas

| Engine | Endpoint | $/8s (aprox.) | Duracao | Audio | end_frame | Aspect | Forte em |
|--------|----------|------|---------|-------|-----------|--------|----------|
| `gemini-omni` (default) | `google/gemini-omni-flash/image-to-video` | ~$1.04 (720p, $0.13/s) | 3-10s (int) | nativo (ambient + fala, gerado automatico) | nao | 16:9 / 9:16 | modelo mais recente, image-to-video com audio nativo grounded no Gemini |
| `veo` | `fal-ai/veo3.1/lite/image-to-video` | $0.40 | 4/6/8s | ambient + fala (dialogue) | nao | 16:9 / 9:16 | mais barato, PT-BR validado, dialogue confiavel |
| `kling` | `fal-ai/kling-video/{o3,v2.5}/...` | $1.00-1.40 (5s) | 5s fixo | nao | sim (O3) | 16:9 | B-roll silencioso, start_end_frame legado |
| `kling-v3` | `fal-ai/kling-video/v3/pro/image-to-video` | ~$0.90-1.57 (audio off/on) | 3-15s (int) | nativo (musica+SFX+fala), so EN/CN nativo | sim | fixo (nao configuravel) | cinematico, unica engine com `negative_prompt` nativo, ate 15s |
| `happy-horse` | `fal-ai/alibaba/happy-horse/image-to-video` | $1.12 (720p) / $2.24 (1080p) | 3-15s | nativo + lip-sync | nao | livre (segue imagem) | lip-sync EN/JP/CN/etc, durações longas (>8s) |
| `seedance` | `fal-ai/bytedance/seedance-2.0/image-to-video` | $2.42 (720p Std) | 4-15s ou `auto` | nativo (musica+SFX+fala) | sim | 7 opcoes | transicoes start→end, direcao de camera, hero shots |
| `seedance-fast` | `bytedance/seedance-2.0/fast/image-to-video` | ~$1.94 (720p, ~20% mais barato) | 4-15s ou `auto` | nativo (musica+SFX+fala) | sim | 7 opcoes | mesma qualidade do Seedance por menos, mas so 480p/720p (sem 1080p) |

**Atencao (gemini-omni):** dialogue/lip-sync via prompt-injection segue o mesmo padrao de Veo/Happy Horse/Seedance (`vo`, `voice`, `sfx`, `ambient`), mas esse comportamento **ainda nao foi validado** neste projeto — a documentacao publica do fal.ai nao confirma suporte a lip-sync nem idiomas. Testar com `single` em 1 clip antes de rodar `batch`, especialmente para PT-BR.

**Atencao (kling-v3) — CRÍTICO para PT-BR:** o audio nativo (dialogue/musica/SFX) e documentado oficialmente so em chines e ingles — **outros idiomas, incluindo portugues, sao auto-traduzidos para ingles pelo proprio modelo**. Isso e diferente do "nao documentado" das outras engines: aqui a fala pode literalmente sair em ingles mesmo com `vo`/`voice` escritos em PT-BR. NAO usar `type: dialogue` com `kling-v3` em producao sem validar 1 clip primeiro — para b-roll silencioso/`single_frame` sem fala, o risco nao se aplica.

**Atencao (happy-horse/seedance/seedance-fast):** NAO tem PT-BR documentado nas linguas de lip-sync. Testar com 1 clip antes de batch em PT.

## Como escolher engine

Definir em 3 lugares (ordem de prioridade):

1. **`job.engine`** no video-spec.json — override por shot (mais especifico)
2. **`--engine` no CLI** — override de sessao (quando passado explicitamente)
3. **`default_settings.engine`** no video-spec.json — default do projeto
4. Fallback: `"gemini-omni"`

Regra de bolso:
- **Default novo projeto:** `gemini-omni` (modelo mais recente, audio nativo)
- **Prioridade de custo:** `engine: "veo"` no default_settings (mais barato, ~$0.40/8s vs ~$1.04/8s do gemini-omni)
- **Shot com transicao start→end:** `engine: "seedance"` (ou `seedance-fast` para economizar) no job
- **Shot que precisa >8s sem cortar:** `engine: "happy-horse"`, `engine: "seedance"` ou `engine: "kling-v3"` (ate 15s) no job
- **Shot com direcao de camera complexa** (dolly zoom, POV switch): `engine: "seedance"` no job
- **Precisa de `negative_prompt` de verdade** (excluir elementos visuais especificos): `engine: "kling-v3"` — unica engine que suporta nativamente
- **Seedance mas com orcamento apertado:** `engine: "seedance-fast"` — mesma qualidade, ~20% mais barato, so nao suporta 1080p
- **Mistura permitida:** o batch processa cada job com sua engine

## Tipos de Job

### Gemini Omni Flash (--engine gemini-omni, padrao)

| Tipo | Endpoint fal.ai | Duracao | Audio |
|------|-----------------|---------|-------|
| `single_frame` / `action` / `broll` | `google/gemini-omni-flash/image-to-video` | 3-10s (inteiro) | ambiente (gerado automaticamente) |
| `dialogue` | `google/gemini-omni-flash/image-to-video` | 3-10s (inteiro) | fala + ambiente via prompt-injection (nao validado — ver aviso acima) |

Campos do payload:
| Campo | Obrigatorio | Descricao |
|-------|-------------|-----------|
| `prompt` | sim | Descricao visual: cinematografia + sujeito + acao + contexto + estilo |
| `image` | sim | Keyframe (resolvido para `image_url`) |
| `duration` | nao | Inteiro 3-10, default 8. O script clipa para o range valido |
| `aspect_ratio` | nao | `16:9` (default) ou `9:16` — qualquer outro valor cai para `16:9` |

**Sem `resolution`, `negative_prompt`, `seed` ou `end_image_url`** — nao documentados pelo fal.ai para este modelo.
**Audio** e gerado automaticamente pelo modelo (nao ha flag `generate_audio`), assim como no Veo.

### Tipo `dialogue` — campos do job (Gemini Omni Flash / Veo / Happy Horse / Seedance)

O tipo `dialogue` monta o prompt automaticamente com as camadas de audio:

| Campo | Obrigatorio | Descricao |
|-------|-------------|-----------|
| `prompt` | sim | Descricao visual: cinematografia + sujeito + acao + contexto + estilo |
| `vo` | sim | Texto falado pelo personagem |
| `voice` | recomendado | Descricao da voz para consistencia (tom, faixa, sotaque). Ex: `"in a deep, authoritative baritone"` |
| `sfx` | nao | Efeitos sonoros. Ex: `"leather chair creaking, pen tapping"` |
| `ambient` | nao | Ambiente sonoro. Ex: `"quiet executive office hum"` |
| `image` | sim | Keyframe PNG |
| `duration` | nao | Depende da engine (ver tabelas acima) |

O script monta o prompt final assim:
```
[prompt visual]

The character says [voice], "[vo]"
SFX: [sfx]
Ambient noise: [ambient]
```

**Para consistencia de voz**: usar a MESMA string `voice` em todos os jobs do mesmo personagem. A string vem do campo `voz_veo` do personagem em `clientes/{slug}/assets/characters.json` — nunca inventar de memoria. Descrever tom (deep, soft, raspy), faixa (baritone, tenor, alto), ritmo (measured, rapid) e sotaque.

**Regras visuais para dialogue (CRITICO):**
- **1 personagem por clip**: cenas com 2+ personagens visiveis confundem a engine sobre quem fala — o audio fica dividido entre os personagens. SEMPRE usar single shot de quem fala; se a cena pede dois, mostrar apenas quem fala e referenciar o outro no prompt (`"speaking to someone off-camera"`).
- **Sem `negative_prompt`** nas engines que nao suportam (Veo rejeita com erro 422; so `kling-v3` aceita nativamente). Para evitar musica, incluir `No background music, only dialogue and ambient sounds` no prompt visual.

**Formula do prompt visual (guia oficial Veo 3.1):**
```
[Cinematografia] + [Sujeito] + [Acao] + [Contexto] + [Estilo & Ambiencia]
```

### Veo (--engine veo, alternativa mais barata)

| Tipo | Endpoint fal.ai | Duracao | Audio |
|------|-----------------|---------|-------|
| `single_frame` / `action` / `broll` | `fal-ai/veo3.1/lite/image-to-video` | 4s, 6s ou 8s | ambiente |
| `dialogue` | `fal-ai/veo3.1/lite/image-to-video` | 4s, 6s ou 8s | fala + ambiente |

A duracao e configuravel por job (`"duration": 6`) ou via `default_settings.duration`. O script arredonda para o valor Veo valido mais proximo (4, 6 ou 8).

### Kling (--engine kling)

| Tipo | Endpoint fal.ai | Duracao | Audio |
|------|-----------------|---------|-------|
| `start_end_frame` / `interpolation` | `fal-ai/kling-video/o3/standard/image-to-video` | 5s | nao |
| `single_frame` / `action` / `broll` | `fal-ai/kling-video/v2.5-turbo/pro/image-to-video` | 5s | nao |
| `lipsync` | `fal-ai/kling-video/lipsync/audio-to-video` | variavel | nao |

Override de modelo: `--model <endpoint>` aplica o mesmo endpoint a todos os jobs.

### Kling v3 Pro (--engine kling-v3)

| Tipo | Endpoint fal.ai | Duracao | Audio |
|------|-----------------|---------|-------|
| `single_frame` / `action` / `broll` / `dialogue` / `start_end_frame` | `fal-ai/kling-video/v3/pro/image-to-video` | 3-15s (inteiro) | nativo (musica+SFX+fala), so EN/CN documentado |

Campos do payload:
| Campo | Obrigatorio | Descricao |
|-------|-------------|-----------|
| `prompt` | sim | Descricao do movimento. Em `dialogue`, inclui fala via prompt-injection |
| `image` | sim (para single_frame/dialogue) | Keyframe inicial — **enviado como `start_image_url`, nao `image_url`** (unica engine com essa diferenca) |
| `start_image` + `end_image` | sim (para start_end_frame) | Frame inicial e final para transicao |
| `duration` | nao | Inteiro `"3"`...`"15"`, default `"5"` |
| `negative_prompt` | nao | **Unica engine do projeto que suporta nativamente.** Default da API: `"blur, distort, and low quality"` |
| `cfg_scale` | nao | Float, controla forca de aderencia ao prompt (default API: `0.5`) |
| `generate_audio` | nao | `true` (default) — audio nativo |

**Sem `resolution`/`aspect_ratio` configuraveis** — output fixo, nao documentados como parametros.
**Recursos avancados nao implementados no script:** `multi_prompt` (ate 6 shots em 1 clip), `elements` (personagem/objeto de referencia via `@Element1`), `shot_type`. Se precisar deles, adicionar manualmente ao payload ou pedir para expandir `_build_kling_v3_payload`.
**PT-BR em dialogue:** ver aviso critico na secao "Engines suportadas" acima — audio nativo so documentado em EN/CN, outros idiomas sao auto-traduzidos para ingles.

### Happy Horse (--engine happy-horse)

| Tipo | Endpoint fal.ai | Duracao | Audio |
|------|-----------------|---------|-------|
| `single_frame` / `action` / `broll` / `dialogue` | `fal-ai/alibaba/happy-horse/image-to-video` | 3-15s (inteiro) | nativo + lip-sync |

Campos do payload:
| Campo | Obrigatorio | Descricao |
|-------|-------------|-----------|
| `prompt` | sim (mas opcional na API — passamos sempre) | Descricao da animacao. Em `dialogue`, inclui fala via prompt-injection |
| `image` | sim | Keyframe (resolvido para `image_url`) |
| `duration` | nao | Inteiro 3-15, default 5. Aceita valores fora do range — sao clipados |
| `resolution` | nao | `720p` (default) ou `1080p` |
| `seed` | nao | Inteiro 0-2147483647 para reproducibilidade |

**Sem `aspect_ratio`** — a saida segue o aspect ratio da imagem de entrada (input deve ter aspecto entre 1:2.5 e 2.5:1, min 300px, max 10MB).
**Sem `negative_prompt`** — usar instrucoes positivas no prompt.

### Seedance (--engine seedance)

| Tipo | Endpoint fal.ai | Duracao | Audio |
|------|-----------------|---------|-------|
| `single_frame` / `action` / `broll` / `dialogue` / `start_end_frame` | `fal-ai/bytedance/seedance-2.0/image-to-video` | 4-15s ou `auto` | nativo (musica+SFX+lip-sync) |

Campos do payload:
| Campo | Obrigatorio | Descricao |
|-------|-------------|-----------|
| `prompt` | sim | Descricao do movimento. Em `dialogue`, inclui fala via prompt-injection |
| `image` | sim (para single_frame/dialogue) | Keyframe inicial |
| `start_image` + `end_image` | sim (para start_end_frame) | Frame inicial e final para transicao |
| `duration` | nao | `"auto"` (default), `"4"`...`"15"` |
| `resolution` | nao | `480p`, `720p` (default) ou `1080p` |
| `aspect_ratio` | nao | `auto` (default), `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` |
| `generate_audio` | nao | `true` (default) — audio nativo. Setar `false` so se quiser silencio (mesmo assim, audio vem incluso gratuito) |
| `seed` | nao | Inteiro para reproducibilidade |

**Sem `negative_prompt`** — usar instrucoes positivas no prompt.

### Seedance Fast (--engine seedance-fast)

Mesmo schema do Seedance padrao (ver acima), com duas diferencas:

| Campo | Diferenca vs Seedance padrao |
|-------|-------------------------------|
| `resolution` | So `480p` ou `720p` — o script clipa automaticamente para `720p` se pedir `1080p` |
| `bitrate_mode` | Novo campo opcional: `"standard"` (default) ou `"high"` |
| `seed` | **Nao enviado** — nao documentado como input aceito pelo endpoint fast (o script ignora esse campo mesmo se presente no job) |

Mesma qualidade visual do Seedance padrao, ~20% mais barato, latencia menor. Use quando nao precisar de 1080p.
