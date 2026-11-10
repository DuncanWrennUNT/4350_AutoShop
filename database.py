import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
	conn = sqlite3.connect('auto_parts.db')
	cursor = conn.cursor()
	cursor.execute("PRAGMA foreign_keys = ON:")
	
	tables = ['Purchase_Order_Item', 'Purchase-Order', 'Return_Item', 'Delivery', 'Payment', 'Order_Item', 'Orders', 'Inventory', 'Part', 'Supplier', 'Customer_Vehicle', 'Customer', 'Employee', 'Store']
	for table in tables:
		cursor.execute(f"DROP TABLE IF EXISTS {table}")
		
		
		
		#START OF TABLES
		
		cursor.execute('''CREATE TABLE Employee (
			employee_id INTEGER PRIMARY_KEY AUTOINCREMENT, store_id INTEGER, manager_id INTEGER,
			first_name TEXT NOT NULL, last_name TEXT NOT NULL, department TEXT, role TEXT,
			phone TEXT, email TEXT UNIQUE, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
			hire_date TEXT, status TEXT,
			FOREIGN KEY (store_id) REFERENCES Store(store_id),
			FOREIGN KEY (manager_id) REFERENCES Employee(employee_id)
		)''')
		
		cursor.execute('''CREATE TABLE Customer (
			Customer_id INTEGER PRIMARY KEY AUTOINCREMENT, preferred_store_id INTEGER,
			first_name TEXT NOT NULLL, last_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
			phone TEXT, street TEXT, city TEXT, state TEXT, zip TEXT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
			created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (preferred_store_id) REFERENCES Store(store_id)
		)''')
		
		cursor.execute('''CREATE TABLE Supplier(supplier_id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_name TEXT UNIQUE NOT_NULL, phone TEXT, email TEXT, address TEXT)')
		
		cursor.execute('''CREATE TABLE Part(
			part_id INTEGER PARIMARY KEY AUTOINCREMENT, part_number TEXT UNIQUE NOT NULL, part_name TEXT UNIQUE NOT NULL,
			category TEXT, description TEXT, part_condition TEXT CHECK(partcondition IN ('New', 'Rebuilt')),
			unit_price REAL NOT NULL CHECK(unit_price>= 0), supplier_id INTEGER, FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
			)''')
		
		cursor.execute('''CREATE TABLE Orders (
			order_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, store_id INTEGER,
			order_date TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'Pending', total_amount REAL NOT NULL DEFAULT 0.0,
			FOREIGN KEY (order_id, part_id), FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE, FOREIGN KEY (part_id) REFERENCES Part(part_id)
		)''')
		
		cursor.execute('''CREATE TABLE Order_Item (
			order_id INTEGER, part_id INTEGER, quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price REAL NOT NULL,
			PRIMARY KEY (order_id, part_id), FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE, FOREIGN KEY (part_id) REFERENCES Part(part_id)
		)''')
		
		cursor.execute('''CREATE TABLE Payment (
			payment_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, method TEXT, card_type TEXT, card_last4 TEXT,
			billing_address TEXT, amount REAL, payment_date TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT, FOREIGN KEY (order_id) REFERENCES Orders(order_id)
		)''')
		
		
		
		#START OF REPORTS
		cursor.execute("""
			create view low_stock AS
			SELECT s.store_name, p.part_number, p.part_name, i.quantity, i.reorder_level
			FROM Inventory i
			JOIN Part p ON i.part_id = p.part_id
			join Store s ON s.store_id = i.store_id
			WHERE i.quantity <= i.reorder_level
		""")
		
		
		
		conn.commit()
		conn.close()
		print("Database Framework Initialized.")
		
if __name__ == '__main__':
	init_db()