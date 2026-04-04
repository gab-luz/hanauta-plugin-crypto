#!/usr/bin/env python3
from __future__ import annotations

SERVICE_KEY = "crypto_widget"


def register_hanauta_plugin() -> dict[str, object]:
    """Metadata-only plugin entrypoint for the crypto widget scripts."""
    return {
        "id": SERVICE_KEY,
        "name": "Crypto Widget",
        "api_min_version": 1,
        "service_sections": [],
    }
