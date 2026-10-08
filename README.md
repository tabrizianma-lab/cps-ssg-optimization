# Stackelberg Security Game for Cyber-Physical Systems (SSG-CPS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Repository](https://img.shields.io/badge/GitHub-cps--ssg--optimization-blue?logo=github)](https://github.com/tabrizianma-lab/cps-ssg-optimization)

This repository provides the open-access replication package, benchmark dataset, numerical validation outputs, and exact HiGHS Mixed-Integer Linear Programming (MILP) solver code for the manuscript:

> **"Optimal Defense Resource Allocation in Cyber-Physical Systems: A Bilevel Stackelberg Security Game with Strong-Duality Reformulation"**  
> *Target Journal: International Journal of Information Security (IJIS)*

---

## 1. Research Overview

Protecting interconnected Cyber-Physical Systems (CPS) subject to strict defensive budgets demands mathematically rigorous control allocation. We formulate this challenge as a bilevel Stackelberg Security Game (SSG):
- **Leader (Defender):** Selects an optimal discrete portfolio of NIST SP 800-53 security controls to minimize residual physical damage under budget constraints.
- **Follower (Attacker):** Solves an interdiction problem to maximize physical damage by allocating penetration effort across critical process subsystems after observing defense hardening.

By establishing strong duality for the continuous follower interdiction problem, we linearize the complementary slackness conditions using Fortuny-Amat & McCarl big-$M$ parameters. This transforms the bilevel program into an exact, single-level Mixed-Integer Linear Program (MILP), solved to global optimality via `scipy.optimize.milp` backed by the open-source HiGHS solver engine.

---

## 2. File Manifest

All operational, data, and visual artifacts are maintained in the root directory for direct execution:

| File Name | Format | Role & Description |
| :--- | :---: | :--- |
| `run_experiments.py` | Python Script | Primary end-to-end execution script. Solves the exact strong-duality MILP, computes Greedy, CVSS-Ranked, and Uniform baselines, performs Big-$M$ sensitivity analysis, and generates high-resolution figures. |
| `cps_stc4.xlsx` | Excel Dataset | Case study dataset based on the Tennessee Eastman Process (TEP). Contains parameters for 10 physical assets (A01–A10), 35 NIST SP 800-53 candidate controls, baseline risk metrics ($R_0$), implementation costs, and attacker effort coefficients. |
| `ssg_computational_results.xlsx` | Excel Results | Comprehensive numerical output workbook containing four sheets: `Pareto_and_Benchmarks`, `Bilevel_Heatmap`, `Big_M_Sensitivity`, and `Target_Shifting`. |
| `Figure_1_Pareto_Front.png` | Image (600 DPI) | Risk mitigation Pareto frontier comparing the proposed exact MILP against Greedy, CVSS-Ranked, and Uniform baseline strategies across budget range $B \in [0, 240]$. |
| `Figure_2_Budget_Heatmap.png` | Image (600 DPI) | Interaction matrix heatmap illustrating residual system damage across defender budgets ($B \in [30, 240]$) and attacker capabilities ($b \in [10, 100]$). |
| `Figure_3_BigM_Analysis.png` | Image (600 DPI) | Raster plot demonstrating computational tractability, solve times, and objective value invariance across penalty parameters $M \in [1.5, 1000]$. |
| `Figure_3_BigM_Analysis.pdf` | Vector Graphic | High-resolution vector version of Figure 3 for publication-quality rendering. |
| `Figure_4_Target_Shifting.png` | Image (600 DPI) | Asset infiltration dynamics demonstrating attacker target shifting across assets A01–A10 as defense budget increases. |
| `requirements.txt` | Text File | Complete environment dependencies required for replication. |
| `LICENSE` | Text File | MIT Open-Source License terms. |

---

## 3. Mathematical & Algorithmic Specifications

- **Mathematical Reformulation:** Single-level Strong-Duality MILP via Fortuny-Amat & McCarl linearization.
- **Optimization Engine:** `scipy.optimize.milp` utilizing the HiGHS branch-and-cut / simplex solver.
- **Convergence Tolerance:** Relative MIP optimality gap $\le 10^{-4}$.
- **Baseline Models Evaluated:**
  1. *Greedy Benefit-Cost Ratio Heuristic:* Selects controls prioritizing maximum risk reduction per unit cost ($\Delta_{ik} / c_{ik}$).
  2. *CVSS-Ranked Defense:* Allocates defensive budget sequentially to assets with highest baseline vulnerability severity scores.
  3. *Uniform Defense Baseline:* Distributes defensive expenditure uniformly across all available control options.

---

## 4. Replication Protocol

### Step 1: Environment Setup
Ensure Python 3.9 or higher is installed, then install all required packages:
```bash
pip install -r requirements.txt
```

### Step 2: Run Experiments
Execute the primary script directly from the root directory:
```bash
python run_experiments.py
```

### Output Verification
Execution completes in approximately 2 to 10 seconds depending on system hardware. The script regenerates all four figures (600 DPI) and updates `ssg_computational_results.xlsx`.

---

## 5. Authors & Institutional Affiliation

- **Mohammad Amin Tabrizian Sichani** ([ma.tabrizian@ut.ac.ir](mailto:ma.tabrizian@ut.ac.ir))  
  *School of Industrial Engineering, College of Engineering, University of Tehran, Tehran, Iran*

- **Mahya Omidifar** ([mahya.omidi.far@ut.ac.ir](mailto:mahya.omidi.far@ut.ac.ir))  
  *School of Industrial Engineering, College of Engineering, University of Tehran, Tehran, Iran*

- **Dr. Jalal Delaram** ([delaram@ut.ac.ir](mailto:delaram@ut.ac.ir))  
  *School of Industrial Engineering, College of Engineering, University of Tehran, Tehran, Iran*

---

## 6. Citation

If you use this codebase, methodology, or dataset in academic research, please cite:

```bibtex
@article{tabrizian2026ssgcps,
  author  = {Tabrizian Sichani, Mohammad Amin and Omidifar, Mahya and Delaram, Jalal},
  title   = {Optimal Defense Resource Allocation in Cyber-Physical Systems: A Bilevel Stackelberg Security Game with Strong-Duality Reformulation},
  journal = {International Journal of Information Security},
  year    = {2026},
  url     = {https://github.com/tabrizianma-lab/cps-ssg-optimization}
}
```

---

## 7. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
