from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import joblib
import bcrypt
import os
import sqlite3
from functools import wraps 

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_default_secret_key")  # Use environment variable in production

# Load the dataset (ensure the path is correct)
DATA_FILE_PATH = "output_file.csv"  # Change this to the correct file path
data = pd.read_csv(DATA_FILE_PATH)

# Dummy user data for login (replace with a database)
users = {}  # Example: {"username": hashed_password}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "info")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Home Route
@app.route("/")
@login_required
def index():
    return render_template("home.html")

# About Route
@app.route("/about")
@login_required
def about():
    return render_template("about.html")

# View Dataset Route
@app.route("/view")
@login_required
def dataset():
   conn = sqlite3.connect('transactions.db')
   cursor = conn.cursor()

    # Query the database
   cursor.execute('SELECT * FROM transactions')  # Replace 'dataset' with your table name
   data = cursor.fetchall()  # Fetch all rows
   headers = [description[0] for description in cursor.description]  # Get column names

   conn.close()
  
   return render_template('dataset.html', headers=headers, rows=data)
# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Validate credentials
        if username in users and bcrypt.checkpw(password.encode('utf-8'), users[username]):
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password. Please try again.", "danger")
    return render_template("login.html")

# Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if username in users:
            flash("Username already exists. Please choose a different one.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users[username] = hashed_password
            flash("Signup successful! You can now log in.", "success")
            return redirect(url_for("login"))
    return render_template("signup.html")

# Logout Route
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# Prediction Route
@app.route("/predict", methods=["POST", "GET"])
@login_required
def predict():
    try:
        if request.method == "POST":
            # Retrieve form data
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

            # Validate inputs
            if form_data["transaction_amount"] <= 0 or form_data["credit_limit"] <= 0 or form_data["open_to_buy"] < 0:
                flash("Transaction amount, credit limit must be positive, and open-to-buy cannot be negative.", "danger")
                return redirect(url_for("predict"))

            # Prepare data for prediction
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

            # Load preprocessing components and model
            label_encoder = joblib.load("label_encoders.pkl")
            scaler = joblib.load("scaler.pkl")
            lgbm_model = joblib.load("fraud_detection_lgbm_model.pkl")

            # Encode categorical variables
            for col in ["Transaction Type", "Currency Code", "Transaction Country", "Transaction City"]:
                new_data[col] = label_encoder[col].transform(new_data[col])

            # Align columns with training data
            new_data = new_data[scaler.feature_names_in_]

            # Scale features
            new_data_scaled = scaler.transform(new_data)

            # Predict fraud
            fraud_prediction_proba = lgbm_model.predict_proba(new_data_scaled)[0]  # Probabilities: [Not Fraud, Fraud]
            fraud_probability = fraud_prediction_proba[1]  # Probability of Fraud
            fraud_prediction = "Fraud" if fraud_probability > 0.5 else "Not Fraud"

            return render_template(
                "prediction.html",
                result=fraud_prediction,
                probability=round(fraud_probability * 100, 2),  # Convert to percentage
            )
        return render_template("prediction.html")

    except Exception as e:
        flash(f"An error occurred during prediction: {str(e)}", "danger")
        return redirect(url_for("predict"))

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
