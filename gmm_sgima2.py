from numpy.linalg import inv, pinv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import chi2

# 載入資料
data = pd.read_csv("data.csv")
V = data['V'].values
sigma = data['sigma'].values
c = data['c'].values
V_prev = data['V_prev'].values
T = len(V)

# 定義模型變體
def build_instruments(use_sigma_squared=False):
    sig_term = sigma**2 if use_sigma_squared else sigma
    z_base = np.column_stack((np.ones(T), sig_term, np.sqrt(c)))
    log_c = np.log(c + 1e-8)
    log_v = np.log(V_prev + 1e-8)
    z_ext1 = z_base * sig_term[:, None]
    z_ext2 = z_base * log_c[:, None]
    z_ext3 = z_base * log_v[:, None]
    instruments = np.column_stack((z_base, z_ext1, z_ext2, z_ext3))
    return instruments, sig_term

def gmm_estimation(use_sigma_squared=False):
    instruments, sig_term = build_instruments(use_sigma_squared)

    def compute_moments(theta):
        a_0, a_sigma, a_c = theta
        residuals = V - a_0 - a_sigma * sig_term - a_c * np.sqrt(c)
        m = residuals[:, None] * instruments
        return m

    def average_moments(theta):
        return compute_moments(theta).mean(axis=0)

    def gmm_obj_step1(theta):
        m = average_moments(theta)
        return m @ m

    theta0 = [50, 1000, 5]
    result1 = minimize(gmm_obj_step1, theta0, method='BFGS')
    theta1 = result1.x

    m_matrix = compute_moments(theta1)
    S = np.cov(m_matrix.T, bias=True)
    W = pinv(S)

    def gmm_obj_step2(theta):
        m = average_moments(theta)
        return m @ W @ m

    result2 = minimize(gmm_obj_step2, theta1, method='BFGS')
    theta2 = result2.x

    def numerical_gradient(f, theta, eps=1e-6):
        grad = []
        for i in range(len(theta)):
            delta = np.zeros_like(theta)
            delta[i] = eps
            diff = (f(theta + delta) - f(theta - delta)) / (2 * eps)
            grad.append(diff)
        return np.array(grad).T

    G = numerical_gradient(average_moments, theta2)
    var_theta = inv(G.T @ W @ G)
    std_err = np.sqrt(np.diag(var_theta))
    ci_lower = theta2 - 1.96 * std_err
    ci_upper = theta2 + 1.96 * std_err

    # Hansen J-test
    m_final = average_moments(theta2)
    J_stat = T * m_final @ W @ m_final
    df = len(m_final) - len(theta2)
    p_value = 1 - chi2.cdf(J_stat, df)

    return theta2, std_err, ci_lower, ci_upper, J_stat, p_value

# 執行對比實驗
theta_linear, se_linear, ci_l_linear, ci_u_linear, j_linear, p_linear = gmm_estimation(False)
theta_squared, se_squared, ci_l_squared, ci_u_squared, j_squared, p_squared = gmm_estimation(True)

(theta_linear, se_linear, ci_l_linear, ci_u_linear, j_linear, p_linear,
 theta_squared, se_squared, ci_l_squared, ci_u_squared, j_squared, p_squared)
