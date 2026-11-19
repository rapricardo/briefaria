## Outros Modos

| Modo | Output | Uso |
|------|--------|-----|
| `carousel_batch` | N slides com texto (principal) | Carrossel de producao via roteiro.json |
| `storyboard` | N shots 16:9 via storyboard.json | Shots de video (keyframe separado) |
| `keyframes` | N frames via image-spec.json | Keyframes de video (legado) |
| `image` | 1 imagem com texto | Post avulso |
| `carousel` | N imagens com texto | Carrossel simples (sem chaining) |
| `photo` | 1 foto sem texto | Background, cena isolada |
| `photo_carousel` | N fotos sem texto | Serie de cenas |

### Storyboard (video — PREFERIDO)

Modo dedicado para pipeline de vídeo com campo `keyframe` separado de `cena`. Usa `build_storyboard_prompt()` que monta prompt estruturado com STYLE, CAMERA, LIGHTING, SCENE e RESTRICTIONS.

```bash
python workflows/imagen/scripts/imagen.py \
  --branding-file clientes/{slug}/branding.json \
  storyboard \
  --spec clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/storyboard.json \
  --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/
```

Opcoes:
- `--regenerate-shot N`: refaz apenas shot N (usa anterior como referencia)
- `--section problema`: gera apenas shots de uma secao
- `--aspect-ratio 16:9`: default para storyboard (landscape para video)

Resolve `personagem` → model sheet automaticamente via `characters` dict no spec.

`style_reference` na raiz do storyboard tem prioridade no prompt; sem ele, o script usa `direcao_visual.referencia_artistica` do branding. Ao escrever o storyboard, copie `direcao_video.style_reference` do `branding.json` do cliente quando o bloco existir, e use `direcao_video.personagem_*` para figurino e model sheets.

Output: `shot_XX.png` + `prompt_XX.txt`

#### Input: storyboard.json

```json
{
  "style_reference": "Alex Webb layered street photography...",
  "characters": { "concierge_mulher": "../../assets/model-sheets/concierge_mulher.png" },
  "shots": [{
    "id": 1, "secao": "intro",
    "cena": "Ação narrativa em PT (referência editorial)",
    "keyframe": "Static composition in EN for Gemini (max 300ch) — POSE not ACTION",
    "cinematografia": "high angle wide frontal",
    "iluminacao": "golden hour tropical light",
    "personagem": "concierge_mulher",
    "movimento": "slow_zoom_in"
  }]
}
```

- `keyframe`: composicao ESTATICA que o Gemini desenha (fallback para `cena` se ausente)
- `cena`: acao narrativa — referencia editorial, NAO vai pro prompt de imagem
- `movimento`: tipo Ken Burns — NAO vai no prompt (imagem e estatica)

#### Campos obrigatorios por shot (case-sensitive)

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| `id` | number | SIM | Sequencial 1..N |
| `secao` | string | SIM | hook, contexto, conflito, virada, resolucao, cta, etc. |
| `start` | number | SIM | Inicio em segundos (do transcript) |
| `end` | number | SIM | Fim em segundos (do transcript) |
| `duracao` | number | SIM | = round(end - start, 2). **Nunca omitir.** |
| `vo` | string | SIM | Texto falado. **Nunca usar "fala", "narracao" ou "texto"** |
| `cena` | string | SIM | Descricao editorial da cena (PT-BR) |
| `keyframe` | string | SIM | Composicao visual completa (EN, min 100 chars) |
| `cinematografia` | string | SIM | Enquadramento (medium, wide, close-up, overhead, etc.) |
| `iluminacao` | string | SIM | Tipo de luz (warm, golden, practical, etc.) |
| `movimento` | string | SIM | Camera (slow_zoom_in, slow_pan_right, static, etc.) |
| `personagem` | string | nao | Ref para o dict `characters` no root |

Root: `style_reference` (estetica global), `characters` (dict com paths para model sheets, **relativos ao storyboard.json** — `../../` sobe ate `clientes/{slug}/`), `total_duration`, `shots`.

#### Personagens e model sheets

Todo personagem com dialogo DEVE existir em `clientes/{slug}/assets/characters.json` ANTES do storyboard, com: `aparencia` (EN, fisico detalhado), `figurino` (EN, pecas/cores/tecidos), `voz_veo` (direcao de voz para video), `personalidade` (PT, para dialogos), `model_sheet_prompt` (EN) e `model_sheet_file`.

1. **Gerar o model sheet** via modo `photo` usando o `model_sheet_prompt`:
```bash
python workflows/imagen/scripts/imagen.py photo \
  --scene "[model_sheet_prompt]" --branding-file clientes/{slug}/branding.json \
  --output clientes/{slug}/assets/model-sheets/{model_sheet_file}
```
Deve ser **close-up em fundo neutro** — vira referencia de imagem para consistencia entre shots.

2. **Keyframes com personagem**: SEMPRE copiar `aparencia` + `figurino` do characters.json para dentro do keyframe — nunca descrever de memoria. Template:
```
"[Enquadramento] of [aparencia] wearing [figurino], [pose/emocao],
[ambiente detalhado], [props], [iluminacao], [estilo visual], [film grain]"
```

#### Validacao obrigatoria antes de gerar

```bash
python scripts/validate-storyboard.py --spec storyboard.json
```
**0 erros obrigatorio**, warnings revisados. Checa campos, timing, min 100 chars por keyframe e existencia dos model sheets. Gerar review HTML (`scripts/generate_storyboard_review.py`) quando solicitado ou quando o projeto tiver gate visual acordado. Respeitar o orçamento já autorizado.

### Keyframes (legado)

```bash
python workflows/imagen/scripts/imagen.py \
  --branding-file clientes/{slug}/branding.json \
  keyframes \
  --spec clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/image-spec.json \
  --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/
```

Suporta `--regenerate-frame F01-A` para refazer frame individual.
