#!/usr/bin/env python3
"""Publica um carrossel já hospedado em URLs públicas no Instagram.

O manifesto precisa ser criado por scripts/r2_assets.py. Este script não envia
arquivos ao R2 e não apaga mídia. Ele cria os containers, espera o processamento
da Meta e publica somente quando todos os itens estiverem prontos.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT / ".env.meta-instagram"
FINISHED_STATUSES = {"FINISHED", "PUBLISHED"}
FAILED_STATUSES = {"ERROR", "EXPIRED"}


def read_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError(f"Arquivo de credencial não encontrado: {path}")
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    required = ("META_ACCESS_TOKEN", "META_IG_USER_ID")
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise RuntimeError(f"Credenciais incompletas: {', '.join(missing)}")
    return values


def api_base(config: dict[str, str]) -> str:
    mode = config.get("META_API_MODE", "facebook_login")
    if mode == "facebook_login":
        return "https://graph.facebook.com"
    if mode == "instagram_login":
        return "https://graph.instagram.com"
    raise RuntimeError("META_API_MODE deve ser facebook_login ou instagram_login.")


def api_url(config: dict[str, str], path: str) -> str:
    parts = [api_base(config).rstrip("/")]
    version = config.get("META_GRAPH_API_VERSION", "").strip("/")
    if version:
        parts.append(version)
    parts.append(path.lstrip("/"))
    return "/".join(parts)


def request_json(config: dict[str, str], method: str, path: str, params: dict[str, str]) -> dict[str, Any]:
    payload = {**params, "access_token": config["META_ACCESS_TOKEN"]}
    url = api_url(config, path)
    if method == "GET":
        request = Request(f"{url}?{urlencode(payload)}", headers={"Accept": "application/json"})
    else:
        request = Request(
            url,
            data=urlencode(payload).encode("utf-8"),
            method=method,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        )
    try:
        with urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
            meta_error = body.get("error", {})
            message = meta_error.get("message", "erro desconhecido")
            code = meta_error.get("code")
            subcode = meta_error.get("error_subcode")
        except (UnicodeDecodeError, json.JSONDecodeError):
            message, code, subcode = error.reason, None, None
        detail = f" (código {code}" if code is not None else ""
        detail += f", subcódigo {subcode})" if subcode is not None else ")" if code is not None else ""
        raise RuntimeError(f"Meta recusou a operação: {message}{detail}") from error
    except URLError as error:
        raise RuntimeError(f"Não foi possível chegar à API da Meta: {error.reason}") from error


def load_caption(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Legenda não encontrada: {path}")
    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.strip() == "---":
            break
        if raw_line.startswith("# "):
            continue
        lines.append(raw_line)
    caption = "\n".join(lines).strip()
    if not caption:
        raise RuntimeError("A legenda está vazia.")
    if len(caption) > 2200:
        raise RuntimeError(f"A legenda tem {len(caption)} caracteres; o limite do Instagram é 2.200.")
    return caption


def load_assets(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"Manifesto não encontrado: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not 2 <= len(assets) <= 10:
        raise RuntimeError("Um carrossel do Instagram precisa de 2 a 10 imagens no manifesto.")

    validated: list[dict[str, str]] = []
    for item in assets:
        url = item.get("public_url")
        name = item.get("file")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise RuntimeError("Todo item do manifesto precisa ter uma public_url HTTPS.")
        if not isinstance(name, str):
            raise RuntimeError("Todo item do manifesto precisa ter um nome de arquivo.")
        validated.append({"file": name, "public_url": url})
    return validated


def wait_for_container(config: dict[str, str], container_id: str, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        status = request_json(config, "GET", container_id, {"fields": "status_code,status"})
        code = status.get("status_code", "UNKNOWN")
        print(f"Container {container_id}: {code}")
        if code in FINISHED_STATUSES:
            return status
        if code in FAILED_STATUSES:
            detail = status.get("status", "sem detalhe retornado")
            raise RuntimeError(f"Container {container_id} falhou: {detail}")
        time.sleep(5)
    raise RuntimeError(f"Tempo esgotado ao processar o container {container_id}.")


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def load_state(path: Path, assets: list[dict[str, str]], caption: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema": "briefaria/instagram-publish-state/v1",
            "assets": assets,
            "caption": caption,
            "children": [],
        }
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("assets") != assets or state.get("caption") != caption:
        raise RuntimeError(
            f"O estado existente em {path} pertence a outro carrossel. Use outro --state; não o sobrescreva."
        )
    if not isinstance(state.get("children"), list):
        raise RuntimeError(f"Estado inválido em {path}: children precisa ser uma lista.")
    return state


def publish(args: argparse.Namespace, config: dict[str, str]) -> int:
    assets = load_assets(args.manifest)
    caption = load_caption(args.caption_file)
    ig_user_id = config["META_IG_USER_ID"]
    state_path = args.state.resolve()
    state = load_state(state_path, assets, caption)
    if isinstance(state.get("media_id"), str):
        print(f"Carrossel já publicado. Media ID: {state['media_id']}")
        return 0

    children = state["children"]
    if len(children) > len(assets):
        raise RuntimeError(f"Estado inválido em {state_path}: há mais containers que slides.")

    for index, asset in enumerate(assets, start=1):
        if index <= len(children):
            container_id = children[index - 1]
            if not isinstance(container_id, str):
                raise RuntimeError(f"Estado inválido em {state_path}: container de slide não é texto.")
            print(f"Slide {index}/{len(assets)} retomado: {container_id}")
        else:
            response = request_json(
                config,
                "POST",
                f"{ig_user_id}/media",
                {"image_url": asset["public_url"], "is_carousel_item": "true"},
            )
            container_id = response.get("id")
            if not isinstance(container_id, str):
                raise RuntimeError(f"A Meta não retornou container para {asset['file']}.")
            children.append(container_id)
            save_json(state_path, state)
            print(f"Slide {index}/{len(assets)} criado: {container_id}")
        wait_for_container(config, container_id, args.timeout)

    parent_id = state.get("creation_id")
    if not isinstance(parent_id, str):
        parent = request_json(
            config,
            "POST",
            f"{ig_user_id}/media",
            {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption},
        )
        parent_id = parent.get("id")
        if not isinstance(parent_id, str):
            raise RuntimeError("A Meta não retornou o container do carrossel.")
        state["creation_id"] = parent_id
        save_json(state_path, state)
        print(f"Carrossel criado: {parent_id}")
    else:
        print(f"Carrossel retomado: {parent_id}")
    wait_for_container(config, parent_id, args.timeout)

    if state.get("publish_started_at"):
        raise RuntimeError(
            "A publicação já foi iniciada e o retorno não foi registrado. Não repita a chamada; reconcilie a conta antes."
        )
    state["publish_started_at"] = datetime.now(UTC).isoformat()
    save_json(state_path, state)
    published = request_json(config, "POST", f"{ig_user_id}/media_publish", {"creation_id": parent_id})
    post_id = published.get("id")
    if not isinstance(post_id, str):
        raise RuntimeError("A Meta não retornou o ID da publicação.")

    state["media_id"] = post_id
    state["published_at"] = datetime.now(UTC).isoformat()
    save_json(state_path, state)

    result = {
        "schema": "briefaria/instagram-publish-result/v1",
        "published_at": datetime.now(UTC).isoformat(),
        "instagram_user_id": ig_user_id,
        "media_id": post_id,
        "creation_id": parent_id,
        "slides": assets,
        "caption": caption,
    }
    result_path = args.result.resolve()
    save_json(result_path, result)
    print(f"Publicado com sucesso. Media ID: {post_id}")
    print(f"Registro criado: {result_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Publica um carrossel do R2 no Instagram")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--caption-file", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path, help="Estado persistente para retomar a mesma publicação")
    parser.add_argument("--timeout", type=int, default=180, help="Tempo máximo por container, em segundos")
    args = parser.parse_args()
    try:
        return publish(args, read_env(args.env_file))
    except (RuntimeError, json.JSONDecodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
