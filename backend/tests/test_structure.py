# backend/tests/test_structure.py

import unittest
from app.core.oi_analysis import TradeStructureIdentifier, TradeStructure

class TestTradeStructure(unittest.TestCase):
    def setUp(self):
        self.identifier = TradeStructureIdentifier()
        self.lot_size = 50
        self.atm = 19500

    def test_bull_call_spread(self):
        # Long 19500 CE, Short 19600 CE
        oi_changes = {
            (19500, 'CE'): 2000,   # Buying base
            (19600, 'CE'): -2000,  # Selling higher strike?
            # Wait, Bull Call Spread is BUY lower strike call, SELL higher strike call.
            # Selling call -> Open Interest usually INCREASES (Short Buildup).
            # So both legs should see POSITIVE OI Change if new positions are opening.
            # Buyer opens long (+OI), Seller opens short (+OI).
            # Yes, the logic in identifier says: "Both same direction change ... = spread pair"
            # If both positive OI change, it means new contracts created.

            (19500, 'CE'): 5000,
            (19600, 'CE'): 4500
        }

        # Price rising
        price_chg = 0.5

        detections = self.identifier.identify(
            symbol="NIFTY",
            oi_changes=oi_changes,
            price_change=price_chg,
            atm_strike=self.atm,
            lot_size=50
        )

        # Check if any detection is BULL_CALL_SPREAD
        found = any(d.structure == TradeStructure.BULL_CALL_SPREAD for d in detections)
        self.assertTrue(found)

    def test_naked_put_buy(self):
        oi_changes = {
            (19400, 'PE'): 8000  # Big put buying
        }
        price_chg = -0.8  # Market falling

        detections = self.identifier.identify("NIFTY", oi_changes, price_chg, self.atm, 50)
        found = any(d.structure == TradeStructure.NAKED_PUT_BUY for d in detections)
        self.assertTrue(found)

if __name__ == '__main__':
    unittest.main()
