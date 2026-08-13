"""
Stage 0: estimate the within-candidate score noise floor (sigma).

Runs one prompt variant N times per CV against one model and appends every cal lto a JSONL log.
Resumable: re-running skips (applicant_id, rep) pairs already logged.
"""
from __future__ import annotations

import time
import argparse
import json
import random
import re
import sys 
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent 
DATA = ROOT / "filer_fra_Dag"
RESULTS = ROOT / "resultater"

load_dotenv(ROOT / ".env")

SCORE_RE = re.compile(r"SCORE\s*:\s*([0-9]+(?:[.,][0-9]+)?)", re.IGNORECASE)

def load_inputs(n_cvs: int, variant_id: str):
    ad = (DATA / "stillingsannonse.md").read_text(encoding="utf-8")

    variants = json.loads((DATA / "prompt_varianter.json").read_text(encoding="utf-8"))

    try:
        template = next(v["mal"] for v in variants if v["variant_id"] == variant_id)
    except StopIteration:
        sys.exit(f"No prompt variant '{variant_id}' in prompt_varianter.json")

    cvs = []
    with (DATA / "cv_korpus.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rec = json.loads(line)
                cvs.append((rec["applicant_id"], rec["cv_text"]))
    cvs.sort(key=lambda r: r[0])
    return ad, template, cvs[:n_cvs]

def build_prompt(template: str, ad: str, cv_text: str) -> str:
    return template.replace("{stillingsannonse}", ad).replace("{cv_text}", cv_text)

def parse_score(text:str):
    if not text:
        return None
    matches = SCORE_RE.findall(text)
    if not matches:
        return None
    return float(matches[-1].replace(",","."))

def already_done(log_path: Path) -> set[tuple[str,int]]:
    done = set()
    if log_path.exists():
        with log_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    done.add((rec["applicant_id"], rec["rep"]))
    return done

def call_model(provider, model, prompt, temperature, max_tokens, max_retries=8):
    """Returns (raw_text, resolved_model_id, thinking_tokens)"""

    if provider not in {"gemini", "ollama", "anthropic", "openai"}:
        raise ValueError(f"Unknown provider: {provider}")
    
    delay = 15.0 
    for attempt in range(max_retries):
        try:
            if provider == "gemini":
                from google import genai
                from google.genai import types
                client = genai.Client()
                r = client.models.generate_content(
                    model = model,
                    contents = prompt,
                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        thinking_config=types.ThinkingConfig(thinking_level="low"),
                    ),
                )
                thinking = getattr(r.usage_metadata, "thoughts_token_count", None)
                return r.text, getattr(r, "model_version", model), thinking

            # if provider == "anthropic":
            #     from anthropic import Anthropic

            # if provider == "openai":
            #     from openai import OpenAI

            if provider == "ollama":
                from openai import OpenAI
                c = OpenAI(base_url="http://localhost:11434/v1", api_key = "ollama")
                r = c.chat.completions.create(
                    model=model, max_tokens=max_tokens, temperature=temperature,
                    messages=[{"role":"user", "content":prompt}],
                )
                return r.choices[0].message.content, r.model, None

        except Exception as exc:
            if attempt == max_retries - 1:
                raise 
            print(f"   retry {attempt + 1} after error: {exc}")
            time.sleep(delay)
            delay = min(delay * 2, 120)
    raise RuntimeError(f"call_model exhausted retrues for provider={provider}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True,
                    choices=["gemini", "ollama", "anthropic", "openai"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--temperature", type=float, required=True)
    ap.add_argument("--max-tokens", type=int, default=300)
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--n-cvs", type=int, default=20)
    ap.add_argument("--variant", default="P0")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.0,
                    help="seconds to wait between calls")
    args = ap.parse_args()

    ad, template, cvs = load_inputs(args.n_cvs, args.variant)

    RESULTS.mkdir(exist_ok=True)
    tag = f"{args.provider}_{args.model}_t{args.temperature}_{args.variant}"
    tag = tag.replace(".", "-").replace("/", "-").replace(":", "-")
    log_path = RESULTS / f"stage0_{tag}.jsonl"

    done = already_done(log_path)
    work = [
        (aid, cv, rep)
        for aid,cv in cvs
        for rep in range(args.reps)
        if (aid, rep) not in done
    ]
    random.Random(args.seed).shuffle(work)

    print(f"CVs: {len(cvs)} | reps: {args.reps} | already logged: {len(done)}")
    print(f"Calls to make: {len(work)}")
    print(f"Log: {log_path}")
    if not work:
        print("Nothing to do.")
        return
    if not args.yes and input("Proceed? [y/n] ").strip().lower() != "y":
        return

    with log_path.open("a", encoding="utf-8") as fh:
        for i, (aid, cv_text, rep) in enumerate(work, start=1):
            prompt = build_prompt(template, ad, cv_text)
            raw, resolved_model, thinking = call_model(
                args.provider, args.model, prompt,
                args.temperature, args.max_tokens,
            )
            record = {
                "applicant_id": aid,
                "rep": rep,
                "score": parse_score(raw),
                "raw_response": raw,
                "prompt_variant_id": args.variant,
                "provider": args.provider,
                "model_requested": args.model,
                "model_resolved": resolved_model,
                "temperature": args.temperature,
                "max_tokens": args.max_tokens,
                "thinking_tokens": thinking,
                "order_seed": args.seed,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }

            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()

            flag = "" if record["score"] is not None else "  <-- PARSE FAILURE"
            print(f"[{i}/{len(work)}] {aid} rep{rep}: {record['score']}{flag}")

            if args.sleep:
                time.sleep(args.sleep)

    print(f"\nDone. {log_path}")

if __name__ == "__main__":
    main()