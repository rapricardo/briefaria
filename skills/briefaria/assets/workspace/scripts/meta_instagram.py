#!/usr/bin/env python3
"""Verifica uma conexão de publicação do Instagram sem publicar conteúdo.

Uso:
  python scripts/meta_instagram.py verify
  python scripts/meta_instagram.py verify --env-file caminho/.env.meta-instagram
  python scripts/meta_instagram.py media --media-id 123456789

O script nunca exibe o access token. Para publicação, as imagens deverão estar
em URLs HTTPS públicas; essa etapa será criada depois que a conexão for validada.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT / ".env.meta-instagram"


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
    return values


def api_url(base_url: str, api_version: str, path: str) -> str:
    segments = [base_url.rstrip("/")]
    if api_version:
        segments.append(api_version.strip("/"))
    segments.append(path.lstrip("/"))
    return "/".join(segments)


def get_json(url: str, params: dict[str, str]) -> dict[str, Any]:
    request_url = f"{url}?{urlencode(params)}"
    request = Request(request_url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            message = payload.get("error", {}).get("message", "erro desconhecido")
            code = payload.get("error", {}).get("code")
        except (UnicodeDecodeError, json.JSONDecodeError):
            message = error.reason
            code = None
        suffix = f" (código {code})" if code is not None else ""
        raise RuntimeError(f"Meta recusou a verificação: {message}{suffix}") from error
    except URLError as error:
        raise RuntimeError(f"Não foi possível chegar à API da Meta: {error.reason}") from error


def verify_facebook_login(config: dict[str, str]) -> dict[str, Any]:
    token = config["META_ACCESS_TOKEN"]
    version = config.get("META_GRAPH_API_VERSION", "")
    base = "https://graph.facebook.com"
    page_id = config.get("META_PAGE_ID", "")
    ig_user_id = config.get("META_IG_USER_ID", "")

    if ig_user_id:
        return get_json(
            api_url(base, version, ig_user_id),
            {"fields": "id,username", "access_token": token},
        )

    path = page_id if page_id else "me/accounts"
    params = {
        "access_token": token,
        "fields": "id,name,instagram_business_account{id,username}",
    }
    return get_json(api_url(base, version, path), params)


def verify_instagram_login(config: dict[str, str]) -> dict[str, Any]:
    token = config["META_ACCESS_TOKEN"]
    version = config.get("META_GRAPH_API_VERSION", "")
    ig_user_id = config.get("META_IG_USER_ID", "") or "me"
    return get_json(
        api_url("https://graph.instagram.com", version, ig_user_id),
        {"fields": "id,username", "access_token": token},
    )


def verify(env_file: Path) -> int:
    config = read_env(env_file)
    token = config.get("META_ACCESS_TOKEN", "")
    if not token:
        print(f"Preencha META_ACCESS_TOKEN em {env_file} e rode novamente.")
        return 2

    mode = config.get("META_API_MODE", "facebook_login")
    if mode == "facebook_login":
        payload = verify_facebook_login(config)
    elif mode == "instagram_login":
        payload = verify_instagram_login(config)
    else:
        print("META_API_MODE deve ser facebook_login ou instagram_login.", file=sys.stderr)
        return 2

    print("Conexão com a Meta validada. Token não exibido.")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("\nPróximo passo: confirme a conta acima; então registraremos META_IG_USER_ID e a origem HTTPS dos assets.")
    return 0


def media(env_file: Path, media_id: str) -> int:
    """Consulta o registro de uma publicação já criada, sem alterar nada."""
    config = read_env(env_file)
    token = config.get("META_ACCESS_TOKEN", "")
    if not token:
        print(f"Preencha META_ACCESS_TOKEN em {env_file} e rode novamente.")
        return 2

    mode = config.get("META_API_MODE", "facebook_login")
    if mode == "facebook_login":
        base = "https://graph.facebook.com"
    elif mode == "instagram_login":
        base = "https://graph.instagram.com"
    else:
        print("META_API_MODE deve ser facebook_login ou instagram_login.", file=sys.stderr)
        return 2

    payload = get_json(
        api_url(base, config.get("META_GRAPH_API_VERSION", ""), media_id),
        {"fields": "id,permalink,timestamp,media_type", "access_token": token},
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validação segura da API do Instagram")
    parser.add_argument("command", choices=["verify", "media"])
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--media-id", help="ID de uma publicação já criada (usado com media)")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            return verify(args.env_file)
        if not args.media_id:
            print("--media-id é obrigatório com o comando media.", file=sys.stderr)
            return 2
        return media(args.env_file, args.media_id)
    except RuntimeError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
