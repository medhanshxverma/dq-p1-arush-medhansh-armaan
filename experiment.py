"""Do Quantum @ UVA | Team 1 | Connectivity and gate-density simulation."""
import argparse
import csv
import random
from pathlib import Path

def build_circuit(n, density, layers, seed):
    from qiskit import QuantumCircuit
    rng = random.Random(seed)
    forward = QuantumCircuit(n)
    count = round(density * (n // 2))
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
                seed = args.seed + 100000*n + round(density*100)*1000 + trial
                original = build_circuit(n, density, args.layers, seed)
                original_cx = original.count_ops().get("cx", 0)
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
                        qubits=n, target_density=density, trial=trial,
                        topology=topology, logical_cx=original_cx,
                        cx_count=cx, swap_count=swaps,
                        added_cx_equivalents=cx+3*swaps-original_cx,
                        compiled_depth=circuit.depth(), shots=args.shots,
                        success_probability=count/args.shots)
                    rows.append(row)
                    print(row)
    return rows

def export(rows, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/"results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for n in sorted(set(r["qubits"] for r in rows)):
        subset = [r for r in rows if r["qubits"] == n]
        for metric in ("success_probability", "swap_count", "compiled_depth"):
            fig, ax = plt.subplots(figsize=(6,4))
            for layout in ("line", "all_to_all"):
                points = []
                for d in sorted(set(r["target_density"] for r in subset)):
                    values = [r[metric] for r in subset
                              if r["target_density"] == d and r["topology"] == layout]
                    points.append((d, sum(values)/len(values)))
                ax.plot([p[0] for p in points],
                        [p[1] for p in points], marker="o", label=layout)
            ax.set_xlabel("Target two-qubit density")
            ax.set_ylabel(metric)
            ax.set_title(f"{n} qubits — {metric}")
            ax.legend()
            fig.tight_layout()
            fig.savefig(directory/f"{metric}_{n}q.png", dpi=160)
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
    print("These are simulation results, not real-QPU measurements.")

if __name__ == "__main__":
    main()
