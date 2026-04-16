"""
Database initialization script.
Run this once to set up the database tables.

Usage:
    python init_db.py
"""

import sqlite3
import os

DB_PATH = "transactions.db"
SQL_FILE = "transactions.sql"


def init_database():
    """Initialize the database with schema and seed data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Create transactions table if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            Account_Number INTEGER,
            Card_Number FLOAT,
            Open_to_Buy FLOAT,
            Credit_Limit FLOAT,
            Transaction_Amount FLOAT,
            Transaction_Time TEXT,
            Transaction_Date TEXT,
            Transaction_Type TEXT,
            Currency_Code TEXT,
            Merchant_Category_Code INTEGER,
            Merchant_Number TEXT,
            Transaction_Country TEXT,
            Transaction_City TEXT,
            Approval_Code TEXT,
            Fraud_Label TEXT
        )
        """
    )

    # Load seed data from SQL file if transactions table is empty
    count = cursor.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    if count == 0 and os.path.exists(SQL_FILE):
        print(f"Loading seed data from {SQL_FILE}...")
        with open(SQL_FILE, "r") as f:
            sql = f.read()
        cursor.executescript(sql)
        new_count = cursor.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        print(f"Loaded {new_count} transactions.")
    else:
        print(f"Transactions table already has {count} records.")

    conn.commit()
    conn.close()
    print("Database initialization complete.")


if __name__ == "__main__":
    init_database()
