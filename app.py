from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import bcrypt
import razorpay
import secrets

load_dotenv()

app = Flask(__name__)

# ── Session ──────────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}})

# ── Razorpay ─────────────────────────────────────────────────────────────────
razorpay_client = razorpay.Client(auth=(
    os.getenv('RAZORPAY_KEY_ID', 'your_razorpay_key_id'),
    os.getenv('RAZORPAY_KEY_SECRET', 'your_razorpay_key_secret')
))

# ── SQLite ───────────────────────────────────────────────────────────────────
DB_PATH = os.getenv('DB_PATH', 'crochet.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                email      TEXT    UNIQUE NOT NULL,
                password   TEXT    NOT NULL,
                phone      TEXT    NOT NULL,
                address    TEXT    DEFAULT '',
                created_at TEXT    DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS category (
                categoryId   INTEGER PRIMARY KEY AUTOINCREMENT,
                categoryName TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS product (
                productId   INTEGER PRIMARY KEY AUTOINCREMENT,
                productName TEXT    NOT NULL,
                price       REAL    NOT NULL DEFAULT 0,
                quantity    INTEGER NOT NULL DEFAULT 0,
                categoryId  INTEGER REFERENCES category(categoryId)
            );
            CREATE TABLE IF NOT EXISTS customer (
                customerId INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                phoneNo    TEXT NOT NULL,
                address    TEXT NOT NULL,
                email      TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                orderId        INTEGER PRIMARY KEY AUTOINCREMENT,
                orderNote      TEXT,
                customerId     INTEGER REFERENCES customer(customerId),
                orderDate      TEXT    DEFAULT (datetime('now')),
                payment_id     TEXT,
                total_amount   REAL    DEFAULT 0,
                payment_status TEXT    DEFAULT 'pending'
            );
            CREATE TABLE IF NOT EXISTS order_product (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                orderId   INTEGER REFERENCES orders(orderId),
                productId INTEGER REFERENCES product(productId),
                quantity  INTEGER NOT NULL,
                subtotal  REAL    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contact (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                email           TEXT NOT NULL,
                message         TEXT NOT NULL,
                submission_date TEXT DEFAULT (datetime('now'))
            );
        """)
        count = conn.execute("SELECT COUNT(*) FROM category").fetchone()[0]
        if count == 0:
            conn.executemany("INSERT INTO category (categoryName) VALUES (?)", [
                ('Children',), ('Bags',), ('Accessories',),
                ('Clothes',), ('Toys',), ('Gift Items',)
            ])
        conn.commit()
    print(f"SQLite ready → {DB_PATH}")

init_db()

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ── Health check ─────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Server is running!"})

# ── Register ─────────────────────────────────────────────────────────────────
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data     = request.get_json(force=True)
        name     = data.get('name', '').strip()
        email    = data.get('email', '').strip()
        password = data.get('password', '')
        phone    = data.get('phone', '').strip()
        address  = data.get('address', '').strip()

        if not all([name, email, password, phone]):
            return jsonify({"error": "Missing required fields"}), 400

        with get_db() as conn:
            if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                return jsonify({"error": "User already exists"}), 400
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn.execute(
                "INSERT INTO users (name, email, password, phone, address) VALUES (?,?,?,?,?)",
                (name, email, hashed, phone, address)
            )
            conn.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({"error": str(e)}), 500

# ── Login ─────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data     = request.get_json(force=True)
        email    = data.get('email', '').strip()
        password = data.get('password', '')

        if not all([email, password]):
            return jsonify({"error": "Email and password required"}), 400

        with get_db() as conn:
            user = row_to_dict(
                conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            )

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({"error": "Invalid credentials"}), 401

        session['user_id']    = user['id']
        session['user_name']  = user['name']
        session['user_email'] = user['email']

        return jsonify({
            "message": "Login successful",
            "user": {"id": user['id'], "name": user['name'], "email": user['email']}
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": str(e)}), 500

# ── Logout ────────────────────────────────────────────────────────────────────
@app.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return '', 200
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# ── Auth status ───────────────────────────────────────────────────────────────
@app.route('/auth/status', methods=['GET'])
def auth_status():
    if 'user_id' in session:
        return jsonify({
            "authenticated": True,
            "user": {
                "id":    session['user_id'],
                "name":  session['user_name'],
                "email": session['user_email']
            }
        }), 200
    return jsonify({"authenticated": False}), 200

# ── Razorpay: create order ────────────────────────────────────────────────────
@app.route('/create_payment_order', methods=['POST', 'OPTIONS'])
def create_payment_order():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data   = request.get_json(force=True)
        amount = data.get('amount')
        if not amount:
            return jsonify({"error": "Amount is required"}), 400

        rz_order = razorpay_client.order.create(data={
            'amount':          int(amount),
            'currency':        'INR',
            'receipt':         f'order_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'payment_capture': 1
        })
        return jsonify({
            "order_id": rz_order['id'],
            "amount":   rz_order['amount'],
            "currency": rz_order['currency'],
            "key_id":   os.getenv('RAZORPAY_KEY_ID')
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Razorpay: verify payment ──────────────────────────────────────────────────
@app.route('/verify_payment', methods=['POST', 'OPTIONS'])
def verify_payment():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json(force=True)
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id':   data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature':  data.get('razorpay_signature')
        })
        return jsonify({"status": "success", "message": "Payment verified"}), 200
    except Exception as e:
        return jsonify({"error": "Payment verification failed", "message": str(e)}), 400

# ── Categories ────────────────────────────────────────────────────────────────
@app.route('/categories', methods=['GET', 'PUT', 'OPTIONS'])
def categories():
    if request.method == 'OPTIONS':
        return '', 200
    if request.method == 'GET':
        with get_db() as conn:
            return jsonify(rows_to_list(conn.execute("SELECT * FROM category").fetchall()))
    try:
        new_cats = request.get_json()
        if not isinstance(new_cats, list):
            return jsonify({"error": "Expected a list"}), 400
        with get_db() as conn:
            conn.execute("DELETE FROM category")
            for cat in new_cats:
                conn.execute(
                    "INSERT INTO category (categoryId, categoryName) VALUES (?,?)",
                    (cat.get('categoryId'), cat.get('categoryName'))
                )
            conn.commit()
        return jsonify({"message": "Categories updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Products ──────────────────────────────────────────────────────────────────
@app.route('/products', methods=['GET'])
def get_products():
    with get_db() as conn:
        return jsonify(rows_to_list(conn.execute("SELECT * FROM product").fetchall()))

@app.route('/products/<int:category_id>', methods=['GET'])
def get_products_by_category(category_id):
    with get_db() as conn:
        return jsonify(rows_to_list(
            conn.execute("SELECT * FROM product WHERE categoryId = ?", (category_id,)).fetchall()
        ))

# ── Submit order ──────────────────────────────────────────────────────────────
@app.route('/submit_order', methods=['POST', 'OPTIONS'])
def submit_order():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data         = request.get_json(force=True)
        note         = data.get('note', '')
        cart         = data.get('cart', [])
        payment_id   = data.get('payment_id')
        total_amount = data.get('total_amount', 0)

        if not cart:
            return jsonify({"error": "Cart is empty"}), 400
        if not payment_id:
            return jsonify({"error": "Payment ID is required"}), 400

        # Accept user_id from session OR from request body (localStorage fallback)
        user_id = session.get('user_id') or data.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        with get_db() as conn:
            user = row_to_dict(
                conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            )
            if not user:
                return jsonify({"error": "User not found"}), 404

            cur = conn.execute(
                "INSERT INTO customer (name, phoneNo, address, email) VALUES (?,?,?,?)",
                (user['name'], user['phone'], user.get('address', ''), user['email'])
            )
            customer_id = cur.lastrowid

            cur = conn.execute(
                """INSERT INTO orders (orderNote, customerId, orderDate, payment_id, total_amount, payment_status)
                   VALUES (?,?,?,?,?,?)""",
                (note, customer_id, datetime.now().isoformat(), payment_id, total_amount, 'completed')
            )
            order_id = cur.lastrowid

            for item in cart:
                cur = conn.execute(
                    "INSERT INTO product (productName, price, quantity, categoryId) VALUES (?,?,?,?)",
                    (item.get('productName', 'Custom Product'),
                     item.get('price', 0.0),
                     item.get('quantity', 1),
                     item.get('categoryId', 1))
                )
                conn.execute(
                    "INSERT INTO order_product (orderId, productId, quantity, subtotal) VALUES (?,?,?,?)",
                    (order_id, cur.lastrowid, item['quantity'], item['subtotal'])
                )
            conn.commit()

        return jsonify({"status": "success", "message": "Order placed successfully",
                        "orderId": order_id, "customerId": customer_id})

    except Exception as e:
        print(f"submit_order error: {e}")
        return jsonify({"error": "Server error", "message": str(e)}), 500

# ── Contact ───────────────────────────────────────────────────────────────────
@app.route('/submit_contact', methods=['POST', 'OPTIONS'])
def submit_contact():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data    = request.get_json(force=True)
        name    = data.get('name', '').strip()
        email   = data.get('email', '').strip()
        message = data.get('message', '').strip()

        if not all([name, email, message]):
            return jsonify({"error": "Missing required fields"}), 400

        with get_db() as conn:
            conn.execute(
                "INSERT INTO contact (name, email, message) VALUES (?,?,?)",
                (name, email, message)
            )
            conn.commit()

        return jsonify({"status": "success", "message": "Message sent successfully"})

    except Exception as e:
        print(f"submit_contact error: {e}")
        return jsonify({"error": "Server error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
