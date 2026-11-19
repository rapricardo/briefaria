# Voice-Over via ElevenLabs (v2)

Script que gera áudio de narração via ElevenLabs Text-to-Speech API.

## Integração com Pipeline (status.json)

Este skill é acionado quando `status.json` do projeto indica:

```json
{
  "pipeline": {"voiceover": "pending"}
}
```

Após execução bem-sucedida, atualizar `pipeline.voiceover` para `"done"`, preservando a estrutura existente.

## Paths v2

```
clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/
├── roteiro.json          # Input: roteiro com texto de narração
├── status.json           # Controle de fases do pipeline
└── audio/
    └── voiceover.mp3     # Output principal
```

## Pré-requisitos

- `ELEVENLABS_API_KEY` no `.env` ou variável de ambiente
- Input: `roteiro.json` (campo `narration` ou texto dos slides) ou texto livre

## Modos de Operação

```bash
# 1. DRY-RUN — mostra texto parseado sem gerar
python workflows/voiceover/scripts/elevenlabs_vo.py dry-run \
    --script /path/to/voiceover/vo_script.txt

# 2. VOICES — lista vozes disponíveis na conta
python workflows/voiceover/scripts/elevenlabs_vo.py voices

# 3. FULL — gera 1 MP3 de texto livre (modo principal v2)
python workflows/voiceover/scripts/elevenlabs_vo.py full \
    --text "Texto completo aqui" \
    --voice-id "VOICE_ID" \
    --output clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/audio/voiceover.mp3

# 4. FROM-SCRIPT — parse vo_script.txt → 1 MP3 contínuo
python workflows/voiceover/scripts/elevenlabs_vo.py from-script \
    --script /path/to/vo_script.txt \
    --voice-id "VOICE_ID" \
    --output clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/audio/voiceover.mp3

# 5. PER-ACT — parse vo_script.txt → 1 MP3 por ato
python workflows/voiceover/scripts/elevenlabs_vo.py per-act \
    --script /path/to/vo_script.txt \
    --voice-id "VOICE_ID" \
    --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/audio/

# 6. PER-BEAT — parse manifest.json → 1 MP3 por beat
python workflows/voiceover/scripts/elevenlabs_vo.py per-beat \
    --manifest path/to/manifest.json \
    --output-dir clientes/{slug}/producao/{YYYY-MM-DD}_{projeto}/audio/ \
    [--voice-override VOICE_ID] \
    [--dry-run]
```

## Input

### Opção A: roteiro.json (preferencial)

Extrair texto de narração do `roteiro.json` e passar via `--text` no modo `full`:

```json
{
  "narration": "Texto completo da narração...",
  "slides": [
    {"num": 1, "tipo": "gancho", "cena": "...", "texto1": "..."}
  ]
}
```

### Opção B: vo_script.txt (legado)

Formato com marcações de ato, usado nos modos `from-script`, `per-act` e `dry-run`.

### Opção C: Texto livre

Passar diretamente via `--text` no modo `full`.

## Output

- **Modo principal:** `audio/voiceover.mp3` (MP3 único, contínuo)
- `from-script`: salva como `voiceover.mp3`
- `per-act`: salva como `vo_ato_01.mp3`, `vo_ato_02.mp3`, etc.
- `per-beat`: salva como `{who}_{beat_id}.mp3` (atualiza manifest)

## Modelo

Default: `eleven_multilingual_v2` (suporta português nativo).

Override: `--model eleven_turbo_v2_5` para menor latência.

## Fluxo v2 (resumo)

1. Verificar `status.json` → `voiceover: pending`
2. Ler `roteiro.json` e extrair texto de narração
3. Executar `full --text "..." --voice-id ID --output audio/voiceover.mp3`
4. Atualizar `status.json` → `voiceover: done`
