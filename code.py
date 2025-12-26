
import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any
import base64

# Store templates configuration
STORE_TEMPLATES = {
    'cafe': {
        'name': 'Café/Coffee Shop',
        'icon': '☕',
        'fields': [
            {'id': 'name', 'type': 'text', 'label': 'Item', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'price', 'type': 'number', 'label': 'Price', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'quantity', 'type': 'number', 'label': 'Quantity', 'required': False, 'showInCart': True, 'showInReceipt': False},
            {'id': 'size', 'type': 'select', 'label': 'Size', 'options': ['Small', 'Medium', 'Large'], 'required': False, 'showInCart': True, 'showInReceipt': True},
            {'id': 'temperature', 'type': 'select', 'label': 'Temperature', 'options': ['Hot', 'Iced'], 'required': False, 'showInCart': False, 'showInReceipt': False}
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
            {'id': 'quantity', 'type': 'number', 'label': 'Qty', 'required': False, 'showInCart': True, 'showInReceipt': False},
            {'id': 'category', 'type': 'text', 'label': 'Category', 'required': False, 'showInCart': False, 'showInReceipt': False},
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
            {'id': 'quantity', 'type': 'number', 'label': 'Qty', 'required': False, 'showInCart': True, 'showInReceipt': False},
            {'id': 'category', 'type': 'select', 'label': 'Category', 'options': ['Appetizer', 'Main Course', 'Dessert', 'Beverage'], 'required': False, 'showInCart': False, 'showInReceipt': False},
            {'id': 'spiceLevel', 'type': 'select', 'label': 'Spice Level', 'options': ['Mild', 'Medium', 'Hot', 'Extra Hot'], 'required': False, 'showInCart': True, 'showInReceipt': True},
        ],
        'theme': {'primary': '#dc2626', 'secondary': '#ef4444', 'background': '#fef2f2', 'accent': '#f87171'},
        'taxRate': 8,
        'currency': '$'
    },
    'custom': {
        'name': 'Custom Store',
        'icon': '⚙️',
        'fields': [
            {'id': 'name', 'type': 'text', 'label': 'Item Name', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'price', 'type': 'number', 'label': 'Price', 'required': True, 'showInCart': True, 'showInReceipt': True},
            {'id': 'quantity', 'type': 'number', 'label': 'Quantity', 'required': False, 'showInCart': True, 'showInReceipt': False}
        ],
        'theme': {'primary': '#6366f1', 'secondary': '#818cf8', 'background': '#eef2ff', 'accent': '#a5b4fc'},
        'taxRate': 10,
        'currency': '$'
    }
}

FIELD_TYPES = [
    {'value': 'text', 'label': 'Text Input'},
    {'value': 'number', 'label': 'Number'},
    {'value': 'select', 'label': 'Dropdown'},
    {'value': 'textarea', 'label': 'Long Text'},
    {'value': 'date', 'label': 'Date'},
    {'value': 'time', 'label': 'Time'}
]

# Initialize session state
def init_session_state():
    defaults = {
        'screen': 'welcome',
        'config': None,
        'products': [],
        'customers': [],  # New: Customer database
        'cart': [],
        'transactions': [],
        'setup_step': 1,
        'current_discount': 0,
        'show_product_form': False,
        'show_customer_form': False,  # New: For customer form
        'edit_product': None,
        'edit_customer': None  # New: For editing customers
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Global CSS for black text and professional styling
def apply_global_styles(config):
    primary = config['theme']['primary'] if config else '#6366f1'
    background = config['theme']['background'] if config else '#ffffff'
    accent = config['theme']['accent'] if config else '#a5b4fc'
    
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {background};
        color: black;
    }}
    .main-header {{
        background-color: {primary};
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }}
    .stat-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: black;
    }}
    .product-card {{
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid {accent};
        cursor: pointer;
        color: black;
    }}
    .stTextInput > div > div > input {{
        color: black;
    }}
    .stNumberInput > div > div > input {{
        color: black;
    }}
    .stSelectbox > div > div > select {{
        color: black;
    }}
    .stButton > button {{
        color: black;
    }}
    .stMetric > label {{
        color: black;
    }}
    .stWrite {{
        color: black;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: black;
    }}
    .low-stock {{
        color: orange;
        font-weight: bold;
    }}
    .out-of-stock {{
        color: red;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

def welcome_screen():
    st.markdown("""
    <div style='text-align: center; padding: 3rem;'>
        <h1 style='font-size: 3rem; color: black;'>🏪 Universal POS</h1>
        <p style='font-size: 1.5rem; color: black;'>The Point of Sale System That Adapts to YOU</p>
        <p style='color: #666;'>Customize every field, color, and feature for your unique business</p>
    </div>
    """, unsafe_allow_html=True)
   
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("⚡ **Quick Setup**\n\nStart with templates or build from scratch")
    with col2:
        st.info("🎨 **Fully Custom**\n\nDesign, fields, and workflow")
    with col3:
        st.info("📐 **Any Business**\n\nCafé to pharmacy to boutique")
   
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Get Started →", type="primary", use_container_width=True):
        st.session_state.screen = 'setup'
        st.rerun()

def setup_wizard():
    if st.session_state.setup_step == 1:
        st.title("Choose Your Starting Point")
        st.write("Pick a template to customize or start from scratch")
       
        cols = st.columns(4)
        for idx, (key, template) in enumerate(STORE_TEMPLATES.items()):
            with cols[idx % 4]:
                if st.button(f"{template['icon']}\n\n**{template['name']}**\n\n{len(template['fields'])} fields",
                           key=f"template_{key}", use_container_width=True):
                    st.session_state.config = {
                        'businessType': key,
                        'businessName': '',
                        'theme': template['theme'],
                        'fields': template['fields'].copy(),  # Copy to avoid mutation
                        'taxRate': template['taxRate'],
                        'currency': template['currency'],
                        'discountRate': 0,
                        'showTax': True,
                        'showDiscount': True,
                        'receiptFooter': 'Thank you for your business!',
                        'enableInventory': True,  # Enable inventory by default
                        'enableCustomers': True  # New: Enable customer database
                    }
                    st.session_state.current_discount = template['taxRate']
                    st.session_state.setup_step = 2
                    st.rerun()
        # Custom option
        if st.button("⚙️ Start Custom", use_container_width=True):
            st.session_state.config = STORE_TEMPLATES['custom'].copy()
            st.session_state.config.update({
                'businessType': 'custom', 
                'businessName': '', 
                'fields': STORE_TEMPLATES['custom']['fields'].copy(),
                'enableInventory': True,
                'enableCustomers': True
            })
            st.session_state.setup_step = 2
            st.rerun()
   
    elif st.session_state.setup_step == 2:
        st.title("Customize Your Store")
       
        config = st.session_state.config
       
        config['businessName'] = st.text_input("Business Name", value=config.get('businessName', ''), help="Enter your business name for receipts and headers")
       
        col1, col2 = st.columns(2)
        with col1:
            config['currency'] = st.text_input("Currency Symbol", value=config.get('currency', '$'), max_chars=1, help="e.g., $, €, £")
        with col2:
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), min_value=0.0, step=0.1, help="Sales tax percentage")
       
        config['discountRate'] = st.number_input("Default Discount (%)", value=float(config.get('discountRate', 0)), min_value=0.0, max_value=100.0, step=0.1, help="Default discount applied to sales")
       
        config['enableInventory'] = st.checkbox("Enable Inventory Tracking", value=config.get('enableInventory', True), help="Track stock levels and prevent overselling")
       
        config['enableCustomers'] = st.checkbox("Enable Customer Database", value=config.get('enableCustomers', True), help="Manage customer profiles and loyalty")
       
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.setup_step = 1
                st.rerun()
        with col2:
            if st.button("Next: Customize Fields →", type="primary"):
                st.session_state.setup_step = 3
                st.rerun()
   
    elif st.session_state.setup_step == 3:
        field_customizer()

def field_customizer():
    st.title("Customize Your Fields")
    st.write("Add, remove, or modify fields to match your business needs. Fields marked as required must be filled when adding products.")
   
    config = st.session_state.config
   
    # Ensure name and price fields are always present and required
    if not any(f['id'] == 'name' for f in config['fields']):
        config['fields'].insert(0, {'id': 'name', 'type': 'text', 'label': 'Item Name', 'required': True, 'showInCart': True, 'showInReceipt': True})
    if not any(f['id'] == 'price' for f in config['fields']):
        config['fields'].insert(1, {'id': 'price', 'type': 'number', 'label': 'Price', 'required': True, 'showInCart': True, 'showInReceipt': True})
    
    # Add inventory field if enabled
    if config.get('enableInventory', False):
        inventory_field = {'id': 'inventory', 'type': 'number', 'label': 'Inventory (Stock Qty)', 'required': True, 'showInCart': False, 'showInReceipt': False, 'default': 0}
        if not any(f['id'] == 'inventory' for f in config['fields']):
            config['fields'].append(inventory_field)
   
    # Display existing fields with better editing
    for idx, field in enumerate(config['fields']):
        if field['id'] in ['name', 'price', 'inventory']:  # Protect core fields
            expanded = True
        else:
            expanded = False
        with st.expander(f"{field['label']} ({field['type']}) {'(Protected)' if field['id'] in ['name', 'price', 'inventory'] else ''}", expanded=expanded):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                field['label'] = st.text_input("Label", value=field['label'], key=f"label_{idx}", help="Display name for this field")
            with col2:
                field['required'] = st.checkbox("Required", value=field['required'], key=f"req_{idx}", help="Must be filled for products")
            with col3:
                field['showInCart'] = st.checkbox("Show in Cart", value=field['showInCart'], key=f"cart_{idx}")
            with col4:
                field['showInReceipt'] = st.checkbox("Show in Receipt", value=field['showInReceipt'], key=f"receipt_{idx}")
            
            if field['type'] == 'select' and field['id'] not in ['name', 'price', 'inventory']:
                options_str = st.text_input("Options (comma-separated)", value=', '.join(field.get('options', [])), key=f"opts_{idx}", help="e.g., Small, Medium, Large")
                field['options'] = [opt.strip() for opt in options_str.split(',') if opt.strip()]
            
            if field['id'] not in ['name', 'price', 'inventory']:
                if st.button("Remove Field", key=f"remove_{idx}", type="secondary"):
                    del config['fields'][idx]
                    st.success(f"Removed {field['label']}")
                    st.rerun()
   
    # Add new field
    with st.expander("➕ Add New Field", expanded=False):
        new_label = st.text_input("Field Label", help="What should this field be called?")
        new_type = st.selectbox("Field Type", [t['value'] for t in FIELD_TYPES],
                               format_func=lambda x: next(t['label'] for t in FIELD_TYPES if t['value'] == x),
                               help="Choose the input type")
       
        new_options = []
        if new_type == 'select':
            new_options_str = st.text_input("Options (comma separated)", help="e.g., Red, Blue, Green")
            new_options = [opt.strip() for opt in new_options_str.split(',') if opt.strip()]
       
        new_required = st.checkbox("Required", value=False, help="Must be filled for products")
        new_show_cart = st.checkbox("Show in Cart", value=True)
        new_show_receipt = st.checkbox("Show in Receipt", value=True)
       
        if st.button("Add Field", type="primary"):
            if new_label:
                new_field = {
                    'id': f"custom_{len(config['fields'])}_{int(datetime.now().timestamp())}",
                    'type': new_type,
                    'label': new_label,
                    'options': new_options,
                    'required': new_required,
                    'showInCart': new_show_cart,
                    'showInReceipt': new_show_receipt
                }
                config['fields'].append(new_field)
                st.success(f"Added '{new_label}'")
                st.rerun()
            else:
                st.error("Please enter a label for the field.")
   
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.setup_step = 2
            st.rerun()
    with col2:
        if st.button("Complete Setup ✓", type="primary"):
            st.session_state.screen = 'dashboard'
            st.rerun()

def header():
    config = st.session_state.config
   
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"<h1 style='color: black;'>{config['businessName'] or 'Universal POS'}</h1>",
                   unsafe_allow_html=True)
   
    with col2:
        # Navigation
        nav_screens = ['dashboard', 'pos', 'products', 'customers', 'settings']  # Added 'customers'
        current_index = nav_screens.index(st.session_state.screen) if st.session_state.screen in nav_screens else 0
       
        screen = st.selectbox("Navigate:", ['Dashboard', 'POS', 'Products', 'Customers', 'Settings'],
                             index=current_index,
                             label_visibility='collapsed',
                             key='nav_select')
        st.session_state.screen = screen.lower()

def dashboard():
    config = st.session_state.config
    transactions = st.session_state.transactions
    products = st.session_state.products
    customers = st.session_state.customers  # New: Customers
   
    # Calculate statistics
    today = datetime.now().date()
    today_transactions = [t for t in transactions if datetime.fromisoformat(t['timestamp']).date() == today]
    today_sales = sum(t['total'] for t in today_transactions)
    all_time_sales = sum(t['total'] for t in transactions)
    
    # Inventory stats
    if config.get('enableInventory', False):
        low_stock_threshold = 5  # Configurable in future
        low_stock_products = sum(1 for p in products if p.get('inventory', 0) <= low_stock_threshold and p.get('inventory', 0) > 0)
        out_of_stock = sum(1 for p in products if p.get('inventory', 0) <= 0)
    
    # Customer stats
    if config.get('enableCustomers', False):
        active_customers = len(customers)
        total_customer_spend = sum(t['total'] for t in transactions if t.get('customer_id'))
   
    # Stats cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Today's Sales", f"{config['currency']}{today_sales:.2f}",
                 f"{len(today_transactions)} transactions")
    with col2:
        st.metric("Products", len(products), "items in catalog")
    with col3:
        st.metric("All-Time Sales", f"{config['currency']}{all_time_sales:.2f}",
                 f"{len(transactions)} total")
    
    if config.get('enableInventory', False):
        col4, col5 = st.columns(2)
        with col4:
            st.metric("Low Stock", low_stock_products, f"Alert threshold: ≤{low_stock_threshold}")
        with col5:
            st.metric("Out of Stock", out_of_stock, "Needs restock")
    
    if config.get('enableCustomers', False):
        col6, col7 = st.columns(2)
        with col6:
            st.metric("Customers", active_customers, "registered profiles")
        with col7:
            st.metric("Customer Spend", f"{config['currency']}{total_customer_spend:.2f}", "total from tracked sales")
   
    # Quick actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🛒 Start New Sale", type="primary", use_container_width=True):
            st.session_state.screen = 'pos'
            st.rerun()
    with col2:
        if st.button("➕ Manage Products", use_container_width=True):
            st.session_state.screen = 'products'
            st.rerun()
    with col3:
        if config.get('enableCustomers', False):
            if st.button("👥 Manage Customers", use_container_width=True):
                st.session_state.screen = 'customers'
                st.rerun()
   
    # Recent transactions table for better professionalism
    if today_transactions:
        st.subheader("Recent Transactions")
        trans_data = []
        for t in today_transactions[:10]:  # Limit to 10
            customer_name = next((c['name'] for c in customers if c['id'] == t.get('customer_id')), 'Guest')
            trans_data.append({
                'Time': datetime.fromisoformat(t['timestamp']).strftime("%I:%M %p"),
                'Customer': customer_name,
                'Items': len(t['items']),
                'Total': f"{config['currency']}{t['total']:.2f}"
            })
        st.table(trans_data)

def pos_screen():
    config = st.session_state.config
    products = st.session_state.products
    customers = st.session_state.customers  # New
    cart = st.session_state.cart
   
    enable_inventory = config.get('enableInventory', False)
    enable_customers = config.get('enableCustomers', False)
    
    col1, col2 = st.columns([2, 1])
   
    with col1:
        st.subheader("Products")
        search = st.text_input("🔍 Search products...", help="Type to filter products by name")
       
        filtered_products = [p for p in products if search.lower() in p.get('name', '').lower()] if search else products
       
        if filtered_products:
            # Use columns for better layout, limit to 3 per row
            for i in range(0, len(filtered_products), 3):
                cols = st.columns(3)
                for j, product in enumerate(filtered_products[i:i+3]):
                    with cols[j]:
                        stock_class = ""
                        if enable_inventory:
                            stock = product.get('inventory', 0)
                            if stock <= 0:
                                stock_class = "out-of-stock"
                            elif stock <= 5:
                                stock_class = "low-stock"
                        
                        btn_disabled = enable_inventory and product.get('inventory', 0) <= 0
                        btn_text = f"**{product['name']}**\n\n{config['currency']}{product['price']:.2f}"
                        if enable_inventory:
                            btn_text += f"\n\nStock: {product.get('inventory', 0)}"
                        
                        if st.button(btn_text, key=f"prod_{product['id']}", use_container_width=True, disabled=btn_disabled):
                            # Check stock before adding
                            if enable_inventory and product.get('inventory', 0) <= 0:
                                st.error(f"{product['name']} is out of stock!")
                                st.rerun()
                            else:
                                # Add to cart with all fields
                                cart_item = {**product, 'cartQuantity': 1}
                                existing = next((item for item in cart if item['id'] == product['id']), None)
                                if existing:
                                    if enable_inventory and (existing['cartQuantity'] + 1 > product.get('inventory', float('inf'))):
                                        st.error(f"Not enough stock for {product['name']}!")
                                        st.rerun()
                                    else:
                                        existing['cartQuantity'] += 1
                                else:
                                    cart.append(cart_item)
                                st.rerun()
                        
                        if stock_class:
                            st.markdown(f"<span class='{stock_class}'>⚠️ {stock_class.replace('-', ' ').title()}</span>", unsafe_allow_html=True)
        else:
            st.info("No products found. Add products in the Products section.")
   
    with col2:
        st.subheader(f"Cart ({len(cart)} items)")
        
        # New: Customer selection
        if enable_customers:
            selected_customer = st.selectbox("Select Customer", ["Guest"] + [c['name'] for c in customers], key="customer_select")
            if selected_customer != "Guest":
                current_customer = next((c for c in customers if c['name'] == selected_customer), None)
                st.caption(f"Customer: {current_customer['name']} | Total Orders: {len([t for t in st.session_state.transactions if t.get('customer_id') == current_customer['id']])}")
        
        if cart:
            for item in cart:
                with st.container():
                    # Display item name and price
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**{item['name']}**")
                        st.caption(f"{config['currency']}{item['price']:.2f} × {item['cartQuantity']}")
                        # Show other fields if showInCart
                        for field in config['fields']:
                            if field['id'] not in ['name', 'price', 'inventory'] and field.get('showInCart', False) and item.get(field['id']):
                                st.caption(f"{field['label']}: {item[field['id']]}")
                        
                        # Show remaining stock
                        if enable_inventory:
                            remaining = item.get('inventory', 0) - item['cartQuantity']
                            st.caption(f"Remaining stock: {remaining}")
                    with col_b:
                        st.write(f"**{config['currency']}{(item['price'] * item['cartQuantity']):.2f}**")
                   
                    # Controls
                    col_x, col_y, col_z = st.columns([1, 1, 1])
                    with col_x:
                        if st.button("➖", key=f"dec_{item['id']}", use_container_width=True):
                            item['cartQuantity'] -= 1
                            if item['cartQuantity'] <= 0:
                                cart.remove(item)
                            st.rerun()
                    with col_y:
                        if st.button("➕", key=f"inc_{item['id']}", use_container_width=True):
                            if not enable_inventory or (item['cartQuantity'] + 1 <= item.get('inventory', float('inf'))):
                                item['cartQuantity'] += 1
                                st.rerun()
                            else:
                                st.error(f"Not enough stock for {item['name']}!")
                    with col_z:
                        if st.button("🗑️", key=f"del_{item['id']}", type="secondary", use_container_width=True):
                            cart.remove(item)
                            st.rerun()
                    st.divider()
           
            # Totals with validation
            subtotal = sum(item['price'] * item['cartQuantity'] for item in cart)
            discount_rate = st.number_input("Discount (%)", value=float(config.get('discountRate', 0)), min_value=0.0, max_value=100.0, step=0.1, help="Apply discount to subtotal")
            discount = subtotal * (discount_rate / 100)
            taxable = subtotal - discount
            tax = taxable * (config['taxRate'] / 100) if config.get('showTax', True) else 0
            total = taxable + tax
           
            st.divider()
            st.write(f"**Subtotal:** {config['currency']}{subtotal:.2f}")
            if discount > 0:
                st.write(f"**Discount:** -{config['currency']}{discount:.2f}")
            if tax > 0:
                st.write(f"**Tax ({config['taxRate']}%)**: {config['currency']}{tax:.2f}")
            st.markdown(f"**Total: {config['currency']}{total:.2f}**")
           
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear Cart", type="secondary", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()
            with col2:
                if st.button("Complete Sale", type="primary", use_container_width=True, disabled=subtotal == 0):
                    if subtotal > 0:  # Validation
                        # Check overall stock for all cart items
                        stock_ok = True
                        if enable_inventory:
                            for item in cart:
                                if item['cartQuantity'] > item.get('inventory', 0):
                                    stock_ok = False
                                    st.error(f"Insufficient stock for {item['name']}")
                                    break
                        
                        if stock_ok:
                            customer_id = None
                            if enable_customers and selected_customer != "Guest":
                                customer_id = current_customer['id']
                            
                            transaction = {
                                'id': str(datetime.now().timestamp()),
                                'items': [{**item, 'cartQuantity': item['cartQuantity']} for item in cart],  # Copy with quantity
                                'subtotal': subtotal,
                                'discount': discount,
                                'tax': tax,
                                'total': total,
                                'timestamp': datetime.now().isoformat(),
                                'customer_id': customer_id  # New: Associate with customer
                            }
                            st.session_state.transactions.insert(0, transaction)
                            
                            # Decrement inventory
                            if enable_inventory:
                                for item in cart:
                                    product = next(p for p in products if p['id'] == item['id'])
                                    product['inventory'] -= item['cartQuantity']
                            
                            # Update customer total spend if applicable
                            if customer_id:
                                for cust in customers:
                                    if cust['id'] == customer_id:
                                        cust['total_spend'] = cust.get('total_spend', 0) + total
                                        cust['order_count'] = cust.get('order_count', 0) + 1
                                        break
                            
                            st.session_state.cart = []
                            st.session_state.last_transaction = transaction
                            st.session_state.screen = 'receipt'
                            st.rerun()
                        else:
                            st.warning("Cannot complete sale due to insufficient stock. Please adjust cart.")
                    else:
                        st.error("Cart is empty. Add items to proceed.")
        else:
            st.info("Your cart is empty. Select products to add.")

def customers_screen():  # New: Customers management screen
    config = st.session_state.config
    customers = st.session_state.customers
    enable_customers = config.get('enableCustomers', False)
    
    if not enable_customers:
        st.warning("Customer database is disabled in settings.")
        if st.button("Go to Settings"):
            st.session_state.screen = 'settings'
            st.rerun()
        return
    
    st.subheader(f"Customer Database ({len(customers)} customers)")
    
    # Search
    search = st.text_input("🔍 Search customers...", key="cust_search")
    filtered_customers = [c for c in customers if search.lower() in c.get('name', '').lower()] if search else customers
    
    # Add customer button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Customer", type="primary"):
            st.session_state.show_customer_form = True
            st.session_state.edit_customer = None
            st.rerun()
    
    # Customer form
    if st.session_state.get('show_customer_form', False):
        is_edit = st.session_state.edit_customer is not None
        st.markdown("---")
        with st.form("customer_form"):
            st.subheader("Add/Edit Customer" + (" (Editing)" if is_edit else ""))
            cust_data = {}
            errors = []
            edit_cust = st.session_state.edit_customer or {}
            
            # Standard customer fields
            cust_data['name'] = st.text_input("Full Name", value=edit_cust.get('name', ''), help="Customer's full name")
            cust_data['email'] = st.text_input("Email", value=edit_cust.get('email', ''), help="Contact email")
            cust_data['phone'] = st.text_input("Phone", value=edit_cust.get('phone', ''), help="Phone number")
            cust_data['address'] = st.text_area("Address", value=edit_cust.get('address', ''), help="Billing address")
            cust_data['notes'] = st.text_area("Notes", value=edit_cust.get('notes', ''), max_chars=500, help="Any additional notes")
            cust_data['total_spend'] = st.number_input("Total Spend (auto-tracked)", value=float(edit_cust.get('total_spend', 0)), disabled=True)
            cust_data['order_count'] = st.number_input("Order Count (auto-tracked)", value=int(edit_cust.get('order_count', 0)), disabled=True)
            
            if st.form_submit_button("Save Customer", type="primary"):
                if not cust_data['name']:
                    st.error("Name is required.")
                else:
                    cust_data['id'] = edit_cust.get('id', str(datetime.now().timestamp()))
                    # Check duplicate
                    duplicate = next((c for c in customers if c['name'].lower() == cust_data['name'].lower() and c['id'] != cust_data['id']), None)
                    if duplicate:
                        duplicate.update(cust_data)
                        st.success("Customer updated!")
                    else:
                        customers.append(cust_data)
                        st.success("Customer added!")
                    st.session_state.show_customer_form = False
                    st.session_state.edit_customer = None
                    st.rerun()
            
            if st.form_submit_button("Cancel", type="secondary"):
                st.session_state.show_customer_form = False
                st.session_state.edit_customer = None
                st.rerun()
    
    # Display customers
    if filtered_customers:
        for cust in filtered_customers:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.write(f"**{cust.get('name', 'Unnamed')}**")
                if cust.get('email'):
                    st.caption(f"Email: {cust['email']}")
                if cust.get('phone'):
                    st.caption(f"Phone: {cust['phone']}")
                if cust.get('total_spend', 0) > 0:
                    st.caption(f"Total Spend: {config['currency']}{cust['total_spend']:.2f} | Orders: {cust.get('order_count', 0)}")
            with col2:
                if cust.get('address'):
                    st.caption(cust['address'][:50] + "..." if len(cust['address']) > 50 else cust['address'])
                if cust.get('notes'):
                    st.caption(f"Notes: {cust['notes'][:30]}...")
            with col3:
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Edit", key=f"edit_cust_{cust['id']}"):
                        st.session_state.edit_customer = cust
                        st.session_state.show_customer_form = True
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_cust_{cust['id']}"):
                        if cust in st.session_state.customers:
                            st.session_state.customers.remove(cust)
                            st.success("Customer deleted.")
                            st.rerun()
            st.divider()
    else:
        st.info("No customers found. Add your first customer!")

def products_screen():
    config = st.session_state.config
    products = st.session_state.products
    enable_inventory = config.get('enableInventory', False)
   
    st.subheader(f"Product Catalog ({len(products)} items)")
   
    # Add product button
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search products...", key="prod_search")
        filtered = [p for p in products if search.lower() in p.get('name', '').lower()] if search else products
    with col2:
        if st.button("➕ Add Product", type="primary"):
            st.session_state.show_product_form = True
            st.session_state.edit_product = None
            st.rerun()
   
    # Product form with validation
    if st.session_state.get('show_product_form', False):
        is_edit = st.session_state.edit_product is not None
        st.markdown("---")
        with st.form("product_form"):
            st.subheader("Add/Edit Product" + (" (Editing)" if is_edit else ""))
            product_data = {}
            errors = []
            edit_prod = st.session_state.edit_product or {}
            
            for field in config['fields']:
                field_id = field['id']
                default_val = edit_prod.get(field_id, field.get('default', ''))
                if field['type'] == 'text':
                    product_data[field_id] = st.text_input(field['label'], value=default_val if isinstance(default_val, str) else '', placeholder=f"Enter {field['label'].lower()}", key=f"prod_{field_id}")
                elif field['type'] == 'number':
                    min_val = 0.01 if field_id == 'price' else 0
                    step = 0.01 if field_id == 'price' else 1
                    format_str = "%.2f" if field_id == 'price' else "%.0f"
                    product_data[field_id] = st.number_input(field['label'], value=float(default_val) if default_val else 0.0, min_value=min_val, step=step, format=format_str, key=f"prod_{field_id}")
                elif field['type'] == 'select':
                    options = [''] + field.get('options', [])
                    product_data[field_id] = st.selectbox(field['label'], options, index=options.index(default_val) if default_val in options else 0, key=f"prod_{field_id}")
                elif field['type'] == 'textarea':
                    product_data[field_id] = st.text_area(field['label'], value=default_val if isinstance(default_val, str) else '', key=f"prod_{field_id}")
                elif field['type'] == 'date':
                    product_data[field_id] = st.date_input(field['label'], value=datetime.strptime(default_val, '%Y-%m-%d').date() if default_val and isinstance(default_val, str) else None, key=f"prod_{field_id}")
                elif field['type'] == 'time':
                    product_data[field_id] = st.time_input(field['label'], value=datetime.strptime(default_val, '%H:%M').time() if default_val and isinstance(default_val, str) else None, key=f"prod_{field_id}")
                
                # Validation for required
                if field.get('required', False) and not product_data.get(field_id):
                    errors.append(f"{field['label']} is required.")
           
            submitted = st.form_submit_button("Save Product", type="primary")
            if submitted:
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    if 'name' not in product_data or not product_data['name']:
                        st.error("Product name is required.")
                    elif 'price' not in product_data or product_data['price'] <= 0:
                        st.error("Valid price is required.")
                    elif enable_inventory and 'inventory' not in product_data:
                        st.error("Inventory quantity is required when inventory tracking is enabled.")
                    else:
                        product_data['id'] = edit_prod.get('id', str(datetime.now().timestamp()))
                        # Check for duplicate name
                        duplicate = next((p for p in products if p['name'].lower() == product_data['name'].lower() and p['id'] != product_data['id']), None)
                        if duplicate:
                            duplicate.update({k: v for k, v in product_data.items() if k != 'id'})
                        else:
                            products.append(product_data)
                        st.success("Product saved!")
                        st.session_state.show_product_form = False
                        st.session_state.edit_product = None
                        st.rerun()
           
            if st.form_submit_button("Cancel", type="secondary"):
                st.session_state.show_product_form = False
                st.session_state.edit_product = None
                st.rerun()
   
    # Display products
    if filtered:
        for idx, product in enumerate(filtered):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.write(f"**{product.get('name', 'Unnamed')}**")
                for field in config['fields']:
                    if field['id'] not in ['name', 'price', 'inventory'] and product.get(field['id']):
                        st.caption(f"{field['label']}: {product[field['id']]}")
            with col2:
                st.markdown(f"**{config['currency']}{product.get('price', 0):.2f}**")
                if enable_inventory:
                    stock = product.get('inventory', 0)
                    stock_class = "low-stock" if 0 < stock <= 5 else "out-of-stock" if stock <= 0 else ""
                    st.markdown(f"<span class='{stock_class}'>Stock: {stock}</span>", unsafe_allow_html=True)
            with col3:
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Edit", key=f"edit_{product['id']}"):
                        st.session_state.edit_product = product
                        st.session_state.show_product_form = True
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_{product['id']}"):
                        if product in st.session_state.products:
                            st.session_state.products.remove(product)
                            st.success("Product deleted.")
                            st.rerun()
            st.divider()
    else:
        st.info("No products match the search. Try adjusting your search or add new products.")

def settings_screen():
    config = st.session_state.config
   
    st.subheader("Store Settings")
   
    # Business Info
    with st.expander("👨‍💼 Business Information", expanded=True):
        config['businessName'] = st.text_input("Business Name", value=config.get('businessName', ''), help="Displayed on receipts")
        col1, col2 = st.columns(2)
        with col1:
            config['currency'] = st.text_input("Currency Symbol", value=config.get('currency', '$'), max_chars=3)
        with col2:
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), min_value=0.0, step=0.1)
        config['showTax'] = st.checkbox("Show Tax on Receipts", value=config.get('showTax', True))
        config['showDiscount'] = st.checkbox("Allow Discounts", value=config.get('showDiscount', True))
        config['receiptFooter'] = st.text_area("Receipt Footer", value=config.get('receiptFooter', 'Thank you!'), help="Message at the bottom of receipts", max_chars=200)
        config['enableInventory'] = st.checkbox("Enable Inventory Tracking", value=config.get('enableInventory', True), help="Track stock and prevent overselling. Restart app to apply changes.")
        config['enableCustomers'] = st.checkbox("Enable Customer Database", value=config.get('enableCustomers', True), help="Manage customers and track loyalty. Restart app to apply changes.")
   
    # Theme
    with st.expander("🎨 Theme & Colors"):
        col1, col2 = st.columns(2)
        with col1:
            config['theme']['primary'] = st.color_picker("Primary Color", value=config['theme'].get('primary', '#6366f1'))
            config['theme']['accent'] = st.color_picker("Accent Color", value=config['theme'].get('accent', '#a5b4fc'))
        with col2:
            config['theme']['secondary'] = st.color_picker("Secondary Color", value=config['theme'].get('secondary', '#818cf8'))
            config['theme']['background'] = st.color_picker("Background Color", value=config['theme'].get('background', '#ffffff'))
        st.markdown("Preview: Changes apply immediately.")
   
    # Backup/Restore
    with st.expander("💾 Backup & Restore", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export Data"):
                data = {
                    'config': config,
                    'products': st.session_state.products,
                    'customers': st.session_state.customers,  # New
                    'transactions': st.session_state.transactions[-50:]  # Last 50 transactions
                }
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(data, indent=2, default=str),
                    file_name=f"{config.get('businessName', 'universal-pos')}-backup.json",
                    mime="application/json"
                )
        with col2:
            uploaded = st.file_uploader("📤 Upload Backup", type=['json'])
            if uploaded:
                try:
                    data = json.load(uploaded)
                    if 'config' in data:
                        st.session_state.config = data['config']
                    if 'products' in data:
                        st.session_state.products = data['products']
                    if 'customers' in data:  # New
                        st.session_state.customers = data['customers']
                    if 'transactions' in data:
                        st.session_state.transactions.extend(data['transactions'][-50:])  # Append recent
                    st.success("Data imported successfully! Refresh to see changes.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error importing: {str(e)}")
   
    # Reset option
    with st.expander("⚠️ Reset to Defaults", expanded=False):
        if st.button("Reset Configuration", type="secondary"):
            if st.checkbox("Confirm reset (irreversible)"):
                st.session_state.config = None
                st.session_state.screen = 'welcome'
                st.session_state.setup_step = 1
                st.rerun()

def receipt_screen():
    config = st.session_state.config
    transaction = st.session_state.get('last_transaction')
    customers = st.session_state.customers  # New
   
    if not transaction:
        st.error("No transaction found. Returning to POS.")
        st.session_state.screen = 'pos'
        st.rerun()
        return
   
    # Get customer info
    customer_name = "Guest"
    if transaction.get('customer_id'):
        customer = next((c for c in customers if c['id'] == transaction['customer_id']), None)
        if customer:
            customer_name = customer['name']
    
    # Professional receipt layout
    st.markdown(f"""
    <div style='text-align: center; background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        <h2 style='color: black; margin: 0;'>{config['businessName'] or 'Universal POS'}</h2>
        <p style='color: #666; margin: 0.5rem 0;'>Receipt #{transaction['id'][:8]}</p>
        <p style='color: #666; margin: 0;'>{datetime.fromisoformat(transaction['timestamp']).strftime("%B %d, %Y %I:%M %p")}</p>
        <p style='color: #666; margin: 0;'>{customer_name}</p>
    </div>
    """, unsafe_allow_html=True)
   
    st.divider()
   
    # Items table
    st.subheader("Items")
    for item in transaction['items']:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{item['name']}**")
            # Show fields if showInReceipt
            for field in config['fields']:
                if field['id'] not in ['name', 'price', 'inventory'] and field.get('showInReceipt', False) and item.get(field['id']):
                    st.caption(f"{field['label']}: {item[field['id']]}")
        with col2:
            st.write(f"x{item['cartQuantity']}")
        with col3:
            st.write(f"{config['currency']}{(item['price'] * item['cartQuantity']):.2f}")
   
    st.divider()
   
    # Totals
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**Subtotal:**")
    with col2:
        st.write(f"{config['currency']}{transaction['subtotal']:.2f}")
   
    if transaction['discount'] > 0 and config.get('showDiscount', True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Discount:**")
        with col2:
            st.write(f"-{config['currency']}{transaction['discount']:.2f}")
   
    if transaction['tax'] > 0 and config.get('showTax', True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Tax:**")
        with col2:
            st.write(f"{config['currency']}{transaction['tax']:.2f}")
   
    st.divider()
   
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 style='color: black;'>**Total:**</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h2 style='color: black;'>{config['currency']}{transaction['total']:.2f}</h2>",
                   unsafe_allow_html=True)
   
    if config.get('receiptFooter'):
        st.info(config['receiptFooter'])
   
    # Actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🖨️ Print Receipt", type="secondary"):
            st.info("Printing functionality can be added via browser print (Ctrl+P).")
    with col2:
        if st.button("📄 Email Receipt", type="secondary"):
            st.info("Email integration can be added in future updates.")
    with col3:
        if st.button("🛒 New Sale", type="primary"):
            st.session_state.screen = 'pos'
            st.rerun()

# Main app
def main():
    st.set_page_config(
        page_title="Universal POS - Professional Edition", 
        page_icon="🏪", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
   
    init_session_state()
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
        elif st.session_state.screen == 'customers':  # New
            customers_screen()
        elif st.session_state.screen == 'settings':
            settings_screen()
        elif st.session_state.screen == 'receipt':
            receipt_screen()

if __name__ == "__main__":
    main()

