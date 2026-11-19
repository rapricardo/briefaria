#!/usr/bin/env python3
"""
Imagen - Gerador unificado de imagens para a Máquina de Marketing.

Backend padrão: Nano Banana 2 via fal.ai (--backend nano, usa FAL_KEY)
Backend alternativo: Gemini Flash-Lite (gemini-3.1-flash-lite-image, usa GEMINI_API_KEY) — default do backend gemini
Backend alternativo: GLM-Image via Z.ai (--backend glm)
Modelo Gemini Flash: --model flash (gemini-3.1-flash-image-preview) — Nano Banana 2 completo
Modelo Gemini Pro: --model pro (gemini-3-pro-image-preview) — melhor raciocínio, gráficos complexos

Modos:
  image           - Imagem única COM texto integrado
  carousel        - Múltiplas imagens COM texto integrado
  photo           - Fotografia pura SEM texto
  photo_carousel  - Múltiplas fotos SEM texto

Fontes de branding (mutuamente exclusivas, nesta prioridade):
  --branding '{...}'       - JSON inline
  --branding-file path.json - Arquivo JSON local
  --client-id TASK_ID      - Busca do ClickUp (requer CLICKUP_TOKEN)

Recursos extras:
  --reference-image path.png  - Imagem de referência para consistência (só Gemini)
  --regenerate-slide N        - Refaz apenas o slide N de um carrossel existente

Requer: GEMINI_API_KEY (padrão), GLM_API_KEY/ZAI_API_KEY (backend glm) ou FAL_KEY (backend nano)

Uso:
  python imagen.py image --content "Texto" --branding-file branding.json --output img.png
  python imagen.py carousel --topic "Tema" --slides '["S1","S2"]' --branding-file branding.json --output-dir /path/
  python imagen.py photo --scene "Descrição" --branding '{}' --output foto.png
  python imagen.py photo_carousel --topic "Tema" --scenes '["C1","C2"]' --branding-file b.json --output-dir /path/
  python imagen.py carousel --topic "Tema" --slides '["S1","S2"]' --branding-file b.json --output-dir /path/ --regenerate-slide 3
  python imagen.py photo --scene "Cena" --branding-file b.json --reference-image ref.png --output foto.png
  python imagen.py --branding-file branding.json storyboard --spec storyboard.json --output-dir shots/

Modos adicionais:
  carousel_batch  - Carrossel a partir de roteiro.json (1 slide por vez, reference chaining)
  keyframes       - Keyframes a partir de image-spec.json (pipeline de vídeo)
  storyboard      - Shots de vídeo a partir de storyboard.json (keyframe separado)
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# ---------------------------------------------------------------------------
# .env loading — busca API keys sem expor
# ---------------------------------------------------------------------------
def load_dotenv():
    """Carrega variáveis de um arquivo .env (busca em locais comuns)."""
    search_paths = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
    ]
    # Subir a partir do script até encontrar .env ou CLAUDE.md
    script_dir = Path(__file__).resolve().parent
    for _ in range(6):
        search_paths.append(script_dir / ".env")
        if (script_dir / "CLAUDE.md").exists():
            break
        script_dir = script_dir.parent

    for env_path in search_paths:
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ[key] = value
            return str(env_path)
    return None

# ---------------------------------------------------------------------------
# APIs
# ---------------------------------------------------------------------------
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODELS = {
    "flash-lite": f"{GEMINI_BASE_URL}/gemini-3.1-flash-lite-image:generateContent",
    "flash": f"{GEMINI_BASE_URL}/gemini-3.1-flash-image-preview:generateContent",
    "pro":   f"{GEMINI_BASE_URL}/gemini-3-pro-image-preview:generateContent",
}
GEMINI_DEFAULT_MODEL = "flash-lite"
GLM_API_URL = "https://api.z.ai/api/paas/v4/images/generations"

# fal.ai Nano Banana 2
FAL_QUEUE_BASE = "https://queue.fal.run"
FAL_STORAGE_INITIATE = "https://rest.alpha.fal.ai/storage/upload/initiate"
NANO_ENDPOINT = "fal-ai/nano-banana-2"

# Cache de uploads para evitar re-upload de model sheets
_fal_upload_cache = {}

# ---------------------------------------------------------------------------
# Style Mappings (dropdown ClickUp → keywords otimizadas por backend)
# ---------------------------------------------------------------------------
GEMINI_STYLE_MAPPINGS = {
    "Científico": "educational Britannica style, fine line engraving illustration, medical infographic aesthetic, soft blue-green lighting, clean data visualization elements, professional healthcare design",
    "Orgânico": "watercolor textures, natural botanical elements, golden-hour warm lighting, earth tones, soft organic flowing shapes, hand-drawn feel",
    "Minimalista": "minimalist line art, bold geometric shapes, dramatic negative space, clean sans-serif typography, monochromatic with accent color",
    "Clean": "modern flat design, soft gradients, natural window light, airy composition, subtle shadows, professional corporate aesthetic",
    "Moderno": "contemporary design, dynamic geometric patterns, neon accents, cinematic depth, bold color blocking, tech-forward aesthetic",
    "Bold": "high contrast dramatic lighting, saturated colors, strong typography, impactful visual hierarchy, attention-grabbing composition",
}

GLM_STYLE_MAPPINGS = {
    "Científico": "educational infographic style, medical illustration, clean data visualization, scientific diagram with fine line art, professional healthcare design, soft blue-green color scheme",
    "Orgânico": "watercolor artistic style, natural botanical elements, warm golden lighting, earth tones palette, soft organic flowing shapes, hand-painted aesthetic",
    "Minimalista": "minimalist design, bold geometric shapes, dramatic negative space, clean sans-serif typography, monochromatic with single accent color",
    "Clean": "modern flat design, soft gradient background, natural lighting feel, airy composition, subtle shadows, professional corporate aesthetic",
    "Moderno": "contemporary design, dynamic geometric patterns, vibrant accent colors, bold color blocking, tech-forward futuristic aesthetic",
    "Bold": "high contrast dramatic style, saturated vivid colors, strong impactful typography, attention-grabbing visual hierarchy",
}

LIGHTING_MAPPINGS = {
    "Científico": "soft clinical lighting, clean white with subtle blue tones, even illumination",
    "Orgânico": "golden-hour rim lighting, warm natural sunlight, soft diffused glow",
    "Minimalista": "soft studio lighting, minimal shadows, clean even exposure",
    "Clean": "natural window light, soft morning light, gentle ambient illumination",
    "Moderno": "dramatic lighting with neon reflections, cinematic color grading",
    "Bold": "high contrast dramatic lighting, strong directional light, deep shadows",
}


# ---------------------------------------------------------------------------
# Branding loading
# ---------------------------------------------------------------------------
def load_branding(args) -> dict:
    """Carrega branding de uma das 3 fontes (inline, arquivo, ClickUp)."""
    if args.branding and args.branding != "{}":
        return json.loads(args.branding)

    if hasattr(args, 'branding_file') and args.branding_file:
        with open(args.branding_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    if hasattr(args, 'client_id') and args.client_id:
        return _fetch_branding_from_clickup(args.client_id)

    return {}


def _fetch_branding_from_clickup(client_id: str) -> dict:
    """Busca branding do cliente no ClickUp via API."""
    token = os.environ.get("CLICKUP_TOKEN")
    if not token:
        raise Exception("CLICKUP_TOKEN não definido (necessário para --client-id)")

    url = f"https://api.clickup.com/api/v2/task/{client_id}"
    req = Request(url, headers={"Authorization": token})

    try:
        with urlopen(req, timeout=30) as response:
            task = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        raise Exception(f"Erro ao buscar cliente {client_id}: {e.code}")

    branding = {
        "nome": task.get("name", ""),
        "cores": "", "fontes": "", "tom_de_voz": "",
        "estilo_visual": "", "palavras_chave": "", "palavras_proibidas": "",
    }

    field_mapping = json.loads(os.environ.get("CLICKUP_BRANDING_FIELDS", "{}"))
    if not isinstance(field_mapping, dict) or not field_mapping:
        raise ValueError("Configure CLICKUP_BRANDING_FIELDS com os IDs de campos do ClickUp.")
    if any(key not in branding for key in field_mapping.values()):
        raise ValueError("CLICKUP_BRANDING_FIELDS contém chaves de branding desconhecidas.")

    for field in task.get("custom_fields", []):
        fid = field.get("id")
        if fid in field_mapping:
            key = field_mapping[fid]
            value = field.get("value", "")
            if field.get("type") == "drop_down" and isinstance(value, int):
                options = field.get("type_config", {}).get("options", [])
                if 0 <= value < len(options):
                    value = options[value].get("name", "")
            branding[key] = value if value else ""

    return branding


# ---------------------------------------------------------------------------
# Style expansion
# ---------------------------------------------------------------------------
def expand_style(style_value: str, backend: str) -> tuple:
    """Expande estilo do dropdown para keywords otimizadas por backend."""
    mappings = GEMINI_STYLE_MAPPINGS if backend in ("gemini", "nano") else GLM_STYLE_MAPPINGS
    style = mappings.get(style_value, style_value)
    lighting = LIGHTING_MAPPINGS.get(style_value, "professional studio lighting")
    return style, lighting


def humanize_branding(branding: dict, backend: str) -> dict:
    """Traduz branding cru em campos otimizados para prompt de imagem.

    - Cores: remove hex codes, mantém só nomes descritivos
    - Style: usa style_reference se disponível, senão expand_style
    - Forbidden: preserva lista original para RESTRICTIONS
    """
    # 1. Cores: strip hex codes em qualquer formato
    #    "Vermelho (#EE2C39)" → "Vermelho"
    #    "Laranja #FF6600"    → "Laranja"
    colors_raw = branding.get("cores", "")
    colors_clean = re.sub(r'\s*\(?#[0-9A-Fa-f]{3,8}\)?', '', colors_raw)
    if not colors_clean.strip():
        colors_clean = "modern, professional color palette"

    # 2. Style: spec/style_reference > expand_style do dropdown
    style_ref = branding.get("style_reference", "")
    if not style_ref:
        visual_raw = branding.get("estilo_visual", "Clean")
        style_ref, _ = expand_style(visual_raw, backend)

    # 3. Palavras proibidas: preservar para seção RESTRICTIONS
    forbidden_raw = branding.get("palavras_proibidas", "")

    return {
        "colors": colors_clean,
        "style": style_ref,
        "forbidden": forbidden_raw,
    }


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
def build_text_image_prompt(content: str, branding: dict, backend: str) -> str:
    """Prompt para imagem COM TEXTO integrado."""
    hb = humanize_branding(branding, backend)
    tone = branding.get('tom_de_voz', 'professional and approachable')
    visual_style_raw = branding.get('estilo_visual', 'Clean')
    _, lighting = expand_style(visual_style_raw, backend)

    return f"""Create a professional Instagram image.

## SUBJECT
Primary text to display: "{content}"
Brand personality: {tone}

## VISUAL STYLE
Style keywords: {hb["style"]}
Color scheme: {hb["colors"]}
Typography: Bold, highly legible, high contrast against background, integrated into composition

## ENVIRONMENT & LIGHTING
{lighting}
Supporting visual elements that reinforce the message without overwhelming the text

## COMPOSITION
- 20-30% negative space for breathing room
- Text as focal point with complementary visual elements
- Professional, polished finish

## RESTRICTIONS (CRITICAL)
- This is an ILLUSTRATION/ARTWORK, not a UI mockup or app screenshot
- Do NOT render device frames, phone bezels, browser windows, or app interfaces
- Do NOT show color swatches, hex codes, palettes, or design system elements
- Do NOT add slide numbers, pagination, or "Slide X/Y"
- Do NOT add any text other than the specified content above
- No watermarks or logos
- Avoid: {hb["forbidden"] or "cluttered elements, generic stock photos"}

Output a ready-to-post Instagram image with the text beautifully integrated."""


def build_photo_prompt(scene: str, branding: dict, backend: str) -> str:
    """Prompt para FOTOGRAFIA pura, sem texto."""
    hb = humanize_branding(branding, backend)
    tone = branding.get('tom_de_voz', 'professional and approachable')
    visual_style_raw = branding.get('estilo_visual', 'Clean')
    _, lighting = expand_style(visual_style_raw, backend)

    return f"""Create a professional PHOTOGRAPH for Instagram. Photography only, NO TEXT.

## SUBJECT
{scene}

## VISUAL STYLE
Style keywords: {hb["style"]}
Color scheme: {hb["colors"]}
Mood/tone: {tone}

## ENVIRONMENT & LIGHTING
{lighting}
Sharp subject with subtle depth of field (bokeh background)
Professional studio quality finish

## COMPOSITION
- Clean, uncluttered frame
- Subject as clear focal point
- Natural, unforced positioning

## RESTRICTIONS (CRITICAL)
- This is a PHOTOGRAPH, not a UI mockup or app screenshot
- Do NOT render device frames, phone bezels, browser windows, or app interfaces
- Do NOT show color swatches, hex codes, palettes, or design system elements
- No text, words, letters, numbers, or typography
- No overlays, captions, titles, or labels
- No watermarks or logos
- Avoid: {hb["forbidden"] or "cluttered elements, generic stock photos"}

Output a clean, beautiful photograph. Text will be added later in post-production."""


def build_carousel_slide_prompt(slide: dict, spec: dict, branding: dict, backend: str) -> str:
    """Monta prompt para UM slide do carrossel, mantendo contexto visual global.

    Lê campos estruturados do slide:
    - cinematografia: shot size + camera angle + camera position
    - cor_primaria: tom dominante da cena
    - referencias_artisticas: referência visual/artística
    """
    hb = humanize_branding(branding, backend)
    n = len(spec.get("slides", []))

    # Style reference: spec pode sobrescrever branding
    style_ref = spec.get("style_reference", "") or hb["style"]

    num = slide.get("numero", 1)
    tipo = slide.get("tipo", "conteúdo")
    cena = slide.get("cena", "")
    cinematografia = slide.get("cinematografia", "medium shot eye level")
    cor = slide.get("cor_primaria", hb["colors"])
    ref_art = slide.get("referencias_artisticas", "")
    texto1 = slide.get("texto1", "")
    texto2 = slide.get("texto2", "")

    text_lines = []
    if texto1:
        text_lines.append(f'Line 1: "{texto1}"')
    if texto2:
        text_lines.append(f'Line 2: "{texto2}"')
    text_render = "\n".join(text_lines) if text_lines else "No text in this slide."

    ref_section = f"\nArtistic reference: {ref_art}" if ref_art else ""

    return f"""Create slide {num} of {n} for an Instagram carousel.

## VISUAL IDENTITY (same across ALL slides)
Style: {style_ref}
Color scheme: {hb["colors"]}
Typography: Bold, highly legible, high contrast against background
Format: 1:1 square

## CAMERA
{cinematografia}

## SCENE DESCRIPTION (visual layout ONLY — do NOT render any words, numbers, or labels from this paragraph as visible text)
{cena}
Primary color tone: {cor}{ref_section}

## COPY (these exact words must appear in the image — nothing else)
{text_render}

## RESTRICTIONS (CRITICAL)
- IGNORE any text, numbers, labels, or captions inside SCENE DESCRIPTION — they describe layout, NOT content to display
- The ONLY visible words in the final image must be the lines listed under COPY
- Render each line from COPY exactly ONCE — never duplicate, never omit
- This is an ILLUSTRATION/ARTWORK, not a UI mockup or app screenshot
- Do NOT render device frames, phone bezels, browser windows, or app interfaces
- Do NOT show color swatches, hex codes, palettes, or design system elements
- Do NOT create grids, collages, mosaics, or multi-panel layouts — this is ONE single full-size slide
- No slide numbers, pagination, or "Slide X/Y"
- No Instagram logos, social media icons, or platform UI elements
- No watermarks or logos unless explicitly described in the scene
- Text must be EXACTLY as specified — do not translate, rephrase, or add text
- Match the visual style of the reference image (if provided)"""


# ---------------------------------------------------------------------------
# Image generation - Gemini backend
# ---------------------------------------------------------------------------
def _gemini_generate(prompt: str, api_key: str, reference_image: str = None,
                     aspect_ratio: str = "1:1", model: str = None) -> bytes:
    """Gera imagem via Gemini API. Suporta reference image (multimodal)."""
    model = model or GEMINI_DEFAULT_MODEL
    api_url = GEMINI_MODELS[model]
    url = f"{api_url}?key={api_key}"

    parts = [{"text": prompt}]

    # Se tem imagem de referência, envia como input multimodal
    if reference_image:
        ref_path = Path(reference_image)
        if not ref_path.exists():
            raise Exception(f"Imagem de referência não encontrada: {reference_image}")
        ref_data = base64.b64encode(ref_path.read_bytes()).decode('utf-8')
        mime = "image/png" if ref_path.suffix.lower() == ".png" else "image/jpeg"
        parts.insert(0, {"inlineData": {"mimeType": mime, "data": ref_data}})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio, "imageSize": "1K"}
        }
    }

    data = json.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"Gemini API error {e.code}: {error_body}")

    try:
        part = result["candidates"][0]["content"]["parts"][0]
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
        else:
            raise Exception("Response does not contain image data")
    except (KeyError, IndexError):
        raise Exception(f"Failed to parse Gemini response: {json.dumps(result)[:500]}")


def _gemini_generate_batch(prompt: str, api_key: str, model: str = None,
                           aspect_ratio: str = "1:1") -> list:
    """Gera múltiplas imagens via Gemini em uma única chamada (TEXT+IMAGE)."""
    model = model or GEMINI_DEFAULT_MODEL
    api_url = GEMINI_MODELS[model]
    url = f"{api_url}?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio, "imageSize": "1K"}
        }
    }

    data = json.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"Gemini API error {e.code}: {error_body}")

    # Extrair todas as imagens da resposta
    images = []
    try:
        parts = result["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                images.append(base64.b64decode(part["inlineData"]["data"]))
    except (KeyError, IndexError):
        raise Exception(f"Failed to parse Gemini batch response: {json.dumps(result)[:500]}")

    if not images:
        raise Exception("Gemini batch response contained no images")

    return images


# ---------------------------------------------------------------------------
# Image generation - GLM backend
# ---------------------------------------------------------------------------
def _glm_generate(prompt: str, api_key: str, size: str = "1280x1280") -> bytes:
    """Gera imagem via GLM-Image API (Z.ai). Retorna bytes da imagem."""
    payload = {"model": "glm-image", "prompt": prompt, "size": size}
    data = json.dumps(payload).encode('utf-8')

    req = Request(GLM_API_URL, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    })

    try:
        with urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"GLM-Image API error {e.code}: {error_body}")

    try:
        entry = result["data"][0]
        image_ref = entry.get("url") or entry.get("b64_json")
        if not image_ref:
            raise Exception(f"No image in response: {result}")
    except (KeyError, IndexError):
        raise Exception(f"Failed to parse GLM response: {json.dumps(result)[:500]}")

    # Se for base64, decodifica; se for URL, baixa
    if image_ref.startswith("http"):
        dl_req = Request(image_ref)
        with urlopen(dl_req, timeout=60) as resp:
            return resp.read()
    else:
        return base64.b64decode(image_ref)


# ---------------------------------------------------------------------------
# Image generation - Nano Banana 2 (fal.ai) infrastructure
# ---------------------------------------------------------------------------
def _fal_upload_image(image_path, api_key):
    """Upload de imagem local para fal.ai storage. Retorna URL pública.

    Usa cache para evitar re-upload de model sheets entre shots.
    """
    abs_path = str(Path(image_path).resolve())
    if abs_path in _fal_upload_cache:
        return _fal_upload_cache[abs_path]

    if not Path(image_path).exists():
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    with open(image_path, "rb") as f:
        image_data = f.read()

    ext = Path(image_path).suffix.lower()
    content_types = {".png": "image/png", ".jpg": "image/jpeg",
                     ".jpeg": "image/jpeg", ".webp": "image/webp"}
    content_type = content_types.get(ext, "image/png")
    filename = Path(image_path).name

    # Step 1: Initiate upload
    initiate_body = json.dumps({
        "file_name": filename,
        "content_type": content_type,
    }).encode("utf-8")

    req = Request(FAL_STORAGE_INITIATE, data=initiate_body, headers={
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }, method="POST")

    try:
        with urlopen(req, timeout=30) as resp:
            upload_info = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao iniciar upload ({e.code}): {body}")

    upload_url = upload_info["upload_url"]
    file_url = upload_info["file_url"]

    # Step 2: PUT the file
    req2 = Request(upload_url, data=image_data, headers={
        "Content-Type": content_type,
    }, method="PUT")

    try:
        with urlopen(req2, timeout=60) as resp:
            pass  # 200 OK = success
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha no upload da imagem ({e.code}): {body}")

    _fal_upload_cache[abs_path] = file_url
    return file_url


def _fal_submit_request(endpoint, payload, api_key):
    """POST para fal.ai queue. Retorna dict com request_id, status_url, response_url."""
    url = f"{FAL_QUEUE_BASE}/{endpoint}"
    body = json.dumps(payload).encode("utf-8")

    req = Request(url, data=body, headers={
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }, method="POST")

    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {
                "request_id": result.get("request_id"),
                "status_url": result.get("status_url"),
                "response_url": result.get("response_url"),
            }
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao submeter request ({e.code}): {body}")


def _fal_check_status(status_url, api_key):
    """GET status de um request na queue."""
    req = Request(status_url, headers={
        "Authorization": f"Key {api_key}",
    }, method="GET")

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao verificar status ({e.code}): {body}")


def _fal_get_result(response_url, api_key):
    """GET resultado de um request completado."""
    req = Request(response_url, headers={
        "Authorization": f"Key {api_key}",
    }, method="GET")

    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao buscar resultado ({e.code}): {body}")


def _fal_submit_and_wait(endpoint, payload, api_key, poll_interval=10, max_wait=300):
    """Envia request para fal.ai e aguarda resultado com polling."""
    submit_info = _fal_submit_request(endpoint, payload, api_key)
    request_id = submit_info["request_id"]
    status_url = submit_info["status_url"]
    response_url = submit_info["response_url"]
    print(f"  [nano] Request enviado: {request_id}")

    elapsed = 0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        status = _fal_check_status(status_url, api_key)
        state = status.get("status", "UNKNOWN")

        if state == "COMPLETED":
            print(f"  [nano] Completado em ~{elapsed}s")
            return _fal_get_result(response_url, api_key)
        elif state in ("FAILED", "CANCELLED"):
            error = status.get("error", "Erro desconhecido")
            raise RuntimeError(f"Job falhou ({state}): {error}")
        else:
            logs = status.get("logs", [])
            last_log = logs[-1]["message"] if logs else state
            print(f"  [nano] [{elapsed}s] {last_log}")

    raise TimeoutError(f"Timeout após {max_wait}s esperando resultado do Nano Banana 2")


def _nano_generate(prompt, api_key, reference_image=None,
                   aspect_ratio="1:1", resolution="1K"):
    """Gera imagem via Nano Banana 2 (fal.ai). Retorna bytes."""
    image_urls = []
    if reference_image:
        url = _fal_upload_image(reference_image, api_key)
        image_urls.append(url)

    payload = {
        "prompt": prompt,
        "num_images": 1,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "resolution": resolution,
        "safety_tolerance": "5",
    }
    if image_urls:
        payload["image_urls"] = image_urls

    result = _fal_submit_and_wait(NANO_ENDPOINT, payload, api_key)
    image_url = result["images"][0]["url"]

    # Download da imagem
    req = Request(image_url)
    with urlopen(req, timeout=60) as resp:
        return resp.read()


# ---------------------------------------------------------------------------
# Unified generate function
# ---------------------------------------------------------------------------
def generate_image(prompt: str, api_key: str, backend: str,
                   reference_image: str = None, aspect_ratio: str = "1:1",
                   model: str = None) -> bytes:
    """Interface unificada de geração. Retorna bytes da imagem."""
    if backend == "gemini":
        return _gemini_generate(prompt, api_key, reference_image, aspect_ratio, model=model)
    elif backend == "glm":
        if reference_image:
            print("  [aviso] GLM não suporta reference-image, ignorando", file=sys.stderr)
        return _glm_generate(prompt, api_key)
    elif backend == "nano":
        return _nano_generate(prompt, api_key, reference_image, aspect_ratio)
    else:
        raise Exception(f"Backend desconhecido: {backend}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_image(args, branding: dict, api_key: str):
    """Gera uma imagem única com texto."""
    prompt = build_text_image_prompt(args.content, branding, args.backend)
    ref = getattr(args, 'reference_image', None)

    print(f"[{args.tag}] Gerando imagem: {args.content[:50]}...")
    image_data = generate_image(prompt, api_key, args.backend, ref, model=args.model)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_data)

    result = {"success": True, "type": "image", "backend": args.backend,
              "model": args.model if args.backend == "gemini" else None,
              "path": str(output), "size_bytes": len(image_data)}
    print(json.dumps(result, indent=2))


def cmd_carousel(args, branding: dict, api_key: str):
    """Gera carrossel com texto."""
    slides = json.loads(args.slides)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ref = getattr(args, 'reference_image', None)
    regen = getattr(args, 'regenerate_slide', None)

    # Se --regenerate-slide, só refaz esse slide
    if regen:
        slide_indices = [regen - 1]  # 1-indexed → 0-indexed
        print(f"[{args.tag}] Regenerando slide {regen} de {len(slides)}...")
    else:
        slide_indices = range(len(slides))
        print(f"[{args.tag}] Gerando carrossel: {len(slides)} slides...")

    results = []
    for i in slide_indices:
        slide_num = i + 1
        slide_content = slides[i]
        try:
            print(f"  Slide {slide_num}/{len(slides)}: {slide_content[:40]}...")
            prompt = build_text_image_prompt(slide_content, branding, args.backend)
            image_data = generate_image(prompt, api_key, args.backend, ref, model=args.model)

            output_path = output_dir / f"slide_{slide_num:02d}.png"
            output_path.write_bytes(image_data)
            results.append({"slide": slide_num, "success": True, "path": str(output_path)})

            # Rate limiting para GLM
            if args.backend == "glm" and i < max(slide_indices):
                time.sleep(1)
        except Exception as e:
            results.append({"slide": slide_num, "success": False, "error": str(e)})

    successful = sum(1 for r in results if r["success"])
    output = {"success": successful > 0, "type": "carousel", "backend": args.backend,
              "model": args.model if args.backend == "gemini" else None,
              "topic": args.topic, "total_slides": len(slides),
              "generated": successful, "output_dir": str(output_dir), "results": results}
    if regen:
        output["regenerated_slide"] = regen
    print(json.dumps(output, indent=2))


def cmd_carousel_batch(args, branding: dict, api_key: str):
    """Gera carrossel a partir de roteiro.json: 1 prompt por slide com reference chaining."""
    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise Exception(f"Arquivo spec não encontrado: {spec_path}")

    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slides = spec.get("slides", [])
    if not slides:
        raise Exception("Nenhum slide encontrado no spec")

    ref = getattr(args, 'reference_image', None)
    regen = getattr(args, 'regenerate_slide', None)

    if regen:
        # Regenerar apenas 1 slide, usando slide anterior existente como referência
        target_idx = None
        for idx, s in enumerate(slides):
            if s.get("numero", idx + 1) == regen:
                target_idx = idx
                break
        if target_idx is None:
            raise Exception(f"Slide {regen} não encontrado no spec")

        # Referência: slide anterior existente na pasta (ou --reference-image se slide 1)
        if target_idx > 0:
            prev_num = slides[target_idx - 1].get("numero", target_idx)
            prev_path = output_dir / f"slide_{prev_num:02d}.png"
            ref_image = str(prev_path) if prev_path.exists() else ref
        else:
            ref_image = ref

        slide = slides[target_idx]
        tipo = slide.get("tipo", "")
        texto1 = slide.get("texto1", "")
        print(f"[{args.tag}] Regenerando slide {regen}/{len(slides)} ({tipo}): {texto1[:40]}...")

        prompt = build_carousel_slide_prompt(slide, spec, branding, args.backend)

        # Salvar prompt para auditoria
        prompt_path = output_dir / f"prompt_{regen:02d}.txt"
        prompt_path.write_text(prompt, encoding='utf-8')

        image_data = generate_image(
            prompt, api_key, args.backend,
            reference_image=ref_image, model=args.model
        )

        output_path = output_dir / f"slide_{regen:02d}.png"
        output_path.write_bytes(image_data)

        output = {
            "success": True, "type": "carousel_batch", "backend": args.backend,
            "model": args.model if args.backend == "gemini" else None,
            "regenerated_slide": regen, "path": str(output_path),
            "size_bytes": len(image_data),
            "reference_used": ref_image or "none",
            "prompt_path": str(prompt_path),
        }
        print(json.dumps(output, indent=2))
        return

    # Geração completa com reference chaining
    print(f"[{args.tag}] Gerando carrossel: {len(slides)} slides com reference chaining...")

    results = []
    prev_image = ref  # Encadear referência para consistência visual
    for i, slide in enumerate(slides):
        slide_num = slide.get("numero", i + 1)
        tipo = slide.get("tipo", "")
        texto1 = slide.get("texto1", "")
        try:
            print(f"  Slide {slide_num}/{len(slides)} ({tipo}): {texto1[:40]}...")
            prompt = build_carousel_slide_prompt(slide, spec, branding, args.backend)

            # Salvar prompt para auditoria
            prompt_path = output_dir / f"prompt_{slide_num:02d}.txt"
            prompt_path.write_text(prompt, encoding='utf-8')

            image_data = generate_image(
                prompt, api_key, args.backend,
                reference_image=prev_image, model=args.model
            )

            output_path = output_dir / f"slide_{slide_num:02d}.png"
            output_path.write_bytes(image_data)
            results.append({"slide": slide_num, "success": True, "path": str(output_path),
                            "size_bytes": len(image_data), "prompt_path": str(prompt_path)})

            # Usar slide gerado como referência para o próximo
            prev_image = str(output_path)

            # Pequena pausa entre chamadas
            if i < len(slides) - 1:
                time.sleep(0.5)

        except Exception as e:
            results.append({"slide": slide_num, "success": False, "error": str(e)})
            print(f"  ERRO em slide {slide_num}: {e}", file=sys.stderr)

    successful = sum(1 for r in results if r["success"])
    output = {
        "success": successful > 0,
        "type": "carousel_batch",
        "backend": args.backend,
        "model": args.model if args.backend == "gemini" else None,
        "total_slides": len(slides),
        "generated": successful,
        "output_dir": str(output_dir),
        "results": results
    }
    print(json.dumps(output, indent=2))


def cmd_photo(args, branding: dict, api_key: str):
    """Gera uma foto sem texto."""
    prompt = build_photo_prompt(args.scene, branding, args.backend)
    ref = getattr(args, 'reference_image', None)
    ar = getattr(args, 'aspect_ratio', None) or "1:1"

    print(f"[{args.tag}] Gerando foto: {args.scene[:50]}...")
    image_data = generate_image(prompt, api_key, args.backend, ref, aspect_ratio=ar, model=args.model)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_data)

    result = {"success": True, "type": "photo", "backend": args.backend,
              "model": args.model if args.backend == "gemini" else None,
              "path": str(output), "size_bytes": len(image_data)}
    print(json.dumps(result, indent=2))


def cmd_photo_carousel(args, branding: dict, api_key: str):
    """Gera carrossel de fotos sem texto."""
    scenes = json.loads(args.scenes)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ref = getattr(args, 'reference_image', None)
    regen = getattr(args, 'regenerate_slide', None)
    ar = getattr(args, 'aspect_ratio', '1:1') or '1:1'

    if regen:
        indices = [regen - 1]
        print(f"[{args.tag}] Regenerando foto {regen} de {len(scenes)}...")
    else:
        indices = range(len(scenes))
        print(f"[{args.tag}] Gerando {len(scenes)} fotos...")

    results = []
    for i in indices:
        num = i + 1
        scene_desc = scenes[i]
        try:
            print(f"  Foto {num}/{len(scenes)}: {scene_desc[:40]}...")
            prompt = build_photo_prompt(scene_desc, branding, args.backend)
            image_data = generate_image(prompt, api_key, args.backend, ref, ar, model=args.model)

            output_path = output_dir / f"photo_{num:02d}.png"
            output_path.write_bytes(image_data)
            results.append({"slide": num, "success": True, "path": str(output_path)})

            if args.backend == "glm" and i < max(indices):
                time.sleep(1)
        except Exception as e:
            results.append({"slide": num, "success": False, "error": str(e)})

    successful = sum(1 for r in results if r["success"])
    output = {"success": successful > 0, "type": "photo_carousel", "backend": args.backend,
              "model": args.model if args.backend == "gemini" else None,
              "topic": args.topic, "total_photos": len(scenes),
              "generated": successful, "output_dir": str(output_dir), "results": results}
    print(json.dumps(output, indent=2))


def resolve_character_path(char_ref: str, spec_path: Path) -> str | None:
    """Resolve path de model sheet com fallback.

    Tenta, em ordem:
      1. Relativo ao storyboard.json (spec_path.parent / char_ref)
      2. Relativo ao diretório do cliente (subindo até clientes/{slug}/)
      3. Path absoluto (se char_ref for absoluto)

    Retorna o path como string ou None se não encontrar.
    """
    if Path(char_ref).is_absolute():
        p = Path(char_ref)
        if p.exists():
            return str(p)
        return None

    # 1. Relativo ao spec
    p1 = (spec_path.parent / char_ref).resolve()
    if p1.exists():
        return str(p1)

    # 2. Relativo ao cliente (subir até clientes/{slug}/)
    parts = spec_path.parent.resolve().parts
    try:
        idx = parts.index("clientes")
        client_dir = Path(*parts[:idx + 2])  # clientes/{slug}/
        p2 = (client_dir / char_ref).resolve()
        if p2.exists():
            return str(p2)
    except (ValueError, IndexError):
        pass

    # 3. Tentar sem prefixo ../../ (caso alguém colocou path direto)
    import re as _re
    clean = _re.sub(r'^(\.\./)+', '', char_ref)
    if clean != char_ref:
        p3 = (spec_path.parent / clean).resolve()
        if p3.exists():
            return str(p3)

    return None


def build_keyframe_prompt(frame: dict, spec: dict) -> str:
    """Monta prompt para keyframe a partir de campos estruturados.

    Formato novo: cena, cinematografia, cor_primaria, referencias_artisticas, movimento_camera.
    Expande {characters.X} e {style_reference} na cena.
    """
    style_ref = spec.get("style_reference", "")
    characters = spec.get("characters", {})

    cena = frame.get("cena", "")
    cinematografia = frame.get("cinematografia", "medium shot eye level")
    cor = frame.get("cor_primaria", "")
    ref_art = frame.get("referencias_artisticas", "")
    movimento = frame.get("movimento_camera", "")

    # Expandir {characters.X} e {style_reference} na cena
    cena = cena.replace("{style_reference}", style_ref)
    for match in re.findall(r'\{characters\.(\w+)\}', cena):
        value = characters.get(match, f"[MISSING: {match}]")
        cena = cena.replace(f"{{characters.{match}}}", value)

    parts = [f"{style_ref}.", f"{cinematografia}.", cena]
    if cor:
        parts.append(f"Primary color tone: {cor}.")
    if ref_art:
        parts.append(f"Artistic reference: {ref_art}.")
    if movimento:
        parts.append(f"Camera movement: {movimento}.")
    parts.append("9:16 vertical format.")

    return " ".join(parts)


def validate_blacklist(text: str, blacklist: list) -> list:
    """Checa texto contra blacklist visual. Retorna palavras encontradas."""
    if not blacklist or not text:
        return []
    text_lower = text.lower()
    found = [word for word in blacklist if word.lower() in text_lower]
    if found:
        print(f"  [aviso] Blacklist visual: {', '.join(found)}", file=sys.stderr)
    return found


def build_storyboard_prompt(shot: dict, spec: dict, branding: dict, backend: str) -> str:
    """Monta prompt para UM shot do storyboard (imagem estática para vídeo).

    Hierarquia de prioridade (Gemini dá mais peso ao que vem primeiro):
      1. Scene (keyframe) — sujeito + ambiente + objetos + pose
      2. Lighting — iluminação específica do shot
      3. Camera — enquadramento e ângulo
      4. Style — referência artística curta (sufixo)
      5. Restrictions — mínimas, só o essencial

    Regras de separação:
      - branding.json: palavras_proibidas_visuais (blacklist pro skill que ESCREVE keyframes)
      - storyboard.json: style_reference curto, por shot: keyframe, iluminacao, cinematografia
      - prompt: só o que o Gemini precisa pra DESENHAR, sem redundância
    """
    # Keyframe (fallback para cena)
    keyframe = shot.get("keyframe") or shot.get("cena", "")
    iluminacao = shot.get("iluminacao", "natural light")
    cinematografia = shot.get("cinematografia", "medium shot eye level")

    # Style curto: spec.style_reference > branding.referencia_artistica
    style_ref = spec.get("style_reference", "")
    if not style_ref:
        style_ref = branding.get("direcao_visual", {}).get("referencia_artistica", "")

    sections = []
    sections.append(f"Scene: {keyframe}")
    sections.append(f"Lighting: {iluminacao}")
    sections.append(f"Camera: {cinematografia}")
    if style_ref:
        sections.append(f"Style: {style_ref}, cinematic still photograph")
    else:
        sections.append("Style: cinematic still photograph")
    sections.append("No text or watermarks. Still photograph.")

    return "\n".join(sections)


def cmd_keyframes(args, api_key: str):
    """Gera keyframes a partir de um image-spec.json (pipeline de vídeo)."""
    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise Exception(f"Arquivo spec não encontrado: {spec_path}")

    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    style_ref = spec.get("style_reference", "")
    characters = spec.get("characters", {})
    frames = spec.get("frames", [])
    ar = getattr(args, 'aspect_ratio', '9:16') or '9:16'
    ref_image = getattr(args, 'reference_image', None)
    regen = getattr(args, 'regenerate_frame', None)

    # Filtrar frames se --regenerate-frame
    if regen:
        frames = [f for f in frames if f["id"] == regen]
        if not frames:
            raise Exception(f"Frame '{regen}' não encontrado no spec")
        print(f"[{args.tag}] Regenerando frame {regen}...")
    else:
        print(f"[{args.tag}] Gerando {len(frames)} keyframes (aspect: {ar})...")

    def expand_vars(prompt: str) -> str:
        """Expande {style_reference} e {characters.xxx} no prompt."""
        prompt = prompt.replace("{style_reference}", style_ref)
        for match in re.findall(r'\{characters\.(\w+)\}', prompt):
            value = characters.get(match, f"[MISSING: {match}]")
            prompt = prompt.replace(f"{{characters.{match}}}", value)
        return prompt

    results = []
    prev_image = ref_image  # Encadear referência para consistência
    for i, frame in enumerate(frames):
        fid = frame["id"]
        # Retrocompat: formato antigo usa "prompt", formato novo usa "cena"
        if "prompt" in frame:
            expanded = expand_vars(frame["prompt"])
        else:
            expanded = build_keyframe_prompt(frame, spec)

        try:
            print(f"  [{i+1}/{len(frames)}] {fid}: {expanded[:60]}...")
            image_data = generate_image(
                expanded, api_key, args.backend,
                reference_image=prev_image, aspect_ratio=ar,
                model=args.model
            )

            output_path = output_dir / f"{fid}.png"
            output_path.write_bytes(image_data)
            results.append({"frame": fid, "success": True, "path": str(output_path),
                            "size_bytes": len(image_data)})

            # Usar frame gerado como referência para o próximo (consistência)
            if not regen:
                prev_image = str(output_path)

            # Pequena pausa entre chamadas
            if i < len(frames) - 1:
                time.sleep(0.5)

        except Exception as e:
            results.append({"frame": fid, "success": False, "error": str(e)})
            print(f"  ERRO em {fid}: {e}", file=sys.stderr)

    successful = sum(1 for r in results if r["success"])
    output = {
        "success": successful > 0,
        "type": "keyframes",
        "backend": args.backend,
        "model": args.model if args.backend == "gemini" else None,
        "project": spec.get("project", ""),
        "total_frames": len(spec.get("frames", [])),
        "generated": successful,
        "aspect_ratio": ar,
        "output_dir": str(output_dir),
        "results": results
    }
    print(json.dumps(output, indent=2))


def cmd_storyboard(args, branding: dict, api_key: str):
    """Gera shots a partir de storyboard.json (pipeline de vídeo com keyframe separado)."""
    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise Exception(f"Arquivo spec não encontrado: {spec_path}")

    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    shots = spec.get("shots", [])
    if not shots:
        raise Exception("Nenhum shot encontrado no spec")

    ar = getattr(args, 'aspect_ratio', '16:9') or '16:9'
    ref_image = getattr(args, 'reference_image', None)
    regen = getattr(args, 'regenerate_shot', None)
    section_filter = getattr(args, 'section', None)

    # Blacklist visual do branding
    blacklist = branding.get("direcao_visual", {}).get("palavras_proibidas_visuais", [])

    # Filtrar por seção se pedido
    if section_filter:
        shots = [s for s in shots if s.get("secao") == section_filter]
        if not shots:
            raise Exception(f"Nenhum shot na seção '{section_filter}'")
        print(f"[{args.tag}] Filtrando seção '{section_filter}': {len(shots)} shots")

    # Regenerar apenas 1 shot
    if regen:
        target = None
        for idx, s in enumerate(shots):
            if s.get("id") == regen:
                target = (idx, s)
                break
        if target is None:
            raise Exception(f"Shot {regen} não encontrado")

        idx, shot = target
        # Referência: shot anterior existente na pasta
        if idx > 0:
            prev_id = shots[idx - 1].get("id")
            prev_path = output_dir / f"shot_{prev_id:02d}.png"
            ref = str(prev_path) if prev_path.exists() else ref_image
        else:
            ref = ref_image

        # Resolve personagem como reference image (com fallback de paths)
        personagem = shot.get("personagem")
        characters = spec.get("characters", {})
        if personagem and personagem in characters:
            resolved = resolve_character_path(characters[personagem], spec_path)
            if resolved:
                ref = resolved
            else:
                print(f"  ⚠️  Character '{personagem}': model sheet não encontrado em nenhum path")

        keyframe_text = shot.get("keyframe") or shot.get("cena", "")
        validate_blacklist(keyframe_text, blacklist)

        print(f"[{args.tag}] Regenerando shot {regen}...")
        prompt = build_storyboard_prompt(shot, spec, branding, args.backend)

        prompt_path = output_dir / f"prompt_{regen:02d}.txt"
        prompt_path.write_text(prompt, encoding='utf-8')

        image_data = generate_image(
            prompt, api_key, args.backend,
            reference_image=ref, aspect_ratio=ar, model=args.model
        )

        output_path = output_dir / f"shot_{regen:02d}.png"
        output_path.write_bytes(image_data)

        result = {
            "success": True, "type": "storyboard",
            "backend": args.backend,
            "model": args.model if args.backend == "gemini" else None,
            "regenerated_shot": regen, "path": str(output_path),
            "size_bytes": len(image_data),
            "reference_used": ref or "none",
            "prompt_path": str(prompt_path),
        }
        print(json.dumps(result, indent=2))
        return

    # Geração completa com reference chaining
    all_shots = spec.get("shots", [])
    if section_filter:
        print(f"[{args.tag}] Gerando {len(shots)} shots (seção: {section_filter})...")
    else:
        print(f"[{args.tag}] Gerando {len(shots)} shots com reference chaining...")

    results = []
    prev_image = ref_image
    characters = spec.get("characters", {})

    for i, shot in enumerate(shots):
        shot_id = shot.get("id", i + 1)
        try:
            keyframe_text = shot.get("keyframe") or shot.get("cena", "")
            validate_blacklist(keyframe_text, blacklist)

            vo_preview = shot.get("vo", "")[:40]
            print(f"  Shot {shot_id}/{all_shots[-1]['id'] if all_shots else '?'}: {vo_preview}...")

            prompt = build_storyboard_prompt(shot, spec, branding, args.backend)

            # Salvar prompt para auditoria
            prompt_path = output_dir / f"prompt_{shot_id:02d}.txt"
            prompt_path.write_text(prompt, encoding='utf-8')

            # Resolve personagem como reference image (prioridade sobre chaining, com fallback)
            ref_for_shot = prev_image
            personagem = shot.get("personagem")
            if personagem and personagem in characters:
                resolved = resolve_character_path(characters[personagem], spec_path)
                if resolved:
                    ref_for_shot = resolved
                else:
                    print(f"  ⚠️  Shot {shot_id}: character '{personagem}' model sheet não encontrado")

            image_data = generate_image(
                prompt, api_key, args.backend,
                reference_image=ref_for_shot, aspect_ratio=ar, model=args.model
            )

            output_path = output_dir / f"shot_{shot_id:02d}.png"
            output_path.write_bytes(image_data)
            results.append({
                "shot": shot_id, "success": True, "path": str(output_path),
                "size_bytes": len(image_data), "prompt_path": str(prompt_path)
            })

            # Usar shot gerado como referência para o próximo
            prev_image = str(output_path)

            if i < len(shots) - 1:
                time.sleep(0.5)

        except Exception as e:
            results.append({"shot": shot_id, "success": False, "error": str(e)})
            print(f"  ERRO em shot {shot_id}: {e}", file=sys.stderr)

    successful = sum(1 for r in results if r["success"])
    output = {
        "success": successful > 0,
        "type": "storyboard",
        "backend": args.backend,
        "model": args.model if args.backend == "gemini" else None,
        "total_shots": len(shots),
        "generated": successful,
        "aspect_ratio": ar,
        "output_dir": str(output_dir),
        "results": results
    }
    if section_filter:
        output["section"] = section_filter
    print(json.dumps(output, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    # Carregar .env antes de tudo
    env_file = load_dotenv()
    if env_file:
        print(f"[env] Carregado: {env_file}", file=sys.stderr)

    parser = argparse.ArgumentParser(
        description="Imagen - Gerador unificado de imagens (Máquina de Marketing)")

    # Global options
    parser.add_argument("--backend", default="gemini", choices=["gemini", "glm", "nano"],
                        help="Backend de geração (default: gemini)")
    parser.add_argument("--model", default="flash-lite", choices=["flash-lite", "flash", "pro"],
                        help="Modelo Gemini: flash-lite (Nano Banana 2 Lite, padrão — mais rápido/barato), "
                             "flash (Nano Banana 2 completo) ou pro (Nano Banana Pro, melhor raciocínio/gráficos)")
    parser.add_argument("--reference-image",
                        help="Imagem de referência para consistência visual (só Gemini)")
    parser.add_argument("--aspect-ratio", default=None,
                        help="Aspect ratio da imagem (ex: 1:1, 9:16, 16:9). Default: 1:1 para posts, 9:16 para keyframes")

    # Branding sources (mutuamente exclusivas na prática, prioridade: inline > file > clickup)
    parser.add_argument("--branding", default="{}", help="Branding JSON inline")
    parser.add_argument("--branding-file", help="Caminho para branding.json")
    parser.add_argument("--client-id", help="Task ID do cliente no ClickUp")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    # image
    p_img = subparsers.add_parser("image", help="Imagem única com texto")
    p_img.add_argument("--content", required=True, help="Texto para exibir na imagem")
    p_img.add_argument("--output", required=True, help="Caminho do arquivo de saída")

    # carousel
    p_car = subparsers.add_parser("carousel", help="Carrossel com texto")
    p_car.add_argument("--topic", required=True, help="Tema do carrossel")
    p_car.add_argument("--slides", required=True, help="JSON array com conteúdo dos slides")
    p_car.add_argument("--output-dir", required=True, help="Pasta de saída")
    p_car.add_argument("--regenerate-slide", type=int, help="Refazer apenas slide N (1-indexed)")

    # photo
    p_pho = subparsers.add_parser("photo", help="Foto sem texto")
    p_pho.add_argument("--scene", required=True, help="Descrição da cena (formato SAAC)")
    p_pho.add_argument("--output", required=True, help="Caminho do arquivo de saída")

    # photo_carousel
    p_phc = subparsers.add_parser("photo_carousel", help="Carrossel de fotos sem texto")
    p_phc.add_argument("--topic", required=True, help="Tema do carrossel")
    p_phc.add_argument("--scenes", required=True, help="JSON array com descrições de cenas")
    p_phc.add_argument("--output-dir", required=True, help="Pasta de saída")
    p_phc.add_argument("--regenerate-slide", type=int, help="Refazer apenas foto N (1-indexed)")

    # carousel_batch
    p_cb = subparsers.add_parser("carousel_batch", help="Carrossel batch: 1 prompt, N imagens")
    p_cb.add_argument("--spec", required=True, help="Caminho para roteiro.json com cenas")
    p_cb.add_argument("--output-dir", required=True, help="Pasta de saída")
    p_cb.add_argument("--regenerate-slide", type=int, help="Refazer apenas slide N (1-indexed), usando slide anterior como referência")

    # keyframes (novo — pipeline de vídeo)
    p_kf = subparsers.add_parser("keyframes", help="Gerar keyframes a partir de image-spec.json")
    p_kf.add_argument("--spec", required=True, help="Caminho para image-spec.json")
    p_kf.add_argument("--output-dir", required=True, help="Pasta de saída para os frames")
    p_kf.add_argument("--regenerate-frame", help="Refazer apenas frame específico (ex: F01-A)")

    # storyboard (pipeline de vídeo com keyframe separado)
    p_sb = subparsers.add_parser("storyboard", help="Gerar shots a partir de storyboard.json")
    p_sb.add_argument("--spec", required=True, help="Caminho para storyboard.json")
    p_sb.add_argument("--output-dir", required=True, help="Pasta de saída para os shots")
    p_sb.add_argument("--regenerate-shot", type=int, help="Refazer apenas shot N (1-indexed)")
    p_sb.add_argument("--section", help="Gerar apenas shots de uma seção específica")

    args = parser.parse_args()

    # Default aspect ratio: tenta ler formato do status.json (se spec fornecido), senao usa default por modo
    if args.aspect_ratio is None:
        formato_from_status = None
        spec_path = getattr(args, 'spec', None)
        if spec_path:
            status_path = Path(spec_path).parent / "status.json"
            if status_path.exists():
                try:
                    with open(status_path, 'r', encoding='utf-8') as _f:
                        formato_from_status = json.load(_f).get("formato")
                except Exception:
                    pass
        if formato_from_status:
            args.aspect_ratio = formato_from_status
        else:
            args.aspect_ratio = "9:16" if args.mode == "keyframes" else "16:9" if args.mode == "storyboard" else "1:1"

    # Tag de log: [gemini/flash], [gemini/pro], [nano] ou [glm]
    if args.backend == "gemini":
        args.tag = f"{args.backend}/{args.model}"
    elif args.backend == "nano":
        args.tag = "nano"
    else:
        args.tag = args.backend

    # Resolver API key pelo backend
    if args.backend == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Erro: GEMINI_API_KEY não definida. Crie um .env na raiz do projeto com: GEMINI_API_KEY=sua_key", file=sys.stderr)
            sys.exit(1)
    elif args.backend == "nano":
        api_key = os.environ.get("FAL_KEY")
        if not api_key:
            print("Erro: FAL_KEY não definida. Crie um .env na raiz do projeto com: FAL_KEY=sua_key", file=sys.stderr)
            sys.exit(1)
    else:
        api_key = os.environ.get("GLM_API_KEY") or os.environ.get("ZAI_API_KEY")
        if not api_key:
            print("Erro: GLM_API_KEY ou ZAI_API_KEY não definida", file=sys.stderr)
            sys.exit(1)

    # Keyframes não usa branding (prompts já vêm completos no spec)
    if args.mode == "keyframes":
        try:
            cmd_keyframes(args, api_key)
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}))
            sys.exit(1)
        return

    # Carregar branding para os outros modos
    try:
        branding = load_branding(args)
        nome = branding.get("nome", "")
        if nome:
            print(f"Cliente: {nome}")
    except Exception as e:
        print(f"Erro ao carregar branding: {e}", file=sys.stderr)
        sys.exit(1)

    # Executar comando
    try:
        if args.mode == "image":
            cmd_image(args, branding, api_key)
        elif args.mode == "carousel":
            cmd_carousel(args, branding, api_key)
        elif args.mode == "photo":
            cmd_photo(args, branding, api_key)
        elif args.mode == "photo_carousel":
            cmd_photo_carousel(args, branding, api_key)
        elif args.mode == "carousel_batch":
            cmd_carousel_batch(args, branding, api_key)
        elif args.mode == "storyboard":
            cmd_storyboard(args, branding, api_key)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
