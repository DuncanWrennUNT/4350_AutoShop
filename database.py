import sqlite3
from flask import views
from werkzeug.security import generate_password_hash

def init_db():
conn = sqlite3.connect('auto_parts.db')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
views = ['v_daily_sales', 'v_weekly_sales', 'v_monthly_sales', 'v_low_stock', 'v_employee_status', 'v_part_sales', 'v_inventory_value', 'v_returns']
for view in views:
    cursor.execute(f"DROP VIEW IF EXISTS {view}")
tables = ['Purchase_Order_Item', 'Purchase_Order', 'Return_Item', 'Delivery', 'Payment', 'Order_Item', 'Orders', 'Inventory', 'Part', 'Supplier', 'Customer_Vehicle', 'Customer', 'Employee', 'Store']
for table in tables:
	cursor.execute(f"DROP TABLE IF EXISTS {table}")
		
		
		
    #START OF TABLES
cursor.execute('''CREATE TABLE Store (
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT UNIQUE NOT NULL,
    street TEXT, city TEXT, state TEXT, zip TEXT, phone TEXT
)''')
		
cursor.execute('''CREATE TABLE Employee (
		employee_id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER, manager_id INTEGER,
		first_name TEXT NOT NULL, last_name TEXT NOT NULL, department TEXT, role TEXT,
		phone TEXT, email TEXT UNIQUE, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
		hire_date TEXT DEFAULT CURRENT_DATE, status TEXT DEFAULT 'Active',
		FOREIGN KEY (store_id) REFERENCES Store(store_id),
		FOREIGN KEY (manager_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
)''')
		
cursor.execute('''CREATE TABLE Customer (
		Customer_id INTEGER PRIMARY KEY AUTOINCREMENT, preferred_store_id INTEGER,
		first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
		phone TEXT, street TEXT, city TEXT, state TEXT, zip TEXT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
		created_at TEXT DEFAULT CURRENT_DATE, FOREIGN KEY (preferred_store_id) REFERENCES Store(store_id)
)''')
		
cursor.execute('''CREATE TABLE Customer_Vehicle (
        vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        year INTEGER,
        make TEXT NOT NULL,
        model TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE
)''')
        
cursor.execute('''CREATE TABLE Supplier(supplier_id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_name TEXT UNIQUE NOT NULL, phone TEXT, email TEXT, address TEXT)''')
		
cursor.execute('''CREATE TABLE Part(
		part_id INTEGER PRIMARY KEY AUTOINCREMENT, part_number TEXT UNIQUE NOT NULL, part_name TEXT UNIQUE NOT NULL,
		category TEXT, description TEXT, part_condition TEXT CHECK(part_condition IN ('New', 'Rebuilt')),
		unit_price REAL NOT NULL CHECK(unit_price>= 0), supplier_id INTEGER, FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
	)''')

cursor.execute('''CREATE TABLE Inventory (
        store_id INTEGER,
        part_id INTEGER,
        quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
        reorder_level INTEGER NOT NULL DEFAULT 5,
        PRIMARY KEY (store_id, part_id),
        FOREIGN KEY (store_id) REFERENCES Store(store_id) ON DELETE RESTRICT,
        FOREIGN KEY (part_id) REFERENCES Part(part_id) ON DELETE RESTRICT
    )''')
		
cursor.execute('''CREATE TABLE Orders (
			order_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, store_id INTEGER,
			order_date TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'Pending', total_amount REAL NOT NULL DEFAULT 0.0,
			FOREIGN KEY (customer_id) REFERENCES Customer(customer_id), FOREIGN KEY (order_id) REFERENCES Orders(order_id)
		)''')
		
cursor.execute('''CREATE TABLE Order_Item (
			order_id INTEGER, part_id INTEGER, quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price REAL NOT NULL,
			PRIMARY KEY (order_id, part_id), FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE, FOREIGN KEY (part_id) REFERENCES Part(part_id)
		)''')
		
cursor.execute('''CREATE TABLE Payment (
			payment_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, method TEXT, card_type TEXT, card_last4 TEXT,
			billing_address TEXT, amount REAL, payment_date TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT, FOREIGN KEY (order_id) REFERENCES Orders(order_id)
		)''')
		
cursor.execute('''CREATE TABLE Delivery (
            delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER UNIQUE,
            employee_id INTEGER,
            ship_date TEXT,
            delivery_date TEXT,
            tracking_number TEXT UNIQUE,
            status TEXT DEFAULT 'Pending' CHECK(status IN('Pending', 'Shipped', 'Delivered', 'Cancelled')),
            FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE, 
            FOREIGN KEY (store_id) REFERENCES Store(store_id),
            FOREIGN KEY (employee_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
        )''')
        
cursor.execute('''CREATE TABLE Return_Item (
            return_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            part_id INTEGER,
            employee_id INTEGER,
            return_date TEXT DEFAULT CURRENT_TIMESTAMP,
            quantity INTEGER NOT NULL CHECK(quantity>0),
            reason TEXT,
            refund_amount REAL NOT NULL,
            FOREIGN KEY(order_id, part_id) REFERENCES Order_Item(order_id, part_id),
            FOREIGN KEY(employee_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
        )''')
        
cursor.execute('''CREATE TABLE Purchase_Order(
            po_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            store_id INTEGER,
            employee_id INTEGER,
            order_date TEXT DEFAULT CURRENT_DATE,
            expected_date TEXT,
            po_type TEXT DEFAULT 'Ordered' CHECK(po_typeIN ('Ordered', 'Received', 'Stopped')),
            FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
            FOREIGN KEY (store_id) REFERENCES Store(store_id),
            FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
        )''')
        
cursor.execute('''CREATE TABLE Purchase_Order_Item (
            po_id INTEGER PRIMARY KEY AUTOINCREMENT,
			supplier_id INTEGER,
			store_id INTEGER,
			employee_id INTEGER,
			order_date TEXT DEFAULT CURRENT_DATE,
            expected_date TEXT,
			po_type TEXT DEFAULT 'Reorder' CHECK(po_type IN ('Reorder', 'New Part Order')),
			status TEXT DEFAULT 'Ordered' CHECK(status IN ('Ordered', 'Received', 'Stopped')),
			FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
			FOREIGN KEY (store_id) REFERENCES Store(store_id),
			FOREIGN KEY (employee_id) REFERENCES Employee(employee_id) ON DELETE SET NULL
			)''')
        
		
		#START OF REPORTS
cursor.execute("""
            CREATE VIEW v_daily_sales AS
            SELECT s.store_name, DATE(o.order_date) AS period, COUNT(o.order_id) AS order_count, SUM(o.total_amount - ifnull((select sum(r.refund_amount) from Return r where r.order_id = o.order_id), 0)) AS revenue
            FROM Orders o JOIN Store s ON o.store_id = s.store_id
            WHERE o.status != 'Cancelled'
            GROUP BY s.store_id, Date(o.order_date)
        """)
cursor.execute("""
            CREATE VIEW v_weekly_sales AS
            SELECT s.store_name, strftime('%Y-W%W', o.order_date) AS period, COUNT(o.order_id) AS order_count, SUM(o.total_amount - ifnull((select sum(r.refund_amount) from Return r where r.order_id = o.order_id), 0)) AS revenue
            FROM Orders o JOIN Store s ON o.store_id = s.store_id
            WHERE o.status != 'Cancelled'
            GROUP BY s.store_id, strftime('%Y-W%W', o.order_date)
        """)
cursor.execute("""
            CREATE VIEW v_monthly_sales AS
            SELECT s.store_name, strftime('%Y-%m', o.order_date) AS period, COUNT(o.order_id) AS order_count, SUM(o.total_amount - ifnull((select sum(r.refund_amount) from Return r where r.order_id = o.order_id), 0)) AS revenue
            FROM Orders o JOIN Store s ON o.store_id = s.store_id
            WHERE o.status != 'Cancelled'
            GROUP BY s.store_id, strftime('%Y-%m', o.order_date)
        """)
cursor.execute("""
			create view v_low_stock AS
			SELECT s.store_name, p.part_number, p.part_name, p.supplier_id, i.quantity, i.reorder_level
			FROM Inventory i
			JOIN Part p ON i.part_id = p.part_id
			join Store s ON s.store_id = i.store_id
			WHERE i.quantity <= i.reorder_level
		""")
cursor.execute("""
            CREATE VIEW v_employee_status AS
            SELECT e.employee_id, e.first_name ||' '|| e.last_name AS employee_name,
                s.store_name, e.department, e.role, e.status,
                IFNULL(m.first_name ||' '|| m.last_name, 'None') AS manager_name
            FROM employee e
            JOIN Store s ON e.store_id = s.store_id
            LEFT JOIN Employee m ON e.manager_id = m.employee_id
        """)
cursor.execute("""
    CREATE VIEW v_part_sales AS
    SELECT p.part_id, p.part_number, p.part_name, p.category
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
	SELECT r.return_id, r.return_date, s.store_name, r.order_id, p.part_number, p.part_name, r.quantity, r.reason, r.refund_amount
	IFNULL (e.first_name ||' '|| e.last_name, 'Unknown') AS processed_by
    FROM Return_Item r
    JOIN Orders o ON r.order_id = o.order_id
	JOIN Store s ON o.store_id = s.store_id
	JOIN Part p ON r.part_id = p.part_id
""")

conn.commit()
conn.close()
print("Database Framework Initialized.")
		
if __name__ == '__main__':
    init_db()