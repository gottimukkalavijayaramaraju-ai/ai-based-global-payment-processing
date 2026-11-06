"""Quick demo: python test_demo.py (no server needed)."""
import os
if os.path.exists("payments.db"):
    os.remove("payments.db")
from app import app, init_db

init_db()
client = app.test_client()

cases = [
    ("Normal domestic", dict(card_number="4111111111111111", amount=45, currency="USD",
        card_country="US", merchant_country="US", device_id="dev1")),
    ("Large cross-border, new device", dict(card_number="5555555555554444", amount=450000,
        currency="INR", card_country="IN", merchant_country="BR", device_id="dev9")),
    ("Invalid card", dict(card_number="1234", amount=10, currency="EUR",
        card_country="DE", merchant_country="DE", device_id="d")),
]
for name, body in cases:
    r = client.post("/api/payments", json=body)
    print(f"{name}: {r.status_code} {r.get_json()}")
print("History:", client.get("/api/payments").get_json())
