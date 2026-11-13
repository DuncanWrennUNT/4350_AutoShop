from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import uuid
from datetime import date
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'retail_auto_parts_key'

def get_db_connection():
    conn = sqlite3.connect('auto_parts.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset = "UTF-8">
    <title>Management Center</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #f3f4f6; color: #333; }
        header { background-color: #1e293b; color: white; padding: 18px 25px; text-align: center; border-bottom: 4px solid #38b82f6; }
        header h1 { margin 0; font-size: 22px; }
        .user-status { font-size: 14px; color: #cbd5e1; }
        
        /* Menu Bar / Dropdowns */
        nav { background: #334155; display: flex; justify-content: center; flex-wrap: wrap; }
        .menu-item { position: relative; display: inline-block; }
        .menu-btn { display: block; color: white; padding: 14px 22px; text-decoration: none; font-weight:600; border: none; background: transparent; font-size: 16px; cursor: pointer; }
        .menu-item:hover { background-color: #475569; }
        .dropdown { display: none; position: absolute; backgroun-color: white; min-width: 220px; box-shadow 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 0 0 6px 6px; }
        .dropdown a { color: #1e293b; padding: 11px 16px; text-decoration: none; display: block; font-size: 14px; border-bottom: 1px solid #f1f5f9; }
        .dropdown a:hover { background-color: #eff6ff; color: #2563eb; }
        .menu-item:hover .dropdown {display: block; }

        .container {max-width: 1150px; margin: 25px auto; padding: 25px; background: white; border-radius: 8px; box-shadow: 0 2px 8px -1px rgba(0,0,0,0.08); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }
        th, td { border: 1px solid #e2e8f0; padding: 10px 12px; text-alighn: left; } 
        th { background-color: #f8fafc; color: #475569; }
        .btn { background: #2563eb; color: white; padding: 7px 14px; text-decoration: none; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; dispaly: inline-block; }
        .btn:hover { background: #1d4ed8; }
        .btn-success { background: #16a34a; }
        .btn-success:hover { background: #15803d; }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; }
        .btn-secondary { background : #64748b; }
        .badge { padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        .badge-low { background-color: #fee2e2; color: #991b1b; }
        .badge-ok { background-color: #dcfce7; color: #166534; }
        .flash { padding: 12px; background-color: #eff6ff; border-left: 4px solid #3b82f6; color: #1e40af; margin-bottom: 20px; border-radius: 4px; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { border: 1px solid #e2e8f0; padding: 18px; border-radius: 6px; background: #f8fafc; margin-bottom: 20px; }
        input, select, texturearea { padding: 7px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; }
        .form-row { margin-bottom: 12px; }
        .form-row label { display: block; font-weight: 600l margin-bottom: 4px; font-size: 13px; }
        .form-row input, .form-row select { width: 95%; }
    </style>
</head>

<body>
    <header>
        <h1> Auto Shop Operating System</h1>
        <div class = "user-status'>
            {% if session.get('mode') == 'customer %}
                Customer: <strong>{{session['username'] }}</strong> | Cart: <strong>{{ session.get('cart', [])|length }} </strong> item(s)
            {% elif session.get('mode') == 'store'%}
                Staff: <strong>{{ session['username']}}</strong> ({{ session{'role']}})
            {% else %}
                Guest Mode
            {% endif %}
        </div>
    </header>
    <nav>
        <div class="menu-item">
            <button class = "menu-btn"> Customer Mode</button>
            <div class="dropdown">
                <a href="{{ url_for('browse_catalog') }}">Browse & Search Parts</a>
                {% if session.get('mode') == 'customer' %}
                    <a href="{{ url_for('view_cart') }}">Browse & Search Parts</a>
                    <a href="{{ url_for('customer_history') }}">My Orders & Returns</a>
                    <a href="{{ url_for('customer_profile') }}">My Profiles & Vehicles</a>
                    <a href="{{ url_for('logout') }}">Logout</a>
                {% else %}
                    <a href="{{ url_for('customer_login') }}">Customer Login</a>
                    <a href="{{ url_for('customer_register') }}">Create Customer Account</a>
                {% endif %}
            </div>
        </div>

        <div class="menu-item">
            <button class ="menu-btn">Store Mode</button>
            <div class="dropdown">
                {% if session.get('mode') == 'store'%}
                    <a href="{{ url_for('store_orders') }}>Customer Orders, Deliveries & Returns</a>
                    <a href="{{ url_for('store_purchase_orders') }}>Supplier Purchase Orders</a>
                    <a href="{{ url_for('store_db_management') }}>Parts, Inventory & Store DB</a>
                    <a href="{{ url_for('store_employees') }}>Employee Management</a>
                    <a href="{{ url_for('store_reports') }}">System Reports</a>
                    <a href="{{ url_for('logout') }}">Logout</a>
                {% else %}
                    <a href="{{ url_for('store_login') }}>Employee Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class= "container">
        {% with messages = get_flashed_message() %}
            {% if messages %}
                {%for message in messages %}
                    <div class="flash"> {{ message }} </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

#Start Route
@app.route('/')
def browse_catalog():
    search = request.args.get('search', '').strip()
    store_filter = request.args.get('store_id', '')
    conn = get_db_connection()
    stores = conn.execute("SELECT * FROM Store").fetchall()
    
    sql = """
        SELECT p.*, s.store_id, s.store_name, i.quantity, i.reorder_level
        FROM Part p
        JOIN Inventory i ON p.part_id = i.part_id
        JOIN Store s ON i.store_id = s.store_id
        WHERE 1=1
    """
    params = []
    
    if search:
        sql += " AND (p.part_name LIKE ? OR p.part_number LIKE ? OR p.category LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    if store_filter:
        sql += " AND s.store_id = ?"
        params.append(store_filter)
    parts = conn.execute (sql, params).fetchall()
    conn.close()
    
    template = """
        {% extends "base" %}
        {% block content %}
        <h2> Auto Parts Catalog</h2>
        <form method="GET" style= "display:flex; gap:10px; margin-bottom 15px;">
            <input type="text" name="search" style="flex:2;" placeholder = "Search catalog items by name or part code" value ="{{ search }}">
            <select name="store_id" style="flex:1;">
                <option value="">All Store Branches</option>
                {% for s in stores %}
                    <option value="{{ s['store_id'] }}" {% if store_filter == s['store_id']|string %}selected{%endif %>{{ s['store_name'] }}</option>
                {% endfor %}
            </select>
            <button type="submit" class"btn">Search</button>
        </form>
        
        <table>
            <tr>
                <th>Part #</th><th>Part Name</th><th>Category</th><th>Condition</th><th>Price</th><th>Location</th><th>Inventory</th><th>Action</th>
            </tr>
            {% for p in parts %}
            <tr>
                <td><strong>{{ p['[part_number'] }} </strong></td>
                <td><a href="{{ url_for('part_detail', part_id=['part_id']) }}">{{ p['part_name'] }}</a></td>
                <td>{{ p['category'] }}</td>
                <td>{{ p['part_condition'] }}</td>
                <td>{{ "%%.2f"|format(p['unit_price']) }}</td>
                <td>{{ p['store_name'] }}</td>
                <td>
                    {{ pt['quantity'] }}
                    {% if p['quantity'] == 0 %}
                        <span class="badge badge-danger">Out of Stock</span>
                    {% elif p['quantity'] <= p['reorder_level'] %}
                        <span class="badge badge-low">Low Stock</span>
                    {% else %}
                        <span class="badge badge-ok'>In Stock</span>
                    {% endif %}
                </td>
                <td>
                    <a href="{{ url_for('part_detail', part_id=p['part_id']) }}" class="btn btn-secondary"> Details</a>
                    {% if session.get('mode') == 'customer and part['quantity'] > 0 %}
                        <form method="POST" action"{{ url_for('add_to_cart') }}" style="display:inline;">
                            <input type="hidden" name="part_id" value"{{ p['part_id'] }}">
                            <input type="hidden" name="store_id" value="{{ p['store_id'] }}">
                            <input type="number" name="qty" value="1" min="1" max="{{part['quantity'] }}" style="width:45px;">
                            <button type="submit" class="btn btn-success">Add to Cart</button>
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
    store_filter = store_filter, base=BASE_LAYOUT)

@app.route('/part/<int:part_id>')
def part_detail(part_id):
    conn = get_db_connection()
    part = conn.execute("""
        SELECT p.*, sup.supplier_name
        FROM Part p 
        LEFT JOIN Supplier sup ON p.supplier_id = sup.supplier_id
        WHERE p.part_id = ?
    """, (part_id,)).fetchone()
    Stock = conn.execute("""
        SELECT s.store_id, s.store_name, s.city, s.state, s.phone, i.quantity
        FROM Inventory i JOIN Store s on i.store_id = s.store_id
        WHERE i.part_id = ?
    """, (part_id,)).fetchall()
    conn.close()
    template = """
    {% extends "base" %}
    {% block content %}
    <a href="{{ url_for('browse_catalog') }}">&larr; Back to Catalog</a>
    
    <h2>{{ part['part_name']}} ){{ part['part_number'] }})</h2>
    <p>Category: {{ part['category'] }} | Condition {{ part['part_condition'] }}</p>
    <p>Unit Price: <strong>${{ "%.2f"|format(part['unit_price']) }}</strong></p>
    <Description: {{part['description'] }}</p>
    <h3>Store Branch Availability</h3>
    <table>
        <tr><th>Branch</th><th>Location></th><th>Phone</th><th>Quantity</th><th>Order</th></tr>
        {% for s in stock %}
        <tr>
            <td>{{ s['store_name'] }}</td>
            <td>{{s['city"] }}, {{s['state'] }}</td>
            <td>{{ s['phone'] }}</td>
            <td>{{ s['quantity'] }}</td>
            <td>
                {% if session.get('mode') == 'customer' and s['quantity'] > 0 %}
                    <form method="POST" action="{{ url_for('add_to_cart') }}">
                        <input type="hidden" name="part_id" value"{{ part['part_id'] }}">
                            <input type="hidden" name="store_id" value="{{ s['store_id'] }}">
                            <input type="number" name="qty" value="1" min="1" max="{{s['quantity'] }}" style="width:55px;">
                            <button type="submit" class="btn btn-success">Add to Cart</button>
                        </form>
                    {% elif session.get('mode') != 'customer' %}
                        <a href="{{ url_for('customer_login') }}">Log in to order</a>
                    {% else %}
                        <span class='badge badge-dange">Out of Stock</span>
                    {% elseif %}
                </td>
            </tr>
            {% endfor %}
        </table>
        {% endblock %}
        """
        return render_template_string(template, part=part, stock=stock, base=BASE_LAYOUT)
        
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
        low_stock = conn.execute("SELECT * FROM v_low_stock").fetchall()
        daily = conn.execute("SELECT * FROM v_daily_sales").fetchall()
        weekly = conn.execute("SELECT * FROM v_weekly_sales").fetchall()
        monthly = conn.execute("SELECT * FROM v_monthly_sales").fetchall()
        emp_status = conn.execute("SELECT * FROM v_employee_status").fetchall()
        conn.close()
        template = """
        {% extends "base" %}
        {% block content %}
        <h3>1. Low Stock Reorder Alert</h2>
        <table>
            <tr>
                <th>Store</th>
                <th>Part Name</th>
                <th>Part #</th>
                <th>Quantity</th>
                <th>Reorder Level</th>
            </tr>
            {% for item in low_stock %}
            <tr>
                <td>{{ item['store_name'] }}</td>
                <td>{{ item['part_number'] }}</td>
                <td>{{ item['part_name'] }}</td>
                <td>{{ item['quantity'] }}</td>
                <td>{{ item['reorder_level'] }}</td>
            </tr>
            {% endfor %}
        </table>
        <h3>2.Daily Sales (v_daily_sales)</h3>
        <table>
            <tr>
                <th>Store</th>
                <th>Date</th>
                <th>Orders</th>
                <th>Revenue</th>
            </tr>
            {% for r in monthly %}
            <tr>
                <td>{{ r['store_name'] }}</td>
                <td>{{ r['period'] }}</td>
                <td>{{ r['order_count'] }}</td>
                <td>{{ "%.2f"|format(r['revenue']) }}</td>
            </tr>
            {% endfor %}
        <h3>3. Weekly Sales (v_weekly_sales)</h3>
        <table>
            <tr>
                <th>Store</th>
                <th>Week</th>
                <th>Orders</th>
                <th>Revenue</th>
            </tr>
            {% for r in monthly %}
            <tr>
                <td>{{ r['store_name'] }}</td>
                <td>{{ r['period'] }}</td>
                <td>{{ r['order_count'] }}</td>
                <td>{{ "%.2f"|format(r['revenue']) }}</td>
            </tr>
            {% endfor %}
        <h3>4. Monthly Sales (v_monthly_sales)</h3>
        <table>
            <tr>
                <th>Store</th>
                <th>Month</th>
                <th>Orders</th>
                <th>Revenue</th>
            </tr>
            {% for r in monthly %}
            <tr>
                <td>{{ r['store_name'] }}</td>
                <td>{{ r['period'] }}</td>
                <td>{{ r['order_count'] }}</td>
                <td>{{ "%.2f"|format(r['revenue']) }}</td>
            </tr>
            {% endfor %}
        </table>
        <h3>5. Employee Status Report (v_employee_status)</h3>
        <table>
            <tr>
                <th>ID</th>
                <th>Employee</th>
                <th>Store</th>
                <th>Department</th>
                <th>Role</th>
                <th>Manager</th>
                <th>Status</th>
            </tr>
            {% for e in emp_status %}
            <tr>
                <td>#{{ e['employee_id'] }}</td>
                <td>{{ e['employee_name'] }}</td>
                <td>{{ e['store_name'] }}</td>
                <td>{{ e['department'] }}</td>
                <td>{{ e['role'] }}</td>
                <td>{{ e['manager_name'] }}</td>
                <td>{{ e['status'] }}</td>
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