from __future__ import annotations

import time
import argparse
import json
import random
import re
import sys 
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from models import get_arm, make_client

ROOT = Path(__file__).resolve().parent.parent 
DATA = ROOT / "filer_fra_Dag"
RESULTS = ROOT / "resultater"

load_dotenv(ROOT / ".env")

SCORE_LINE_RE = re.compile(r"SCORE\s*:\s*([^\n\r]*)", re.IGNORECASE)
NUM_RE = re.compile(r"[0-9]+(?:[.,][0-9]+)?")

def load_inputs(n_cvs: int, variant_id: str, cv_field: str):
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
                if cv_field not in rec:
                    sys.exit(f"cv_korpus.jsonl has no field {cv_field!r} "
                             f"for {rec.get('applicant_id')}")
                cvs.append((rec["applicant_id"], rec[cv_field]))
    cvs.sort(key=lambda r: r[0])
    return ad, template, cvs[:n_cvs]

def build_prompt(template: str, ad: str, cv_text: str) -> str:
    return template.replace("{stillingsannonse}", ad).replace("{cv_text}", cv_text)

def parse_score(text:str | None):
    """Returns (score, parse_path): no_match | plain | sum_total | sum_added"""
    if not text:
        return None, "no_match"
    lines = SCORE_LINE_RE.findall(text)
    if not lines:
        return None, "no_match"
    tail = lines[-1]
    if "=" in tail:
        nums = NUM_RE.findall(tail.rsplit("=", 1)[1])
        if not nums:
            return None, "no_match"
        return float(nums[0].replace(",", ".")), "sum_total"
    nums = [float(n.replace(",", ".")) for n in NUM_RE.findall(tail)]
    if not nums:
        return None, "no_match"
    if "+" in tail and len(nums) > 1:
        return sum(nums), "sum_added"
    return nums[0], "plain"

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
    """Returns (raw_text, resolved_model_id, meta)"""

    if provider not in {"normistral", "gemini", "ollama", "anthropic", "openai"}:
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
                        thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                    ),
                )
                um = r.usage_metadata
                meta = {
                    "thinking_tokens": getattr(um, "thoughts_token_count", None),
                    "prompt_tokens": getattr(um, "prompt_token_count", None),
                    "completion_tokens": getattr(um, "candidates_token_count", None),
                    "finish_reason": str(r.candidates[0].finish_reason) if r.candidates else None,
                    "system_fingerprint": None,
                }
                return r.text, getattr(r, "model_version", model), meta

            if provider in {"normistral", "openai"}:
                arm = get_arm(provider)
                c = make_client(arm.provider)
                kw = {
                    "model": arm.model,
                    "messages": [{"role": "user", "content": prompt}],
                    arm.token_param: max_tokens,
                }
                if arm.supports_temperature:
                    kw["temperature"] = temperature
                r = c.chat.completions.create(**kw)
                u = r.usage
                meta = {
                    "thinking_tokens": getattr(
                        getattr(u, "completion_tokens_details", None),
                        "reasoning_tokens", None),
                    "prompt_tokens": getattr(u, "prompt_tokens", None),
                    "completion_tokens": getattr(u, "completion_tokens", None),
                    "finish_reason": r.choices[0].finish_reason,
                    "system_fingerprint": getattr(r, "system_fingerprint", None)
                }
                return r.choices[0].message.content, r.model, meta

            if provider == "anthropic":
                arm = get_arm("anthropic")
                c = make_client(arm.provider)
                kw = {
                    "model": arm.model, 
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if arm.supports_temperature:
                    kw["temperature"] = temperature
                r = c.messages.create(**kw)
                u = r.usage
                meta = {
                    "thinking_tokens": None,
                    "prompt_tokens": getattr(u, "input_tokens", None),
                    "completion_tokens": getattr(u, "output_tokens", None),
                    "finish_reason": r.stop_reason,
                    "system_fingerprint": "n/a (provider does not emit this field)",
                }
                text = "".join(
                    b.text for b in r.content if getattr(b, "type", "") == "text")
                return text, r.model, meta

            if provider == "ollama":
                from openai import OpenAI
                c = OpenAI(base_url="http://localhost:11434/v1", api_key = "ollama")
                r = c.chat.completions.create(
                    model=model, max_tokens=max_tokens, temperature=temperature,
                    messages=[{"role":"user", "content":prompt}],
                )
                meta = {
                    "thinking_tokens": None,
                    "prompt_tokens": getattr(r.usage, "prompt_tokens", None),
                    "completion_tokens": getattr(r.usage, "completion_tokens", None),
                    "finish_reason": r.choices[0].finish_reason,
                    "system_fingerprint": getattr(r, "system_fingerprint", None),
                }
                return r.choices[0].message.content, r.model, meta

        except (AttributeError, TypeError, KeyError, NameError):
            raise
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
                    choices=["normistral", "gemini", "ollama", "anthropic", "openai"])
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
    ap.add_argument("--cv-field", choices=["cv_text", "cv_text_anonymisert"],
                    default="cv_text",
                    help="which CV version to send; cv_text carries name, " \
                    "birth year, address and any parental leave entry")
    args = ap.parse_args()

    arm = get_arm(args.provider)
    if args.model != arm.model:
        sys.exit(f"--model {args.model!r} != ARMS[{args.provider}].model {arm.model!r}; "
                 "the log would be mislabelled.")
    if arm.reasoning and args.max_tokens < 2048:
        sys.exit(f"--max-tokens {args.max_tokens} too low for a reasoning arm "
                    f"(ARMS[{args.provider!r}].max_tokens = {arm.max_tokens}).")

    ad, template, cvs = load_inputs(args.n_cvs, args.variant, args.cv_field)

    RESULTS.mkdir(exist_ok=True)
    cvtag = "cvanon" if args.cv_field == "cv_text_anonymisert" else "cvfull"
    tag = f"{args.provider}_{args.model}_t{args.temperature}_{args.variant}_{cvtag}"
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
            raw, resolved_model, meta = call_model(
                args.provider, args.model, prompt,
                args.temperature, args.max_tokens,
            )
            score, parse_path = parse_score(raw)
            record = {
                "applicant_id": aid,
                "rep": rep,
                "score": score,
                "parse_path": parse_path,
                "raw_response": raw,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt_chars": len(prompt),
                "prompt_variant_id": args.variant,
                "cv_field": args.cv_field,
                "provider": args.provider,
                "model_requested": args.model,
                "model_resolved": resolved_model,
                "temperature_requested": args.temperature,
                "temperature_sent": arm.supports_temperature,
                "temperature_behaviour": arm.temperature_behaviour,
                "max_tokens": args.max_tokens,
                **meta,
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