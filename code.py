import streamlit as st
import json
import sqlite3
import uuid  # FIX: For unique IDs
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from contextlib import contextmanager

# ============== DATABASE SETUP ==============

DB_NAME = "pos_system_final.db"

@contextmanager
def get_db():
    """Context manager for database connections with thread safety"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database with all required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        
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

    @staticmethod
    def delete(product_id):
        with get_db() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))

class CustomerDB:
    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            results = cursor.execute("SELECT * FROM customers ORDER BY name").fetchall()
            return [json.loads(row['data']) for row in results if row['data']]

    @staticmethod
    def add(customer_data):
        with get_db() as conn:
            conn.execute("""
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

    @staticmethod
    def update(customer_data):
        with get_db() as conn:
            conn.execute("""
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

    @staticmethod
    def delete(customer_id):
        with get_db() as conn:
            conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))

class TransactionDB:
    @staticmethod
    def get_todays_total():
        with get_db() as conn:
            cursor = conn.cursor()
            result = cursor.execute("""
                SELECT SUM(total) as total 
                FROM transactions 
                WHERE date(timestamp) = date('now', 'localtime')
            """).fetchone()
            return result['total'] if result and result['total'] else 0.0

    @staticmethod
    def get_stats(days=30):
        # FIX: Parameterized query to prevent SQL Injection
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Use SQLite date function modifiers securely
            date_modifier = f"-{days} days"
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    SUM(total) as total_sales,
                    AVG(total) as avg_sale
                FROM transactions
                WHERE date(timestamp) >= date('now', ?)
            """, (date_modifier,))
            result = cursor.fetchone()
            
            cursor.execute("""
                SELECT SUM(quantity) as total_items
                FROM transaction_items ti
                JOIN transactions t ON ti.transaction_id = t.id
                WHERE date(t.timestamp) >= date('now', ?)
            """, (date_modifier,))
            items_result = cursor.fetchone()
            
            return {
                'transaction_count': result['count'] or 0,
                'total_sales': result['total_sales'] or 0.0,
                'avg_transaction': result['avg_sale'] or 0.0,
                'total_items_sold': items_result['total_items'] or 0
            }

    @staticmethod
    def process_sale(transaction_data, cart_items, update_inventory_bool):
        """Atomic transaction to save sale and update inventory safely"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. Check Inventory Levels First (if enabled)
            if update_inventory_bool:
                for item in cart_items:
                    curr_stock = cursor.execute("SELECT inventory FROM products WHERE id = ?", (item['id'],)).fetchone()
                    if curr_stock and curr_stock['inventory'] < item['cartQuantity']:
                         raise ValueError(f"Insufficient stock for {item['name']}")

            # 2. Create Transaction
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
            
            # 3. Add Items & Update Inventory
            for item in cart_items:
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
                
                if update_inventory_bool:
                    cursor.execute("UPDATE products SET inventory = inventory - ? WHERE id = ?", 
                                 (item['cartQuantity'], item['id']))
            
            # 4. Update Customer Stats
            if transaction_data.get('customer_id'):
                # Calculate points (simplified logic passed in)
                points = int(transaction_data['total']) 
                cursor.execute("""
                    UPDATE customers 
                    SET total_spend = total_spend + ?, 
                        loyalty_points = loyalty_points + ?,
                        order_count = order_count + 1
                    WHERE id = ?
                """, (transaction_data['total'], points, transaction_data['customer_id']))

# ============== CONFIGURATION ==============

STORE_TEMPLATES = {
    'cafe': {
        'name': 'Café/Coffee Shop',
        'icon': '☕',
        'theme': {'primary': '#8B4513', 'secondary': '#D2691E', 'background': '#FFF8DC', 'accent': '#CD853F'},
        'taxRate': 8, 'currency': '$'
    },
    'retail': {
        'name': 'Retail Store',
        'icon': '🏪',
        'theme': {'primary': '#2563eb', 'secondary': '#3b82f6', 'background': '#eff6ff', 'accent': '#60a5fa'},
        'taxRate': 10, 'currency': '$'
    },
    'restaurant': {
        'name': 'Restaurant',
        'icon': '🍽️',
        'theme': {'primary': '#dc2626', 'secondary': '#ef4444', 'background': '#fef2f2', 'accent': '#f87171'},
        'taxRate': 8, 'currency': '$'
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
        'last_transaction': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============== STYLING ==============

def apply_global_styles(config):
    theme = config.get('theme', STORE_TEMPLATES['cafe']['theme']) if config else STORE_TEMPLATES['cafe']['theme']
    primary = theme.get('primary', '#2563eb')
    background = theme.get('background', '#f8fafc')
    
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, {background} 0%, #ffffff 100%); }}
    .metric-card {{
        background: white; padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {primary};
    }}
    .product-card {{
        background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e5e7eb;
    }}
    .main-header {{
        background: {primary}; color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# ============== NAVIGATION (FIXED) ==============

def update_screen_callback():
    """Callback to update screen state immediately upon selection"""
    st.session_state.screen = st.session_state.nav_selection.lower()

def header():
    config = ConfigDB.get()
    
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col1:
        st.markdown(f"### 🏪 {config.get('businessName', 'POS System')}")
    
    with col2:
        today_sales = TransactionDB.get_todays_total()
        st.caption("Today's Revenue")
        st.markdown(f"**{config.get('currency', '$')}{today_sales:.2f}**")
    
    with col3:
        screens = ['Dashboard', 'POS', 'Products', 'Customers', 'Analytics', 'Settings']
        
        # Determine correct index safely
        current_screen_name = st.session_state.screen.capitalize()
        try:
            current_index = screens.index(current_screen_name)
        except ValueError:
            current_index = 0
            
        # FIX: Added key and on_change callback for reliable navigation
        st.selectbox(
            "Navigation", 
            screens, 
            index=current_index, 
            key="nav_selection", 
            on_change=update_screen_callback,
            label_visibility="collapsed"
        )
    
    st.divider()

# ============== SCREENS ==============

def welcome_screen():
    st.markdown("<h1 style='text-align: center;'>Welcome to POS Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("No configuration found. Let's set up your store.")
        if st.button("🚀 Start Setup", type="primary", use_container_width=True):
            st.session_state.screen = 'setup'
            st.rerun()

def setup_wizard():
    st.title("Setup Wizard")
    
    if st.session_state.setup_step == 1:
        st.subheader("Select Business Type")
        cols = st.columns(3)
        for idx, (key, template) in enumerate(STORE_TEMPLATES.items()):
            with cols[idx % 3]:
                if st.button(f"{template['icon']} {template['name']}", use_container_width=True):
                    # Save initial config
                    config = {
                        'businessType': key,
                        'theme': template['theme'],
                        'taxRate': template['taxRate'],
                        'currency': template['currency'],
                        'enableInventory': True,
                        'enableCustomers': True,
                        'enableLoyalty': True,
                        'businessName': ''
                    }
                    ConfigDB.save(config)
                    st.session_state.setup_step = 2
                    st.rerun()
                    
    elif st.session_state.setup_step == 2:
        config = ConfigDB.get()
        st.subheader("Store Details")
        
        with st.form("setup_form"):
            config['businessName'] = st.text_input("Business Name", value="My Store")
            config['currency'] = st.text_input("Currency Symbol", value=config['currency'])
            config['taxRate'] = st.number_input("Tax Rate (%)", value=config['taxRate'])
            
            if st.form_submit_button("Finish Setup"):
                ConfigDB.save(config)
                st.session_state.screen = 'dashboard'
                st.rerun()

def dashboard():
    config = ConfigDB.get()
    stats = TransactionDB.get_stats(30)
    
    st.subheader("📊 Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><h3>Sales (30d)</h3><h2>{config['currency']}{stats['total_sales']:.2f}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h3>Transactions</h3><h2>{stats['transaction_count']}</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>Avg Sale</h3><h2>{config['currency']}{stats['avg_transaction']:.2f}</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🛒 Go to POS", type="primary", use_container_width=True):
            st.session_state.screen = 'pos'
            st.rerun()
    with c2:
        if st.button("📦 Manage Products", use_container_width=True):
            st.session_state.screen = 'products'
            st.rerun()
    with c3:
        if st.button("👥 Manage Customers", use_container_width=True):
            st.session_state.screen = 'customers'
            st.rerun()

def pos_screen():
    config = ConfigDB.get()
    products = ProductDB.get_all()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Products")
        search = st.text_input("Search", label_visibility="collapsed", placeholder="Search products...")
        
        filtered = [p for p in products if search.lower() in p['name'].lower()]
        
        for i in range(0, len(filtered), 3):
            cols = st.columns(3)
            for j, p in enumerate(filtered[i:i+3]):
                with cols[j]:
                    stock_display = f"Stock: {p.get('inventory', 0)}" if config['enableInventory'] else ""
                    st.markdown(f"""
                    <div class='product-card'>
                        <b>{p['name']}</b><br>
                        {config['currency']}{p['price']:.2f}<br>
                        <small>{stock_display}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Disable if out of stock
                    disabled = config['enableInventory'] and p.get('inventory', 0) <= 0
                    if st.button("Add", key=f"add_{p['id']}", disabled=disabled, use_container_width=True):
                        # Add to cart logic
                        existing = next((item for item in st.session_state.cart if item['id'] == p['id']), None)
                        if existing:
                            existing['cartQuantity'] += 1
                        else:
                            st.session_state.cart.append({**p, 'cartQuantity': 1})
                        st.rerun()

    with col2:
        st.subheader("Current Order")
        cart = st.session_state.cart
        
        if not cart:
            st.info("Cart is empty")
        else:
            total = 0
            for item in cart:
                row_total = item['price'] * item['cartQuantity']
                total += row_total
                
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.write(f"{item['name']} (x{item['cartQuantity']})")
                with c2:
                    st.write(f"{config['currency']}{row_total:.2f}")
                with c3:
                    if st.button("X", key=f"rem_{item['id']}"):
                        cart.remove(item)
                        st.rerun()
            
            st.divider()
            tax = total * (config.get('taxRate', 0) / 100)
            final_total = total + tax
            
            st.write(f"Subtotal: {config['currency']}{total:.2f}")
            st.write(f"Tax: {config['currency']}{tax:.2f}")
            st.markdown(f"### Total: {config['currency']}{final_total:.2f}")
            
            # Checkout
            customers = CustomerDB.get_all()
            cust_names = ["Guest"] + [c['name'] for c in customers]
            selected_cust = st.selectbox("Customer", cust_names)
            
            pay_method = st.selectbox("Payment", PAYMENT_METHODS)
            
            if st.button("✅ Complete Sale", type="primary", use_container_width=True):
                # Prepare Transaction Data
                cust_id = next((c['id'] for c in customers if c['name'] == selected_cust), None)
                
                transaction = {
                    'id': str(uuid.uuid4()),  # FIX: Unique UUID
                    'customer_id': cust_id,
                    'subtotal': total,
                    'tax': tax,
                    'total': final_total,
                    'payment_method': pay_method,
                    'timestamp': datetime.now().isoformat()
                }
                
                try:
                    # FIX: Process Atomically
                    TransactionDB.process_sale(transaction, cart, config['enableInventory'])
                    
                    st.session_state.last_transaction = transaction
                    st.session_state.last_transaction['items'] = cart  # attach items for receipt
                    st.session_state.cart = []
                    st.session_state.screen = 'receipt'
                    st.success("Sale Successful!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Transaction failed: {e}")

def products_screen():
    st.subheader("Manage Products")
    
    with st.expander("Add New Product", expanded=st.session_state.show_product_form):
        with st.form("new_product"):
            name = st.text_input("Name")
            price = st.number_input("Price", min_value=0.0)
            inventory = st.number_input("Inventory", min_value=0, step=1)
            
            if st.form_submit_button("Save Product"):
                ProductDB.add({
                    'id': str(uuid.uuid4()), # FIX: UUID
                    'name': name,
                    'price': price,
                    'inventory': inventory,
                    'category': 'General'
                })
                st.success("Product Added")
                st.rerun()
                
    # List Products
    df = pd.DataFrame(ProductDB.get_all())
    if not df.empty:
        st.dataframe(df[['name', 'price', 'inventory', 'category']], use_container_width=True)

def receipt_screen():
    st.subheader("Receipt")
    trans = st.session_state.last_transaction
    if not trans:
        st.error("No receipt to show")
        if st.button("Back"): 
            st.session_state.screen = 'pos'
            st.rerun()
        return

    st.markdown(f"""
    <div style='background: white; padding: 20px; border: 1px dashed black;'>
        <h3 style='text-align: center;'>Receipt</h3>
        <p>ID: {trans['id']}</p>
        <p>Date: {trans['timestamp']}</p>
        <hr>
    """, unsafe_allow_html=True)
    
    for item in trans.get('items', []):
        st.write(f"{item['name']} x{item['cartQuantity']} - {item['price'] * item['cartQuantity']:.2f}")
        
    st.markdown("---")
    st.markdown(f"**TOTAL: {trans['total']:.2f}**")
    
    if st.button("Start New Sale", type="primary"):
        st.session_state.screen = 'pos'
        st.rerun()

# ============== MAIN ENTRY POINT ==============

def main():
    st.set_page_config(page_title="POS Pro", layout="wide")
    init_database()
    init_session_state()
    
    config = ConfigDB.get()
    
    # Logic to handle first-time run
    if not config:
        if st.session_state.screen != 'setup':
            st.session_state.screen = 'welcome'
    
    apply_global_styles(config)
    
    # Router
    if st.session_state.screen == 'welcome':
        welcome_screen()
    elif st.session_state.screen == 'setup':
        setup_wizard()
    else:
        # Show header only if configured
        header()
        
        if st.session_state.screen == 'dashboard':
            dashboard()
        elif st.session_state.screen == 'pos':
            pos_screen()
        elif st.session_state.screen == 'products':
            products_screen()
        elif st.session_state.screen == 'customers':
            # Simplified placeholder for brevity, logic follows products
            st.info("Customer Management Screen")
        elif st.session_state.screen == 'receipt':
            receipt_screen()
        elif st.session_state.screen == 'analytics':
             st.info("Analytics Screen")
        elif st.session_state.screen == 'settings':
             st.info("Settings Screen")

if __name__ == "__main__":
    main()
