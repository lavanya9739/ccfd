# Credit Card Fraud Detection Platform

A full-stack web application for real-time credit card fraud detection powered by **LightGBM** machine learning. Built with Flask, featuring an interactive analytics dashboard, multi-step prediction wizard, and a modern responsive UI with dark/light theme support.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask)
![LightGBM](https://img.shields.io/badge/LightGBM-4.6-green)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## Features

### Fraud Detection
- **LightGBM ML Model** trained on 1000+ transaction records
- **8-feature analysis**: transaction type, amount, credit limit, city, country, currency, merchant code, open-to-buy
- **Risk level classification**: Low / Medium / High / Critical
- **Feature importance visualization** showing which factors influenced each prediction
- **Prediction history** tracking all past analyses per user

### Analytics Dashboard
- **6 KPI cards** with animated counters (total transactions, fraud count, fraud rate, averages)
- **5 interactive charts** (Chart.js): fraud vs legit doughnut, fraud by city, fraud by type, amount distribution, monthly trend
- **Geographic heatmap** (Leaflet.js) showing fraud hotspots across Indian cities
- **Recent fraud alerts** table

### Security
- **CSRF protection** on all forms (Flask-WTF)
- **Bcrypt password hashing** with enforcement policy (8+ chars, uppercase, lowercase, digit, special character)
- **Rate limiting** (Flask-Limiter): login 10/min, signup 5/min, API 30/min
- **Session timeout** after 30 minutes
- **Card number masking** in dataset view and CSV exports
- **Input validation** against known encoder classes

### UI/UX
- **Dark / Light theme** toggle with localStorage persistence
- **Toast notifications** replacing traditional flash messages
- **Split-screen auth pages** with password strength meter and show/hide toggle
- **Multi-step prediction wizard** (3 steps with progress indicators)
- **Auto-fill demo buttons** to try sample fraud/legit transactions
- **Animated gauge meter** displaying fraud probability
- **Sortable dataset table** with filter chips (All / Fraud / Legit)
- **CSV export** with masked card numbers
- **PDF report** via browser print
- **Tabbed About page** with timeline and threshold visualization
- **Responsive design** with mobile hamburger menu
- **Page transitions and ripple effects** on buttons

### REST API

| Endpoint | Method | Description |
|---|---|---|
| `/api/predict` | POST | JSON-based fraud prediction |
| `/api/stats` | GET | Dataset statistics |
| `/api/notifications` | GET | Recent fraud alerts |
| `/api/export` | GET | Download transactions as CSV |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask, Gunicorn |
| **ML Model** | LightGBM, scikit-learn, Pandas |
| **Database** | SQLite |
| **Frontend** | HTML5, CSS3 (custom properties), Vanilla JS |
| **Charts** | Chart.js |
| **Maps** | Leaflet.js + OpenStreetMap |
| **Security** | Flask-WTF, Flask-Limiter, Bcrypt |
| **Deployment** | Docker, Render |

---

## Project Structure

```
ccfd/
├── app.py                          # Flask application (routes, API, auth, ML)
├── init_db.py                      # Database initialization script
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container config
├── docker-compose.yml              # Docker Compose config
├── .env.example                    # Environment variables template
├── fraud_detection_lgbm_model.pkl  # Trained LightGBM model
├── label_encoders.pkl              # Label encoders for categorical features
├── scaler.pkl                      # StandardScaler for normalization
├── transactions.db                 # SQLite database
├── transactions.sql                # Schema + seed data (1000 records)
├── output_file.csv                 # Reference dataset
├── static/
│   ├── styles.css                  # Complete stylesheet (dark/light themes)
│   ├── app.js                      # Client-side interactions
│   └── *.jpg/png/webp              # Image assets
└── templates/
    ├── base.html                   # Layout (navbar, footer, toasts)
    ├── home.html                   # Landing page
    ├── login.html                  # Split-screen login
    ├── signup.html                 # Split-screen signup + strength meter
    ├── dashboard.html              # Analytics dashboard + heatmap
    ├── prediction.html             # Multi-step wizard + gauge
    ├── dataset.html                # Sortable table + filters + export
    ├── about.html                  # Tabbed content + timeline
    └── contact.html                # Split-layout contact form
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/lavanya9739/ccfd.git
cd ccfd

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python init_db.py

# Run the application
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

### Environment Variables (Optional)

Copy `.env.example` to `.env` and configure:

```bash
SECRET_KEY=your-random-secret-key
FLASK_DEBUG=0
```

---

## Docker Deployment

```bash
docker-compose up --build
```

The app will be available at **http://localhost:5000**.

---

## Deploy to Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) and sign up with GitHub
3. Create a **New Web Service** and connect this repo
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:10000`
   - **Environment Variable**: `SECRET_KEY` = any random string
5. Deploy

---

## API Usage

### Predict Fraud

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "Online Payment",
    "currency_code": "INR",
    "transaction_country": "IN",
    "transaction_city": "Mumbai",
    "transaction_amount": 9500,
    "credit_limit": 25000,
    "merchant_category_code": 5411,
    "open_to_buy": 2000
  }'
```

**Response:**
```json
{
  "prediction": "Fraud",
  "fraud_probability": 72.35,
  "risk_level": "High"
}
```

### Get Statistics

```bash
curl http://localhost:5000/api/stats
```

**Response:**
```json
{
  "total_transactions": 1000,
  "fraud_count": 53,
  "legitimate_count": 947,
  "fraud_rate_percent": 5.3
}
```

---

## How the Model Works

The platform uses **LightGBM (Light Gradient Boosting Machine)**, an ensemble learning algorithm developed by Microsoft that builds sequential decision trees to minimize prediction error.

**Pipeline:**
1. **Preprocessing** - Categorical features (transaction type, city, country, currency) are label-encoded; numerical features are standardized with `StandardScaler`
2. **Prediction** - The ensemble of decision trees outputs a fraud probability between 0 and 1
3. **Classification** - Probability > 0.5 = Fraud, otherwise Not Fraud
4. **Risk Assessment** - Low (0-40%), Medium (40-60%), High (60-80%), Critical (80-100%)

**Prediction Formula:**
```
y = SUM(m=1 to M) alpha_m * T_m(x)
```

**Loss Function (Binary Cross-Entropy):**
```
L(y, p) = -[y * log(p) + (1 - y) * log(1 - p)]
```

### Dataset Details

| Field | Description |
|---|---|
| Account Number | Bank account identifier |
| Card Number | Credit card number (masked in UI) |
| Open to Buy | Available credit remaining |
| Credit Limit | Maximum credit limit |
| Transaction Amount | Amount spent |
| Transaction Time | Timestamp of transaction |
| Transaction Date | Date of transaction |
| Transaction Type | Online Payment, Purchase, Refund, Cash Withdrawal |
| Currency Code | Currency used (INR) |
| Merchant Category Code | Type of merchant |
| Merchant Number | Unique merchant identifier |
| Transaction Country | Country of transaction |
| Transaction City | City of transaction |
| Approval Code | Approval status |
| Fraud Label | Fraud / Not Fraud |

---

## Team

| Name | USN |
|---|---|
| Aishwarya MK | 1BH21CS006 |
| Indhu V | 1BH21CS037 |
| Lavanya R | 1BH21CS056 |
| Pooja K | 1BH21CS077 |

---

## License

This project is open source and available under the [MIT License](LICENSE).
