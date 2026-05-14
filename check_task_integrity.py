import csv
import json
import os
import re

def check_integrity(csv_path="tasks/tasks_11_40.csv", tasks_dir="tasks"):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    missing = []
    mismatches = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Match '11Ex' to 'task-11.ipynb' or 'task_11.ipynb'
            task_num = re.search(r'(\d+)', str(row['task_id'])).group(1)
            notebook_path = os.path.join(tasks_dir, f"task-{task_num}.ipynb")
            
            if not os.path.exists(notebook_path):
                missing.append(f"Task {task_num} (Missing {notebook_path})")
                continue
            
            with open(notebook_path, 'r', encoding='utf-8') as nbf:
                try:
                    nb = json.load(nbf)
                    content = ""
                    for cell in nb['cells']:
                        if cell['cell_type'] == 'code':
                            content += "".join(cell['source'])
                    
                    # Check Ground Truth
                    # Search for GROUND_TRUTH = <val>
                    gt_match = re.search(r"GROUND_TRUTH\s*=\s*([-+]?\d*\.?\d+(?:[eE^][-+]?\d+)?)", content)
                    if gt_match:
                        gt_val = gt_match.group(1).strip()
                        try:
                            if float(gt_val) != float(row['ground_truth']):
                                mismatches.append(f"Task {task_num} GT Mismatch: CSV({row['ground_truth']}) vs NB({gt_val})")
                        except:
                            if gt_val != str(row['ground_truth']):
                                mismatches.append(f"Task {task_num} String Mismatch: CSV({row['ground_truth']}) vs NB({gt_val})")
                    
                    # Check Problem Statement snippet existence
                    snippet = row['problem_statement'][:50] # Check first 50 chars
                    if snippet not in content:
                        mismatches.append(f"Task {task_num} Prompt Mismatch or Missing.")

                except Exception as e:
                    mismatches.append(f"Task {task_num} Parse Error: {str(e)}")

    print("\n=== INTEGRITY REPORT ===")
    if not missing and not mismatches:
        print("✅ SUCCESS: All tasks consistent with CSV.")
    else:
        if missing:
            print(f"❌ MISSING TASKS ({len(missing)}):")
            for m in missing: print(f"  - {m}")
        if mismatches:
            print(f"❌ MISMATCHES ({len(mismatches)}):")
            for m in mismatches: print(f"  - {m}")

if __name__ == "__main__":
    check_integrity()
