"""
pull_provider_csv.py

Fetch provider CSV feeds and ingest into DB outliers.

Usage:
  python backend/scripts/pull_provider_csv.py --config backend/provider_sources.json
"""
import argparse
import asyncio
import json
import os
import sys
import tempfile
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "scripts"))

from ingest_outlier_csv_db import main_async as ingest_csv


def load_sources(config_path: str) -> List[Dict[str, Any]]:
    env_sources = os.environ.get("KOMISSION_PROVIDER_SOURCES")
    if env_sources:
        return json.loads(env_sources)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def download_csv(url: str, headers: Dict[str, str]) -> str:
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(response.content)
            return tmp.name


def build_headers(source: Dict[str, Any]) -> Dict[str, str]:
    headers = {}
    if isinstance(source.get("headers"), dict):
        headers.update(source["headers"])
    if source.get("cookie"):
        headers["Cookie"] = source["cookie"]
    return headers


async def main_async(args: argparse.Namespace) -> None:
    sources = load_sources(args.config)
    if not isinstance(sources, list):
        raise ValueError("Provider config must be a list of sources.")

    for source in sources:
        name = source.get("name", "provider")
        url = source.get("url")
        if not url:
            continue

        headers = build_headers(source)
        csv_path = await download_csv(url, headers)

        ingest_args = argparse.Namespace(
            csv=csv_path,
            source_name=name,
            category=source.get("category"),
            platform=source.get("platform"),
        )
        await ingest_csv(ingest_args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch provider CSV feeds and ingest into DB")
    parser.add_argument("--config", default=os.path.join(BASE_DIR, "provider_sources.json"))
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
