# Skill: Render (Remotion)

Composicao programatica de video a partir de assets (imagens, audio, clips). Remotion monta a timeline em React e renderiza MP4 via ffmpeg.

## Quando usar

- Fase `compor` esta pendente no `status.json` da producao
- Designer pede preview (animatic) ou render final do video
- Assets ja existem: keyframes em `imagens/`, audio em `audio/`, clips em `clips/`

## Pre-requisitos

- Node.js >= 18 e dependencias do Remotion instaladas (`cd remotion && npm install`)
- Manifest existente; edit_decisions somente quando o projeto usar edição de gravação
- Assets referenciados no manifest devem existir nos paths indicados

## Compositions disponiveis

### Animatic (preview rapido)

- **ID:** `Animatic`
- **Modo:** `animatic`
- Visual: keyframes estaticos com efeito Ken Burns (zoom lento 1x -> 1.08x)
- Audio: narracoes e SFX sobrepostos
- Legendas: exibidas sobre o video
- **Uso:** validar timing, sequencia de cenas e narrativa antes de gerar clips finais
- **Tempo de render:** segundos (nao depende de APIs externas)

### Final (render completo)

- **ID:** `Final`
- **Modo:** `final`
- Visual: clips de video gerados (via video-clips) quando disponiveis; fallback para keyframes com Ken Burns
- Audio: narracoes (exceto em beats com lipsync, onde o audio ja esta no clip)
- Legendas: exibidas sobre o video
- **Uso:** exportacao final para publicacao
- **Tempo de render:** depende da duracao e resolucao

## Estrutura de dados

### Manifest (manifest.json)

Arquivo central que descreve o projeto. Pode vir de edit_decisions em gravações ou do planejamento em vídeos gerados.

```json
{
  "project": "nome-do-projeto",
  "client": "slug-do-cliente",
  "branding_file": "../../../branding.json",
  "settings": {
    "fps": 30,
    "width": 1080,
    "height": 1920,
    "duration_total_s": 33
  },
  "characters": {
    "oli": { "voice_id": "abc123", "role": "narrador" }
  },
  "scenes": [
    {
      "id": "S01",
      "act": 1,
      "duration_s": 5,
      "beats": [
        {
          "id": "S01-B01",
          "duration_s": 5,
          "type": "scene",
          "visual": "Descricao visual do beat",
          "keyframes": ["imagens/S01-B01.png"],
          "who": "oli",
          "audio_text": "Texto narrado",
          "audio_file": "audio/S01-B01.mp3",
          "clip_file": "clips/S01-B01.mp4",
          "caption": "Legenda exibida",
          "video_job": {
            "type": "lipsync",
            "api": "kling",
            "prompt": "..."
          }
        }
      ]
    }
  ],
  "sfx": [
    {
      "id": "sfx-01",
      "description": "som ambiente",
      "file": "audio/sfx-01.mp3",
      "attach_to": "S01-B01"
    }
  ]
}
```

### Tipos de beat

| Tipo | Descricao |
|------|-----------|
| `scene` | Cena principal com personagem |
| `broll` | Imagem/video de cobertura |
| `metafora` | Representacao visual de conceito |
| `pausa` | Momento de respiro, silencio |
| `dado` | Dado/estatistica em destaque |

### Tipos de video_job

| Tipo | Descricao |
|------|-----------|
| `lipsync` | Sincronizacao labial (audio embutido no clip) |
| `interpolation` | Transicao entre 2 keyframes |
| `action` | Movimento a partir de 1 keyframe |
| `broll` | Clip de cobertura |

### Branding (resolvido do branding.json do cliente)

```json
{
  "colors": {
    "verde_escuro": "#2B4A2E",
    "creme": "#F6F1EB",
    "dourado": "#C4975A"
  },
  "fonts": {
    "display": "Instrument Serif",
    "body": "DM Sans"
  }
}
```

### Timeline (gerada automaticamente)

Array de `BeatTimeline` calculado pelo `resolve-manifest.js`:

```json
[
  { "beatId": "S01-B01", "startFrame": 0, "durationInFrames": 150 },
  { "beatId": "S01-B02", "startFrame": 150, "durationInFrames": 90 }
]
```

## Paths de producao

```
clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/
  manifest.json
  imagens/          # Keyframes (.png)
  audio/            # Narracoes e SFX (.mp3)
  clips/            # Clips de video gerados (.mp4)
  render/
    animatic.mp4    # Preview rapido
    final/
      final_YYYYMMDD.mp4  # Render final
```

## Comandos

### Via script render.sh (recomendado)

```bash
# Animatic (preview)
# Na raiz do workspace
./remotion/scripts/render.sh animatic clientes/{slug}/producao/{projeto}/manifest.json

# Final
./remotion/scripts/render.sh final clientes/{slug}/producao/{projeto}/manifest.json

# Output customizado
./remotion/scripts/render.sh animatic manifest.json /tmp/preview.mp4
```

O script:
1. Cria symlink `remotion/public/prod` -> pasta de producao
2. Executa `resolve-manifest.js` para converter manifest.json em CompositionProps (resolve paths, parse branding, calcula timeline)
3. Renderiza via `npx remotion render`
4. Remove symlink ao finalizar

### Via npx direto (avancado)

```bash
cd remotion

# Gerar props manualmente
PROPS=$(node scripts/resolve-manifest.js /path/to/manifest.json prod)

# Render
npx remotion render src/index.ts Animatic output.mp4 --props="$PROPS"
```

## Componentes Remotion

| Componente | Funcao |
|------------|--------|
| `Beat` | Renderiza um beat: visual (video ou keyframe), audio, SFX, legenda |
| `KenBurns` | Efeito de zoom lento sobre imagem estatica |
| `Caption` | Legenda estilizada com branding |
| `Crossfade` | Transicao suave entre elementos |

### Logica do Beat

- **Modo final + clip_file existe:** renderiza `OffthreadVideo` (clip gerado)
- **Caso contrario:** renderiza primeiro keyframe com `KenBurns`
- **Audio:** renderiza `Audio` exceto quando `mode=final` e `video_job.type=lipsync` (audio ja embutido no clip)
- **SFX:** todos os SFX com `attach_to` == beat.id sao sobrepostos com volume 0.5

## Integracao com status.json

```json
{
  "compor": {
    "status": "pending",
    "animatic": null,
    "final": null
  }
}
```

Apos render:

```json
{
  "compor": {
    "status": "done",
    "animatic": "render/animatic.mp4",
    "final": "render/final/final_20260307.mp4"
  }
}
```

## Fluxo tipico

1. Ler o manifest existente e a fase de composição no status; usar edit_decisions apenas em projetos de edição
2. Gerar/atualizar `manifest.json` a partir das edit decisions
3. Rodar render animatic para preview
4. Corrigir problemas de timing dentro do escopo; revisão humana quando solicitada
5. Gerar clips via `video-clips` se fizerem parte da entrega autorizada
6. Rodar render final
7. Atualizar `status.json` com paths dos outputs

## Composicao ReelDialogue (reels com dialogo)

Para reels e videos curtos com dialogo, a composicao `ReelDialogue` (projeto `remotion/` na raiz do repo) compoe o video final direto — sem DaVinci:

- Transicoes crossfade entre cenas
- Logo do cliente como watermark
- Lower third com nome do personagem (fonte do cliente)
- Legendas estilo TikTok (caixa alta, amarela, sombra dura preta, centro da tela)
- Card CTA final com logo + slogan

**Setup para novo cliente:**
1. Copiar fonte, logo e clips para `remotion/public/`
2. Gerar `captions.json` a partir do storyboard (palavras do `vo` com timing)
3. Configurar props em `remotion/src/Root.tsx` (shots, logo, cores, fonte)

**Comandos:**
```bash
npx remotion studio                                    # preview no browser
npx remotion render ReelDialogue --output render/reel.mp4
```

**Dependencias ja instaladas:** `@remotion/media`, `@remotion/fonts`, `@remotion/transitions`, `@remotion/captions`.

Ao trabalhar com codigo Remotion, use a skill `remotion-best-practices`.
