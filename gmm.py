#!/usr/bin/env python
# coding: utf-8
"""
two_step_gmm_volume.py
-------------------------------------------------
• 讀取 data.csv（需含 V, sigma, c 三欄）
• 自動產生 V_prev = V.shift(1)
• 刪除任何含 NaN 的列
• 刪除對 log / sqrt 不合法的列 (V_prev<=0, c<=0)
• 建立 12 維 instruments
• 兩階段 GMM 估計 a0, a_sigma, a_c
• 輸出估計值、標準誤、95% CI、Hansen J-test
• 畫收斂軌跡與誤差條圖
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import inv, pinv
from scipy.optimize import minimize
from scipy.stats import chi2

# ---------------- 1. 讀檔並基礎清理 ---------------- #
CSV_FILE = "data.csv"              # ← 若檔名不同請修改
EPS      = 1e-8                    # 防 log(0)

data = pd.read_csv(CSV_FILE, dtype=str)

# 把數字欄轉成 float，轉不過去則成 NaN
for col in ['V', 'sigma', 'c']:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# 產生 V_prev
data['V_prev'] = data['V'].shift(1)

# 直接丟棄任何關鍵欄位為 NaN 的列
data = data.dropna(subset=['V', 'sigma', 'c', 'V_prev']).reset_index(drop=True)

# 丟棄對 log/sqrt 不合法的列
data = data[(data['V_prev'] > 0) & (data['c'] > 0) & (data['sigma'] >= 0)].reset_index(drop=True)

# ---------------- 2. NumPy 陣列 ---------------- #
V      = data['V'     ].to_numpy()
sigma  = data['sigma' ].to_numpy()
c      = data['c'     ].to_numpy()
V_prev = data['V_prev'].to_numpy()
T      = len(V)

# ---------------- 3. instruments (12 維) ---------------- #
z_base = np.column_stack((np.ones(T),            # 1
                          sigma,                 # 2
                          np.sqrt(c)))           # 3

log_c  = np.log(c      + EPS)
log_v  = np.log(V_prev + EPS)

z_ext1 = z_base * sigma[:, None]   # 3 × sigma  → 3 cols
z_ext2 = z_base * log_c[:, None]   # 3 × log c → 3 cols
z_ext3 = z_base * log_v[:, None]   # 3 × log v → 3 cols

Z = np.column_stack((z_base, z_ext1, z_ext2, z_ext3))  # (T, 12)

# ---------------- 4. GMM moment 函數 ---------------- #
def compute_moments(theta):
    a0, a_sigma, a_c = theta
    resid = V - a0 - a_sigma * sigma - a_c * np.sqrt(c)
    return resid[:, None] * Z            # shape (T, 12)

def avg_moments(theta):
    return compute_moments(theta).mean(axis=0)   # shape (12,)

# --------------- 5. 一階段 GMM (identity weight) ------- #
def gmm_obj_step1(theta):
    m = avg_moments(theta)
    return m @ m                               # 即 m'Im

theta0 = np.array([50.0, 1000.0, 5.0])         # 初始猜值，依資料調整
res1   = minimize(gmm_obj_step1, theta0, method='BFGS')
theta1 = res1.x

# --------------- 6. 二階段 GMM (optimal weight) -------- #
#   (a) 計算 sample covariance S
m_mat = compute_moments(theta1)
S     = np.cov(m_mat.T, bias=True)             # shape (12, 12)
W_opt = pinv(S)                                # Moore-Penrose 逆

def gmm_obj_step2(theta):
    m = avg_moments(theta)
    return m @ W_opt @ m                       # m' W m

#   (b) 估計
trajectory = []
def _track(xk): trajectory.append(xk.copy())

res2   = minimize(gmm_obj_step2, theta1, method='BFGS', callback=_track)
theta2 = res2.x

# ---------------- 7. 標準誤 (兩階段) ------------------- #
def num_grad(f, theta, eps=1e-6):
    g = np.zeros((len(theta), len(avg_moments(theta))))
    for i in range(len(theta)):
        delta        = np.zeros_like(theta)
        delta[i]     = eps
        g[i, :]      = (f(theta + delta) - f(theta - delta)) / (2*eps)
    return g.T                                       # shape (12, 3)

G     = num_grad(avg_moments, theta2)
var_t = inv(G.T @ W_opt @ G) / T                     # Newey-West 可另行加入
se_t  = np.sqrt(np.diag(var_t))

z_95      = 1.96
ci_lower  = theta2 - z_95 * se_t
ci_upper  = theta2 + z_95 * se_t
param_names = ['a0', 'a_sigma', 'a_c']

# ---------------- 8. Hansen J-test --------------------- #
m_final = avg_moments(theta2)
J_stat  = T * (m_final @ W_opt @ m_final)
df_J    = Z.shape[1] - len(theta2)
p_J     = 1 - chi2.cdf(J_stat, df_J)

# ---------------- 9. 輸出結果 ------------------------- #
print("\n=== Two-step GMM Estimates ===")
for n, est, se, lo, hi in zip(param_names, theta2, se_t, ci_lower, ci_upper):
    print(f"{n:8}: {est:12.4f}  SE={se:9.4f}  95% CI=[{lo:10.4f}, {hi:10.4f}]")

print(f"\nHansen J-stat = {J_stat:.4f}  (df={df_J})  p-value = {p_J:.4f}")

# ---------------- 10. 收斂軌跡圖 ----------------------- #
trajectory = np.vstack(trajectory)  # shape (iters, 3)
fig, axes = plt.subplots(3, 1, figsize=(7, 9), sharex=True)
for i, ax in enumerate(axes):
    ax.plot(trajectory[:, i], marker='o')
    ax.axhline(theta2[i], color='r', ls='--', label='Final')
    ax.set_ylabel(param_names[i])
    ax.legend()
axes[-1].set_xlabel('Iteration')
fig.suptitle('Parameter Convergence (Step 2)')
plt.tight_layout()
plt.show()

# ---------------- 11. 誤差條圖 ------------------------- #
plt.figure(figsize=(6, 4))
x_pos = np.arange(len(theta2))
plt.bar(x_pos, theta2, yerr=se_t, alpha=0.7, capsize=8)
plt.xticks(x_pos, param_names)
plt.ylabel('Estimate')
plt.title('GMM Parameter Estimates ± 1 SE')
plt.grid(True, axis='y')
plt.tight_layout()
plt.show()
