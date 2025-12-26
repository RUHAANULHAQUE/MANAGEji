import streamlit as st
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from contextlib import contextmanager

# ============== DATABASE SETUP ==============

DB_NAME = "pos_system.db"

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database with all required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                inventory INTEGER DEFAULT 0,
                category TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                loyalty_points INTEGER DEFAULT 0,
                total_spend REAL DEFAULT 0,
                order_count INTEGER DEFAULT 0,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                customer_id TEXT,
                subtotal REAL NOT NULL,
                discount REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                tip REAL DEFAULT 0,
                total REAL NOT NULL,
                payment_method TEXT,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transaction items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                product_id TEXT,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                data TEXT,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id)
            )
        """)
        
        conn.commit()

# ============== DATABASE OPERATIONS ==============

class ConfigDB:
    @staticmethod
    def get():
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                result = cursor.execute("SELECT data FROM config WHERE id = 1").fetchone()
                if result:
                    return json.loads(result['data'])
            except Exception:
                return None
            return None
    
    @staticmethod
    def save(config_data):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config (id, data) VALUES (1, ?)
            """, (json.dumps(config_data),))
            conn.commit()

class ProductDB:
    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            results = cursor.execute("SELECT * FROM products ORDER BY name").fetchall()
            products = []
            for row in results:
                product = json.loads(row['data']) if row['data'] else {}
                product.update({
                    'id': row['id'],
                    'name': row['name'],
                    'price': row['price'],
                    'inventory': row['inventory'],
                    'category': row['category']
                })
                products.append(product)
            return products
    
    @staticmethod
    def get_by_id(product_id):
        with get_db() as conn:
            cursor = conn.cursor()
            result = cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if result:
                product = json.loads(result['data']) if result['data'] else {}
                product.update({
                    'id': result['id'],
                    'name': result['name'],
                    'price': result['price'],
                    'inventory': result['inventory'],
                    'category': result['category']
                })
                return product
        return None
    
    @staticmethod
    def add(product_data):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (id, name, price, inventory, category, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                product_data['id'],
                product_data['name'],
                product_data['price'],
                product_data.get('inventory', 0),
                product_data.get('category', 'General'),
                json.dumps(product_data)
            ))
            conn.commit()
    
    @staticmethod
    def update(product_data):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products 
                SET name = ?, price = ?, inventory = ?, category = ?, data = ?
                WHERE id = ?
            """, (
                product_data['name'],
                product_data['price'],
                product_data.get('inventory', 0),
                product_data.get('category', 'General'),
                json.dumps(product_data),
                product_data['id']
            ))
            conn.commit()
    
    @staticmethod
    def delete(product_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
    
    @staticmethod
    def update_inventory(product_id, quantity_change):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products 
                SET inventory = inventory + ?
                WHERE id = ?
            """, (quantity_change, product_id))
            conn.commit()

class CustomerDB:
    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            results = cursor.execute("SELECT * FROM customers ORDER BY name").fetchall()
            customers = []
            for row in results:
                customer = json.loads(row['data']) if row['data'] else {}
                customer.update({
                    'id': row['id'],
                    'name': row['name'],
                    'email': row['email'],
                    'phone': row['phone'],
                    'loyalty_points': row['loyalty_points'],
                    'total_spend': row['total_spend'],
                    'order_count': row['order_count']
                })
                customers.append(customer)
            return customers
    
    @staticmethod
    def get_by_id(customer_id):
        with get_db() as conn:
            cursor = conn.cursor()
            result = cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
            if result:
                customer = json.loads(result['data']) if result['data'] else {}
                customer.update({
                    'id': result['id'],
                    'name': result['name'],
                    'email': result['email'],
                    'phone': result['phone'],
                    'loyalty_points': result['loyalty_points'],
                    'total_spend': result['total_spend'],
                    'order_count': result['order_count']
                })
                return customer
        return None
    
    @staticmethod
    def add(customer_data):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (id, name, email, phone, loyalty_points, total_spend, order_count, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_data['id'],
                customer_data['name'],
                customer_data.get('email', ''),
                customer_data.get('phone', ''),
                customer_data.get('loyalty_points', 0),
                customer_data.get('total_spend', 0),
                customer_data.get('order_count', 0),
                json.dumps(customer_data)
            ))
            conn.commit()
    
    @staticmethod
    def update(customer_data):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE customers 
                SET name = ?, email = ?, phone = ?, loyalty_points = ?, total_spend = ?, order_count = ?, data = ?
                WHERE id = ?
            """, (
                customer_data['name'],
                customer_data.get('email', ''),
                customer_data.get('phone', ''),
                customer_data.get('loyalty_points', 0),
                customer_data.get('total_spend', 0),
                customer_data.get('order_count', 0),
                json.dumps(customer_data),
                customer_data['id']
            ))
            conn.commit()
    
    @staticmethod
    def delete(customer_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
    
    @staticmethod
    def update_stats(customer_id, total_spent, loyalty_points):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE customers 
                SET total_spend = total_spend + ?, 
                    loyalty_points = loyalty_points + ?,
                    order_count = order_count + 1
                WHERE id = ?
            """, (total_spent, loyalty_points, customer_id))
            conn.commit()

class TransactionDB:
    @staticmethod
    def get_all(limit=None):
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM transactions ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"
            results = cursor.execute(query).fetchall()
            
            transactions = []
            for row in results:
                trans = json.loads(row['data']) if row['data'] else {}
                trans.update({
                    'id': row['id'],
                    'customer_id': row['customer_id'],
                    'subtotal': row['subtotal'],
                    'discount': row['discount'],
                    'tax': row['tax'],
                    'tip': row['tip'],
                    'total': row['total'],
                    'payment_method': row['payment_method'],
                    'timestamp': row['timestamp']
                })
                
                # Get items
                items = cursor.execute("""
                    SELECT * FROM transaction_items WHERE transaction_id = ?
                """, (row['id'],)).fetchall()
                
                trans['items'] = []
                for item in items:
                    item_data = json.loads(item['data']) if item['data'] else {}
                    item_data.update({
                        'product_name': item['product_name'],
                        'price': item['price'],
                        'cartQuantity': item['quantity']
                    })
                    trans['items'].append(item_data)
                
                transactions.append(trans)
            
            return transactions
    
    @staticmethod
    def get_todays_total():
        """Get total sales for today using SQL aggregation for performance"""
        with get_db() as conn:
            cursor = conn.cursor()
            # SQLite 'now', 'localtime' gets today's date in local time
            result = cursor.execute("""
                SELECT SUM(total) as total 
                FROM transactions 
                WHERE date(timestamp) = date('now', 'localtime')
            """).fetchone()
            return result['total'] if result and result['total'] else 0.0

    @staticmethod
    def add(transaction_data):
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Insert transaction
            cursor.execute("""
                INSERT INTO transactions (id, customer_id, subtotal, discount, tax, tip, total, payment_method, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_data['id'],
                transaction_data.get('customer_id'),
                transaction_data['subtotal'],
                transaction_data.get('discount', 0),
                transaction_data.get('tax', 0),
                transaction_data.get('tip', 0),
                transaction_data['total'],
                transaction_data.get('payment_method', 'Cash'),
                json.dumps(transaction_data),
                transaction_data['timestamp']
            ))
            
            # Insert transaction items
            for item in transaction_data['items']:
                cursor.execute("""
                    INSERT INTO transaction_items (transaction_id, product_id, product_name, price, quantity, data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    transaction_data['id'],
                    item.get('id'),
                    item['name'],
                    item['price'],
                    item['cartQuantity'],
                    json.dumps(item)
                ))
            
            conn.commit()
    
    @staticmethod
    def get_stats(days=30):
        # Improved SQL date handling
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as count,
                    SUM(total) as total_sales,
                    AVG(total) as avg_sale
                FROM transactions
                WHERE date(timestamp) >= date('now', '-{days} days')
            """)
            result = cursor.fetchone()
            
            cursor.execute(f"""
                SELECT SUM(quantity) as total_items
                FROM transaction_items ti
                JOIN transactions t ON ti.transaction_id = t.id
                WHERE date(t.timestamp) >= date('now', '-{days} days')
            """)
            items_result = cursor.fetchone()
            
            return {
                'transaction_count': result['count'] or 0,
                'total_sales': result['total_sales'] or 0.0,
                'avg_transaction': result['avg_sale'] or 0.0,
                'total_items_sold': items_result['total_items'] or 0
            }

# ============== CONFIGURATION ==============

STORE_TEMPLATES = {
    'cafe': {
        'name': 'Café/Coffee Shop',
        'icon': '☕',
        'fields': [
            {'id': 'name', 'type': 'text', 'label': 'Item', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'price', 'type': 'number', 'label': 'Price', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'size', 'type': 'select', 'label': 'Size', 'options': ['Small', 'Medium', 'Large'], 'required': False, 'showInCart': True, 'showInReceipt': True},
            {'id': 'category', 'type': 'select', 'label': 'Category', 'options': ['Coffee', 'Tea', 'Pastry', 'Sandwich'], 'required': False, 'showInCart': False, 'showInReceipt': False}
        ],
        'theme': {'primary': '#8B4513', 'secondary': '#D2691E', 'background': '#FFF8DC', 'accent': '#CD853F'},
        'taxRate': 8,
        'currency': '$'
    },
    'retail': {
        'name': 'Retail Store',
        'icon': '🏪',
        'fields': [
            {'id': 'name', 'type': 'text', 'label': 'Product Name', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'price', 'type': 'number', 'label': 'Price', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'category', 'type': 'select', 'label': 'Category', 'options': ['Electronics', 'Clothing', 'Home', 'Accessories'], 'required': False, 'showInCart': False, 'showInReceipt': False},
            {'id': 'sku', 'type': 'text', 'label': 'SKU', 'required': False, 'showInCart': False, 'showInReceipt': True},
        ],
        'theme': {'primary': '#2563eb', 'secondary': '#3b82f6', 'background': '#eff6ff', 'accent': '#60a5fa'},
        'taxRate': 10,
        'currency': '$'
    },
    'restaurant': {
        'name': 'Restaurant',
        'icon': '🍽️',
        'fields': [
            {'id': 'name', 'type': 'text', 'label': 'Dish', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'price', 'type': 'number', 'label': 'Price', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'category', 'type': 'select', 'label': 'Category', 'options': ['Appetizer', 'Main Course', 'Dessert', 'Beverage'], 'required': False, 'showInCart': False, 'showInReceipt': False},
            {'id': 'spiceLevel', 'type': 'select', 'label': 'Spice Level', 'options': ['Mild', 'Medium', 'Hot', 'Extra Hot'], 'required': False, 'showInCart': True, 'showInReceipt': True},
        ],
        'theme': {'primary': '#dc2626', 'secondary': '#ef4444', 'background': '#fef2f2', 'accent': '#f87171'},
        'taxRate': 8,
        'currency': '$'
    }
}

PAYMENT_METHODS = ['Cash', 'Credit Card', 'Debit Card', 'Mobile Payment', 'Gift Card']

# ============== SESSION STATE ==============

def init_session_state():
    defaults = {
        'screen': 'welcome',
        'cart': [],
        'setup_step': 1,
        'show_product_form': False,
        'show_customer_form': False,
        'edit_product': None,
        'edit_customer': None,
        'selected_category': 'All',
        'view_mode': 'grid',
        'last_transaction': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============== STYLING ==============

def apply_global_styles(config):
    # Handle None config (first run)
    theme = config['theme'] if config else STORE_TEMPLATES['cafe']['theme']
    primary = theme.get('primary', '#2563eb')
    background = theme.get('background', '#f8fafc')
    accent = theme.get('accent', '#60a5fa')
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background: linear-gradient(135deg, {background} 0%, #ffffff 100%);
    }}
    
    .metric-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid {primary};
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    
    .product-card {{
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        cursor: pointer;
        transition: all 0.2s;
        height: 100%;
    }}
    
    .product-card:hover {{
        border-color: {accent};
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }}
    
    .product-card.out-of-stock {{
        opacity: 0.6;
        border-color: #ef4444;
    }}
    
    .product-card.low-stock {{
        border-color: #f59e0b;
    }}
    
    .badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    
    .badge-success {{
        background: #d1fae5;
        color: #065f46;
    }}
    
    .badge-warning {{
        background: #fef3c7;
        color: #92400e;
    }}
    
    .badge-danger {{
        background: #fee2e2;
        color: #991b1b;
    }}
    
    .main-header {{
        background: linear-gradient(135deg, {primary} 0%, {accent} 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    
    .cart-item {{
        background: #f9fafb;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid {primary};
    }}
    
    .stat-number {{
        font-size: 2rem;
        font-weight: 700;
        color: {primary};
        margin: 0;
    }}
    
    .stat-label {{
        color: #6b7280;
        font-size: 0.875rem;
        margin: 0;
    }}
    
    .stButton > button {{
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# ============== HELPER FUNCTIONS ==============

def get_top_products(limit=5):
    with get_db() as conn:
        cursor = conn.cursor()
        results = cursor.execute("""
            SELECT 
                product_name as name,
                SUM(quantity) as quantity,
                SUM(price * quantity) as revenue
            FROM transaction_items
            GROUP BY product_name
            ORDER BY revenue DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        return [{'name': r['name'], 'quantity': r['quantity'], 'revenue': r['revenue']} for r in results]

def calculate_loyalty_points(total, rate=1):
    return int(total * rate)

# ============== WELCOME SCREEN ==============

def welcome_screen():
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
        <h1 style='font-size: 3.5rem; font-weight: 700; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;'>
            🏪 Universal POS Pro
        </h1>
        <p style='font-size: 1.5rem; color: #64748b; margin-bottom: 0.5rem;'>
            Next-Generation Point of Sale System
        </p>
        <p style='color: #94a3b8; font-size: 1.1rem;'>
            Complete business management with SQLite database, analytics, and customer insights
        </p>
    </div>
    """, unsafe_allow_html=True)
   
    col1, col2, col3, col4 = st.columns(4)
    features = [
        ("💾", "Database", "SQLite persistence"),
        ("📊", "Analytics", "Real-time insights"),
        ("📦", "Inventory", "Smart tracking"),
        ("👥", "Customers", "Loyalty system")
    ]
    
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(f"""
            <div class='metric-card' style='text-align: center;'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>{icon}</div>
                <h3 style='margin: 0; font-size: 1.1rem;'>{title}</h3>
                <p style='color: #6b7280; font-size: 0.875rem; margin: 0.5rem 0 0 0;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
   
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            st.session_state.screen = 'setup'
            st.rerun()

# ============== SETUP WIZARD ==============

def setup_wizard():
    st.progress((st.session_state.setup_step - 1) / 2)
    
    if st.session_state.setup_step == 1:
        st.markdown("<h2 style='text-align: center;'>Choose Your Business Type</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Select a template to get started quickly</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
       
        cols = st.columns(3)
        for idx, (key, template) in enumerate(STORE_TEMPLATES.items()):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class='product-card' style='text-align: center; min-height: 200px;'>
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>{template['icon']}</div>
                    <h3 style='margin: 0; color: #1f2937;'>{template['name']}</h3>
                    <p style='color: #6b7280; margin: 0.5rem 0;'>{len(template['fields'])} custom fields</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select", key=f"template_{key}", use_container_width=True, type="primary"):
                    config = {
                        'businessType': key,
                        'businessName': '',
                        'theme': template['theme'],
                        'fields': template['fields'].copy(),
                        'taxRate': template['taxRate'],
                        'currency': template['currency'],
                        'discountRate': 0,
                        'showTax': True,
                        'receiptFooter': 'Thank you for your business!',
                        'enableInventory': True,
                        'enableCustomers': True,
                        'enableLoyalty': True,
                        'loyaltyRate': 1,
                        'lowStockThreshold': 5
                    }
                    ConfigDB.save(config)
                    st.session_state.setup_step = 2
                    st.rerun()
   
    elif st.session_state.setup_step == 2:
        st.markdown("<h2 style='text-align: center;'>Configure Your Store</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
       
        config = ConfigDB.get()
        if not config:
            st.error("Configuration lost. Please restart setup.")
            st.session_state.setup_step = 1
            st.rerun()
       
        config['businessName'] = st.text_input("Business Name *", value=config.get('businessName', ''), 
                                               help="Your business name for receipts and branding")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            config['currency'] = st.text_input("Currency", value=config.get('currency', '$'), max_chars=3)
        with col2:
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), 
                                               min_value=0.0, max_value=100.0, step=0.5)
        with col3:
            config['lowStockThreshold'] = st.number_input("Low Stock Alert", value=5, min_value=1, step=1)
        
        st.markdown("#### Features")
        col1, col2, col3 = st.columns(3)
        with col1:
            config['enableInventory'] = st.checkbox("📦 Inventory Tracking", value=True)
        with col2:
            config['enableCustomers'] = st.checkbox("👥 Customer Database", value=True)
        with col3:
            config['enableLoyalty'] = st.checkbox("⭐ Loyalty Program", value=True)
        
        if config.get('enableInventory') and not any(f['id'] == 'inventory' for f in config['fields']):
            config['fields'].append({
                'id': 'inventory',
                'type': 'number',
                'label': 'Stock Quantity',
                'required': True,
                'showInCart': False,
                'showInReceipt': False,
                'default': 0
            })
       
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.setup_step = 1
                st.rerun()
        with col3:
            if st.button("Complete Setup ✓", type="primary", use_container_width=True):
                if not config.get('businessName'):
                    st.error("Please enter a business name")
                else:
                    ConfigDB.save(config)
                    st.session_state.screen = 'dashboard'
                    st.success("🎉 Setup complete! Data is now saved to SQLite database.")
                    st.rerun()

# ============== HEADER ==============

def header():
    config = ConfigDB.get()
    
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div class='main-header' style='padding: 1rem 1.5rem;'>
            <h2 style='margin: 0; color: white;'>{config.get('businessName', 'Universal POS Pro')}</h2>
            <p style='margin: 0; opacity: 0.9; font-size: 0.9rem;'>{datetime.now().strftime("%A, %B %d, %Y")}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Use SQL aggregation for accuracy
        today_sales = TransactionDB.get_todays_total()
        st.metric("Today's Sales", f"{config['currency']}{today_sales:.2f}")
    
    with col3:
        screens = ['Dashboard', 'POS', 'Products', 'Customers', 'Analytics', 'Settings']
        screen_map = {s: s.lower() for s in screens}
        
        current_idx = [s.lower() for s in screens].index(st.session_state.screen) if st.session_state.screen in [s.lower() for s in screens] else 0
        selected = st.selectbox("", screens, index=current_idx, label_visibility="collapsed")
        if screen_map[selected] != st.session_state.screen:
            st.session_state.screen = screen_map[selected]
            st.rerun()

# ============== DASHBOARD ==============

def dashboard():
    config = ConfigDB.get()
    
    # Use SQL for heavy lifting
    today_sales = TransactionDB.get_todays_total()
    stats = TransactionDB.get_stats(30)
    products = ProductDB.get_all()
    
    # Get recent transactions for today count
    with get_db() as conn:
        cursor = conn.cursor()
        today_count = cursor.execute("SELECT COUNT(*) as cnt FROM transactions WHERE date(timestamp) = date('now', 'localtime')").fetchone()['cnt']
    
    st.subheader("📊 Business Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='stat-label'>Today's Revenue</p>
            <p class='stat-number'>{config['currency']}{today_sales:.2f}</p>
            <p class='stat-label'>{today_count} transactions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='stat-label'>30-Day Revenue</p>
            <p class='stat-number'>{config['currency']}{stats['total_sales']:.2f}</p>
            <p class='stat-label'>{stats['transaction_count']} transactions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='stat-label'>Average Sale</p>
            <p class='stat-number'>{config['currency']}{stats['avg_transaction']:.2f}</p>
            <p class='stat-label'>Per transaction</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='stat-label'>Products</p>
            <p class='stat-number'>{len(products)}</p>
            <p class='stat-label'>In catalog</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick actions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🛒 New Sale", type="primary", use_container_width=True):
            st.session_state.screen = 'pos'
            st.rerun()
    with col2:
        if st.button("➕ Add Product", use_container_width=True):
            st.session_state.screen = 'products'
            st.session_state.show_product_form = True
            st.rerun()
    with col3:
        if st.button("👥 Customers", use_container_width=True):
            st.session_state.screen = 'customers'
            st.rerun()
    with col4:
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.screen = 'analytics'
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top Products")
        top_products = get_top_products(5)
        if top_products:
            for i, prod in enumerate(top_products):
                st.markdown(f"""
                <div class='cart-item'>
                    <strong>{i+1}. {prod['name']}</strong><br>
                    <span style='color: #6b7280;'>Sold: {prod['quantity']} | Revenue: {config['currency']}{prod['revenue']:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No sales data yet")
    
    with col2:
        st.subheader("⚠️ Inventory Alerts")
        if config.get('enableInventory'):
            threshold = config.get('lowStockThreshold', 5)
            low_stock = [p for p in products if 0 < p.get('inventory', 0) <= threshold]
            out_stock = [p for p in products if p.get('inventory', 0) <= 0]
            
            if out_stock:
                st.error(f"🚨 {len(out_stock)} products out of stock")
                for prod in out_stock[:5]:
                    st.markdown(f"• **{prod['name']}** - Restock needed")
            
            if low_stock:
                st.warning(f"⚡ {len(low_stock)} products low on stock")
                for prod in low_stock[:5]:
                    st.markdown(f"• **{prod['name']}** - Only {prod.get('inventory', 0)} left")
            
            if not low_stock and not out_stock:
                st.success("✅ All products well stocked!")
        else:
            st.info("Inventory tracking is disabled")

# ============== POS SCREEN ==============

def pos_screen():
    config = ConfigDB.get()
    products = ProductDB.get_all()
    cart = st.session_state.cart
    
    # Optimization: Map for O(1) lookup
    cart_map = {item['id']: item for item in cart}
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            search = st.text_input("🔍 Search products...", key="pos_search")
        with col_b:
            view_mode = st.radio("", ["Grid", "List"], horizontal=True, label_visibility="collapsed")
        
        filtered = [p for p in products if not search or search.lower() in p.get('name', '').lower()]
        
        if filtered:
            if view_mode == "Grid":
                for i in range(0, len(filtered), 3):
                    cols = st.columns(3)
                    for j, product in enumerate(filtered[i:i+3]):
                        with cols[j]:
                            stock = product.get('inventory', 999)
                            stock_class = 'out-of-stock' if stock <= 0 else 'low-stock' if stock <= config.get('lowStockThreshold', 5) else ''
                            
                            # Check cart quantity efficiently
                            in_cart_qty = cart_map.get(product['id'], {}).get('cartQuantity', 0)
                            
                            st.markdown(f"""
                            <div class='product-card {stock_class}'>
                                <h4 style='margin: 0 0 0.5rem 0;'>{product['name']}</h4>
                                <p style='color: #2563eb; font-size: 1.25rem; font-weight: 600; margin: 0;'>
                                    {config['currency']}{product['price']:.2f}
                                </p>
                                {f"<p style='color: #6b7280; font-size: 0.875rem; margin: 0.5rem 0 0 0;'>Stock: {stock}</p>" if config.get('enableInventory') else ""}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Add", key=f"add_{product['id']}", 
                                       disabled=stock <= 0 and config.get('enableInventory'), 
                                       use_container_width=True):
                                if product['id'] in cart_map:
                                    existing = cart_map[product['id']]
                                    max_stock = stock if config.get('enableInventory') else 999
                                    if existing['cartQuantity'] < max_stock:
                                        existing['cartQuantity'] += 1
                                    else:
                                        st.error("Not enough stock!")
                                else:
                                    cart.append({**product, 'cartQuantity': 1})
                                st.rerun()
            else:
                for product in filtered:
                    col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])
                    with col_a:
                        st.markdown(f"**{product['name']}**")
                    with col_b:
                        st.markdown(f"{config['currency']}{product['price']:.2f}")
                    with col_c:
                        if config.get('enableInventory'):
                            stock = product.get('inventory', 0)
                            st.markdown(f"Stock: {stock}")
                    with col_d:
                        if st.button("Add", key=f"add_list_{product['id']}", 
                                   disabled=product.get('inventory', 999) <= 0 and config.get('enableInventory')):
                            if product['id'] in cart_map:
                                cart_map[product['id']]['cartQuantity'] += 1
                            else:
                                cart.append({**product, 'cartQuantity': 1})
                            st.rerun()
        else:
            st.info("No products found")
    
    with col2:
        st.markdown(f"### 🛒 Cart ({len(cart)})")
        
        if config.get('enableCustomers'):
            customers = CustomerDB.get_all()
            customer_names = ['Guest'] + [c['name'] for c in customers]
            selected_customer = st.selectbox("Customer", customer_names, key="pos_customer")
        
        if cart:
            for item in cart:
                st.markdown(f"""
                <div class='cart-item'>
                    <strong>{item['name']}</strong><br>
                    <span style='color: #6b7280;'>{config['currency']}{item['price']:.2f} × {item['cartQuantity']}</span>
                    <strong style='float: right;'>{config['currency']}{(item['price'] * item['cartQuantity']):.2f}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_a:
                    if st.button("➖", key=f"dec_{item['id']}", use_container_width=True):
                        item['cartQuantity'] -= 1
                        if item['cartQuantity'] <= 0:
                            cart.remove(item)
                        st.rerun()
                with col_b:
                    if st.button("➕", key=f"inc_{item['id']}", use_container_width=True):
                        max_qty = item.get('inventory', 999) if config.get('enableInventory') else 999
                        if item['cartQuantity'] < max_qty:
                            item['cartQuantity'] += 1
                            st.rerun()
                with col_c:
                    if st.button("🗑️", key=f"del_{item['id']}", use_container_width=True):
                        cart.remove(item)
                        st.rerun()
            
            st.divider()
            
            subtotal = sum(item['price'] * item['cartQuantity'] for item in cart)
            
            discount_pct = st.number_input("Discount (%)", value=0.0, min_value=0.0, max_value=100.0, step=1.0)
            discount = subtotal * (discount_pct / 100)
            
            tip = st.number_input(f"Tip ({config['currency']})", value=0.0, min_value=0.0, step=1.0)
            
            taxable = subtotal - discount
            tax = taxable * (config['taxRate'] / 100)
            total = taxable + tax + tip
            
            st.markdown(f"""
            **Subtotal:** {config['currency']}{subtotal:.2f}<br>
            **Discount:** -{config['currency']}{discount:.2f}<br>
            **Tax ({config['taxRate']}%):** {config['currency']}{tax:.2f}<br>
            **Tip:** {config['currency']}{tip:.2f}<br>
            <h3 style='color: #2563eb;'>Total: {config['currency']}{total:.2f}</h3>
            """, unsafe_allow_html=True)
            
            payment_method = st.selectbox("Payment", PAYMENT_METHODS)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear", type="secondary", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()
            with col2:
                if st.button("Complete", type="primary", use_container_width=True):
                    customer_id = None
                    if config.get('enableCustomers') and selected_customer != 'Guest':
                        customer = next(c for c in customers if c['name'] == selected_customer)
                        customer_id = customer['id']
                        
                        # Update customer stats
                        loyalty_points = calculate_loyalty_points(total, config.get('loyaltyRate', 1)) if config.get('enableLoyalty') else 0
                        CustomerDB.update_stats(customer_id, total, loyalty_points)
                    
                    transaction = {
                        'id': str(datetime.now().timestamp()),
                        'items': [{**item} for item in cart],
                        'subtotal': subtotal,
                        'discount': discount,
                        'tax': tax,
                        'tip': tip,
                        'total': total,
                        'payment_method': payment_method,
                        'customer_id': customer_id,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    TransactionDB.add(transaction)
                    
                    # Update inventory in database
                    if config.get('enableInventory'):
                        for item in cart:
                            ProductDB.update_inventory(item['id'], -item['cartQuantity'])
                    
                    st.session_state.cart = []
                    st.session_state.last_transaction = transaction
                    st.session_state.screen = 'receipt'
                    st.success("✅ Transaction saved to database!")
                    st.rerun()
        else:
            st.info("Cart is empty")

# ============== PRODUCTS SCREEN ==============

def products_screen():
    config = ConfigDB.get()
    products = ProductDB.get_all()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📦 Products ({len(products)})")
    with col2:
        if st.button("➕ Add Product", type="primary", use_container_width=True):
            st.session_state.show_product_form = True
            st.session_state.edit_product = None
            st.rerun()
    
    if st.session_state.get('show_product_form'):
        with st.form("product_form"):
            st.subheader("Add/Edit Product")
            
            edit_prod = st.session_state.edit_product or {}
            product_data = {}
            
            col1, col2 = st.columns(2)
            with col1:
                product_data['name'] = st.text_input("Product Name *", value=edit_prod.get('name', ''))
                product_data['price'] = st.number_input("Price *", value=float(edit_prod.get('price', 0)), min_value=0.01, step=0.01, format="%.2f")
            with col2:
                if config.get('enableInventory'):
                    product_data['inventory'] = st.number_input("Stock *", value=int(edit_prod.get('inventory', 0)), min_value=0)
                
                categories = list(set(p.get('category', 'General') for p in products)) + ['General', 'New Category']
                product_data['category'] = st.selectbox("Category", categories, index=categories.index(edit_prod.get('category', 'General')) if edit_prod.get('category') in categories else 0)
            
            submitted = st.form_submit_button("Save", type="primary")
            cancelled = st.form_submit_button("Cancel")
            
            if cancelled:
                st.session_state.show_product_form = False
                st.rerun()
            
            if submitted:
                if not product_data['name'] or product_data['price'] <= 0:
                    st.error("Name and valid price required")
                else:
                    product_data['id'] = edit_prod.get('id', str(datetime.now().timestamp()))
                    
                    if st.session_state.edit_product:
                        ProductDB.update(product_data)
                        st.success("Product updated in database!")
                    else:
                        ProductDB.add(product_data)
                        st.success("Product added to database!")
                    
                    st.session_state.show_product_form = False
                    st.session_state.edit_product = None
                    st.rerun()
    
    search = st.text_input("🔍 Search products...")
    filtered = [p for p in products if not search or search.lower() in p.get('name', '').lower()]
    
    if filtered:
        for i in range(0, len(filtered), 3):
            cols = st.columns(3)
            for j, product in enumerate(filtered[i:i+3]):
                if j < len(cols):
                    with cols[j]:
                        stock = product.get('inventory', 0) if config.get('enableInventory') else None
                        stock_class = "danger" if stock == 0 else "warning" if stock and stock <= 5 else "success"
                        
                        st.markdown(f"""
                        <div class='product-card'>
                            <h4>{product['name']}</h4>
                            <p style='color: #2563eb; font-size: 1.25rem;'>{config['currency']}{product['price']:.2f}</p>
                            {f"<span class='badge badge-{stock_class}'>Stock: {stock}</span>" if stock is not None else ""}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Edit", key=f"edit_{product['id']}", use_container_width=True):
                                st.session_state.edit_product = product
                                st.session_state.show_product_form = True
                                st.rerun()
                        with col_b:
                            if st.button("Delete", key=f"del_{product['id']}", use_container_width=True):
                                ProductDB.delete(product['id'])
                                st.success("Deleted from database!")
                                st.rerun()
    else:
        st.info("No products found")

# ============== CUSTOMERS SCREEN ==============

def customers_screen():
    config = ConfigDB.get()
    customers = CustomerDB.get_all()
    
    if not config.get('enableCustomers'):
        st.warning("Customer database is disabled. Enable it in Settings.")
        return
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"👥 Customers ({len(customers)})")
    with col2:
        if st.button("➕ Add Customer", type="primary", use_container_width=True):
            st.session_state.show_customer_form = True
            st.session_state.edit_customer = None
            st.rerun()
    
    if st.session_state.get('show_customer_form'):
        with st.form("customer_form"):
            st.subheader("Add/Edit Customer")
            
            edit_cust = st.session_state.edit_customer or {}
            customer_data = {}
            
            customer_data['name'] = st.text_input("Full Name *", value=edit_cust.get('name', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                customer_data['email'] = st.text_input("Email", value=edit_cust.get('email', ''))
                customer_data['phone'] = st.text_input("Phone", value=edit_cust.get('phone', ''))
            with col2:
                customer_data['loyalty_points'] = st.number_input("Loyalty Points", 
                                                                  value=int(edit_cust.get('loyalty_points', 0)), 
                                                                  disabled=True)
                customer_data['total_spend'] = st.number_input("Total Spend", 
                                                               value=float(edit_cust.get('total_spend', 0)), 
                                                               disabled=True)
            
            submitted = st.form_submit_button("Save", type="primary")
            cancelled = st.form_submit_button("Cancel")
            
            if cancelled:
                st.session_state.show_customer_form = False
                st.rerun()
            
            if submitted:
                if not customer_data['name']:
                    st.error("Name is required")
                else:
                    customer_data['id'] = edit_cust.get('id', str(datetime.now().timestamp()))
                    customer_data['order_count'] = edit_cust.get('order_count', 0)
                    
                    if st.session_state.edit_customer:
                        CustomerDB.update(customer_data)
                        st.success("Customer updated in database!")
                    else:
                        CustomerDB.add(customer_data)
                        st.success("Customer added to database!")
                    
                    st.session_state.show_customer_form = False
                    st.session_state.edit_customer = None
                    st.rerun()
    
    search = st.text_input("🔍 Search customers...")
    filtered = [c for c in customers if not search or search.lower() in c.get('name', '').lower()]
    
    if filtered:
        for customer in filtered:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{customer.get('name', 'Unknown')}**")
                if customer.get('email'):
                    st.caption(f"📧 {customer['email']}")
            with col2:
                st.caption(f"💰 Spent: {config['currency']}{customer.get('total_spend', 0):.2f}")
                st.caption(f"📦 Orders: {customer.get('order_count', 0)}")
                if config.get('enableLoyalty'):
                    st.caption(f"⭐ Points: {customer.get('loyalty_points', 0)}")
            with col3:
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Edit", key=f"edit_cust_{customer['id']}", use_container_width=True):
                        st.session_state.edit_customer = customer
                        st.session_state.show_customer_form = True
                        st.rerun()
                with col_b:
                    if st.button("Del", key=f"del_cust_{customer['id']}", use_container_width=True):
                        CustomerDB.delete(customer['id'])
                        st.success("Deleted from database!")
                        st.rerun()
            st.divider()
    else:
        st.info("No customers found")

# ============== ANALYTICS SCREEN ==============

def analytics_screen():
    config = ConfigDB.get()
    
    st.subheader("📈 Business Analytics")
    
    # Time range selector
    time_range = st.selectbox("Time Range", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])
    
    days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90, "All Time": 99999}
    days = days_map[time_range]
    
    stats = TransactionDB.get_stats(days)
    
    if stats['transaction_count'] == 0:
        st.info("No transaction data available for this period.")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Revenue", f"{config['currency']}{stats['total_sales']:.2f}")
    with col2:
        st.metric("Transactions", stats['transaction_count'])
    with col3:
        st.metric("Avg Sale", f"{config['currency']}{stats['avg_transaction']:.2f}")
    with col4:
        st.metric("Items Sold", stats['total_items_sold'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top Products")
        top_products = get_top_products(10)
        if top_products:
            for i, prod in enumerate(top_products):
                st.markdown(f"""
                {i+1}. **{prod['name']}** - {prod['quantity']} sold - {config['currency']}{prod['revenue']:.2f}
                """)
        else:
            st.info("No product data yet")
    
    with col2:
        st.subheader("💳 Payment Methods")
        
        with get_db() as conn:
            cursor = conn.cursor()
            results = cursor.execute(f"""
                SELECT payment_method, SUM(total) as total
                FROM transactions
                WHERE date(timestamp) >= date('now', '-{days} days')
                GROUP BY payment_method
                ORDER BY total DESC
            """).fetchall()
            
            if results:
                for row in results:
                    st.markdown(f"**{row['payment_method']}:** {config['currency']}{row['total']:.2f}")
            else:
                st.info("No payment data yet")
    
    # Daily sales trend
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Daily Sales Trend")
    
    with get_db() as conn:
        cursor = conn.cursor()
        results = cursor.execute(f"""
            SELECT DATE(timestamp) as date, SUM(total) as sales
            FROM transactions
            WHERE date(timestamp) >= date('now', '-{days} days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """).fetchall()
        
        if results:
            df = pd.DataFrame([(r['date'], r['sales']) for r in results], columns=['Date', 'Sales'])
            st.line_chart(df.set_index('Date'))
        else:
            st.info("Not enough data for chart")

# ============== SETTINGS SCREEN ==============

def settings_screen():
    config = ConfigDB.get()
    
    st.subheader("⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["Business Info", "Features", "Data Management"])
    
    with tab1:
        config['businessName'] = st.text_input("Business Name", value=config.get('businessName', ''))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # FIXED SYNTAX ERROR HERE
            config['currency'] = st.text_input("Currency", value=config.get('currency', '$'))
        with col2:
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), 
                                               min_value=0.0, step=0.5)
        with col3:
            config['lowStockThreshold'] = st.number_input("Low Stock Threshold", 
                                                         value=int(config.get('lowStockThreshold', 5)), 
                                                         min_value=1)
        
        config['receiptFooter'] = st.text_area("Receipt Footer", value=config.get('receiptFooter', 'Thank you!'))
        
        if st.button("💾 Save Settings", type="primary"):
            ConfigDB.save(config)
            st.success("Settings saved to database!")
            st.rerun()
    
    with tab2:
        config['enableInventory'] = st.checkbox("Enable Inventory Tracking", value=config.get('enableInventory', True))
        config['enableCustomers'] = st.checkbox("Enable Customer Database", value=config.get('enableCustomers', True))
        config['enableLoyalty'] = st.checkbox("Enable Loyalty Program", value=config.get('enableLoyalty', True))
        
        if config['enableLoyalty']:
            config['loyaltyRate'] = st.number_input("Loyalty Points per $1", 
                                                   value=float(config.get('loyaltyRate', 1)), 
                                                   min_value=0.1, step=0.1)
        
        if st.button("💾 Save Features", type="primary"):
            ConfigDB.save(config)
            st.success("Feature settings saved!")
            st.rerun()
    
    with tab3:
        st.markdown("#### Database Information")
        
        with get_db() as conn:
            cursor = conn.cursor()
            product_count = cursor.execute("SELECT COUNT(*) as count FROM products").fetchone()['count']
            customer_count = cursor.execute("SELECT COUNT(*) as count FROM customers").fetchone()['count']
            transaction_count = cursor.execute("SELECT COUNT(*) as count FROM transactions").fetchone()['count']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Products", product_count)
        with col2:
            st.metric("Customers", customer_count)
        with col3:
            st.metric("Transactions", transaction_count)
        
        st.markdown("#### Export Data")
        if st.button("📥 Export to JSON"):
            data = {
                'config': config,
                'products': ProductDB.get_all(),
                'customers': CustomerDB.get_all(),
                'transactions': TransactionDB.get_all(100)
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(data, indent=2, default=str),
                file_name=f"pos-backup-{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        st.markdown("#### Danger Zone")
        if st.checkbox("Show dangerous operations"):
            if st.button("🗑️ Clear All Transactions", type="secondary"):
                if st.checkbox("Confirm delete all transactions"):
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM transaction_items")
                        cursor.execute("DELETE FROM transactions")
                        conn.commit()
                    st.success("All transactions deleted")
                    st.rerun()

# ============== RECEIPT SCREEN ==============

def receipt_screen():
    config = ConfigDB.get()
    transaction = st.session_state.get('last_transaction')
    
    if not transaction:
        st.error("No transaction found")
        st.session_state.screen = 'pos'
        st.rerun()
        return
    
    customer_name = "Guest"
    if transaction.get('customer_id'):
        customer = CustomerDB.get_by_id(transaction['customer_id'])
        if customer:
            customer_name = customer['name']
    
    st.markdown(f"""
    <div style='text-align: center; background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        <h2 style='color: black; margin: 0;'>{config['businessName'] or 'Universal POS Pro'}</h2>
        <p style='color: #666; margin: 0.5rem 0;'>Receipt #{transaction['id'][:8]}</p>
        <p style='color: #666; margin: 0;'>{datetime.fromisoformat(transaction['timestamp']).strftime("%B %d, %Y %I:%M %p")}</p>
        <p style='color: #666; margin: 0;'>Customer: {customer_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("Items")
    for item in transaction['items']:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{item['name']}**")
        with col2:
            st.write(f"x{item['cartQuantity']}")
        with col3:
            st.write(f"{config['currency']}{(item['price'] * item['cartQuantity']):.2f}")
    
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**Subtotal:**")
    with col2:
        st.write(f"{config['currency']}{transaction['subtotal']:.2f}")
    
    if transaction.get('discount', 0) > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Discount:**")
        with col2:
            st.write(f"-{config['currency']}{transaction['discount']:.2f}")
    
    if transaction.get('tax', 0) > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Tax:**")
        with col2:
            st.write(f"{config['currency']}{transaction['tax']:.2f}")
    
    if transaction.get('tip', 0) > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Tip:**")
        with col2:
            st.write(f"{config['currency']}{transaction['tip']:.2f}")
    
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 style='color: black;'>**Total:**</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h2 style='color: #2563eb;'>{config['currency']}{transaction['total']:.2f}</h2>",
                   unsafe_allow_html=True)
    
    st.info(config.get('receiptFooter', 'Thank you for your business!'))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🖨️ Print", use_container_width=True):
            st.info("Use Ctrl+P to print")
    with col2:
        if st.button("📧 Email", use_container_width=True):
            st.info("Email feature coming soon")
    with col3:
        if st.button("🛒 New Sale", type="primary", use_container_width=True):
            st.session_state.screen = 'pos'
            st.rerun()

# ============== MAIN APP ==============

def main():
    st.set_page_config(
        page_title="Universal POS Pro", 
        page_icon="🏪", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize database
    init_database()
    init_session_state()
    
    # Load config from database
    config = ConfigDB.get()
    
    # Apply global styles with fallback for first run
    default_theme = STORE_TEMPLATES['cafe']['theme']
    active_config = config if config else {'theme': default_theme, 'businessName': 'Universal POS'}
    apply_global_styles(active_config)
    
    if st.session_state.screen == 'welcome' or not config:
        welcome_screen()
    elif st.session_state.screen == 'setup':
        setup_wizard()
    else:
        header()
        
        if st.session_state.screen == 'dashboard':
            dashboard()
        elif st.session_state.screen == 'pos':
            pos_screen()
        elif st.session_state.screen == 'products':
            products_screen()
        elif st.session_state.screen == 'customers':
            customers_screen()
        elif st.session_state.screen == 'analytics':
            analytics_screen()
        elif st.session_state.screen == 'settings':
            settings_screen()
        elif st.session_state.screen == 'receipt':
            receipt_screen()

if __name__ == "__main__":
    main()
