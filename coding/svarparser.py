"""
svarparser.py -- one parser for every arm and every prompt variant.
"""

from __future__ import annotations

import json 
import re 
from typing import NamedTuple 

LABELS = ("UTDANNING", "ERFARING", "VERKTOY", "FORMIDLING")
TRUNCATED = frozenset({"length", "max_tokens", "MAX_TOKENS", "FinishReason.MAX_TOKENS"})
TOL = 0.05 #largest gap between stated total and sum of subscores 

_NUM = r"[0-9]+(?:[.,][0-9]+)?"
NUM_RE = re.compile(_NUM)
THINK_RE = re.compile(r"<think>.*?</think>\s*", re.S)
JSON_RE = re.compile(r"\{.*\}", re.S)
SCORE_RE = re.compile(r"(?<![A-ZÆØÅ])SCORE\W{0,3}:\s*([^\n\r]*)",re.I)
DEL_RE = re.compile(
    r"^[\s*#>\-]{0,6}(UTDANNING|ERFARING|VERKT[OØ]Y|FORMIDLING)"
    r"[^:\n\r]{0,20}:\D{0,6}(" + _NUM + ")",
    re.I | re.M)

class Parsed(NamedTuple):
    score: float | None #total, 0-100
    deler: dict[str, float] | None #subscores found, by label
    deler_sum_ok: bool | None #None where there is nothing to compare
    parse_path: str
    outcome: str #ok | truncated | no_score | empty

def _num(s: str) -> float:
    return float(s.replace(",", "."))

def _label(key: str) -> str:
    return key.upper().replace("Ø", "O")

def _score_line(tail: str):
    """(total, addends, path) from the text after SCORE:'."""
    left, eq, right = tail.rpartition("=")
    if eq and (m := NUM_RE.search(right)):
        return (_num(m.group()),
                [_num(n) for n in NUM_RE.findall(left)], "sum_total")
    nums = [_num(n) for n in NUM_RE.findall(tail)]
    if not nums:
        return None, [], "no_match"
    if "+" in tail and len(nums) > 1:
        return sum(nums), nums, "sum_added"
    return nums[0], [], "plain"

def _from_json(body:str):
    """(total, subscores, path) from JSON object, fenced or not."""
    m = JSON_RE.search(body)
    if not m:
        return None, {}, "no_match"
    try:
        obj = json.loads(m.group())
    except ValueError:
        return None, {}, "json_invalid"
    if not isinstance(obj, dict):
        return None, {}, "json_invalid"
    flat: dict = {}
    for k, v in obj.items(): #lift one nested level, e.g. "delscorer"
        flat.update(v if isinstance(v, dict) else {k:v})
    vals: dict[str, float] = {}
    for k, v in flat.items():
        if isinstance(v, str) and NUM_RE.fullmatch(v.strip()):
            v = _num(v.strip())
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            vals[_label(str(k))] = float(v)
    total = next((vals[k] for k in ("SCORE", "TOTAL", "SUM") if k in vals), None)
    return total, {k: vals[k] for k in LABELS if k in vals}, "json_score"

def parse_response(text: str | None, finish_reason=None) -> Parsed:
    cut = str(finish_reason) in TRUNCATED

    def out(path, outcome, score=None, deler=None, ok=None):
        return Parsed(score, deler or None, ok, path,
                      "truncated" if cut else outcome)

    if not text or not text.strip():
        return out("none", "empty")
    body = THINK_RE.sub("", text).strip()
    if not body:
        return out("think_only", "empty")
    if body.startswith("<think>"):
        return out("think_unterminated", "no_score")

    total, deler, addends, path = None, {}, [], "no_match"
    if "{" in body:
        total, deler, path = _from_json(body)
    if total is None and len(deler) < len(LABELS):
        json_path, path = path, "no_match"
        deler = {_label(k): _num(v) for k,v in DEL_RE.findall(body)}
        lines = SCORE_RE.findall(body)
        if lines:
            total, addends, path = _score_line(lines[-1])
        if total is None and json_path == "json_invalid":
            path = json_path

    complete = len(deler) == len(LABELS)
    stated = total is not None and path != "sum_added"
    if total is None and complete:
        total = sum(deler.values())
        path = "json_summed" if path == "json_score" else "deler_summed"
    if total is None:
        return out(path, "no_score", deler=deler)
    if not 0 <= total <= 100:
        return out("out_of_range", "no_score", deler=deler)

    parts = (list(deler.values()) if complete
             else addends if len(addends) == len(LABELS) else None)
    ok = abs(sum(parts) - total) <= TOL if parts and stated else None
    return out(path, "ok", float(total), deler, ok)