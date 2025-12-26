# Improved POS app with working SQLite database
# To run: pip install streamlit pandas
# Then: streamlit run code.py

import streamlit as st
import json
import sqlite3
from datetime import datetime
import pandas as pd
from contextlib import contextmanager
from uuid import uuid4
import os

# ============== DATABASE SETUP ==============

DB_NAME = os.environ.get("POS_DB", "pos_system.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_database():
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
                created_at TEXT DEFAULT (datetime('now'))
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
                created_at TEXT DEFAULT (datetime('now'))
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
                timestamp TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE SET NULL
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
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
            )
        """)
        conn.commit()

# ============== DATABASE OPERATIONS ==============

class ConfigDB:
    @staticmethod
    def get():
        with get_db() as conn:
            row = conn.execute("SELECT data FROM config WHERE id = 1").fetchone()
            return json.loads(row["data"]) if row else None

    @staticmethod
    def save(config_data):
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO config (id, data) VALUES (1, ?)",
                (json.dumps(config_data),)
            )
            conn.commit()

class ProductDB:
    @staticmethod
    def _row_to_product(row):
        product = json.loads(row['data']) if row['data'] else {}
        product.update({
            'id': row['id'],
            'name': row['name'],
            'price': row['price'],
            'inventory': row['inventory'],
            'category': row['category'] or 'General'
        })
        return product

    @staticmethod
    def get_all():
        with get_db() as conn:
            results = conn.execute("SELECT * FROM products ORDER BY name COLLATE NOCASE").fetchall()
            return [ProductDB._row_to_product(r) for r in results]

    @staticmethod
    def get_by_id(product_id):
        with get_db() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            return ProductDB._row_to_product(row) if row else None

    @staticmethod
    def add(product_data):
        with get_db() as conn:
            pdata = dict(product_data)
            pdata.setdefault('category', 'General')
            pdata.setdefault('inventory', 0)
            pdata.setdefault('price', 0.0)
            pid = pdata.get('id') or str(uuid4())
            pdata['id'] = pid
            conn.execute(
                "INSERT INTO products (id, name, price, inventory, category, data) VALUES (?, ?, ?, ?, ?, ?)",
                (pid, pdata['name'], float(pdata['price']), int(pdata['inventory']), pdata['category'], json.dumps(pdata))
            )
            conn.commit()
            return pid

    @staticmethod
    def update(product_data):
        with get_db() as conn:
            pdata = dict(product_data)
            conn.execute(
                "UPDATE products SET name = ?, price = ?, inventory = ?, category = ?, data = ? WHERE id = ?",
                (pdata['name'], float(pdata['price']), int(pdata.get('inventory', 0)), pdata.get('category', 'General'),
                 json.dumps(pdata), pdata['id'])
            )
            conn.commit()

    @staticmethod
    def delete(product_id):
        with get_db() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

    @staticmethod
    def update_inventory(product_id, quantity_change):
        with get_db() as conn:
            conn.execute("UPDATE products SET inventory = inventory + ? WHERE id = ?", (int(quantity_change), product_id))
            conn.commit()

class CustomerDB:
    @staticmethod
    def _row_to_customer(row):
        customer = json.loads(row['data']) if row['data'] else {}
        customer.update({
            'id': row['id'],
            'name': row['name'],
            'email': row['email'],
            'phone': row['phone'],
            'loyalty_points': row['loyalty_points'],
            'total_spend': row['total_spend'],
            'order_count': row['order_count'],
        })
        return customer

    @staticmethod
    def get_all():
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM customers ORDER BY name COLLATE NOCASE").fetchall()
            return [CustomerDB._row_to_customer(r) for r in rows]

    @staticmethod
    def add(customer_data):
        with get_db() as conn:
            cdata = dict(customer_data)
            cid = cdata.get('id') or str(uuid4())
            cdata['id'] = cid
            conn.execute(
                "INSERT INTO customers (id, name, email, phone, loyalty_points, total_spend, order_count, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (cid, cdata['name'], cdata.get('email', ''), cdata.get('phone', ''), 0, 0.0, 0, json.dumps(cdata))
            )
            conn.commit()
            return cid

    @staticmethod
    def update(customer_data):
        with get_db() as conn:
            cdata = dict(customer_data)
            conn.execute(
                "UPDATE customers SET name = ?, email = ?, phone = ?, data = ? WHERE id = ?",
                (cdata['name'], cdata.get('email', ''), cdata.get('phone', ''), json.dumps(cdata), cdata['id'])
            )
            conn.commit()

    @staticmethod
    def delete(customer_id):
        with get_db() as conn:
            conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()

    @staticmethod
    def update_stats(customer_id, total_spent, loyalty_points):
        with get_db() as conn:
            conn.execute(
                "UPDATE customers SET total_spend = total_spend + ?, loyalty_points = loyalty_points + ?, order_count = order_count + 1 WHERE id = ?",
                (float(total_spent), int(loyalty_points), customer_id)
            )
            conn.commit()

class TransactionDB:
    @staticmethod
    def get_todays_total():
        with get_db() as conn:
            row = conn.execute("SELECT SUM(total) as total FROM transactions WHERE date(timestamp) = date('now', 'localtime')").fetchone()
            return float(row['total']) if row and row['total'] is not None else 0.0

    @staticmethod
    def add(transaction_data):
        with get_db() as conn:
            tid = transaction_data.get('id') or str(uuid4())
            timestamp = transaction_data.get('timestamp') or datetime.utcnow().isoformat()
            conn.execute(
                "INSERT INTO transactions (id, customer_id, subtotal, discount, tax, tip, total, payment_method, data, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (tid, transaction_data.get('customer_id'), float(transaction_data['subtotal']),
                 float(transaction_data.get('discount', 0)), float(transaction_data.get('tax', 0)), float(transaction_data.get('tip', 0)),
                 float(transaction_data['total']), transaction_data.get('payment_method', 'Cash'),
                 json.dumps(transaction_data), timestamp)
            )
            for item in transaction_data.get('items', []):
                # ensure item fields are primitive types
                pid = item.get('id')
                pname = item.get('name') or item.get('product_name') or 'Unknown'
                price = float(item.get('price', 0.0))
                qty = int(item.get('cartQuantity', item.get('quantity', 1)))
                conn.execute(
                    "INSERT INTO transaction_items (transaction_id, product_id, product_name, price, quantity, data) VALUES (?, ?, ?, ?, ?, ?)",
                    (tid, pid, pname, price, qty, json.dumps(item))
                )
            conn.commit()
            return tid

    @staticmethod
    def get_stats(days=30):
        with get_db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count, SUM(total) as total_sales, AVG(total) as avg_sale FROM transactions WHERE date(timestamp) >= date('now', ?)",
                (f'-{int(days)} days',)
            ).fetchone()
            items = conn.execute(
                "SELECT SUM(ti.quantity) as total_items FROM transaction_items ti JOIN transactions t ON ti.transaction_id = t.id WHERE date(t.timestamp) >= date('now', ?)",
                (f'-{int(days)} days',)
            ).fetchone()
            return {
                'transaction_count': int(row['count']) if row and row['count'] is not None else 0,
                'total_sales': float(row['total_sales']) if row and row['total_sales'] is not None else 0.0,
                'avg_transaction': float(row['avg_sale']) if row and row['avg_sale'] is not None else 0.0,
                'total_items_sold': int(items['total_items']) if items and items['total_items'] is not None else 0
            }

def get_top_products(limit=5, days=None):
    with get_db() as conn:
        if days:
            sql = """
                SELECT ti.product_name as name, SUM(ti.quantity) as quantity, SUM(ti.price * ti.quantity) as revenue
                FROM transaction_items ti
                JOIN transactions t ON ti.transaction_id = t.id
                WHERE date(t.timestamp) >= date('now', ?)
                GROUP BY ti.product_name
                ORDER BY revenue DESC
                LIMIT ?
            """
            params = (f'-{int(days)} days', int(limit))
        else:
            sql = """
                SELECT product_name as name, SUM(quantity) as quantity, SUM(price * quantity) as revenue
                FROM transaction_items
                GROUP BY product_name
                ORDER BY revenue DESC
                LIMIT ?
            """
            params = (int(limit),)
        rows = conn.execute(sql, params).fetchall()
        return [{'name': r['name'], 'quantity': int(r['quantity'] or 0), 'revenue': float(r['revenue'] or 0.0)} for r in rows]

# ============== CONFIGURATION ==============

TEMPLATES = {
    'cafe': {'name': 'Café', 'icon': '☕', 'theme': {'primary': '#8B4513', 'accent': '#CD853F', 'bg': '#FFF8DC'}, 'taxRate': 8, 'currency': '$'},
    'retail': {'name': 'Retail', 'icon': '🏪', 'theme': {'primary': '#2563eb', 'accent': '#60a5fa', 'bg': '#eff6ff'}, 'taxRate': 10, 'currency': '$'},
    'restaurant': {'name': 'Restaurant', 'icon': '🍽️', 'theme': {'primary': '#dc2626', 'accent': '#f87171', 'bg': '#fef2f2'}, 'taxRate': 8, 'currency': '$'}
}

PAYMENT_METHODS = ['Cash', 'Credit Card', 'Debit Card', 'Mobile Payment']

def init_session_state():
    defaults = {
        'screen': 'welcome',
        'cart': [],
        'setup_step': 1,
        'edit_product_id': None,
        'edit_customer_id': None,
        'selected_cat': 'All',
        'last_transaction': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============== STYLING ==============

def apply_styles(config):
    theme = config.get('theme') if config else TEMPLATES['cafe']['theme']
    primary = theme.get('primary', '#2563eb')
    accent = theme.get('accent', '#60a5fa')
    bg = theme.get('bg', '#f8fafc')

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: linear-gradient(135deg, {bg} 0%, #fff 100%); }}
    #MainMenu, footer, .stDeployButton {{ visibility: hidden; }}

    .metric-card {{
        background: white; padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid {primary};
        transition: transform 0.2s; cursor: pointer;
    }}
    .metric-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}

    .product-card {{
        background: white; padding: 1.25rem; border-radius: 12px; border: 2px solid #e5e7eb;
        transition: all 0.2s; height: 100%; cursor: pointer;
    }}
    .product-card:hover {{ border-color: {accent}; transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.12); }}
    .product-card.out-of-stock {{ opacity: 0.5; border-color: #ef4444; cursor: not-allowed; }}
    .product-card.low-stock {{ border-color: #f59e0b; }}

    .cart-container {{
        background: white; border-radius: 12px; padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08); position: sticky; top: 20px;
    }}

    .cart-item {{
        background: #f9fafb; padding: 1rem; border-radius: 8px;
        margin-bottom: 0.75rem; border-left: 3px solid {primary};
    }}

    .main-header {{
        background: linear-gradient(135deg, {primary} 0%, {accent} 100%);
        color: white; padding: 1.5rem 2rem; border-radius: 16px;
        margin-bottom: 2rem; box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }}

    .stat-number {{ font-size: 2rem; font-weight: 700; color: {primary}; margin: 0; line-height: 1; }}
    .stat-label {{ color: #6b7280; font-size: 0.875rem; margin: 0.5rem 0 0 0; }}

    .badge {{
        display: inline-block; padding: 0.25rem 0.75rem;
        border-radius: 12px; font-size: 0.75rem; font-weight: 600;
    }}
    .badge-success {{ background: #d1fae5; color: #065f46; }}
    .badge-warning {{ background: #fef3c7; color: #92400e; }}
    .badge-danger {{ background: #fee2e2; color: #991b1b; }}

    .stButton > button {{
        border-radius: 8px; font-weight: 500; transition: all 0.2s;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    </style>
    """, unsafe_allow_html=True)

# ============== WELCOME SCREEN ==============

def welcome_screen():
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
        <h1 style='font-size: 3.5rem; font-weight: 700; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;'>
            🏪 Universal POS Pro
        </h1>
        <p style='font-size: 1.5rem; color: #64748b; margin-bottom: 0.5rem;'>Next-Generation Point of Sale</p>
        <p style='color: #94a3b8; font-size: 1.1rem;'>SQLite Database • Analytics • Customer Management</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    features = [("💾", "Database", "Persistent storage"),
                ("📊", "Analytics", "Real-time insights"),
                ("📦", "Inventory", "Smart tracking"),
                ("👥", "Customers", "Loyalty program")]
    for col, feat in zip(cols, features):
        icon, title, desc = feat
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
        if st.button("🚀 Get Started", type="primary"):
            st.session_state.screen = 'setup'
            st.rerun()

# ============== SETUP WIZARD ==============

def setup_wizard():
    st.progress(min(max((st.session_state.setup_step - 1) / 2.0, 0.0), 1.0))

    if st.session_state.setup_step == 1:
        st.markdown("<h2 style='text-align: center;'>Choose Your Business Type</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        cols = st.columns(3)
        for idx, (key, template) in enumerate(TEMPLATES.items()):
            with cols[idx]:
                st.markdown(f"""
                <div class='product-card' style='text-align: center; min-height: 200px;'>
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>{template['icon']}</div>
                    <h3 style='margin: 0; color: #1f2937;'>{template['name']}</h3>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Select", key=f"template_{key}"):
                    config = {
                        'businessType': key,
                        'businessName': '',
                        'theme': template['theme'],
                        'taxRate': template['taxRate'],
                        'currency': template['currency'],
                        'enableInventory': True,
                        'enableCustomers': True,
                        'enableLoyalty': True,
                        'loyaltyRate': 1,
                        'lowStockThreshold': 5
                    }
                    ConfigDB.save(config)
                    st.session_state.setup_step = 2
                    st.rerun()
    else:
        st.markdown("<h2 style='text-align: center;'>Configure Your Store</h2>", unsafe_allow_html=True)
        config = ConfigDB.get()
        if not config:
            st.error("Configuration lost")
            if st.button("← Back"):
                st.session_state.setup_step = 1
                st.rerun()
            return

        with st.form("setup_form"):
            config['businessName'] = st.text_input("Business Name *", value=config.get('businessName', ''))
            col1, col2, col3 = st.columns(3)
            with col1:
                config['currency'] = st.text_input("Currency", value=config.get('currency', '$'), max_chars=3)
            with col2:
                config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), min_value=0.0, max_value=100.0, step=0.5)
            with col3:
                config['lowStockThreshold'] = st.number_input("Low Stock Alert", value=int(config.get('lowStockThreshold', 5)), min_value=1, step=1)

            st.markdown("#### Features")
            col1, col2, col3 = st.columns(3)
            with col1:
                config['enableInventory'] = st.checkbox("📦 Inventory", value=bool(config.get('enableInventory', True)))
            with col2:
                config['enableCustomers'] = st.checkbox("👥 Customers", value=bool(config.get('enableCustomers', True)))
            with col3:
                config['enableLoyalty'] = st.checkbox("⭐ Loyalty", value=bool(config.get('enableLoyalty', True)))

            col1, col2 = st.columns(2)
            with col1:
                back = st.form_submit_button("← Back")
            with col2:
                complete = st.form_submit_button("Complete ✓")

            if back:
                st.session_state.setup_step = 1
                st.rerun()
            if complete:
                if not config.get('businessName'):
                    st.error("Please enter a business name")
                else:
                    ConfigDB.save(config)
                    st.session_state.screen = 'dashboard'
                    st.success("🎉 Setup complete!")
                    st.rerun()

# ============== HEADER ==============

def header():
    config = ConfigDB.get() or {}
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"""
        <div class='main-header'>
            <h2 style='margin: 0; color: white; font-size: 1.5rem;'>{config.get('businessName', 'POS Pro')}</h2>
            <p style='margin: 0; opacity: 0.9; font-size: 0.9rem;'>{datetime.now().strftime("%B %d, %Y")}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        today_sales = TransactionDB.get_todays_total()
        currency = config.get('currency', '$')
        st.metric("Today's Sales", f"{currency}{today_sales:.2f}")

    with col3:
        screens = {'Dashboard': 'dashboard', 'POS': 'pos', 'Products': 'products', 'Customers': 'customers', 'Analytics': 'analytics', 'Settings': 'settings'}
        current = [k for k, v in screens.items() if v == st.session_state.screen]
        idx = list(screens.keys()).index(current[0]) if current else 0
        selected = st.selectbox("Go to", list(screens.keys()), index=idx, label_visibility="collapsed")
        if screens[selected] != st.session_state.screen:
            st.session_state.screen = screens[selected]
            st.rerun()

# ============== DASHBOARD ==============

def dashboard():
    config = ConfigDB.get() or {}
    today_sales = TransactionDB.get_todays_total()
    stats = TransactionDB.get_stats(30)
    products = ProductDB.get_all()

    with get_db() as conn:
        today_count = conn.execute("SELECT COUNT(*) as cnt FROM transactions WHERE date(timestamp) = date('now', 'localtime')").fetchone()['cnt'] or 0

    st.subheader("📊 Overview")
    col1, col2, col3, col4 = st.columns(4)

    currency = config.get('currency', '$')
    metrics = [
        ("Today", f"{currency}{today_sales:.2f}", f"{today_count} sales"),
        ("30-Day", f"{currency}{stats['total_sales']:.2f}", f"{stats['transaction_count']} sales"),
        ("Avg Sale", f"{currency}{stats['avg_transaction']:.2f}", "Per transaction"),
        ("Products", len(products), "In catalog")
    ]

    for col, (label, number, sub) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <p class='stat-label'>{label}</p>
                <p class='stat-number'>{number}</p>
                <p class='stat-label'>{sub}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    actions = [("🛒 New Sale", 'pos'), ("➕ Product", 'products'), ("👥 Customers", 'customers'), ("📈 Analytics", 'analytics')]
    for col, (label, screen) in zip([col1, col2, col3, col4], actions):
        with col:
            if st.button(label):
                st.session_state.screen = screen
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top Products")
        top = get_top_products(5, days=30)
        if top:
            for i, p in enumerate(top, 1):
                st.markdown(f"""
                <div class='cart-item'>
                    <strong>{i}. {p['name']}</strong><br>
                    <span style='color: #6b7280;'>Sold: {p['quantity']} | {currency}{p['revenue']:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No sales yet")

    with col2:
        st.subheader("⚠️ Inventory")
        if config.get('enableInventory'):
            threshold = int(config.get('lowStockThreshold', 5))
            low = [p for p in products if 0 < p.get('inventory', 0) <= threshold]
            out = [p for p in products if p.get('inventory', 0) <= 0]

            if out:
                st.error(f"🚨 {len(out)} out of stock")
                for p in out[:3]:
                    st.markdown(f"• {p['name']}")
            if low:
                st.warning(f"⚡ {len(low)} low stock")
                for p in low[:3]:
                    st.markdown(f"• {p['name']} ({p['inventory']} left)")
            if not low and not out:
                st.success("✅ All stocked")
        else:
            st.info("Enable in Settings")

# ============== POS SCREEN ==============

def pos_screen():
    config = ConfigDB.get() or {}
    products = ProductDB.get_all()
    cart = st.session_state.cart

    col1, col2 = st.columns([2.5, 1.5])

    with col1:
        search_col, cat_col = st.columns([3, 1])
        with search_col:
            search = st.text_input("🔍 Search...", key="search", placeholder="Type to search")
        with cat_col:
            categories = ['All'] + sorted({p.get('category', 'General') for p in products})
            selected_cat = st.selectbox("", categories, label_visibility="collapsed", key="category_filter")

        filtered = products
        if search:
            filtered = [p for p in filtered if search.lower() in p.get('name', '').lower()]
        if selected_cat != 'All':
            filtered = [p for p in filtered if p.get('category') == selected_cat]

        if filtered:
            for i in range(0, len(filtered), 3):
                cols = st.columns(3)
                for j, product in enumerate(filtered[i:i+3]):
                    with cols[j]:
                        stock = int(product.get('inventory', 0))
                        in_stock = (stock > 0) or not config.get('enableInventory', True)
                        stock_class = ''
                        if not in_stock:
                            stock_class = 'out-of-stock'
                        elif in_stock and stock <= int(config.get('lowStockThreshold', 5)) and config.get('enableInventory', True):
                            stock_class = 'low-stock'

                        # badge
                        badge_html = ""
                        if config.get('enableInventory', True):
                            if stock == 0:
                                badge_html = f"<span class='badge badge-danger'>Stock: {stock}</span>"
                            elif stock <= int(config.get('lowStockThreshold', 5)):
                                badge_html = f"<span class='badge badge-warning'>Stock: {stock}</span>"
                            else:
                                badge_html = f"<span class='badge badge-success'>Stock: {stock}</span>"

                        st.markdown(f"""
                        <div class='product-card {stock_class}'>
                            <h4 style='margin: 0 0 0.5rem 0;'>{product['name']}</h4>
                            <p style='color: #2563eb; font-size: 1.4rem; font-weight: 700; margin: 0.25rem 0;'>
                                {config.get('currency', '$')}{product['price']:.2f}
                            </p>
                            {badge_html}
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button("Add", key=f"add_{product['id']}", disabled=(not in_stock)):
                            # normalize product snapshot stored in cart
                            snapshot = {
                                'id': product['id'],
                                'name': product['name'],
                                'price': float(product['price']),
                                'cartQuantity': 1,
                                'inventory': int(product.get('inventory', 0))
                            }
                            existing = next((c for c in cart if c['id'] == snapshot['id']), None)
                            if existing:
                                existing['cartQuantity'] += 1
                            else:
                                cart.append(snapshot)
                            st.rerun()
        else:
            st.info("No products found")

    with col2:
        st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
        st.markdown(f"### 🛒 Cart ({len(cart)})")

        customers = []
        selected_customer = 'Guest'
        if config.get('enableCustomers', True):
            customers = CustomerDB.get_all()
            customer_opts = ['Guest'] + [c['name'] for c in customers]
            selected_customer = st.selectbox("Customer", customer_opts)

        if cart:
            for item in list(cart):  # copy to avoid mutation issues during iteration
                st.markdown(f"""
                <div class='cart-item'>
                    <strong>{item['name']}</strong><br>
                    <div style='display: flex; justify-content: space-between; margin-top: 0.5rem;'>
                        <span>{config.get('currency', '$')}{item['price']:.2f} × {item['cartQuantity']}</span>
                        <strong style='color: #2563eb;'>{config.get('currency', '$')}{(item['price'] * item['cartQuantity']):.2f}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_a:
                    if st.button("−", key=f"dec_{item['id']}"):
                        item['cartQuantity'] -= 1
                        if item['cartQuantity'] <= 0:
                            cart.remove(item)
                        st.rerun()
                with col_b:
                    if st.button("+", key=f"inc_{item['id']}"):
                        # prevent adding beyond inventory when enabled
                        if config.get('enableInventory', True) and item.get('inventory', 0) <= item['cartQuantity']:
                            st.warning("Not enough stock")
                        else:
                            item['cartQuantity'] += 1
                        st.rerun()
                with col_c:
                    if st.button("🗑️", key=f"del_{item['id']}"):
                        cart.remove(item)
                        st.rerun()

            st.divider()
            subtotal = sum(item['price'] * item['cartQuantity'] for item in cart)
            tax = subtotal * (float(config.get('taxRate', 0)) / 100.0)
            total = subtotal + tax

            st.markdown(f"""
            <div style='background: #f9fafb; padding: 1rem; border-radius: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                    <span>Subtotal:</span><span>{config.get('currency', '$')}{subtotal:.2f}</span>
                </div>
                <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                    <span>Tax ({config.get('taxRate', 0)}%):</span><span>{config.get('currency', '$')}{tax:.2f}</span>
                </div>
                <hr style='margin: 0.75rem 0; border-top: 2px solid #e5e7eb;'>
                <div style='display: flex; justify-content: space-between;'>
                    <strong style='font-size: 1.25rem;'>Total:</strong>
                    <strong style='font-size: 1.5rem; color: #2563eb;'>{config.get('currency', '$')}{total:.2f}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            payment = st.selectbox("Payment", PAYMENT_METHODS)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear"):
                    st.session_state.cart = []
                    st.rerun()
            with col2:
                if st.button("Complete"):
                    customer_id = None
                    if config.get('enableCustomers', True) and selected_customer != 'Guest':
                        cust = next((c for c in customers if c['name'] == selected_customer), None)
                        if cust:
                            customer_id = cust['id']
                            points = int(total) if config.get('enableLoyalty', True) else 0
                            CustomerDB.update_stats(customer_id, total, points)

                    transaction = {
                        'id': str(uuid4()),
                        'items': [{**item} for item in cart],
                        'subtotal': subtotal,
                        'discount': 0.0,
                        'tax': tax,
                        'tip': 0.0,
                        'total': total,
                        'payment_method': payment,
                        'customer_id': customer_id,
                        'timestamp': datetime.utcnow().isoformat()
                    }

                    TransactionDB.add(transaction)
                    if config.get('enableInventory', True):
                        for item in cart:
                            ProductDB.update_inventory(item['id'], -int(item['cartQuantity']))

                    st.session_state.cart = []
                    st.session_state.last_transaction = transaction
                    st.success("✅ Sale complete!")
                    st.rerun()
        else:
            st.info("Cart is empty")
        st.markdown("</div>", unsafe_allow_html=True)

# ============== PRODUCTS SCREEN ==============

def products_screen():
    config = ConfigDB.get() or {}
    products = ProductDB.get_all()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📦 Products ({len(products)})")
    with col2:
        if st.button("➕ Add"):
            st.session_state.edit_product_id = 'new'
            st.rerun()

    if st.session_state.get('edit_product_id'):
        is_new = st.session_state.edit_product_id == 'new'
        edit = {} if is_new else ProductDB.get_by_id(st.session_state.edit_product_id) or {}

        with st.form("product_form"):
            st.subheader("Add Product" if is_new else "Edit Product")
            data = {}
            col1, col2 = st.columns(2)
            with col1:
                data['name'] = st.text_input("Name *", value=edit.get('name', ''))
                data['price'] = st.number_input("Price *", value=float(edit.get('price', 0.0)), min_value=0.0, step=0.01)
            with col2:
                if config.get('enableInventory', True):
                    data['inventory'] = st.number_input("Stock", value=int(edit.get('inventory', 0)), min_value=0)
                data['category'] = st.text_input("Category", value=edit.get('category', 'General'))

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Cancel"):
                    st.session_state.edit_product_id = None
                    st.rerun()
            with col2:
                if st.form_submit_button("Save"):
                    if data['name'] and float(data['price']) >= 0:
                        data['id'] = edit.get('id', str(uuid4()))
                        if is_new:
                            ProductDB.add(data)
                        else:
                            ProductDB.update(data)
                        st.session_state.edit_product_id = None
                        st.success("Saved!")
                        st.rerun()
                    else:
                        st.error("Name and price required")

    search = st.text_input("🔍 Search products...", key="product_search")
    filtered = [p for p in products if not search or search.lower() in p.get('name', '').lower()]

    if filtered:
        for p in filtered:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            with col1:
                st.markdown(f"**{p['name']}** - {config.get('currency', '$')}{p['price']:.2f}")
            with col2:
                if config.get('enableInventory', True):
                    st.write(f"Stock: {p.get('inventory', 0)}")
            with col3:
                if st.button("Edit", key=f"edit_{p['id']}"):
                    st.session_state.edit_product_id = p['id']
                    st.rerun()
            with col4:
                if st.button("Delete", key=f"del_{p['id']}"):
                    ProductDB.delete(p['id'])
                    st.success("Deleted")
                    st.rerun()
            st.divider()
    else:
        st.info("No products")

# ============== CUSTOMERS SCREEN ==============

def customers_screen():
    config = ConfigDB.get() or {}
    customers = CustomerDB.get_all()

    if not config.get('enableCustomers', True):
        st.warning("Enable in Settings")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"👥 Customers ({len(customers)})")
    with col2:
        if st.button("➕ Add"):
            st.session_state.edit_customer_id = 'new'
            st.rerun()

    if st.session_state.get('edit_customer_id'):
        is_new = st.session_state.edit_customer_id == 'new'
        edit = {} if is_new else (next((c for c in customers if c['id'] == st.session_state.edit_customer_id), {}))

        with st.form("customer_form"):
            st.subheader("Add Customer" if is_new else "Edit Customer")
            data = {}
            data['name'] = st.text_input("Name *", value=edit.get('name', ''))
            col1, col2 = st.columns(2)
            with col1:
                data['email'] = st.text_input("Email", value=edit.get('email', ''))
            with col2:
                data['phone'] = st.text_input("Phone", value=edit.get('phone', ''))

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Cancel"):
                    st.session_state.edit_customer_id = None
                    st.rerun()
            with col2:
                if st.form_submit_button("Save"):
                    if data['name']:
                        data['id'] = edit.get('id', str(uuid4()))
                        if is_new:
                            CustomerDB.add(data)
                        else:
                            CustomerDB.update(data)
                        st.session_state.edit_customer_id = None
                        st.success("Saved!")
                        st.rerun()
                    else:
                        st.error("Name required")

    if customers:
        for c in customers:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{c['name']}**")
                if c.get('email'):
                    st.caption(c['email'])
            with col2:
                st.caption(f"Spent: {config.get('currency', '$')}{c.get('total_spend', 0):.2f}")
                if config.get('enableLoyalty', True):
                    st.caption(f"Points: {c.get('loyalty_points', 0)}")
            with col3:
                if st.button("Edit", key=f"edit_c_{c['id']}"):
                    st.session_state.edit_customer_id = c['id']
                    st.rerun()
            st.divider()
    else:
        st.info("No customers")

# ============== ANALYTICS SCREEN ==============

def analytics_screen():
    config = ConfigDB.get() or {}
    st.subheader("📈 Analytics")

    time_range = st.selectbox("Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days"])
    days = {'Last 7 Days': 7, 'Last 30 Days': 30, 'Last 90 Days': 90}[time_range]
    stats = TransactionDB.get_stats(days)

    if stats['transaction_count'] == 0:
        st.info("No data for this period")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Revenue", f"{config.get('currency', '$')}{stats['total_sales']:.2f}")
    with col2:
        st.metric("Transactions", stats['transaction_count'])
    with col3:
        st.metric("Avg Sale", f"{config.get('currency', '$')}{stats['avg_transaction']:.2f}")
    with col4:
        st.metric("Items Sold", stats['total_items_sold'])

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Products")
        top = get_top_products(10, days=days)
        for i, p in enumerate(top, 1):
            st.write(f"{i}. **{p['name']}** - {p['quantity']} sold - {config.get('currency', '$')}{p['revenue']:.2f}")

    with col2:
        st.subheader("Payment Methods")
        with get_db() as conn:
            results = conn.execute(
                "SELECT payment_method, SUM(total) as total FROM transactions WHERE date(timestamp) >= date('now', ?) GROUP BY payment_method ORDER BY total DESC",
                (f'-{int(days)} days',)
            ).fetchall()
            for r in results:
                st.write(f"**{r['payment_method']}:** {config.get('currency', '$')}{float(r['total'] or 0):.2f}")

# ============== SETTINGS SCREEN ==============

def settings_screen():
    config = ConfigDB.get() or {}
    st.subheader("⚙️ Settings")

    with st.form("settings"):
        config['businessName'] = st.text_input("Business Name", value=config.get('businessName', ''))
        col1, col2 = st.columns(2)
        with col1:
            config['currency'] = st.text_input("Currency", value=config.get('currency', '$'))
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), min_value=0.0, step=0.5)
        with col2:
            config['enableInventory'] = st.checkbox("Inventory Tracking", value=config.get('enableInventory', True))
            config['enableCustomers'] = st.checkbox("Customer Database", value=config.get('enableCustomers', True))

        if st.form_submit_button("Save"):
            ConfigDB.save(config)
            st.success("Saved!")
            st.rerun()

# ============== MAIN ==============

def main():
    st.set_page_config(page_title="POS Pro", page_icon="🏪", layout="wide", initial_sidebar_state="collapsed")
    init_database()
    init_session_state()
    config = ConfigDB.get()
    apply_styles(config or TEMPLATES['cafe'])

    if st.session_state.screen == 'welcome' or not config:
        welcome_screen()
    elif st.session_state.screen == 'setup':
        setup_wizard()
    else:
        header()
        screens = {
            'dashboard': dashboard,
            'pos': pos_screen,
            'products': products_screen,
            'customers': customers_screen,
            'analytics': analytics_screen,
            'settings': settings_screen
        }
        func = screens.get(st.session_state.screen, dashboard)
        func()

if __name__ == "__main__":
    main()
