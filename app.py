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
@app.route('/customer/history')
def customer_history():
    if session.get('mode') != 'customer':
        return redirect(url_for('customer_login'))
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT o.order_id, o.order_date, o.status, o.total_amount, p.part_name, oi.quantity
        FROM Order o
        JOIN Order_Item oi ON o.order_id = oi.order_id
        JOIN Part p ON oi.part_id = p.part_id
        WHERE o.customer_id = ? ORDER BY o.order_date DESC
    """, (session['customer_id'],)).fetchall()
    conn.close()
    template = """
        {%extends "base" %}
        {%block content %}
        <h1>Customer Order History</h1>
        {% for o in orders %}
        {% endfor %}
    Order ID
        Date/Time Timestamp Details | Quantity Ordered | Total Invoice | Fulfillment Status
        #{{ o.order_id }} | {{ o.order_date }} | {{ o.part_name }} | {{ o.quantity }} | ${{ "%.2f"|format(o['total_amount']) }} | {{ o.status }
    {% endblock %}
        """
    return render_template_string(template, orders=orders, base=BASE_LAYOUT)

#Store Operation Section
@app.route('/store/login', methods=['GET', 'POST'])
def store_login():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        conn = get_db_connection()
        emp = conn.execute('SELECT * FROM Employee WHERE username = ? AND status="Active" ', (username,)).fetchone()
        conn.close()
        if emp and check_password_hash(emp['password_hash'], password):
            session.clear()
            session['mode'] = 'store'
            session['store_id'] = emp['store_id']
            session['username'] = f"{emp['first_name']} {emp['last_name']} ({emp['role']})"
            flash("Store login successful.")
            return redirect(url_for('manage_employees'))
        else:
            flash("Invalid store credentials.")

    template = """
        {% extends "base" %}
        {% block content %}
        <h1>Store Login</h1>
        <form method="POST">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
            <button type="submit">Login</button>
        </form>
        {% endblock %}
    """
    return render_template_string(template, base=BASE_LAYOUT)


@app.route('/store/employees', methods=['GET', 'POST'])
def manage_employees():
    if session.get('mode') != 'store':
        return redirect(url_for('store_login'))

    conn = get_db_connection()
    if request.method == 'POST':
        if 'add' in request.form:
            conn.execute("""
                INSERT INTO Employee (store_id, first_name, last_name, department, role, username, password_hash, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')
                """, (
                    session.get('store_id'),
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form.get('department'),
                    request.form['role'],
                    request.form['username'],
                    generate_password_hash('welcome123')
                ))
            conn.commit()
            flash("Employee added successfully.")
        elif 'delete' in request.form:
            conn.execute(
                'UPDATE Employee SET status = "Terminated" WHERE employee_id = ?',
                (request.form['employee_id'],)
            )
            conn.commit()
            flash("Employee record marked as inactive.")

    employees = conn.execute('SELECT e.*, s.store_name FROM Employee e JOIN Store s ON e.store_id = s.store_id WHERE e.status = "Active"').fetchall()
    conn.close()

    template = """
        {% extends "base" %}
        {% block content %}
        <h1>Manage Employees</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Department</th>
                <th>Role</th>
                <th>Actions</th>
            </tr>
            {% for e in employees %}
            <tr>
                <td>{{ e.employee_id }}</td>
                <td>{{ e.first_name }}</td>
                <td>{{ e.last_name }}</td>
                <td>{{ e.department }}</td>
                <td>{{ e.role }}</td>
                <td>
                    <form method="POST">
                        <input type="hidden" name="employee_id" value="{{ e.employee_id }}">
                        <button type="submit" name="delete">Delete</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
        <h2>Add Employee</h2>
        <form method="POST">
            <label for="first_name">First Name:</label>
            <input type="text" id="first_name" name="first_name" required>
            <label for="last_name">Last Name:</label>
            <input type="text" id="last_name" name="last_name" required>
            <label for="department">Department:</label>
            <input type="text" id="department" name="department">
            <label for="role">Role:</label>
            <input type="text" id="role" name="role" required>
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
            <button type="submit" name="add">Add Employee</button>
        </form>
        {% endblock %}
    """
    return render_template_string(template, employees=employees, base=BASE_LAYOUT)

@app.route('/store/orders')
def order_management():
    if session.get{'mode'} != 'store': return redirect(url_for('store_login'))
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT o.order_id, o.order_date, o.total_amount, o.status, c.first_name || ' ' || c.last_name as customer_name, s.store_name
        FROM Orders o
        JOIN Customer c on o.customer_id = c.customer_id
        JOIN Store s on o.store_id = s.store_id
    """).fetchall()
    conn.close()
    template = """
    {% extends "base" %}
    {% block content %}
    <h1> Queue & Delivery Pipeline Log
    <table>
            <tr>
                <th>Customer ID</th>
                <th>Branch</th>
                <th>Node</th>
                <th>Date Logged</th>
                <th>Net Invoiced</th>
                <th>Fulfillment Status</th>
            </tr>
            {% for o in orders %}
            <tr>
                <td>{{ o['customer_name'] }}</td>
                <td>{{ o['store_name'] }}</td>
                <td>{{ o['order_id'] }}</td>
                <td>{{ o['order_date'] }}</td>
                <td>${{ "%.2f"|format(o['total_amount']) }}</td>
                <td>${{ o['status'] }}</td>
            </tr>
            {% endfor %}
        </table>
    {% endblock %}
    """
    return render_template_string(template, orders=orders, base=BASE_LAYOUT)
    @app.route('/store/reports')
    def store_reports():
        if session.get('mode') != 'store': return redirect(url_for('store_login'))
        conn = get_db_connection()
        low_stock = conn.execute("SELECT * FROM low_stock").fetchall()
        store_metrics = conn.execute("""
            SELECT s.store_name, count(o.order_id) as total_orders, IFNULL(SUM(o.total_amount), 0.0) as gross_revenue
            FROM Store s
            LEFT JOIN Orders o on s.store_id = o.store_id
            GROUP BY s.store_name
        """).fetchall()
        conn.close()
    template = """
    {% extends "base" %}
    {% block content %}
    <h1>Store Reports</h1>
    <h2>Low Stock Items</h2>
    <table>
        <tr>
            <th>Item ID</th>
            <th>Item Name</th>
            <th>Quantity</th>
        </tr>
        {% for item in low_stock %}
        <tr>
            <td>{{ item['item_id'] }}</td>
            <td>{{ item['item_name'] }}</td>
            <td>{{ item['quantity'] }}</td>
        </tr>
        {% endfor %}
    </table>
    <h2>Store Metrics</h2>
    <table>
        <tr>
            <th>Store Name</th>
            <th>Total Orders</th>
            <th>Gross Revenue</th>
        </tr>
        {% for metric in store_metrics %}
        <tr>
            <td>{{ metric['store_name'] }}</td>
            <td>{{ metric['total_orders'] }}</td>
            <td>${{ "%.2f"|format(metric['gross_revenue']) }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endblock %}
    """
    return render_template_string(template, low_stock=low_stock, store_metrics=store_metrics, base=BASE_LAYOUT)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('browse_catalog'))
    if __name__ == '__main__':
        app.run(debug=True, port=5000)