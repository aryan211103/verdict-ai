#!/usr/bin/env python3
"""
List Granite chat/instruct models available on this watsonx.ai instance.
Run after .env is populated:  python scripts/list_watsonx_models.py
"""

import os, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

required = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"]
missing  = [k for k in required if not os.environ.get(k)]
if missing:
    sys.exit(f"Missing env vars: {missing}\nCreate .env from .env.example first.")

from ibm_watsonx_ai import Credentials, APIClient

credentials = Credentials(
    url     = os.environ["WATSONX_URL"],
    api_key = os.environ["WATSONX_API_KEY"],
)
client = APIClient(credentials, project_id=os.environ["WATSONX_PROJECT_ID"])

# Fetch all available foundation models
all_models = client.foundation_models.get_model_specs().get("resources", [])

# Filter to Granite chat / instruct models
granite_chat = [
    m for m in all_models
    if "granite" in m.get("model_id", "").lower()
    and any(kw in m.get("model_id", "").lower()
            for kw in ("chat", "instruct"))
]

print(f"Granite chat/instruct models on {os.environ['WATSONX_URL']}:\n")
for m in sorted(granite_chat, key=lambda x: x["model_id"]):
    label     = m.get("label", "")
    tasks     = [t.get("id","") for t in m.get("tasks", [])]
    lifecycle = m.get("lifecycle", [])
    status    = next((s.get("id","") for s in lifecycle if s.get("current")), "unknown")
    print(f"  {m['model_id']}")
    print(f"    label={label!r}  tasks={tasks}  status={status}")

if not granite_chat:
    print("No Granite chat/instruct models found — check your instance region.")
