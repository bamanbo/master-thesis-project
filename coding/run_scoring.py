"""
For every prompt variant in prompt_varianter.json, score every CV the number of
times that variant specifies, and append each call to one JSONL log per 
arm and CV version. 

    python coding/run_scoring.py --check-ladder
    python coding/run_scoring.py --arm anthropic --n-cvs 2 --variants P0, P0d
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys 
import time
from collections import Counter 
from datetime import datetime, timezone
from pathlib import Path

from models import get_arm
from stage0_run import build_prompt, call_model
from svarparser import Parsed, parse_response

ROOT = Path(__file__).resolve().parent.parent
#DATA = ROOT / "filer_fra_Dag"
DATA = ROOT / "korpus_n150_s11"
RESULTS = ROOT / "resultater"


def load_variants(wanted: str | None) -> list[dict]:
    vs = json.loads((DATA / "prompt_varianter.json").read_text(encoding="utf-8"))
    if wanted:
        keep = [w.strip() for w in wanted.split(",")]
        known = {v["variant_id"] for v in vs}
        missing = [w for w in keep if w not in known]
        if missing:
            sys.exit(f"Unknown variant(s): {', '.join(missing)}")
        vs = [v for v in vs if v["variant_id"] in keep]
    return sorted(vs, key=lambda v: (v["avstandstrinn"], v["variant_id"]))

def load_corpus(cv_field: str, n_cvs: int) -> list[tuple[str,str]]:
    cvs = []
    with (DATA / "cv_korpus.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if cv_field not in rec:
                sys.exit(f"cv_korpus.jsonl has no field {cv_field!r} "
                         f"for {rec.get('applicant_id')}")
            cvs.append((rec["applicant_id"], rec[cv_field]))
        cvs.sort(key=lambda r: r[0])
        return cvs[:n_cvs]

def already_done(log_path: Path) -> tuple[set[tuple[str, str, int]], int]:
    """Returns (cells with outcome 'ok', total rows in the log).
    
    api_error, no_score, empty and truncated rows are not counted as done.
     Truncated is deliberate: raising the token budget should make a resume redo those cells."""

    done: set[tuple[str, str, int]] = set()
    rows = 0
    if log_path.exists():
        with log_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rows += 1
                r = json.loads(line)
                if r.get("outcome") == "ok":
                    done.add((r["prompt_variant_id"], r["applicant_id"],
                              r["rep"]))
    return done, rows

def check_ladder(cv_field: str) -> None:
    """Offline: confirm step zero is byte-identical and print the ladder."""
    vs = load_variants(None)
    ad = (DATA / "stillingsannonse.md").read_text(encoding="utf-8")
    aid, cv = load_corpus(cv_field, 1)[0]
    print(f"{'variant':8s} {'trinn':>5s} {'reps':>4s} {'template':12s} {'prompt':12s} beskrivelse")
    seen: dict[int, list[str]] = {}
    for v in vs:
        th = hashlib.sha256(v["mal"].encode("utf-8")).hexdigest()[:10]
        ph = hashlib.sha256(
            build_prompt(v["mal"], ad, cv).encode("utf-8")).hexdigest()[:10]
        print(f"{v['variant_id']:8s} {v['avstandstrinn']:5d} {v['repetisjoner']:4d} "
              f"{th:12s} {ph:12s} {v['beskrivelse']}")
        seen.setdefault(v["avstandstrinn"], []).append(v["variant_id"])
    p0 = next(v for v in vs if v["variant_id"] == "P0")["mal"]
    p0d = next((v for v in vs if v["variant_id"] == "P0d"), {}).get("mal")
    print()
    if p0d is None:
        print("FAIL: no P0d variant; step zero has no blind control")
    elif p0 == p0d:
        print(f"OK: P0 and P0d are byte-identical ({len(p0)} chars)")
    else:
        print("FAIL: P0 AND P0d differ; the noise floor would be measured "
                "on two different prompts")
    steps = sorted(seen)
    gaps = [s for s in range(min(steps), max(steps)) if s not in seen]
    if gaps:
        print(f"note: no variant at avstandstrinn {gaps}")
    for s, ids in seen.items():
        if len(ids) > 1 and s != 0:
            print(f"note: {', '.join(ids)} share avstandstrinn {s}")
    print(f"\ncalls for the full ladder: "
            f"{sum(v['repetisjoner'] for v in vs)} per candidate")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["normistral", "openai", "anthropic"])
    ap.add_argument("--variants", default=None,
                    help="comma-separated variant ids; default is all")
    ap.add_argument("--n-cvs", type=int, default=40)
    ap.add_argument("--cv-field", choices=["cv_text", "cv_text_anonymisert"],
                    default="cv_text")
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--rpm", type=float, default=0.0,
                    help="max requests per minute; 0 disables pacing")
    ap.add_argument("--max-calls", type=int, default=0,
                    help="stop after this many calls this session; 0 means all")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--check-ladder", action="store_true")
    args = ap.parse_args()

    if args.check_ladder:
        check_ladder(args.cv_field)
        return
    if not args.arm or args.temperature is None:
        sys.exit("--arm and --temperature are required "
                 "(or use --check-ladder)")

    arm = get_arm(args.arm)
    if arm.reasoning and arm.max_tokens < 2048:
        sys.exit(f"ARMS[{args.arm!r}].max_tokens = {arm.max_tokens} is too "
                 "low for a reasoning arm.")
    ad = (DATA / "stillingsannonse.md").read_text(encoding="utf-8")
    variants = load_variants(args.variants)
    cvs = load_corpus(args.cv_field, args.n_cvs)

    RESULTS.mkdir(exist_ok=True)
    cvtag = "cvanon" if args.cv_field == "cv_text_anonymisert" else "cvfull"
    log_path = RESULTS / f"run_{args.arm}_{cvtag}.jsonl"
    done, rows_logged = already_done(log_path)

    work = [(v, aid, cv, rep)
            for v in variants
            for aid, cv in cvs 
            for rep in range(v["repetisjoner"])
            if (v["variant_id"], aid, rep) not in done]
    random.Random(args.seed).shuffle(work)
    if args.max_calls:
        work = work[:args.max_calls]

    print(f"arm {args.arm} ({arm.model}) | cv_field {args.cv_field}")
    print(f"variants {', '.join(v['variant_id'] for v in variants)} "
          f"| CVs {len(cvs)} | rows logged {rows_logged} "
          f"| usable {len(done)} | retrying {rows_logged - len(done)}")
    print(f"Calls to make: {len(work)}")
    print(f"Log: {log_path}")
    if not work:
        print("Nothing to do.")
        return 
    if not args.yes and input("Proceed? [y/n] ").strip().lower() != "y":
        return

    interval = 60.0 / args.rpm if args.rpm else 0.0
    outcomes: Counter[str] = Counter()
    last = 0.0
    with log_path.open("a", encoding="utf-8") as fh:
        for i, (v, aid, cv, rep) in enumerate(work, start=1):
            if interval:
                wait = interval - (time.time() - last)
                if wait > 0:
                    time.sleep(wait)
            last = time.time()
            prompt = build_prompt(v["mal"], ad, cv)
            try:
                raw, resolved, meta = call_model(
                    args.arm, arm.model, prompt, args.temperature, arm.max_tokens)
                parsed = parse_response(raw, meta.get("finish_reason"))
                err = None
            except Exception as exc:
                raw, resolved, meta = None, arm.model, {}
                parsed = Parsed(None, None, None, "none", "api_error")
                err = f"{type(exc).__name__}: {exc}"
            outcomes[parsed.outcome] += 1

            record = {
                "applicant_id": aid,
                "prompt_variant_id": v["variant_id"],
                "avstandstrinn": v["avstandstrinn"],
                "rep": rep,
                "score": parsed.score,
                "deler": parsed.deler,
                "deler_sum_ok": parsed.deler_sum_ok,
                "parse_path": parsed.parse_path,
                "outcome": parsed.outcome,
                "error": err,
                "raw_response": raw,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt_chars": len(prompt),
                "cv_field": args.cv_field,
                "provider": args.arm,
                "model_requested": arm.model,
                "model_resolved": resolved,
                "temperature_requested": args.temperature,
                "temperature_sent": arm.supports_temperature,
                "temperature_behaviour": arm.temperature_behaviour,
                "max_tokens": arm.max_tokens,
                **meta,
                "order_seed": args.seed,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            flag = ("" if parsed.outcome == "ok"
            else f" <-- {parsed.outcome.upper()}")
            print(f"[{i}/{len(work)}] {v['variant_id']:4s} {aid} rep{rep}: "
                  f"{parsed.score}{flag}")

    print(f"\nDone. {log_path}")
    print(f"outcomes: {dict(outcomes)}")
    if outcomes["truncated"]:
        print(f"WARNING: {outcomes['truncated']} truncated responses. "
              "Truncation is non-random; report it before any score statistic.")

if __name__=="__main__":
    main()