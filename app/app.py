
import os
import re
import secrets
import logging
import pymysql

from decimal import Decimal, InvalidOperation
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, session
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

logging.basicConfig(level=logging.INFO)

DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"


# DATABASE CONNECTION
def get_db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "securebank_app"),
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "securebank"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


# HOME
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("auth"))
    return redirect(url_for("dashboard"))


# AUTHENTICATION PAGE
@app.route("/auth")
def auth():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("auth.html")


# REGISTER
@app.route("/register", methods=["POST"])
def register():
    full_name = request.form.get("full_name", "").strip()
    mobile = request.form.get("mobile_number", "").strip()
    password = request.form.get("password", "")

    if not full_name or len(full_name) > 100:
        flash("Enter a valid full name.")
        return redirect(url_for("auth"))

    if not re.fullmatch(r"[0-9]{10,15}", mobile):
        flash("Enter a valid mobile number.")
        return redirect(url_for("auth"))

    if len(password) < 8:
        flash("Password must contain at least 8 characters.")
        return redirect(url_for("auth"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE mobile_number = %s",
                (mobile,)
            )

            if cursor.fetchone():
                flash("Mobile number is already registered.")
                return redirect(url_for("auth"))

            cursor.execute(
                """INSERT INTO users
                   (full_name, mobile_number, password_hash, is_verified)
                   VALUES (%s, %s, %s, FALSE)""",
                (full_name, mobile, generate_password_hash(password))
            )

            user_id = cursor.lastrowid

        connection.commit()

        otp = f"{secrets.randbelow(1000000):06d}"

        session.clear()
        session["pending_user_id"] = user_id
        session["demo_otp"] = otp

        flash("Registration successful. Verify your demo OTP.")

        if DEMO_MODE:
            flash(f"DEMO OTP: {otp}")

        return redirect(url_for("verify_otp"))

    except pymysql.err.IntegrityError:
        connection.rollback()
        flash("Mobile number is already registered.")

    except Exception:
        connection.rollback()
        app.logger.exception("Registration failed")
        flash("Registration failed. Please try again.")

    finally:
        connection.close()

    return redirect(url_for("auth"))


# OTP VERIFICATION
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_user_id" not in session:
        return redirect(url_for("auth"))

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()

        if not secrets.compare_digest(
            entered_otp, session.get("demo_otp", "")
        ):
            flash("Incorrect demo OTP.")
            return redirect(url_for("verify_otp"))

        connection = get_db()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET is_verified = TRUE WHERE id = %s",
                    (session["pending_user_id"],)
                )

            connection.commit()
            session.clear()

            flash("Verification successful. Please log in.")
            return redirect(url_for("auth"))

        except Exception:
            connection.rollback()
            app.logger.exception("OTP verification failed")
            flash("Verification failed.")

        finally:
            connection.close()

    return render_template("verify_otp.html", demo_mode=DEMO_MODE)


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    mobile = request.form.get("mobile_number", "").strip()
    password = request.form.get("password", "")

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, full_name, password_hash, is_verified
                   FROM users
                   WHERE mobile_number = %s""",
                (mobile,)
            )
            user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            flash("Invalid mobile number or password.")
            return redirect(url_for("auth"))

        if not user["is_verified"]:
            flash("Please verify your mobile number first.")
            return redirect(url_for("auth"))

        session.clear()
        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]

        return redirect(url_for("dashboard"))

    except Exception:
        app.logger.exception("Login failed")
        flash("Unable to log in. Please try again.")
        return redirect(url_for("auth"))

    finally:
        connection.close()


# CREATE DEMO BANK ACCOUNT
@app.route("/add-account", methods=["POST"])
def add_account():
    if "user_id" not in session:
        return redirect(url_for("auth"))

    account_number = request.form.get("account_number", "").strip()
    opening_balance = request.form.get("opening_balance", "0").strip()
    pin = request.form.get("pin", "").strip()

    if not re.fullmatch(r"[0-9]{8,18}", account_number):
        flash("Account number must contain 8–18 digits.")
        return redirect(url_for("dashboard"))

    if not re.fullmatch(r"[0-9]{6}", pin):
        flash("Demo PIN must contain exactly 6 digits.")
        return redirect(url_for("dashboard"))

    try:
        balance = Decimal(opening_balance)

        if (
            not balance.is_finite()
            or balance < 0
            or balance > Decimal("10000000")
            or balance.as_tuple().exponent < -2
        ):
            raise InvalidOperation

    except (InvalidOperation, ValueError):
        flash("Enter a valid opening balance.")
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT full_name, mobile_number FROM users WHERE id = %s",
                (session["user_id"],)
            )
            user = cursor.fetchone()

            if not user:
                flash("User account not found.")
                return redirect(url_for("logout"))

            cursor.execute(
                "SELECT account_number FROM accounts WHERE user_id = %s",
                (session["user_id"],)
            )

            if cursor.fetchone():
                flash("You already have a linked demo bank account.")
                return redirect(url_for("dashboard"))

            upi_id = f"{user['mobile_number']}@securebank"

            cursor.execute(
                """INSERT INTO accounts
                   (account_number, name, balance, user_id, upi_id)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    account_number,
                    user["full_name"],
                    balance,
                    session["user_id"],
                    upi_id
                )
            )

            cursor.execute(
                "UPDATE users SET pin_hash = %s WHERE id = %s",
                (generate_password_hash(pin), session["user_id"])
            )

        connection.commit()
        flash("Demo bank account created successfully!")

    except pymysql.err.IntegrityError:
        connection.rollback()
        flash("Account number or UPI ID already exists.")

    except Exception:
        connection.rollback()
        app.logger.exception("Account creation failed")
        flash("Unable to create demo account.")

    finally:
        connection.close()

    return redirect(url_for("dashboard"))


# SEND DEMO MONEY
@app.route("/send-money", methods=["POST"])
def send_money():
    if "user_id" not in session:
        return redirect(url_for("auth"))

    recipient = request.form.get("recipient", "").strip()
    pin = request.form.get("pin", "").strip()
    amount_text = request.form.get("amount", "").strip()

    if not recipient or len(recipient) > 100:
        flash("Enter a valid recipient account number, mobile number or UPI ID.")
        return redirect(url_for("dashboard"))

    if not re.fullmatch(r"[0-9]{6}", pin):
        flash("Enter your six-digit demo transaction PIN.")
        return redirect(url_for("dashboard"))

    try:
        amount = Decimal(amount_text)

        if (
            not amount.is_finite()
            or amount <= 0
            or amount > Decimal("10000000")
            or amount.as_tuple().exponent < -2
        ):
            raise InvalidOperation

    except (InvalidOperation, ValueError):
        flash("Enter a valid transfer amount.")
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:

            # Lock and retrieve sender account
            cursor.execute(
                """SELECT a.account_number, a.balance, u.pin_hash
                   FROM accounts a
                   JOIN users u ON a.user_id = u.id
                   WHERE a.user_id = %s
                   FOR UPDATE""",
                (session["user_id"],)
            )

            sender = cursor.fetchone()

            if not sender:
                raise ValueError("Create your demo bank account first.")

            if not sender["pin_hash"] or not check_password_hash(
                sender["pin_hash"], pin
            ):
                raise ValueError("Incorrect demo transaction PIN.")

            # Find recipient by account number, mobile number or UPI ID.
            # LEFT JOIN allows existing demo accounts without registered users.
            cursor.execute(
                """SELECT a.account_number, a.balance
                   FROM accounts a
                   LEFT JOIN users u ON a.user_id = u.id
                   WHERE a.account_number = %s
                      OR a.upi_id = %s
                      OR u.mobile_number = %s
                   LIMIT 1
                   FOR UPDATE""",
                (recipient, recipient, recipient)
            )

            receiver = cursor.fetchone()

            if not receiver:
                raise ValueError(
                    "Recipient not found. Enter an existing demo account "
                    "number, registered mobile number or UPI ID."
                )

            if sender["account_number"] == receiver["account_number"]:
                raise ValueError("You cannot transfer money to yourself.")

            if Decimal(str(sender["balance"])) < amount:
                raise ValueError("Insufficient demo account balance.")

            # Debit sender
            cursor.execute(
                """UPDATE accounts
                   SET balance = balance - %s
                   WHERE account_number = %s AND balance >= %s""",
                (amount, sender["account_number"], amount)
            )

            if cursor.rowcount != 1:
                raise RuntimeError("Sender balance update failed.")

            # Credit receiver
            cursor.execute(
                """UPDATE accounts
                   SET balance = balance + %s
                   WHERE account_number = %s""",
                (amount, receiver["account_number"])
            )

            if cursor.rowcount != 1:
                raise RuntimeError("Receiver balance update failed.")

            # Save transaction permanently
            cursor.execute(
                """INSERT INTO transactions
                   (sender, receiver, amount, status)
                   VALUES (%s, %s, %s, 'SUCCESS')""",
                (
                    sender["account_number"],
                    receiver["account_number"],
                    amount
                )
            )

            transaction_id = cursor.lastrowid

        # Commit debit, credit and transaction together
        connection.commit()

        flash(
            f"Demo payment successful! Transaction ID: {transaction_id}"
        )

    except ValueError as exc:
        connection.rollback()
        flash(str(exc))

    except Exception:
        connection.rollback()
        app.logger.exception("Money transfer failed")
        flash("Transfer failed. No balance changes were saved.")

    finally:
        connection.close()

    return redirect(url_for("dashboard"))


# TRANSACTION HISTORY
@app.route("/transactions")
def transaction_history():
    if "user_id" not in session:
        return redirect(url_for("auth"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT account_number
                   FROM accounts
                   WHERE user_id = %s""",
                (session["user_id"],)
            )

            account = cursor.fetchone()

            if not account:
                flash("Create your demo bank account first.")
                return redirect(url_for("dashboard"))

            account_number = account["account_number"]

            cursor.execute(
                """SELECT id, sender, receiver, amount, status, created_at
                   FROM transactions
                   WHERE sender = %s OR receiver = %s
                   ORDER BY created_at DESC, id DESC""",
                (account_number, account_number)
            )

            transactions = cursor.fetchall()

        return render_template(
            "transactions.html",
            transactions=transactions,
            account_number=account_number
        )

    except Exception:
        app.logger.exception("Transaction history failed")
        flash("Unable to load transaction history.")
        return redirect(url_for("dashboard"))

    finally:
        connection.close()


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT account_number, name, balance, upi_id
                   FROM accounts
                   WHERE user_id = %s""",
                (session["user_id"],)
            )

            account = cursor.fetchone()

        return render_template(
            "dashboard.html",
            account=account,
            full_name=session["full_name"]
        )

    except Exception:
        app.logger.exception("Dashboard loading failed")
        flash("Unable to load dashboard.")
        return redirect(url_for("auth"))

    finally:
        connection.close()


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.")
    return redirect(url_for("auth"))


# HEALTH CHECK
@app.route("/health")
def health():
    connection = None

    try:
        connection = get_db()

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return jsonify({
            "status": "UP",
            "application": "SecureBank",
            "database": "CONNECTED"
        }), 200

    except Exception:
        app.logger.exception("Database health check failed")

        return jsonify({
            "status": "DOWN",
            "database": "DISCONNECTED"
        }), 503

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
