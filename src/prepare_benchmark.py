import re
from datasets import load_dataset
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Matches "CLASS <name> DEFINITION ... ENDCLASS." (lazy, so it stops at the first ENDCLASS)
DEFINITION_PATTERN = re.compile(
    r"CLASS\s+\w+\s+DEFINITION.*?ENDCLASS\s*\.",
    flags=re.DOTALL | re.IGNORECASE,
)


def extract_definition(abap_code):
    """Return the CLASS ... DEFINITION ... ENDCLASS. part, or None if not found."""
    match = DEFINITION_PATTERN.search(abap_code)
    return match.group(0) if match else None


def build_prompt(row):
    """Combine the Python task description with the required ABAP signature."""
    definition = extract_definition(row["abap_canonical_solution"])
    prompt = (
        "Implement the following task in ABAP.\n\n"
        "Task (described as a Python function):\n"
        f"{row['prompt'].strip()}\n\n"
        "Use exactly this ABAP class definition, and write both the "
        "DEFINITION and the IMPLEMENTATION:\n"
        f"{definition}\n"
    )
    return {"definition": definition, "abap_prompt": prompt}


ds = load_dataset(
    "timkoehne/LLM-ABAP-Code-Generation-Benchmark",
    data_files="dataset.jsonl",
    split="train",
)

humaneval = ds.filter(lambda row: "z_humaneval_erp_" not in row["abap_canonical_solution"].lower())
erp = ds.filter(lambda row: "z_humaneval_erp_" in row["abap_canonical_solution"].lower())

print("HumanEval tasks:", len(humaneval))
print("ERP tasks:", len(erp))

# Add the signature and the final prompt to every HumanEval task
humaneval = humaneval.map(build_prompt)

# Sanity check: every task must have a definition
failed = [row["id"] for row in humaneval if row["definition"] is None]
print("Tasks without a definition:", len(failed), failed)

humaneval.to_json(DATA_DIR / "humaneval_abap.jsonl")
erp.to_json(DATA_DIR / "erp_abap.jsonl")

print("\nExample prompt:\n")
print(humaneval[0]["abap_prompt"])