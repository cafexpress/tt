from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('cafe_pos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item TEXT,
                price REAL,
                quantity INTEGER,
                total REAL,
                payment_method TEXT,
                order_type TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT,
                stock INTEGER,
                price REAL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_number INTEGER,
                status TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT,
                role TEXT
                )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('cafe_pos.db')
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if request.method == 'POST':
        item = request.form['item']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        total = price * quantity
        payment_method = request.form['payment_method']
        order_type = request.form['order_type']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('cafe_pos.db')
        c = conn.cursor()
        c.execute("INSERT INTO sales (date, item, price, quantity, total, payment_method, order_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (date, item, price, quantity, total, payment_method, order_type))
        conn.commit()
        conn.close()
        return redirect(url_for('sales'))
    
    conn = sqlite3.connect('cafe_pos.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sales")
    sales_data = c.fetchall()
    conn.close()
    return render_template('sales.html', sales=sales_data)

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        item = request.form['item']
        stock = int(request.form['stock'])
        price = float(request.form['price'])
        
        conn = sqlite3.connect('cafe_pos.db')
        c = conn.cursor()
        c.execute("INSERT INTO inventory (item, stock, price) VALUES (?, ?, ?)",
                  (item, stock, price))
        conn.commit()
        conn.close()
        return redirect(url_for('inventory'))
    
    conn = sqlite3.connect('cafe_pos.db')
    c = conn.cursor()
    c.execute("SELECT * FROM inventory")
    inventory_data = c.fetchall()
    conn.close()
    return render_template('inventory.html', inventory=inventory_data)

@app.route('/tables', methods=['GET'])
def tables():
    conn = sqlite3.connect('cafe_pos.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tables")
    tables_data = c.fetchall()
    conn.close()
    return render_template('tables.html', tables=tables_data)

@app.route('/api/orders', methods=['POST'])
def api_orders():
    data = request.get_json()
    item = data['item']
    quantity = int(data['quantity'])
    payment_method = data['payment_method']
    order_type = data['order_type']
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('cafe_pos.db')
    c = conn.cursor()
    c.execute("SELECT price, stock FROM inventory WHERE item = ?", (item,))
    inventory_data = c.fetchone()
    if not inventory_data:
        return jsonify({"error": "Item not found"}), 400
    price, stock = inventory_data
    if quantity > stock:
        return jsonify({"error": "Not enough stock"}), 400
    total = price * quantity
    
    c.execute("INSERT INTO sales (date, item, price, quantity, total, payment_method, order_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (date, item, price, quantity, total, payment_method, order_type))
    c.execute("UPDATE inventory SET stock = stock - ? WHERE item = ?", (quantity, item))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Order processed successfully", "total": total})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
