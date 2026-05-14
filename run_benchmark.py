import os
import json
import re
from datetime import datetime

class MockLLM:
    """Mock LLM to verify the harness and problem statements."""
    def prompt(self, text):
        # We simulate a failure response to prove the pipeline is alive
        return '{"final_answer": "0.0"}'
    def __str__(self):
        return "Local-Test-Harness"

def extract_code_from_ipynb(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
        code = ""
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                # Skip the .run() cell to avoid redundant calls
                cell_content = "".join(cell['source'])
                if ".run(" not in cell_content and ".evaluate(" not in cell_content:
                    code += cell_content + "\n"
        return code

def run_notebook_task(filepath, llm):
    """Executes the task logic inside the notebook programmatically."""
    code = extract_code_from_ipynb(filepath)
    
    # Create a mock for kaggle_benchmarks
    mock_kbench = type('obj', (object,), {
        "task": lambda **kwargs: lambda f: f,
        "llm": llm
    })
    
    # Inject into sys.modules so 'import kaggle_benchmarks' works
    import sys
    import types
    mod = types.ModuleType("kaggle_benchmarks")
    mod.task = mock_kbench.task
    mod.llm = mock_kbench.llm
    sys.modules["kaggle_benchmarks"] = mod

    namespace = {
        "kaggle_benchmarks": mod,
        "kbench": mod,
        "llm": llm
    }
    
    try:
        # Execute the setup and task definition
        exec(code, namespace)
        
        # Find the task function (e.g., task_11)
        task_num = re.search(r'task-(\d+)', filepath).group(1)
        func_name = f"task_{task_num}"
        
        if func_name in namespace:
            task_func = namespace[func_name]
            passed, total = task_func(llm)
            return passed, total, "Success"
        else:
            return 0, 1, f"Error: {func_name} not found in NB"
    except Exception as e:
        return 0, 1, f"Exception: {str(e)}"

def initiate_build_and_test():
    print("🚀 Initiating Build and Test Sequence for Tasks 11-40...\n")
    tasks_dir = "tasks"
    llm = MockLLM()
    
    results = []
    
    # Sort files to run in order 11, 12, 13...
    files = [f for f in os.listdir(tasks_dir) if f.startswith("task-") and f.endswith(".ipynb")]
    # Extract numbers for sorting
    files.sort(key=lambda x: int(re.search(r'(\d+)', x).group(1)))

    for filename in files:
        task_num = int(re.search(r'(\d+)', filename).group(1))
        if 11 <= task_num <= 40:
            print(f"Testing {filename}...", end=" ", flush=True)
            path = os.path.join(tasks_dir, filename)
            passed, total, status = run_notebook_task(path, llm)
            
            # Since we are using MockLLM, 'passed' will be 0, which is EXPECTED.
            # We are verifying that the code EXECUTED without errors.
            is_built = "✅ BUILT" if "Success" in status else f"❌ FAILED ({status})"
            print(is_built)
            
            results.append({
                "task_id": f"fp_{task_num}",
                "status": status,
                "built": "Success" in status
            })

    print("\n" + "="*30)
    print("      BUILD REPORT")
    print("="*30)
    print(f"Total Tasks Attempted: {len(results)}")
    success_count = sum(1 for r in results if r['built'])
    print(f"Successfully Built:    {success_count}")
    print("="*30)
    
    if success_count == len(results):
        print("\n✨ ALL TASKS ARE BUILT AND READY FOR DEPLOYMENT.")
    else:
        print("\n⚠️ SOME TASKS FAILED TO BUILD. CHECK LOGS.")

if __name__ == "__main__":
    initiate_build_and_test()
