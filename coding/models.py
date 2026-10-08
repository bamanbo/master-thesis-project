from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests 
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SIGMA2_HOST = "https://chat.llm.sigma2.no"
SIGMA2_BASE_URL = f"{SIGMA2_HOST}/api"

@dataclass(frozen=True)
class Arm:
    key: str
    provider: str
    model: str
    role: str
    max_tokens: int
    reasoning: bool
    supports_temperature: bool = True 
    supports_seed: bool = False
    token_param: str="max_tokens"
    temperature_behaviour: str = "unknown"

ARMS: dict[str, Arm] = {
    "normistral": Arm(
        key = "normistral",
        provider="normistral",
        model="NorMistral-11b-thinking:latest",
        role="open-weights Norwegian (11B), reasoning-tuned",
        max_tokens=4096,
        reasoning=True,
        supports_temperature=False,
        supports_seed=False,
        temperature_behaviour="ignored",
    ),

    "openai": Arm(
        key="openai",
        provider="openai",
        model="gpt-5.6-luna",
        role="commercial, cheapest current tier",
        max_tokens=4096,
        reasoning=True,
        supports_temperature=False,
        token_param="max_completion_tokens",
        temperature_behaviour="rejected",
    ),

    "anthropic": Arm(
        key="anthropic",
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        role="commercial, cheapest current tier",
        max_tokens=1024,
        reasoning=False,
        supports_temperature = False,
        temperature_behaviour="accepted",
    ),
}

def get_arm(key: str) -> Arm:
    if key not in ARMS:
        raise SystemExit(f"Unknown arm '{key}'. Choose from {', '.join(ARMS)}")
    return ARMS[key]

#-----------CLIENTS-----------
def make_client(provider:str) -> Any:
    """Raise RuntimeError so callers can handle it"""
    if provider == "normistral":
        from openai import OpenAI
        key = os.environ.get("SIGMA2_API_KEY")
        if not key:
            raise RuntimeError("SIGMA2_API_KEY missing or empty in .env")
        return OpenAI(base_url=SIGMA2_BASE_URL, api_key=key, timeout=900.0)

    if provider == "openai":
        from openai import OpenAI
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY missing or empty in .env")
        return OpenAI(timeout=300.0)

    if provider == "anthropic":
        from anthropic import Anthropic
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY missing or empty in .env")
        return Anthropic(timeout=300.0)

    raise RuntimeError(f"Unknown provider: {provider}")

def list_available(provider: str) -> list[str]:
    """Model ids the provider will actually serve"""
    if provider == "normistral":
        key = os.environ.get("SIGMA2_API_KEY")
        if not key:
            raise RuntimeError("SIGMA2_API_KEY missing or empty in .env")
        r = requests.get(f"{SIGMA2_BASE_URL}/models",
                         headers={"Authorization": f"Bearer {key}"}, timeout=60)
        r.raise_for_status()
        return sorted(str(m.get("id")) for m in r.json().get("data", []))

    c = make_client(provider)
    if provider == "openai":
        return sorted(m.id for m in c.models.list())
    if provider == "anthropic":
        return sorted(m.id for m in c.models.list(limit=100))
    return []

def verify(arm: Arm) -> dict:
    out: dict[str, Any] = {
        "arm": arm.key,
        "provider": arm.provider,
        "model_requested": arm.model,
        "role": arm.role,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        c = make_client(arm.provider)
        probe= [{"role": "user", "content": "Svar med kun tallet 7."}]

        if arm.provider == "anthropic":
            kw = {"model": arm.model, "max_tokens": 2048 if arm.reasoning else 32,
                  "messages": probe}
            if arm.supports_temperature:
                kw["temperature"] = 0
            r = c.messages.create(**kw)
            out["model_resolved"] = getattr(r, "model", arm.model)
            out["system_fingerprint"] = "n/a (provider does not emit this field)"
            out["reply"] = "".join(
                b.text for b in r.content if getattr(b, "type", "") == "text")[:160]
        else:
            kw = {"model": arm.model, "messages":probe,
                  arm.token_param: 2048 if arm.reasoning else 64}
            if arm.supports_temperature:
                kw["temperature"] = 0
            r = c.chat.completions.create(**kw)
            out["model_resolved"] = getattr(r, "model", arm.model)
            out["system_fingerprint"] = getattr(r, "system_fingerprint", None)
            out["reply"] = (r.choices[0].message.content or "")[:160]

        out["ok"] = True
    except Exception as exc:
        out["ok"] = False
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="ping each arm and print resolved provenance")
    ap.add_argument("--arm", default=None, choices=list(ARMS),
                    help="restrict --verify to a single arm")
    ap.add_argument("--list", metavar="PROVIDER", default=None,
                    choices=["normistral", "openai", "anthropic"],
                    help="list every model id a provider serves")
    args = ap.parse_args()

    if args.list:
        try:
            for m in list_available(args.list):
                print(" ", m)
        except Exception as exc:
            raise SystemExit(f"{type(exc).__name__}: {exc}")
        return

    if args.verify:
        targets = [ARMS[args.arm]] if args.arm else list(ARMS.values())
        results = []
        for arm in targets:
            r = verify(arm)
            results.append(r)
            print(f"[{'OK ' if r['ok'] else 'FAIL'}] {arm.key:11s} {arm.model}")
            if r["ok"]:
                print(f"      resolved    : {r['model_resolved']}")
                print(f"      fingerprint : {r.get('system_fingerprint')}")
                print(f"      reply       : {r['reply']!r}")
            else:
                print(f"      {r['error']}")
        print("\n--- provenance block")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    for a in ARMS.values():
        print(json.dumps(asdict(a), ensure_ascii=False))

if __name__ == "__main__":
    main()