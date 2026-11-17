"""Do Quantum @ UVA | Team 1 | Connectivity and gate-density simulation."""
import argparse
import csv
import random
import math
import statistics
from collections import defaultdict
from pathlib import Path

def build_circuit(n, density, layers, seed):
    from qiskit import QuantumCircuit
    rng = random.Random(seed)
    forward = QuantumCircuit(n)
    count = int(math.floor(density * (n // 2) + 0.5))
    for _ in range(layers):
        for q in range(n):
            getattr(forward, rng.choice(("h", "s", "x")))(q)
        order = list(range(n))
        rng.shuffle(order)
        for k in range(count):
            forward.cx(order[2*k], order[2*k+1])
        forward.barrier()
    qc = QuantumCircuit(n)
    qc.compose(forward, inplace=True)
    qc.barrier()
    qc.compose(forward.inverse(), inplace=True)
    qc.measure_all()
    return qc

def run(args):
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    model = NoiseModel()
    if args.p1:
        model.add_all_qubit_quantum_error(
            depolarizing_error(args.p1, 1), ["h", "s", "sdg", "x"])
    if args.p2:
        cx_err = depolarizing_error(args.p2, 2)
        model.add_all_qubit_quantum_error(cx_err, ["cx"])
        model.add_all_qubit_quantum_error(
            cx_err.compose(cx_err).compose(cx_err), ["swap"])
    simulator = AerSimulator(method="stabilizer", noise_model=model)
    rows = []
    for n in args.qubits:
        for density in args.densities:
            for trial in range(args.trials):
                seed = args.seed + 100000*n + round(density*100)*10000 + trial
                original = build_circuit(n, density, args.layers, seed)
                original_cx = original.count_ops().get("cx", 0)
                realized_density = original_cx / (2 * args.layers * (n // 2))
                for topology in ("line", "all_to_all"):
                    coupling = (CouplingMap.from_line(n, bidirectional=True)
                                if topology == "line" else CouplingMap.from_full(n))
                    circuit = transpile(
                        original, coupling_map=coupling,
                        basis_gates=["h", "s", "sdg", "x", "cx", "swap"],
                        layout_method="trivial", routing_method="basic",
                        optimization_level=0, seed_transpiler=seed)
                    ops = circuit.count_ops()
                    swaps = ops.get("swap", 0)
                    cx = ops.get("cx", 0)
                    count = simulator.run(
                        circuit, shots=args.shots,
                        seed_simulator=seed).result().get_counts().get("0"*n, 0)
                    row = dict(
                        qubits=n, target_density=density, realized_density=realized_density,
                        layers_forward=args.layers, trial=trial,
                        topology=topology, logical_cx=original_cx,
                        compiled_cx=cx, swap_count=swaps, effective_cx=cx+3*swaps,
                        added_cx_equivalents=cx+3*swaps-original_cx,
                        compiled_depth=circuit.depth(), shots=args.shots,
                        zero_counts=count, success_probability=count/args.shots)
                    rows.append(row)
                    print(row)
    return rows

def export(rows, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with (directory/"raw_results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary=[]
    for n in sorted(set(r["qubits"] for r in rows)):
        for density in sorted(set(r["target_density"] for r in rows)):
            for topology in ("all_to_all", "line"):
                group=[r for r in rows if r["qubits"]==n and r["target_density"]==density and r["topology"]==topology]
                def avg(k):
                    return statistics.mean(r[k] for r in group)
                summary.append(dict(qubits=n, target_density=density, topology=topology, trials=len(group),
                    mean_realized_density=avg("realized_density"),mean_swaps=avg("swap_count"),
                    mean_compiled_depth=avg("compiled_depth"),mean_added_cx_equivalents=avg("added_cx_equivalents"),
                    mean_success_probability=avg("success_probability")))
    with (directory/"summary.csv").open("w", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    for n in sorted(set(r["qubits"] for r in summary)):
        subset=[r for r in summary if r["qubits"]==n]
        for metric, key, ylabel in (
            ("success","mean_success_probability","P(all-zero outcome)"),
            ("swaps","mean_swaps","Mean added SWAP gates"),
            ("depth","mean_compiled_depth","Mean transpiled circuit depth")):
            fig, ax=plt.subplots(figsize=(6.4,4.2))
            for topology in ("line","all_to_all"):
                points=sorted((r for r in subset if r["topology"]==topology),
                             key=lambda r:r["target_density"])
                ax.plot([r["target_density"] for r in points],
                        [r[key] for r in points],marker="o",label=topology.replace("_","-"))
            ax.set_title(f"{n} qubits: {ylabel}")
            ax.set_xlabel("Target two-qubit gate density")
            ax.set_ylabel(ylabel)
            if metric=="success":
                ax.set_ylim(0,1.03)
            ax.legend()
            ax.grid(alpha=.25)
            fig.tight_layout()
            fig.savefig(directory/f"{metric}_{n}q.png",dpi=160)
            plt.close(fig)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--qubits", type=int, nargs="+", default=[4,6,8])
    p.add_argument("--densities", type=float, nargs="+", default=[0,.5,1])
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--shots", type=int, default=1024)
    p.add_argument("--p1", type=float, default=.001)
    p.add_argument("--p2", type=float, default=.01)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--output-dir", type=Path, default=Path("results"))
    a = p.parse_args()
    if any(n < 2 or n % 2 for n in a.qubits):
        p.error("qubit counts must be even integers >= 2")
    if any(not 0 <= d <= 1 for d in a.densities):
        p.error("densities must be between 0 and 1")
    if min(a.layers, a.trials, a.shots) < 1:
        p.error("layers, trials, shots must be positive")
    if not (0 <= a.p1 <= 1 and 0 <= a.p2 <= 1):
        p.error("noise probabilities must be in [0,1]")
    try:
        export(run(a), a.output_dir)
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Missing dependency {exc.name}; install requirements.txt") from exc
    print(f"Saved {len(rows)} simulator trials and summary/plots in {a.output_dir}/")
    print("These are synthetic-noise simulations, not real-QPU measurements.")

if __name__ == "__main__":
    main()
