#!/usr/bin/env python3
"""
fal.ai Video Generator - Skill Script
Gera clips de video a partir de keyframes via fal.ai.

Modos:
  dry-run        - Mostra payloads sem enviar (zero custo)
  single         - Gera 1 clip especifico por job_id
  batch          - Gera todos os clips do spec em sequencia
  from-manifest  - Gera clips do manifest.json
  single-beat    - Gera 1 clip de beat especifico do manifest

Engines (--engine):
  gemini-omni (padrao) - Google Gemini Omni Flash (audio nativo, image-to-video)
  veo            - Veo 3.1 Lite (barato, audio ambiente) / Veo 3 (dialogue) — alternativa
  kling          - Kling O3/v2.5 (compatibilidade retroativa)
  kling-v3       - Kling v3 Pro (audio nativo, negative_prompt, cfg_scale, ate 15s)
  happy-horse    - Alibaba Happy Horse 1.0 (lip-sync nativo, durações 3-15s)
  seedance       - ByteDance Seedance 2.0 (end_image_url, áudio nativo, 7 aspect ratios)
  seedance-fast  - ByteDance Seedance 2.0 Fast (~20% mais barato, 480p/720p apenas)

A engine pode ser definida em 3 lugares (ordem de prioridade):
  1. job["engine"] no video-spec.json — override por shot
  2. default_settings["engine"] no video-spec.json — default do projeto
  3. --engine no CLI — fallback

Endpoints Gemini Omni Flash:
  single_frame / broll / action / dialogue -> google/gemini-omni-flash/image-to-video
  (sem suporte a start_end_frame — nao documentado pelo fal.ai)

Endpoints Kling:
  start_end_frame -> fal-ai/kling-video/o3/standard/image-to-video
  single_frame    -> fal-ai/kling-video/v2.5-turbo/pro/image-to-video
  lipsync         -> fal-ai/kling-video/lipsync/audio-to-video
  broll           -> fal-ai/kling-video/v2.5-turbo/pro/image-to-video
  interpolation   -> fal-ai/kling-video/o3/standard/image-to-video
  action          -> fal-ai/kling-video/v2.5-turbo/pro/image-to-video

Endpoints Kling v3 Pro (todos os tipos -> mesmo endpoint; usa start_image_url, nao image_url):
  single_frame / broll / action / dialogue / start_end_frame
    -> fal-ai/kling-video/v3/pro/image-to-video
  Audio nativo (musica+SFX+fala) so em chines/ingles nativamente — outros idiomas sao
  auto-traduzidos para ingles. NAO confiavel para dialogue em PT-BR sem validar 1 clip.

Endpoints Veo:
  single_frame    -> fal-ai/veo3.1/lite/image-to-video
  broll           -> fal-ai/veo3.1/lite/image-to-video
  action          -> fal-ai/veo3.1/lite/image-to-video
  dialogue        -> fal-ai/veo3.1/lite/image-to-video

Endpoints Happy Horse (todos os tipos -> mesmo endpoint, lip-sync nativo):
  single_frame / broll / action / dialogue -> fal-ai/alibaba/happy-horse/image-to-video

Endpoints Seedance (todos os tipos -> mesmo endpoint, suporta end_image_url):
  single_frame / broll / action / dialogue / start_end_frame
    -> fal-ai/bytedance/seedance-2.0/image-to-video

Endpoints Seedance Fast (mesmo schema do Seedance, resolucao limitada a 480p/720p):
  single_frame / broll / action / dialogue / start_end_frame
    -> bytedance/seedance-2.0/fast/image-to-video

Requer: FAL_KEY como variavel de ambiente.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Endpoint defaults por tipo de job
ENDPOINTS = {
    "start_end_frame": "fal-ai/kling-video/o3/standard/image-to-video",
    "single_frame": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
    "text_to_video": "fal-ai/kling-video/v2.5-turbo/pro/text-to-video",
    "lipsync": "fal-ai/kling-video/lipsync/audio-to-video",
    "broll": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
    "interpolation": "fal-ai/kling-video/o3/standard/image-to-video",
    "action": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
}

# Veo endpoints (via fal.ai)
VEO_ENDPOINTS = {
    "single_frame": "fal-ai/veo3.1/lite/image-to-video",
    "broll": "fal-ai/veo3.1/lite/image-to-video",
    "action": "fal-ai/veo3.1/lite/image-to-video",
    "dialogue": "fal-ai/veo3.1/lite/image-to-video",
}

# Happy Horse endpoints (Alibaba — lip-sync nativo em 7 idiomas, sem PT-BR documentado)
HAPPY_HORSE_ENDPOINTS = {
    "single_frame": "alibaba/happy-horse/image-to-video",
    "broll": "alibaba/happy-horse/image-to-video",
    "action": "alibaba/happy-horse/image-to-video",
    "dialogue": "alibaba/happy-horse/image-to-video",
}

# Seedance endpoints (ByteDance — suporta end_image_url, audio nativo)
SEEDANCE_ENDPOINTS = {
    "single_frame": "fal-ai/bytedance/seedance-2.0/image-to-video",
    "broll": "fal-ai/bytedance/seedance-2.0/image-to-video",
    "action": "fal-ai/bytedance/seedance-2.0/image-to-video",
    "dialogue": "fal-ai/bytedance/seedance-2.0/image-to-video",
    "start_end_frame": "fal-ai/bytedance/seedance-2.0/image-to-video",
}

# Gemini Omni Flash endpoints (Google — engine padrao, audio nativo, sem start_end_frame)
GEMINI_OMNI_ENDPOINTS = {
    "single_frame": "google/gemini-omni-flash/image-to-video",
    "broll": "google/gemini-omni-flash/image-to-video",
    "action": "google/gemini-omni-flash/image-to-video",
    "dialogue": "google/gemini-omni-flash/image-to-video",
}

# Kling v3 Pro endpoints (todos os tipos -> mesmo endpoint; usa start_image_url)
KLING_V3_ENDPOINTS = {
    "single_frame": "fal-ai/kling-video/v3/pro/image-to-video",
    "broll": "fal-ai/kling-video/v3/pro/image-to-video",
    "action": "fal-ai/kling-video/v3/pro/image-to-video",
    "dialogue": "fal-ai/kling-video/v3/pro/image-to-video",
    "start_end_frame": "fal-ai/kling-video/v3/pro/image-to-video",
}

# Seedance Fast endpoints (mesmo schema do Seedance, resolucao limitada a 480p/720p)
SEEDANCE_FAST_ENDPOINTS = {
    "single_frame": "bytedance/seedance-2.0/fast/image-to-video",
    "broll": "bytedance/seedance-2.0/fast/image-to-video",
    "action": "bytedance/seedance-2.0/fast/image-to-video",
    "dialogue": "bytedance/seedance-2.0/fast/image-to-video",
    "start_end_frame": "bytedance/seedance-2.0/fast/image-to-video",
}

FAL_API_BASE = "https://queue.fal.run"
FAL_UPLOAD_URL = "https://fal.run/fal-ai/fal-ai/any/upload"
FAL_STORAGE_URL = "https://fal.ai/api/storage/upload/initiate"


def load_dotenv():
    """Carrega variáveis de um arquivo .env se existir."""
    # Procura .env no diretório atual e nos pais
    search_dir = os.getcwd()
    for _ in range(5):  # máximo 5 níveis acima
        env_path = os.path.join(search_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
            return
        parent = os.path.dirname(search_dir)
        if parent == search_dir:
            break
        search_dir = parent


def get_api_key():
    """Retorna FAL_KEY ou falha com mensagem clara."""
    key = os.environ.get("FAL_KEY")
    if not key:
        print("ERROR: FAL_KEY não encontrada nas variáveis de ambiente.")
        print("Configure com: export FAL_KEY=\"sua-chave\"")
        sys.exit(1)
    return key


def upload_image(image_path, api_key):
    """Upload de imagem local para fal.ai storage. Retorna URL pública."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    # Ler a imagem como base64
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Detectar content type
    ext = os.path.splitext(image_path)[1].lower()
    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    content_type = content_types.get(ext, "image/png")
    filename = os.path.basename(image_path)

    # Usar REST upload direto do fal.ai
    # Step 1: Initiate upload
    initiate_url = "https://rest.alpha.fal.ai/storage/upload/initiate"
    initiate_body = json.dumps({
        "file_name": filename,
        "content_type": content_type,
    }).encode("utf-8")

    req = urllib.request.Request(
        initiate_url,
        data=initiate_body,
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            upload_info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao iniciar upload ({e.code}): {body}")

    upload_url = upload_info["upload_url"]
    file_url = upload_info["file_url"]

    # Step 2: PUT the file
    req2 = urllib.request.Request(
        upload_url,
        data=image_data,
        headers={
            "Content-Type": content_type,
        },
        method="PUT",
    )

    try:
        with urllib.request.urlopen(req2) as resp:
            pass  # 200 OK = success
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha no upload da imagem ({e.code}): {body}")

    return file_url


def upload_audio(audio_path, api_key):
    """Upload de arquivo de audio para fal.ai storage. Retorna URL publica."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio nao encontrado: {audio_path}")

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    ext = os.path.splitext(audio_path)[1].lower()
    content_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
    }
    content_type = content_types.get(ext, "audio/mpeg")
    filename = os.path.basename(audio_path)

    # Same upload flow as upload_image
    initiate_url = "https://rest.alpha.fal.ai/storage/upload/initiate"
    initiate_body = json.dumps({
        "file_name": filename,
        "content_type": content_type,
    }).encode("utf-8")

    req = urllib.request.Request(
        initiate_url,
        data=initiate_body,
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            upload_info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao iniciar upload ({e.code}): {body}")

    upload_url = upload_info["upload_url"]
    file_url = upload_info["file_url"]

    req2 = urllib.request.Request(
        upload_url,
        data=audio_data,
        headers={"Content-Type": content_type},
        method="PUT",
    )

    try:
        with urllib.request.urlopen(req2) as resp:
            pass
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha no upload do audio ({e.code}): {body}")

    return file_url


def _normalize_veo_duration(dur) -> str:
    """Normaliza duracao para formato Veo: '4s', '6s' ou '8s'.

    Aceita int (4, 6, 8), float (4.0), string ('4s', '6', '8s').
    Arredonda para o valor valido mais proximo.
    """
    VEO_DURATIONS = [4, 6, 8]
    # Extrair numero
    if isinstance(dur, str):
        dur = dur.rstrip("s")
    try:
        n = float(dur)
    except (ValueError, TypeError):
        return "8s"
    # Arredondar para o valor Veo mais proximo
    best = min(VEO_DURATIONS, key=lambda x: abs(x - n))
    return f"{best}s"


def _normalize_happy_horse_duration(dur) -> int:
    """Normaliza duracao para Happy Horse: inteiro entre 3 e 15 (default 5)."""
    if isinstance(dur, str):
        dur = dur.rstrip("s")
    try:
        n = int(round(float(dur)))
    except (ValueError, TypeError):
        return 5
    return max(3, min(15, n))


def _normalize_seedance_duration(dur) -> str:
    """Normaliza duracao para Seedance: 'auto' ou string '4'..'15' (default 'auto')."""
    if dur is None or str(dur).lower() == "auto":
        return "auto"
    if isinstance(dur, str):
        dur = dur.rstrip("s")
    try:
        n = int(round(float(dur)))
    except (ValueError, TypeError):
        return "auto"
    return str(max(4, min(15, n)))


def _normalize_kling_v3_duration(dur) -> str:
    """Normaliza duracao para Kling v3 Pro: string entre '3' e '15' (default '5')."""
    if isinstance(dur, str):
        dur = dur.rstrip("s")
    try:
        n = int(round(float(dur)))
    except (ValueError, TypeError):
        return "5"
    return str(max(3, min(15, n)))


def _normalize_gemini_omni_duration(dur) -> int:
    """Normaliza duracao para Gemini Omni Flash: inteiro entre 3 e 10 (default 8)."""
    if isinstance(dur, str):
        dur = dur.rstrip("s")
    try:
        n = int(round(float(dur)))
    except (ValueError, TypeError):
        return 8
    return max(3, min(10, n))


def _normalize_gemini_omni_aspect(aspect) -> str:
    """Normaliza aspect_ratio para Gemini Omni Flash: so suporta 16:9 e 9:16."""
    if aspect in ("16:9", "9:16"):
        return aspect
    return "16:9"


def _append_dialogue_audio(prompt: str, job: dict) -> str:
    """Anexa fala (vo), SFX e ambient ao prompt visual.

    Funciona em qualquer engine que faca lip-sync via prompt (Veo, Happy Horse, Seedance).
    """
    vo_text = job.get("vo", "")
    voice_desc = job.get("voice", "")
    sfx = job.get("sfx", "")
    ambient = job.get("ambient", "")
    if vo_text:
        if voice_desc:
            prompt = f'{prompt}\n\nThe character says {voice_desc}, "{vo_text}"'
        else:
            prompt = f'{prompt}\n\nThe character says: "{vo_text}"'
    if sfx:
        prompt = f'{prompt}\nSFX: {sfx}'
    if ambient:
        prompt = f'{prompt}\nAmbient noise: {ambient}'
    return prompt


def _build_happy_horse_payload(job, default_settings, image_urls):
    """Payload Happy Horse: prompt, image_url, duration (int), resolution.

    Nao suporta aspect_ratio (segue formato da imagem), nao suporta negative_prompt.
    Audio gerado automaticamente, sem flag de controle.
    """
    job_type = job.get("type", "single_frame")
    img = job.get("image", "")

    prompt = job.get("prompt", "")
    if job_type == "dialogue":
        prompt = _append_dialogue_audio(prompt, job)

    dur = job.get("duration", default_settings.get("duration", 5))
    payload = {
        "prompt": prompt,
        "image_url": image_urls.get(img, f"<MISSING:{img}>"),
        "duration": _normalize_happy_horse_duration(dur),
        "resolution": job.get("resolution", default_settings.get("resolution", "720p")),
    }
    if job.get("seed") is not None:
        payload["seed"] = job["seed"]
    return payload


def _build_seedance_payload(job, default_settings, image_urls, fast=False):
    """Payload Seedance: prompt, image_url, duration, resolution, aspect_ratio.

    Suporta end_image_url quando type == 'start_end_frame'.
    Audio gerado automaticamente (generate_audio default true), inclui musica+SFX+lip-sync.

    fast=True usa o endpoint Seedance Fast: mesma qualidade, ~20% mais barato, mas
    resolucao limitada a 480p/720p (sem 1080p) e sem suporte documentado a 'seed'.
    """
    job_type = job.get("type", "single_frame")

    prompt = job.get("prompt", "")
    if job_type == "dialogue":
        prompt = _append_dialogue_audio(prompt, job)

    if job_type == "start_end_frame":
        img = job.get("start_image", "")
        end_img = job.get("end_image", "")
    else:
        img = job.get("image", "")
        end_img = None

    dur = job.get("duration", default_settings.get("duration", "auto"))
    aspect = job.get("aspect_ratio", default_settings.get("aspect_ratio", "auto"))
    resolution = job.get("resolution", default_settings.get("resolution", "720p"))
    if fast and resolution not in ("480p", "720p"):
        resolution = "720p"

    payload = {
        "prompt": prompt,
        "image_url": image_urls.get(img, f"<MISSING:{img}>"),
        "duration": _normalize_seedance_duration(dur),
        "resolution": resolution,
        "aspect_ratio": aspect,
    }
    if end_img:
        payload["end_image_url"] = image_urls.get(end_img, f"<MISSING:{end_img}>")
    if job.get("generate_audio") is not None:
        payload["generate_audio"] = job["generate_audio"]
    if not fast and job.get("seed") is not None:
        payload["seed"] = job["seed"]
    if fast:
        bitrate_mode = job.get("bitrate_mode", default_settings.get("bitrate_mode"))
        if bitrate_mode:
            payload["bitrate_mode"] = bitrate_mode
    return payload


def _build_kling_v3_payload(job, default_settings, image_urls):
    """Payload Kling v3 Pro: start_image_url (NAO image_url), end_image_url, duration,
    negative_prompt, cfg_scale, generate_audio.

    Unica engine do projeto que aceita negative_prompt nativamente.
    Audio nativo (musica+SFX+fala) so documentado para chines/ingles — outros idiomas
    sao auto-traduzidos para ingles pelo modelo. Para dialogue em PT-BR, testar 1 clip
    antes de batch (a fala pode sair em ingles mesmo com vo/voice em portugues).
    """
    job_type = job.get("type", "single_frame")

    prompt = job.get("prompt", "")
    if job_type == "dialogue":
        prompt = _append_dialogue_audio(prompt, job)

    if job_type == "start_end_frame":
        img = job.get("start_image", "")
        end_img = job.get("end_image", "")
    else:
        img = job.get("image", "")
        end_img = None

    dur = job.get("duration", default_settings.get("duration", 5))

    payload = {
        "prompt": prompt,
        "start_image_url": image_urls.get(img, f"<MISSING:{img}>"),
        "duration": _normalize_kling_v3_duration(dur),
    }
    if end_img:
        payload["end_image_url"] = image_urls.get(end_img, f"<MISSING:{end_img}>")

    neg = job.get("negative_prompt", default_settings.get("negative_prompt"))
    if neg:
        payload["negative_prompt"] = neg

    cfg = job.get("cfg_scale", default_settings.get("cfg_scale"))
    if cfg is not None:
        payload["cfg_scale"] = cfg

    if job.get("generate_audio") is not None:
        payload["generate_audio"] = job["generate_audio"]

    return payload


def _build_gemini_omni_payload(job, default_settings, image_urls):
    """Payload Gemini Omni Flash: prompt, image_url, duration, aspect_ratio.

    Nao suporta resolution, negative_prompt, seed nem end_image_url (start_end_frame).
    Audio (ambiente + fala) e gerado automaticamente pelo modelo, sem flag de controle.
    Dialogue funciona por prompt-injection (mesmo padrao de Veo/Happy Horse/Seedance) —
    ainda nao validado neste projeto, testar com 1 clip antes de rodar em batch.
    """
    job_type = job.get("type", "single_frame")
    img = job.get("image", "")

    prompt = job.get("prompt", "")
    if job_type == "dialogue":
        prompt = _append_dialogue_audio(prompt, job)

    dur = job.get("duration", default_settings.get("duration", 8))
    aspect = job.get("aspect_ratio", default_settings.get("aspect_ratio", "16:9"))

    payload = {
        "prompt": prompt,
        "image_url": image_urls.get(img, f"<MISSING:{img}>"),
        "duration": _normalize_gemini_omni_duration(dur),
        "aspect_ratio": _normalize_gemini_omni_aspect(aspect),
    }
    return payload


def build_request(job, default_settings, image_urls, model_override=None, engine="gemini-omni"):
    """Converte job do video-spec em endpoint + payload para fal.ai.

    Args:
        engine: engine default do CLI ("gemini-omni", "veo", "kling", "kling-v3",
                "happy-horse", "seedance", "seedance-fast").
                Pode ser sobrescrita por default_settings["engine"] do spec ou
                por job["engine"] no shot individual.
    """
    job_type = job.get("type", "single_frame")
    duration_raw = job.get("duration", default_settings.get("duration", 5))

    # Resolver engine efetiva: job > CLI (se explicito) > default_settings > "gemini-omni"
    job_engine = (
        job.get("engine")
        or engine
        or default_settings.get("engine")
        or "gemini-omni"
    )

    # Resolver endpoint
    if model_override:
        endpoint = model_override
    elif job_engine == "gemini-omni" and job_type in GEMINI_OMNI_ENDPOINTS:
        endpoint = GEMINI_OMNI_ENDPOINTS[job_type]
    elif job_engine == "veo" and job_type in VEO_ENDPOINTS:
        endpoint = VEO_ENDPOINTS[job_type]
    elif job_engine == "kling-v3" and job_type in KLING_V3_ENDPOINTS:
        endpoint = KLING_V3_ENDPOINTS[job_type]
    elif job_engine == "happy-horse" and job_type in HAPPY_HORSE_ENDPOINTS:
        endpoint = HAPPY_HORSE_ENDPOINTS[job_type]
    elif job_engine == "seedance" and job_type in SEEDANCE_ENDPOINTS:
        endpoint = SEEDANCE_ENDPOINTS[job_type]
    elif job_engine == "seedance-fast" and job_type in SEEDANCE_FAST_ENDPOINTS:
        endpoint = SEEDANCE_FAST_ENDPOINTS[job_type]
    else:
        endpoint = ENDPOINTS.get(job_type)
        if not endpoint:
            raise ValueError(f"Tipo de job desconhecido: {job_type}")
        # Fallback caiu no Kling
        job_engine = "kling"

    is_veo = job_engine == "veo"

    # --- Gemini Omni Flash ---
    if job_engine == "gemini-omni":
        return endpoint, _build_gemini_omni_payload(job, default_settings, image_urls)

    # --- Kling v3 Pro ---
    if job_engine == "kling-v3":
        return endpoint, _build_kling_v3_payload(job, default_settings, image_urls)

    # --- Happy Horse ---
    if job_engine == "happy-horse":
        return endpoint, _build_happy_horse_payload(job, default_settings, image_urls)

    # --- Seedance ---
    if job_engine == "seedance":
        return endpoint, _build_seedance_payload(job, default_settings, image_urls)

    # --- Seedance Fast ---
    if job_engine == "seedance-fast":
        return endpoint, _build_seedance_payload(job, default_settings, image_urls, fast=True)

    # --- Dialogue (Veo — fala incluída no prompt, áudio gerado automaticamente) ---
    if job_type == "dialogue":
        img = job.get("image", "")
        vo_text = job.get("vo", "")
        prompt = job.get("prompt", "")
        voice_desc = job.get("voice", "")
        sfx = job.get("sfx", "")
        ambient = job.get("ambient", "")
        if vo_text:
            if voice_desc:
                prompt = f'{prompt}\n\nThe character says {voice_desc}, "{vo_text}"'
            else:
                prompt = f'{prompt}\n\nThe character says: "{vo_text}"'
        if sfx:
            prompt = f'{prompt}\nSFX: {sfx}'
        if ambient:
            prompt = f'{prompt}\nAmbient noise: {ambient}'
        veo_dur = job.get("duration", default_settings.get("duration", 8))
        veo_dur_str = _normalize_veo_duration(veo_dur)
        payload = {
            "prompt": prompt,
            "image_url": image_urls.get(img, f"<MISSING:{img}>"),
            "duration": veo_dur_str,
            "resolution": "720p",
            "aspect_ratio": default_settings.get("aspect_ratio", "16:9"),
        }
        if job.get("negative_prompt"):
            payload["negative_prompt"] = job["negative_prompt"]
        return endpoint, payload

    # --- Veo payload (single_frame, broll, action) ---
    if is_veo and job_type in ("single_frame", "broll", "action"):
        img = job.get("image", "")
        # Veo 3.1 Lite suporta 4s, 6s, 8s — normalizar para formato string com "s"
        veo_dur = job.get("duration", default_settings.get("duration", 8))
        veo_dur_str = _normalize_veo_duration(veo_dur)
        payload = {
            "prompt": job.get("prompt", ""),
            "image_url": image_urls.get(img, f"<MISSING:{img}>"),
            "duration": veo_dur_str,
            "resolution": "720p",
            "aspect_ratio": default_settings.get("aspect_ratio", "16:9"),
        }
        # Veo 3.1 Lite NAO suporta negative_prompt — ignorar
        return endpoint, payload

    # --- Kling payloads (comportamento original) ---
    duration = str(duration_raw)

    if job_type == "start_end_frame":
        start_img = job.get("start_image", "")
        end_img = job.get("end_image", "")
        # Kling 2.5 usa "tail_image_url", Kling O3 usa "end_image_url"
        if "v2.5" in endpoint or "v2.1" in endpoint:
            end_key = "tail_image_url"
        else:
            end_key = "end_image_url"
        payload = {
            "prompt": job.get("prompt", ""),
            "image_url": image_urls.get(start_img, f"<MISSING:{start_img}>"),
            end_key: image_urls.get(end_img, f"<MISSING:{end_img}>"),
            "duration": duration,
        }
        if job.get("negative_prompt"):
            payload["negative_prompt"] = job["negative_prompt"]
    elif job_type in ("single_frame", "broll", "action"):
        img = job.get("image", "")
        payload = {
            "prompt": job.get("prompt", ""),
            "image_url": image_urls.get(img, f"<MISSING:{img}>"),
            "duration": duration,
        }
        if job.get("negative_prompt"):
            payload["negative_prompt"] = job["negative_prompt"]
    elif job_type == "text_to_video":
        payload = {
            "prompt": job.get("prompt", ""),
            "duration": duration,
        }
        if job.get("aspect_ratio"):
            payload["aspect_ratio"] = job["aspect_ratio"]
        elif default_settings.get("aspect_ratio"):
            payload["aspect_ratio"] = default_settings["aspect_ratio"]
        if job.get("negative_prompt"):
            payload["negative_prompt"] = job["negative_prompt"]
        elif default_settings.get("negative_prompt"):
            payload["negative_prompt"] = default_settings["negative_prompt"]
        # Se tem reference_image, muda para image-to-video
        ref = job.get("reference_image")
        if ref and image_urls:
            endpoint = ENDPOINTS["single_frame"]
            payload["image_url"] = image_urls.get(ref, f"<MISSING:{ref}>")
    else:
        raise ValueError(f"Tipo de job desconhecido: {job_type}")

    return endpoint, payload


def submit_request(endpoint, payload, api_key):
    """Envia request para fal.ai queue e retorna dict com request_id, status_url, response_url."""
    url = f"{FAL_API_BASE}/{endpoint}"
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {
                "request_id": result.get("request_id"),
                "status_url": result.get("status_url"),
                "response_url": result.get("response_url"),
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao submeter request ({e.code}): {body}")


def check_status(status_url, api_key):
    """Verifica status de um request na queue usando URL direta."""
    req = urllib.request.Request(
        status_url,
        headers={
            "Authorization": f"Key {api_key}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao verificar status ({e.code}): {body}")


def get_result(response_url, api_key):
    """Busca resultado de um request completado usando URL direta."""
    req = urllib.request.Request(
        response_url,
        headers={
            "Authorization": f"Key {api_key}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Falha ao buscar resultado ({e.code}): {body}")


def submit_and_wait(endpoint, payload, api_key, poll_interval=10, max_wait=600):
    """Envia request e aguarda resultado com polling."""
    submit_info = submit_request(endpoint, payload, api_key)
    request_id = submit_info["request_id"]
    status_url = submit_info["status_url"]
    response_url = submit_info["response_url"]
    print(f"  ⏳ Request enviado: {request_id}")

    elapsed = 0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        status = check_status(status_url, api_key)
        state = status.get("status", "UNKNOWN")

        if state == "COMPLETED":
            print(f"  ✅ Completado em ~{elapsed}s")
            return get_result(response_url, api_key)
        elif state in ("FAILED", "CANCELLED"):
            error = status.get("error", "Erro desconhecido")
            raise RuntimeError(f"Job falhou ({state}): {error}")
        else:
            logs = status.get("logs", [])
            last_log = logs[-1]["message"] if logs else state
            print(f"  ⏳ [{elapsed}s] {last_log}")

    raise TimeoutError(f"Timeout após {max_wait}s esperando resultado")


def download_video(url, output_path):
    """Baixa vídeo de URL para arquivo local."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            with open(output_path, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Falha ao baixar vídeo ({e.code}): {url}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  💾 Salvo: {output_path} ({size_mb:.1f}MB)")


def load_spec(spec_path):
    """Carrega e valida o video-spec.json."""
    if not os.path.exists(spec_path):
        print(f"ERROR: Spec não encontrado: {spec_path}")
        sys.exit(1)

    with open(spec_path, "r") as f:
        spec = json.load(f)

    if "jobs" not in spec:
        print("ERROR: Spec sem campo 'jobs'")
        sys.exit(1)

    return spec


def collect_image_files(jobs):
    """Coleta nomes únicos de imagens referenciadas nos jobs."""
    images = set()
    for job in jobs:
        if job.get("type") == "start_end_frame":
            images.add(job["start_image"])
            images.add(job["end_image"])
        elif job.get("type") in ("single_frame", "dialogue", "broll", "action"):
            if job.get("image"):
                images.add(job["image"])
        elif job.get("type") == "text_to_video":
            ref = job.get("reference_image")
            if ref:
                images.add(ref)
    return images


def upload_images(image_names, images_dir, api_key):
    """Faz upload de todas as imagens necessárias. Retorna dict nome→url.

    Se o nome contém '/' é tratado como path relativo ao cwd (ex: assets/model-sheets/x.png).
    Caso contrário, é resolvido dentro de images_dir.
    """
    urls = {}
    total = len(image_names)
    for i, name in enumerate(sorted(image_names), 1):
        if "/" in name or os.path.isabs(name):
            path = name
        else:
            path = os.path.join(images_dir, name)
        print(f"  📤 Upload [{i}/{total}]: {name}...", end=" ", flush=True)
        url = upload_image(path, api_key)
        urls[name] = url
        print("OK")
    return urls


def process_job(job, default_settings, image_urls, output_dir, api_key, model_override=None, engine="gemini-omni"):
    """Processa um job: build → submit → wait → download."""
    job_id = job["id"]
    endpoint, payload = build_request(job, default_settings, image_urls, model_override, engine=engine)

    print(f"\n🎬 {job_id}: {job.get('description', '')}")
    print(f"  Endpoint: {endpoint}")

    result = submit_and_wait(endpoint, payload, api_key)

    video_url = result.get("video", {}).get("url")
    if not video_url:
        print(f"  ⚠️  Resultado sem URL de vídeo: {json.dumps(result, indent=2)}")
        return None

    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    download_video(video_url, output_path)
    return output_path


# === Manifest Functions ===

def load_manifest(manifest_path):
    """Load manifest and extract video jobs from beats."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_dir = os.path.dirname(os.path.abspath(manifest_path))
    jobs = []

    for scene in manifest["scenes"]:
        for beat in scene["beats"]:
            job = beat.get("video_job")
            if not job:
                continue
            jobs.append({
                "beat_id": beat["id"],
                "beat": beat,
                "job_type": job["type"],
                "api": job.get("api", ENDPOINTS.get(job["type"])),
                "prompt": job.get("prompt", ""),
                "negative_prompt": job.get("negative_prompt", ""),
                "manifest_dir": manifest_dir,
            })

    return manifest, jobs


def build_manifest_payload(job, images_dir, api_key, dry_run=False):
    """Build payload for a manifest-based video job."""
    beat = job["beat"]
    job_type = job["job_type"]
    manifest_dir = job["manifest_dir"]

    if job_type == "lipsync":
        # Lipsync: keyframe image + audio file
        image_path = os.path.join(images_dir, beat["keyframes"][0])
        audio_path = os.path.join(manifest_dir, beat["audio_file"]) if beat.get("audio_file") else None

        if dry_run:
            return {
                "image_url": f"<upload:{image_path}>",
                "audio_url": f"<upload:{audio_path}>",
                "duration": str(beat["duration_s"]),
            }

        image_url = upload_image(image_path, api_key)
        if not audio_path:
            raise ValueError(f"Lipsync beat {beat['id']} requires audio_file")
        audio_url = upload_audio(audio_path, api_key)

        return {
            "image_url": image_url,
            "audio_url": audio_url,
            "duration": str(beat["duration_s"]),
        }

    elif job_type == "interpolation":
        # Start+end frame interpolation
        if len(beat["keyframes"]) < 2:
            raise ValueError(f"Interpolation beat {beat['id']} needs 2+ keyframes")

        start_path = os.path.join(images_dir, beat["keyframes"][0])
        end_path = os.path.join(images_dir, beat["keyframes"][-1])

        if dry_run:
            return {
                "prompt": job["prompt"],
                "image_url": f"<upload:{start_path}>",
                "end_image_url": f"<upload:{end_path}>",
                "duration": str(beat["duration_s"]),
            }

        start_url = upload_image(start_path, api_key)
        end_url = upload_image(end_path, api_key)

        endpoint = job["api"]
        if "v2.5" in endpoint or "v2.1" in endpoint:
            end_key = "tail_image_url"
        else:
            end_key = "end_image_url"

        payload = {
            "prompt": job["prompt"],
            "image_url": start_url,
            end_key: end_url,
            "duration": str(beat["duration_s"]),
        }
        if job["negative_prompt"]:
            payload["negative_prompt"] = job["negative_prompt"]
        return payload

    else:
        # action, broll, single_frame — single image
        image_path = os.path.join(images_dir, beat["keyframes"][0])

        if dry_run:
            return {
                "prompt": job["prompt"],
                "image_url": f"<upload:{image_path}>",
                "duration": str(beat["duration_s"]),
            }

        image_url = upload_image(image_path, api_key)

        payload = {
            "prompt": job["prompt"],
            "image_url": image_url,
            "duration": str(beat["duration_s"]),
        }
        if job["negative_prompt"]:
            payload["negative_prompt"] = job["negative_prompt"]
        return payload


# === CLI Commands ===

def cmd_dry_run(args):
    """Mostra payloads que seriam enviados, sem executar nem fazer upload."""
    spec = load_spec(args.spec)
    default_settings = spec.get("default_settings", {})
    jobs = spec["jobs"]

    # Usar placeholders para URLs
    image_names = collect_image_files(jobs)
    image_urls = {name: f"https://fal.storage/<uploaded>/{name}" for name in image_names}

    print(f"📋 Projeto: {spec.get('project', 'N/A')}")
    print(f"📊 Total de jobs: {len(jobs)}")
    print(f"🖼️  Imagens necessárias: {', '.join(sorted(image_names))}")
    print()

    # Verificar existência das imagens
    if args.images_dir:
        missing = []
        for name in sorted(image_names):
            path = os.path.join(args.images_dir, name)
            if not os.path.exists(path):
                missing.append(name)
        if missing:
            print(f"⚠️  Imagens faltando em {args.images_dir}:")
            for m in missing:
                print(f"   ❌ {m}")
            print()
        else:
            print(f"✅ Todas as {len(image_names)} imagens encontradas em {args.images_dir}")
            print()

    for job in jobs:
        endpoint, payload = build_request(job, default_settings, image_urls, args.model, engine=args.engine)
        print(f"--- {job['id']}: {job.get('description', '')} ---")
        print(f"  Type: {job.get('type')}")
        print(f"  Endpoint: {endpoint}")
        print(f"  Payload:")
        print(f"  {json.dumps(payload, indent=4, ensure_ascii=False)}")
        print()


def cmd_single(args):
    """Gera 1 clip específico."""
    spec = load_spec(args.spec)
    default_settings = spec.get("default_settings", {})
    api_key = get_api_key()

    # Encontrar job
    job = None
    for j in spec["jobs"]:
        if j["id"] == args.job_id:
            job = j
            break
    if not job:
        print(f"ERROR: Job '{args.job_id}' não encontrado no spec.")
        available = [j["id"] for j in spec["jobs"]]
        print(f"Jobs disponíveis: {', '.join(available)}")
        sys.exit(1)

    # Upload das imagens deste job
    image_names = set()
    if job.get("type") == "start_end_frame":
        image_names.add(job["start_image"])
        image_names.add(job["end_image"])
    else:
        image_names.add(job["image"])

    images_dir = args.images_dir
    output_dir = args.output_dir or os.path.join(os.path.dirname(args.spec), "clips")

    print(f"🎬 Gerando clip: {args.job_id}")
    print(f"📤 Fazendo upload de {len(image_names)} imagem(ns)...")
    image_urls = upload_images(image_names, images_dir, api_key)

    result_path = process_job(job, default_settings, image_urls, output_dir, api_key, args.model, engine=args.engine)

    if result_path:
        print(f"\n🎉 Clip gerado com sucesso: {result_path}")
    else:
        print(f"\n❌ Falha ao gerar clip")
        sys.exit(1)


def cmd_batch(args):
    """Gera todos os clips do spec em sequência."""
    spec = load_spec(args.spec)
    default_settings = spec.get("default_settings", {})
    jobs = spec["jobs"]
    api_key = get_api_key()

    images_dir = args.images_dir
    output_dir = args.output_dir or os.path.join(os.path.dirname(args.spec), "clips")

    # Upload de TODAS as imagens de uma vez
    image_names = collect_image_files(jobs)
    print(f"📋 Projeto: {spec.get('project', 'N/A')}")
    print(f"📊 Total de jobs: {len(jobs)}")
    print(f"📤 Fazendo upload de {len(image_names)} imagens...")
    image_urls = upload_images(image_names, images_dir, api_key)

    # Processar cada job
    results = []
    for i, job in enumerate(jobs, 1):
        print(f"\n{'='*50}")
        print(f"  Job {i}/{len(jobs)}")
        try:
            result_path = process_job(job, default_settings, image_urls, output_dir, api_key, args.model, engine=args.engine)
            results.append((job["id"], "✅", result_path))
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            results.append((job["id"], "❌", str(e)))

    # Resumo
    print(f"\n{'='*50}")
    print(f"📊 Resumo")
    print(f"{'='*50}")
    for job_id, status, detail in results:
        print(f"  {status} {job_id}: {detail}")

    success = sum(1 for _, s, _ in results if s == "✅")
    print(f"\n{success}/{len(results)} clips gerados com sucesso.")


def cmd_from_manifest(args):
    """Gera todos os clips do manifest."""
    manifest, jobs = load_manifest(args.manifest)
    manifest_dir = os.path.dirname(os.path.abspath(args.manifest))
    output_dir = args.output_dir or os.path.join(manifest_dir, "clips")

    print(f"Manifest: {args.manifest}")
    print(f"Jobs: {len(jobs)}")
    print(f"Images: {args.images_dir}")
    print(f"Output: {output_dir}")

    if args.dry_run:
        print("\nDRY RUN - nenhuma chamada de API\n")
        for job in jobs:
            payload = build_manifest_payload(job, args.images_dir, None, dry_run=True)
            print(f"--- {job['beat_id']} ({job['job_type']}) ---")
            print(f"  Endpoint: {job['api']}")
            print(f"  Payload: {json.dumps(payload, indent=4, ensure_ascii=False)}")
            print()
        return

    api_key = get_api_key()
    os.makedirs(output_dir, exist_ok=True)

    results = []
    for i, job in enumerate(jobs, 1):
        beat_id = job["beat_id"]
        print(f"\n{'='*50}")
        print(f"  Job {i}/{len(jobs)}: {beat_id} ({job['job_type']})")

        try:
            endpoint = job["api"]
            payload = build_manifest_payload(job, args.images_dir, api_key)
            result = submit_and_wait(endpoint, payload, api_key)

            video_url = result.get("video", {}).get("url")
            if not video_url:
                print(f"  Resultado sem URL de video")
                results.append((beat_id, "FAIL", "no video URL"))
                continue

            output_path = os.path.join(output_dir, f"{beat_id}.mp4")
            download_video(video_url, output_path)

            # Update manifest
            job["beat"]["clip_file"] = f"clips/{beat_id}.mp4"
            results.append((beat_id, "OK", output_path))
        except Exception as e:
            print(f"  Erro: {e}")
            results.append((beat_id, "FAIL", str(e)))

    # Save updated manifest
    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nManifest atualizado: {args.manifest}")

    # Summary
    print(f"\nResumo:")
    for beat_id, status, detail in results:
        print(f"  [{status}] {beat_id}: {detail}")


def cmd_single_beat(args):
    """Gera 1 clip de beat especifico."""
    manifest, jobs = load_manifest(args.manifest)
    manifest_dir = os.path.dirname(os.path.abspath(args.manifest))
    output_dir = args.output_dir or os.path.join(manifest_dir, "clips")

    # Find the specific job
    job = None
    for j in jobs:
        if j["beat_id"] == args.beat_id:
            job = j
            break

    if not job:
        available = [j["beat_id"] for j in jobs]
        print(f"ERROR: Beat '{args.beat_id}' nao encontrado.")
        print(f"Beats disponiveis: {', '.join(available)}")
        sys.exit(1)

    api_key = get_api_key()
    os.makedirs(output_dir, exist_ok=True)

    print(f"Beat: {args.beat_id} ({job['job_type']})")
    endpoint = job["api"]
    payload = build_manifest_payload(job, args.images_dir, api_key)
    result = submit_and_wait(endpoint, payload, api_key)

    video_url = result.get("video", {}).get("url")
    if not video_url:
        print(f"Resultado sem URL de video")
        sys.exit(1)

    output_path = os.path.join(output_dir, f"{args.beat_id}.mp4")
    download_video(video_url, output_path)

    # Update manifest
    job["beat"]["clip_file"] = f"clips/{args.beat_id}.mp4"
    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nClip gerado: {output_path}")
    print(f"Manifest atualizado: {args.manifest}")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Gera clips de video via fal.ai a partir de video-spec.json ou manifest.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Ver o que seria enviado (sem custo) — Gemini Omni Flash (padrao)
  python fal_video.py dry-run --spec video-spec-v2.json --images-dir imagens/

  # Usar Veo em vez de Gemini Omni Flash
  python fal_video.py --engine veo batch --spec video-spec-v2.json --images-dir imagens/

  # Usar Kling em vez do padrao
  python fal_video.py --engine kling batch --spec video-spec-v2.json --images-dir imagens/

  # Gerar 1 clip
  python fal_video.py single --spec video-spec-v2.json --job-id clip_02 --images-dir imagens/

  # Gerar todos os clips
  python fal_video.py batch --spec video-spec-v2.json --images-dir imagens/

  # Gerar clips do manifest (dry-run)
  python fal_video.py from-manifest --manifest manifest.json --images-dir imagens/ --dry-run

  # Gerar clips do manifest
  python fal_video.py from-manifest --manifest manifest.json --images-dir imagens/

  # Gerar 1 beat do manifest
  python fal_video.py single-beat --manifest manifest.json --beat-id cena_01a --images-dir imagens/
""",
    )

    parser.add_argument("--engine", default=None,
                        choices=["gemini-omni", "veo", "kling", "kling-v3", "happy-horse",
                                 "seedance", "seedance-fast"],
                        help="Engine de video. Se omitido, usa default_settings.engine do spec "
                             "ou 'gemini-omni' como fallback. Quando passada explicitamente, "
                             "sobrescreve o default do spec. job.engine no spec sempre vence.")

    subparsers = parser.add_subparsers(dest="command", help="Modo de operação")

    # dry-run
    p_dry = subparsers.add_parser("dry-run", help="Mostra payloads sem enviar")
    p_dry.add_argument("--spec", required=True, help="Caminho para video-spec.json")
    p_dry.add_argument("--images-dir", help="Pasta com as imagens (para validar existência)")
    p_dry.add_argument("--model", help="Override de endpoint fal.ai para todos os jobs")

    # single
    p_single = subparsers.add_parser("single", help="Gera 1 clip específico")
    p_single.add_argument("--spec", required=True, help="Caminho para video-spec.json")
    p_single.add_argument("--job-id", required=True, help="ID do job (ex: clip_02)")
    p_single.add_argument("--images-dir", required=True, help="Pasta com as imagens")
    p_single.add_argument("--output-dir", help="Pasta de saída (default: clips/ ao lado do spec)")
    p_single.add_argument("--model", help="Override de endpoint fal.ai")

    # batch
    p_batch = subparsers.add_parser("batch", help="Gera todos os clips")
    p_batch.add_argument("--spec", required=True, help="Caminho para video-spec.json")
    p_batch.add_argument("--images-dir", required=True, help="Pasta com as imagens")
    p_batch.add_argument("--output-dir", help="Pasta de saida (default: clips/ ao lado do spec)")
    p_batch.add_argument("--model", help="Override de endpoint fal.ai")

    # from-manifest
    p_manifest = subparsers.add_parser("from-manifest", help="Gera clips do manifest")
    p_manifest.add_argument("--manifest", required=True, help="Caminho para manifest.json")
    p_manifest.add_argument("--images-dir", required=True, help="Pasta com as imagens")
    p_manifest.add_argument("--output-dir", help="Pasta de saida (default: clips/ ao lado do manifest)")
    p_manifest.add_argument("--model", help="Override de endpoint fal.ai")
    p_manifest.add_argument("--dry-run", action="store_true", help="Mostra payloads sem enviar")

    # single-beat
    p_sbeat = subparsers.add_parser("single-beat", help="Gera 1 clip de beat especifico")
    p_sbeat.add_argument("--manifest", required=True, help="Caminho para manifest.json")
    p_sbeat.add_argument("--beat-id", required=True, help="ID do beat (ex: cena_01a)")
    p_sbeat.add_argument("--images-dir", required=True, help="Pasta com as imagens")
    p_sbeat.add_argument("--output-dir", help="Pasta de saida")
    p_sbeat.add_argument("--model", help="Override de endpoint fal.ai")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "dry-run":
        cmd_dry_run(args)
    elif args.command == "single":
        cmd_single(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "from-manifest":
        cmd_from_manifest(args)
    elif args.command == "single-beat":
        cmd_single_beat(args)


if __name__ == "__main__":
    main()
