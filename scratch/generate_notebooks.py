import csv
import json
import os
import re

# We'll clone this from Task 1
KAGGLE_METADATA = {
    "accelerator": "none",
    "dataSources": [],
    "dockerImageVersionId": 31358,
    "isInternetEnabled": True,
    "language": "python",
    "sourceType": "notebook",
    "isGpuEnabled": False
}

UTILS_CODE = """
try:
    import kaggle_benchmarks as kbench
except ImportError:
    # Failsafe: Mock the kbench harness if the library is not found (e.g. during build/commit)
    import types
    class MockTask:
        def __init__(self, f): self.f = f
        def run(self, *args, **kwargs): return self.f(*args, **kwargs)
        def evaluate(self, *args, **kwargs):
            class Res: 
                def as_dataframe(self): return None
            return Res()
        def __call__(self, *args, **kwargs): return self.f(*args, **kwargs)
    kbench = types.SimpleNamespace()
    kbench.task = lambda **kwargs: lambda f: MockTask(f)
    kbench.llm = types.SimpleNamespace(prompt=lambda p: '{"final_answer": "0.0"}')
    print('⚠️ kaggle_benchmarks not found. Running in Failsafe (Mock) mode.')

import json
import re
import math
from datetime import datetime

# (Rest of the utils remain the same...)
def extract_json(text):
    if not text: return None
    fence = re.search(r"```(?:json)?\\s*(\\{.*?\\})\\s*```", text, re.DOTALL)
    if fence: blob = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start: return None
        blob = text[start:end + 1]
    try: return json.loads(blob)
    except: return None

def numeric_pass(answer_text, ground_truth, rel_tol=0.015):
    def parse_physics_number(text):
        s = str(text).replace(",", "").strip().lower()
        s = re.sub(r"\\\\times\\s*10\\s*(\\^|e)\\s*{{?(-?\\d+)}}?", r"e\\2", s)
        s = re.sub(r"\\*\\s*10\\s*(\\^|e)\\s*{{?(-?\\d+)}}?", r"e\\2", s)
        match = re.search(r"[-+]?\\d*\\.?\\d+(?:[eE^][-+]?\\d+)?", s)
        if match:
            try: return float(match.group(0).replace("^", "e"))
            except: return None
        return None
    pred = parse_physics_number(answer_text)
    try:
        target = float(ground_truth)
        if pred is None: return False
        if target == 0: return abs(pred) < 1e-9
        return math.isclose(pred, target, rel_tol=rel_tol)
    except: return False
"""

def generate_deployment_suite(csv_path="tasks/tasks_11_40.csv", root_dir="deploy"):
    if not os.path.exists(root_dir): os.makedirs(root_dir)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        tasks = list(reader)

    upload_commands = []
    
    for row in tasks:
        task_num = re.search(r'(\d+)', row['task_id']).group(1)
        task_dir = os.path.join(root_dir, f"task_{task_num}")
        if not os.path.exists(task_dir): os.makedirs(task_dir)
        
        slug = f"fp-{task_num}-{re.sub(r'[^a-z0-0]+', '-', row['name'].lower())}"[:50].strip('-')
        
        # 1. Create Notebook
        nb = {
            "cells": [
                {"cell_type": "code", "metadata": {}, "outputs": [], "source": [
                    UTILS_CODE,
                    f"\n# Task {task_num}: {row['name']}\n",
                    f"TASK_ID = \"fp_{task_num}\"\n",
                    f"GROUND_TRUTH = {row['ground_truth']}\n",
                    "\n",
                    f"@kbench.task(name=\"FP-{task_num} {row['name']}\", description=\"{row['domain']}\")\n",
                    f"def task_{task_num}(llm) -> tuple[int, int]:\n",
                    f"    prompt = \"\"\"You are solving a frontier physics problem. Return valid JSON only.\\n\\n{row['problem_statement']}\\n\\nReturn JSON: {{\\\"final_answer\\\": \\\"<value>\\\"}}\"\"\"\n",
                    "    response = llm.prompt(prompt)\n",
                    "    parsed = extract_json(response)\n",
                    "    final_ans = parsed.get(\"final_answer\", \"\") if parsed else \"\"\n",
                    f"    passed = numeric_pass(final_ans, GROUND_TRUTH)\n",
                    f"    return (1 if passed else 0, 1)\n"
                ]},
                {"cell_type": "code", "metadata": {}, "outputs": [], "source": [f"task_{task_num}.run(kbench.llm)\n"]}
            ],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "name": "python3"},
                "kaggle": KAGGLE_METADATA
            },
            "nbformat": 4, "nbformat_minor": 4
        }
        
        nb_filename = f"task-{task_num}.ipynb"
        with open(os.path.join(task_dir, nb_filename), 'w', encoding='utf-8') as nbf:
            json.dump(nb, nbf, indent=1)

        # 2. Create kernel-metadata.json
        meta = {
            "id": f"richaflutr/{slug}",
            "title": f"FP-{task_num} {row['name']}",
            "code_file": nb_filename,
            "language": "python",
            "kernel_type": "notebook",
            "is_private": "true",
            "enable_gpu": "false",
            "enable_internet": "true"
        }
        with open(os.path.join(task_dir, "kernel-metadata.json"), 'w', encoding='utf-8') as mf:
            json.dump(meta, mf, indent=1)
            
        upload_commands.append(f"kaggle kernels push -p {task_dir}")

    # 3. Save upload script
    with open("upload_all.sh", "w") as sf:
        sf.write("#!/bin/bash\n")
        sf.write("export KAGGLE_CONFIG_DIR=~/.kaggle\n")
        # Use the full path I found earlier
        K_BIN = "/Users/richa/Library/Python/3.9/bin/kaggle"
        for cmd in upload_commands:
            sf.write(f"{K_BIN} {cmd.split('kaggle ')[1]}\n")
            
    os.chmod("upload_all.sh", 0o755)
    print(f"Deployment suite generated in {root_dir}/. Run './upload_all.sh' to push all tasks.")

if __name__ == "__main__":
    generate_deployment_suite()
