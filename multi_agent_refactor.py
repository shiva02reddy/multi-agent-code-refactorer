import os
import re
import json
from typing import List, Dict
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------------------------------------
# Helper Functions for File Operations
# -----------------------------------------------------------
def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def list_python_files(folder: str) -> List[str]:
    files = []
    for root, _, filenames in os.walk(folder):
        for file in filenames:
            if file.endswith(".py"):
                files.append(os.path.join(root, file))
    return files

# -----------------------------------------------------------
# LLM Call (Reusable)
# -----------------------------------------------------------
def call_agent(system_msg: str, user_msg: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
    )
    return response.choices[0].message.content

# -----------------------------------------------------------
# Agent 1: Code Analyzer
# -----------------------------------------------------------
def analyze_codebase(files: List[str]) -> Dict:
    all_issues = {}

    for file in files:
        content = read_file(file)

        prompt = f"""
        Analyze the following Python file and list ALL refactor issues:

        - Unused imports  
        - Duplicate functions  
        - No docstrings  
        - Long functions  
        - Poor naming  
        - Dead code  
        - Bad structure  

        Return output as JSON only.

        FILE CONTENT:
        {content}
        """

        result = call_agent("You are a Code Analysis Agent.", prompt)

        try:
            result_json = json.loads(result)
        except:
            result_json = {"issues": ["Unable to parse AI output"], "raw": result}

        all_issues[file] = result_json

    return all_issues

# -----------------------------------------------------------
# Agent 2: Refactor Agent
# -----------------------------------------------------------
def refactor_files(files: List[str], analysis: Dict):
    for file in files:
        content = read_file(file)

        prompt = f"""
        Based on the following issues, rewrite the ENTIRE file cleanly.

        Issues:
        {json.dumps(analysis[file], indent=2)}

        Original code:
        {content}

        Return ONLY the rewritten Python code.
        """

        result = call_agent("You are a Senior Refactor Engineer.", prompt)
        write_file(file, result)

# -----------------------------------------------------------
# Agent 3: Documentation Agent
# -----------------------------------------------------------
def add_documentation(files: List[str]):
    for file in files:
        content = read_file(file)

        prompt = f"""
        Add complete professional docstrings to all classes and functions.
        Preserve logic exactly.

        Return ONLY the new Python file.
        
        FILE:
        {content}
        """

        updated = call_agent("You are a Documentation Agent.", prompt)
        write_file(file, updated)

# -----------------------------------------------------------
# Agent 4: Reviewer & Tester Agent
# -----------------------------------------------------------
def reviewer_check(files: List[str]) -> Dict:
    all_reviews = {}

    for file in files:
        content = read_file(file)

        prompt = f"""
        Review this file for:
        - correctness
        - code quality
        - bugs
        - missing edge cases

        Give a JSON output:
        {{
          "score": 0-10,
          "problems": [...],
          "suggestions": [...]
        }}

        FILE:
        {content}
        """

        result = call_agent("You are a Code Review Agent.", prompt)

        try:
            result_json = json.loads(result)
        except:
            result_json = {"score": 0, "problems": ["Parsing error"], "raw": result}

        all_reviews[file] = result_json

    return all_reviews

# -----------------------------------------------------------
# MAIN PIPELINE
# -----------------------------------------------------------
def run_pipeline(project_folder: str):
    print("\n🔍 Scanning files...")
    files = list_python_files(project_folder)

    print(f"Found {len(files)} Python files.\n")

    print("📌 Step 1: Analyzing codebase...")
    analysis = analyze_codebase(files)

    print("🛠 Step 2: Refactoring files...")
    refactor_files(files, analysis)

    print("📝 Step 3: Adding documentation...")
    add_documentation(files)

    print("🔎 Step 4: Final review...")
    review = reviewer_check(files)

    print("\n🎉 DONE — Refactor Complete!\n")
    print(json.dumps(review, indent=2))


# -----------------------------------------------------------
# RUN
# -----------------------------------------------------------
if __name__ == "__main__":
    project_path = input("\nEnter path of the project folder to refactor: ")
    run_pipeline(project_path)
