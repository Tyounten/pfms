from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from db_queries import fetch_user, fetch_daily_transactions, fetch_dashboard_data, fetch_account_data, fetch_monthly_transactions, fetch_transactions, fetch_budgets, add_budget, update_budget, delete_budget
import mysql.connector
import pymysql

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

# Database connection
def connect_db():
    return pymysql.connect(host='localhost', user='root', password='root', database='pfms_db', cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Fetch user from database
        user = fetch_user(email, password)

        if user:
            session['user_id'] = user['id']  # Store user ID in session
            session['email'] = user['email']  # Store user email in session
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("signin.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered!", "danger")
        else:
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            conn.commit()
            flash("Account created successfully!", "success")
            return redirect(url_for('signin'))

        cursor.close()
        conn.close()

    return render_template("signup.html")


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    flash("You have been logged out!", "info")
    return redirect(url_for('signin'))


@app.route('/dashboard')
def dashboard():
    data = {
        "total_balance": 50000,
        "budget_used": 75,
        "debts_pending": 2,
        "monthly_income": 60000,
        "monthly_expenses": 45000,
        "last_six_months_income": [50000, 55000, 60000, 58000, 62000, 64000],
        "last_six_months_expenses": [30000, 35000, 40000, 39000, 41000, 43000],
    }
    return render_template("dashboard.html", data=data)


@app.route('/accounts')
def accounts():
    data = fetch_account_data()
    return render_template('Account.html', data=data)

# ----- Fetch All Transactions -----
def fetch_transactions():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, time, type, category, account, amount FROM transactions")
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    return transactions

# ----- Transactions Page -----
@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        trans_type = request.form['type']
        category = request.form['category']
        account = request.form['account']
        amount = float(request.form['amount'])

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, time, type, category, account, amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (date, time, trans_type, category, account, amount))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Transaction added successfully!", "success")
        return redirect(url_for('transactions'))

    transactions_data = fetch_transactions()

    # Calculate summary
    total_income = sum(row['amount'] for row in transactions_data if row['type'].lower() == 'income')
    total_expenses = sum(row['amount'] for row in transactions_data if row['type'].lower() == 'expense')
    total_balance = total_income - total_expenses

    return render_template(
        'transactions.html',
        transactions=transactions_data,
        total_income=total_income,
        total_expenses=total_expenses,
        total_balance=total_balance
    )

# ----- Delete a Transaction -----
@app.route('/delete_transaction/<int:id>', methods=['GET'])
def delete_transaction(id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Transaction deleted successfully!", "success")
    return redirect(url_for('transactions'))


@app.route('/budgets', methods=['GET', 'POST'])
def budgets():
    if request.method == 'POST':
        name = request.form['name']
        budget_amount = float(request.form['budget_amount'])
        used_amount = float(request.form['used_amount'])

        add_budget(name, budget_amount, used_amount)
        return redirect(url_for('budgets'))

    budgets_data = fetch_budgets()
    total_budget = sum(b['budget_amount'] for b in budgets_data)
    total_used = sum(b['used_amount'] for b in budgets_data)
    total_remaining = total_budget - total_used

    return render_template('Budgets.html', budgets=budgets_data, 
                           total_budget=total_budget, total_used=total_used, total_remaining=total_remaining)

def update_budget_route():
    id = request.form['edit_id']
    name = request.form['edit_name']
    budget_amount = float(request.form['edit_budget_amount'])
    used_amount = float(request.form['edit_used_amount'])

    update_budget(id, name, budget_amount, used_amount)
    flash("Budget updated successfully!", "success")  # Add flash message
    return redirect(url_for('budgets'))

@app.route('/delete_budget/<int:id>')
def delete_budget_route(id):
    delete_budget(id)
    flash("Budget deleted successfully!", "success")  # Add flash message
    return redirect(url_for('budgets'))

@app.route('/reports')
def reports():
    daily_transactions = fetch_daily_transactions()
    monthly_transactions = fetch_monthly_transactions()
    
    return render_template('Reports.html', daily_transactions=daily_transactions, monthly_transactions=monthly_transactions)


@app.route('/api/daily-transactions')
def daily_transactions():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT DATE(date) AS day,
               SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS total_income,
               SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS total_expense
        FROM transactions
        GROUP BY day
        ORDER BY day
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/monthly-transactions')
def monthly_transactions():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT DATE_FORMAT(date, '%Y-%m') AS month,
               SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS total_income,
               SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS total_expense
        FROM transactions
        GROUP BY month
        ORDER BY month
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
