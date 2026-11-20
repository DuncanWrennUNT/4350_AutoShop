import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# The database file always lives next to this script, no matter where the app is started from.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_parts.db')


def init_db(seed=True):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    views = ['v_daily_sales', 'v_weekly_sales', 'v_monthly_sales', 'v_low_stock', 'v_employee_status', 'v_part_sales', 'v_inventory_value', 'v_returns']
    for view in views:
        cursor.execute(f"DROP VIEW IF EXISTS {view}")
    tables = ['Purchase_Order_Item', 'Purchase_Order', 'Return_Item', 'Delivery', 'Payment', 'Order_Item', 'Orders', 'Inventory', 'Part', 'Supplier', 'Customer_Vehicle', 'Customer', 'Employee', 'Store']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute("PRAGMA foreign_keys = ON;")

    # START OF TABLES
    cursor.execute('''CREATE TABLE Store (
        store_id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT UNIQUE NOT NULL,
        street TEXT, city TEXT, state TEXT, zip TEXT, phone TEXT
    )''')

    cursor.execute('''CREATE TABLE Employee (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER NOT NULL, manager_id INTEGER,
        first_name TEXT NOT NULL, last_name TEXT NOT NULL, department TEXT, role TEXT,
        phone TEXT, email TEXT UNIQUE, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        hire_date TEXT DEFAULT (date('now', 'localtime')), status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
        FOREIGN KEY (store_id) REFERENCES Store(store_id),
        FOREIGN KEY (manager_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
    )''')

    cursor.execute('''CREATE TABLE Customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT, preferred_store_id INTEGER,
        first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        phone TEXT, street TEXT, city TEXT, state TEXT, zip TEXT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT (date('now', 'localtime')),
        FOREIGN KEY (preferred_store_id) REFERENCES Store(store_id) ON DELETE SET NULL
    )''')

    cursor.execute('''CREATE TABLE Customer_Vehicle (
        vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        year INTEGER,
        make TEXT NOT NULL,
        model TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE Supplier (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_name TEXT UNIQUE NOT NULL,
        phone TEXT, email TEXT, address TEXT
    )''')

    cursor.execute('''CREATE TABLE Part (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT, part_number TEXT UNIQUE NOT NULL, part_name TEXT NOT NULL,
        category TEXT, description TEXT, part_condition TEXT NOT NULL DEFAULT 'New' CHECK(part_condition IN ('New', 'Rebuilt')),
        unit_price REAL NOT NULL CHECK(unit_price >= 0), supplier_id INTEGER,
        FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
    )''')

    cursor.execute('''CREATE TABLE Inventory (
        store_id INTEGER,
        part_id INTEGER,
        quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
        reorder_level INTEGER NOT NULL DEFAULT 5 CHECK(reorder_level >= 0),
        PRIMARY KEY (store_id, part_id),
        FOREIGN KEY (store_id) REFERENCES Store(store_id) ON DELETE RESTRICT,
        FOREIGN KEY (part_id) REFERENCES Part(part_id) ON DELETE RESTRICT
    )''')

    cursor.execute('''CREATE TABLE Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, store_id INTEGER NOT NULL,
        order_date TEXT DEFAULT (datetime('now', 'localtime')),
        status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Paid', 'Shipped', 'Delivered', 'Cancelled', 'Returned')),
        total_amount REAL NOT NULL DEFAULT 0.0 CHECK(total_amount >= 0),
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
        FOREIGN KEY (store_id) REFERENCES Store(store_id)
    )''')

    cursor.execute('''CREATE TABLE Order_Item (
        order_id INTEGER, part_id INTEGER, quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price REAL NOT NULL CHECK(unit_price >= 0),
        PRIMARY KEY (order_id, part_id),
        FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (part_id) REFERENCES Part(part_id)
    )''')

    cursor.execute('''CREATE TABLE Payment (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, method TEXT NOT NULL, card_type TEXT, card_last4 TEXT CHECK(card_last4 IS NULL OR length(card_last4) = 4),
        billing_address TEXT, amount REAL NOT NULL CHECK(amount >= 0), payment_date TEXT DEFAULT (datetime('now', 'localtime')),
        status TEXT DEFAULT 'Approved' CHECK(status IN ('Approved', 'Declined', 'Refunded')),
        FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE Delivery (
        delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER UNIQUE NOT NULL,
        employee_id INTEGER,
        ship_date TEXT,
        delivery_date TEXT,
        tracking_number TEXT UNIQUE,
        status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled')),
        FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
    )''')

    cursor.execute('''CREATE TABLE Return_Item (
        return_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        part_id INTEGER NOT NULL,
        employee_id INTEGER,
        return_date TEXT DEFAULT (datetime('now', 'localtime')),
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        reason TEXT,
        refund_amount REAL NOT NULL CHECK(refund_amount >= 0),
        FOREIGN KEY (order_id, part_id) REFERENCES Order_Item(order_id, part_id),
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
    )''')

    cursor.execute('''CREATE TABLE Purchase_Order (
        po_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER NOT NULL,
        store_id INTEGER NOT NULL,
        employee_id INTEGER,
        order_date TEXT DEFAULT (date('now', 'localtime')),
        expected_date TEXT,
        po_type TEXT DEFAULT 'Reorder' CHECK(po_type IN ('Reorder', 'New Part Order')),
        status TEXT DEFAULT 'Ordered' CHECK(status IN ('Ordered', 'Received', 'Stopped')),
        FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
        FOREIGN KEY (store_id) REFERENCES Store(store_id),
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
    )''')

    cursor.execute('''CREATE TABLE Purchase_Order_Item (
        po_id INTEGER,
        part_id INTEGER,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
        PRIMARY KEY (po_id, part_id),
        FOREIGN KEY (po_id) REFERENCES Purchase_Order(po_id) ON DELETE CASCADE,
        FOREIGN KEY (part_id) REFERENCES Part(part_id)
    )''')

    # START OF REPORTS
    cursor.execute("""
        CREATE VIEW v_daily_sales AS
        SELECT s.store_name, DATE(o.order_date) AS period, COUNT(o.order_id) AS order_count,
               SUM(o.total_amount - IFNULL((SELECT SUM(r.refund_amount) FROM Return_Item r WHERE r.order_id = o.order_id), 0)) AS revenue
        FROM Orders o JOIN Store s ON o.store_id = s.store_id
        WHERE o.status != 'Cancelled'
        GROUP BY s.store_id, DATE(o.order_date)
    """)
    cursor.execute("""
        CREATE VIEW v_weekly_sales AS
        SELECT s.store_name, strftime('%Y-W%W', o.order_date) AS period, COUNT(o.order_id) AS order_count,
               SUM(o.total_amount - IFNULL((SELECT SUM(r.refund_amount) FROM Return_Item r WHERE r.order_id = o.order_id), 0)) AS revenue
        FROM Orders o JOIN Store s ON o.store_id = s.store_id
        WHERE o.status != 'Cancelled'
        GROUP BY s.store_id, strftime('%Y-W%W', o.order_date)
    """)
    cursor.execute("""
        CREATE VIEW v_monthly_sales AS
        SELECT s.store_name, strftime('%Y-%m', o.order_date) AS period, COUNT(o.order_id) AS order_count,
               SUM(o.total_amount - IFNULL((SELECT SUM(r.refund_amount) FROM Return_Item r WHERE r.order_id = o.order_id), 0)) AS revenue
        FROM Orders o JOIN Store s ON o.store_id = s.store_id
        WHERE o.status != 'Cancelled'
        GROUP BY s.store_id, strftime('%Y-%m', o.order_date)
    """)
    cursor.execute("""
        CREATE VIEW v_low_stock AS
        SELECT s.store_name, p.part_number, p.part_name, p.supplier_id, i.quantity, i.reorder_level
        FROM Inventory i
        JOIN Part p ON i.part_id = p.part_id
        JOIN Store s ON s.store_id = i.store_id
        WHERE i.quantity <= i.reorder_level
    """)
    cursor.execute("""
        CREATE VIEW v_employee_status AS
        SELECT e.employee_id, e.first_name || ' ' || e.last_name AS employee_name,
               s.store_name, e.department, e.role, e.status,
               IFNULL(m.first_name || ' ' || m.last_name, 'None') AS manager_name
        FROM Employee e
        JOIN Store s ON e.store_id = s.store_id
        LEFT JOIN Employee m ON e.manager_id = m.employee_id
    """)
    cursor.execute("""
        CREATE VIEW v_part_sales AS
        SELECT p.part_id, p.part_number, p.part_name, p.category,
               IFNULL(sold.units, 0) AS units_sold,
               IFNULL(ret.units, 0) AS units_returned,
               IFNULL(sold.units, 0) - IFNULL(ret.units, 0) AS net_units,
               IFNULL(sold.revenue, 0) AS revenue,
               IFNULL(ret.refunds, 0) AS refunds,
               IFNULL(sold.revenue, 0) - IFNULL(ret.refunds, 0) AS net_revenue
        FROM Part p
        LEFT JOIN (
            SELECT oi.part_id, SUM(oi.quantity) AS units, SUM(oi.quantity * oi.unit_price) AS revenue
            FROM Order_Item oi JOIN Orders o ON oi.order_id = o.order_id
            WHERE o.status != 'Cancelled'
            GROUP BY oi.part_id
        ) sold ON p.part_id = sold.part_id
        LEFT JOIN (
            SELECT r.part_id, SUM(r.quantity) AS units, SUM(r.refund_amount) AS refunds
            FROM Return_Item r JOIN Orders o ON r.order_id = o.order_id
            WHERE o.status != 'Cancelled'
            GROUP BY r.part_id
        ) ret ON p.part_id = ret.part_id
    """)
    cursor.execute("""
        CREATE VIEW v_inventory_value AS
        SELECT s.store_name, p.part_name, i.quantity, p.unit_price, (i.quantity * p.unit_price) AS total_value
        FROM Inventory i
        JOIN Part p ON i.part_id = p.part_id
        JOIN Store s ON i.store_id = s.store_id
    """)
    cursor.execute("""
        CREATE VIEW v_returns AS
        SELECT r.return_id, r.return_date, s.store_name, r.order_id, p.part_number, p.part_name, r.quantity, r.reason, r.refund_amount,
               IFNULL(e.first_name || ' ' || e.last_name, 'Unknown') AS processed_by
        FROM Return_Item r
        JOIN Orders o ON r.order_id = o.order_id
        JOIN Store s ON o.store_id = s.store_id
        JOIN Part p ON r.part_id = p.part_id
        LEFT JOIN Employee e ON r.employee_id = e.employee_id
    """)

    if seed:
        seed_sample_data(cursor)

    conn.commit()
    conn.close()
    print("Database Framework Initialized.")


def seed_sample_data(cursor):
    """Sample data so every screen and report has something to show."""
    cursor.executemany("INSERT INTO Store (store_name, street, city, state, zip, phone) VALUES (?, ?, ?, ?, ?, ?)", [
        ('Denton Main Street', '120 W Hickory St', 'Denton', 'TX', '76201', '940-555-0101'),
        ('Lewisville Crossing', '450 S Stemmons Fwy', 'Lewisville', 'TX', '75067', '972-555-0202'),
    ])

    # (store, manager, first, last, department, role, phone, email, username, password)
    employees = [
        (1, None, 'Maria', 'Lopez', 'Management', 'Store Manager', '940-555-1001', 'mlopez@autoshop.test', 'Manager1', 'adminpwd'),
        (1, 1, 'James', 'Carter', 'Sales', 'Sales Associate', '940-555-1002', 'jcarter@autoshop.test', 'Staff1', 'staffpwd'),
        (1, 1, 'Aisha', 'Khan', 'Shipping', 'Delivery Clerk', '940-555-1003', 'akhan@autoshop.test', 'Staff2', 'staffpwd'),
        (2, None, 'Robert', 'Nguyen', 'Management', 'Store Manager', '972-555-2001', 'rnguyen@autoshop.test', 'Manager2', 'adminpwd'),
        (2, 4, 'Emily', 'Brooks', 'Sales', 'Sales Associate', '972-555-2002', 'ebrooks@autoshop.test', 'Staff3', 'staffpwd'),
    ]
    for e in employees:
        cursor.execute("""INSERT INTO Employee (store_id, manager_id, first_name, last_name, department, role, phone, email, username, password_hash, hire_date)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2025-03-01')""", (*e[:9], generate_password_hash(e[9])))

    cursor.executemany("INSERT INTO Supplier (supplier_name, phone, email, address) VALUES (?, ?, ?, ?)", [
        ('Lone Star Auto Supply', '214-555-3001', 'orders@lonestarauto.test', '900 Commerce St, Dallas, TX'),
        ('Gulf Coast Parts Co.', '713-555-3002', 'sales@gulfcoastparts.test', '55 Harbor Rd, Houston, TX'),
        ('Reman Experts LLC', '512-555-3003', 'service@remanexperts.test', '18 Industrial Blvd, Austin, TX'),
    ])

    # (number, name, category, description, condition, price, supplier)
    parts = [
        ('BRK-1001', 'Ceramic Brake Pads (Front)', 'Brakes', 'Low-dust ceramic pads for most sedans', 'New', 54.99, 1),
        ('BRK-1002', 'Brake Rotor 11.9 in', 'Brakes', 'Vented front rotor', 'New', 72.50, 1),
        ('BRK-2001', 'Brake Caliper (Rebuilt)', 'Brakes', 'Remanufactured front caliper', 'Rebuilt', 48.00, 3),
        ('ENG-1001', 'Synthetic Oil 5W-30 (5 qt)', 'Engine', 'Full synthetic motor oil', 'New', 29.99, 2),
        ('ENG-1002', 'Oil Filter', 'Engine', 'Spin-on oil filter', 'New', 8.49, 2),
        ('ENG-1003', 'Engine Air Filter', 'Engine', 'Panel air filter', 'New', 18.99, 2),
        ('ELE-1001', 'Car Battery 650 CCA', 'Electrical', 'Group 35 battery, 3-year warranty', 'New', 159.99, 1),
        ('ELE-2001', 'Alternator (Rebuilt)', 'Electrical', 'Remanufactured 130A alternator', 'Rebuilt', 189.00, 3),
        ('ELE-2002', 'Starter Motor (Rebuilt)', 'Electrical', 'Remanufactured starter', 'Rebuilt', 139.00, 3),
        ('IGN-1001', 'Iridium Spark Plug', 'Ignition', 'Long-life iridium plug', 'New', 11.99, 2),
        ('SUS-1001', 'Front Strut Assembly', 'Suspension', 'Complete quick-strut assembly', 'New', 129.95, 1),
        ('WIP-1001', 'Wiper Blade 22 in', 'Accessories', 'All-season beam wiper', 'New', 21.99, 2),
    ]
    cursor.executemany("INSERT INTO Part (part_number, part_name, category, description, part_condition, unit_price, supplier_id) VALUES (?, ?, ?, ?, ?, ?, ?)", parts)

    # Inventory per store: (quantity, reorder level). A few rows are at or below the reorder level on purpose.
    store1 = [(25, 5), (12, 4), (3, 4), (40, 10), (60, 15), (18, 5), (7, 3), (2, 2), (4, 2), (80, 20), (6, 2), (30, 8)]
    store2 = [(10, 5), (8, 4), (5, 4), (22, 10), (12, 15), (9, 5), (4, 3), (3, 2), (0, 2), (50, 20), (2, 2), (15, 8)]
    for store_id, stock in ((1, store1), (2, store2)):
        for part_id, (qty, level) in enumerate(stock, start=1):
            cursor.execute("INSERT INTO Inventory (store_id, part_id, quantity, reorder_level) VALUES (?, ?, ?, ?)", (store_id, part_id, qty, level))

    customers = [
        (1, 'John', 'Smith', 'john.smith@example.com', '940-555-4001', '101 Oak St', 'Denton', 'TX', '76201', 'customer1', 'custpwd'),
        (2, 'Sara', 'Lee', 'sara.lee@example.com', '972-555-4002', '22 Elm Ave', 'Lewisville', 'TX', '75067', 'customer2', 'custpwd'),
        (1, 'David', 'Garcia', 'david.garcia@example.com', '940-555-4003', '7 Pine Ct', 'Denton', 'TX', '76205', 'customer3', 'custpwd'),
    ]
    for c in customers:
        cursor.execute("""INSERT INTO Customer (preferred_store_id, first_name, last_name, email, phone, street, city, state, zip, username, password_hash, created_at)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2026-09-01')""", (*c[:10], generate_password_hash(c[10])))
    cursor.executemany("INSERT INTO Customer_Vehicle (customer_id, year, make, model) VALUES (?, ?, ?, ?)", [
        (1, 2018, 'Toyota', 'Camry'), (1, 2012, 'Ford', 'F-150'), (2, 2020, 'Honda', 'Civic'), (3, 2016, 'Chevrolet', 'Malibu'),
    ])

    # Historical orders spread over the last weeks so the daily/weekly/monthly reports have data.
    now = datetime.now()
    # (customer, store, days ago, status, delivery status, [(part, qty)], card type, last4)
    orders = [
        (1, 1, 40, 'Delivered', 'Delivered', [(1, 1), (2, 2)], 'Visa', '4242'),
        (2, 2, 33, 'Delivered', 'Delivered', [(7, 1)], 'Mastercard', '5454'),
        (3, 1, 20, 'Returned', 'Delivered', [(4, 2), (5, 2)], 'Visa', '1111'),
        (1, 1, 12, 'Delivered', 'Delivered', [(10, 4)], 'Visa', '4242'),
        (2, 2, 6, 'Shipped', 'Shipped', [(11, 1), (12, 2)], 'American Express', '0005'),
        (3, 1, 2, 'Paid', 'Pending', [(6, 1), (5, 1)], 'Discover', '1117'),
        (1, 1, 0, 'Paid', 'Pending', [(3, 1)], 'Visa', '4242'),
    ]
    for n, (cust, store, days, status, dstatus, items, card_type, last4) in enumerate(orders, start=1):
        odate = now - timedelta(days=days)
        total = 0.0
        prices = []
        for part_id, qty in items:
            price = cursor.execute("SELECT unit_price FROM Part WHERE part_id=?", (part_id,)).fetchone()[0]
            prices.append(price)
            total += price * qty
        cursor.execute("INSERT INTO Orders (customer_id, store_id, order_date, status, total_amount) VALUES (?, ?, ?, ?, ?)",
                       (cust, store, odate.strftime('%Y-%m-%d %H:%M:%S'), status, round(total, 2)))
        order_id = cursor.lastrowid
        for (part_id, qty), price in zip(items, prices):
            cursor.execute("INSERT INTO Order_Item (order_id, part_id, quantity, unit_price) VALUES (?, ?, ?, ?)", (order_id, part_id, qty, price))
        addr = cursor.execute("SELECT street || ', ' || city || ', ' || state || ' ' || zip FROM Customer WHERE customer_id=?", (cust,)).fetchone()[0]
        cursor.execute("INSERT INTO Payment (order_id, method, card_type, card_last4, billing_address, amount, payment_date, status) VALUES (?, 'Credit Card', ?, ?, ?, ?, ?, 'Approved')",
                       (order_id, card_type, last4, addr, round(total, 2), odate.strftime('%Y-%m-%d %H:%M:%S')))
        ship = (odate + timedelta(days=1)).strftime('%Y-%m-%d') if dstatus in ('Shipped', 'Delivered') else None
        deliv = (odate + timedelta(days=3)).strftime('%Y-%m-%d') if dstatus == 'Delivered' else None
        handler = 3 if store == 1 else 5
        cursor.execute("INSERT INTO Delivery (order_id, employee_id, ship_date, delivery_date, tracking_number, status) VALUES (?, ?, ?, ?, ?, ?)",
                       (order_id, handler if ship else None, ship, deliv, f"TRK-SAMPLE{n:03d}", dstatus))

    # Order 3 had one oil jug returned.
    cursor.execute("INSERT INTO Return_Item (order_id, part_id, employee_id, return_date, quantity, reason, refund_amount) VALUES (3, 4, 2, ?, 1, 'Wrong viscosity', 29.99)",
                   ((now - timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S'),))

    # Supplier purchase orders: one received, one still open, one stopped.
    pos = [
        (2, 1, 1, 18, 'Reorder', 'Received', [(5, 40, 3.10)]),
        (3, 1, 1, 3, 'Reorder', 'Ordered', [(8, 5, 95.00)]),
        (1, 2, 4, 5, 'New Part Order', 'Stopped', [(11, 4, 70.00)]),
    ]
    for sup, store, emp, days, po_type, status, items in pos:
        od = (now - timedelta(days=days)).strftime('%Y-%m-%d')
        ed = (now - timedelta(days=days) + timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO Purchase_Order (supplier_id, store_id, employee_id, order_date, expected_date, po_type, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (sup, store, emp, od, ed, po_type, status))
        po_id = cursor.lastrowid
        for part_id, qty, cost in items:
            cursor.execute("INSERT INTO Purchase_Order_Item (po_id, part_id, quantity, unit_cost) VALUES (?, ?, ?, ?)", (po_id, part_id, qty, cost))


if __name__ == '__main__':
    init_db()
