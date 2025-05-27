from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# DB connection with error handling
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="shree@88",  # change if needed
        database="crochet"
    )
    cursor = db.cursor(dictionary=True)
    print("Database connection successful!")
except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
    exit(1)

# Load products data
def load_products():
    with open('products.json', 'r') as f:
        return json.load(f)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/api/products')
def get_products():
    products = load_products()
    return jsonify(products)

# Test route to verify server is running
@app.route('/', methods=['GET'])
def home_api():
    return jsonify({"message": "Server is running!"})

# Insert test data
@app.route('/insert_test_data', methods=['GET'])
def insert_test_data():
    try:
        # Insert categories
        categories = [
            ('Children',),
            ('Bags',),
            ('Accessories',),
            ('Clothes',),
            ('Toys',),
            ('Gift items',)
        ]
        cursor.executemany("INSERT INTO category (categoryName) VALUES (%s)", categories)
        db.commit()
        print("Categories inserted successfully")

        # Insert products
        products = [
            ('Woolen cord', 3999.99, 10, 1),
            ('Beach Bag', 2499.99, 15, 2),
            ('Earrings', 1999.99, 20, 3),
            ('Cradle hooks', 1499.99, 12, 4)
        ]
        cursor.executemany(
            "INSERT INTO product (productName, price, quantity, categoryId) VALUES (%s, %s, %s, %s)",
            products
        )
        db.commit()
        print("Products inserted successfully")

        return jsonify({"message": "Test data inserted successfully"})
    except Exception as e:
        db.rollback()
        print(f"Error inserting test data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get all categories
@app.route('/categories', methods=['GET'])
def get_categories():
    print("Categories endpoint called")  # Debug print
    try:
        # First, check if the category table exists
        cursor.execute("SHOW TABLES LIKE 'category'")
        if not cursor.fetchone():
            print("Category table does not exist! Creating it...")  # Debug print
            # Create category table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category (
                    categoryId INT PRIMARY KEY,
                    categoryName VARCHAR(100) NOT NULL
                )
            """)
            db.commit()
            print("Category table created successfully")

        # Then get all categories
        cursor.execute("SELECT * FROM category")
        categories = cursor.fetchall()
        print("Found categories:", categories)  # Debug print
        
        if not categories:
            print("No categories found in database, inserting default categories...")  # Debug print
            # Insert default categories if none exist
            default_categories = [
                (1, 'Children'),
                (2, 'Bags'),
                (3, 'Accessories'),
                (4, 'Clothes'),
                (5, 'Toys'),
                (6, 'Gift Items')
            ]
            cursor.executemany("INSERT INTO category (categoryId, categoryName) VALUES (%s, %s)", default_categories)
            db.commit()
            print("Inserted default categories")  # Debug print
            
            # Fetch categories again
            cursor.execute("SELECT * FROM category")
            categories = cursor.fetchall()
            print("Categories after insertion:", categories)  # Debug print

        return jsonify(categories)
    except Exception as e:
        print(f"Error getting categories: {str(e)}")  # Debug print
        return jsonify({"error": str(e)}), 500

# Get all products
@app.route('/products', methods=['GET'])
def get_products_api():
    if request.method != 'GET':
        return jsonify({"error": "Method not allowed. Use GET method."}), 405
    try:
        cursor.execute("SELECT * FROM product")
        products = cursor.fetchall()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get products by category
@app.route('/products/<int:category_id>', methods=['GET'])
def get_products_by_category(category_id):
    if request.method != 'GET':
        return jsonify({"error": "Method not allowed. Use GET method."}), 405
    try:
        cursor.execute("SELECT * FROM product WHERE categoryId = %s", (category_id,))
        products = cursor.fetchall()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Debug route to check available products
@app.route('/debug/products', methods=['GET'])
def debug_products():
    try:
        cursor.execute("SELECT productId, productName, price FROM product")
        products = cursor.fetchall()
        return jsonify({
            "message": "Available products",
            "products": products
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/categories', methods=['GET', 'PUT'])
def categories():
    if request.method == 'GET':
        # Your existing code to fetch categories
        cursor.execute("SELECT * FROM category")
        categories = cursor.fetchall()
        return jsonify(categories)

    elif request.method == 'PUT':
        try:
            new_categories = request.get_json()
            if not isinstance(new_categories, list):
                return jsonify({"error": "Expected a list of categories"}), 400
            
            # Optional: clear the existing categories first
            cursor.execute("DELETE FROM category")
            db.commit()

            # Insert new categories
            for category in new_categories:
                categoryId = category.get('categoryId')
                categoryName = category.get('categoryName')
                if categoryId is None or categoryName is None:
                    return jsonify({"error": "Missing categoryId or categoryName"}), 400
                
                cursor.execute(
                    "INSERT INTO category (categoryId, categoryName) VALUES (%s, %s)",
                    (categoryId, categoryName)
                )
            db.commit()

            return jsonify({"message": "Categories updated successfully"})

        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

@app.route('/submit_order', methods=['POST', 'OPTIONS'])
def submit_order():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 200

    print("Received request headers:", dict(request.headers))  # Debug print
    
    try:
        # Try to get JSON data regardless of content type
        data = request.get_json(force=True)
        print("Received order data:", data)  # Debug print

        if data is None:
            return jsonify({
                "error": "Invalid JSON",
                "message": "Request body must be valid JSON"
            }), 400

        # Extract data
        name = data.get('name')
        phone = data.get('phone')
        address = data.get('address')
        email = data.get('email')
        note = data.get('note', '')
        cart = data.get('cart', [])

        # Validate required fields
        missing_fields = []
        if not name: missing_fields.append('name')
        if not phone: missing_fields.append('phone')
        if not address: missing_fields.append('address')
        if not email: missing_fields.append('email')
        if not cart: missing_fields.append('cart')

        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }), 400

        # Step 1: Insert customer
        cursor.execute("""
            INSERT INTO customer (name, phoneNo, address, email) 
            VALUES (%s, %s, %s, %s)
        """, (name, phone, address, email))
        db.commit()
        customer_id = cursor.lastrowid
        print(f"Created customer with ID: {customer_id}")  # Debug print

        # Step 2: Create order
        cursor.execute("""
            INSERT INTO `order` (orderNote, customerId, orderDate) 
            VALUES (%s, %s, %s)
        """, (note, customer_id, datetime.now()))
        db.commit()
        order_id = cursor.lastrowid
        print(f"Created order with ID: {order_id}")  # Debug print

        # Step 3: Create products and insert into order_product
        for item in cart:
            # Create new product
            cursor.execute("""
                INSERT INTO product (productName, price, quantity, categoryId) 
                VALUES (%s, %s, %s, %s)
            """, (
                item.get('productName', 'Custom Product'),
                item.get('price', 0.0),
                item.get('quantity', 1),
                item.get('categoryId', 1)  # Default category ID
            ))
            db.commit()
            product_id = cursor.lastrowid

            # Add to order_product
            cursor.execute("""
                INSERT INTO order_product (orderId, productId, quantity, subtotal) 
                VALUES (%s, %s, %s, %s)
            """, (order_id, product_id, item['quantity'], item['subtotal']))
            db.commit()

        print("Order products inserted successfully")  # Debug print

        return jsonify({
            "status": "success",
            "message": "Order placed successfully",
            "orderId": order_id,
            "customerId": customer_id
        })

    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")  # Debug print
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500

@app.route('/submit_contact', methods=['POST', 'OPTIONS'])
def submit_contact():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json(force=True)
        print("Received contact data:", data)  # Debug print

        if data is None:
            return jsonify({
                "error": "Invalid JSON",
                "message": "Request body must be valid JSON"
            }), 400

        # Extract data
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')

        # Validate required fields
        missing_fields = []
        if not name: missing_fields.append('name')
        if not email: missing_fields.append('email')
        if not message: missing_fields.append('message')

        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }), 400

        # Create contact table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                submission_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

        # Insert contact form data
        cursor.execute("""
            INSERT INTO contact (name, email, message) 
            VALUES (%s, %s, %s)
        """, (name, email, message))
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Message sent successfully"
        })

    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")  # Debug print
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
