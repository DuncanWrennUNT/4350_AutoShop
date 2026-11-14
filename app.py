from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from jinja2 import dictloader
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

app.jinja_loader = dictloader.DictLoader({'base': LAYOUT})

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
    return render_template_string(template, parts=parts,stores=stores, search=search, store_filter=store_filter)

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
    return render_template_string(template, part=part)

@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    conn = get_db_connection()
    stores = conn.execute("SELECT * FROM Store").fetchall()
    if request.method == 'POST':
        try:
            conn.execute("""INSERT INTO Customer (preferred_store_id, first_name, last_name, email, phone, street, city, state, zip, username, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form['preferred_store_id'],
                request.form['first_name'],
                request.form['last_name'],
                request.form['email'],
                request.form['phone'],
                request.form['street'],
                request.form['city'],
                request.form['state'],
                request.form['zip'],
                request.form['username'],
                generate_password_hash(request.form['password'])
            ))
            cust_id = conn.lastrowid
            if request.form.get('make') and request.form.get('model'):
                conn.execute("INSERT INTO Customer_Vehicle (customer_id, make, model, year) VALUES (?, ?, ?, ?)", 
                             (cust_id, request.form['make'], request.form['model'], request.form['year']))
            conn.commit()
            flash("Customer account created successfully. Please log in.")
            return redirect(url_for('customer_login'))
        except sqlite3.IntegrityError:
            flash("Username or email already exists. Please choose a different username or email.")
        conn.close()
        template = """
        {% extends "base" %}
        {% block content %}
        <h2>Customer Account Registration</h2>
        <form method="POST">
            <div class="grid-2">
                <div class="card">
                    <h3>Personal Information</h3>
                    <div class="form-row"><label>First Name</label><input type="text" name="first_name" required></div>
                    <div class="form-row"><label>Last Name</label><input type="text" name="last_name" required></div>
                    <div class="form-row"><label>Email</label><input type="email" name="email" required></div>
                    <div class="form-row"><label>Phone</label><input type="text" name="phone"></div>
                    <div class="form-row"><label>Username</label><input type="text" name="username" required></div>
                    <div class="form-row"><label>Password</label><input type="password" name="password" required></div>
                </div>
                <div class="card">
                    <h3>Address, Store & Vehicle</h3>
                    <div class="form-row"><label>Street Address</label><input type="text" name="address" required></div>
                    <div class="form-row"><label>City</label><input type="text" name="city" required></div>
                    <div class="form-row"><label>State</label><input type="text" name="state" required></div>
                    <div class="form-row"><label>ZIP Code</label><input type="text" name="zip" required></div>
                    <div class="form-row"><label>Preferred Store</label><select name="preferred_store_id">{% for s in stores %}<option value="{{ s['store_id'] }}">{{ s['store_name'] }}</option>{% endfor %}</select></div>
                    <h4>Vehicle Information (Optional)</h4>
                    <div class="form-row"><label>Make</label><input type="text" name="make"></div>
                    <div class="form-row"><label>Model</label><input type="text" name="model"></div>
                    <div class="form-row"><label>Year</label><input type="number" name="year" min="1900" max="{{ current_year }}"></div>
                </div>
            </div>
            <button type="submit" class="btn btn-success">Create Account</button>
        </form>
        {% endblock %}
        """
        return render_template_string(template, stores=stores, current_year=date.today().year)


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
             session['cart'] = []
             flash(f"Customer session initialized for user {username}")
             return redirect(url_for('browse_catalog'))
        flash("Invalid secure validation credentials.")

    template = """
    {% extends "base" %}
    {% block content %}
    <div style="max-width:400px; margin:auto; padding:20px; border:1px solid #ccc; border_radius: 6px;">
        <h3>Customer Portal Auth</h3>
        <form method="POST">
            <div class="grid-2">
                <div class="card">
                    <h3>Personal & Account Info</h3>
                    <div class="form-row"><label>Username</label><input type="text" name="username" required></div>
                    <div class="form-row"><label>Password</label><input type="password" name="password" required></div>
                    <div class="form-row"><label>First Name</label><input type="text" name="first_name"></div>
                    <div class="form-row"><label>Last Name</label><input type="text" name="last_name"></div>
                    <div class="form-row"><label>Email</label><input type="text" name="email"></div>
                    <div class="form-row"><label>Phone Number</label><input type="text" name="phone"></div>
                </div>
                <div class="card">
                    <h3>Address & Vehicle Info</h3>
                    <div class="form-row"><label>Street Address</label><input type="text" name="street"></div>
                    <div class="form-row"><label>City</label><input type="text" name="city"></div>
                    <div class="form-row"><label>State</label><input type="text" name="state"></div>
                    <div class="form-row"><label>ZIP Code</label><input type="text" name="zip"></div>
                    <div class="form-row"><label>Preferred Store</label><select name="preferred_store_id" required> {% for s in stores %} <option value="{{ s.store_id }}">{{ s.store_name }}</option> {% endfor %} </select></div>
                    <h4>Vehicle Information (Optional)</h4>
                    <div class="form-row"><label>Vehicle Make</label><input type="text" name="make"></div>
                    <div class="form-row"><label>Vehicle Model</label><input type="text" name="model"></div>
                    <div class="form-row"><label>Vehicle Year</label><input type="number" name="year" min="1900" max="{{ current_year }}"></div>
                </div>
            </div>
            <button type="submit" class="btn btn-success">Register Account</button>
        </form>
    </div>
    {% endblock %}
    """
    return render_template_string(template)

@app.route('/customer/profile')
def customer_profile():
    if session.get('mode') != 'customer':
        return redirect(url_for('customer_login'))
    conn = get_db_connection()
    if request.method == 'POST':
        if 'update_profile' in request.form:
            conn.execute("""
                UPDATE Customer SET first_name = ?, last_name = ?, email = ?, phone = ?, street = ?, city = ?, state = ?, zip = ?, preferred_store_id = ?
                WHERE customer_id = ?
            """, (
                request.form['first_name'],
                request.form['last_name'],
                request.form['email'],
                request.form['phone'],
                request.form['street'],
                request.form['city'],
                request.form['state'],
                request.form['zip'],
                request.form['preferred_store_id'],
                session['customer_id']
            ))
            conn.commit()
            flash("Profile updated successfully.")
        elif 'add_vehicle' in request.form:
            conn.execute("""
                INSERT INTO Customer_Vehicle (customer_id, make, model, year)
                VALUES (?, ?, ?, ?)
            """, (
                session['customer_id'],
                request.form['make'],
                request.form['model'],
                request.form['year']
            ))
            conn.commit()
            flash("Vehicle added successfully.")
    customer = conn.execute("SELECT * FROM Customer WHERE customer_id = ?", (session['customer_id'],)).fetchone()
    vehicles = conn.execute("SELECT * FROM Customer_Vehicle WHERE customer_id = ?", (session['customer_id'],)).fetchall()
    stores = conn.execute("SELECT * FROM Store").fetchall()
    conn.close()
    template = """
    {% extends "base" %}
    {% block content %}
    <h2>Customer Profile</h2>
    <div class="grid-2">
        <div class="card">
            <h3>Contact & Billing Information</h3>
            <p>Name: {{ customer['first_name'] }} {{ customer['last_name'] }} ({{ customer['email'] }})</p>
            <form method="POST">
                <div class="form-row"><label>Phone</label><input type="text" name="phone" value="{{ customer['phone'] }}"></div>
                <div class="form-row"><label>Street</label><input type="text" name="street" value="{{ customer['street'] }}"></div>
                <div class="form-row"><label>City</label><input type="text" name="city" value="{{ customer['city'] }}"></div>
                <div class="form-row"><label>State</label><input type="text" name="state" value="{{ customer['state'] }}"></div>
                <div class="form-row"><label>ZIP</label><input type="text" name="zip" value="{{ customer['zip'] }}"></div>
                <div class="form-row"><label>Preferred Store</label><select name="preferred_store_id">{% for s in stores %}<option value="{{ s['store_id'] }}" {% if customer['preferred_store_id'] == s['store_id'] %}selected{% endif %}>{{ s['store_name'] }}</option>{% endfor %}</select></div>
                <button type="submit" name="update_profile" class="btn btn-success">Update Profile</button>
            </form>
        </div>
        <div class="card">
            <h3>My Vehicles</h3>
            {% if vehicles %}
                <ul>
                    {% for v in vehicles %}
                        <li>{{ v['year'] }} {{ v['make'] }} {{ v['model'] }}</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p>No vehicles registered.</p>
            {% endif %}
            <h4>Add a New Vehicle</h4>
            <form method="POST">
                <div class="form-row"><label>Make</label><input type="text" name="make" required></div>
                <div class="form-row"><label>Model</label><input type="text" name="model" required></div>
                <div class="form-row"><label>Year</label><input type="number" name="year" min="1900" max="{{ current_year }}" required></div>
                <button type="submit" name="add_vehicle" class="btn btn-success">Add Vehicle</button>
            </form>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(template, customer=customer, vehicles=vehicles, stores=stores, current_year=date.today().year)

@app.route('/customer/cart/add', methods=['POST'])
def add_to_cart():
    if session.get('mode') != 'customer':
        return redirect(url_for('customer_login'))
    part_id, store_id, qty, cart = request.form['part_id'], request.form['store_id'], int(request.form['qty']), session.get('cart', [])
    if cart and cart[0]['store_id'] != store_id:
        flash("You can only add items from one store at a time. Please clear your cart to add items from a different store.")
        return redirect(url_for('view_cart'))
    for item in cart:
        if item['part_id'] == part_id and item['store_id'] == store_id:
            item['qty'] += qty
            break
    else:
        cart.append({'part_id': part_id, 'store_id': store_id, 'qty': qty})
    session['cart'] = cart
    flash(f"Added {qty} item(s) to your shopping cart.")
    return redirect(url_for('browse_catalog'))

@app.route('/customer/cart', methods=['GET', 'POST'])
def view_cart():
    if session.get('mode') != 'customer':
        return redirect(url_for('customer_login'))
    conn = get_db_connection()
    cart = session.get('cart', [])
    cart_details = []
    total_amount = 0.0
    for item in cart:
        part = conn.execute("""
            SELECT p.part_id, p.part_number, p.part_name, p.unit_price, s.store_name, i.quantity AS stock
            FROM Part p
            JOIN Inventory i ON p.part_id = i.part_id
            JOIN Store s ON i.store_id = s.store_id
            WHERE p.part_id = ? AND s.store_id = ?
        """, (item['part_id'], item['store_id'])).fetchone()
        if part:
            item_total = part['unit_price'] * item['qty']
            total_amount += item_total
            cart_details.append({
                'part_id': part['part_id'],
                'part_number': part['part_number'],
                'part_name': part['part_name'],
                'unit_price': part['unit_price'],
                'store_name': part['store_name'],
                'quantity': item['qty'],
                'item_total': item_total,
                'available_quantity': part['quantity']
            })
    customer = conn.execute("SELECT * FROM Customer WHERE customer_id = ?", (session['customer_id'],)).fetchone()
    conn.close()
    template = """
        {% extends "base" %}
        {% block content %}
        <h2>Shopping Cart</h2>
        {% if not cart_details %}
        <p>Your shopping cart is empty.</p>
        {% else %}
        <table>
            <tr><th>Part Name</th><th>Store</th><th>Unit Price</th><th>Quantity</th><th>Total</th></tr>
            {% for item in cart_details %}
            <tr>
                <td>{{ item['part_name'] }}</td>
                <td>{{ item['store_name'] }}</td>
                <td>${{ "%.2f"|format(item['unit_price']) }}</td>
                <td>{{ item['quantity'] }} (Available: {{ item['available_quantity'] }})</td>
                <td>${{ "%.2f"|format(item['item_total']) }}</td>
            </tr>
            {% endfor %}
            <tr><td colspan="4" style="text-align:right;"><strong>Total Amount:</strong></td><td>${{ "%.2f"|format(total_amount) }}</td></tr>
        </table>
        <form method="POST" action="{{ url_for('checkout') }}">
            <button type="submit" class="btn btn-primary">Proceed to Checkout</button>
        </form>
    {% endif %}
{% endblock %}
    """
    return render_template_string(template, cart_details=cart_details, total_amount=total_amount, customer=customer)

@app.route('/customer/checkout', methods=['POST'])
def checkout():
    if session.get('mode') != 'customer':
        return redirect(url_for('customer_login'))
    cart = session.get('cart', [])
    if not cart:
        flash("Your shopping cart is empty.")
        return redirect(url_for('view_cart'))
    conn = get_db_connection()
    cur = conn.cursor()
    store_id = cart[0]['store_id']
    total_amount = 0.0
    verified_items = []
    for item in cart:
        part = cur.execute("SELECT p.unit_price, p.part_name FROM Part WHERE part_id = ?", (item['part_id'],)).fetchone()
        inv = cur.execute("SELECT quantity FROM Inventory WHERE part_id = ? AND store_id = ?", (item['part_id'], item['store_id'])).fetchone()
        if not part or inv['quantity'] < item['qty']:
            flash(f"Insufficient stock for part ID {item['part_id']} at store ID {item['store_id']}.")
            total_amount += part['unit_price'] * item['qty']
            verified_items.append((item['part_id'], item['quantity'], part['unit_price']))
        cur.execute("INSERT INTO ORDERS(customer_id, store_id, status, total_amount) VALUES (?, ?, 'Paid', ?)", (session['customer_id'], store_id, total_amount))
        order_id = cur.lastrowid
        for pid, qty, price in verified_items:
            cur.execute("INSERT INTO Order_Item(order_id, part_id, quantity, unit_price) VALUES (?, ?, ?, ?)", (order_id, pid, qty, price))
            cur.execute("UPDATE Inventory SET quantity = quantity - ? WHERE part_id = ? AND store_id = ?", (qty, pid, store_id))
            card_num = request.form['card_number'].strip()
            last4 = card_num[-4:] if len(card_num) >= 4 else '0000'
            cur.execute("""INSERT INTO Payment(order_id, payment_method, card_type, card_last4, billing_address, amount, status) VALUES (?, 'Credit Card', ?, ?, ?, ?)", (order_id, request.form['method'], request.form['card_type'], last4, request.form['billing_address'], total_amount, 'Approved')""")
            tracking = f"TRK-{uuid.uuid4().hex[:8].upper()}"
            cur.execute("INSERT INTO Delivery(order_id, tracking_number, status) VALUES (?, ?, 'Processing')", (order_id, tracking))
            conn.commit()
            conn.close()
            session['cart'] = []
            flash(f"Order placed successfully! Your order ID is {order_id}. Tracking number: {tracking}")
            return redirect(url_for('customer_history'))

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
    return render_template_string(template, orders=orders)

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
    return render_template_string(template)
    
@app.route('/store/orders', methods=['GET', 'POST'])
def store_orders():
    if session.get('mode') != 'store': return redirect(url_for('store_login'))
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_delivery':
            order_id = request.form['order_id']
            new_status = request.form['delivery_status']
            tracking = request.form['tracking_number']
            ship_dt = date.today().isoformat() if new_status in ('Shipped', 'Delivered') else None
            deliv_dt = date.today().isoformat() if new_status == 'Delivered' else None
            conn.execute("""
                UPDATE Delivery SET status=?, tracking_number=?, employee_id=?,
                ship_date=COALESCE(ship_date, ?), delivery_date=COALESCE(?, delivery_date)
                WHERE order_id=?
            """, (new_status, tracking, session['employee_id'], ship_dt, deliv_dt, order_id))
            if new_status == 'Cancelled':
                conn.execute("UPDATE Orders SET status='Cancelled' WHERE order_id=?", (order_id,))
            elif new_status in ('Shipped', 'Delivered'):
                conn.execute("UPDATE Orders SET status=? WHERE order_id=?", (new_status, order_id))
            conn.commit()
            flash(f"Delivery & order status updated for Order #{order_id}.")
        elif action == 'process_return':
            order_id = int(request.form['order_id'])
            part_id = int(request.form['part_id'])
            qty = int(request.form['quantity'])
            reason = request.form['reason']
            oi = conn.execute("SELECT unit_price, quantity FROM Order_Item WHERE order_id=? AND part_id=?", (order_id, part_id)).fetchone()
            ord_row = conn.execute("SELECT store_id FROM Orders WHERE order_id=?", (order_id,)).fetchone()
            if oi and qty <= oi['quantity']:
                refund = oi['unit_price'] * qty
                conn.execute("""
                    INSERT INTO Return_Item (order_id, part_id, employee_id, quantity, reason, refund_amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, part_id, session['employee_id'], qty, reason, refund))
                conn.execute("UPDATE Inventory SET quantity = quantity + ? WHERE store_id=? AND part_id=?",
                             (qty, ord_row['store_id'], part_id))
                conn.execute("UPDATE Orders SET status='Returned' WHERE order_id=?", (order_id,))
                conn.commit()
                flash(f"Return processed (${refund:.2f} refunded) and inventory restocked.")
            else:
                flash("Invalid return quantity.")
    orders = conn.execute("""
        SELECT o.*, c.first_name || ' ' || c.last_name AS customer_name, s.store_name,
               d.tracking_number, d.ship_date, d.delivery_date, d.status AS delivery_status, pay.method AS payment_method
        FROM Orders o
        JOIN Customer c ON o.customer_id = c.customer_id
        JOIN Store s ON o.store_id = s.store_id
        LEFT JOIN Delivery d ON o.order_id = d.order_id
        LEFT JOIN Payment pay ON o.order_id = pay.order_id
        ORDER BY o.order_id DESC
    """).fetchall()
    order_items = conn.execute("""
        SELECT oi.order_id, oi.part_id, oi.quantity, p.part_number, p.part_name
        FROM Order_Item oi JOIN Part p ON oi.part_id = p.part_id
    """).fetchall()
    conn.close()
    template = """
    {% extends "base" %}
    {% block content %}
    <h2>Customer Order, Delivery & Return Management</h2>
    <table>
        <tr><th>Order #</th><th>Customer</th><th>Branch</th><th>Order Date</th><th>Payment</th><th>Total</th><th>Delivery & Tracking</th><th>Update Status</th></tr>
        {% for o in orders %}
        <tr>
            <td>#{{ o['order_id'] }}<br><span class="badge badge-warn">{{ o['status'] }}</span></td>
            <td>{{ o['customer_name'] }}</td>
            <td>{{ o['store_name'] }}</td>
            <td>{{ o['order_date'] }}</td>
            <td>{{ o['payment_method'] }}</td>
            <td>${{ "%.2f"|format(o['total_amount']) }}</td>
            <td>
                Status: {{ o['delivery_status'] }}<br>
                Ship: {{ o['ship_date'] or '-' }} | Deliv: {{ o['delivery_date'] or '-' }}
            </td>
            <td>
                <form method="POST">
                    <input type="hidden" name="action" value="update_delivery">
                    <input type="hidden" name="order_id" value="{{ o['order_id'] }}">
                    <select name="delivery_status">
                        {% for st in ['Pending', 'Shipped', 'Delivered', 'Cancelled'] %}
                        <option value="{{ st }}" {% if o['delivery_status'] == st %}selected{% endif %}>{{ st }}</option>
                        {% endfor %}
                    </select>
                    <input type="text" name="tracking_number" value="{{ o['tracking_number'] or '' }}" placeholder="Tracking #" style="width:120px;">
                    <button type="submit" class="btn">Update</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
 
    <div class="card" style="margin-top:25px;">
        <h3>Process Customer Return</h3>
        <form method="POST">
            <input type="hidden" name="action" value="process_return">
            <div class="form-row"><label>Order ID</label>
                <select name="order_id">
                    {% for o in orders %}<option value="{{ o['order_id'] }}">Order #{{ o['order_id'] }} ({{ o['customer_name'] }})</option>{% endfor %}
                </select>
            </div>
            <div class="form-row"><label>Part Returned</label>
                <select name="part_id">
                    {% for item in order_items %}<option value="{{ item['part_id'] }}">Order #{{ item['order_id'] }} - {{ item['part_number'] }} ({{ item['part_name'] }})</option>{% endfor %}
                </select>
            </div>
            <div class="form-row"><label>Quantity Returned</label><input type="number" name="quantity" min="1" value="1" required></div>
            <div class="form-row"><label>Reason</label><input type="text" name="reason" required></div>
            <button type="submit" class="btn btn-danger">Log Return & Refund</button>
        </form>
    </div>
    {% endblock %}
    """
    return render_template_string(template, orders=orders, order_items=order_items)

@app.route('/store/purchase-orders', methods=['GET', 'POST'])
def store_purchase_orders():
    if session.get('mode') != 'store': return redirect(url_for('store_login'))
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_po':
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO Purchase_Order (supplier_id, store_id, employee_id, expected_date, po_type, status)
                VALUES (?, ?, ?, ?, ?, 'Ordered')
            """, (request.form['supplier_id'], request.form['store_id'], session['employee_id'],
                  request.form['expected_date'], request.form['po_type']))
            po_id = cur.lastrowid
            cur.execute("INSERT INTO Purchase_Order_Item (po_id, part_id, quantity, unit_cost) VALUES (?, ?, ?, ?)",
                        (po_id, request.form['part_id'], request.form['quantity'], request.form['unit_cost']))
            conn.commit()
            flash(f"Purchase Order #{po_id} submitted to supplier.")
        elif action == 'update_po':
            po_id = int(request.form['po_id'])
            new_status = request.form['status']
            po = conn.execute("SELECT * FROM Purchase_Order WHERE po_id=?", (po_id,)).fetchone()
            if po and po['status'] == 'Ordered' and new_status == 'Received':
                items = conn.execute("SELECT * FROM Purchase_Order_Item WHERE po_id=?", (po_id,)).fetchall()
                for it in items:
                    conn.execute("""
                        INSERT INTO Inventory (store_id, part_id, quantity, reorder_level)
                        VALUES (?, ?, ?, 5)
                        ON CONFLICT(store_id, part_id) DO UPDATE SET quantity = quantity + excluded.quantity
                    """, (po['store_id'], it['part_id'], it['quantity']))
            conn.execute("UPDATE Purchase_Order SET status=? WHERE po_id=?", (new_status, po_id))
            conn.commit()
            flash(f"Purchase Order #{po_id} marked as {new_status}.")
    pos = conn.execute("""
        SELECT po.*, sup.supplier_name, s.store_name, p.part_number, p.part_name, poi.quantity, poi.unit_cost
        FROM Purchase_Order po
        JOIN Supplier sup ON po.supplier_id = sup.supplier_id
        JOIN Store s ON po.store_id = s.store_id
        JOIN Purchase_Order_Item poi ON po.po_id = poi.po_id
        JOIN Part p ON poi.part_id = p.part_id
        ORDER BY po.po_id DESC
    """).fetchall()
    suppliers = conn.execute("SELECT * FROM Supplier").fetchall()
    stores = conn.execute("SELECT * FROM Store").fetchall()
    parts = conn.execute("SELECT * FROM Part").fetchall()
    conn.close()
    template = """
    {% extends "base" %}
    {% block content %}
    <h2>Supplier Purchase Orders (Order New / Reorder / Stop Orders)</h2>
    <div class="card">
        <h3>Create Supplier Purchase Order</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_po">
            <div class="form-row"><label>Order Type</label>
                <select name="po_type"><option value="Reorder">Reorder</option><option value="New Part Order">New Part Order</option></select>
            </div>
            <div class="form-row"><label>Destination Store</label>
                <select name="store_id">{% for s in stores %}<option value="{{ s['store_id'] }}">{{ s['store_name'] }}</option>{% endfor %}</select>
            </div>
            <div class="form-row"><label>Supplier</label>
                <select name="supplier_id">{% for sup in suppliers %}<option value="{{ sup['supplier_id'] }}">{{ sup['supplier_name'] }}</option>{% endfor %}</select>
            </div>
            <div class="form-row"><label>Part</label>
                <select name="part_id">{% for p in parts %}<option value="{{ p['part_id'] }}">{{ p['part_number'] }} - {{ p['part_name'] }}</option>{% endfor %}</select>
            </div>
            <div class="form-row"><label>Quantity</label><input type="number" name="quantity" min="1" value="1" required></div>
            <div class="form-row"><label>Unit Cost ($)</label><input type="number" name="unit_cost" step="0.01" min="0" required></div>
            <div class="form-row"><label>Expected Delivery Date</label><input type="date" name="expected_date" required></div>
            <button type="submit" class="btn btn-success">Submit Purchase Order</button>
        </form>
    </div>
    <table>
        <tr><th>PO #</th><th>Type</th><th>Store</th><th>Supplier</th><th>Part</th><th>Qty</th><th>Unit Cost</th><th>Expected</th><th>Status</th><th>Action</th></tr>
        {% for po in pos %}
        <tr>
            <td>#{{ po['po_id'] }}</td>
            <td>{{ po['po_type'] }}</td>
            <td>{{ po['store_name'] }}</td>
            <td>{{ po['supplier_name'] }}</td>
            <td>{{ po['part_number'] }} ({{ po['part_name'] }})</td>
            <td>{{ po['quantity'] }}</td>
            <td>${{ "%.2f"|format(po['unit_cost']) }}</td>
            <td>{{ po['expected_date'] }}</td>
            <td>{{ po['status'] }}</td>
            <td>
                {% if po['status'] == 'Ordered' %}
                <form method="POST" style="display:inline;">
                    <input type="hidden" name="action" value="update_po">
                    <input type="hidden" name="po_id" value="{{ po['po_id'] }}">
                    <button type="submit" name="status" value="Received" class="btn btn-success">Mark Received</button>
                    <button type="submit" name="status" value="Stopped" class="btn btn-danger">Stop Order</button>
                </form>
                {% else %}
                    -
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    {% endblock %}
    """
    return render_template_string(template, pos=pos, suppliers=suppliers, stores=stores, parts=parts)
 
@app.route('/store/database', methods=['GET', 'POST'])
def store_db_management():
    if session.get('mode') != 'store': return redirect(url_for('store_login'))
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_part':
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO Part (part_number, part_name, category, description, part_condition, unit_price, supplier_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (request.form['part_number'], request.form['part_name'], request.form['category'],
                      request.form['description'], request.form['part_condition'], request.form['unit_price'], request.form['supplier_id']))
                new_part_id = cur.lastrowid
                stores = cur.execute("SELECT store_id FROM Store").fetchall()
                for s in stores:
                    cur.execute("INSERT INTO Inventory (store_id, part_id, quantity, reorder_level) VALUES (?, ?, 0, 5)", (s['store_id'], new_part_id))
                conn.commit()
                flash("New auto part added to catalog.")
            except sqlite3.IntegrityError:
                flash("Part number already exists.")
        elif action == 'update_part':
            conn.execute("UPDATE Part SET part_name=?, unit_price=?, part_condition=? WHERE part_id=?",
                         (request.form['part_name'], request.form['unit_price'], request.form['part_condition'], request.form['part_id']))
            conn.commit()
            flash("Part updated.")
        elif action == 'add_store':
            try:
                conn.execute("INSERT INTO Store (store_name, street, city, state, zip, phone) VALUES (?,?,?,?,?,?)",
                             (request.form['store_name'], request.form['street'], request.form['city'],
                              request.form['state'], request.form['zip'], request.form['phone']))
                conn.commit()
                flash("New store location added.")
            except sqlite3.IntegrityError:
                flash("Store name already exists.")
    parts = conn.execute("SELECT p.*, sup.supplier_name FROM Part p LEFT JOIN Supplier sup ON p.supplier_id = sup.supplier_id").fetchall()
    stores = conn.execute("SELECT * FROM Store").fetchall()
    suppliers = conn.execute("SELECT * FROM Supplier").fetchall()
    conn.close()
    template = """
    {% extends "base" %}
    {% block content %}
    <h2>Database Management — Parts & Store Branches</h2>
    <div class="grid-2">
        <div class="card">
            <h3>Add New Auto Part</h3>
            <form method="POST">
                <input type="hidden" name="action" value="add_part">
                <div class="form-row"><label>Part Number</label><input type="text" name="part_number" required></div>
                <div class="form-row"><label>Part Name</label><input type="text" name="part_name" required></div>
                <div class="form-row"><label>Category</label><input type="text" name="category"></div>
                <div class="form-row"><label>Description</label><input type="text" name="description"></div>
                <div class="form-row"><label>Condition</label>
                    <select name="part_condition"><option value="New">New</option><option value="Rebuilt">Rebuilt</option></select>
                </div>
                <div class="form-row"><label>Unit Price ($)</label><input type="number" name="unit_price" step="0.01" min="0" required></div>
                <div class="form-row"><label>Primary Supplier</label>
                    <select name="supplier_id">{% for sup in suppliers %}<option value="{{ sup['supplier_id'] }}">{{ sup['supplier_name'] }}</option>{% endfor %}</select>
                </div>
                <button type="submit" class="btn btn-success">Add Part</button>
            </form>
        </div>
        <div class="card">
            <h3>Add New Store Location</h3>
            <form method="POST">
                <input type="hidden" name="action" value="add_store">
                <div class="form-row"><label>Store Name</label><input type="text" name="store_name" required></div>
                <div class="form-row"><label>Street</label><input type="text" name="street"></div>
                <div class="form-row"><label>City</label><input type="text" name="city"></div>
                <div class="form-row"><label>State</label><input type="text" name="state" maxlength="2"></div>
                <div class="form-row"><label>ZIP Code</label><input type="text" name="zip" maxlength="5"></div>
                <div class="form-row"><label>Phone</label><input type="text" name="phone"></div>
                <button type="submit" class="btn btn-success">Add Store Branch</button>
            </form>
        </div>
    </div>
 
    <h3>Active Branches</h3>
    <ul>
        {% for s in stores %}<li>{{ s['store_name'] }} — {{ s['city'] }}, {{ s['state'] }} ({{ s['phone'] }})</li>{% endfor %}
    </ul>
 
    <h3>Update Existing Auto Parts</h3>
    <table>
        <tr><th>Part #</th><th>Name</th><th>Condition</th><th>Unit Price</th><th>Supplier</th><th>Save</th></tr>
        {% for p in parts %}
        <tr>
            <td>{{ p['part_number'] }}</td>
            <td><input type="text" name="part_name" value="{{ p['part_name'] }}" form="upd{{ p['part_id'] }}"></td>
            <td>
                <select name="part_condition" form="upd{{ p['part_id'] }}">
                    <option value="New" {% if p['part_condition'] == 'New' %}selected{% endif %}>New</option>
                    <option value="Rebuilt" {% if p['part_condition'] == 'Rebuilt' %}selected{% endif %}>Rebuilt</option>
                </select>
            </td>
            <td><input type="number" name="unit_price" step="0.01" min="0" value="{{ p['unit_price'] }}" form="upd{{ p['part_id'] }}" style="width:90px;"></td>
            <td>{{ p['supplier_name'] or '-' }}</td>
            <td>
                <form id="upd{{ p['part_id'] }}" method="POST">
                    <input type="hidden" name="action" value="update_part">
                    <input type="hidden" name="part_id" value="{{ p['part_id'] }}">
                    <button type="submit" class="btn">Save</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% endblock %}
    """
    return render_template_string(template, parts=parts, stores=stores, suppliers=suppliers)

@app.route('/store/employees', methods=['GET', 'POST'])
def store_employees():
    if session.get('mode') != 'store':
        return redirect(url_for('store_login'))
    is_manager = (session.get('role') =='Store Manager')
    conn = get_db_connection()
    if request.method == 'POST':
        if not is_manager:
            flash("Permisson Denied: Only Store Managers can modify employee records.")
            return redirect(url_for('store_employees'))
        action = request.form.get('action')
        if action == 'add':
            
            conn.execute("""
                    INSERT INTO Employee (store_id, manager_id, first_name, last_name, department, role, phone, email, username, password_hash, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active')
                """, (
                    request.form['store_id'],
                    request.form['manager_id'],
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['department'],
                    request.form['role'],
                    request.form['phone'],
                    request.form['email'],
                    request.form['username'],
                    generate_password_hash(request.form['hashed_password'])))
            conn.commit()
            flash("Employee added successfully.")
        elif action == 'delete':
            conn.execute(
                "DELETE FROM Employee WHERE employee_id = ?",
                (request.form['employee_id'],)
            )
            conn.commit()
            flash("Employee removed.")

    employees = conn.execute("SELECT e.*, s.store_name FROM Employee e JOIN Store s ON e.store_id = s.store_id").fetchall()
    stores = conn.execute("SELECT * FROM Store").fetchall()
    conn.close()

    template = """
        {% extends "base" %}
        {% block content %}
        <h2>Manage Employees</h2>
        {% if not is_manager %}
            <p><em>Editing restricted to only Store Managers.</em></p>
        {% else %}
        <div class="card">
            <h3>Add a new employee</h3>
            <form method="POST">
                <input type="hidden" name="action" value="add">
                <div class ="grid-2">
                    <div>
                        <div class="form-row"><label>First Name</label><input type="text" name="first_name" required></div>
                        <div class="form-row"><label>Last Name</label><input type="text" name="last_name" required></div>
                        <div class="form-row"><label>Department</label><input type="text" name="department"></div>
                        <div class="form-row"><label>Role</label><input type="text" name="role" placeholder="e.g. Store Manager, Sales Associate">></div>
                        <div class="form-row"><label>Phone</label><input type="text" name="phone"></div>
                    </div>
                    <div>
                        <div class="form-row"><label>Email</label><input type="email" name="email"></div>
                        <div class="form-row"><label>Assigned Store</label><select name ="store_id">{% for s in stores %}<option value="{{ s['store_id'] }}">{{ s['store_name'] }}</option>{% endfor %} </select></div>
                        <div class="form-row"><label>Login Username</label><input type="text" name="username" required></div>
                        <div class="form-row"><label>Password</label><input type="password" name="password" required></div>
                    </div>
                </div>
                <button type="submit" class="btn btn-success">Add Employee</button>
            </form>
        </div>
        {% endif %}
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Store</th>
                <th>Department</th>
                <th>Role</th>
                <th>Status</th>
                {% if is_manager %}<th>Actions</th>{% endif %}
            </tr>
            {% for e in employees %}
            <tr>
                <td>#{{ e['employee_id'] }}</td>
                <td>{{ e['first_name'] }} {{ e['last_name'] }}, {{ e['username'] }}</td>
                <td>{{ e['store_name'] }}</td>
                {% if is_manager %}
                    <td>
                        <form method="POST" style="display:inline;">
                            <input type="hidden" name="action" value="edit">
                            <input type="hidden" name="employee_id" value="{{ e['employee_id' }}">
                            <input type+"text" name="department" value="{{ e['department'] or ''}}"style="width:110px;">
                            <input type="text" name="role" value="{{ e['role'] or '' }}"style="width:110px;">
                            <select name="store_id">
                                {% for s in stores %}<option value="{{ s['store_id'] }}" {% if s['store_id'] == e['store_id'] %}selected{% endif %}>{{ s['store_name'] }}</option>{% endfor %}
                            </select>
                            <select name="status">
                                <option value = "Active" {% if e['status'] =='Active' %}selected{% endif %}>Active</option>
                                <option value = "Inactive" {% if e['status'] =='Inactive' %}selected{% endif %}Inactive{/option>
                            </select>
                            <button type="submit" class="btn">Save</button>
                        </form>
                    </td>
                    <td>
                        <form method="POST" onsubmit="return confirm('Remove this employee?')">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="employee_id" value="{{ e['employee_id'] }}">
                            <button type="submit" class="btn btn-danger">Delete</button>
                        </form>
                    </td>
                {% else %}
                    <td>{{ e['department'] }}</td>
                    <td>{{ e['role'] }}</td>
                    <td>{{ e['status'] }}</td>
                {% endif %}
            </tr>
            {% endfor %}
        <table>
        {%endblock%}
        """
    return render_template_string(template, employees=employees)

@app.route('/store/orders')
def order_management():
    if session.get('mode') != 'store': return redirect(url_for('store_login'))
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
    return render_template_string(template, orders=orders)
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