"""
Optimal Defensive Resource Allocation in Cyber-Physical Systems via Stackelberg Security Games
Engine: Native SciPy MILP (HiGHS Backend) - High Performance & Python 3.14 Compatible
Target Journal: International Journal of Information Security (IJIS)
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import milp, LinearConstraint, Bounds

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

# ==============================================================================
# 1. DATA INGESTION
# ==============================================================================
def load_and_validate_dataset(filepath='cps_stc4.xlsx'):
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    full_path = os.path.join(script_dir, filepath)
    if not os.path.exists(full_path):
        full_path = filepath
        
    xls = pd.ExcelFile(full_path)
    assets_df = pd.read_excel(xls, sheet_name='Assets').copy()
    controls_df = pd.read_excel(xls, sheet_name='NIST_Controls').copy()
    params_df = pd.read_excel(xls, sheet_name='Game_Parameters').copy()
    
    controls_df = controls_df.loc[controls_df['Control_Row_ID'].notna()].copy()
    controls_df.loc[:, 'Control_ID'] = controls_df['Control_ID'].astype(str).str.strip()
    controls_df.loc[:, 'Asset_ID'] = controls_df['Asset_ID'].astype(str).str.strip()
    assets_df.loc[:, 'Asset_ID'] = assets_df['Asset_ID'].astype(str).str.strip()
    controls_df.reset_index(drop=True, inplace=True)
    
    return assets_df, controls_df, params_df

# ==============================================================================
# 2. STRONG-DUALITY MILP FORMULATION (HiGHS ENGINE)
# ==============================================================================
def solve_ssg_milp(assets_df, controls_df, B_def, b_att, Big_M=2.0):
    I_list = assets_df['Asset_ID'].tolist()
    K_list = controls_df.index.tolist()
    
    n_I = len(I_list)
    n_K = len(K_list)
    
    R0 = assets_df['R0'].values
    c_att = assets_df['Attacker_Cost_c_att'].values
    c_def = controls_df['Cost_c_ik'].values
    delta = controls_df['Delta_ik'].values
    
    asset_to_ctrl_indices = {i: controls_df[controls_df['Asset_ID'] == asset_id].index.tolist() 
                             for i, asset_id in enumerate(I_list)}

    # Variables ordering:
    # x: [0 : n_K] (binary)
    # lmbda: [n_K] (continuous >= 0)
    # mu: [n_K + 1 : n_K + 1 + n_I] (continuous >= 0)
    # y: [n_K + 1 + n_I : n_K + 1 + 2*n_I] (continuous in [0, 1])
    # z_mu: [n_K + 1 + 2*n_I : n_K + 1 + 3*n_I] (binary)
    # z_dual: [n_K + 1 + 3*n_I : n_K + 1 + 4*n_I] (binary)
    # z_lmbda: [n_K + 1 + 4*n_I] (binary)
    
    idx_x = 0
    idx_lmbda = n_K
    idx_mu = n_K + 1
    idx_y = idx_mu + n_I
    idx_z_mu = idx_y + n_I
    idx_z_dual = idx_z_mu + n_I
    idx_z_lmbda = idx_z_dual + n_I
    n_vars = idx_z_lmbda + 1
    
    # Objective: Minimize b_att * lmbda + sum(mu_i)
    c = np.zeros(n_vars)
    c[idx_lmbda] = b_att
    c[idx_mu:idx_mu + n_I] = 1.0
    
    # Integrality constraints (1 = integer/binary, 0 = continuous)
    integrality = np.zeros(n_vars)
    integrality[idx_x:idx_x + n_K] = 1
    integrality[idx_z_mu:idx_z_mu + n_I] = 1
    integrality[idx_z_dual:idx_z_dual + n_I] = 1
    integrality[idx_z_lmbda] = 1
    
    # Variable bounds
    lb = np.zeros(n_vars)
    ub = np.full(n_vars, np.inf)
    ub[idx_x:idx_x + n_K] = 1.0
    ub[idx_y:idx_y + n_I] = 1.0
    ub[idx_z_mu:idx_z_mu + n_I] = 1.0
    ub[idx_z_dual:idx_z_dual + n_I] = 1.0
    ub[idx_z_lmbda] = 1.0
    bounds = Bounds(lb, ub)
    
    # Constraints list
    A_rows = []
    lhs = []
    rhs = []
    
    # 1. Defender Budget: sum(c_def_k * x_k) <= B_def
    row = np.zeros(n_vars)
    row[idx_x:idx_x + n_K] = c_def
    A_rows.append(row)
    lhs.append(-np.inf)
    rhs.append(B_def)
    
    # 2. Dual Feasibility: lmbda * c_att_i + mu_i + R0_i * sum(delta_k * x_k) >= R0_i
    for i in range(n_I):
        row = np.zeros(n_vars)
        row[idx_lmbda] = c_att[i]
        row[idx_mu + i] = 1.0
        for k in asset_to_ctrl_indices[i]:
            row[idx_x + k] = R0[i] * delta[k]
        A_rows.append(row)
        lhs.append(R0[i])
        rhs.append(np.inf)
        
    # 3. Attacker Budget: sum(c_att_i * y_i) <= b_att
    row = np.zeros(n_vars)
    row[idx_y:idx_y + n_I] = c_att
    A_rows.append(row)
    lhs.append(-np.inf)
    rhs.append(b_att)
    
    # 4. Strong-Duality Linearization (Fortuny-Amat Disjunctions):

    # Lambda slackness:
    # lmbda - Big_M * z_lmbda <= 0
    row = np.zeros(n_vars)
    row[idx_lmbda] = 1.0
    row[idx_z_lmbda] = -Big_M
    A_rows.append(row)
    lhs.append(-np.inf)
    rhs.append(0.0)
    
    # (b_att - sum c_att_i * y_i) - M_att_slack * (1 - z_lmbda) <= 0
    # => -sum(c_att_i * y_i) + M_att_slack * z_lmbda <= M_att_slack - b_att
    M_att_slack = max(float(Big_M), float(b_att) + 5.0)
    row = np.zeros(n_vars)
    row[idx_y:idx_y + n_I] = -c_att
    row[idx_z_lmbda] = M_att_slack
    A_rows.append(row)
    lhs.append(-np.inf)
    rhs.append(M_att_slack - b_att)
    
    # Mu slackness for each i:
    # mu_i - Big_M * z_mu_i <= 0
    # (1 - y_i) - 1.0 * (1 - z_mu_i) <= 0 => -y_i + z_mu_i <= 0
    for i in range(n_I):
        row = np.zeros(n_vars)
        row[idx_mu + i] = 1.0
        row[idx_z_mu + i] = -Big_M
        A_rows.append(row)
        lhs.append(-np.inf)
        rhs.append(0.0)
        
        row = np.zeros(n_vars)
        row[idx_y + i] = -1.0
        row[idx_z_mu + i] = 1.0
        A_rows.append(row)
        lhs.append(-np.inf)
        rhs.append(0.0)
        
    # Dual slackness for each i:
    # y_i - z_dual_i <= 0
    # slack_i - Big_M * (1 - z_dual_i) <= 0
    # => lmbda * c_att_i + mu_i + R0_i * sum(delta_k * x_k) + Big_M * z_dual_i <= Big_M + R0_i
    for i in range(n_I):
        row = np.zeros(n_vars)
        row[idx_y + i] = 1.0
        row[idx_z_dual + i] = -1.0
        A_rows.append(row)
        lhs.append(-np.inf)
        rhs.append(0.0)
        
        row = np.zeros(n_vars)
        row[idx_lmbda] = c_att[i]
        row[idx_mu + i] = 1.0
        for k in asset_to_ctrl_indices[i]:
            row[idx_x + k] = R0[i] * delta[k]
        row[idx_z_dual + i] = Big_M
        A_rows.append(row)
        lhs.append(-np.inf)
        rhs.append(Big_M + R0[i])
        
    constraints = LinearConstraint(np.array(A_rows), lhs, rhs)
    
    start_time = time.time()
    #res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)
    res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints, options={'mip_rel_gap': 1e-4})

    solve_time = time.time() - start_time
    
    if not res.success:
        raise RuntimeError(f"MILP solver failed: {res.status} - {res.message}")
        
    sol = res.x
    damage = res.fun
    print(f"[Solver Log] Status: {res.status} ({res.message}) | Optimization Success: {res.success} | Time: {solve_time:.4f}s")
    x_sol = {k: int(round(sol[idx_x + k])) for k in range(n_K)}
    y_sol = {I_list[i]: float(sol[idx_y + i]) for i in range(n_I)}
    
    return {
        'damage': damage,
        'solve_time': solve_time,
        'x': x_sol,
        'y': y_sol
    }

# ==============================================================================
# 3. BENCHMARK HEURISTICS
# ==============================================================================
def evaluate_attacker_response(assets_df, controls_df, deployed_controls, b_att):
    """
    Evaluates the optimal attacker strategy (continuous knapsack response)
    given a specific set of deployed defender controls (indexed by DataFrame row indices).
    """
    r_effective = {}
    for i in assets_df['Asset_ID']:
        ctrls_for_i = controls_df[(controls_df['Asset_ID'] == i) & (controls_df.index.isin(deployed_controls))]
        sum_delta = ctrls_for_i['Delta_ik'].sum()
        r0_i = assets_df.loc[assets_df['Asset_ID'] == i, 'R0'].values[0]
        #r_effective[i] = max(0.0, float(r0_i - sum_delta))
        r_effective[i] = float(r0_i * max(0.0, 1.0 - sum_delta))

    
    atk_df = assets_df.copy()
    atk_df['R_eff'] = atk_df['Asset_ID'].map(r_effective)
    atk_df['Attacker_Efficiency'] = atk_df['R_eff'] / atk_df['Attacker_Cost_c_att']
    atk_df = atk_df.sort_values(by='Attacker_Efficiency', ascending=False)
    
    b_rem = float(b_att)
    total_damage = 0.0
    y_alloc = {i: 0.0 for i in assets_df['Asset_ID']}
    
    for _, row in atk_df.iterrows():
        a_id = row['Asset_ID']
        c_att = float(row['Attacker_Cost_c_att'])
        r_eff = float(row['R_eff'])
        
        if b_rem <= 0:
            break
            
        if b_rem >= c_att:
            y_alloc[a_id] = 1.0
            total_damage += r_eff
            b_rem -= c_att
        else:
            fraction = b_rem / c_att
            y_alloc[a_id] = fraction
            total_damage += fraction * r_eff
            b_rem = 0.0
            break
            
    return total_damage, y_alloc


def run_benchmark_heuristics(assets_df, controls_df, B_def, b_att):
    # 1. Greedy Mitigation-Cost Ratio
    r0_map = dict(zip(assets_df['Asset_ID'], assets_df['R0']))
    ctrls_greedy = controls_df.copy()
    ctrls_greedy['density'] = (ctrls_greedy['Delta_ik'] * ctrls_greedy['Asset_ID'].map(r0_map)) / ctrls_greedy['Cost_c_ik']
    ctrls_greedy = ctrls_greedy.sort_values(by='density', ascending=False)
    
    greedy_deployed = []
    current_cost = 0.0
    for idx, row in ctrls_greedy.iterrows():
        if current_cost + row['Cost_c_ik'] <= B_def:
            greedy_deployed.append(idx)
            current_cost += row['Cost_c_ik']
    damage_greedy, _ = evaluate_attacker_response(assets_df, controls_df, greedy_deployed, b_att)
    
    # 2. Industry Baseline (CVSS-Ranked)
    cvss_map = dict(zip(assets_df['Asset_ID'], assets_df['CVSS_v31_Base']))
    ctrls_cvss = controls_df.copy()
    ctrls_cvss['cvss'] = ctrls_cvss['Asset_ID'].map(cvss_map)
    ctrls_cvss = ctrls_cvss.sort_values(by=['cvss', 'Delta_ik'], ascending=[False, False])
    
    cvss_deployed = []
    current_cost = 0.0
    for idx, row in ctrls_cvss.iterrows():
        if current_cost + row['Cost_c_ik'] <= B_def:
            cvss_deployed.append(idx)
            current_cost += row['Cost_c_ik']
    damage_cvss, _ = evaluate_attacker_response(assets_df, controls_df, cvss_deployed, b_att)
    
    # 3. Uniform Defense
    uniform_deployed = []
    current_cost = 0.0
    for i in assets_df['Asset_ID']:
        first_ctrl = controls_df[controls_df['Asset_ID'] == i]
        if not first_ctrl.empty:
            idx = first_ctrl.index[0]
            cost = float(first_ctrl.iloc[0]['Cost_c_ik'])
            if current_cost + cost <= B_def:
                uniform_deployed.append(idx)
                current_cost += cost
    damage_uniform, _ = evaluate_attacker_response(assets_df, controls_df, uniform_deployed, b_att)
    
    # Return explicit dictionary for execute_full_suite
    return {
        'Greedy': damage_greedy,
        'CVSS_Ranked': damage_cvss,
        'Uniform': damage_uniform
    }


# ==============================================================================
# 4. EXPERIMENTS SUITE EXECUTION
# ==============================================================================
def execute_full_suite():
    print("=================================================================")
    print("EXECUTING FORENSIC STACKELBERG MILP (SciPy/HiGHS Engine)")
    print("=================================================================")
    
    assets_df, controls_df, params_df = load_and_validate_dataset('cps_stc4.xlsx')
    
    # Experiment 1: Budget Sweep
    print("\n[+] Running Experiment 1: Defender Budget Sweep & Benchmarks...")
    budgets = [0, 30, 60, 90, 120, 150, 180, 240, 300, 360, 480, 600]
    pareto_records = []
    for b in budgets:
        milp_res = solve_ssg_milp(assets_df, controls_df, B_def=b, b_att=50, Big_M=2.0)
        bench_res = run_benchmark_heuristics(assets_df, controls_df, B_def=b, b_att=50)
        pareto_records.append({
            'Defender_Budget': b,
            'Proposed_MILP': milp_res['damage'],
            'Greedy_Heuristic': bench_res['Greedy'],
            'CVSS_Ranked': bench_res['CVSS_Ranked'],
            'Uniform_Defense': bench_res['Uniform'],
            'Solve_Time_Sec': milp_res['solve_time']
        })
    pareto_df = pd.DataFrame(pareto_records)
    
    # Experiment 2: Bilevel Heatmap
    print("[+] Running Experiment 2: Bilevel Budget Matrix...")
    b_def_range = [30, 60, 90, 120, 180, 240]
    b_att_range = [10, 25, 50, 75, 100]
    heatmap_matrix = np.zeros((len(b_att_range), len(b_def_range)))
    for r_idx, b_att_val in enumerate(b_att_range):
        for c_idx, b_def_val in enumerate(b_def_range):
            res = solve_ssg_milp(assets_df, controls_df, B_def=b_def_val, b_att=b_att_val, Big_M=2.0)
            heatmap_matrix[r_idx, c_idx] = res['damage']
    heatmap_df = pd.DataFrame(heatmap_matrix, index=[f"b_att={x}" for x in b_att_range],
                              columns=[f"B={x}" for x in b_def_range])
    
    # Experiment 3: Big-M Sensitivity
    print("[+] Running Experiment 3: Big-M Sensitivity Analysis...")
    big_m_values = [1.5, 2.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]
    big_m_records = []
    for m in big_m_values:
        res = solve_ssg_milp(assets_df, controls_df, B_def=120, b_att=50, Big_M=m)
        big_m_records.append({
            'Big_M': m,
            'Expected_Damage': res['damage'],
            'Solve_Time_Sec': res['solve_time']
        })
    big_m_df = pd.DataFrame(big_m_records)
    
    # Experiment 4: Target Shifting
    print("[+] Running Experiment 4: Attacker Target Shifting...")
    shift_budgets = [0, 60, 120, 180, 240]
    shift_records = {}
    for b in shift_budgets:
        res = solve_ssg_milp(assets_df, controls_df, B_def=b, b_att=50, Big_M=2.0)
        shift_records[f"B={b}"] = res['y']
    shift_df = pd.DataFrame(shift_records)
    
    # Export to Excel
    out_excel = 'ssg_computational_results.xlsx'
    with pd.ExcelWriter(out_excel) as writer:
        pareto_df.to_excel(writer, sheet_name='Pareto_and_Benchmarks', index=False)
        heatmap_df.to_excel(writer, sheet_name='Bilevel_Heatmap')
        big_m_df.to_excel(writer, sheet_name='Big_M_Sensitivity', index=False)
        shift_df.to_excel(writer, sheet_name='Target_Shifting')
    print(f"[+] Output dataset successfully saved to: {out_excel}")
    
    return pareto_df, heatmap_df, big_m_df, shift_df

# ==============================================================================
# 5. RENDERING 300 DPI FIGURES
# ==============================================================================
def render_manuscript_figures(pareto_df, heatmap_df, big_m_df, shift_df):
    print("\n[+] Exporting Figures at  600 DPI...")
    
    # Figure 1
    plt.figure(figsize=(9, 5.5))
    plt.plot(pareto_df['Defender_Budget'], pareto_df['Proposed_MILP'], 'r-o', linewidth=2, label='Proposed Strong-Duality MILP (Optimal)')
    plt.plot(pareto_df['Defender_Budget'], pareto_df['Greedy_Heuristic'], 'b--s', linewidth=1.5, label='Greedy Mitigation-Cost Ratio')
    plt.plot(pareto_df['Defender_Budget'], pareto_df['CVSS_Ranked'], 'g-.^', linewidth=1.5, label='Industry Baseline (CVSS-Ranked)')
    plt.plot(pareto_df['Defender_Budget'], pareto_df['Uniform_Defense'], 'k:d', linewidth=1.5, label='Uniform Allocation')
    plt.axvline(x=120, color='gray', linestyle=':', label='Baseline Budget ($B=120$)')
    plt.title('Figure 1: Risk Mitigation Pareto Frontier vs. State-of-the-Art Benchmarks', fontsize=11, fontweight='bold')
    plt.xlabel('Defender Security Budget ($B$)', fontsize=10)
    plt.ylabel('Attacker Expected System Damage ($R^{\\mathrm{post}}$)', fontsize=10)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('Figure_1_Pareto_Front.png', dpi=600)
    plt.close()
    
    # Figure 2
    plt.figure(figsize=(8, 6))
    heat_data = heatmap_df.copy()
    heat_data.index = [x.replace('b_att=', '$b^{\\mathrm{att}}=') + '$' for x in heat_data.index]
    heat_data.columns = [x.replace('B=', '$B=') + '$' for x in heat_data.columns]
    
    cax = plt.imshow(heat_data.values, cmap='YlOrRd', aspect='auto')
    plt.colorbar(cax, label='Expected Post-Attack Damage')
    plt.xticks(np.arange(len(heat_data.columns)), heat_data.columns)
    plt.yticks(np.arange(len(heat_data.index)), heat_data.index)
    for i in range(len(heat_data.index)):
        for j in range(len(heat_data.columns)):
            plt.text(j, i, f"{heat_data.values[i, j]:.2f}", ha='center', va='center', color='black', fontsize=9)
    plt.title('Figure 2: Bilevel Game Interaction Matrix (Defender vs. Attacker Budget)', fontsize=11, fontweight='bold')
    plt.xlabel('Defender Budget Allocation ($B$)', fontsize=10)
    plt.ylabel('Attacker Infiltration Budget ($b^{\\mathrm{att}}$)', fontsize=10)
    plt.tight_layout()
    plt.savefig('Figure_2_Budget_Heatmap.png', dpi=600)
    plt.close()
    
    # Figure 3
    fig, ax1 = plt.subplots(figsize=(8, 5))
    color = 'tab:blue'
    ax1.set_xlabel('Big-$M$ Penalty Parameter (Log Scale)', fontsize=10)
    ax1.set_ylabel('Execution Time (seconds)', color=color, fontsize=10)
    ax1.plot(big_m_df['Big_M'], big_m_df['Solve_Time_Sec'], color=color, marker='s', linewidth=1.8)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xscale('log')
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Calculated System Damage', color=color, fontsize=10)
    ax2.plot(big_m_df['Big_M'], big_m_df['Expected_Damage'], color=color, marker='o', linestyle='--', linewidth=1.5)
    ax2.tick_params(axis='y', labelcolor=color)
     # Force plain numerical formatting on axes to eliminate offset notation (+2.884e0)
    ax1.ticklabel_format(style='plain', useOffset=False, axis='y')
    ax2.ticklabel_format(style='plain', useOffset=False, axis='y')

    plt.title('Figure 3: Computational Tractability and Solution Invariance across Big-M', fontsize=11, fontweight='bold')
    plt.tight_layout()
    # Save both high-resolution PNG and publication-ready vector PDF
    plt.savefig('Figure_3_BigM_Analysis.png', dpi=600, bbox_inches='tight')
    plt.savefig('Figure_3_BigM_Analysis.pdf', format='pdf', bbox_inches='tight')
    plt.close()

    
    # Figure 4
    plt.figure(figsize=(10, 5.5))
    assets = shift_df.index.tolist()
    x = np.arange(len(assets))
    width = 0.15
    for idx, col in enumerate(shift_df.columns):
        plt.bar(x + idx * width, shift_df[col], width, label=col)
    plt.xlabel('CPS Physical Assets (A01 - A10)', fontsize=10)
    plt.ylabel('Attacker Attack Probability / Infiltration Share ($y_i$)', fontsize=10)
    plt.title('Figure 4: Attacker Target Deflection Dynamics Under Progressive Defense Budgets', fontsize=11, fontweight='bold')
    plt.xticks(x + width * 2, assets)
    plt.legend(frameon=True, fontsize=9)
    plt.grid(True, linestyle='--', alpha=0.5, axis='y')
    plt.tight_layout()
    plt.savefig('Figure_4_Target_Shifting.png', dpi=600)
    plt.close()

if __name__ == "__main__":
    pareto, heatmap, big_m, shift = execute_full_suite()
    render_manuscript_figures(pareto, heatmap, big_m, shift)
    print("\n[+] Full Suite Completed: Excel & 4 Figures Ready for IJIS Submission.")
