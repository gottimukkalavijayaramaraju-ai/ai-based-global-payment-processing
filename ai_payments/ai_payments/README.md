# AI-Based Global Payment Processing (Base Project)

Flask API that processes payments in multiple currencies and uses a
RandomForest model to score fraud risk, then approves, flags, or declines.

## Run
    pip install -r requirements.txt
    python test_demo.py        # offline demo
    python app.py              # start API on :5000

## API
POST /api/payments  { card_number, amount, currency, card_country, merchant_country, device_id }
GET  /api/payments/<id>
GET  /api/payments

Example:
    curl -X POST localhost:5000/api/payments -H "Content-Type: application/json" \
      -d '{"card_number":"4111111111111111","amount":45,"currency":"EUR","card_country":"DE","merchant_country":"DE","device_id":"dev1"}'

## Flow
validate (Luhn, currency) -> convert to USD -> features (amount, hour, country risk,
cross-border, velocity, new device) -> fraud score -> APPROVED (<0.4) / REVIEW / DECLINED (>0.7)

## Next steps
Live FX rates, real payment gateway (Stripe/Razorpay), real training data,
auth + API keys, PCI-compliant tokenization, Postgres, dashboard UI.
