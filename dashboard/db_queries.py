import mysql
from db_connection import get_db_connection

def fetch_user(email, password):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="pfms_db"
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def fetch_dashboard_data():
    # Get total_balance from fetch_account_data
    account_data = fetch_account_data()
    total_balance = account_data["total_balance"]

    # DB connection for budgets (you can optionally optimize by reusing connection)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT SUM(budget_amount) AS total_budget, SUM(used_amount) AS total_used FROM budgets")
    budget_data = cursor.fetchone()
    total_budget = budget_data["total_budget"] or 0
    total_used = budget_data["total_used"] or 0

    # Calculate budget used percentage safely
    budget_used = (total_used / total_budget) * 100 if total_budget > 0 else 0

    cursor.close()
    conn.close()

    return {
        "total_balance": total_balance or 0,
        "budget_used": round(budget_used, 2),
    }



def fetch_account_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM accounts")
    accounts = cursor.fetchall()

    # Calculate summary
    total_income = sum(acc["income"] for acc in accounts)
    total_expenses = sum(acc["expenses"] for acc in accounts)
    total_balance = total_income - total_expenses

    cursor.close()
    conn.close()

    return {
        "accounts": accounts,
        "total_accounts": len(accounts),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_balance": total_balance
    }

def fetch_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, date, time, type, category, account, amount 
        FROM transactions
        ORDER BY date DESC, time DESC
    """)
    transactions = cursor.fetchall()

    cursor.close()
    conn.close()
    return transactions


def fetch_budgets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, budget_amount, used_amount, 
        (budget_amount - used_amount) AS remaining
        FROM budgets
        ORDER BY name ASC
    """)
    
    budgets = cursor.fetchall()
    cursor.close()
    conn.close()
    return budgets

def add_budget(name, budget_amount, used_amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO budgets (name, budget_amount, used_amount) 
        VALUES (%s, %s, %s)
    """, (name, budget_amount, used_amount))

    conn.commit()
    cursor.close()
    conn.close()

def update_budget(id, name, budget_amount, used_amount):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE budgets 
        SET name = %s, budget_amount = %s, used_amount = %s 
        WHERE id = %s
    """, (name, budget_amount, used_amount, id))

    conn.commit()
    cursor.close()
    conn.close()

def delete_budget(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM budgets WHERE id = %s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

# Fetch Daily Transactions (Last 7 Days)
def fetch_daily_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT DATE(date) as day, 
               SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS total_income,
               SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS total_expense
        FROM transactions
        WHERE date >= CURDATE() - INTERVAL 7 DAY
        GROUP BY day
        ORDER BY day;
    """)
    
    daily_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return daily_data

# Fetch Monthly Transactions (Grouped by Month)
def fetch_monthly_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT DATE_FORMAT(date, '%Y-%m') as month, 
               SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS total_income,
               SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS total_expense
        FROM transactions
        GROUP BY month
        ORDER BY month;
    """)
    
    monthly_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return monthly_data

def insert_account(name, income, expenses):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO accounts (name, income, expenses)
        VALUES (%s, %s, %s)
    """, (name, income, expenses))

    conn.commit()
    cursor.close()
    conn.close()
