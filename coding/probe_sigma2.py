import hashlib
import json 
import os
import sys
import time 
import requests 
from dotenv import load_dotenv

URL = "https://chat.llm.sigma2.no/api/chat/completions"
MODEL = "NorMistral-11b-thinking:latest"
PROMPT = "Skriv en setning om en tilfeldig by i Norge."
REPS = 5
MAX_TOKENS = 300
TEMPS = [0.0, 2.0]

load_dotenv()
API_KEY = os.environ.get("SIGMA2_API_KEY")
if not API_KEY:
    sys.exit("SIGMA2_API_KEY not found in .env")

HEADERS = {
    "Authorization": "Bearer " + API_KEY,
    "Content-Type": "application/json",
}

def call(temperature):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": temperature,
        "max_tokens": MAX_TOKENS,
    }
    t0 = time.time()
    r = requests.post(URL, headers=HEADERS, json=payload, timeout=300)
    dt = time.time() - t0
    r.raise_for_status()
    data = r.json()
    choice = data["choices"][0]
    text = choice["message"]["content"]
    finish = choice.get("finish_reason")
    fp = data.get("system_fingerprint")
    return text, finish, fp, dt

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

def main():
    results = {}
    for temp in TEMPS:
        print("\n=== temperature = {} ===".format(temp))
        hashes = []
        for i in range(REPS):
            try:
                text, finish, fp, dt = call(temp)
            except Exception as e:
                print("  rep {}: ERROR {}".format(i+1, e))
                continue
            h = digest(text)
            hashes.append(h)
            preview = " ".join(text.split())[:70]
            print(" rep{}: {} {:.1f}s finish={} fp={}".format(
                i + 1, h, dt, finish, fp))
            print("     {}".format(preview))
        results[temp] = hashes

    print("\n=== summary ===")
    for temp in TEMPS:
        hs = results.get(temp, [])
        print(" t={}: {} calls, {} distinct".format(temp, len(hs), len(set(hs))))

    lo = set(results.get(TEMPS[0], []))
    hi = set(results.get(TEMPS[-1], []))
    if not lo or not hi:
        verdict = "INCONCLUSIVE. Calls failed."
    elif len(lo) == 1 and len(hi)>1:
        verdict = "HONOURED. t=0 deterministic, t=2 varies"
    elif len(lo) == 1 and len(hi)==1:
            verdict = "INCONCLUSIVE. Deterministic at both. Sampling may be pinned or ignored."
    elif len(hi) > len(lo):
        verdict = "PARTIAL. t=0 not deterministic, but t=2 varies more"
    else:
        verdict = "NOT HONOURED. t=0 varies as much as t=2"
    print("\n VERDICT: " + verdict)

    out = {
        "model": MODEL, 
        "prompt": PROMPT,
        "reps": REPS,
        "max_tokens": MAX_TOKENS,
        "hashes": {str(k): v for k, v in results.items()},
        "verdict": verdict,
    }
    with open("resultater/probe_sigma2.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("  written: resultater/probe_sigma.json")

if __name__ == "__main__":
    main()

    

