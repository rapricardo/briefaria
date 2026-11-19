## Montagem via FFmpeg (assemble.py)

Alternativa ao Remotion para montagem direta. Nao precisa de Node.js — usa FFmpeg puro.

Script: `workflows/render/scripts/assemble.py`

### Analisar coverage

```bash
python workflows/render/scripts/assemble.py \
  --manifest clientes/{slug}/producao/{projeto}/manifest.json \
  --analyze
```

Reporta beat a beat: duracao do audio vs footage disponivel, gaps, clips curtos. Mostra exatamente o que falta gerar antes de montar.

### Ver plano de montagem (dry-run)

```bash
python workflows/render/scripts/assemble.py \
  --manifest manifest.json \
  --output render/final.mp4 \
  --dry-run
```

### Montar video final

```bash
python workflows/render/scripts/assemble.py \
  --manifest manifest.json \
  --output render/final.mp4
```

O que faz:
- Le o manifest beat a beat
- Clips de video: redimensiona e ajusta duracao
- Keyframes (imagem): aplica Ken Burns (zoom lento)
- Sincroniza audio de cada beat
- Concatena tudo na ordem e gera MP4 final

### Quando usar assemble.py vs Remotion

| Criterio | assemble.py (FFmpeg) | Remotion |
|----------|---------------------|----------|
| Dependencias | So FFmpeg | Node.js + npm |
| Velocidade | Rapido | Mais lento (React render) |
| Motion graphics | Nao | Sim (componentes React) |
| Legendas estilizadas | Nao | Sim (com branding) |
| Crossfades | Nao | Sim |
| Preview iterativo | Sim (--dry-run) | Sim (studio) |
| Montagem simples | Ideal | Overkill |

**Regra:** se e "clips + audio na sequencia", use assemble.py. Se precisa de legendas estilizadas, motion graphics ou crossfades, use Remotion.

---
