# Simple filter components
# These are just functions that return filter values

import streamlit as st
from datetime import datetime, timedelta

def date_range_filter(default_days=30):
    days_options = [7, 30, 90, 180]
    
    selected = st.sidebar.selectbox(
        "Time Range",
        days_options,
        index=days_options.index(default_days) if default_days in days_options else 1
    )
    
    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=selected)
    
    return start_date, end_date, selected

def product_filter(products_data):     #Product selector - dropdown or multi-select
    st.sidebar.markdown("### Products")
    
    # Create mapping for display
    product_options = []
    for p in products_data:
        title_short = p['title'][:50] + ('...' if len(p['title']) > 50 else '')
        label = f"{p['product_id']} - {title_short}"
        product_options.append((label, p['product_id']))
    
    if not product_options:
        return None, None
    
    # Single product selector
    selected_label = st.sidebar.selectbox(
        "Select Product",
        [opt[0] for opt in product_options],
        index=0
    )
    
    # Get corresponding product_id
    selected_id = None
    for label, pid in product_options:
        if label == selected_label:
            selected_id = pid
            break
    
    # Multi-select for comparison (optional)
    compare_products = st.sidebar.multiselect(
        "Compare Products (max 5)",
        [opt[0] for opt in product_options],
        max_selections=5
    )
    
    # Get IDs for comparison
    compare_ids = []
    for label in compare_products:
        for opt_label, pid in product_options:
            if opt_label == label:
                compare_ids.append(pid)
                break
    
    return selected_id, compare_ids

def availability_filter():
    options = ['All', 'In Stock', 'Out of Stock', 'Unknown']
    selected = st.sidebar.radio("Availability", options)
    return selected

def price_range_filter():
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        min_price = st.number_input("Min Price", value=0, min_value=0)
    
    with col2:
        max_price = st.number_input("Max Price", value=100000, min_value=0)
    
    return min_price, max_price

def search_filter():      #Search box for product
    search_query = st.sidebar.text_input("Search Products", "")
    return search_query