from flask import Flask, render_template, request, redirect, url_for, jsonify
import database as db

app = Flask(__name__)

# ======================================================================================================
# Transaction Routes
# ======================================================================================================

@app.route('/')
def index():
    transactions = db.get_all_transactions()
    return render_template('index.html', transactions=transactions)

@app.route('/transaction/add', methods=['GET', 'POST'])
def add_transaction():
    categories = db.get_all_categories()

    if request.method == 'POST':
        amount      = request.form.get('amount', '').strip()
        type_       = request.form.get('type', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id') or None
        date        = request.form.get('date', '').strip()

        if not amount or not type_ or not date:
            return render_template('add_transaction.html', categories=categories, error="Amount, Type, and Date are required.")
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError

        except ValueError:
            return render_template('add_transaction.html', categories=categories, error="Amount must be a positive number.")
        
        if type_ not in ('income', 'expense'):
            return render_template('add_transaction.html', categories=categories, error="Type must be either 'income' or 'expense'.")

        db.add_transaction(amount, type_, description, category_id, date)
        return redirect(url_for('index'))
    
    return render_template('add_transaction.html', categories=categories)

@app.route('/transaction/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    transactions = db.get_transaction_by_id(transaction_id)
    categories = db.get_all_categories()

    if request.method == 'POST':
        amount      = request.form.get('amount', '').strip()
        type_       = request.form.get('type', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id') or None
        date        = request.form.get('date', '').strip()

        if not amount or not type_ or not date:
            return render_template('edit_transaction.html', categories=categories, error="Amount, Type, and Date are required.")
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError

        except ValueError:
            return render_template('edit_transaction.html', categories=categories, error="Amount must be a positive number.")
        
        if type_ not in ('income', 'expense'):
            return render_template('edit_transaction.html', categories=categories, error="Type must be either 'income' or 'expense'.")

        db.update_transaction(transaction_id, amount, type_, description, category_id, date)
        return redirect(url_for('index'))
    
    return render_template('edit_transaction.html', transaction=transactions, categories=categories)

@app.route('/transaction/delete/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    db.delete_transaction(transaction_id)
    return redirect(url_for('index'))  

# ======================================================================================================
# Budget Routes
# ======================================================================================================

@app.route('/budgets')
def budgets():
    budgets = db.get_all_budgets()
    categories = db.get_all_categories()
    return render_template('budgets.html', budgets=budgets, categories=categories)

@app.route('/budgets/set', methods=['POST'])
def set_budget():
    category_id = request.form.get('category_id', '').strip() or None
    monthly_limit = request.form.get('monthly_limit', '').strip()

    if not category_id or not monthly_limit:
        return redirect(url_for('budgets'))
    
    try:
        monthly_limit = float(monthly_limit)
        if monthly_limit <= 0:
            raise ValueError
    
    except ValueError:
        return redirect(url_for('budgets'))

    db.set_budget(category_id, monthly_limit)
    return redirect(url_for('budgets'))

@app.route('/budgets/delete/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    db.delete_budget(budget_id)
    return redirect(url_for('budgets'))

# ======================================================================================================
# Chart Data Routes
# ======================================================================================================

@app.route('/charts/expenses_by_category')
def chart_expenses_by_category():
    data = db.get_expenses_by_category()
    return jsonify([dict(row) for row in data])

   
@app.route('/charts/monthly_totals')
def chart_monthly_totals():
    data = db.get_monthly_totals()
    return jsonify([dict(row) for row in data])

# ======================================================================================================
# Entry Point
# ======================================================================================================

if __name__ == '__main__':
    app.run(debug=True)
         