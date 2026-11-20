from datasets import load_dataset
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

ds = load_dataset(
    "timkoehne/LLM-ABAP-Code-Generation-Benchmark",
    data_files="dataset.jsonl",
    split="train",
)

humaneval = ds.filter(lambda row: "z_humaneval_erp_" not in row["abap_canonical_solution"].lower())
erp = ds.filter(lambda row: "z_humaneval_erp_" in row["abap_canonical_solution"].lower())

print("HumanEval tasks:", len(humaneval))
print("ERP tasks:", len(erp))

humaneval.to_json(DATA_DIR / "humaneval_abap.jsonl")
erp.to_json(DATA_DIR / "erp_abap.jsonl")