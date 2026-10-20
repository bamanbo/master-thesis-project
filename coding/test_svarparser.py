from svarparser import parse_response

CASES = [
    # (answer, expected score, expected subscores, expected sum_ok)
    ("BEGRUNNELSE: x.\nUTDANNING: 20\nERFARING: 15\nVERKTOY:22\n"
    "FORMIDLING: 8\nSCORE:65",
    65.0, {"UTDANNING": 20, "ERFARING":15, "VERKTOY":22,
           "FORMIDLING":8}, True),
    ("BEGRUNNELSE: x. UTDANNING: 20/25 ERFARING: 20/25 "
     "VERKTØY: 22/25 FORMIDLING: 20/25 SCORE: 62",
     62.0, {"UTDANNING": 20, "ERFARING": 20, "VERKTOY": 22,
            "FORMIDLING": 20}, False),
    ("BEGRUNNELSE: x. Utdanning: 15 | Erfaring: 20 | Verktøy: 25 | "
     "Formidling: 20 | SCORE: 60",
     60.0, {"UTDANNING": 15, "ERFARING": 20, "VERKTOY": 25, "FORMIDLING": 20}, False),
    ("BEGRUNNELSE: X.\nUTDANNING: 25\nERFARING: 20\nVERKTØ: 22\n"
     "FORMIDLING: 12\nSCORE: 79",
     79.0, {"UTDANNING": 25, "ERFARING": 20, "VERKTOY":22,
            "FORMIDLING": 12}, True),
    ("BEGRUNNELSE: Erfaring er solid med 9 år, Samlet sett "
     "vurderes kandidaten til **SCORE: 58** av 100.",
     58.0, None, None),
]

def main() -> None:
    failed = 0
    for i, (text, score, deler, sum_ok) in enumerate(CASES, start=1):
        p = parse_response(text, "stop")
        got = p.deler
        if (p.score, got, p.deler_sum_ok) != (score, deler, sum_ok):
            failed += 1
            print(f"FAIL {i}: {p}")
    print(f"{len(CASES) - failed} of {len(CASES)} passed")
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()