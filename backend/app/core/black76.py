# backend/app/core/black76.py
import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
import pandas as pd

@dataclass
class GreekResult:
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    vanna: float
    charm: float
    vomma: float
    speed: float

class Black76Engine:
    R = 0.065
    def price_and_greeks(self, F, K, T, sigma, option_type) -> GreekResult:
        if T <= 0: T = 1/365/24
        if sigma <= 0: sigma = 0.001
        r = self.R
        sqrt_T = np.sqrt(T)
        d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        exp_rT = np.exp(-r * T)
        pdf_d1 = norm.pdf(d1)
        if option_type == 'CE':
            price = exp_rT * (F * norm.cdf(d1) - K * norm.cdf(d2))
            delta = exp_rT * norm.cdf(d1)
        else:
            price = exp_rT * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
            delta = exp_rT * (norm.cdf(d1) - 1)
        gamma = exp_rT * pdf_d1 / (F * sigma * sqrt_T)
        vega = F * exp_rT * pdf_d1 * sqrt_T / 100
        theta_base = -(F * exp_rT * pdf_d1 * sigma / (2 * sqrt_T)) / 365
        theta = theta_base - r * K * exp_rT * (norm.cdf(d2) if option_type == 'CE' else -norm.cdf(-d2)) / 365
        vanna = -exp_rT * (d2 / sigma) * pdf_d1
        term = (2*r*T - d2*sigma*sqrt_T) / (2*T*sigma*sqrt_T)
        charm = exp_rT * pdf_d1 * term * (1 if option_type == 'CE' else -1)
        return GreekResult(price, delta, gamma, vega, theta, vanna, charm, 0, 0)
