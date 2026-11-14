"""Reproduce local durable two-agent test logs and synthetic restart controls."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT/"research/runs/2026-11-14/durable-two-agents")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    checks = []

    def run(command, log, *, normalize=None):
        started = time.perf_counter()
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=600,
                                env=os.environ | {"PYTHONIOENCODING": "utf-8"})
        output = result.stdout + result.stderr
        if normalize:
            output = output.replace(str(normalize), "TEMPORARY_SYNTHETIC_EVIDENCE")
            output = output.replace(json.dumps(str(normalize))[1:-1], "TEMPORARY_SYNTHETIC_EVIDENCE")
        (args.out/log).write_text(output, encoding="utf-8")
        checks.append({"command": ["python" if i == 0 and value == sys.executable else
                        str(value).replace(str(normalize), "TEMPORARY_SYNTHETIC_EVIDENCE") if normalize else value
                        for i, value in enumerate(command)],
                       "exit_code": result.returncode, "seconds": round(time.perf_counter()-started, 3), "log": log})
        if result.returncode:
            raise RuntimeError(f"check failed; inspect {args.out/log}")
        return json.loads(result.stdout) if log.endswith(".json") else output

    source_files = ["examples/durable_two_agents.py", "examples/persistent_agents.py", "examples/two_agents.py",
                    "tests/test_durable_two_agents.py", "scripts/validate_durable_two_agents.py",
                    "docs/experiments/DURABLE-TWO-AGENT-RECEIPTS.md", "README.md",
                    "docs/project/EXECUTION-HANDOFF.md", "docs/ROADMAP.md"]
    source_files += [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT/"src").rglob("*.py"))]
    commit = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    report = {"status": "failed", "source_commit": commit,
              "environment": {"python": sys.version, "sqlite": sqlite3.sqlite_version,
                              "platform": platform.platform(), "machine": platform.machine(),
                              "processor": platform.processor(), "cpu_count": os.cpu_count()},
              "source_sha256": {name: sha256((ROOT/name).read_bytes()).hexdigest() for name in source_files},
              "checks": checks,
              "initial_test_finding": "Initial authored 13-test run had one history-comparison failure: live tuples versus CLI JSON lists. Round records now normalize to JSON types; no persistent world or memory mismatch was found.",
              "harness_portability_fix": "The first full validation passed every check, then failed printing the accented repository path on a cp1252 console. The completion message now uses ASCII; this report is from the subsequent complete validation invocation.",
              "limits": ["Synthetic, same-owner, bounded 20-round lab; no LLM, user data or outside effects.",
                         "Journal and memory commit separately; process-exit tests are not physical power-loss certification.",
                         "No policy-superiority, storage-performance, shared-contract or production acceptance claim."]}
    try:
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_durable_two_agents.py", "-v"], "targeted-tests.log")
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], "full-tests.log")
        run([sys.executable, "scripts/check_repository.py"], "repository-check.log")
        run([sys.executable, "-m", "py_compile", "examples/durable_two_agents.py",
             "tests/test_durable_two_agents.py", "scripts/validate_durable_two_agents.py"], "syntax-check.log")
        run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "diff", "--check"], "diff-check.log")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"pair.sqlite3"
            base = [sys.executable, "examples/durable_two_agents.py", "--db", str(path)]
            first = run(base+["--rounds", "3"], "restart-1.json", normalize=path)
            second = run(base+["--rounds", "3"], "restart-2.json", normalize=path)
            status = run(base+["--status", "--history"], "restart-status.json", normalize=path)
            assert (first["round"], second["resumed_from_round"], second["round"], status["round"]) == (3, 3, 6, 6)
            assert second["memory"] == status["memory"] and second["budget"] == status["budget"]
            results = {}
            for name, extra in (("hostile-memory", ["--scenario", "hostile"]),
                                ("hostile-control", ["--scenario", "hostile", "--policy", "always_offer"]),
                                ("cooperative-notifications", ["--mode", "notifications"]),
                                ("cooperative-reconcile", ["--mode", "reconcile"])):
                control = Path(directory)/(name+".sqlite3")
                command = [sys.executable, "examples/durable_two_agents.py", "--db", str(control), "--rounds", "20"]
                if name.startswith("hostile"):
                    command += ["--delay", "0", "--drop-every", "0"]
                result = run(command+extra, name+".json", normalize=control)
                results[name] = {key: result[key] for key in ("sent", "returned", "actual_loss", "peak_actual_exposure", "exact_events")}
            assert results["hostile-memory"]["actual_loss"] == 2
            assert results["hostile-control"]["actual_loss"] == 4
            assert results["cooperative-notifications"]["sent"] == 8
            assert results["cooperative-reconcile"]["sent"] == 20
            report["synthetic_controls"] = results
            report["restart_rounds"] = [first["round"], second["round"], status["round"]]
            report["status"] = "passed"
    finally:
        report["artifact_sha256"] = {check["log"]: sha256((args.out/check["log"]).read_bytes()).hexdigest() for check in checks}
        (args.out/"validation.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("PASS: local validation completed; see validation.json in the output directory")


if __name__ == "__main__":
    main()
