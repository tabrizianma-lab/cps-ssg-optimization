# Optimal Resource Allocation in Cyber-Physical Systems via Strong-Duality Bilevel Stackelberg Security Games

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Optimization: HiGHS](https://img.shields.io/badge/Solver-HiGHS%20%28SciPy%2Fhighspy%29-green.svg)](https://highs.dev/)
[![DOI: Zenodo](https://img.shields.io/badge/DOI-Zenodo%20Archive-blue)](https://doi.org/)
[![Journal: IJIS](https://img.shields.io/badge/Submitted%20to-Int.%20J.%20Inf.%20Secur.%20%28IJIS%29-red)](https://www.springer.com/journal/10207)

This repository contains the complete computational reproduction suite and empirical dataset for the paper:

> **"Optimal Resource Allocation in Cyber-Physical Systems via Strong-Duality Bilevel Stackelberg Security Games"**  
> *Mohammad Amin Tabrizian, Mahya Omidifar, and Jalal Delaram*  
> Submitted to the *International Journal of Information Security* (IJIS), Springer.

---

## 1. Overview and Theoretical Framework

Cyber-Physical Systems (CPS) and Industrial Control Systems (ICS) face increasingly sophisticated, coordinated cyber-physical threats. Defending such networks requires allocating constrained defensive budgets across combinatorial security control candidates under strategic, adversarial behavior.

```
                      +---------------------------------------+
                      |       LEADER (System Defender)        |
                      |   Minimizes Defender Loss / Regret   |
                      |    Subject to: Budget Constraint B    |
                      |       Decisions: x_j in {0, 1}        |
                      +-------------------+-------------------+
                                          |
                      Defensive Strategy  |  Observed by
                      Investment Profile  |  Attacker
                                          v
                      +-------------------+-------------------+
                      |      FOLLOWER (Strategic Attacker)    |
                      |     Maximizes Attack Utility U_A      |
                      |    Decisions: continuous w_i >= 0     |
                      +-------------------+-------------------+
```

### Core Mathematical Methodology
1. **Bilevel Stackelberg Security Game (SSG):** Modeled as a leader-follower non-cooperative game where the defender selects binary security investments $x_j \in \{0, 1\}$ from NIST SP 800-53 controls, and the attacker chooses continuous resource/target allocations $w_i \ge 0$.
2. **Strong Duality Reformulation:** The lower-level continuous follower problem is strictly linear and bounded, allowing exact transformation into the upper-level program via its dual formulation and Strong Duality theorem.
3. **Big-$M$ Linearization:** Non-linear complementary slackness conditions are linearized via exact disjunctive Big-$M$ constraints, converting the bilevel model into a single-level Mixed-Integer Linear Program (MILP).
4. **Deterministic Convergence:** Solved to global optimality with an explicit relative MIP gap tolerance $\le 10^{-4}$ using the state-of-the-art open-source HiGHS interior-point/simplex branch-and-cut solver.

---

## 2. Repository Structure (Flat Single-Root Directory)

All replication scripts, empirical datasets, and analytical outputs are maintained in a clean, unified root structure:

```
cps-ssg-optimization/
├── README.md                       # Complete documentation and reproduction guide
├── LICENSE                         # MIT License
├── run_experiments_v40.py          # Complete optimization engine & experiment driver
├── cps_stc4.xlsx                   # Empirical dataset: 10 physical assets, 35 NIST controls
├── ssg_computational_results.xlsx  # Raw numerical results (Pareto, Big-M, benchmarks)
├── Figure_1_Pareto_Front.png       # Publication Figure 1: SSG vs. CVSS vs. Greedy Pareto frontier
├── Figure_2_Budget_Heatmap.png      # Publication Figure 2: Control allocation heatmap across budgets
├── Figure_3_BigM_Analysis.png      # Publication Figure 3: Big-M sensitivity and tightness analysis
└── Figure_4_Target_Shifting.png    # Publication Figure 4: Attacker target shift under defense
```

### File Inventory Details
* **`run_experiments_v40.py`**: Standalone, deterministic Python script executing the full experimental pipeline (Data validation $\to$ MILP construction $\to$ HiGHS solution $\to$ Excel/Figure exports).
* **`cps_stc4.xlsx`**: Parameterized empirical dataset based on the Tennessee Eastman Process (TEP) benchmark comprising 10 critical assets (reactors, separators, strippers, compressors, pumps), 35 NIST SP 800-53 Rev. 5 security controls, CVSS v3.1 base metrics, deployment costs, and asset impact weights.
* **`ssg_computational_results.xlsx`**: Four structured sheets containing all numerical records:
  * `Pareto_and_Benchmarks`: Budgets $B \in [100, 1200]$, objective values, runtimes, and baseline comparisons.
  * `Bilevel_Heatmap`: Control selection frequencies across budget tiers.
  * `Big_M_Sensitivity`: Solver stability across penalty values $M \in [10^1, 10^7]$.
  * `Target_Shifting`: Attacker resource reallocation dynamics across assets.
* **`Figure_1` to `Figure_4`**: Vector-quality 300 DPI publication figures corresponding directly to the manuscript.

---

## 3. System Requirements & Installation

The optimization suite is lightweight and requires **Python 3.9+** (fully verified up to Python 3.12/3.14).

### Dependencies
* `numpy` (>= 1.22)
* `pandas` (>= 1.4)
* `openpyxl` (>= 3.0)
* `scipy` (>= 1.9, provides native `scipy.optimize.milp` with HiGHS backend)
* `matplotlib` (>= 3.5)
* `highspy` (optional, for standalone HiGHS direct C++ bindings)

### Installation Command
Install all required dependencies with a single command:

```bash
pip install numpy pandas openpyxl scipy matplotlib highspy
```

---

## 4. Execution and Replication

To execute all experiments, reproduce the exact numerical tables, and generate the publication-ready figures, run:

```bash
python run_experiments_v40.py
```

### Execution Details:
* Execution time: typically under 5 seconds total runtime for the complete experiment suite on standard commodity hardware.
* Outputs generated/verified automatically in the current directory:
  * `ssg_computational_results.xlsx` (updated raw tables)
  * `Figure_1_Pareto_Front.png`
  * `Figure_2_Budget_Heatmap.png`
  * `Figure_3_BigM_Analysis.png`
  * `Figure_4_Target_Shifting.png`

---

## 5. Core Empirical Verification Points

The artifact guarantees deterministic reproduction of the findings reported in the article:

| Metric / Dimension | Reported Result | Empirical Verification Point | Status |
| :--- | :--- | :--- | :--- |
| **Pareto Frontier Range** | Defender Loss $\in [2.109210, 3.038567]$ | Evaluated across budgets $B = 100$ to $1200$ | **Verified Exact** |
| **CVSS Benchmark Advantage** | **+24.35%** Improvement | SSG formulation vs. CVSS-severity heuristic | **Verified Exact** |
| **Greedy Heuristic Advantage**| **+19.50%** Improvement | SSG formulation vs. Knapsack/Greedy allocation | **Verified Exact** |
| **Computational Solve Time** | **$\le 1.731\text{ s}$** (Max at $B=600$) | Median solve time: $\sim 0.005\text{ s}$; worst-case: $1.731\text{ s}$ | **Verified Exact** |
| **MIP Optimality Gap** | **$\le 10^{-4}$ ($0.01\%$)** | HiGHS relative convergence tolerance reached | **Verified Exact** |
| **Big-$M$ Invariance** | Stable for $M \in [10^2, 10^5]$ | Objective value strictly invariant; dual tightness confirmed | **Verified Exact** |

---

## 6. BibTeX Citation

If you use this codebase, model formulation, or dataset in your research, please cite:

```bibtex
@article{tabrizian2026optimal,
  title     = {Optimal Resource Allocation in Cyber-Physical Systems via Strong-Duality Bilevel Stackelberg Security Games},
  author    = {Tabrizian, Mohammad Amin and Omidifar, Mahya and Delaram, Jalal},
  journal   = {International Journal of Information Security},
  year      = {2026},
  publisher = {Springer},
  note      = {Submitted / Under Review}
}
```

---

## 7. Contact & Authorship

* **Mohammad Amin Tabrizian**  
  School of Industrial Engineering, College of Engineering, University of Tehran, Tehran, Iran  
  Email: `m.a.tabrizian@ut.ac.ir`

* **Mahya Omidifar**  
  Department of Industrial Engineering, Sharif University of Technology, Tehran, Iran  

* **Dr. Jalal Delaram** *(Corresponding Author)*  
  Assistant Professor, School of Industrial Engineering, College of Engineering, University of Tehran, Tehran, Iran  
  Email: `delaram@ut.ac.ir`

---

## 8. License

This project is licensed under the terms of the **MIT License**. See the [LICENSE](LICENSE) file for details.
