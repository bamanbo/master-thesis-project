"""
sjekk_e5.py -- checks one elicitation draft against the pilot gates.

Gates, applied to the weakest rep:
parse rate >= 98% own choice; ok rows / rows, retries counted, 
                                API errors not
distinct >= 12, Dag's E5 weakest model (metodenotat 3.1)
at cut-off <= 2 Dag's E5, E6 was rejected at 3
"""

from __future__ import annotations

import argparse 
import json 
from collections import Counter, defaultdict
from pathlib import Path

MIN_PARSE, MIN_DISTINCT, MAX_AT_K = 0.98, 12, 2



def main() -> None: 
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--k", type=int, default=None,
                    help="cut-off; default 20/150 of the CVs, rounded")
    a = ap.parse_args()

    rows = [json.loads(line) for line in 
            a.log.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [r for r in rows if r["prompt_variant_id"] == a.variant]
    if not rows:
        raise SystemExit(f"No rows for {a.variant} in {a.log}")

    judged = [r for r in rows if r["outcome"] != "api_error"]
    ok = [r for r in judged if r["outcome"] == "ok"]
    parse = len(ok) / len(judged) if judged else 0.0

    last: dict[tuple[int, str], dict] = {}
    for r in ok: #file order: the last row wins
        last[(r["rep"], r["applicant_id"])] = r
    reps: dict[int, list[float]] = defaultdict(list)
    for (rep, _), r in last.items():
        reps[rep].append(r["score"])

    n_cv = len({r["applicant_id"] for r in rows})
    k = a.k or max(1, round(n_cv * 20 / 150))
    full = {rep: s for rep, s in reps.items() if len(s) == n_cv}

    print(f"{a.variant}: {n_cv} CVs, K = {k}, {len(rows)} rows, "
          f"{len(rows) - len(judged)} API errors")
    print(f"outcomes: {dict(Counter(r['outcome'] for r in judged))}")
    bad_sum = sum(r.get("deler_sum_ok") is False for r in ok)
    no_parts = sum(len(r.get("deler") or {}) != 4 for r in ok)
    print(f"subscores: {no_parts} ok rows without all four, "
          f"{bad_sum} where they do not sum to the total")

    print(f"\n{'rep':>4s} {'distinct':>9s} {'at K':>5s} score at K")
    worst_d, worst_t = None, None
    for rep in sorted(reps):
        s = sorted(reps[rep], reverse=True)
        if rep not in full:
            print(f"{rep:4d} incomplete ({len(s)} of {n_cv}), not judged")
            continue
        d, t = len(set(s)), s.count(s[k-1])
        worst_d = d if worst_d is None else min(worst_d, d)
        worst_t = t if worst_t is None else max(worst_t, t)
        print(f"{rep:4d} {d:9d} {t:5d} {s[k - 1]}")

    if not full:
        raise SystemExit("\nFAIL: no complete rep to judge")
    assert worst_d is not None and worst_t is not None

    gates = [("parse rate", f"{parse:.1%}", parse >= MIN_PARSE),
             ("distinct (worst rep)", worst_d, worst_d >= MIN_DISTINCT),
             ("at cut-off (worst rep)", worst_t, worst_t <= MAX_AT_K)]
    print()
    for name, value, passed in gates:
        print(f"{'PASS' if passed else 'FAIL'} {name}: {value}")
    raise SystemExit(0 if all(p for *_, p in gates) else 1)

if __name__ == "__main__":
    main()

