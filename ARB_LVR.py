import matplotlib.pyplot as plt
from mpmath import mp, cosh, sqrt
import numpy as np

# Set high precision
mp.dps = 50

# Functions with high precision
def P_trade(lam, gamma, sigma):
    return 1 / (1 + sqrt(2 * lam) * gamma / sigma)

def ARB(lam, gamma, sigma):
    a = sigma ** 2 / 8
    if lam > a:
        b = P_trade(lam, gamma, sigma)
        c = cosh(gamma / 2) / (1 - a / lam)
        return a * b * c
    else:
        return 0

def perfect_gamma(lam,sigma):
    return sigma/sqrt(2*lam)

def sigma_z(lam, gamma, sigma):
    P = P_trade(lam, gamma, sigma)
    a = (1 - P) * gamma ** 2 / 3
    tmp = sigma / sqrt(2 * lam)
    b = P * ((gamma + tmp)**2 + tmp**2)
    return sqrt(a + b)

# Parameters
sigma = 0.08  # Daily volatility (fractional, e.g., 5% = 0.05)
lam = 1 / 12 * 86400 # Mean interblock time (12 seconds)
gammas = np.linspace(0.01, 200, 1000) * 0.0001  # Gamma in fractional units (0.01 bp to 100 bp)

# Compute values
arb_values = [ARB(lam, gamma, sigma) * 10000 for gamma in gammas]  # Convert ARB to bp
sigma_z_values = [sigma_z(lam, gamma, sigma) * 10000 for gamma in gammas]  # Convert σ_z to bp

# Highlight points for specific gamma values
highlight_gammas = [0.01, 1, 5, 10, 30, 100]  # Gamma in bp
highlight_points = [(sigma_z(lam, gamma * 0.0001, sigma) * 10000,
                     ARB(lam, gamma * 0.0001, sigma) * 10000)
                    for gamma in highlight_gammas]

# Plot ARB/V(P) vs σ_z
plt.figure(figsize=(10, 6))
plt.plot(sigma_z_values, arb_values, label=r'ARB/$V(P)$', color='blue')

# Add horizontal line at σ^2 / 8 (in bp)
horizontal_line = (sigma ** 2 / 8) * 10000
plt.axhline(y=horizontal_line, color='red', linestyle='--', label=r'LVR/$V(P) = \sigma^2 / 8$')

# Add vertical line at σ sqrt(1/λ) (in bp)
vertical_line = sigma * sqrt(1 / lam) * 10000
plt.axvline(x=vertical_line, color='green', linestyle='--', label=r'$\sigma \sqrt{1/\lambda}$')

# Add highlight points
for (sigma_z_val, arb_val), gamma in zip(highlight_points, highlight_gammas):
    plt.scatter(sigma_z_val, arb_val, color='red')
    plt.text(sigma_z_val, arb_val, f"γ = {gamma} (bp)", fontsize=8, color='red')

# Labels and Title
plt.xlabel(r'$\sigma_z$ (bp)', fontsize=12)
plt.ylabel(r'ARB/$V(P)$ (bp, daily)', fontsize=12)
plt.title(r'ARB/$V(P)$ vs $\sigma_z$ with Varying $\gamma$', fontsize=14)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(f"ARB_vs_sigma_z_{round(sigma*100)}.jpg")
plt.close()  # Close the plot

sigmas = np.linspace(0.001, 0.35, 350)
perfect_gamma_values = [perfect_gamma(lam, sigma) for sigma in sigmas]  # Convert σ_z to bp

plt.figure(figsize=(10, 6))
plt.plot(sigmas, perfect_gamma_values, label=r'gamma(P)$', color='blue')
plt.savefig(f"gamma_vs_sigma_z.jpg")
