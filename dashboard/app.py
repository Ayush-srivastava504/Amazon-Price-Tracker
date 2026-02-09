#!/usr/bin/env python3
import streamlit as st
import yaml
import os
from datetime import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))


# Local imports
from queries import get_dashboard_data, get_price_trends, search_products
from components import charts, filters

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'dashboard_config.yaml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# Page config
st.set_page_config(
    page_title=config['ui']['page_title'],
    page_icon=config['ui']['page_icon'],
    layout=config['ui']['layout'],
    initial_sidebar_state=config['ui']['initial_sidebar_state']
)

# Title
st.title("📈 Amazon Price Tracker")
st.markdown("---")

# Load initial data
try:
    data = get_dashboard_data(days=config['time_ranges']['default'])
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# Date range
start_date, end_date, days_selected = filters.date_range_filter(
    default_days=config['time_ranges']['default']
)

# Product filter
selected_product, compare_products = filters.product_filter(data.get('products', []))

# Search
search_query = filters.search_filter()
if search_query:
    search_results = search_products(search_query)
    if search_results:
        st.sidebar.write(f"Found {len(search_results)} products")

# Main content
if not data.get('products'):
    st.warning("No products found. Run the scraper first.")
    st.stop()

# Stats row
st.header("Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Products", data['stats'].get('total_products', 0))

with col2:
    st.metric("In Stock", data['stats'].get('in_stock', 0))

with col3:
    avg_price = data['stats'].get('avg_price')
    st.metric("Avg Price", f"₹{avg_price:,.2f}" if avg_price else "N/A")

with col4:
    st.metric("Last Updated", datetime.now().strftime("%H:%M"))

# Alerts
if data.get('alerts'):
    st.subheader("⚠️ Price Alerts")
    for alert in data['alerts'][:5]:  # Show top 5
        change_pct = alert.get('change_pct', 0)
        emoji = "🔻" if change_pct < 0 else "🔼"
        color = "red" if change_pct < -10 else "orange" if change_pct > 10 else "green"
        
        st.markdown(f"""
        {emoji} **{alert.get('title', 'Unknown')}**  
        ₹{alert.get('current_price', 0):,.2f} ({change_pct:+.1f}%)
        """)

# Charts section
st.markdown("---")
st.header("Charts")

if selected_product:
    # Single product view
    product_data = get_dashboard_data(days=days_selected, product_id=selected_product)
    
    if product_data and product_data.get('history'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Price History")
            fig = charts.price_history_chart(
                product_data['history'],
                title=f"Price: {product_data['product']['title'][:50]}..."
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Product Details")
            if product_data.get('product'):
                p = product_data['product']
                st.write(f"**ID:** {p['product_id']}")
                st.write(f"**Title:** {p['title']}")
                st.write(f"**Current Price:** ₹{p['current_price']:,.2f}" if p['current_price'] else "**Price:** N/A")
                st.write(f"**Availability:** {p['availability']}")
                st.write(f"**Rating:** {p['rating']}" if p['rating'] else "**Rating:** N/A")
                st.write(f"**Seller:** {p['seller']}" if p['seller'] else "**Seller:** N/A")
                st.write(f"**Last Updated:** {p['last_seen_at']}")
    
    # Comparison chart if selected
    if compare_products:
        st.subheader("Price Comparison")
        trends = get_price_trends(compare_products, days=days_selected)
        if trends:
            fig = charts.multi_product_chart(trends, title="Price Comparison")
            st.plotly_chart(fig, use_container_width=True)

else:
    # Overview charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Availability")
        fig = charts.availability_chart(data['stats'])
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Price Distribution")
        fig = charts.price_distribution_chart(data.get('products', []))
        if fig:
            st.plotly_chart(fig, use_container_width=True)

# Products table
st.markdown("---")
st.header("Products")

if data.get('products'):
    # Simple table - Streamlit's built-in is fine
    display_cols = ['product_id', 'title', 'current_price', 'availability', 'last_seen_at']
    display_data = []
    
    for p in data['products'][:config['limits']['max_products_table']]:
        row = {
            'product_id': p['product_id'],
            'title': p['title'][:70] + ('...' if len(p['title']) > 70 else ''),
            'current_price': f"₹{p['current_price']:,.2f}" if p['current_price'] else 'N/A',
            'availability': p['availability'],
            'last_seen_at': p['last_seen_at']
        }
        display_data.append(row)
    
    st.dataframe(display_data, use_container_width=True)
    
    # Export option
    if st.button("Export to CSV"):
        import pandas as pd
        df = pd.DataFrame(display_data)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"amazon_prices_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown("*Dashboard updated at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "*")
st.caption("Amazon Price Tracker - Local Dashboard")