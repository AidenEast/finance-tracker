import pyodbc
import os
from dotenv import load_dotenv

# ======================================================================================================
# Configuration
# ======================================================================================================
load_dotenv()  # Load environment variables from .env file if it exists

SERVER = os.getenv('DB_SERVER')  # Update this to your actual server name if different
DATABASE = os.getenv('DB_NAME')

CONNECTION_STRING = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    'Trusted_Connection=yes;'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
)

def get_connection():
    """Return a pyodbc connection."""
    return pyodbc.connect(CONNECTION_STRING)

def fetchall_as_dict(cursor):
    """Fetch all rows from a cursor and return as a list of dictionaries."""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def fetchone_as_dict(cursor):
    """Fetch one row from a cursor and return as a dictionary."""
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))

def init_db():
    """
    Run schema.sql against the database to create tables if they don't exist.
    Safe to re-run, schema.sql should use IF NOT EXISTS checks.
    Note: The database itself must already exist in SSMS before calling this function.
    """
    with open('schema.sql', 'r') as f:
        sql = f.read()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        statements = [stmt.strip() for stmt in sql.split('\nGO') if stmt.strip()]
        for statement in statements:
            cursor.execute(statement)
        conn.commit()
    print("Database initialized successfully.")


# ======================================================================================================
# Categories
# ======================================================================================================

def get_all_categories():
    """Return a list of all categories."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        return fetchall_as_dict(cursor)
    
def add_category(name, color="#4A90D9"):
    """Add a new category."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name, color) VALUES (?, ?)", (name, color))
        conn.commit()

def delete_category(category_id):
    """Delete a category by id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()

def update_category(category_id, name=None, color=None):
    """Update a category's name and/or color."""
    if name is None and color is None:
        return  # nothing to update
    
    with get_connection() as conn:
        cursor = conn.cursor()
        if name is not None and color is not None:
            cursor.execute("UPDATE categories SET name = ?, color = ? WHERE id = ?", (name, color, category_id))
        elif name is not None:
            cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))
        elif color is not None:
            cursor.execute("UPDATE categories SET color = ? WHERE id = ?", (color, category_id))
        conn.commit()

# ======================================================================================================
# Transactions
# ======================================================================================================

def get_all_transactions(filters=None):
    """
    Return a list of all transactions, optionally filtered by criteria in the filters dict.
    Supported filters: category_id, start_date, end_date, min_amount, max_amount
    """
    query = """
        SELECT t.id, t.amount, t.type, t.description, t.date,
               c.name AS category_name, c.color AS category_color
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
    """
    conditions, params = [], []

    if filters:
        if filters.get('category_id'):
            conditions.append("t.category_id = ?")
            params.append(filters['category_id'])
        if filters.get('type'):
            conditions.append("t.type = ?")
            params.append(filters['type'])
        if filters.get('start_date'):
            conditions.append("t.date >= ?")
            params.append(filters['start_date'])
        if filters.get('end_date'):
            conditions.append("t.date <= ?")
            params.append(filters['end_date'])
        if filters.get('min_amount') is not None:
            conditions.append("t.amount >= ?")
            params.append(filters['min_amount'])
        if filters.get('max_amount') is not None:
            conditions.append("t.amount <= ?")
            params.append(filters['max_amount'])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY t.date DESC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return fetchall_as_dict(cursor)

def get_transaction_by_id(transaction_id):
    """Return a single transaction by id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM transactions
            WHERE id = ?
        """, (transaction_id,))
        return fetchone_as_dict(cursor)

def add_transaction(amount, type_, description, category_id, date):
    """Add a new transaction."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (amount, type, description, category_id, date)
            VALUES (?, ?, ?, ?, ?)
        """, (amount, type_, description, category_id, date))
        conn.commit()

def delete_transaction(transaction_id):
    """Delete a transaction by id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()

def update_transaction(transaction_id, amount=None, type_=None, description=None, category_id=None, date=None):
    """Update a transaction's details."""
    updates, params = [], []

    if amount is not None:
        updates.append("amount = ?")
        params.append(amount)
    if type_ is not None:
        updates.append("type = ?")
        params.append(type_)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if category_id is not None:
        updates.append("category_id = ?")
        params.append(category_id)
    if date is not None:
        updates.append("date = ?")
        params.append(date)

    if not updates:
        return  # nothing to update

    query = "UPDATE transactions SET " + ", ".join(updates) + " WHERE id = ?"
    params.append(transaction_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()


# ======================================================================================================
# Budgets
# ======================================================================================================

def get_all_budgets():
    """Return a list of all budgets."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.id, b.monthly_limit, c.name AS category_name, c.id AS category_id,
                   COALESCE(SUM(CASE
                       WHEN t.type = 'expense'
                        AND FORMAT(t.date, 'yyyy-MM') = FORMAT(GETDATE(), 'yyyy-MM')
                       THEN t.amount ELSE 0 END), 0) AS spent
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            LEFT JOIN transactions t ON t.category_id = c.id
            GROUP BY b.id, b.monthly_limit, c.name, c.id
            ORDER BY c.name
        """)
        return fetchall_as_dict(cursor)
    
def set_budget(category_id, monthly_limit):
    """Set or update the budget for a category."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            MERGE budgets AS target
            USING (SELECT ? AS category_id, ? AS monthly_limit) AS source
                ON target.category_id = source.category_id
            WHEN MATCHED THEN
                UPDATE SET monthly_limit = source.monthly_limit
            WHEN NOT MATCHED THEN
                INSERT (category_id, monthly_limit)
                VALUES (source.category_id, source.monthly_limit);
        """, (category_id, monthly_limit))
        conn.commit()

def delete_budget(budget_id):
    """Delete a budget by id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        conn.commit()

# ======================================================================================================
# Chart Data
# ======================================================================================================

def get_monthly_expenses_by_category():
    """Return total expenses for the current month grouped by category."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.name, c.color, SUM(t.amount) AS total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'expense'
              AND FORMAT(t.date, 'yyyy-MM') = FORMAT(GETDATE(), 'yyyy-MM')
            GROUP BY c.name, c.color
            ORDER BY total DESC
        """)
        return fetchall_as_dict(cursor)
    
def get_monthly_totals(months=6):
    """Return income vs expense totals for the last N months."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP (?)
                FORMAT(date, 'yyyy-MM') AS month,
                SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expenses
            FROM transactions
            GROUP BY FORMAT(date, 'yyyy-MM')
            ORDER BY month DESC
        """, (months,))
        return fetchall_as_dict(cursor)