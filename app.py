from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'retail_auto_parts_key'

def get_db_connection():
    conn = sqlite3.connect('auto_parts.db')
    conn.row_factory = sqlite3.Row
    return conn

LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset = "UTF-8">
    <title>Management Center</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #f3f4f6; color: #333; }
        header { background-color: #1e293b; color: white; padding: 20px; text-align: center; border-bottom: 4px solid #38b82f6; }

        /* Menu Bar / Dropdowns */
        nav { background: #334155; display: flex; justify-content: center; padding: 15px 25px; text-decoration: none; font-weight:600; border: none; background: transparent; font-size: 16px; cursor: pointer; }
        .menu-item { position: relative; display: inline-block; }
        .menu-item > a, .menu-btn { display: block; color: white; padding: 15px 25px; text-decoration: none; font-weight:600; border: none; background: transparent; font-size: 16px; cursor: pointer; }
        .menu-item:hover { background-color: #475569; }
        .dropdown { display: none; position: absolute; backgroun-color: white; min-width: 200px; box-shadow 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 0 0 4px 4px; }
        .dropdown a { color: #334155; padding: 12px 16px; text-decoration: none; display: block; font-size: 14px; }
        .dropdown a:hover { background-color: #f1f5f9; color: #2563eb; }
        .menu-item:hover .dropdown {display: block; }

        .container {max-width: 1100px; margin: 30px auto; padding: 25px; background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-low { background-color: #fee2e2; color: #991b1b; }
        .badge-ok { background-color: #dcfce7; color: #166534; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; } 
        th, td { border: 1px solid #e2e8f0; padding: 12px; text-alighn: left; } 
        th { background-color: #f8fafc; color: #475569; }
        .btn { background: #2563eb; color: white; padding: 8px 16px; text-decoration: none; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #1d4ed8; }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; }
        .flash { padding: 12px; background-color: #eff6ff; border-left: 4px solid #3b82f6; color: #1e40af; margin-bottom: 20px; border-radius: 4px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; background: #f8fafc; }
    </style>
</head>
<body>
    <header>
        <h1 style="margin:0; font-size: 28px; font-weight: 400;"> Auto Shop Operating System</h1>
    </header>
    <nav>
        <!-- CUSTOMER OPTIONS MENU -->
        <div class="menu-item">
            <button class = "menu-btn"> Customer </button>
            <div class="dropdown">
                <a href="{{ url_for('browse_catalog') }}">Browse/Search Catalog</a>
                {% if session.get('mode') == 'customer' %}
                    <a href="{{ url_for('customer_history') }}"> Purchase History</a>
                    <a href="{{ url_for('logout') }}"> Logout</a>
                {% else %}
                    <a href="{{ url_for('customer_login') }}"> Login to Account</a>
                {% endif %}
            </div>
        </div>

        <!-- STORE MANAGEMENT MENU -->
        <div class="menu-item">
            <button class ="menu-btn"> Store Mode</button>
                {% if session.get('mod') == 'store'%}
                    <a href="{{ url_for('manage_employees') }}> Manage Employees</a>
                    <a href="{{ url_for('order_management') }}> Order & Returns</a>
                    <a href="{{ url_for('report_management') }}> Reports</a>
                    <a href="{{ url_for('logout') }}> Logout</a>
                {% else %}
                    <a href="{{ url_for('store_login') }}> Employee Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class= "container">
        {% with messages = get_flashed_message() %}
            {% if messages %}
                {%for message in messages %}
                    <div class="flash"> {{ message}} </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %} {% endblock %}
    </div>
</body>
</html>
"""

#Start Route
@app.route('/')
def browse_catalog():
    search = request.args.get('searc', '')
    conn = get_db_connection()
    if search:
            query = """
                select p.*, s.store_name, i.quantity, i.reorder_level
                FROM Part p
                JOIN Inventory I on p.part_id = i.part_id
                JOIN Store s ON i.store_id = s.store_id
                WHERE p.part_name LIKE ? OR p.part_number LIKE ?
            """
            parts = conn.execute(query, (f'%{search}%', f'%{search}%')).fetchall()
    else:
            parts = conn.execute("""
                SELECT p.*, s.store_name, i.quantity, i.reorder_level
                FROM Part p
                JOIN inventory i ON p.part_id = i.part_id
                JOIN Store s ON i.store_id = s.store_id
            """).fetchall()
    conn.close()

    template = """
        {% extends "base" %}
        {% block content %}
        <h2> Auto Parts Catalog</h2>
        <form method="GET action"{{ url_for('browse_catalog") }}" style= "display:flex; gap:10px; margin-bottom 20px;">
            <input type="text" name="search" style="flex:1; padding:10px;' border-radius:4px; border:1px solid #ccc;" placeholder = "Search catalog items by name or part code" value ="{{ request.args.get('search','') }}">
            <button type="submit" class"btn">Query Inventory</button>
        </form>
        <table>
            <tr>
                <th>Part Number</th><th>Name</th><th>Condition</th><th>Price</th><th>Location</th><th>Inventory</th><th>Action</th>
            </tr>
            {% for part in parts %}
            <tr>
                <td><strong>{{ part['[part_number'] }} </strong></td>
                <td>{{ part['part_name'] }}</td>
                <td>{{ part['part_condition'] }}</td>
                <td>{{ "%%.2f"|format(part['unit_price']) }}</td>
                <td>{{ part['store_name'] }}</td>
                <td>
                    {{ part['quantity'] }}
                    {% if part['quantity'] <= part['reorder_level'] %}
                        <span class="badge badge-low">Low</span>
                    {% else %}
                        <span class="badge badge-ok'>OK</span>
                    {% endif %}
                </td>
                <td>
                    {% if session.get('mode') == 'customer and part['quantity'] > 0 %}
                        <form method="POST" action"{{ url_for('place_order') }}">
                            <input type="hidden" name="part_id" value"{{ part['part_id'] }}">
                            <input type="hidden" name="store_id" value="{{ part['store_id'] }}">
                            <input type="number" name="qty" value="1" min="1" max="{{part['quantity'] }}" style="width:50px; padding:4px;">
                            <button type="submit" class="btn">Order Web Unit</button>
                        </form>
                    {% elif session.get('mode') == 'customer' %}
                        <span style="color:gray; font-size:12px;">Out of Stock</span>
                    {% else %}
                        <small style="color:gray;">
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
        {% endblock %}
        """
    return render_template_string(template, parts=parts, base=BASE_LAYOUT)

#CUSTOMER PORTAL
@app.route('/customer/login', method=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Customer WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
             session.clear()
             session['mode'] = 'customer'
             session['customer_id'] = user['customer_id']
             session['username'] = f"{user['first_name']} {user['last_name']}"
             flash(f"Customer session initialized for user {username}")
             return redirect(url_for('browse_catalog'))
        flash("Invalid secure validation credentials.")

    template = """
    {% extends "base" %}
    {% block content %}
    <div style="max-width:400px; margin:auto; padding:20px; border:1px solid #ccc; border_radius: 6px;">
        <h3>Customer Portal Auth</h3>
        <form method="POST">
            <p><label>Username:</label><input type="text" name="username" style="width:100%; padding: 8px;" required></p>
            <p><label>Password:</label><input type="password" name="password" style="width:100%; padding:8px;" required></p>
            <button type="submit" class="btn" style="width:100%;">Authorize Session</button>
        </form>
        <p style="font-size:12px; color:gray; text-alight:center; margin-top:15px;">Demo profile: johndoe/password123</p>
    </div>
    {% endblock %}
    """
    return render_template_string(template, base=BASE_LAYOUT)

@app.route('/customer/order', methods=['POST'])
def place_order():
     if session.get('mode') != 'customer':
            return redirect(url_for('customer_login'))
            part_id = int(request.form['part_id'])
            store_id = int(request.form['store_id'])
            qty = int(request.form['qty'])
            conn = get_db_connection()
            part = conn.execute('SELECT * FROM Part WHERE part_id = ?', (part_id,)).fetchone()
            inv = conn.execute('SELECT quantity FROM Inventory WHERE store_id = ? AND part_id = ?', (store_id, part_id)).fetchone()
            if inv and inv['quantity'] >= qty:
                total = part['unit_price'] * qty
                #Need to make a metrics chain, using database
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Order_Item(order_id, part_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (session['customer_id'], store_id, total))
                order_id = cursor.lastrowid
                cursor.execute("INSERT INTO Order_Item (order_id, part_id, quantity, unit_price) VALUES (?, ?, ?, 'Paid')",
                    (order_id, part_id, qty, part['unit_price']))
                cursor.execute("INSERT INTO Payment (order_id, method, card_type, card_last4, amount, status) VALUES (?, 'Credit Card', 'Visa', '4321', ?, 'Approved')", #EXAMPLE INPUT FOR CARD, NEED TO REPLACE
                    (order_id, total))
                conn.commit()
                flash(f"Order#{order_id} generated successfully! ${total: .2f} processed via Credit Card verification.")
            else:
                flash("Stock depletion error encouterd during transaction table phase.")
                conn.close()
                return redirect(url_for('browse_catalog'))
