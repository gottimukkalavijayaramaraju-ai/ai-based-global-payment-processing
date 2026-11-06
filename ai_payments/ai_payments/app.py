"""AI-Based Global Payment Processing - base API (Flask + SQLite)."""
import hashlib
import sqlite3
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from currency import RATES_PER_USD, to_usd
from fraud_model import FraudModel

DB_PATH = "payments.db"
APPROVE_BELOW, DECLINE_ABOVE = 0.40, 0.70

app = Flask(__name__)
model = FraudModel()


# ---------- helpers ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY, created_at REAL, amount REAL, currency TEXT,
            amount_usd REAL, card_hash TEXT, card_last4 TEXT,
            card_country TEXT, merchant_country TEXT, device_id TEXT,
            risk_score REAL, status TEXT, reason TEXT)""")


def luhn_ok(number: str) -> bool:
    digits = [int(d) for d in number][::-1]
    total = sum(digits[0::2]) + sum(sum(divmod(d * 2, 10)) for d in digits[1::2])
    return total % 10 == 0


def validate(p):
    errs = []
    card = str(p.get("card_number", "")).replace(" ", "")
    if not (card.isdigit() and 12 <= len(card) <= 19 and luhn_ok(card)):
        errs.append("invalid card_number")
    try:
        if float(p.get("amount", 0)) <= 0:
            errs.append("amount must be > 0")
    except (TypeError, ValueError):
        errs.append("amount must be a number")
    if str(p.get("currency", "")).upper() not in RATES_PER_USD:
        errs.append(f"currency must be one of {sorted(RATES_PER_USD)}")
    for f in ("card_country", "merchant_country", "device_id"):
        if not p.get(f):
            errs.append(f"{f} is required")
    return errs, card


# ---------- routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/payments")
def create_payment():
    p = request.get_json(silent=True) or {}
    errs, card = validate(p)
    if errs:
        return jsonify(errors=errs), 400

    amount = float(p["amount"])
    currency = p["currency"].upper()
    amount_usd = to_usd(amount, currency)
    card_hash = hashlib.sha256(card.encode()).hexdigest()  # never store the PAN
    card_country = p["card_country"].upper()
    merchant_country = p["merchant_country"].upper()
    now = time.time()

    with db() as c:
        velocity = c.execute(
            "SELECT COUNT(*) FROM payments WHERE card_hash=? AND created_at>?",
            (card_hash, now - 3600)).fetchone()[0]
        known = c.execute(
            "SELECT 1 FROM payments WHERE card_hash=? AND device_id=? LIMIT 1",
            (card_hash, p["device_id"])).fetchone()

        score = model.score(
            amount_usd=amount_usd,
            hour=datetime.now(timezone.utc).hour,
            country=merchant_country,
            cross_border=card_country != merchant_country,
            txn_last_hour=velocity,
            new_device=known is None)

        if score < APPROVE_BELOW:
            status, reason = "APPROVED", "low risk"
        elif score > DECLINE_ABOVE:
            status, reason = "DECLINED", "high fraud risk"
        else:
            status, reason = "REVIEW", "medium risk - manual review"

        pid = "pay_" + uuid.uuid4().hex[:12]
        c.execute("INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (pid, now, amount, currency, amount_usd, card_hash,
                   card[-4:], card_country, merchant_country,
                   p["device_id"], round(score, 4), status, reason))

    return jsonify(id=pid, status=status, reason=reason,
                   risk_score=round(score, 4), amount=amount,
                   currency=currency, amount_usd=amount_usd), 201


@app.get("/api/payments/<pid>")
def get_payment(pid):
    row = db().execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not row:
        return jsonify(error="not found"), 404
    d = dict(row)
    d.pop("card_hash")
    return jsonify(d)


@app.get("/api/payments")
def list_payments():
    rows = db().execute(
        "SELECT id,amount,currency,amount_usd,card_last4,risk_score,status "
        "FROM payments ORDER BY created_at DESC LIMIT 50").fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
