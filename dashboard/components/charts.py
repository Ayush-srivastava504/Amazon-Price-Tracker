# Simple charting functions
# Just enough to visualize

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def price_history_chart(history_data, title="Price History"):
    if not history_data:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(history_data)
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    
    # Simple line chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['scraped_at'],
        y=df['price'],
        mode='lines+markers',
        name='Price',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def multi_product_chart(trends_data, title="Price Comparison"):      #Line chart for multiple products
    if not trends_data:
        return None
    
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, trend in enumerate(trends_data[:5]):  # Max 5 lines
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=trend['dates'],
            y=trend['prices'],
            mode='lines',
            name=trend['title'][:30] + ('...' if len(trend['title']) > 30 else ''),
            line=dict(color=color, width=2)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        hovermode='x unified',
        template='plotly_white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def availability_chart(stats):     #Pie chart for product availability
    if not stats:
        return None
    
    # Extract counts
    labels = ['In Stock', 'Out of Stock', 'Unknown']
    values = [
        stats.get('in_stock', 0),
        stats.get('out_of_stock', 0),
        stats.get('total_products', 0) - (stats.get('in_stock', 0) + stats.get('out_of_stock', 0))
    ]
    
    colors = ['#2ca02c', '#d62728', '#7f7f7f']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker=dict(colors=colors)
    )])
    
    fig.update_layout(
        title="Product Availability",
        template='plotly_white'
    )
    
    return fig

def price_distribution_chart(products_data):      #Histogram of current prices
    if not products_data:
        return None
    
    # Extract prices
    prices = [p['current_price'] for p in products_data if p.get('current_price')]
    
    if not prices:
        return None
    
    fig = px.histogram(
        x=prices,
        nbins=20,
        title="Price Distribution",
        labels={'x': 'Price (₹)', 'y': 'Count'}
    )
    
    fig.update_layout(
        template='plotly_white',
        bargap=0.1
    )
    
    return fig