# Personagens e model sheets


Todo personagem com diálogo DEVE ter um **characters.json** e um **model sheet** antes de criar o storyboard.

#### 1. Criar `characters.json` em `clientes/{slug}/assets/`

Definir aparência, figurino e voz para cada personagem com diálogo:

```json
{
  "meta": {
    "cliente": "slug",
    "estetica": "referência estética global",
    "regras_visuais": ["regra 1", "regra 2"]
  },
  "characters": {
    "slug_personagem": {
      "slug": "slug_personagem",
      "nome": "Nome",
      "papel": "Cargo / Papel",
      "idade": "45",
      "genero": "masculino",
      "etnia": "descrição",
      "aparencia": "EN — descrição física detalhada (pele, cabelo, rosto, constituição)",
      "figurino": "EN — descrição completa do figurino (peças, cores, tecidos, acessórios)",
      "voz_veo": "in a [tom], [faixa] with [ritmo] and [sotaque], speaking with [qualidade]",
      "personalidade": "PT — traços de personalidade para guiar a escrita de diálogos",
      "model_sheet_prompt": "EN — prompt completo para gerar o model sheet",
      "model_sheet_file": "slug_personagem.png"
    }
  }
}
```

#### 2. Gerar model sheets

Gerar via `imagen.py photo` usando o `model_sheet_prompt` do characters.json:
```bash
python imagen.py photo --scene "[model_sheet_prompt]" --branding-file branding.json \
  --output clientes/{slug}/assets/model-sheets/{model_sheet_file}
```

O model sheet deve ser **close-up em fundo neutro** — funciona como referência de imagem para o Gemini manter consistência visual entre shots.

#### 3. Usar no storyboard

O `characters` dict no storyboard aponta para os model sheets:
```json
"characters": {
  "ceo": "../../assets/model-sheets/slug_ceo.png",
  "comercial": "../../assets/model-sheets/slug_comercial.png"
}
```
Paths são resolvidas **relativas ao storyboard.json**. `../../` sobe até `clientes/slug/`.

#### 4. Usar no video-spec (dialogue)

O campo `voice` de cada job vem do `voz_veo` do characters.json:
```json
"voice": "in a deep, commanding contralto with measured cadence"
```
Repetir a MESMA string em TODOS os jobs do mesmo personagem.

#### Como escrever keyframes com personagem

**LER characters.json** antes de escrever keyframes. Cada keyframe DEVE incluir a `aparencia` e o `figurino` do personagem (copiados do JSON, não inventados).

Template:
```
"[Enquadramento] of [aparencia do characters.json] wearing [figurino do characters.json],
[pose/emoção], [ambiente detalhado], [props específicos],
[iluminação], [estilo visual], [film grain]"
```

**REGRA**: nunca descrever um personagem de memória — sempre copiar `aparencia` + `figurino` do characters.json para garantir consistência entre shots.

**Verificar** que os model sheets existem antes de gerar imagens. O script `validate-storyboard.py` faz essa checagem automaticamente.
