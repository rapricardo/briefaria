# Skill: Transcricao de Video/Audio (whisper.cpp)

Transcricao local via whisper.cpp — roda 100% offline, sem API key, otimizado para Apple Silicon (Metal + Neural Engine).

## IMPORTANTE

- **SEMPRE usar o script** `python workflows/transcribe/scripts/transcribe.py` para transcrever
- **NUNCA instalar openai-whisper** (pacote Python) — este projeto usa **whisper-cpp** (binario C++ via Homebrew)
- **NUNCA tentar importar whisper** via Python — o script chama `whisper-cli` diretamente via subprocess
- Se `whisper-cli` nao estiver no PATH, rodar: `brew install whisper-cpp`

## Quando Usar

- Fase `transcrever` esta com status `pending` no `status.json`
- Designer solicita transcricao de gravacao
- Qualquer momento em que se precise extrair texto de audio/video

## Dependencias

| Ferramenta | Instalacao | Notas |
|-----------|------------|-------|
| whisper-cpp | `brew install whisper-cpp` | Binario C++ via Homebrew (NAO e openai-whisper Python) |
| FFmpeg | `brew install ffmpeg` | Extrai audio de video (mkv, mov, mp4) |
| Modelo GGML | Ver abaixo | Baixar 1x, roda offline depois |

### Baixar modelo

```bash
mkdir -p models
curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin \
  -o models/ggml-medium.bin
```

O modelo `medium` (~1.5GB) e o padrao — bom equilibrio entre qualidade em portugues e velocidade. Baixa 1 vez, roda offline depois.

## Input

Qualquer arquivo de audio ou video:
- Video: `.mkv`, `.mov`, `.mp4` (FFmpeg extrai audio automaticamente)
- Audio: `.mp3`, `.wav`, `.flac`, `.ogg` (whisper-cli le direto)

## Output

Tres arquivos na pasta `transcript/`:

| Arquivo | Formato | Descricao |
|---------|---------|-----------|
| `transcript.json` | JSON | Segmentos com palavras e timestamps individuais |
| `transcript.srt` | SRT | Legendas (compativel com editores de video) |
| `transcript.txt` | Texto | Texto corrido, um paragrafo por segmento |

## Comando

```bash
python workflows/transcribe/scripts/transcribe.py \
  --input recordings/screen.mkv \
  --output-dir transcript/
```

### Parametros

| Parametro | Obrigatorio | Default | Descricao |
|-----------|-------------|---------|-----------|
| `--input` | Sim | — | Arquivo de audio/video |
| `--output-dir` | Sim | — | Pasta de saida |
| `--model` | Nao | `medium` | Nome do modelo GGML |
| `--model-dir` | Nao | `models/` | Pasta com modelos .bin |
| `--language` | Nao | `pt` | Codigo do idioma |

### Modelos Disponiveis

| Modelo | Disco | RAM | Velocidade (M-series) | Qualidade PT-BR |
|--------|-------|-----|----------------------|-----------------|
| `tiny` | 75 MB | ~273 MB | ~10x realtime | Fraca |
| `base` | 142 MB | ~388 MB | ~7x realtime | Razoavel |
| `small` | 466 MB | ~852 MB | ~4x realtime | Boa |
| `medium` | 1.5 GB | ~2.1 GB | ~3x realtime | **Muito boa (padrao)** |
| `large` | 2.9 GB | ~3.9 GB | ~1.5x realtime | Excelente |

## Pos-Transcricao

Atualizar `status.json`:

```json
{
  "fase": "transcrever",
  "status": "done",
  "output": "transcript/"
}
```

O proximo passo e a fase `editar` — o designer pede cortes em linguagem natural e o agente gera `edit_decisions.json`.
