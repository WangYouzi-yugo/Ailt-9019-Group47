#!/usr/bin/env python3
"""Check that the configured API key, endpoint and model work.

Reads configuration from .env (or the process environment) and makes ONE
tiny chat request. The key is never printed.

Usage:
    python check_api.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY", "").strip()
base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1").strip()
model = os.environ.get("OPENAI_MODEL", "deepseek-chat").strip()

if not api_key or "<" in api_key or "your-key" in api_key.lower():
    print("No usable OPENAI_API_KEY found.")
    print("Copy .env.example to .env and paste your own key.")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("The 'openai' package is not installed. Run:")
    print("  python -m pip install -r requirements.txt")
    sys.exit(1)

client = OpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=1)

try:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with exactly: API_OK"}],
        max_tokens=8,
        temperature=0,
    )
except Exception as exc:  # noqa: BLE001 - show the real provider error
    print(f"API check failed: {type(exc).__name__}")
    print(str(exc)[:800])
    sys.exit(2)

print("API OK")
print("model:", model)
print("endpoint:", base_url)
print("reply:", (response.choices[0].message.content or "").strip())
