
import os
import math
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-only-secret-change-before-deployment"
)

# Demo accounts
accounts = {
    "1001": {"name": "Sriram", "balance": 50000.00},
    "1002": {"name": "Rahul", "balance": 25000.00}
}

transactions = []


@app.route("/")
def home():
    return render_template(
        "index.html",
        accounts=accounts,
        transactions=transactions
    )


@app.route("/add-account", methods=["POST"])
def add_account():
    name = request.form.get("name", "").strip()
    account_number = request.form.get("account_number", "").strip()

    try:
        deposit = float(request.form.get("deposit", "0"))
    except (ValueError, TypeError):
        flash("Please enter a valid initial deposit.")
        return redirect(url_for("home"))

    if not name or not account_number:
        flash("Customer name and account number are required.")

    elif account_number in accounts:
        flash("This account number already exists.")

    elif not math.isfinite(deposit) or deposit < 0:
        flash("Initial deposit must be a valid non-negative amount.")

    else:
        accounts[account_number] = {
            "name": name,
            "balance": deposit
        }
        flash(f"Account created successfully for {name}!")

    return redirect(url_for("home"))


@app.route("/transfer", methods=["POST"])
def transfer():
    sender = request.form.get("sender", "").strip()
    receiver = request.form.get("receiver", "").strip()

    try:
        amount = float(request.form.get("amount", "0"))
    except (ValueError, TypeError):
        flash("Please enter a valid amount.")
        return redirect(url_for("home"))

    if sender not in accounts or receiver not in accounts:
        flash("Invalid account number.")

    elif sender == receiver:
        flash("Sender and receiver must be different.")

    elif not math.isfinite(amount) or amount <= 0:
        flash("Transfer amount must be greater than zero.")

    elif accounts[sender]["balance"] < amount:
        flash("Insufficient balance.")

    else:
        accounts[sender]["balance"] -= amount
        accounts[receiver]["balance"] += amount

        transactions.insert(0, {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "status": "SUCCESS"
        })

        flash("Transfer completed successfully!")

    return redirect(url_for("home"))


@app.route("/health")
def health():
    return jsonify({
        "status": "UP",
        "application": "Banking DevSecOps",
        "version": "1.0"
    }), 200


@app.route("/api/accounts")
def get_accounts():
    return jsonify(accounts)


@app.route("/api/transactions")
def get_transactions():
    return jsonify(transactions)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
