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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT SUM(amount) AS total_balance FROM transactions")
    total_balance = cursor.fetchone()["total_balance"]

    cursor.execute("SELECT SUM(used_percentage) AS budget_used FROM budgets")
    budget_used = cursor.fetchone()["budget_used"]

    cursor.execute("SELECT COUNT(*) AS debts_pending FROM debts WHERE status='pending'")
    debts_pending = cursor.fetchone()["debts_pending"]

    cursor.execute("SELECT COUNT(*) AS goals_completed FROM goals WHERE status='completed'")
    goals_completed = cursor.fetchone()["goals_completed"]

    cursor.close()
    conn.close()

    return {
        "total_balance": total_balance or 0,
        "budget_used": budget_used or 0,
        "debts_pending": debts_pending or 0,
        "goals_completed": goals_completed or 0
    }

def fetch_account_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name, income, expenses, balance FROM accounts")
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
        SELECT date, time, type, category, account, amount 
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