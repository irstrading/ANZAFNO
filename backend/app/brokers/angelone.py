# backend/app/brokers/angelone.py
from SmartApi import SmartConnect
import pyotp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AngelOneAdapter:
    def __init__(self, api_key: str, client_id: str, password: str, totp_secret: str):
        self.api = SmartConnect(api_key=api_key)
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret

    def login(self) -> Dict[str, Any]:
        totp = pyotp.TOTP(self.totp_secret).now()
        data = self.api.generateSession(self.client_id, self.password, totp)
        if data['status']:
            return data['data']
        raise Exception(f"AngelOne Login Failed: {data['message']}")

    def get_option_chain(self, symbol: str, expiry: str) -> Dict[str, Any]:
        payload = {"symbol": symbol, "expirydate": expiry}
        return self.api.optionChain(payload)
