# Imagen v2

Gerador unificado de imagens. Um script, tres backends, reference chaining automatico.

**Backend Nano Banana 2:** `--backend nano` — usa FAL_KEY (mesma chave do video). Recomendado para setup minimo.
**Backend Gemini Flash-Lite:** `--backend gemini` (default por retrocompat) — usa GEMINI_API_KEY. Modelo `--model flash-lite` (Nano Banana 2 Lite, **padrao do backend gemini**) — mais rapido (~4s) e ~metade do custo do Flash completo.
**Modelo Gemini Flash:** `--model flash` — Nano Banana 2 completo (gemini-3.1-flash-image-preview)
**Modelo Gemini Pro:** `--model pro` — melhor raciocinio/graficos, suporta 4K
**Backend GLM:** `--backend glm` — usar apenas quando solicitado

## Modelos

| Cenario | Flag |
|---------|------|
| Setup minimo (so FAL_KEY) | `--backend nano` |
| Qualquer geracao padrao Gemini | (nenhuma — `gemini/flash-lite` e default) |
| Precisa do Flash completo (nao o Lite) | `--model flash` |
| Graficos complexos, refazer com mais qualidade, 4K | `--model pro` |
| Solicitacao explicita do usuario | `--backend glm` |
| Imagem com referencia visual | **gemini** ou **nano** (GLM nao suporta) |

## Script

**Localizacao:** `workflows/imagen/scripts/imagen.py`

**Requer:**
- `FAL_KEY` para `--backend nano` (Nano Banana 2 via fal.ai)
- `GEMINI_API_KEY` para `--backend gemini` (default por retrocompat)
- `GLM_API_KEY`/`ZAI_API_KEY` para `--backend glm`

**Dependencias:** Nenhuma (stdlib Python). Carrega `.env` automaticamente.

## Fontes de Branding

O script aceita 3 fontes de branding (mutuamente exclusivas, nesta prioridade):

```bash
# 1. Arquivo JSON local (producao — PREFERIDO)
--branding-file clientes/{slug}/branding.json

# 2. JSON inline (rapido para testes)
--branding '{"cores": "#2B4A2E, #6BA368", "estilo_visual": "Organico"}'

# 3. Busca do ClickUp (quando nao tem arquivo local)
--client-id {task_id_conta_ativa}
```

## Style Mappings

O script expande automaticamente o valor do campo `estilo_visual` para keywords otimizadas:

| Estilo Visual | Keywords Expandidas |
|---------------|---------------------|
| Cientifico | Britannica style, engraving illustration, medical infographic |
| Organico | Watercolor, botanical, golden-hour, earth tones |
| Minimalista | Line art, geometric, negative space, monochromatic |
| Clean | Flat design, soft gradients, natural light |
| Moderno | Geometric patterns, neon accents, cinematic |
| Bold | High contrast, saturated colors, impactful |

## Output JSON

Todos os modos retornam JSON estruturado em stdout:

```json
{
  "success": true,
  "type": "carousel_batch",
  "backend": "gemini",
  "total_slides": 6,
  "generated": 6,
  "output_dir": "/path/to/output",
  "results": [
    {"slide": 1, "success": true, "path": "/path/slide_01.png"},
    {"slide": 2, "success": true, "path": "/path/slide_02.png"}
  ]
}
```
