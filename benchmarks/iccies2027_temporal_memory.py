"""Research-only, synthetic full-feedback temporal memory benchmark (ICCIES 2027).

This does not read protected events, implement agents, or measure deployment.
Predictions are always made before observing the corresponding label.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import statistics
import sys
import time
from pathlib import Path

SCENARIOS = ("iid_half", "iid_high", "persist", "alternate", "switch")
MODELS = ("marginal", "conditional", "cost_gate")
SCHEMA = "openworld.iccies2027.temporal-memory.v0"


def tape(scenario: str, seed: int, steps: int) -> tuple[int, ...]:
    if scenario not in SCENARIOS or type(seed) is not int or seed < 0 or type(steps) is not int or not 40 <= steps <= 10000:
        raise ValueError("invalid scenario, seed or steps")
    rng = random.Random(seed)
    ys = [rng.randrange(2)]
    for t in range(1, steps):
        if scenario in ("persist", "alternate", "switch"):
            q = 0.9 if scenario == "persist" or scenario == "switch" and t < steps // 2 else 0.1
            ys.append(ys[-1] if rng.random() < q else 1 - ys[-1])
        else:
            p = 0.5 if scenario == "iid_half" else 0.75
            ys.append(int(rng.random() < p))
    return tuple(ys)


class Marginal:
    def __init__(self):
        self.n = 0
        self.k = 0

    def predict(self) -> float:
        return (self.k + 1) / (self.n + 2)

    def observe(self, y: int):
        if type(y) is not int or y not in (0, 1):
            raise ValueError("binary label required")
        self.n += 1
        self.k += y

    def state(self):
        return {"n": self.n, "k": self.k}


class Conditional(Marginal):
    def __init__(self):
        super().__init__()
        self.last = None
        self.count = [[0, 0], [0, 0]]

    def predict(self) -> float:
        if self.last is None:
            return super().predict()
        row = self.count[self.last]
        return (row[1] + 1) / (sum(row) + 2) if sum(row) >= 2 else super().predict()

    def observe(self, y: int):
        if type(y) is not int or y not in (0, 1):
            raise ValueError("binary label required")
        if self.last is not None:
            self.count[self.last][y] += 1
        super().observe(y)
        self.last = y

    def state(self):
        return {**super().state(), "last": self.last, "counts": self.count}


class CostGate:
    """Opt-in heuristic: discounted prequential Brier gain selects conditional.

    Gate is assessed as a third, competing expert. Both constituent predictors
    receive the same label in this *fully observed* synthetic experiment.
    The gate is not a general online regret theorem or latency guarantee.
    """
    def __init__(self, decay: float = 0.96, penalty: float = 0.005):
        if not (0 < decay < 1) or penalty < 0 or not math.isfinite(penalty):
            raise ValueError("invalid gate hyperparameters")
        self.marginal, self.conditional = Marginal(), Conditional()
        self.decay, self.penalty = decay, penalty
        self.loss_m = self.loss_c = 0.25
        self.conditional_selections = 0

    def predict(self) -> float:
        use_conditional = (self.marginal.n >= 12 and self.loss_m - self.loss_c > self.penalty)
        self.conditional_selections += int(use_conditional)
        return self.conditional.predict() if use_conditional else self.marginal.predict()

    def observe(self, y: int):
        if type(y) is not int or y not in (0, 1):
            raise ValueError("binary label required")
        p_m = self.marginal.predict()
        p_c = self.conditional.predict()
        self.loss_m = self.decay * self.loss_m + (1 - self.decay) * (p_m - y) ** 2
        self.loss_c = self.decay * self.loss_c + (1 - self.decay) * (p_c - y) ** 2
        self.marginal.observe(y)
        self.conditional.observe(y)

    def state(self):
        return {"marginal": self.marginal.state(), "conditional": self.conditional.state(),
                "loss_m": self.loss_m, "loss_c": self.loss_c,
                "conditional_selections": self.conditional_selections}


def evaluate(labels: tuple[int, ...], warmup: int) -> dict:
    if type(warmup) is not int or warmup < 1 or warmup >= len(labels):
        raise ValueError("invalid warmup")
    estimators = {"marginal": Marginal(), "conditional": Conditional(), "cost_gate": CostGate()}
    losses = {k: [] for k in MODELS}
    cpu = {k: 0 for k in MODELS}
    for t, y in enumerate(labels):
        predictions = {}
        for name, estimator in estimators.items():
            start = time.process_time_ns()
            predictions[name] = estimator.predict()
            cpu[name] += time.process_time_ns() - start
        for name, estimator in estimators.items():
            if t >= warmup:
                losses[name].append((predictions[name] - y) ** 2)
            start = time.process_time_ns()
            estimator.observe(y)
            cpu[name] += time.process_time_ns() - start
    return {name: {
        "holdout_prequential_brier": statistics.mean(losses[name]),
        "serialized_predictor_bytes": len(json.dumps(estimators[name].state(), sort_keys=True, separators=(",", ":")).encode()),
        "instrumented_process_cpu_ns": cpu[name],
        **({"conditional_selections_all_ticks": estimators[name].conditional_selections} if name == "cost_gate" else {}),
    } for name in MODELS}


def run(seeds: tuple[int, ...], steps: int = 300, warmup: int = 60, scenarios: tuple[str, ...] = SCENARIOS) -> dict:
    if not seeds or len(set(seeds)) != len(seeds) or any(type(x) is not int or x < 0 for x in seeds):
        raise ValueError("unique nonnegative integer seeds required")
    if type(steps) is not int or not 40 <= steps <= 10000 or type(warmup) is not int or warmup < 1 or warmup >= steps:
        raise ValueError("invalid step or warmup count")
    if not scenarios or len(set(scenarios)) != len(scenarios) or any(s not in SCENARIOS for s in scenarios):
        raise ValueError("invalid scenarios")
    cases = []
    for scenario in scenarios:
        for seed in seeds:
            ys = tape(scenario, seed, steps)
            cases.append({"scenario": scenario, "seed": seed, "tape_sha256": hashlib.sha256(bytes(ys)).hexdigest(),
                          "metrics": evaluate(ys, warmup)})
    return {
        "schema": SCHEMA, "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
        "config": {"seeds": list(seeds), "steps": steps, "warmup": warmup, "scenarios": list(scenarios),
                   "gate_decay": 0.96, "gate_penalty": 0.005},
        "summary": {s: {m: {"mean_brier": statistics.mean(c["metrics"][m]["holdout_prequential_brier"]
                                                           for c in cases if c["scenario"] == s)} for m in MODELS} for s in scenarios},
        "cases": cases,
        "limitations": ["Synthetic binary full-feedback forecasts, not multi-agent reinforcement learning",
                        "The online holdout continues learning after warmup; labels are used only after each forecast",
                        "The full-history exact-evidence ledger is not evaluated or replaced",
                        "The gate is a heuristic, with no universal superiority or regret bound",
                        "CPU and serialized-predictor bytes do not represent full deployment cost",
                        "No hyperparameter tuning on holdout seeds; negative results are required"],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed-start", type=int, default=83001)
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--warmup", type=int, default=60)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    if not 1 <= a.seeds <= 100:
        p.error("seeds must be in [1,100]")
    result = run(tuple(range(a.seed_start, a.seed_start + a.seeds)), a.steps, a.warmup)
    out = json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    if a.out:
        with a.out.open("x", encoding="utf-8") as f:
            f.write(out)
    print(out, end="")


if __name__ == "__main__":
    main()
