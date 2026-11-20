import json
import shutil
import subprocess
from pathlib import Path

CHECK_DIR = Path("abap_check/src")
OUT_FILE = Path("abap_check/out.json")
SYNTAX_RULES = {"parser_error", "check_syntax", "unknown_types"}


def write_abap_files(samples):
    """samples: dict of {class_name: abap_code}. Clears the folder and writes one file per class."""
    if CHECK_DIR.exists():
        shutil.rmtree(CHECK_DIR)
    CHECK_DIR.mkdir(parents=True)
    for class_name, code in samples.items():
        path = CHECK_DIR / f"{class_name.lower()}.clas.abap"
        path.write_text(code.strip() + "\n", encoding="utf-8", newline="\n")


def run_abaplint():
    """Runs abaplint once on the whole folder and returns the list of issues."""
    npx = shutil.which("npx")  # finds npx.cmd on Windows
    subprocess.run(
        [npx, "abaplint", "--outformat", "json", "--outfile", str(OUT_FILE)],
        capture_output=True, text=True,
    )
    return json.loads(OUT_FILE.read_text(encoding="utf-8"))


def summarize(issues, class_names):
    """Groups issues per class and counts syntax errors vs. modernness warnings."""
    results = {name.lower(): {"syntax_errors": 0, "modern_warnings": 0} for name in class_names}
    for issue in issues:
        name = Path(issue["file"]).name.split(".")[0]   # "z_humaneval_000"
        if name not in results:
            continue
        if issue["key"] in SYNTAX_RULES:
            results[name]["syntax_errors"] += 1
        else:
            results[name]["modern_warnings"] += 1
    for r in results.values():
        r["syntax_ok"] = r["syntax_errors"] == 0
    return results

if __name__ == "__main__":
    import re
    from datasets import load_dataset

    ds = load_dataset("json", data_files="data/humaneval_abap.jsonl", split="train")

    # Build {class_name: code} from the reference solutions
    samples = {}
    for row in ds:
        class_name = re.search(r"CLASS\s+(\w+)\s+DEFINITION", row["definition"], re.IGNORECASE).group(1)
        samples[class_name] = row["abap_canonical_solution"]

    write_abap_files(samples)
    issues = run_abaplint()
    results = summarize(issues, samples.keys())

    ok = [name for name, r in results.items() if r["syntax_ok"]]
    failed = [name for name, r in results.items() if not r["syntax_ok"]]
    avg_warnings = sum(results[n]["modern_warnings"] for n in ok) / len(ok)

    print(f"Syntax OK: {len(ok)} / {len(results)}")
    print(f"Avg modernness warnings (syntax-OK only): {avg_warnings:.2f}")
    print("Failed:", failed)