import streamlit as st


def display_metrics(
    net_profit, win_rate, max_drawdown, profit_factor, sharpe_ratio, returns
):
    """Function to display trading performance metrics in a styled format."""
    st.markdown(
        f"""
        <style>
            /* Full-width container */
            .metric-container {{
                display: flex;
                justify-content: space-around;
                width: 100%;
                padding: 20px 0;
                gap: 30px; /* Increased gap between rows */
            }}

            /* Individual metric box */
            .metric-box {{
                flex: 1;
                text-align: center;
                padding: 25px;
                border-radius: 12px;
                background: rgba(255, 255, 255, 90.0); /* Fully transparent */
                box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
                margin: 15px; /* Increased margin for more spacing */
                min-width: 200px; /* Ensures minimum width */
            }}

            /* Metric labels */
            .metric-label {{
                font-size: 20px;
                font-weight: bold;
                color: #333;
            }}

            /* Metric values */
            .metric-value {{
                font-size: 34px;
                font-weight: bold;
                color: #007BFF;
            }}
        </style>

        <!-- First row -->
        <div class="metric-container">
            <div class="metric-box">
                <div class="metric-label">💰 Net Profit</div>
                <div class="metric-value">${net_profit:,.2f}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">📈 Win Rate</div>
                <div class="metric-value">{win_rate:.2f}%</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">📉 Max Drawdown</div>
                <div class="metric-value">{max_drawdown:.2f}%</div>
            </div>
        </div>

        <!-- Second row -->
        <div class="metric-container">
            <div class="metric-box">
                <div class="metric-label">📊 Profit Factor</div>
                <div class="metric-value">{profit_factor:.2f}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">📊 Sharpe Ratio</div>
                <div class="metric-value">{sharpe_ratio:.2f}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">📈 Returns</div>
                <div class="metric-value">{returns:.2f}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
