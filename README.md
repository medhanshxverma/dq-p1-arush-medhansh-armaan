# Do Quantum @ UVA — Architecture Project 1

**Team:** Arush Kapoor, Medhansh Verma, Armaan Ahmed

## Project status
**Qiskit simulation completed on November 17, 2026.** The experiment was executed successfully on a Mac, generating 54 simulator records, a summary CSV, and plots. The measured simulation results are committed in the [`results/`](results/) folder. We report these as Qiskit Aer results, not measurements from a physical quantum computer.

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

Results will appear in `results/` or `results_quick/` as raw_results.csv, summary.csv, and PNG plots.

## Recorded simulation results (November 17, 2026)

The experiment ran successfully on a Mac with Qiskit Aer on November 17, 2026: **54 simulator records**, three trial seeds per setting, and **1,024 measurement shots per trial**. Data are in [raw results](results/raw_results.csv) and [summary](results/summary.csv).

At eight qubits and target gate density 1.0, the linear topology had **26.63%** average all-zero success, **49.33** inserted SWAPs, and compiled depth **69**. The fully connected topology had **75.55%** success, zero SWAPs, and depth **17**. At density zero, both topologies gave matching results.

At six qubits, a requested density of 0.5 becomes realized density 2/3 because the pair count is rounded.

The findings support the hypothesis **under this synthetic-noise simulation**. They do not establish the behavior of real processors. Further validation should test multiple routing algorithms, noise assumptions, and circuit families.

### Results graphs

The SVG charts below were recreated from the uploaded summary CSV and render directly on GitHub. Original Matplotlib PNGs are still in the team's local results folder.

| Qubits | Success | SWAPs | Compiled depth |
| --- | --- | --- | --- |
| 4 | [Graph](results/success_4q.svg) | [Graph](results/swaps_4q.svg) | [Graph](results/depth_4q.svg) |
| 6 | [Graph](results/success_6q.svg) | [Graph](results/swaps_6q.svg) | [Graph](results/depth_6q.svg) |
| 8 | [Graph](results/success_8q.svg) | [Graph](results/swaps_8q.svg) | [Graph](results/depth_8q.svg) |

## Status
- [x] Defined hypothesis and supporting literature
- [x] Created source code and dependency manifest
- [x] Run the Qiskit experiment on Mac; full results generated
- [x] Commit original CSV files and nine redrawn SVG charts

**Verification note:** The original Qiskit Aer run completed successfully and its recorded outputs are available above. These are results from a simulated noise model, not physical QPU measurements. The repository script was updated after the local run to align its output files and column names with the recorded data; independently rerunning that updated version is a useful reproducibility check.
