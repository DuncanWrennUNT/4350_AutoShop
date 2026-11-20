"""End-to-end tests for the Retail Auto Parts System.

Run with:  python test_app.py
Each test works on a fresh copy of the sample database in a temp folder,
so the real auto_parts.db is never touched.
"""
import os
import re
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager

import database
import app as app_module


class AutoPartsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        path = os.path.join(self.tmp.name, 'test.db')
        database.DB_PATH = path
        app_module.DB_PATH = path
        database.init_db()
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    # helpers
    @contextmanager
    def db(self):
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def stock(self, store_id, part_id):
        with self.db() as c:
            return c.execute("SELECT quantity FROM Inventory WHERE store_id=? AND part_id=?", (store_id, part_id)).fetchone()[0]

    def login_customer(self, user='customer1', pwd='custpwd'):
        return self.client.post('/customer/login', data={'username': user, 'password': pwd}, follow_redirects=True)

    def login_store(self, user='Manager1', pwd='adminpwd'):
        return self.client.post('/store/login', data={'username': user, 'password': pwd}, follow_redirects=True)

    def place_order(self, part_id=1, store_id=1, qty=2):
        self.client.post('/customer/cart/add', data={'part_id': str(part_id), 'store_id': str(store_id), 'qty': str(qty)})
        r = self.client.post('/customer/checkout', data={'method': 'Credit Card', 'card_type': 'Visa',
                                                         'card_number': '4111 1111 1111 1234', 'billing_address': '1 Test St'},
                             follow_redirects=True)
        m = re.search(r'order ID is (\d+)', r.get_data(as_text=True))
        return int(m.group(1)) if m else None

    # ---------- Customer mode ----------
    def test_01_every_page_loads(self):
        for url in ['/', '/part/1', '/customer/login', '/customer/register', '/store/login', '/part/9999']:
            r = self.client.get(url)
            self.assertIn(r.status_code, (200, 404), url)
        self.assertEqual(self.client.get('/part/9999').status_code, 404)
        self.login_customer()
        for url in ['/customer/cart', '/customer/history', '/customer/profile']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.login_store()
        for url in ['/store/orders', '/store/orders/log', '/store/purchase-orders', '/store/database', '/store/employees', '/store/reports']:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_02_search(self):
        html = self.client.get('/?search=brake').get_data(as_text=True)
        self.assertIn('BRK-1001', html)
        self.assertNotIn('ENG-1001', html)
        html = self.client.get('/?search=ELE-2001&store_id=2').get_data(as_text=True)
        self.assertIn('Alternator', html)
        self.assertNotIn('Denton Main Street</td>', html)

    def test_03_part_detail_shows_price_qty_condition(self):
        html = self.client.get('/part/8').get_data(as_text=True)
        self.assertIn('$189.00', html)
        self.assertIn('Rebuilt', html)
        self.assertIn('Lewisville Crossing', html)

    def test_04_register_and_login(self):
        r = self.client.post('/customer/register', data={
            'first_name': 'Test', 'last_name': 'User', 'email': 'test@example.com', 'phone': '1',
            'username': 'tester', 'password': 'secret123', 'street': '1 A St', 'city': 'Denton', 'state': 'TX',
            'zip': '76201', 'preferred_store_id': '1', 'make': 'Mazda', 'model': '3', 'year': '2019'}, follow_redirects=True)
        self.assertIn('created successfully', r.get_data(as_text=True))
        with self.db() as c:
            row = c.execute("SELECT password_hash FROM Customer WHERE username='tester'").fetchone()
            self.assertNotEqual(row[0], 'secret123')  # password is hashed
            self.assertEqual(c.execute("SELECT COUNT(*) FROM Customer_Vehicle v JOIN Customer c ON v.customer_id=c.customer_id WHERE c.username='tester'").fetchone()[0], 1)
        # duplicate username is rejected
        r = self.client.post('/customer/register', data={
            'first_name': 'X', 'last_name': 'Y', 'email': 'other@example.com', 'username': 'tester', 'password': 'secret123',
            'street': 's', 'city': 'c', 'state': 'TX', 'zip': '1', 'preferred_store_id': '1'}, follow_redirects=True)
        self.assertIn('already exists', r.get_data(as_text=True))
        self.assertIn('Welcome back', self.login_customer('tester', 'secret123').get_data(as_text=True))
        self.assertIn('Invalid username or password', self.login_customer('tester', 'wrong').get_data(as_text=True))

    def test_05_checkout_decrements_stock_and_stores_last4(self):
        self.login_customer()
        before = self.stock(1, 1)
        order_id = self.place_order(part_id=1, store_id=1, qty=2)
        self.assertIsNotNone(order_id)
        self.assertEqual(self.stock(1, 1), before - 2)
        with self.db() as c:
            pay = c.execute("SELECT * FROM Payment WHERE order_id=?", (order_id,)).fetchone()
            self.assertEqual(pay['card_last4'], '1234')
            self.assertAlmostEqual(pay['amount'], 2 * 54.99, places=2)
            self.assertEqual(c.execute("SELECT status FROM Delivery WHERE order_id=?", (order_id,)).fetchone()[0], 'Pending')
        html = self.client.get('/customer/history').get_data(as_text=True)
        self.assertIn(f'#{order_id}', html)

    def test_06_cannot_buy_more_than_stock(self):
        self.login_customer()
        self.client.post('/customer/cart/add', data={'part_id': '9', 'store_id': '1', 'qty': '50'})
        r = self.client.post('/customer/checkout', data={'card_number': '4111111111111111'}, follow_redirects=True)
        self.assertIn('Insufficient stock', r.get_data(as_text=True))

    def test_07_invalid_card_rejected(self):
        self.login_customer()
        self.client.post('/customer/cart/add', data={'part_id': '1', 'store_id': '1', 'qty': '1'})
        r = self.client.post('/customer/checkout', data={'card_number': 'abc'}, follow_redirects=True)
        self.assertIn('valid card number', r.get_data(as_text=True))

    def test_08_one_store_per_cart_and_clear(self):
        self.login_customer()
        self.client.post('/customer/cart/add', data={'part_id': '1', 'store_id': '1', 'qty': '1'})
        r = self.client.post('/customer/cart/add', data={'part_id': '1', 'store_id': '2', 'qty': '1'}, follow_redirects=True)
        self.assertIn('one store at a time', r.get_data(as_text=True))
        r = self.client.post('/customer/cart', data={'clear_cart': '1'}, follow_redirects=True)
        self.assertIn('cart is empty', r.get_data(as_text=True))

    def test_09_customer_cancel_restocks(self):
        self.login_customer()
        before = self.stock(1, 1)
        order_id = self.place_order(qty=3)
        self.client.post(f'/customer/cancel/{order_id}')
        self.assertEqual(self.stock(1, 1), before)
        with self.db() as c:
            self.assertEqual(c.execute("SELECT status FROM Orders WHERE order_id=?", (order_id,)).fetchone()[0], 'Cancelled')
            self.assertEqual(c.execute("SELECT status FROM Payment WHERE order_id=?", (order_id,)).fetchone()[0], 'Refunded')

    def test_10_profile_update_and_vehicle(self):
        self.login_customer()
        self.client.post('/customer/profile', data={'update_profile': '1', 'first_name': 'Johnny', 'last_name': 'Smith',
                                                    'email': 'john.smith@example.com', 'phone': '000', 'street': '9 New St',
                                                    'city': 'Denton', 'state': 'TX', 'zip': '76201', 'preferred_store_id': '2'})
        self.client.post('/customer/profile', data={'add_vehicle': '1', 'make': 'Kia', 'model': 'Soul', 'year': '2021'})
        with self.db() as c:
            row = c.execute("SELECT * FROM Customer WHERE username='customer1'").fetchone()
            self.assertEqual(row['first_name'], 'Johnny')
            self.assertEqual(row['preferred_store_id'], 2)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM Customer_Vehicle WHERE customer_id=?", (row['customer_id'],)).fetchone()[0], 3)

    def test_11_customer_pages_require_login(self):
        r = self.client.get('/customer/history')
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/store/reports')
        self.assertEqual(r.status_code, 302)

    # ---------- Store mode ----------
    def test_12_store_login(self):
        self.assertIn('Store login successful', self.login_store().get_data(as_text=True))
        self.assertIn('Invalid store credentials', self.login_store('Manager1', 'nope').get_data(as_text=True))

    def test_13_delivery_status_flow(self):
        self.login_customer()
        order_id = self.place_order()
        self.login_store('Staff2', 'staffpwd')
        self.client.post('/store/orders', data={'action': 'update_delivery', 'order_id': order_id, 'delivery_status': 'Shipped', 'tracking_number': 'TRK-T1'})
        with self.db() as c:
            d = c.execute("SELECT * FROM Delivery WHERE order_id=?", (order_id,)).fetchone()
            self.assertEqual(d['status'], 'Shipped')
            self.assertIsNotNone(d['ship_date'])
            self.assertEqual(c.execute("SELECT status FROM Orders WHERE order_id=?", (order_id,)).fetchone()[0], 'Shipped')
        r = self.client.post('/store/orders', data={'action': 'update_delivery', 'order_id': order_id, 'delivery_status': 'Pending', 'tracking_number': 'TRK-T1'}, follow_redirects=True)
        self.assertIn('Cannot revert', r.get_data(as_text=True))
        self.client.post('/store/orders', data={'action': 'update_delivery', 'order_id': order_id, 'delivery_status': 'Delivered', 'tracking_number': 'TRK-T1'})
        with self.db() as c:
            d = c.execute("SELECT * FROM Delivery WHERE order_id=?", (order_id,)).fetchone()
            self.assertEqual(d['status'], 'Delivered')
            self.assertIsNotNone(d['delivery_date'])

    def test_14_store_cancel_restocks(self):
        self.login_customer()
        before = self.stock(1, 1)
        order_id = self.place_order(qty=1)
        self.login_store()
        self.client.post('/store/orders', data={'action': 'update_delivery', 'order_id': order_id, 'delivery_status': 'Cancelled', 'tracking_number': ''})
        self.assertEqual(self.stock(1, 1), before)

    def test_15_return_processing(self):
        self.login_store()
        before = self.stock(1, 10)
        # Order 4 in sample data: 4 spark plugs (part 10) at store 1
        r = self.client.post('/store/orders', data={'action': 'process_return', 'order_part': '4:10', 'quantity': '2', 'reason': 'Extra'}, follow_redirects=True)
        self.assertIn('Return processed', r.get_data(as_text=True))
        self.assertEqual(self.stock(1, 10), before + 2)
        # cannot return more than was bought in total
        r = self.client.post('/store/orders', data={'action': 'process_return', 'order_part': '4:10', 'quantity': '3', 'reason': 'Too many'}, follow_redirects=True)
        self.assertIn('Invalid return quantity', r.get_data(as_text=True))

    def test_16_purchase_orders(self):
        self.login_store()
        before = self.stock(2, 9)
        self.client.post('/store/purchase-orders', data={'action': 'create_po', 'po_type': 'Reorder', 'store_id': '2', 'supplier_id': '3',
                                                         'part_id': '9', 'quantity': '6', 'unit_cost': '80', 'expected_date': '2026-12-01'})
        with self.db() as c:
            po_id = c.execute("SELECT MAX(po_id) FROM Purchase_Order").fetchone()[0]
        self.client.post('/store/purchase-orders', data={'action': 'update_po', 'po_id': po_id, 'status': 'Received'})
        self.assertEqual(self.stock(2, 9), before + 6)
        # a received order cannot be stopped afterwards
        r = self.client.post('/store/purchase-orders', data={'action': 'update_po', 'po_id': po_id, 'status': 'Stopped'}, follow_redirects=True)
        self.assertIn('Only open purchase orders', r.get_data(as_text=True))
        # stop the open sample PO #2; inventory unchanged
        before = self.stock(1, 8)
        self.client.post('/store/purchase-orders', data={'action': 'update_po', 'po_id': 2, 'status': 'Stopped'})
        self.assertEqual(self.stock(1, 8), before)
        with self.db() as c:
            self.assertEqual(c.execute("SELECT status FROM Purchase_Order WHERE po_id=2").fetchone()[0], 'Stopped')

    def test_17_parts_inventory_and_new_store(self):
        self.login_store()
        self.client.post('/store/database', data={'action': 'add_part', 'part_number': 'TST-1', 'part_name': 'Test Part', 'category': 'Test',
                                                  'description': '', 'part_condition': 'New', 'unit_price': '9.99', 'supplier_id': '1'})
        r = self.client.post('/store/database', data={'action': 'add_part', 'part_number': 'TST-1', 'part_name': 'Dup', 'category': '',
                                                      'description': '', 'part_condition': 'New', 'unit_price': '1', 'supplier_id': '1'}, follow_redirects=True)
        self.assertIn('already exists', r.get_data(as_text=True))
        self.client.post('/store/database', data={'action': 'update_part', 'part_id': '1', 'part_name': 'Ceramic Brake Pads (Front)', 'unit_price': '59.99', 'part_condition': 'New'})
        self.client.post('/store/database', data={'action': 'update_inventory', 'store_id': '1', 'part_id': '1', 'quantity': '99', 'reorder_level': '7'})
        r = self.client.post('/store/database', data={'action': 'update_inventory', 'store_id': '1', 'part_id': '1', 'quantity': '-5', 'reorder_level': '7'}, follow_redirects=True)
        self.assertIn('must be whole numbers', r.get_data(as_text=True))
        self.client.post('/store/database', data={'action': 'add_store', 'store_name': 'Frisco Branch', 'street': '1 Main', 'city': 'Frisco', 'state': 'TX', 'zip': '75034', 'phone': '1'})
        with self.db() as c:
            self.assertEqual(c.execute("SELECT unit_price FROM Part WHERE part_id=1").fetchone()[0], 59.99)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM Inventory WHERE part_id=(SELECT part_id FROM Part WHERE part_number='TST-1')").fetchone()[0], 3)  # 2 original stores + Frisco
            new_store = c.execute("SELECT store_id FROM Store WHERE store_name='Frisco Branch'").fetchone()[0]
            self.assertEqual(c.execute("SELECT COUNT(*) FROM Inventory WHERE store_id=?", (new_store,)).fetchone()[0], 13)
        self.assertEqual(self.stock(1, 1), 99)
        self.assertIn('Frisco Branch', self.client.get('/').get_data(as_text=True))

    def test_18_employee_management_manager_only(self):
        self.login_store('Staff1', 'staffpwd')
        r = self.client.post('/store/employees', data={'action': 'add'}, follow_redirects=True)
        self.assertIn('Permission Denied', r.get_data(as_text=True))
        self.login_store()
        self.client.post('/store/employees', data={'action': 'add', 'store_id': '1', 'manager_id': '1', 'first_name': 'New', 'last_name': 'Hire',
                                                   'department': 'Sales', 'role': 'Sales Associate', 'phone': '', 'email': '',
                                                   'username': 'newhire', 'password': 'pass1234'})
        self.client.post('/store/employees', data={'action': 'add', 'store_id': '1', 'first_name': 'Second', 'last_name': 'Hire',
                                                   'department': 'Sales', 'role': 'Sales Associate', 'phone': '', 'email': '',
                                                   'username': 'newhire2', 'password': 'pass1234'})
        with self.db() as c:
            new_id = c.execute("SELECT employee_id FROM Employee WHERE username='newhire'").fetchone()[0]
            self.assertIsNotNone(c.execute("SELECT 1 FROM Employee WHERE username='newhire2'").fetchone())
        self.client.post('/store/employees', data={'action': 'edit', 'employee_id': new_id, 'department': 'Shipping', 'role': 'Delivery Clerk', 'store_id': '2', 'status': 'Inactive'})
        with self.db() as c:
            row = c.execute("SELECT * FROM Employee WHERE employee_id=?", (new_id,)).fetchone()
            self.assertEqual((row['department'], row['store_id'], row['status']), ('Shipping', 2, 'Inactive'))
        # inactive employees cannot log in
        self.assertIn('Invalid store credentials', self.login_store('newhire', 'pass1234').get_data(as_text=True))
        self.login_store()
        self.client.post('/store/employees', data={'action': 'delete', 'employee_id': new_id})
        r = self.client.post('/store/employees', data={'action': 'delete', 'employee_id': '1'}, follow_redirects=True)
        self.assertIn('Cannot delete your own account', r.get_data(as_text=True))
        with self.db() as c:
            self.assertIsNone(c.execute("SELECT 1 FROM Employee WHERE employee_id=?", (new_id,)).fetchone())

    def test_19_reports_have_data(self):
        self.login_store()
        html = self.client.get('/store/reports').get_data(as_text=True)
        for heading in ['Low Stock', 'Daily Sales', 'Weekly Sales', 'Monthly Sales', 'Part Sales', 'Inventory Value', 'Returns', 'Employee Status']:
            self.assertIn(heading, html)
        self.assertIn('Wrong viscosity', html)
        with self.db() as c:
            for v in ['v_daily_sales', 'v_weekly_sales', 'v_monthly_sales', 'v_low_stock', 'v_employee_status', 'v_part_sales', 'v_inventory_value', 'v_returns']:
                self.assertGreater(c.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0], 0, v)

    def test_20_constraints(self):
        with self.db() as c:
            c.execute("PRAGMA foreign_keys = ON")
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("UPDATE Inventory SET quantity = -1 WHERE store_id=1 AND part_id=1")
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("INSERT INTO Part (part_number, part_name, part_condition, unit_price) VALUES ('X', 'X', 'Used', 1)")
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("INSERT INTO Orders (customer_id, store_id, total_amount) VALUES (999, 1, 0)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
