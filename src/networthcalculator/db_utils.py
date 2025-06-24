import sqlite3
import os

#Define allowed categories
ASSET_CATEGORIES = [
        "Cash",
        "Savings",
        "Stocks",
        "Cryptocurrency",
        "Bonds",
        "Mutual Funds",
        "Real Estate",
        "Vehicles",
        "Personal Property",
        "Retirement Accounts",
        "Business Interests",
        "Mortgage",
        "Other"
    ]

LIABILITY_CATEGORIES = [
        "Credit Card Debt",
        "Student Loans",
        "Motor Loans",
        "Personal Loans",
        "Mortgage",
        "Other"
    ]

CASHFLOW_CATEGORIES = [
        "Rent Income",
        "Savings Interest",
        "Dividends",
        "Salary",
        "Business Income",
        "Other"
    ]

def create_table():
    # Ensure the data folder exists
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_folder, exist_ok=True)
    db_path = os.path.join(data_folder, 'networth.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets_liabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            description TEXT NOT NULL,
            value REAL NOT NULL
        )
    ''')

    # Create the history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets_liabilities_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_liability_id INTEGER,
            date TEXT,
            old_value REAL,
            new_value REAL,
            difference REAL,
            description TEXT NOT NULL
        )
    ''')

    # Create the goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            goal_subcategory TEXT NOT NULL,
            goal_amount REAL NOT NULL,
            progress REAL NOT NULL,
            description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    # Ensure the data folder exists
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_folder, exist_ok=True)
    db_path = os.path.join(data_folder, 'networth.db')

    conn = sqlite3.connect(db_path)
    return conn

