# backend/tests/test_core_engines.py

import unittest
from app.core.black76 import Black76Engine
from app.core.gex import DealerExposureEngine
from app.core.oi_analysis import OIVelocityEngine, OISnapshot
import time

class TestBlack76(unittest.TestCase):
    def setUp(self):
        self.engine = Black76Engine()

    def test_atm_delta(self):
        # ATM Call Delta should be approx 0.5
        F = 19500
        K = 19500
        T = 7/365
        sigma = 0.15

        # Call
        res_ce = self.engine.price_and_greeks(F, K, T, sigma, 'CE')
        self.assertAlmostEqual(res_ce.delta, 0.5, delta=0.05)

        # Put
        res_pe = self.engine.price_and_greeks(F, K, T, sigma, 'PE')
        self.assertAlmostEqual(res_pe.delta, -0.5, delta=0.05)

    def test_theta_decay(self):
        # Theta should be negative for long options
        res = self.engine.price_and_greeks(19500, 19600, 7/365, 0.15, 'CE')
        self.assertLess(res.theta, 0)

class TestGEX(unittest.TestCase):
    def setUp(self):
        self.engine = DealerExposureEngine()

    def test_gex_calculation(self):
        # Mock option chain
        chain = [
            # Strike 19000: Call Gamma 0.002, OI 1000 | Put Gamma 0.002, OI 500
            {'strike': 19000, 'ce_gamma': 0.002, 'call_oi': 1000, 'pe_gamma': 0.002, 'put_oi': 500,
             'ce_delta': 0.5, 'pe_delta': -0.5, 'lot_size': 50},
        ]
        spot = 19000

        # GEX = (-1 * CallGamma * CallOI) + (1 * PutGamma * PutOI) * Lot * Spot^2 * 0.01
        # Call Contrib: -1 * 0.002 * 1000 * 50 * 19000^2 * 0.01 = -361,000,000
        # Put Contrib:   1 * 0.002 * 500  * 50 * 19000^2 * 0.01 = +180,500,000
        # Net: -180,500,000

        res = self.engine.calculate_exposures(chain, spot)
        self.assertLess(res['gex'], 0)
        self.assertAlmostEqual(res['gex'], -180500000.0, delta=100000) # Check scale

class TestOIVelocity(unittest.TestCase):
    def test_velocity_spike(self):
        engine = OIVelocityEngine("RELIANCE", 2500, "CE")

        now = time.time()
        # Add baseline
        engine.add_snapshot(OISnapshot(now - 900, 2500, "CE", 10000, 500, 20.0, 0.2))
        engine.add_snapshot(OISnapshot(now - 600, 2500, "CE", 10100, 600, 20.5, 0.2))

        # Add spike
        engine.add_snapshot(OISnapshot(now - 300, 2500, "CE", 15000, 5000, 22.0, 0.25)) # +4900 in 5 min

        vel = engine.velocity(window_minutes=15)
        # Change = 15000 - 10000 = 5000
        # Time = 10 min
        # Rate = 500/min

        self.assertGreater(vel, 400)

if __name__ == '__main__':
    unittest.main()
