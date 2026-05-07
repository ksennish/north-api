from flask import Flask, request, jsonify
from sheets import get_all_rows
import json, re

app = Flask(__name__)


def to_float(value):
    try:
        return float(re.sub(r'[$,]', '', str(value)))
    except (ValueError, TypeError):
        return 0.0

def to_int(value):
    try:
        return int(re.sub(r'[$,]', '', str(value)))
    except (ValueError, TypeError):
        return 0


@app.route("/account")
def account():
    account_id = request.args.get("account_id", "").upper().strip()
    field      = request.args.get("field", None)

    if not account_id:
        return jsonify({"status": "error", "message": "account_id is required"}), 400

    rows  = get_all_rows("Accounts")
    match = next((r for r in rows if r["account_id"].upper() == account_id), None)

    if not match:
        return jsonify({"status": "not_found", "account_id": account_id}), 404

    try:
        deposit_components = json.loads(match.get("deposit_components_json", "[]"))
    except Exception:
        deposit_components = []

    try:
        recent_fees = json.loads(match.get("recent_fees_json", "[]"))
    except Exception:
        recent_fees = []

    chargeback_code   = str(match.get("last_chargeback_code", "")).strip()
    chargeback_reason = str(match.get("last_chargeback_reason", "")).strip()
    chargeback_amount = to_float(match.get("last_chargeback_amount", 0))
    chargeback = {
        "code":   chargeback_code,
        "reason": chargeback_reason,
        "amount": chargeback_amount
    } if chargeback_code else None

    funds_on_hold   = to_float(match.get("funds_on_hold", 0))
    hold_reason     = str(match.get("hold_reason", "")).strip()
    high_txn_limit  = to_float(match.get("high_txn_limit", 0))
    high_txn_amount = to_float(match.get("high_txn_amount", 0))
    hold = None
    if funds_on_hold > 0:
        hold = {
            "amount": funds_on_hold,
            "reason": hold_reason,
        }
        if high_txn_limit > 0:
            hold["high_txn_limit"]  = high_txn_limit
            hold["high_txn_amount"] = high_txn_amount
            hold["high_txn_hold"]   = True
        else:
            hold["high_txn_hold"] = False

    if field:
        field_map = {
            "deposit_components": deposit_components,
            "recent_fees":        recent_fees,
            "chargeback":         chargeback,
            "hold":               hold,
        }
        value = field_map.get(field, match.get(field))
        if value is None:
            return jsonify({"status": "error", "message": f"Field '{field}' not found"}), 404
        return jsonify({
            "status":     "ok",
            "account_id": account_id,
            "field":      field,
            "value":      value
        })

    return jsonify({
        "status": "ok",
        "account": {
            "account_id":          match["account_id"],
            "merchant_name":       match["merchant_name"],
            "balance_available":   to_float(match["balance_available"]),
            "last_deposit_date":   match["last_deposit_date"],
            "last_deposit_amount": to_float(match["last_deposit_amount"]),
            "deposit_components":  deposit_components,
            "hold":                hold,
            "recent_fees":         recent_fees,
            "bank_last4":          str(match["bank_last4"]),
            "bank_routing_last4":  str(match.get("bank_routing_last4", "")),
            "statement_url":       match.get("statement_url", ""),
            "chargeback":          chargeback,
        }
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "north-api", "version": "2.0"})


if __name__ == "__main__":
    app.run(debug=True)