#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3>=1.36,<2"]
# ///
"""Envia assets aprovados ao R2 e gera URLs públicas para a Meta.

Uso:
  uv run scripts/r2_assets.py verify
  uv run scripts/r2_assets.py upload imagem-01.png imagem-02.png \\
    --prefix estudio-exemplo/2026-01-01_demo \\
    --manifest publish/meta-assets.json

O script nunca apaga objetos. Reexecuções são idempotentes: um arquivo com a
mesma chave é mantido, a menos que --replace seja informado explicitamente.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import ClientError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT / ".env.cloudflare-r2"
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


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

    required = (
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_S3_ENDPOINT",
        "R2_BUCKET",
        "R2_PUBLIC_BASE_URL",
    )
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise RuntimeError(f"Credenciais incompletas: {', '.join(missing)}")
    return values


def r2_client(config: dict[str, str]):
    return boto3.client(
        "s3",
        endpoint_url=config["R2_S3_ENDPOINT"],
        aws_access_key_id=config["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=config["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def media_type(path: Path) -> str:
    content_type = mimetypes.guess_type(path.name)[0]
    if content_type not in SUPPORTED_IMAGE_TYPES:
        accepted = ", ".join(sorted(SUPPORTED_IMAGE_TYPES))
        raise RuntimeError(f"{path} não é uma imagem aceita ({accepted}).")
    return content_type


def object_key(prefix: str, path: Path) -> str:
    normalized_prefix = str(PurePosixPath(prefix.strip("/")))
    if not normalized_prefix or normalized_prefix == ".":
        raise RuntimeError("--prefix é obrigatório e não pode ser vazio.")
    return f"{normalized_prefix}/{path.name}"


def public_url(config: dict[str, str], key: str) -> str:
    base_url = config["R2_PUBLIC_BASE_URL"].rstrip("/")
    return f"{base_url}/{quote(key, safe='/')}"


def object_exists(client: Any, bucket: str, key: str) -> bool:
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as error:
        code = str(error.response.get("Error", {}).get("Code", ""))
        if code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def verify(config: dict[str, str]) -> int:
    response = r2_client(config).list_objects_v2(Bucket=config["R2_BUCKET"], MaxKeys=1)
    print("Conexão com R2 validada.")
    print(f"Bucket: {config['R2_BUCKET']}")
    print(f"Objetos visíveis: {response.get('KeyCount', 0)}")
    print(f"Base pública: {config['R2_PUBLIC_BASE_URL']}")
    return 0


def check_public(url: str) -> int:
    request = Request(url, method="HEAD", headers={"User-Agent": "facebookexternalhit/1.1"})
    with urlopen(request, timeout=30) as response:
        return response.status


def upload(args: argparse.Namespace, config: dict[str, str]) -> int:
    client = r2_client(config)
    bucket = config["R2_BUCKET"]
    files = [path.resolve() for path in args.files]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError(f"Arquivo(s) não encontrado(s): {', '.join(missing)}")

    manifest_items: list[dict[str, str]] = []
    for path in files:
        content_type = media_type(path)
        key = object_key(args.prefix, path)
        url = public_url(config, key)
        exists = object_exists(client, bucket, key)

        if exists and not args.replace:
            action = "skipped_existing"
            print(f"Mantido: {key}")
        else:
            client.upload_file(
                str(path),
                bucket,
                key,
                ExtraArgs={
                    "ContentType": content_type,
                    "CacheControl": "public, max-age=31536000, immutable",
                },
            )
            action = "replaced" if exists else "uploaded"
            print(f"Enviado: {key}")

        item = {
            "file": path.name,
            "object_key": key,
            "public_url": url,
            "content_type": content_type,
            "action": action,
        }
        if args.verify_public:
            try:
                item["public_http_status"] = str(check_public(url))
            except Exception as error:  # URL can take a moment to propagate.
                item["public_http_status"] = "unverified"
                item["public_check_note"] = str(error)
        manifest_items.append(item)

    manifest = {
        "schema": "briefaria/meta-assets/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "bucket": bucket,
        "public_base_url": config["R2_PUBLIC_BASE_URL"],
        "prefix": args.prefix.strip("/"),
        "assets": manifest_items,
    }
    manifest_path = args.manifest.resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifesto criado: {manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Upload seguro de imagens ao Cloudflare R2")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify", help="Testa apenas a leitura do bucket")

    upload_parser = subparsers.add_parser("upload", help="Envia imagens aprovadas e gera manifesto")
    upload_parser.add_argument("files", nargs="+", type=Path)
    upload_parser.add_argument("--prefix", required=True, help="Pasta pública, sem barra inicial")
    upload_parser.add_argument("--manifest", required=True, type=Path)
    upload_parser.add_argument("--replace", action="store_true", help="Sobrescreve objetos existentes")
    upload_parser.add_argument(
        "--verify-public",
        action="store_true",
        help="Faz HEAD nas URLs após o upload; útil antes de enviar à Meta",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = read_env(args.env_file)
        if args.command == "verify":
            return verify(config)
        if args.command == "upload":
            return upload(args, config)
        parser.error(f"Comando desconhecido: {args.command}")
    except (ClientError, RuntimeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
