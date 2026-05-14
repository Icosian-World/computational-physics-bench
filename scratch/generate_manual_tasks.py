import csv
import json
import os
import re

def generate_manual_style_notebooks(csv_path="tasks/tasks_11_40.csv", output_dir="tasks"):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        tasks = list(reader)

    for row in tasks:
        task_num = re.search(r'(\d+)', row['task_id']).group(1)
        if int(task_num) > 30: continue # Only doing 11-30 as requested
        
        name = row['name']
        gt = row['ground_truth']
        prompt_text = row['problem_statement']
        func_name = f"fp_{task_num}_{re.sub(r'[^a-z]+', '_', name.lower()).strip('_')}"
        
        # Cell 1: Imports, Helpers, and Task Logic
        cell1_source = [
            "import kaggle_benchmarks as kbench\n",
            "import json\n",
            "import re\n",
            "import math\n",
            "from datetime import datetime\n",
            "\n",
            "# ----------------------------\n",
            "# Global trace store\n",
            "# ----------------------------\n",
            "TRACE_LOG = []\n",
            "\n",
            "FAILURE_MODES = [\n",
            "    \"failure_to_recognize_key_aspects\",\n",
            "    \"hallucination\",\n",
            "    \"misapplication_of_equation_or_model\",\n",
            "    \"incorrect_factual_knowledge\",\n",
            "    \"calculation_error\",\n",
            "]\n",
            "\n",
            "# ----------------------------\n",
            "# Helpers\n",
            "# ----------------------------\n",
            "def extract_json(text):\n",
            "    if not text: return None\n",
            "    fence = re.search(r\"```(?:json)?\\s*(\\{.*?\\})\\s*```\", text, re.DOTALL)\n",
            "    if fence: blob = fence.group(1)\n",
            "    else:\n",
            "        start, end = text.find(\"{\"), text.rfind(\"}\")\n",
            "        if start == -1 or end == -1 or end <= start: return None\n",
            "        blob = text[start:end+1]\n",
            "    try: return json.loads(blob)\n",
            "    except: return None\n",
            "\n",
            "def numeric_pass(answer_text, target, rel_tol=0.015):\n",
            "    def parse_val(t):\n",
            "        s = str(t).replace(\" \", \"\").replace(\",\", \"\").lower()\n",
            "        s = re.sub(r\"\\\\times10\\^?{?(-?\\d+)}?\", r\"e\\1\", s)\n",
            "        m = re.search(r\"[-+]?\\d*\\.?\\d+(?:[eE^][-+]?\\d+)?\", s)\n",
            "        if m: \n",
            "            try: return float(m.group(0).replace(\"^\", \"e\"))\n",
            "            except: return None\n",
            "        return None\n",
            "    pred = parse_val(answer_text)\n",
            "    if pred is None: return False\n",
            "    try:\n",
            "        t_val = float(target)\n",
            "        if t_val == 0: return abs(pred) < 1e-9\n",
            "        return math.isclose(pred, t_val, rel_tol=rel_tol)\n",
            "    except: return False\n",
            "\n",
            f"def classify_failure_fp_{task_num}(answer_text):\n",
            "    if not answer_text or len(str(answer_text)) < 2: return \"hallucination\"\n",
            "    return \"calculation_error\" # Default for numerical tasks\n",
            "\n",
            "def build_trace(*, task_id, llm, prompt, response, parsed, final_answer, passed, failure_mode):\n",
            "    return {\n",
            "        \"timestamp_utc\": datetime.utcnow().isoformat() + \"Z\",\n",
            "        \"task_id\": task_id,\n",
            "        \"model\": str(llm),\n",
            "        \"pass\": bool(passed),\n",
            "        \"failure_mode\": failure_mode,\n",
            "        \"final_answer\": final_answer,\n",
            "        \"raw_output\": response,\n",
            "        \"parsed_output\": parsed,\n",
            "        \"prompt\": prompt\n",
            "    }\n",
            "\n",
            "# ----------------------------\n",
            f"# {name}\n",
            "# ----------------------------\n",
            f"@kbench.task(name=\"FP-{task_num} {name}\", description=\"{row['domain']}\")\n",
            f"def {func_name}(llm) -> tuple[int, int]:\n",
            f"    prompt = r\"\"\"{prompt_text}\n\nReturn JSON only in the following format:\n{{\n  \"final_answer\": \"<numeric value>\"\n}}\"\"\"\n",
            "    response = llm.prompt(prompt)\n",
            "    parsed = extract_json(response)\n",
            "    passed_checks = 0\n",
            "    final_answer = \"\"\n",
            "    failure_mode = None\n",
            "\n",
            "    if parsed is None:\n",
            "        failure_mode = \"hallucination\"\n",
            "    else:\n",
            "        final_answer = parsed.get(\"final_answer\", \"\")\n",
            f"        if numeric_pass(final_answer, {gt}):\n",
            "            passed_checks = 1\n",
            "        else:\n",
            f"            failure_mode = classify_failure_fp_{task_num}(final_answer)\n",
            "\n",
            "    trace = build_trace(\n",
            f"        task_id=\"fp_{task_num}\",\n",
            "        llm=llm, prompt=prompt, response=response, parsed=parsed, \n",
            "        final_answer=final_answer, passed=(passed_checks == 1), failure_mode=failure_mode\n",
            "    )\n",
            "    TRACE_LOG.append(trace)\n",
            "    return (passed_checks, 1)\n"
        ]
        
        # Cell 2: Run
        cell2_source = [f"{func_name}.run(kbench.llm)\n"]
        
        # Cell 3: Evaluate
        cell3_source = [f"results = {func_name}.evaluate(llm=[kbench.llm])\n", "results.as_dataframe()"]
        
        # Cell 4: Trace log display
        cell4_source = [
            "import pandas as pd\n",
            "trace_df = pd.DataFrame(TRACE_LOG)\n",
            "trace_df"
        ]
        
        # Cell 5: Stats
        cell5_source = ["trace_df[\"failure_mode\"].value_counts(dropna=False)"]
        
        # Cell 6: Export
        cell6_source = [f"trace_df.to_csv(\"fp_{task_num}_trace_log.csv\", index=False)"]

        nb = {
            "cells": [
                {"cell_type": "code", "metadata": {"trusted": True}, "outputs": [], "source": cell1_source},
                {"cell_type": "code", "metadata": {"trusted": True}, "outputs": [], "source": cell2_source},
                {"cell_type": "code", "metadata": {"trusted": True}, "outputs": [], "source": cell3_source},
                {"cell_type": "code", "metadata": {"trusted": True}, "outputs": [], "source": cell4_source},
                {"cell_type": "code", "metadata": {"trusted": True}, "outputs": [], "source": cell5_source},
                {"cell_type": "code", "metadata": {"trusted": True}, "outputs": [], "source": cell6_source}
            ],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python", "version": "3.11.15"},
                "kaggle": {"accelerator": "none", "dataSources": [], "dockerImageVersionId": 31358, "isInternetEnabled": True, "language": "python", "sourceType": "notebook", "isGpuEnabled": False}
            },
            "nbformat": 4, "nbformat_minor": 4
        }
        
        with open(os.path.join(output_dir, f"task-{task_num}.ipynb"), 'w', encoding='utf-8') as nbf:
            json.dump(nb, nbf, indent=1)
            
    print(f"Generated tasks 11-30 in {output_dir}/ in the Task 1 style.")

if __name__ == "__main__":
    generate_manual_style_notebooks()
