"""Size and complexity gate for lab 10. The agent must not edit this file.

Usage: python check_budget.py [SRC_DIR] [TESTS_DIR]   (defaults: src tests)
Needs: ruff, radon, complexipy. Exit code 0 means everything is within budget.
SLOC = radon's source lines: blank and comment-only lines are not counted.
"""

import json
import subprocess
import sys
from pathlib import Path

from complexipy import file_complexity
from radon.complexity import cc_visit
from radon.raw import analyze
from radon.visitors import Function

LIMITS = {
    "src_sloc_total": 700,
    "src_sloc_per_file": 200,
    "tests_sloc_total": 300,
    "cyclomatic_per_function": 8,
    "cognitive_per_function": 10,
}
RUFF_RULES = "E,F,W,I,B,UP,C901,PLR0911,PLR0912,PLR0913,PLR0915"
RUFF_LIMITS = [
    "lint.mccabe.max-complexity = 8",
    "lint.pylint.max-branches = 8",
    "lint.pylint.max-statements = 30",
    "lint.pylint.max-args = 5",
    "lint.pylint.max-returns = 4",
    "line-length = 100",
]


def python_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.rglob("*.py") if ".venv" not in p.parts)


def sloc(path: Path) -> int:
    return analyze(path.read_text(encoding="utf-8")).sloc


def worst_functions(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    cyclomatic = [b.complexity for b in cc_visit(text) if isinstance(b, Function)]
    cognitive = [f.complexity for f in file_complexity(str(path), no_ignore=True).functions]
    return max(cyclomatic, default=0), max(cognitive, default=0)


def measure(src: Path) -> list[tuple[Path, int, int, int]]:
    return [(path, sloc(path), *worst_functions(path)) for path in python_files(src)]


def over_limit(label: str, value: int, key: str) -> list[str]:
    return [f"{label}: {value} > {LIMITS[key]}"] if value > LIMITS[key] else []


def file_problems(path: Path, lines: int, cyc: int, cog: int) -> list[str]:
    problems = over_limit(f"{path} SLOC", lines, "src_sloc_per_file")
    problems += over_limit(f"{path} max cyclomatic", cyc, "cyclomatic_per_function")
    return problems + over_limit(f"{path} max cognitive", cog, "cognitive_per_function")


def ruff_violations(folders: list[Path]) -> list[str]:
    cmd = [sys.executable, "-m", "ruff", "check", "--isolated", "--ignore-noqa"]
    cmd += ["--select", RUFF_RULES, "--output-format", "json"]
    for setting in RUFF_LIMITS:
        cmd += ["--config", setting]
    result = subprocess.run(cmd + [str(f) for f in folders], capture_output=True, text=True)
    found = json.loads(result.stdout or "[]")
    return [f"{v['filename']}:{v['location']['row']} {v['code']} {v['message']}" for v in found]


def report(rows: list[tuple[Path, int, int, int]], src_total: int, test_total: int) -> None:
    print(f"{'file':48} {'SLOC':>5} {'max CC':>7} {'max cog':>8}")
    for path, lines, cyc, cog in rows:
        print(f"{str(path):48} {lines:5} {cyc:7} {cog:8}")
    print(f"src total SLOC: {src_total}/{LIMITS['src_sloc_total']}")
    print(f"tests total SLOC: {test_total}/{LIMITS['tests_sloc_total']}")


def check(src: Path, tests: Path) -> list[str]:
    rows = measure(src)
    src_total = sum(row[1] for row in rows)
    test_total = sum(sloc(path) for path in python_files(tests))
    report(rows, src_total, test_total)
    problems = [message for row in rows for message in file_problems(*row)]
    problems += over_limit("src total SLOC", src_total, "src_sloc_total")
    problems += over_limit("tests total SLOC", test_total, "tests_sloc_total")
    problems += [f"{nb}: notebooks are not allowed in src" for nb in src.rglob("*.ipynb")]
    return problems + ruff_violations([d for d in (src, tests) if d.exists()])


def main() -> int:
    given = sys.argv[1:3]
    folders = given + ["src", "tests"][len(given) :]
    problems = check(Path(folders[0]), Path(folders[1]))
    for line in problems:
        print("FAIL", line)
    print("BUDGET OK" if not problems else f"BUDGET FAILED: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
