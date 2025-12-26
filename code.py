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
    if 'screen' not in st.session_state:
        st.session_state.screen = 'welcome'
    if 'config' not in st.session_state:
        st.session_state.config = None
    if 'products' not in st.session_state:
        st.session_state.products = []
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    if 'setup_step' not in st.session_state:
        st.session_state.setup_step = 1
    if 'current_discount' not in st.session_state:
        st.session_state.current_discount = 0

def apply_theme(config):
    if config:
        st.markdown(f"""
        <style>
        .stApp {{
            background-color: {config['theme']['background']};
        }}
        .main-header {{
            background-color: {config['theme']['primary']};
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
        }}
        .product-card {{
            background: white;
            padding: 1rem;
            border-radius: 10px;
            border: 2px solid {config['theme']['accent']};
            cursor: pointer;
        }}
        </style>
        """, unsafe_allow_html=True)

def welcome_screen():
    st.markdown("""
    <div style='text-align: center; padding: 3rem;'>
        <h1 style='font-size: 3rem; color: #6366f1;'>🏪 Universal POS</h1>
        <p style='font-size: 1.5rem; color: #666;'>The Point of Sale System That Adapts to YOU</p>
        <p style='color: #888;'>Customize every field, color, and feature for your unique business</p>
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
                        'fields': template['fields'],
                        'taxRate': template['taxRate'],
                        'currency': template['currency'],
                        'discountRate': 0,
                        'showTax': True,
                        'showDiscount': True,
                        'receiptFooter': 'Thank you for your business!'
                    }
                    st.session_state.current_discount = template['taxRate']
                    st.session_state.setup_step = 2
                    st.rerun()
    
    elif st.session_state.setup_step == 2:
        st.title("Customize Your Store")
        
        config = st.session_state.config
        
        config['businessName'] = st.text_input("Business Name", config.get('businessName', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            config['currency'] = st.text_input("Currency Symbol", config.get('currency', '$'))
        with col2:
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config.get('taxRate', 0)), step=0.1)
        
        config['discountRate'] = st.number_input("Default Discount (%)", value=float(config.get('discountRate', 0)), step=0.1)
        
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
    st.write("Add, remove, or modify fields to match your business needs")
    
    config = st.session_state.config
    
    # Display existing fields
    for idx, field in enumerate(config['fields']):
        with st.expander(f"{field['label']} ({field['type']})", expanded=False):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                field['label'] = st.text_input("Label", field['label'], key=f"label_{idx}")
            with col2:
                field['showInCart'] = st.checkbox("Cart", field['showInCart'], key=f"cart_{idx}")
            with col3:
                field['showInReceipt'] = st.checkbox("Receipt", field['showInReceipt'], key=f"receipt_{idx}")
            
            if field['id'] not in ['name', 'price']:
                if st.button("Remove", key=f"remove_{idx}"):
                    config['fields'].pop(idx)
                    st.rerun()
    
    # Add new field
    with st.expander("➕ Add New Field", expanded=False):
        new_label = st.text_input("Field Label")
        new_type = st.selectbox("Field Type", [t['value'] for t in FIELD_TYPES], 
                               format_func=lambda x: next(t['label'] for t in FIELD_TYPES if t['value'] == x))
        
        new_options = []
        if new_type == 'select':
            new_options_str = st.text_input("Options (comma separated)")
            new_options = [opt.strip() for opt in new_options_str.split(',') if opt.strip()]
        
        if st.button("Add Field"):
            if new_label:
                new_field = {
                    'id': f"field_{datetime.now().timestamp()}",
                    'type': new_type,
                    'label': new_label,
                    'options': new_options,
                    'required': False,
                    'showInCart': True,
                    'showInReceipt': True
                }
                config['fields'].append(new_field)
                st.rerun()
    
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
        st.markdown(f"<h1 style='color: {config['theme']['primary']};'>{config['businessName'] or 'Universal POS'}</h1>", 
                   unsafe_allow_html=True)
    
    with col2:
        # Get current screen index, default to 0 (dashboard) if not in nav list
        nav_screens = ['dashboard', 'pos', 'products', 'settings']
        current_index = nav_screens.index(st.session_state.screen) if st.session_state.screen in nav_screens else 0
        
        screen = st.selectbox("", ['Dashboard', 'POS', 'Products', 'Settings'], 
                             index=current_index,
                             label_visibility='collapsed',
                             key='nav_select')
        st.session_state.screen = screen.lower()

def dashboard():
    config = st.session_state.config
    transactions = st.session_state.transactions
    products = st.session_state.products
    
    # Calculate statistics
    today = datetime.now().date()
    today_transactions = [t for t in transactions if datetime.fromisoformat(t['timestamp']).date() == today]
    today_sales = sum(t['total'] for t in today_transactions)
    all_time_sales = sum(t['total'] for t in transactions)
    
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
    
    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛒 Start New Sale", type="primary", use_container_width=True):
            st.session_state.screen = 'pos'
            st.rerun()
    with col2:
        if st.button("➕ Manage Products", use_container_width=True):
            st.session_state.screen = 'products'
            st.rerun()
    
    # Recent transactions
    if today_transactions:
        st.subheader("Recent Transactions")
        for transaction in today_transactions[:5]:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{len(transaction['items'])} items**")
                    st.caption(datetime.fromisoformat(transaction['timestamp']).strftime("%I:%M %p"))
                with col2:
                    st.markdown(f"<h3 style='color: {config['theme']['primary']};'>{config['currency']}{transaction['total']:.2f}</h3>", 
                               unsafe_allow_html=True)
                st.divider()

def pos_screen():
    config = st.session_state.config
    products = st.session_state.products
    cart = st.session_state.cart
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Products")
        search = st.text_input("🔍 Search products...")
        
        filtered_products = [p for p in products if search.lower() in p.get('name', '').lower()]
        
        if filtered_products:
            cols = st.columns(3)
            for idx, product in enumerate(filtered_products):
                with cols[idx % 3]:
                    if st.button(f"**{product['name']}**\n\n{config['currency']}{product['price']}", 
                               key=f"prod_{product['id']}", use_container_width=True):
                        # Add to cart
                        existing = next((item for item in cart if item['id'] == product['id']), None)
                        if existing:
                            existing['cartQuantity'] += 1
                        else:
                            cart.append({**product, 'cartQuantity': 1})
                        st.rerun()
        else:
            st.info("No products found. Add products in the Products section.")
    
    with col2:
        st.subheader(f"Cart ({len(cart)})")
        
        if cart:
            for item in cart:
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**{item['name']}**")
                        st.caption(f"{config['currency']}{item['price']} × {item['cartQuantity']}")
                    with col_b:
                        st.write(f"**{config['currency']}{item['price'] * item['cartQuantity']:.2f}**")
                    
                    col_x, col_y, col_z = st.columns([1, 1, 1])
                    with col_x:
                        if st.button("➖", key=f"dec_{item['id']}"):
                            item['cartQuantity'] -= 1
                            if item['cartQuantity'] <= 0:
                                cart.remove(item)
                            st.rerun()
                    with col_y:
                        if st.button("➕", key=f"inc_{item['id']}"):
                            item['cartQuantity'] += 1
                            st.rerun()
                    with col_z:
                        if st.button("🗑️", key=f"del_{item['id']}"):
                            cart.remove(item)
                            st.rerun()
                    st.divider()
            
            # Calculate totals
            subtotal = sum(item['price'] * item['cartQuantity'] for item in cart)
            discount_rate = st.number_input("Discount (%)", value=float(config['discountRate']), step=0.1)
            discount = subtotal * (discount_rate / 100)
            taxable = subtotal - discount
            tax = taxable * (config['taxRate'] / 100)
            total = taxable + tax
            
            st.divider()
            st.write(f"Subtotal: {config['currency']}{subtotal:.2f}")
            st.write(f"Discount: -{config['currency']}{discount:.2f}")
            st.write(f"Tax ({config['taxRate']}%): {config['currency']}{tax:.2f}")
            st.markdown(f"<h2 style='color: {config['theme']['primary']};'>Total: {config['currency']}{total:.2f}</h2>", 
                       unsafe_allow_html=True)
            
            if st.button("Complete Sale", type="primary", use_container_width=True):
                transaction = {
                    'id': str(datetime.now().timestamp()),
                    'items': cart.copy(),
                    'subtotal': subtotal,
                    'discount': discount,
                    'tax': tax,
                    'total': total,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.transactions.insert(0, transaction)
                st.session_state.cart = []
                st.session_state.last_transaction = transaction
                st.session_state.screen = 'receipt'
                st.rerun()
        else:
            st.info("Cart is empty")

def products_screen():
    config = st.session_state.config
    products = st.session_state.products
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Products ({len(products)})")
    with col2:
        if st.button("➕ Add Product", type="primary"):
            st.session_state.show_product_form = True
    
    # Product form
    if st.session_state.get('show_product_form', False):
        with st.form("product_form"):
            st.subheader("Add New Product")
            
            product_data = {}
            for field in config['fields']:
                if field['type'] == 'text':
                    product_data[field['id']] = st.text_input(field['label'])
                elif field['type'] == 'number':
                    product_data[field['id']] = st.number_input(field['label'], min_value=0.0, step=0.01 if field['id'] == 'price' else 1.0)
                elif field['type'] == 'select':
                    product_data[field['id']] = st.selectbox(field['label'], [''] + field.get('options', []))
                elif field['type'] == 'textarea':
                    product_data[field['id']] = st.text_area(field['label'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_product_form = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Add Product", type="primary", use_container_width=True):
                    product_data['id'] = str(datetime.now().timestamp())
                    products.append(product_data)
                    st.session_state.show_product_form = False
                    st.rerun()
    
    # Display products
    if products:
        cols = st.columns(3)
        for idx, product in enumerate(products):
            with cols[idx % 3]:
                with st.container():
                    st.write(f"**{product.get('name', 'Unnamed')}**")
                    st.markdown(f"<h3 style='color: {config['theme']['primary']};'>{config['currency']}{product.get('price', 0)}</h3>", 
                               unsafe_allow_html=True)
                    for field in config['fields']:
                        if field['id'] not in ['name', 'price'] and product.get(field['id']):
                            st.caption(f"{field['label']}: {product[field['id']]}")
                    
                    if st.button("🗑️ Delete", key=f"delete_{product['id']}"):
                        products.remove(product)
                        st.rerun()

def settings_screen():
    config = st.session_state.config
    
    st.subheader("Settings")
    
    # Business Info
    with st.expander("Business Information", expanded=True):
        config['businessName'] = st.text_input("Business Name", config['businessName'])
        col1, col2 = st.columns(2)
        with col1:
            config['currency'] = st.text_input("Currency", config['currency'])
        with col2:
            config['taxRate'] = st.number_input("Tax Rate (%)", value=float(config['taxRate']), step=0.1)
    
    # Theme
    with st.expander("Theme Colors"):
        col1, col2 = st.columns(2)
        with col1:
            config['theme']['primary'] = st.color_picker("Primary Color", config['theme']['primary'])
            config['theme']['accent'] = st.color_picker("Accent Color", config['theme']['accent'])
        with col2:
            config['theme']['secondary'] = st.color_picker("Secondary Color", config['theme']['secondary'])
            config['theme']['background'] = st.color_picker("Background Color", config['theme']['background'])
    
    # Export/Import
    with st.expander("Backup & Restore"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export Configuration"):
                data = {
                    'config': config,
                    'products': st.session_state.products
                }
                st.download_button(
                    "Download Config",
                    json.dumps(data, indent=2),
                    file_name=f"{config['businessName']}-config.json",
                    mime="application/json"
                )
        with col2:
            uploaded = st.file_uploader("📤 Import Configuration", type=['json'])
            if uploaded:
                data = json.load(uploaded)
                if 'config' in data:
                    st.session_state.config = data['config']
                if 'products' in data:
                    st.session_state.products = data['products']
                st.success("Configuration imported!")
                st.rerun()

def receipt_screen():
    config = st.session_state.config
    transaction = st.session_state.get('last_transaction')
    
    if not transaction:
        st.error("No transaction found")
        return
    
    st.markdown(f"""
    <div style='text-align: center; background: white; padding: 2rem; border-radius: 10px;'>
        <div style='width: 80px; height: 80px; background: {config['theme']['primary']}; 
                    border-radius: 50%; margin: 0 auto 1rem; display: flex; 
                    align-items: center; justify-content: center;'>
            <span style='font-size: 40px; color: white;'>✓</span>
        </div>
        <h2 style='color: {config['theme']['primary']};'>{config['businessName']}</h2>
        <p>{datetime.fromisoformat(transaction['timestamp']).strftime("%B %d, %Y %I:%M %p")}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    for item in transaction['items']:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{item['name']}**")
            st.caption(f"{config['currency']}{item['price']} × {item['cartQuantity']}")
        with col2:
            st.write(f"**{config['currency']}{item['price'] * item['cartQuantity']:.2f}**")
    
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Subtotal:")
    with col2:
        st.write(f"{config['currency']}{transaction['subtotal']:.2f}")
    
    if transaction['discount'] > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Discount:")
        with col2:
            st.write(f"-{config['currency']}{transaction['discount']:.2f}")
    
    if transaction['tax'] > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Tax:")
        with col2:
            st.write(f"{config['currency']}{transaction['tax']:.2f}")
    
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"<h2 style='color: {config['theme']['primary']};'>Total:</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h2 style='color: {config['theme']['primary']};'>{config['currency']}{transaction['total']:.2f}</h2>", 
                   unsafe_allow_html=True)
    
    if config.get('receiptFooter'):
        st.info(config['receiptFooter'])
    
    if st.button("New Sale", type="primary", use_container_width=True):
        st.session_state.screen = 'pos'
        st.rerun()

# Main app
def main():
    st.set_page_config(page_title="Universal POS", page_icon="🏪", layout="wide")
    
    init_session_state()
    apply_theme(st.session_state.config)
    
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
        elif st.session_state.screen == 'settings':
            settings_screen()
        elif st.session_state.screen == 'receipt':
            receipt_screen()

if __name__ == "__main__":
    main()
