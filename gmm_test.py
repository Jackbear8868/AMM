#!/usr/bin/env python3
# gmm_gpu.py ---------------------------------------------------
"""
GPU-accelerated two-step GMM for volume equation
    V  = a0 + a_sigma·sigma + a_c·sqrt(c) + ε
• supports float32 / float64
• streams dataset in batches if the whole thing does not fit in VRAM
• falls back to NumPy when no CUDA device is visible
"""

import argparse, sys, math, os
import numpy as np
import pandas as pd

# ------------------------------------------------------------
# 0. CLI
# ------------------------------------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--csv",   required=True, help="CSV with V, sigma, c")
ap.add_argument("--dtype", choices=["float32","float64"], default="float32")
ap.add_argument("--batch", type=int, default=0,
                help="rows per GPU batch (0 = auto)")
args   = ap.parse_args()
DTYPE  = np.float32 if args.dtype=="float32" else np.float64
BYTES  = 4 if args.dtype=="float32" else 8
EPS    = 1e-8

# ------------------------------------------------------------
# 1. pick backend: CuPy if GPU, else NumPy
# ------------------------------------------------------------
try:
    import cupy as xp              # noqa: F401
    nGPU = xp.cuda.runtime.getDeviceCount()
    print(f"🟢  CuPy detected  ({nGPU} GPU)")
except Exception:
    import numpy as xp             # type: ignore
    xp.cuda = None                 # dummy attr
    print("🟡  CuPy not found – fallback to CPU NumPy")

GPU = (xp.__name__ == "cupy")

# ------------------------------------------------------------
# 2. quick scan CSV – count rows  (avoid loading twice)
# ------------------------------------------------------------
row_count = sum(1 for _ in open(args.csv)) - 1
print(f"rows in CSV = {row_count:,}")

# ------------------------------------------------------------
# 3. decide batch size
#   memory ≈ 28 * T * bytes_per_float  (see derivation earlier)
# ------------------------------------------------------------
def auto_batch(rows:int, bytes_per=BYTES, vram_GB:float=8.0):
    need = 28 * rows * bytes_per / 1024**3
    return rows if need < vram_GB*0.8 else int(math.floor(vram_GB*0.8*1024**3/(28*bytes_per)))

if args.batch > 0:
    batch_rows = args.batch
else:
    batch_rows = auto_batch(row_count, BYTES,  xp.cuda.Device().mem_info[1]/1024**3 if GPU else 16)

print(f"batch_rows = {batch_rows:,}   (dtype={args.dtype})")

# ------------------------------------------------------------
# 4. first pass  – read in batches, build sufficient stats
#   we need:
#     S₁ = Σ Z'ε   (size 12)
#     S₂ = Σ (Z'ε)(Z'ε)' (size 12×12)
#   plus   X'X , X'y  for closed-form OLS (step-1)
# ------------------------------------------------------------
p   = 12
XtX = xp.zeros((3,3),  dtype=DTYPE)
Xty = xp.zeros(3,       dtype=DTYPE)
Sum_m   = xp.zeros(p,   dtype=DTYPE)
Sum_mmT = xp.zeros((p,p),dtype=DTYPE)

reader = pd.read_csv(args.csv, chunksize=batch_rows,
                     dtype={"V":DTYPE,"sigma":DTYPE,"c":DTYPE})

tot = 0
for chunk in reader:
    chunk["V_prev"] = chunk["V"].shift(1)
    chunk = chunk.dropna(subset=["V","sigma","c","V_prev"])
    chunk = chunk[(chunk["V_prev"]>0)&(chunk["c"]>0)&(chunk["sigma"]>=0)]
    if chunk.empty: continue

    V      = xp.asarray(chunk["V"].values,      dtype=DTYPE)
    sigma  = xp.asarray(chunk["sigma"].values,  dtype=DTYPE)
    c      = xp.asarray(chunk["c"].values,      dtype=DTYPE)
    V_prev = xp.asarray(chunk["V_prev"].values, dtype=DTYPE)
    T = V.size;  tot += T

    X = xp.column_stack((xp.ones(T,dtype=DTYPE), sigma, xp.sqrt(c)))
    XtX += X.T @ X
    Xty += X.T @ V

print(f"effective rows after cleaning = {tot:,}")

# ---------- step-1 closed-form / OLS -------------------------
theta1 = xp.linalg.solve(XtX, Xty).get() if GPU else np.linalg.solve(XtX, Xty)
print("step-1 theta (OLS) =", theta1)

# ------------------------------------------------------------
# 5. second pass  – compute optimal weight matrix
#   S = cov( moments )
# ------------------------------------------------------------
reader = pd.read_csv(args.csv, chunksize=batch_rows,
                     dtype={"V":DTYPE,"sigma":DTYPE,"c":DTYPE})
tot = 0
Sum_m.fill(0); Sum_mmT.fill(0)

a0, a_sig, a_c = [DTYPE(x) for x in theta1]

for chunk in reader:
    chunk["V_prev"] = chunk["V"].shift(1)
    chunk = chunk.dropna(subset=["V","sigma","c","V_prev"])
    chunk = chunk[(chunk["V_prev"]>0)&(chunk["c"]>0)&(chunk["sigma"]>=0)]
    if chunk.empty: continue

    V      = xp.asarray(chunk["V"].values,      dtype=DTYPE)
    sigma  = xp.asarray(chunk["sigma"].values,  dtype=DTYPE)
    c      = xp.asarray(chunk["c"].values,      dtype=DTYPE)
    V_prev = xp.asarray(chunk["V_prev"].values, dtype=DTYPE)
    T = V.size;  tot += T

    Z_base = xp.column_stack((xp.ones(T,dtype=DTYPE),
                              sigma,
                              xp.sqrt(c)))
    log_c  = xp.log(c+EPS)
    log_v  = xp.log(V_prev+EPS)
    Z = xp.column_stack((Z_base,
                         Z_base*sigma[:,None],
                         Z_base*log_c[:,None],
                         Z_base*log_v[:,None]))

    resid = V - a0 - a_sig*sigma - a_c*xp.sqrt(c)
    m = resid[:,None] * Z                 # (T,12)

    Sum_m   += m.sum(axis=0)
    Sum_mmT += m.T @ m

# mean & covariance (on GPU then bring back)
m_bar = Sum_m / tot
S     = (Sum_mmT / tot) - m_bar[:,None]*m_bar[None,:]
m_bar_host = m_bar.get() if GPU else m_bar
S_host     = S.get()     if GPU else S
W_opt = np.linalg.pinv(S_host)

# ------------------------------------------------------------
# 6. step-2 minimization  (still on CPU, small matrix ops)
# ------------------------------------------------------------
def avg_m(theta):
    a0,a_sig,a_c = theta.astype(DTYPE)
    # stream again (memory cheap): only need mean of moments
    reader = pd.read_csv(args.csv, chunksize=batch_rows,
                         dtype={"V":DTYPE,"sigma":DTYPE,"c":DTYPE})
    totM = np.zeros(12, dtype=DTYPE); N=0
    for ch in reader:
        ch["V_prev"]=ch["V"].shift(1)
        ch=ch.dropna(subset=["V","sigma","c","V_prev"])
        ch=ch[(ch["V_prev"]>0)&(ch["c"]>0)&(ch["sigma"]>=0)]
        if ch.empty: continue
        V = ch["V"].to_numpy(dtype=DTYPE)
        sigma = ch["sigma"].to_numpy(dtype=DTYPE)
        c = ch["c"].to_numpy(dtype=DTYPE)
        V_prev = ch["V_prev"].to_numpy(dtype=DTYPE)
        T=V.size; N+=T
        Zb   = np.column_stack((np.ones(T), sigma, np.sqrt(c))).astype(DTYPE)
        m = (V - a0 - a_sig*sigma - a_c*np.sqrt(c))[:,None] * np.column_stack(
                (Zb,
                 Zb*sigma[:,None],
                 Zb*np.log(c+EPS)[:,None],
                 Zb*np.log(V_prev+EPS)[:,None])
            )
        totM += m.sum(axis=0)
    return totM/N

def gmm2(theta):
    m=avg_m(theta)
    return m@W_opt@m

from scipy.optimize import minimize
theta2 = minimize(gmm2, theta1, method="BFGS").x
print("step-2 theta =",theta2)
