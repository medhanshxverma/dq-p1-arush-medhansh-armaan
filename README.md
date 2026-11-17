# Do Quantum @ UVA — Architecture Project 1

**Team:** Arush Kapoor, Medhansh Verma, Armaan Ahmed

## Question
Does higher two-qubit gate density reduce success probability more on a linearly connected quantum processor than on a fully connected processor?

## Hypothesis
Limited connectivity requires routing operations (often SWAP gates) to allow distant qubits to interact. We predict that as two-qubit gate density rises, line topology will require more routing and may have a larger reliability penalty. This is a hypothesis, not an established finding.

## Research background
- Pei Yuan and Shengyu Zhang, [Full Characterization of the Depth Overhead for Quantum Circuit Compilation with Arbitrary Qubit Connectivity Constraint](https://quantum-journal.org/papers/q-2025-05-28-1757/), *Quantum* (2025).
- Giacomo Nannicini et al., [Optimal Qubit Assignment and Routing via Integer Programming](https://doi.org/10.1145/3544563), *ACM Transactions on Quantum Computing* (2022).

These papers motivate the experiment but do not independently prove our hypothesis.

## Experiment
`experiment.py` generates random **mirrored** circuits: it applies a random circuit followed by its inverse, so the ideal noiseless outcome is all zeros. Each generated logical circuit is paired across two hardware coupling graphs:
- a linear nearest-neighbor chain;
- a fully connected graph.

Circuit sizes are 4, 6, and 8 qubits, using target CNOT densities 0, 0.5, and 1.0 across four forward logical layers. The density specifies the fraction of possible disjoint CNOT pairs per layer, rounded to an integer. Barriers and fixed transpiler settings are used to retain a meaningful routing comparison.

Using Qiskit, the script compiles each circuit with the same initial layout and simple routing strategy and records:
- inserted SWAPs;
- compiled depth;
- additional CNOT-equivalent gates (counting a SWAP as 3 CNOTs);
- all-zero success rate under a common **simulated**, uniform depolarizing noise model.

The noise model is idealized, not calibrated from IBM or another real QPU. This experiment does **not** measure CLOPS.

## Run on your Mac
Install Python 3.10 or newer, then open Terminal inside the cloned repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python experiment.py
```

For a quick run:

```bash
python experiment.py --qubits 4 6 --densities 0 0.5 1 --trials 1 --shots 256 --output-dir results_quick
```

Results will appear in `results/` or `results_quick/` as a CSV file and PNG plots of success rates, added SWAP gates, and compiled depth.

## Interpretation
**Predicted**: line topology needs more routing operations, with a potentially larger success penalty at high two-qubit density.

**To establish**: actually execute the script, inspect results from multiple seeds, then report measured *simulation* findings. Saturation and random circuit variability can make the success gap nonmonotonic.

## Status
- [x] Defined hypothesis and supporting literature
- [x] Created source code and dependency manifest
- [ ] Run Qiskit experiment and verify behavior on local computer
- [ ] Review actual results and commit CSV/plots

**No experimental results are claimed here.** The source has been written, but Qiskit was unavailable in the authoring runtime. The team should run and validate before using figures in a flash talk.
