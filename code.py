import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

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
        'config': None,
        'products': [],
        'customers': [],
        'cart': [],
        'transactions': [],
        'setup_step': 1,
        'show_product_form': False,
        'show_customer_form': False,
        'edit_product': None,
        'edit_customer': None,
        'selected_category': 'All',
        'view_mode': 'grid'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============== STYLING ==============

def apply_global_styles(config):
    """
    Applies global CSS that enforces:
      - True black app background with white text.
      - White cards/forms/receipts with green text.
    """
    # Default green palette (used for white-on-green text)
    green_primary = '#16a34a'  # Emerald-600
    green_accent = '#22c55e'   # Emerald-500

    # Use config theme colors if provided, but prefer green for white-card text
    primary = config['theme'].get('primary', green_primary) if config else green_primary
    accent = config['theme'].get('accent', green_accent) if config else green_accent
    background = '#000000'  # Force true black background

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {{
        font-family: 'Inter', sans-serif;
    }}

    /* ===== APP BACKGROUND (BLACK) ===== */
    .stApp {{
        background-color: {background} !important;
        color: #ffffff !important;
    }}

    /* Most text on the dark app background should be white for readability */
    body, p, span, div, label, h1, h2, h3, h4, h5, h6 {{
        color: #ffffff !important;
    }}

    /* ===== WHITE CARD / PANEL STYLES =====
       Make cards and panels white background with green text.
       We apply to commonly used containers in the app.
    */
    .metric-card,
    .product-card,
    .cart-item,
    .receipt,
    .stForm,
    .stRadio,
    .stSelectbox,
    .stFileUploader,
    .main-header,
    .stTextInput > div > div,
    .stNumberInput > div > div {{
        background: #ffffff !important;
        color: {primary} !important;
        border-radius: 10px;
    }}

    /* Ensure inner text inside white cards is green */
    .metric-card *,
    .product-card *,
    .cart-item *,
    .receipt *,
    .main-header * {{
        color: {primary} !important;
    }}

    /* Muted captions inside white areas: darker green */
    .stat-label,
    .stCaption,
    small,
    .muted-text {{
        color: #166534 !important;
    }}

    /* ===== MAIN HEADER: keep high contrast (black header with white text) ===== */
    .main-header {{
        background: #000000 !important;
        border: 1px solid {accent} !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.35) !important;
    }}
    .main-header h2, .main-header p {{
        color: #ffffff !important;
    }}

    /* ===== BUTTONS ===== */
    .stButton > button {{
        background: {primary} !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: .5rem 0.75rem !important;
    }}
    .stButton > button:hover {{
        background: {accent} !important;
        color: #000000 !important;
        transform: translateY(-2px);
    }}

    /* Secondary button style (neutral) */
    button[aria-label="secondary"] {{
        background: #f3f4f6 !important;
        color: {primary} !important;
    }}

    /* ===== INPUTS ===== */
    input, textarea, select {{
        background: #ffffff !important;
        color: {primary} !important;
        border: 1px solid {accent} !important;
        border-radius: 6px !important;
    }}

    /* ===== BADGES ===== */
    .badge-success {{
        background: #dcfce7 !important;
        color: #166534 !important;
    }}

    .badge-warning {{
        background: #fef9c3 !important;
        color: #854d0e !important;
    }}

    .badge-danger {{
        background: #fee2e2 !important;
        color: #991b1b !important;
    }}

    /* ===== CHARTS / PLOTS - ensure contrast on dark background ===== */
    .stLineChart > div, .stPlotlyChart > div {{
        background: transparent !important;
        color: #ffffff !important;
    }}

    /* ===== RECEIPT PRINTABLE AREA ===== */
    .receipt {{
        padding: 1.25rem !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12) !important;
    }}

    /* Hide default Streamlit menu & footer */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# ============== HELPER FUNCTIONS ==============

def get_sales_stats(transactions, days=30):
    cutoff_date = datetime.now() - timedelta(days=days)
    recent = [t for t in transactions if datetime.fromisoformat(t['timestamp']) >= cutoff_date]
    
    return {
        'total_sales': sum(t['total'] for t in recent),
        'transaction_count': len(recent),
        'avg_transaction': sum(t['total'] for t in recent) / len(recent) if recent else 0,
        'total_items_sold': sum(sum(item['cartQuantity'] for item in t['items']) for t in recent)
    }

def get_top_products(transactions, limit=5):
    product_sales = {}
    for t in transactions:
        for item in t['items']:
            pid = item.get('id', item.get('name'))
            if pid not in product_sales:
                product_sales[pid] = {'name': item['name'], 'quantity': 0, 'revenue': 0}
            product_sales[pid]['quantity'] += item['cartQuantity']
            product_sales[pid]['revenue'] += item['price'] * item['cartQuantity']
    
    return sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:limit]

def calculate_loyalty_points(total, rate=1):
    return int(total * rate)

# ============== WELCOME SCREEN ==============

def welcome_screen():
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
        <h1 style='font-size: 3.5rem; font-weight: 700; background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;'>
            🏪 Universal POS Pro
        </h1>
        <p style='font-size: 1.25rem; color: #c7d2d9; margin-bottom: 0.5rem;'>
            Next-Generation Point of Sale System
        </p>
        <p style='color: #9aa6b0; font-size: 1.05rem;'>
            Complete business management with analytics, inventory, and customer insights
        </p>
    </div>
    """, unsafe_allow_html=True)
   
    col1, col2, col3, col4 = st.columns(4)
    features = [
        ("⚡", "Quick Setup", "Ready in minutes"),
        ("📊", "Analytics", "Real-time insights"),
        ("📦", "Inventory", "Smart tracking"),
        ("👥", "Customers", "Loyalty system")
    ]
    
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(f"""
            <div class='metric-card' style='text-align: center; padding:1rem;'>
                <div style='font-size: 2.2rem; margin-bottom: 0.25rem;'>{icon}</div>
                <h3 style='margin: 0; font-size: 1.05rem;'>{title}</h3>
                <p style='color: #166534; font-size: 0.875rem; margin: 0.35rem 0 0 0;'>{desc}</p>
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
        st.markdown("<p style='text-align: center; color: #9aa6b0;'>Select a template to get started quickly</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
       
        cols = st.columns(3)
        for idx, (key, template) in enumerate(STORE_TEMPLATES.items()):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class='product-card' style='text-align: center; min-height: 200px; padding:1rem;'>
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>{template['icon']}</div>
                    <h3 style='margin: 0;'>{template['name']}</h3>
                    <p style='color: #166534; margin: 0.5rem 0;'>{len(template['fields'])} custom fields</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select", key=f"template_{key}", use_container_width=True, type="primary"):
                    st.session_state.config = {
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
                    st.session_state.setup_step = 2
                    st.rerun()
   
    elif st.session_state.setup_step == 2:
        st.markdown("<h2 style='text-align: center;'>Configure Your Store</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
       
        config = st.session_state.config
       
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
                    st.session_state.screen = 'dashboard'
                    st.success("🎉 Setup complete!")
                    st.rerun()

# ============== HEADER ==============

def header():
    config = st.session_state.config
    
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div class='main-header' style='padding: 1rem 1.5rem;'>
            <h2 style='margin: 0;'>{config.get('businessName', 'Universal POS Pro')}</h2>
            <p style='margin: 0; opacity: 0.9; font-size: 0.9rem;'>{datetime.now().strftime("%A, %B %d, %Y")}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        today_sales = sum(t['total'] for t in st.session_state.transactions 
                         if datetime.fromisoformat(t['timestamp']).date() == datetime.now().date())
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
    config = st.session_state.config
    transactions = st.session_state.transactions
    products = st.session_state.products
    
    st.subheader("📊 Business Overview")
    
    today = datetime.now().date()
    today_trans = [t for t in transactions if datetime.fromisoformat(t['timestamp']).date() == today]
    today_sales = sum(t['total'] for t in today_trans)
    
    stats = get_sales_stats(transactions, 30)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='stat-label'>Today's Revenue</p>
            <p class='stat-number'>{config['currency']}{today_sales:.2f}</p>
            <p class='stat-label'>{len(today_trans)} transactions</p>
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
        top_products = get_top_products(transactions, 5)
        if top_products:
            for i, prod in enumerate(top_products):
                st.markdown(f"""
                <div class='cart-item'>
                    <strong>{i+1}. {prod['name']}</strong><br>
                    <span style='color: #166534;'>Sold: {prod['quantity']} | Revenue: {config['currency']}{prod['revenue']:.2f}</span>
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
    config = st.session_state.config
    products = st.session_state.products
    cart = st.session_state.cart
    
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
                            
                            st.markdown(f"""
                            <div class='product-card {stock_class}' style='padding:1rem;'>
                                <h4 style='margin: 0 0 0.5rem 0;'>{product['name']}</h4>
                                <p style='font-size: 1.15rem; font-weight: 600; margin: 0;'>{config['currency']}{product['price']:.2f}</p>
                                {f"<p style='font-size: 0.875rem; margin: 0.5rem 0 0 0;'>Stock: {stock}</p>" if config.get('enableInventory') else ""}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Add", key=f"add_{product['id']}", 
                                       disabled=stock <= 0 and config.get('enableInventory'), 
                                       use_container_width=True):
                                existing = next((item for item in cart if item['id'] == product['id']), None)
                                if existing:
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
                            existing = next((item for item in cart if item['id'] == product['id']), None)
                            if existing:
                                existing['cartQuantity'] += 1
                            else:
                                cart.append({**product, 'cartQuantity': 1})
                            st.rerun()
        else:
            st.info("No products found")
    
    with col2:
        st.markdown(f"### 🛒 Cart ({len(cart)})")
        
        if config.get('enableCustomers'):
            customers = st.session_state.customers
            customer_names = ['Guest'] + [c['name'] for c in customers]
            selected_customer = st.selectbox("Customer", customer_names, key="pos_customer")
        
        if cart:
            for item in cart:
                st.markdown(f"""
                <div class='cart-item' style='padding:0.75rem;'>
                    <strong>{item['name']}</strong><br>
                    <span style='color: #166534;'>{config['currency']}{item['price']:.2f} × {item['cartQuantity']}</span>
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
            
            tip = st.number_input(f"Tip ({config['currency']})", value=0.0, min_value=0.0, step=0.0)
            
            taxable = subtotal - discount
            tax = taxable * (config['taxRate'] / 100)
            total = taxable + tax + tip
            
            st.markdown(f"""
            **Subtotal:** {config['currency']}{subtotal:.2f}<br>
            **Discount:** -{config['currency']}{discount:.2f}<br>
            **Tax ({config['taxRate']}%):** {config['currency']}{tax:.2f}<br>
            **Tip:** {config['currency']}{tip:.2f}<br>
            <h3 style='color: #16a34a;'>Total: {config['currency']}{total:.2f}</h3>
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
                        customer = next(c for c in st.session_state.customers if c['name'] == selected_customer)
                        customer_id = customer['id']
                        customer['total_spend'] = customer.get('total_spend', 0) + total
                        customer['order_count'] = customer.get('order_count', 0) + 1
                        
                        if config.get('enableLoyalty'):
                            points = calculate_loyalty_points(total, config.get('loyaltyRate', 1))
                            customer['loyalty_points'] = customer.get('loyalty_points', 0) + points
                    
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
                    
                    st.session_state.transactions.insert(0, transaction)
                    
                    if config.get('enableInventory'):
                        for item in cart:
                            product = next(p for p in products if p['id'] == item['id'])
                            product['inventory'] -= item['cartQuantity']
                    
                    st.session_state.cart = []
                    st.session_state.last_transaction = transaction
                    st.session_state.screen = 'receipt'
                    st.rerun()
        else:
            st.info("Cart is empty")

# ============== PRODUCTS SCREEN ==============

def products_screen():
    config = st.session_state.config
    products = st.session_state.products
    
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
                product_data['price'] = st.number_input("Price *", value=float(edit_prod.get('price', 0)), min_value=0.01, step=0.01)
            with col2:
                if config.get('enableInventory'):
                    product_data['inventory'] = st.number_input("Stock *", value=int(edit_prod.get('inventory', 0)), min_value=0)
                
                categories = list(set(p.get('category', 'General') for p in products)) + ['General', 'New Category']
                product_data['category'] = st.selectbox("Category", categories)
            
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
                        idx = products.index(st.session_state.edit_product)
                        products[idx] = product_data
                    else:
                        products.append(product_data)
                    
                    st.session_state.show_product_form = False
                    st.session_state.edit_product = None
                    st.success("Product saved!")
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
                        <div class='product-card' style='padding:1rem;'>
                            <h4>{product['name']}</h4>
                            <p style='font-size:1.05rem; margin:0;'>{config['currency']}{product['price']:.2f}</p>
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
                                products.remove(product)
                                st.rerun()
    else:
        st.info("No products found")

# ============== CUSTOMERS SCREEN ==============

def customers_screen():
    config = st.session_state.config
    customers = st.session_state.customers
    
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
                        idx = customers.index(st.session_state.edit_customer)
                        customers[idx] = customer_data
                    else:
                        customers.append(customer_data)
                    
                    st.session_state.show_customer_form = False
                    st.session_state.edit_customer = None
                    st.success("Customer saved!")
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
                        customers.remove(customer)
                        st.rerun()
            st.divider()
    else:
        st.info("No customers found")

# ============== ANALYTICS SCREEN ==============

def analytics_screen():
    config = st.session_state.config
    transactions = st.session_state.transactions
    
    st.subheader("📈 Business Analytics")
    
    if not transactions:
        st.info("No transaction data available yet. Complete some sales to see analytics.")
        return
    
    # Time range selector
    time_range = st.selectbox("Time Range", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])
    
    days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90, "All Time": 99999}
    days = days_map[time_range]
    
    cutoff = datetime.now() - timedelta(days=days)
    filtered_trans = [t for t in transactions if datetime.fromisoformat(t['timestamp']) >= cutoff]
    
    # Key metrics
    total_revenue = sum(t['total'] for t in filtered_trans)
    total_transactions = len(filtered_trans)
    avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
    total_items = sum(sum(item['cartQuantity'] for item in t['items']) for t in filtered_trans)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Revenue", f"{config['currency']}{total_revenue:.2f}")
    with col2:
        st.metric("Transactions", total_transactions)
    with col3:
        st.metric("Avg Sale", f"{config['currency']}{avg_transaction:.2f}")
    with col4:
        st.metric("Items Sold", total_items)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top Products")
        top_products = get_top_products(filtered_trans, 10)
        if top_products:
            for i, prod in enumerate(top_products):
                st.markdown(f"""
                {i+1}. **{prod['name']}** - {prod['quantity']} sold - {config['currency']}{prod['revenue']:.2f}
                """)
    
    with col2:
        st.subheader("💳 Payment Methods")
        payment_breakdown = {}
        for t in filtered_trans:
            method = t.get('payment_method', 'Cash')
            payment_breakdown[method] = payment_breakdown.get(method, 0) + t['total']
        
        if payment_breakdown:
            for method, total in sorted(payment_breakdown.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"**{method}:** {config['currency']}{total:.2f}")
    
    # Daily sales chart data
    if filtered_trans:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📊 Daily Sales Trend")
        
        daily_sales = {}
        for t in filtered_trans:
            date = datetime.fromisoformat(t['timestamp']).date()
            daily_sales[date] = daily_sales.get(date, 0) + t['total']
        
        if daily_sales:
            df = pd.DataFrame(list(daily_sales.items()), columns=['Date', 'Sales'])
            df = df.sort_values('Date')
            st.line_chart(df.set_index('Date'))

# ============== SETTINGS SCREEN ==============

def settings_screen():
    config = st.session_state.config
    
    st.subheader("⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["Business Info", "Features", "Data Management"])
    
    with tab1:
        config['businessName'] = st.text_input("Business Name", value=config.get('businessName', ''))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            config['currency'] = st.text_input("Currency", value=config.get('currency', '$'))
        with col2:
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), 
                                               min_value=0.0, step=0.5)
        with col3:
            config['lowStockThreshold'] = st.number_input("Low Stock Threshold", 
                                                         value=int(config.get('lowStockThreshold', 5)), 
                                                         min_value=1)
        
        config['receiptFooter'] = st.text_area("Receipt Footer", value=config.get('receiptFooter', 'Thank you!'))
    
    with tab2:
        config['enableInventory'] = st.checkbox("Enable Inventory Tracking", value=config.get('enableInventory', True))
        config['enableCustomers'] = st.checkbox("Enable Customer Database", value=config.get('enableCustomers', True))
        config['enableLoyalty'] = st.checkbox("Enable Loyalty Program", value=config.get('enableLoyalty', True))
        
        if config['enableLoyalty']:
            config['loyaltyRate'] = st.number_input("Loyalty Points per $1", 
                                                   value=float(config.get('loyaltyRate', 1)), 
                                                   min_value=0.1, step=0.1)
    
    with tab3:
        st.markdown("#### Export Data")
        if st.button("📥 Export All Data"):
            data = {
                'config': config,
                'products': st.session_state.products,
                'customers': st.session_state.customers,
                'transactions': st.session_state.transactions[-100:]
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(data, indent=2, default=str),
                file_name=f"pos-backup-{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        st.markdown("#### Import Data")
        uploaded = st.file_uploader("Upload backup file", type=['json'])
        if uploaded:
            try:
                data = json.load(uploaded)
                if 'config' in data:
                    st.session_state.config = data['config']
                if 'products' in data:
                    st.session_state.products = data['products']
                if 'customers' in data:
                    st.session_state.customers = data['customers']
                if 'transactions' in data:
                    st.session_state.transactions = data['transactions']
                st.success("Data imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error importing: {str(e)}")

# ============== RECEIPT SCREEN ==============

def receipt_screen():
    config = st.session_state.config
    transaction = st.session_state.get('last_transaction')
    
    if not transaction:
        st.error("No transaction found")
        st.session_state.screen = 'pos'
        st.rerun()
        return
    
    customer_name = "Guest"
    if transaction.get('customer_id'):
        customer = next((c for c in st.session_state.customers if c['id'] == transaction['customer_id']), None)
        if customer:
            customer_name = customer['name']
    
    st.markdown(f"""
    <div class='receipt' style='text-align: center;'>
        <div style='background: transparent; padding: 1.25rem; border-radius: 8px;'>
            <h2 style='margin: 0;'>{config['businessName'] or 'Universal POS Pro'}</h2>
            <p style='margin: 0.35rem 0 0 0; color: #166534;'>Receipt #{transaction['id'][:8]}</p>
            <p style='margin: 0; color: #166534;'>{datetime.fromisoformat(transaction['timestamp']).strftime("%B %d, %Y %I:%M %p")}</p>
            <p style='margin: 0; color: #166534;'>Customer: {customer_name}</p>
        </div>
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
        st.markdown("<h2 style='color: #166534;'>**Total:**</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h2 style='color: #16a34a;'>{config['currency']}{transaction['total']:.2f}</h2>",
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
    
    init_session_state()
    # Ensure config exists for styling defaults when first loaded
    if not st.session_state.config:
        # default to retail template to have a theme object
        st.session_state.config = {
            'businessType': 'retail',
            'businessName': 'My Store',
            'theme': STORE_TEMPLATES['retail']['theme'],
            'fields': STORE_TEMPLATES['retail']['fields'].copy(),
            'taxRate': STORE_TEMPLATES['retail']['taxRate'],
            'currency': STORE_TEMPLATES['retail']['currency'],
            'discountRate': 0,
            'showTax': True,
            'receiptFooter': 'Thank you for your business!',
            'enableInventory': True,
            'enableCustomers': True,
            'enableLoyalty': True,
            'loyaltyRate': 1,
            'lowStockThreshold': 5
        }

    apply_global_styles(st.session_state.config)
    
    if st.session_state.screen == 'welcome':
        welcome_screen()
    elif st.session_state.screen == 'setup':
        setup_wizard()
    elif st.session_state.config:
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
