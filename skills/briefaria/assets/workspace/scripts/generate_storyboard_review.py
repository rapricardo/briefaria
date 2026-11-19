#!/usr/bin/env python3
"""
Storyboard Reviewer Generator
Gera um HTML interativo e autossuficiente para revisar storyboards.

Uso:
  python scripts/generate_storyboard_review.py <projeto_path>

Exemplo:
  python scripts/generate_storyboard_review.py clientes/estudio-exemplo/producao/2026-01-01_demo

O HTML gerado inclui:
- Thumbnails embutidos (base64) de cada shot
- Narração (voice-over) sincronizada com cada shot
- Timeline visual com seções do roteiro
- Sistema de aprovação: aprovar / pedir ajuste / rejeitar por shot
- Campo de notas por shot
- Exportação do review como JSON (para reprocessar shots)
- Navegação por teclado (← →)
"""

import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path


def resize_image_to_base64(image_path: str, max_width: int = 800) -> str:
    """Redimensiona imagem e retorna base64 JPEG."""
    # Try with PIL first, fallback to raw base64
    try:
        from PIL import Image
        import io
        img = Image.open(image_path)
        ratio = max_width / img.width
        if ratio < 1:
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        pass

    # Fallback: try ImageMagick convert
    try:
        result = subprocess.run(
            ["convert", image_path, "-resize", f"{max_width}x", "-quality", "75", "jpeg:-"],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            return base64.b64encode(result.stdout).decode()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Last resort: raw PNG base64 (bigger but works)
    with open(image_path, "rb") as f:
        data = f.read()
    ext = Path(image_path).suffix.lower()
    return base64.b64encode(data).decode()


def get_mime_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")


def load_project(project_path: str) -> dict:
    """Carrega dados do projeto."""
    p = Path(project_path)

    # storyboard.json
    storyboard_file = p / "storyboard.json"
    if not storyboard_file.exists():
        print(f"ERRO: {storyboard_file} não encontrado")
        sys.exit(1)

    with open(storyboard_file) as f:
        storyboard = json.load(f)

    # status.json
    status_file = p / "status.json"
    status = {}
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)

    # roteiro.md
    roteiro_file = p / "roteiro.md"
    roteiro_text = ""
    if roteiro_file.exists():
        with open(roteiro_file) as f:
            roteiro_text = f.read()

    # brief.md
    brief_file = p / "brief.md"
    brief_text = ""
    if brief_file.exists():
        with open(brief_file) as f:
            brief_text = f.read()

    return {
        "storyboard": storyboard,
        "status": status,
        "roteiro": roteiro_text,
        "brief": brief_text,
        "path": str(p),
    }


def build_shots_data(project: dict) -> list:
    """Constrói dados dos shots com imagens embutidas."""
    p = Path(project["path"])
    storyboard = project["storyboard"]
    shots = storyboard.get("shots", [])
    images_dir = p / "imagens"

    shots_data = []
    for shot in shots:
        shot_id = shot["id"]
        image_file = images_dir / f"shot_{shot_id:02d}.png"

        image_b64 = ""
        mime = "image/jpeg"
        if image_file.exists():
            image_b64 = resize_image_to_base64(str(image_file))
            mime = "image/jpeg"  # We convert to JPEG in resize
        else:
            # Try other extensions
            for ext in [".jpg", ".jpeg", ".png"]:
                alt = images_dir / f"shot_{shot_id:02d}{ext}"
                if alt.exists():
                    image_b64 = resize_image_to_base64(str(alt))
                    break

        # Prompt file
        prompt_file = images_dir / f"prompt_{shot_id:02d}.txt"
        prompt_text = ""
        if prompt_file.exists():
            with open(prompt_file) as f:
                prompt_text = f.read().strip()

        shots_data.append({
            "id": shot_id,
            "start": shot.get("start", 0),
            "end": shot.get("end", 0),
            "duracao": shot.get("duracao", 0),
            "secao": shot.get("secao", ""),
            "vo": shot.get("vo", ""),
            "cena": shot.get("cena", ""),
            "keyframe": shot.get("keyframe", ""),
            "cinematografia": shot.get("cinematografia", ""),
            "iluminacao": shot.get("iluminacao", ""),
            "movimento": shot.get("movimento", ""),
            "personagem": shot.get("personagem"),
            "image_b64": image_b64,
            "mime": mime,
            "prompt_used": prompt_text,
        })

    return shots_data


# Paleta base de cores vibrantes para seções — se a seção não estiver aqui,
# gera cor automaticamente via hash do nome (evita fallback cinza genérico)
_SECTION_COLORS_BASE = {
    "gancho": "#F59E0B",
    "conflito": "#EF4444",
    "virada": "#8B5CF6",
    "resolucao": "#10B981",
    "hook": "#F59E0B",
    "intro": "#F59E0B",
    "cta": "#EF4444",
    "recap": "#F59E0B",
}

# Paleta de fallback para seções desconhecidas — cores vibrantes e distinguíveis
_DYNAMIC_PALETTE = [
    "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#06B6D4",
    "#84CC16", "#DC2626", "#A855F7", "#059669", "#D946EF",
]


def _hash_color(name: str) -> str:
    """Gera cor consistente a partir do nome da seção."""
    h = sum(ord(c) * (i + 1) for i, c in enumerate(name))
    return _DYNAMIC_PALETTE[h % len(_DYNAMIC_PALETTE)]


class _SectionColorDict(dict):
    """Dict que gera cores dinâmicas para seções desconhecidas."""
    def __missing__(self, key):
        color = _hash_color(key)
        self[key] = color
        return color


SECTION_COLORS = _SectionColorDict(_SECTION_COLORS_BASE)

SECTION_LABELS = {
    "gancho": "Gancho",
    "conflito": "Conflito",
    "virada": "Virada",
    "resolucao": "Resolucao",
    "hook": "HOOK",
    "intro": "INTRO",
    "problema_sozinho": "SOZINHO",
    "problema_terceirizar": "TERCEIRIZAR",
    "problema_beco": "BECO",
    "transicao": "TRANSICAO",
    "modelo_investimento": "INVESTIMENTO",
    "modelo_tempo": "TEMPO",
    "para_quem": "PRA QUEM",
    "para_quem_infoprodutor": "INFOPRODUTOR",
    "para_quem_criativo": "CRIATIVO",
    "para_quem_videomaker": "VIDEOMAKER",
    "para_quem_agencia": "AGENCIA",
    "recap": "RECAP",
    "proximos": "PROXIMOS",
    "cta": "CTA",
}


def generate_html(project: dict, shots_data: list) -> str:
    """Gera HTML completo e autossuficiente."""
    storyboard = project["storyboard"]
    status = project["status"]
    total_duration = storyboard.get("total_duration", 0)
    style_ref = storyboard.get("style_reference", "")

    project_name = status.get("projeto", Path(project["path"]).name)
    client_name = status.get("cliente", "")

    shots_json = json.dumps(shots_data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Storyboard Review — {project_name}</title>
<style>
:root {{
  --bg: #1a1a2e;
  --surface: #16213e;
  --surface2: #0f3460;
  --text: #e8e8e8;
  --text-muted: #a0a0b0;
  --accent: #e94560;
  --approve: #10B981;
  --adjust: #F59E0B;
  --reject: #EF4444;
  --gancho: #F59E0B;
  --conflito: #EF4444;
  --virada: #8B5CF6;
  --resolucao: #10B981;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  overflow-x: hidden;
}}

/* HEADER */
.header {{
  background: var(--surface);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}}
.header-left {{ display: flex; align-items: center; gap: 16px; }}
.header h1 {{ font-size: 18px; font-weight: 600; }}
.header .meta {{ font-size: 13px; color: var(--text-muted); }}
.badge {{
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

/* PROGRESS BAR */
.progress-bar {{
  background: var(--surface);
  padding: 8px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  position: sticky;
  top: 57px;
  z-index: 99;
}}
.progress-stats {{
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}}
.progress-stats span {{ display: flex; align-items: center; gap: 4px; }}
.progress-stats .dot {{
  width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}}
.progress-track {{
  height: 4px;
  background: rgba(255,255,255,0.08);
  border-radius: 2px;
  overflow: hidden;
  display: flex;
}}
.progress-segment {{ height: 100%; transition: width 0.3s; }}

/* TIMELINE */
.timeline {{
  padding: 12px 24px;
  background: var(--surface);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  overflow-x: auto;
  position: sticky;
  top: 93px;
  z-index: 98;
}}
.timeline-track {{
  display: flex;
  gap: 2px;
  min-width: max-content;
}}
.timeline-shot {{
  height: 40px;
  border-radius: 4px;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: rgba(255,255,255,0.7);
  transition: all 0.2s;
  border: 2px solid transparent;
}}
.timeline-shot:hover {{ filter: brightness(1.2); transform: scaleY(1.1); }}
.timeline-shot.active {{ border-color: white; transform: scaleY(1.15); }}
.timeline-shot.approved {{ box-shadow: 0 2px 0 var(--approve); }}
.timeline-shot.needs-adjust {{ box-shadow: 0 2px 0 var(--adjust); }}
.timeline-shot.rejected {{ box-shadow: 0 2px 0 var(--reject); }}

/* MAIN VIEWER */
.viewer {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}}

.shot-card {{
  background: var(--surface);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
}}

.shot-image-container {{
  position: relative;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.shot-image-container img {{
  max-width: 100%;
  max-height: 65vh;
  object-fit: contain;
}}
.shot-number {{
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(8px);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}}
.shot-section {{
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
}}
.shot-timing {{
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(8px);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  color: var(--text-muted);
}}
.shot-movement {{
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(8px);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  color: var(--text-muted);
}}

/* NAV ARROWS */
.nav-arrows {{
  display: flex;
  justify-content: space-between;
  position: absolute;
  width: 100%;
  top: 50%;
  transform: translateY(-50%);
  padding: 0 8px;
  pointer-events: none;
}}
.nav-arrow {{
  pointer-events: all;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(8px);
  border: none;
  color: white;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}}
.nav-arrow:hover {{ background: rgba(0,0,0,0.8); transform: scale(1.1); }}
.nav-arrow:disabled {{ opacity: 0.3; cursor: default; transform: none; }}

/* VO + DETAILS */
.shot-content {{
  padding: 20px 24px;
}}
.vo-text {{
  font-size: 20px;
  font-weight: 500;
  line-height: 1.5;
  margin-bottom: 16px;
  font-style: italic;
  color: #fff;
  border-left: 3px solid var(--accent);
  padding-left: 16px;
}}
.shot-details {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}}
.detail-item {{
  font-size: 13px;
  color: var(--text-muted);
}}
.detail-item strong {{
  color: var(--text);
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}}
.detail-item.full {{ grid-column: 1 / -1; }}

/* REVIEW CONTROLS */
.review-section {{
  border-top: 1px solid rgba(255,255,255,0.08);
  padding: 16px 24px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}}
.review-btn {{
  border: none;
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.review-btn:hover {{ filter: brightness(1.15); transform: translateY(-1px); }}
.btn-approve {{ background: var(--approve); color: #fff; }}
.btn-adjust {{ background: var(--adjust); color: #1a1a2e; }}
.btn-reject {{ background: var(--reject); color: #fff; }}
.btn-approve.active {{ box-shadow: 0 0 0 3px rgba(16,185,129,0.4); }}
.btn-adjust.active {{ box-shadow: 0 0 0 3px rgba(245,158,11,0.4); }}
.btn-reject.active {{ box-shadow: 0 0 0 3px rgba(239,68,68,0.4); }}

.notes-input {{
  flex: 1;
  min-width: 200px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 8px 12px;
  color: var(--text);
  font-size: 13px;
  font-family: inherit;
  resize: none;
  height: 38px;
}}
.notes-input:focus {{ outline: none; border-color: var(--accent); }}
.notes-input::placeholder {{ color: var(--text-muted); }}

/* EXPANDABLE PROMPT */
.prompt-toggle {{
  background: none;
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--text-muted);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  margin-top: 8px;
}}
.prompt-toggle:hover {{ border-color: rgba(255,255,255,0.3); color: var(--text); }}
.prompt-content {{
  display: none;
  margin-top: 8px;
  padding: 12px;
  background: rgba(0,0,0,0.2);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-muted);
  white-space: pre-wrap;
}}
.prompt-content.show {{ display: block; }}

/* EXPORT BAR */
.export-bar {{
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--surface);
  border-top: 1px solid rgba(255,255,255,0.08);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 100;
}}
.export-btn {{
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}}
.export-btn:hover {{ filter: brightness(1.15); transform: translateY(-1px); }}
.export-btn:disabled {{ opacity: 0.5; cursor: default; transform: none; }}

/* VIEW MODES */
.view-toggle {{
  display: flex;
  gap: 4px;
  background: rgba(255,255,255,0.05);
  padding: 3px;
  border-radius: 8px;
}}
.view-toggle button {{
  background: none;
  border: none;
  color: var(--text-muted);
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
}}
.view-toggle button.active {{
  background: var(--accent);
  color: white;
}}

/* GRID VIEW */
.grid-view {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}}
.grid-card {{
  background: var(--surface);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}}
.grid-card:hover {{ transform: translateY(-2px); border-color: rgba(255,255,255,0.1); }}
.grid-card.approved {{ border-color: var(--approve); }}
.grid-card.needs-adjust {{ border-color: var(--adjust); }}
.grid-card.rejected {{ border-color: var(--reject); }}
.grid-card img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; }}
.grid-card-info {{
  padding: 10px 12px;
}}
.grid-card-info .shot-label {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}}
.grid-card-info .vo-preview {{
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.grid-card-info .status-dot {{
  width: 8px; height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}}

/* FILMSTRIP VIEW */
.filmstrip-view {{
  padding: 24px;
  overflow-x: auto;
}}
.filmstrip-track {{
  display: flex;
  gap: 8px;
  padding-bottom: 16px;
}}
.filmstrip-frame {{
  flex-shrink: 0;
  width: 200px;
  background: var(--surface);
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}}
.filmstrip-frame:hover {{ border-color: rgba(255,255,255,0.2); }}
.filmstrip-frame.active {{ border-color: var(--accent); }}
.filmstrip-frame.approved {{ border-bottom: 3px solid var(--approve); }}
.filmstrip-frame.needs-adjust {{ border-bottom: 3px solid var(--adjust); }}
.filmstrip-frame.rejected {{ border-bottom: 3px solid var(--reject); }}
.filmstrip-frame img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; }}
.filmstrip-label {{
  padding: 4px 8px;
  font-size: 10px;
  text-align: center;
  color: var(--text-muted);
}}

/* TOAST */
.toast {{
  position: fixed;
  top: 20px;
  right: 20px;
  background: var(--surface2);
  color: var(--text);
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 13px;
  z-index: 200;
  opacity: 0;
  transform: translateY(-10px);
  transition: all 0.3s;
  border-left: 3px solid var(--approve);
}}
.toast.show {{ opacity: 1; transform: translateY(0); }}

/* KEYBOARD HINTS */
.keyboard-hints {{
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  gap: 12px;
}}
.kbd {{
  background: rgba(255,255,255,0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
}}

body {{ padding-bottom: 60px; }}

@media (max-width: 768px) {{
  .shot-details {{ grid-template-columns: 1fr; }}
  .review-section {{ flex-direction: column; }}
  .notes-input {{ width: 100%; }}
}}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>Storyboard Review</h1>
    <span class="meta">{client_name} / {project_name}</span>
    <span class="meta">{len(shots_data)} shots &middot; {total_duration:.0f}s</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <div class="view-toggle">
      <button class="active" onclick="setView('single')">Shot</button>
      <button onclick="setView('grid')">Grid</button>
      <button onclick="setView('filmstrip')">Filmstrip</button>
    </div>
    <div class="keyboard-hints">
      <span><span class="kbd">&larr;</span> <span class="kbd">&rarr;</span> navegar</span>
      <span><span class="kbd">A</span> aprovar</span>
      <span><span class="kbd">J</span> ajustar</span>
      <span><span class="kbd">R</span> rejeitar</span>
    </div>
  </div>
</div>

<div class="progress-bar">
  <div class="progress-stats" id="progressStats"></div>
  <div class="progress-track" id="progressTrack"></div>
</div>

<div class="timeline" id="timelineBar">
  <div class="timeline-track" id="timelineTrack"></div>
</div>

<div class="viewer" id="singleView"></div>
<div class="grid-view" id="gridView" style="display:none;"></div>
<div class="filmstrip-view" id="filmstripView" style="display:none;"></div>

<div class="export-bar">
  <div class="keyboard-hints">
    <span id="reviewSummary"></span>
  </div>
  <div style="display:flex;gap:8px;">
    <button class="export-btn" onclick="exportReview()" style="background:var(--surface2);">Exportar Review JSON</button>
    <button class="export-btn" onclick="exportRegenList()">Exportar lista de regeneracao</button>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const SHOTS = {shots_json};

// Cores dinâmicas: base conhecida + hash para seções novas
const _PALETTE = ['#3B82F6','#EF4444','#10B981','#F59E0B','#8B5CF6',
  '#EC4899','#14B8A6','#F97316','#6366F1','#06B6D4',
  '#84CC16','#DC2626','#A855F7','#059669','#D946EF'];
function _hashColor(name) {{
  let h = 0;
  for (let i = 0; i < name.length; i++) h += name.charCodeAt(i) * (i + 1);
  return _PALETTE[h % _PALETTE.length];
}}
const _BASE_COLORS = {{
  gancho: '#F59E0B', conflito: '#EF4444', virada: '#8B5CF6', resolucao: '#10B981',
  hook: '#F59E0B', intro: '#F59E0B', cta: '#EF4444', recap: '#F59E0B',
}};
const SECTION_COLORS = new Proxy(_BASE_COLORS, {{
  get(target, prop) {{ return target[prop] || _hashColor(String(prop)); }}
}});

const SECTION_LABELS = {{
  gancho: 'Gancho', conflito: 'Conflito', virada: 'Virada', resolucao: 'Resolucao',
  hook: 'HOOK', intro: 'INTRO',
  problema_sozinho: 'SOZINHO', problema_terceirizar: 'TERCEIRIZAR', problema_beco: 'BECO',
  transicao: 'TRANSICAO',
  modelo_investimento: 'INVESTIMENTO', modelo_tempo: 'TEMPO',
  para_quem: 'PRA QUEM', para_quem_infoprodutor: 'INFOPRODUTOR', para_quem_criativo: 'CRIATIVO',
  para_quem_videomaker: 'VIDEOMAKER', para_quem_agencia: 'AGENCIA',
  recap: 'RECAP', proximos: 'PROXIMOS', cta: 'CTA',
}};

// State
let currentShot = 0;
let currentView = 'single';
const reviews = {{}};
SHOTS.forEach(s => {{
  reviews[s.id] = {{ status: 'pending', notes: '' }};
}});

function setView(view) {{
  currentView = view;
  document.querySelectorAll('.view-toggle button').forEach(b => b.classList.remove('active'));
  document.querySelector(`.view-toggle button[onclick="setView('${{view}}')"]`).classList.add('active');

  document.getElementById('singleView').style.display = view === 'single' ? '' : 'none';
  document.getElementById('gridView').style.display = view === 'grid' ? '' : 'none';
  document.getElementById('filmstripView').style.display = view === 'filmstrip' ? '' : 'none';

  if (view === 'grid') renderGrid();
  if (view === 'filmstrip') renderFilmstrip();
  if (view === 'single') renderShot(currentShot);
}}

function renderTimeline() {{
  const track = document.getElementById('timelineTrack');
  const totalDur = SHOTS.reduce((sum, s) => sum + s.duracao, 0);
  track.innerHTML = SHOTS.map((s, i) => {{
    const baseWidth = Math.max(SHOTS.length * 40, 900);
    const w = Math.max(20, (s.duracao / totalDur) * baseWidth);
    const color = SECTION_COLORS[s.secao] || '#666';
    const reviewClass = reviews[s.id]?.status === 'approved' ? 'approved' :
                        reviews[s.id]?.status === 'adjust' ? 'needs-adjust' :
                        reviews[s.id]?.status === 'rejected' ? 'rejected' : '';
    return `<div class="timeline-shot ${{i === currentShot ? 'active' : ''}} ${{reviewClass}}"
                 style="width:${{w}}px;background:${{color}}80"
                 onclick="goToShot(${{i}})"
                 title="Shot ${{s.id}} — ${{s.secao}}">${{s.id}}</div>`;
  }}).join('');
}}

function renderProgress() {{
  const stats = {{ pending: 0, approved: 0, adjust: 0, rejected: 0 }};
  SHOTS.forEach(s => stats[reviews[s.id]?.status || 'pending']++);
  const total = SHOTS.length;

  document.getElementById('progressStats').innerHTML = `
    <span><span class="dot" style="background:var(--text-muted)"></span> Pendente: ${{stats.pending}}</span>
    <span><span class="dot" style="background:var(--approve)"></span> Aprovado: ${{stats.approved}}</span>
    <span><span class="dot" style="background:var(--adjust)"></span> Ajustar: ${{stats.adjust}}</span>
    <span><span class="dot" style="background:var(--reject)"></span> Rejeitar: ${{stats.rejected}}</span>
    <span style="margin-left:auto">Progresso: ${{total - stats.pending}}/${{total}}</span>
  `;

  const track = document.getElementById('progressTrack');
  track.innerHTML = `
    <div class="progress-segment" style="width:${{(stats.approved/total)*100}}%;background:var(--approve)"></div>
    <div class="progress-segment" style="width:${{(stats.adjust/total)*100}}%;background:var(--adjust)"></div>
    <div class="progress-segment" style="width:${{(stats.rejected/total)*100}}%;background:var(--reject)"></div>
  `;

  document.getElementById('reviewSummary').textContent =
    `${{stats.approved}} aprovados, ${{stats.adjust}} para ajustar, ${{stats.rejected}} rejeitados`;
}}

function renderShot(index) {{
  currentShot = index;
  const shot = SHOTS[index];
  const review = reviews[shot.id];
  const sectionColor = SECTION_COLORS[shot.secao] || '#666';
  const sectionLabel = SECTION_LABELS[shot.secao] || shot.secao;
  const imgSrc = shot.image_b64 ? `data:${{shot.mime}};base64,${{shot.image_b64}}` : '';

  const viewer = document.getElementById('singleView');
  viewer.innerHTML = `
    <div class="shot-card">
      <div class="shot-image-container">
        ${{imgSrc ? `<img src="${{imgSrc}}" alt="Shot ${{shot.id}}">` : '<div style="padding:100px;color:var(--text-muted)">Imagem nao encontrada</div>'}}
        <span class="shot-number">Shot ${{shot.id}} / ${{SHOTS.length}}</span>
        <span class="shot-section" style="background:${{sectionColor}}">${{sectionLabel}}</span>
        <span class="shot-timing">${{shot.start.toFixed(1)}}s — ${{shot.end.toFixed(1)}}s (${{shot.duracao.toFixed(1)}}s)</span>
        ${{shot.movimento ? `<span class="shot-movement">${{shot.movimento.replace(/_/g, ' ')}}</span>` : ''}}
        <div class="nav-arrows">
          <button class="nav-arrow" onclick="goToShot(${{index-1}})" ${{index === 0 ? 'disabled' : ''}}>&larr;</button>
          <button class="nav-arrow" onclick="goToShot(${{index+1}})" ${{index === SHOTS.length-1 ? 'disabled' : ''}}>&rarr;</button>
        </div>
      </div>
      <div class="shot-content">
        <div class="vo-text">"${{shot.vo}}"</div>
        <div class="shot-details">
          <div class="detail-item"><strong>Cena</strong>${{shot.cena}}</div>
          <div class="detail-item"><strong>Cinematografia</strong>${{shot.cinematografia}}</div>
          <div class="detail-item"><strong>Iluminacao</strong>${{shot.iluminacao}}</div>
          <div class="detail-item"><strong>Personagem</strong>${{shot.personagem || 'Nenhum'}}</div>
          <div class="detail-item full">
            <button class="prompt-toggle" onclick="this.nextElementSibling.classList.toggle('show');this.textContent=this.nextElementSibling.classList.contains('show')?'Esconder keyframe prompt':'Ver keyframe prompt'">Ver keyframe prompt</button>
            <div class="prompt-content">${{shot.keyframe}}</div>
          </div>
          ${{shot.prompt_used ? `
          <div class="detail-item full">
            <button class="prompt-toggle" onclick="this.nextElementSibling.classList.toggle('show');this.textContent=this.nextElementSibling.classList.contains('show')?'Esconder prompt usado':'Ver prompt usado'">Ver prompt usado</button>
            <div class="prompt-content">${{shot.prompt_used}}</div>
          </div>` : ''}}
        </div>
      </div>
      <div class="review-section">
        <button class="review-btn btn-approve ${{review.status==='approved'?'active':''}}" onclick="setReview(${{shot.id}},'approved')">Aprovar</button>
        <button class="review-btn btn-adjust ${{review.status==='adjust'?'active':''}}" onclick="setReview(${{shot.id}},'adjust')">Ajustar</button>
        <button class="review-btn btn-reject ${{review.status==='rejected'?'active':''}}" onclick="setReview(${{shot.id}},'rejected')">Rejeitar</button>
        <textarea class="notes-input" placeholder="Notas de ajuste (ex: trocar iluminacao, refazer com outro angulo...)"
                  oninput="reviews[${{shot.id}}].notes=this.value">${{review.notes}}</textarea>
      </div>
    </div>
  `;

  renderTimeline();
  renderProgress();
  // Scroll timeline to active
  const activeEl = document.querySelector('.timeline-shot.active');
  if (activeEl) activeEl.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
}}

function renderGrid() {{
  const grid = document.getElementById('gridView');
  grid.innerHTML = SHOTS.map((shot, i) => {{
    const imgSrc = shot.image_b64 ? `data:${{shot.mime}};base64,${{shot.image_b64}}` : '';
    const review = reviews[shot.id];
    const reviewClass = review.status === 'approved' ? 'approved' :
                        review.status === 'adjust' ? 'needs-adjust' :
                        review.status === 'rejected' ? 'rejected' : '';
    const sectionColor = SECTION_COLORS[shot.secao] || '#666';
    const statusColor = review.status === 'approved' ? 'var(--approve)' :
                        review.status === 'adjust' ? 'var(--adjust)' :
                        review.status === 'rejected' ? 'var(--reject)' : 'var(--text-muted)';
    return `
      <div class="grid-card ${{reviewClass}}" onclick="setView('single');goToShot(${{i}})">
        ${{imgSrc ? `<img src="${{imgSrc}}">` : '<div style="aspect-ratio:16/9;background:#333;display:flex;align-items:center;justify-content:center;color:#888">?</div>'}}
        <div class="grid-card-info">
          <div class="shot-label" style="color:${{sectionColor}}">
            <span class="status-dot" style="background:${{statusColor}}"></span>
            Shot ${{shot.id}} &middot; ${{shot.secao}}
          </div>
          <div class="vo-preview">"${{shot.vo}}"</div>
        </div>
      </div>
    `;
  }}).join('');
  renderTimeline();
  renderProgress();
}}

function renderFilmstrip() {{
  const strip = document.getElementById('filmstripView');
  strip.innerHTML = `<div class="filmstrip-track">${{
    SHOTS.map((shot, i) => {{
      const imgSrc = shot.image_b64 ? `data:${{shot.mime}};base64,${{shot.image_b64}}` : '';
      const review = reviews[shot.id];
      const reviewClass = review.status === 'approved' ? 'approved' :
                          review.status === 'adjust' ? 'needs-adjust' :
                          review.status === 'rejected' ? 'rejected' : '';
      return `
        <div class="filmstrip-frame ${{i === currentShot ? 'active' : ''}} ${{reviewClass}}"
             onclick="setView('single');goToShot(${{i}})">
          ${{imgSrc ? `<img src="${{imgSrc}}">` : '<div style="aspect-ratio:16/9;background:#333"></div>'}}
          <div class="filmstrip-label">Shot ${{shot.id}} &middot; ${{shot.duracao.toFixed(1)}}s</div>
        </div>
      `;
    }}).join('')
  }}</div>`;
  renderTimeline();
  renderProgress();
}}

function goToShot(index) {{
  if (index < 0 || index >= SHOTS.length) return;
  if (currentView === 'single') renderShot(index);
  else {{ currentShot = index; setView('single'); }}
}}

function setReview(shotId, status) {{
  if (reviews[shotId].status === status) {{
    reviews[shotId].status = 'pending';
  }} else {{
    reviews[shotId].status = status;
  }}
  renderShot(currentShot);
  showToast(`Shot ${{shotId}}: ${{reviews[shotId].status}}`);
}}

function exportReview() {{
  const data = {{
    project: '{project_name}',
    client: '{client_name}',
    reviewed_at: new Date().toISOString(),
    total_shots: SHOTS.length,
    summary: {{
      approved: Object.values(reviews).filter(r => r.status === 'approved').length,
      adjust: Object.values(reviews).filter(r => r.status === 'adjust').length,
      rejected: Object.values(reviews).filter(r => r.status === 'rejected').length,
      pending: Object.values(reviews).filter(r => r.status === 'pending').length,
    }},
    shots: SHOTS.map(s => ({{
      shot_id: s.id,
      secao: s.secao,
      vo: s.vo,
      status: reviews[s.id].status,
      notes: reviews[s.id].notes,
    }})),
  }};
  downloadJSON(data, `review-${{'{project_name}'.replace(/\\s/g,'-')}}.json`);
}}

function exportRegenList() {{
  const toRegen = SHOTS.filter(s => reviews[s.id].status === 'adjust' || reviews[s.id].status === 'rejected');
  if (toRegen.length === 0) {{
    showToast('Nenhum shot para regenerar');
    return;
  }}
  const data = {{
    project: '{project_name}',
    regenerate: toRegen.map(s => ({{
      shot_id: s.id,
      action: reviews[s.id].status === 'adjust' ? 'regenerate_with_changes' : 'regenerate_from_scratch',
      notes: reviews[s.id].notes,
      current_keyframe: s.keyframe,
    }})),
  }};
  downloadJSON(data, `regen-${{'{project_name}'.replace(/\\s/g,'-')}}.json`);
  showToast(`${{toRegen.length}} shots para regenerar exportados`);
}}

function downloadJSON(data, filename) {{
  const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}}

function showToast(msg) {{
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}}

// Keyboard navigation
document.addEventListener('keydown', (e) => {{
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  switch(e.key) {{
    case 'ArrowLeft': goToShot(currentShot - 1); break;
    case 'ArrowRight': goToShot(currentShot + 1); break;
    case 'a': case 'A': setReview(SHOTS[currentShot].id, 'approved'); break;
    case 'j': case 'J': setReview(SHOTS[currentShot].id, 'adjust'); break;
    case 'r': case 'R': setReview(SHOTS[currentShot].id, 'rejected'); break;
    case 'g': case 'G': setView('grid'); break;
    case 'f': case 'F': setView('filmstrip'); break;
    case 's': case 'S': setView('single'); break;
  }}
}});

// Init
renderShot(0);
</script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Gera HTML interativo de review de storyboard")
    parser.add_argument("project_path", help="Caminho para a pasta do projeto")
    parser.add_argument("--output", "-o", help="Caminho do HTML de saida (default: <projeto>/review.html)")
    parser.add_argument("--thumb-width", type=int, default=800, help="Largura max dos thumbnails (default: 800)")
    args = parser.parse_args()

    project = load_project(args.project_path)
    print(f"Projeto: {project['status'].get('projeto', '?')}")
    print(f"Cliente: {project['status'].get('cliente', '?')}")
    print(f"Shots: {len(project['storyboard'].get('shots', []))}")

    print("Processando imagens...")
    shots_data = build_shots_data(project)
    images_found = sum(1 for s in shots_data if s['image_b64'])
    print(f"  {images_found}/{len(shots_data)} imagens encontradas")

    print("Gerando HTML...")
    html = generate_html(project, shots_data)

    output_path = args.output or os.path.join(args.project_path, "review.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Review gerado: {output_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
