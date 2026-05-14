import json
import re
from datetime import datetime
import math

def extract_json(text):
    if not text:
        return None
    # Try markdown code blocks first
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        blob = fence.group(1)
    else:
        # Fallback to first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        blob = text[start:end + 1]
    try:
        return json.loads(blob)
    except Exception:
        return None

def normalize_text(x):
    if x is None:
        return ""
    s = str(x).strip()
    # Clean LaTeX artifacts
    s = s.replace("\\mathrm{", "").replace("\\text{", "")
    s = s.replace("{", "").replace("}", "")
    s = s.replace("^", "").replace("_", " ")
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

def safe_get_attr(obj, attr_name, default=None):
    try:
        return getattr(obj, attr_name, default)
    except Exception:
        return default

def parse_physics_number(text):
    """Robustly extracts a number from strings like '2.52e14', '2.52 \times 10^{14}', or '-1.75 * 10^-22'."""
    s = str(text).replace(",", "").strip().lower()
    # Handle LaTeX scientific notation: 1.0 \times 10^5
    s = re.sub(r"\\times\s*10\s*(\^|e)\s*{?(-?\d+)}?", r"e\1", s)
    s = re.sub(r"\*\s*10\s*(\^|e)\s*{?(-?\d+)}?", r"e\1", s)
    # Extract first sequence that looks like a number
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE^][-+]?\d+)?", s)
    if match:
        val_str = match.group(0).replace("^", "e")
        try:
            return float(val_str)
        except ValueError:
            return None
    return None

def numeric_pass(answer_text, ground_truth, rel_tol=0.015):
    """Returns True if the extracted number is within relative tolerance of ground truth."""
    pred = parse_physics_number(answer_text)
    target = float(ground_truth)
    if pred is None:
        return False
    if target == 0:
        return abs(pred) < 1e-9
    return math.isclose(pred, target, rel_tol=rel_tol)

def build_trace(*, task_id, llm, prompt, response, parsed, final_answer, passed, failure_mode):
    return {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "task_id": task_id,
        "model": str(llm),
        "pass": bool(passed),
        "failure_mode": failure_mode,
        "final_answer": final_answer,
        "raw_output": response,
        "parsed_output": parsed,
        "prompt": prompt,
        "tokens_input": safe_get_attr(llm, "last_input_tokens"),
        "tokens_output": safe_get_attr(llm, "last_output_tokens"),
        "cost": safe_get_attr(llm, "last_cost"),
        "latency_ms": safe_get_attr(llm, "last_latency_ms"),
    }
