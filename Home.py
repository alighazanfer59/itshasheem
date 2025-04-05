import streamlit as st

# Set the page configuration with an emoji in the title
st.set_page_config(page_title="Trading App", page_icon="🏠")

# Title of the app with an emoji in the title
st.title("🏠 Welcome to the Trading App")

# Custom title for the home page
st.markdown(
    """
    <h3 style='font-size:18px; text-align: center;'>Navigate through the app to explore different sections:</h3>
    """,
    unsafe_allow_html=True,
)

# Sidebar content with icons
st.sidebar.title("Navigation Pages")

# List of pages with icons
page_titles = ["Home Page", "Backtest Strategies", "Saved Strategies"]

# Add icons before the filenames in the sidebar
page_icons = {
    "Home Page": "🏠",
    "Backtest Strategies": "📊",
    "Saved Strategies": "💾",
}

# Loop through page titles to display in sidebar with styles
for page in page_titles:
    if page == "Home Page":
        # Make "Home Page" bold and larger
        st.sidebar.markdown(
            f"<h3 style='font-size: 24px; font-weight: bold;'>{page_icons.get(page, '')} {page}</h3>",
            unsafe_allow_html=True,
        )
    else:
        # Indent subpages and use normal style for them
        st.sidebar.markdown(
            f"<p style='margin-left: 20px;'>{page_icons.get(page, '')} {page}</p>",
            unsafe_allow_html=True,
        )

# Main content for the Home page with instructions
st.markdown(
    """
    <p style='font-size:18px; text-align: left;'>This app allows you to:</p>
    <ul style='font-size:18px; text-align: left;'>
        <li>📌 Select and customize trading strategies</li>  
        <li>📈 Fetch historical market data from <b>Yahoo Finance</b></li>  
        <li>🔍 Analyze backtesting stats with <b>key performance metrics</b></li>  
        <li>🛠 Fine-tune <b>indicators, commissions, and spread settings</b></li>  
    </ul>
    <p style='font-size:18px; text-align: center;'>Use the <b>sidebar</b> to navigate between different sections and run your backtests. 🚀</p>
    """,
    unsafe_allow_html=True,
)
