# backend/app/core/black76.py

import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class GreekResult:
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    vanna: float     # dDelta/dIV — VEX ingredient
    charm: float     # dDelta/dT  — CEX ingredient
    vomma: float     # dVega/dIV  — 3rd order
    speed: float     # dGamma/dF  — 3rd order

class Black76Engine:
    """
    CORRECT model for Indian F&O options.
    Uses FUTURES PRICE (F), not Spot.

    Per ANZA docs: Always subscribe to AngelOne FUTURES TOKEN,
    not cash index, for F input.

    Constants (Feb 2026 per ANZA docs):
    - r = 6.5% (India 10Y G-Sec)
    """

    R = 0.065       # India risk-free rate
    EPSILON = 1e-8  # Newton-Raphson convergence

    def price_and_greeks(
        self,
        F: float,       # Futures price (NOT spot)
        K: float,       # Strike
        T: float,       # Time to expiry in years
        sigma: float,   # Implied volatility (decimal)
        option_type: str  # 'CE' or 'PE'
    ) -> GreekResult:

        if T <= 0: T = 1/365/24  # 1 hour floor
        if sigma <= 0: sigma = 0.001

        r = self.R
        sqrt_T = np.sqrt(T)

        d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T

        exp_rT = np.exp(-r * T)
        Nd1    = norm.cdf(d1)
        Nd2    = norm.cdf(d2)
        Nm_d1  = norm.cdf(-d1)
        Nm_d2  = norm.cdf(-d2)
        pdf_d1 = norm.pdf(d1)

        if option_type == 'CE':
            price = exp_rT * (F * Nd1 - K * Nd2)
            delta = exp_rT * Nd1
        else:  # PE
            price = exp_rT * (K * Nm_d2 - F * Nm_d1)
            delta = exp_rT * (Nd1 - 1)   # = -exp(-rT) * N(-d1)

        # Gamma (same for CE and PE)
        gamma = exp_rT * pdf_d1 / (F * sigma * sqrt_T)

        # Vega (same sign for both) — per 1% IV move / 100
        vega = F * exp_rT * pdf_d1 * sqrt_T / 100

        # Theta — per day
        theta_base = -(F * exp_rT * pdf_d1 * sigma / (2 * sqrt_T)) / 365
        if option_type == 'CE':
            theta = theta_base - r * K * exp_rT * Nd2 / 365
        else:
            theta = theta_base + r * K * exp_rT * Nm_d2 / 365

        # Vanna = dDelta/dIV = -exp(-rT) * d2 * pdf(d1) / sigma
        vanna = -exp_rT * (d2 / sigma) * pdf_d1

        # Charm = dDelta/dT
        if option_type == 'CE':
            charm = exp_rT * pdf_d1 * (
                (2*r*T - d2*sigma*sqrt_T) / (2*T*sigma*sqrt_T)
            )
        else:
            charm = -exp_rT * pdf_d1 * (
                (2*r*T - d2*sigma*sqrt_T) / (2*T*sigma*sqrt_T)
            )

        # Vomma = dVega/dIV
        vomma = vega * d1 * d2 / sigma

        # Speed = dGamma/dF
        speed = -gamma * (1 + d1 / (sigma * sqrt_T)) / F

        return GreekResult(
            price=price, delta=delta, gamma=gamma,
            vega=vega, theta=theta, vanna=vanna,
            charm=charm, vomma=vomma, speed=speed
        )

    def implied_volatility(
        self, market_price: float, F: float, K: float,
        T: float, option_type: str
    ) -> float:
        """
        Newton-Raphson IV solver using Black-76 vega as Jacobian.
        """
        if T <= 0 or market_price <= 0:
            return 0.0

        # Bounds check: intrinsic value
        intrinsic = max(0, F - K) if option_type == 'CE' else max(0, K - F)
        if market_price <= intrinsic:
            return 0.001

        sigma = 0.30  # Initial guess

        for _ in range(100):
            g = self.price_and_greeks(F, K, T, sigma, option_type)
            diff = g.price - market_price

            if abs(diff) < self.EPSILON:
                break

            vega_adj = g.vega * 100  # vega was per 1%, need per unit
            if abs(vega_adj) < 1e-10:
                break

            sigma = sigma - diff / vega_adj
            sigma = max(0.001, min(sigma, 5.0))  # 0.1% to 500% IV bounds

        return sigma

    def iv_surface_vectorized(
        self, option_chain: List[Dict], F: float, T: float
    ) -> List[Dict]:
        """
        Solve IV for all strikes simultaneously (conceptual wrapper).
        For now, iterating over rows to keep it simple without py_vollib_vectorized dependency issues.
        The plan mentioned vectorization, but we can implement it iteratively first for correctness.
        """
        results = []
        for row in option_chain:
            processed_row = row.copy()
            for opt_type in ['CE', 'PE']:
                price = row.get(f'{opt_type.lower()}_ltp', 0)
                strike = row['strike']
                if price > 0 and T > 0:
                    iv = self.implied_volatility(price, F, strike, T, opt_type)
                    greeks = self.price_and_greeks(F, strike, T, iv, opt_type)

                    processed_row[f'{opt_type.lower()}_iv'] = iv
                    processed_row[f'{opt_type.lower()}_delta'] = greeks.delta
                    processed_row[f'{opt_type.lower()}_gamma'] = greeks.gamma
                    processed_row[f'{opt_type.lower()}_vega'] = greeks.vega
                    processed_row[f'{opt_type.lower()}_theta'] = greeks.theta
                    processed_row[f'{opt_type.lower()}_vanna'] = greeks.vanna
                    processed_row[f'{opt_type.lower()}_charm'] = greeks.charm
            results.append(processed_row)
        return results
