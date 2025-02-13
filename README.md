 **Credit Card Fraud Detection using LightGBM** project:  

```markdown
# Credit Card Fraud Detection using LightGBM

## 📌 Project Overview
This project aims to detect fraudulent credit card transactions using the **Light Gradient Boosting Machine (LightGBM)** algorithm. The system analyzes transaction patterns and identifies potentially fraudulent activities to enhance security.

## 🚀 Features
- 📊 **Data Processing & Preprocessing**
- 🔍 **Fraud Detection using LightGBM**
- 📉 **Model Evaluation with Accuracy, Precision, Recall, and F1-score**
- 🖥️ **Web Application using Flask**
- 📂 **Data Storage in a Database**

## 🛠️ Tech Stack
- **Python**
- **Flask** (for web-based deployment)
- **LightGBM** (for fraud detection)
- **Pandas & NumPy** (for data handling)
- **Matplotlib & Seaborn** (for visualization)
- **Scikit-learn** (for model evaluation)
- **SQLite / PostgreSQL** (for database storage)

## 📁 Dataset Details
The dataset contains the following fields:
| Field Name            | Description |
|----------------------|-------------|
| Index               | Unique transaction ID |
| Account Number      | Bank account identifier |
| Card Number        | Credit card number |
| Open to Buy        | Available credit limit |
| Credit Limit       | Maximum credit limit |
| Transaction Amount | Amount spent |
| Transaction Time   | Timestamp of transaction |
| Transaction Date   | Date of transaction |
| Transaction Type   | Purchase, Withdrawal, etc. |
| Currency Code      | Currency used |
| Merchant Category  | Type of merchant |
| Merchant Number    | Unique merchant identifier |
| Transaction Country | Country of transaction |
| Transaction City   | City of transaction |
| Approval Code      | Approval status of transaction |
| Fraud Label        | `0` for legitimate, `1` for fraud |

## 🏗️ Project Structure
```
📂 Credit-card-fraud-detection-using-lgbm
 ┣ 📂 static/        # CSS, JS files
 ┣ 📂 templates/     # HTML pages
 ┣ 📜 app.py        # Flask application
 ┣ 📜 model.py      # Fraud detection model
 ┣ 📜 requirements.txt # Python dependencies
 ┣ 📜 README.md      # Project documentation
```

## 🖥️ How to Run Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/lavanya9739/Credit-card-fraud-detection-using-lgbm.git
   ```
2. Navigate to the project folder:
   ```bash
   cd Credit-card-fraud-detection-using-lgbm
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask app:
   ```bash
   python app.py
   ```
5. Open `http://127.0.0.1:5000/` in your browser.


## 📜 License
This project is **open-source** and free to use.

---



