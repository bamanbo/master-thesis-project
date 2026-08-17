import hashlib, json, os, sys, requests
from dotenv import load_dotenv

URL = "https://chat.llm.sigma2.no/api/chat/completions"
MODEL = "NorMistral-11b-thinking:latest"
PROMPT = "Skriv en setning om en tilfeldig by i Norge."

load_dotenv()
KEY = os.environ.get("SIGMA2_API_KEY")
if not KEY:
    sys.exit("SIGMA2_API_KEY missing")
H = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}

def call(seed):
    p = {"model": MODEL,
         "messages": [{"role": "user", "content": PROMPT}],
         "max_tokens": 300}
    if seed is not None:
        p["seed"] = seed
    r = requests.post(URL, headers=H, json=p, timeout=300)
    if r.status_code != 200:
        print("HTTP", r.status_code, r.text[:400])
        return None
    t = r.json()["choices"][0]["message"]["content"]
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:12]

for seed in (None, None, 42, 42, 42, 7, 7):
    print(seed, call(seed))