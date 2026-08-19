import hashlib, json, os, sys, requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "resultater"

URL = "https://chat.llm.sigma2.no/api/chat/completions"
MODEL = "NorMistral-11b-thinking:latest"
PROMPT = "Skriv en setning om en tilfeldig by i Norge."
MAX_TOKENS = 300
SEEDS = (None, None, 42, 42, 42, 7, 7)

load_dotenv(ROOT / ".env")
KEY = os.environ.get("SIGMA2_API_KEY")
if not KEY:
    sys.exit("SIGMA2_API_KEY missing")
H = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}

def call(seed):
    p = {"model": MODEL,
         "messages": [{"role": "user", "content": PROMPT}],
         "max_tokens": MAX_TOKENS}
    if seed is not None:
        p["seed"] = seed
    r = requests.post(URL, headers=H, json=p, timeout=300)
    if r.status_code != 200:
        print("HTTP", r.status_code, r.text[:400])
        return None, None, r.status_code
    t = r.json()["choices"][0]["message"]["content"]
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:12], t, 200

calls = []
for seed in SEEDS:
    h, t, status = call(seed)
    print(seed, h)
    calls.append({"seed": seed, "http_status": status, "sha256_12": h,
                  "chars": len(t or ""), "response_prefix": (t or "")[:600]})

hashes = [c["sha256_12"] for c in calls if c["sha256_12"]]
by_seed = {}
for c in calls:
    if c["seed"] is not None and c["sha256_12"]:
        by_seed.setdefault(c["seed"], []).append(c["sha256_12"])
repeats = {s: v for s, v in by_seed.items() if len(v) > 1}
honoured = bool(repeats) and all(len(set(v)) == 1 for v in repeats.values())

out = {
    "probe": "seed",
    "model": MODEL,
    "prompt": PROMPT,
    "max_tokens": MAX_TOKENS,
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "n_calls": len(hashes),
    "distinct_hashes": len(set(hashes)),
    "seeds_repeated": {str(s): len(v) for s, v in repeats.items()},
    "calls": calls,
    "verdict": ("HONOURED. repeated calls at the same seed matched"
                if honoured else
                "NOT HONOURED. repeated calls at the same seed produced "
                "different output; parameter accepted with no effect"),

}

RESULTS.mkdir(exist_ok=True)
path = RESULTS / "probe_seed.json"
path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{len(set(hashes))}/{len(hashes)} distinct -> {path}")
print(out["verdict"])
