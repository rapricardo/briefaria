# Skill: Edição de Vídeo (Edit Decisions)

O agente analisa a transcrição, interage com o designer e gera decisões de edição. O script `apply_edits.py` aplica as decisões ao vídeo via FFmpeg (rascunho rápido) ou exporta EDL para DaVinci Resolve (finalização).

## Quando usar

- Fase `editar` está pendente no `status.json` da produção
- Designer pede cortes, inserções ou ajustes na transcrição

## Pré-requisito

- `transcript/transcript.json` deve existir (fase `transcrever`: done)

## Tipos de decisão de edição

### cut_silence

Detecta gaps de silêncio maiores que threshold (default 800ms) no `transcript.json`. Gera entries de `remove_segment` para cada gap encontrado.

### remove_segment

Remove trecho do vídeo.

| Campo | Descrição |
|-------|-----------|
| `from` | Timestamp de início do corte |
| `to` | Timestamp de fim do corte |
| `text_removed` | Texto do trecho removido |
| `reason` | Motivo do corte |

O agente busca o texto pedido no `transcript.json` e encontra os timestamps correspondentes.

### insert_broll

Insere clip de b-roll em ponto específico.

| Campo | Descrição |
|-------|-----------|
| `at` | Timestamp de inserção |
| `duration_s` | Duração do clip em segundos |
| `description` | Descrição do b-roll |
| `asset` | Path do clip gerado |

O agente gera o clip via skill `video-clips` ou `imagen` e referencia o path.

### insert_image

Insere imagem estática em ponto específico.

| Campo | Descrição |
|-------|-----------|
| `at` | Timestamp de inserção |
| `duration_s` | Duração da exibição em segundos |
| `description` | Descrição da imagem |
| `asset` | Path da imagem gerada |

## Arquivo edit_decisions.json

```json
{
  "source": "transcript.json",
  "decisions": []
}
```

Cada decisão é adicionada ao array `decisions`. A ordem importa — decisões são aplicadas sequencialmente.

## Comandos do designer e como responder

| Comando | Ação |
|---------|------|
| "corta silêncios" | Analisar `transcript.json`, encontrar gaps > 800ms, adicionar `cut_silence` + `remove_segment` para cada gap |
| "tire a parte que falo sobre X" | Buscar X no transcript, mostrar trecho encontrado com timestamps, adicionar quando o trecho estiver inequívoco, `remove_segment` |
| "cria b-roll quando falo de Y" | Encontrar timestamp de Y, gerar asset via skill adequado, adicionar `insert_broll` |
| "mostra o dado Z como slide" | Gerar imagem via `imagen.py`, adicionar `insert_image` |
| "quero ver como ficou" | Gerar `transcript_edited.txt` com marcações visuais |
| "desfaz o último corte" | Remover última decisão do array |

## Preview (transcript_edited.txt)

Formato de visualização para o designer:

```
[00:00:00] Texto falado...
           ~~[CORTADO: 00:00:22-00:00:25 — silêncio]~~
[00:00:25] Mais texto...
           ▶ [B-ROLL 4s: descrição]
```

## Aplicar edições (apply_edits.py)

Script: `workflows/edit/scripts/apply_edits.py`

### Rascunho rápido (FFmpeg)

```bash
python workflows/edit/scripts/apply_edits.py \
    --input recordings/screen.mkv \
    --decisions transcript/edit_decisions.json \
    --output render/rascunho.mp4
```

Gera vídeo cortado em segundos. O original **nunca é tocado** — o FFmpeg lê e gera arquivo novo. Serve para iterar rapidamente: o designer assiste, pede ajustes ("move o corte 2s pra frente"), o agente atualiza o JSON e roda de novo.

### Preview sem gerar vídeo (dry-run)

```bash
python workflows/edit/scripts/apply_edits.py \
    --input recordings/screen.mkv \
    --decisions transcript/edit_decisions.json \
    --dry-run
```

Mostra segmentos mantidos, tempo removido, inserções pendentes e assets faltantes.

### Exportar EDL para DaVinci Resolve

```bash
python workflows/edit/scripts/apply_edits.py \
    --input recordings/screen.mkv \
    --decisions transcript/edit_decisions.json \
    --export-edl render/timeline.edl
```

Gera EDL (CMX 3600) que o DaVinci importa como timeline. O footage original fica referenciado — todos os ajustes no DaVinci sao nao-destrutivos.

### Fluxo recomendado

1. Transcrever (Whisper) → `transcript.json`
2. Designer pede cortes → agente gera `edit_decisions.json`
3. `--dry-run` para validar cortes
4. `--output rascunho.mp4` para preview rápido
5. Corrigir problemas da edição solicitada; revisão humana quando acordada
6. `--export-edl` para finalizar no DaVinci (cor, zoom, overlays, b-roll)

## Regras

- NUNCA modificar o recording original ou `transcript.json`
- Esclarecer trechos ambíguos antes de aplicar um `remove_segment`
- Preservar decisões anteriores; desfazer altera somente a decisão solicitada
- Atualizar a fase após concluir a edição solicitada; aprovação humana quando já acordada

## Formatos de cortes aceitos pelo script

Formato v1 remove intervalos; `from` e `to` são timestamps:

```json
{"source": "transcript.json", "decisions": [{"type": "remove_segment", "from": "00:00:24.300", "to": "00:00:32.200", "reason": "silêncio"}]}
```

Formato v2 declara regiões mantidas e cortadas; `start` e `end` são segundos numéricos. O script usa os intervalos `keep` diretamente:

```json
{"version": 2, "source": "screen.mkv", "decisions": [{"type": "keep", "start": 2.2, "end": 24.3}, {"type": "cut", "start": 24.3, "end": 32.2}, {"type": "keep", "start": 32.2, "end": 38.3}]}
```

Preserve o formato em uso e confira o dry-run antes de renderizar cortes. Não transforme uma lista v1 de remoções em v2 sem calcular os intervalos mantidos.
