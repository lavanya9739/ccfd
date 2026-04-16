import os
import re
import json
import logging
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
import joblib
import pandas as pd
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    WTF_CSRF_ENABLED=True,
)

# ---------------------------------------------------------------------------
# Security extensions
# ---------------------------------------------------------------------------
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
DATABASE = os.getenv("DATABASE_URI", "transactions.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL,
            transaction_type TEXT,
            currency_code   TEXT,
            transaction_country TEXT,
            transaction_city TEXT,
            transaction_amount REAL,
            credit_limit    REAL,
            merchant_category_code INTEGER,
            open_to_buy     REAL,
            result          TEXT,
            probability     REAL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


init_tables()

# ---------------------------------------------------------------------------
# ML model — load once at startup
# ---------------------------------------------------------------------------
try:
    LGBM_MODEL = joblib.load("fraud_detection_lgbm_model.pkl")
    LABEL_ENCODERS = joblib.load("label_encoders.pkl")
    SCALER = joblib.load("scaler.pkl")
    logger.info("ML model and preprocessing artefacts loaded successfully.")
except FileNotFoundError as exc:
    logger.error("Model file missing: %s", exc)
    LGBM_MODEL = LABEL_ENCODERS = SCALER = None

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"
)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "info")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def mask_card_number(card_num):
    s = str(int(float(card_num)))
    if len(s) > 4:
        return "*" * (len(s) - 4) + s[-4:]
    return s


def get_risk_level(probability):
    if probability >= 80:
        return "Critical"
    elif probability >= 60:
        return "High"
    elif probability >= 40:
        return "Medium"
    else:
        return "Low"


# =========================================================================
# WEB ROUTES
# =========================================================================

@app.route("/")
@login_required
def index():
    return render_template("home.html")


@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS cnt FROM transactions").fetchone()["cnt"]
    fraud = conn.execute(
        "SELECT COUNT(*) AS cnt FROM transactions WHERE Fraud_Label = 'Fraud'"
    ).fetchone()["cnt"]
    not_fraud = total - fraud

    city_rows = conn.execute(
        "SELECT Transaction_City, COUNT(*) AS cnt FROM transactions "
        "WHERE Fraud_Label = 'Fraud' GROUP BY Transaction_City ORDER BY cnt DESC"
    ).fetchall()

    type_rows = conn.execute(
        "SELECT Transaction_Type, COUNT(*) AS cnt FROM transactions "
        "WHERE Fraud_Label = 'Fraud' GROUP BY Transaction_Type ORDER BY cnt DESC"
    ).fetchall()

    month_rows = conn.execute(
        "SELECT substr(Transaction_Date, -4) || '-' || "
        "printf('%02d', CAST(substr(Transaction_Date, 1, instr(Transaction_Date, '/') - 1) AS INTEGER)) AS month, "
        "SUM(CASE WHEN Fraud_Label = 'Fraud' THEN 1 ELSE 0 END) AS fraud_count, "
        "COUNT(*) AS total_count "
        "FROM transactions GROUP BY month ORDER BY month"
    ).fetchall()

    avg_fraud = conn.execute(
        "SELECT AVG(Transaction_Amount) AS avg FROM transactions WHERE Fraud_Label = 'Fraud'"
    ).fetchone()["avg"] or 0
    avg_legit = conn.execute(
        "SELECT AVG(Transaction_Amount) AS avg FROM transactions WHERE Fraud_Label = 'Not Fraud'"
    ).fetchone()["avg"] or 0

    amount_ranges = conn.execute(
        """
        SELECT
            CASE
                WHEN Transaction_Amount < 2000 THEN '0-2K'
                WHEN Transaction_Amount < 4000 THEN '2K-4K'
                WHEN Transaction_Amount < 6000 THEN '4K-6K'
                WHEN Transaction_Amount < 8000 THEN '6K-8K'
                ELSE '8K+'
            END AS range_label,
            SUM(CASE WHEN Fraud_Label = 'Fraud' THEN 1 ELSE 0 END) AS fraud_cnt,
            SUM(CASE WHEN Fraud_Label = 'Not Fraud' THEN 1 ELSE 0 END) AS legit_cnt
        FROM transactions
        GROUP BY range_label
        ORDER BY MIN(Transaction_Amount)
        """
    ).fetchall()

    recent_frauds = conn.execute(
        "SELECT Account_Number, Transaction_City, Transaction_Amount, Transaction_Date "
        "FROM transactions WHERE Fraud_Label = 'Fraud' "
        "ORDER BY rowid DESC LIMIT 10"
    ).fetchall()

    city_coords = {
        "Chennai": [13.0827, 80.2707],
        "Hyderabad": [17.3850, 78.4867],
        "Pune": [18.5204, 73.8567],
        "Mumbai": [19.0760, 72.8777],
        "Kolkata": [22.5726, 88.3639],
        "Delhi": [28.7041, 77.1025],
        "Bangalore": [12.9716, 77.5946],
        "Ahmedabad": [23.0225, 72.5714],
    }

    city_fraud_map = []
    for r in city_rows:
        city_name = r["Transaction_City"]
        if city_name in city_coords:
            city_fraud_map.append({
                "name": city_name,
                "count": r["cnt"],
                "lat": city_coords[city_name][0],
                "lng": city_coords[city_name][1],
            })

    conn.close()

    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    return render_template(
        "dashboard.html",
        total=total,
        fraud=fraud,
        not_fraud=not_fraud,
        fraud_rate=round(fraud / total * 100, 2) if total else 0,
        city_labels=[r["Transaction_City"] for r in city_rows],
        city_counts=[r["cnt"] for r in city_rows],
        type_labels=[r["Transaction_Type"] for r in type_rows],
        type_counts=[r["cnt"] for r in type_rows],
        month_labels=[r["month"] for r in month_rows],
        month_fraud=[r["fraud_count"] for r in month_rows],
        month_total=[r["total_count"] for r in month_rows],
        avg_fraud=round(avg_fraud, 2),
        avg_legit=round(avg_legit, 2),
        amount_labels=[r["range_label"] for r in amount_ranges],
        amount_fraud=[r["fraud_cnt"] for r in amount_ranges],
        amount_legit=[r["legit_cnt"] for r in amount_ranges],
        city_fraud_map=city_fraud_map,
        recent_frauds=recent_frauds,
        greeting=greeting,
    )


@app.route("/view")
@login_required
def dataset():
    page = request.args.get("page", 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    filter_label = request.args.get("filter", "all")

    conn = get_db()
    if filter_label == "fraud":
        total = conn.execute("SELECT COUNT(*) AS cnt FROM transactions WHERE Fraud_Label='Fraud'").fetchone()["cnt"]
        rows = conn.execute("SELECT * FROM transactions WHERE Fraud_Label='Fraud' LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
    elif filter_label == "legit":
        total = conn.execute("SELECT COUNT(*) AS cnt FROM transactions WHERE Fraud_Label='Not Fraud'").fetchone()["cnt"]
        rows = conn.execute("SELECT * FROM transactions WHERE Fraud_Label='Not Fraud' LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) AS cnt FROM transactions").fetchone()["cnt"]
        rows = conn.execute("SELECT * FROM transactions LIMIT ? OFFSET ?", (per_page, offset)).fetchall()

    headers = rows[0].keys() if rows else []
    conn.close()

    masked_rows = []
    for row in rows:
        r = list(row)
        r[1] = mask_card_number(r[1])
        masked_rows.append(r)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "dataset.html",
        headers=headers,
        rows=masked_rows,
        page=page,
        total_pages=total_pages,
        total=total,
        current_filter=filter_label,
    )


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            session.permanent = True
            session["user"] = username
            logger.info("User '%s' logged in.", username)
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            logger.warning("Failed login attempt for '%s'.", username)
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif not PASSWORD_RE.match(password):
            flash(
                "Password must be at least 8 characters with uppercase, lowercase, "
                "digit, and special character (@$!%*?&#).",
                "danger",
            )
        else:
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed),
                )
                conn.commit()
                logger.info("New user registered: '%s'.", username)
                flash("Signup successful! You can now log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Username already exists. Please choose a different one.", "danger")
            finally:
                conn.close()

    return render_template("signup.html")


@app.route("/logout")
def logout():
    user = session.pop("user", None)
    if user:
        logger.info("User '%s' logged out.", user)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM predictions WHERE username = ? ORDER BY created_at DESC LIMIT 10",
        (session.get("user", ""),)
    ).fetchall()
    conn.close()

    if LGBM_MODEL is None:
        flash("ML model is not loaded. Please contact the administrator.", "danger")
        return render_template("prediction.html", history=history)

    if request.method == "POST":
        try:
            form_data = {
                "transaction_type": request.form["transaction_type"],
                "currency_code": request.form["currency_code"],
                "transaction_country": request.form["transaction_country"],
                "transaction_city": request.form["transaction_city"],
                "transaction_amount": float(request.form["transaction_amount"]),
                "credit_limit": float(request.form["credit_limit"]),
                "merchant_category_code": int(request.form["merchant_category_code"]),
                "open_to_buy": float(request.form["open_to_buy"]),
            }

            if form_data["transaction_amount"] <= 0 or form_data["credit_limit"] <= 0:
                flash("Transaction amount and credit limit must be positive.", "danger")
                return redirect(url_for("predict"))
            if form_data["open_to_buy"] < 0:
                flash("Open-to-buy cannot be negative.", "danger")
                return redirect(url_for("predict"))

            categorical_cols = {
                "Transaction Type": form_data["transaction_type"],
                "Currency Code": form_data["currency_code"],
                "Transaction Country": form_data["transaction_country"],
                "Transaction City": form_data["transaction_city"],
            }
            for col, val in categorical_cols.items():
                if val not in LABEL_ENCODERS[col].classes_:
                    flash(
                        f"Unknown value '{val}' for {col}. "
                        f"Accepted: {', '.join(LABEL_ENCODERS[col].classes_)}",
                        "danger",
                    )
                    return redirect(url_for("predict"))

            new_data = pd.DataFrame([{
                "Transaction Type": form_data["transaction_type"],
                "Currency Code": form_data["currency_code"],
                "Transaction Country": form_data["transaction_country"],
                "Transaction City": form_data["transaction_city"],
                "Transaction Amount": form_data["transaction_amount"],
                "Credit Limit": form_data["credit_limit"],
                "Merchant Category Code": form_data["merchant_category_code"],
                "Open to Buy": form_data["open_to_buy"],
            }])

            for col in ["Transaction Type", "Currency Code", "Transaction Country", "Transaction City"]:
                new_data[col] = LABEL_ENCODERS[col].transform(new_data[col])

            new_data = new_data[SCALER.feature_names_in_]
            new_data_scaled = SCALER.transform(new_data)

            proba = LGBM_MODEL.predict_proba(new_data_scaled)[0]
            fraud_probability = proba[1]
            fraud_prediction = "Fraud" if fraud_probability > 0.5 else "Not Fraud"
            probability_pct = round(fraud_probability * 100, 2)

            importances = LGBM_MODEL.feature_importances_
            feature_names = SCALER.feature_names_in_
            importance_pairs = sorted(
                zip(feature_names, importances), key=lambda x: x[1], reverse=True
            )

            conn = get_db()
            conn.execute(
                "INSERT INTO predictions (username, transaction_type, currency_code, "
                "transaction_country, transaction_city, transaction_amount, credit_limit, "
                "merchant_category_code, open_to_buy, result, probability) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session.get("user"),
                    form_data["transaction_type"],
                    form_data["currency_code"],
                    form_data["transaction_country"],
                    form_data["transaction_city"],
                    form_data["transaction_amount"],
                    form_data["credit_limit"],
                    form_data["merchant_category_code"],
                    form_data["open_to_buy"],
                    fraud_prediction,
                    probability_pct,
                ),
            )
            conn.commit()
            history = conn.execute(
                "SELECT * FROM predictions WHERE username = ? ORDER BY created_at DESC LIMIT 10",
                (session.get("user", ""),)
            ).fetchall()
            conn.close()

            logger.info(
                "Prediction by '%s': %s (%.2f%%)",
                session.get("user"),
                fraud_prediction,
                fraud_probability * 100,
            )

            return render_template(
                "prediction.html",
                result=fraud_prediction,
                probability=probability_pct,
                risk_level=get_risk_level(probability_pct),
                feature_importance=importance_pairs,
                history=history,
                form_data=form_data,
            )

        except (ValueError, KeyError) as e:
            flash(f"Invalid input: {e}", "danger")
            return redirect(url_for("predict"))

    return render_template("prediction.html", history=history)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, email, subject, message]):
            flash("All fields are required.", "danger")
        else:
            logger.info("Contact form submitted by %s (%s): %s", name, email, subject)
            flash("Thank you for your message! We will get back to you soon.", "success")
            return redirect(url_for("contact"))

    return render_template("contact.html")


# =========================================================================
# REST API ENDPOINTS
# =========================================================================

@app.route("/api/predict", methods=["POST"])
@csrf.exempt
@limiter.limit("30 per minute")
def api_predict():
    if LGBM_MODEL is None:
        return jsonify({"error": "Model not loaded"}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    required = [
        "transaction_type", "currency_code", "transaction_country",
        "transaction_city", "transaction_amount", "credit_limit",
        "merchant_category_code", "open_to_buy",
    ]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        new_data = pd.DataFrame([{
            "Transaction Type": data["transaction_type"],
            "Currency Code": data["currency_code"],
            "Transaction Country": data["transaction_country"],
            "Transaction City": data["transaction_city"],
            "Transaction Amount": float(data["transaction_amount"]),
            "Credit Limit": float(data["credit_limit"]),
            "Merchant Category Code": int(data["merchant_category_code"]),
            "Open to Buy": float(data["open_to_buy"]),
        }])

        for col in ["Transaction Type", "Currency Code", "Transaction Country", "Transaction City"]:
            new_data[col] = LABEL_ENCODERS[col].transform(new_data[col])

        new_data = new_data[SCALER.feature_names_in_]
        new_data_scaled = SCALER.transform(new_data)

        proba = LGBM_MODEL.predict_proba(new_data_scaled)[0]
        fraud_probability = float(proba[1])

        return jsonify({
            "prediction": "Fraud" if fraud_probability > 0.5 else "Not Fraud",
            "fraud_probability": round(fraud_probability * 100, 2),
            "risk_level": get_risk_level(round(fraud_probability * 100, 2)),
        })

    except Exception as e:
        logger.error("API prediction error: %s", e)
        return jsonify({"error": str(e)}), 422


@app.route("/api/stats", methods=["GET"])
@csrf.exempt
def api_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS cnt FROM transactions").fetchone()["cnt"]
    fraud = conn.execute(
        "SELECT COUNT(*) AS cnt FROM transactions WHERE Fraud_Label = 'Fraud'"
    ).fetchone()["cnt"]
    conn.close()
    return jsonify({
        "total_transactions": total,
        "fraud_count": fraud,
        "legitimate_count": total - fraud,
        "fraud_rate_percent": round(fraud / total * 100, 2) if total else 0,
    })


@app.route("/api/notifications", methods=["GET"])
@csrf.exempt
def api_notifications():
    conn = get_db()
    recent = conn.execute(
        "SELECT Account_Number, Transaction_City, Transaction_Amount, Transaction_Date "
        "FROM transactions WHERE Fraud_Label = 'Fraud' "
        "ORDER BY rowid DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return jsonify([
        {
            "account": r["Account_Number"],
            "city": r["Transaction_City"],
            "amount": round(r["Transaction_Amount"], 2),
            "date": r["Transaction_Date"],
        }
        for r in recent
    ])


@app.route("/api/export")
@login_required
def api_export():
    import io
    import csv
    from flask import Response

    filter_label = request.args.get("filter", "all")
    conn = get_db()
    if filter_label == "fraud":
        rows = conn.execute("SELECT * FROM transactions WHERE Fraud_Label='Fraud'").fetchall()
    elif filter_label == "legit":
        rows = conn.execute("SELECT * FROM transactions WHERE Fraud_Label='Not Fraud'").fetchall()
    else:
        rows = conn.execute("SELECT * FROM transactions").fetchall()
    headers = rows[0].keys() if rows else []
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        r = list(row)
        r[1] = mask_card_number(r[1])
        writer.writerow(r)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_export.csv"},
    )


# =========================================================================
# Error handlers
# =========================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", error="Page not found"), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    flash("Too many requests. Please slow down and try again.", "danger")
    return redirect(url_for("login"))


@app.errorhandler(500)
def internal_error(e):
    logger.error("Internal server error: %s", e)
    return render_template("base.html", error="Internal server error"), 500


# =========================================================================
# Run
# =========================================================================
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host="0.0.0.0", port=5000)
