## Modo Principal: carousel_batch

O modo `carousel_batch` e o padrao para producao de carrosseis. Le `roteiro.json`, gera 1 slide por vez com **reference chaining** (cada slide usa o anterior como imagem de referencia para manter consistencia visual).

### Input: roteiro.json

```json
{
  "style_reference": "flat vector illustration, warm earthy palette, soft rounded shapes",
  "slides": [
    {"num": 1, "tipo": "gancho", "cena": "EN visual prompt describing scene", "texto1": "Max 8 words", "texto2": "optional"},
    {"num": 2, "tipo": "contexto", "cena": "...", "texto1": "...", "texto2": "..."},
    {"num": 3, "tipo": "dado", "cena": "...", "texto1": "..."},
    {"num": 4, "tipo": "tensao", "cena": "...", "texto1": "..."},
    {"num": 5, "tipo": "virada", "cena": "...", "texto1": "..."},
    {"num": 6, "tipo": "cta", "cena": "...", "texto1": "..."}
  ]
}
```

- `cena`: composicao visual em EN — descreve O QUE DESENHAR, nao o que escrever
- `texto1`/`texto2`: UNICO texto renderizado na imagem — max 8 palavras cada
- `style_reference`: keywords de estilo expandidas no prompt de cada slide

### Comando

```bash
python workflows/imagen/scripts/imagen.py \
  --branding-file clientes/{slug}/branding.json \
  carousel_batch \
  --spec clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/roteiro.json \
  --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/
```

### Output

Para cada slide gera dois arquivos:
- `imagens/slide_XX.png` — imagem final
- `imagens/prompt_XX.txt` — prompt exato enviado ao Gemini (audit trail)

### Reference Chaining

Gemini nao suporta batch de imagens separadas (retorna grid/collage). O modo `carousel_batch` resolve isso gerando 1 slide por vez e usando o slide anterior como `--reference-image` automaticamente:

```
slide_01 → gera sem referencia
slide_02 → gera com slide_01 como referencia
slide_03 → gera com slide_02 como referencia
...
```

Resultado: slides individuais com estilo consistente entre todos.

## Regeneracao Individual

Quando apenas 1-2 slides precisam de correcao, usar `--regenerate-slide N` em vez de regerar tudo (economia de tokens):

```bash
python workflows/imagen/scripts/imagen.py \
  --branding-file clientes/{slug}/branding.json \
  carousel_batch \
  --spec clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/roteiro.json \
  --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/imagens/ \
  --regenerate-slide 3
```

- Refaz APENAS o slide 3
- Usa slide 2 (existente na pasta) como referencia automaticamente
- 1 chamada API em vez de 6
