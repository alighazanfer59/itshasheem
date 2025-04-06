import streamlit as st
import os

# 🎨 Define multiple themes
THEMES = {
    "Default (Purple)": {
        "primaryColor": "#B16CEA",
        "backgroundColor": "#252525",
        "secondaryBackgroundColor": "#3A2E52",
        "textColor": "#FFFFFF",
    },
    "Ocean Blue": {
        "primaryColor": "#0099CC",
        "backgroundColor": "#2A2F33",
        "secondaryBackgroundColor": "#1F4E5F",
        "textColor": "#FFFFFF",
    },
    "Emerald Green": {
        "primaryColor": "#26A65B",
        "backgroundColor": "#303A3A",
        "secondaryBackgroundColor": "#1B3A34",
        "textColor": "#FFFFFF",
    },
    "Cyber Night": {
        "primaryColor": "#FF6EC7",
        "backgroundColor": "#1A1A2E",
        "secondaryBackgroundColor": "#16213E",
        "textColor": "#EDEDED",
    },
    "Midnight Teal": {
        "primaryColor": "#1ABC9C",  # Bright teal
        "backgroundColor": "#1C1C1C",
        "secondaryBackgroundColor": "#2C3E50",
        "textColor": "#ECF0F1",
    },
    # "Charcoal Rose": {
    #     "primaryColor": "#FF4C60",  # Soft rose
    #     "backgroundColor": "#232323",
    #     "secondaryBackgroundColor": "#313131",
    #     "textColor": "#F8F8F8",
    # },
    # "Indigo Noir": {
    #     "primaryColor": "#6C5CE7",  # Electric indigo
    #     "backgroundColor": "#121212",
    #     "secondaryBackgroundColor": "#2B2B2B",
    #     "textColor": "#EDEDED",
    # },
    # "Steel Cyan": {
    #     "primaryColor": "#00BCD4",  # Vibrant cyan
    #     "backgroundColor": "#20232A",
    #     "secondaryBackgroundColor": "#282C34",
    #     "textColor": "#FAFAFA",
    # },
    # "Amber Dusk": {
    #     "primaryColor": "#FFC107",  # Warm amber
    #     "backgroundColor": "#2E2E2E",
    #     "secondaryBackgroundColor": "#383838",
    #     "textColor": "#F5F5F5",
    # },
    # "Blush Coral": {
    #     "primaryColor": "#FF6B6B",  # Soft red-coral
    #     "backgroundColor": "#FFF0F0",  # Pale blush
    #     "secondaryBackgroundColor": "#FFE4E1",  # Slightly deeper blush
    #     "textColor": "#2C2C2C",
    # },
    # "Sky Breeze": {
    #     "primaryColor": "#4A90E2",  # Serene blue
    #     "backgroundColor": "#E6F0FA",  # Soft sky
    #     "secondaryBackgroundColor": "#FFFFFF",  # Clean white contrast
    #     "textColor": "#1E1E1E",
    # },
    # "Mint Cream": {
    #     "primaryColor": "#00C896",  # Mint green
    #     "backgroundColor": "#EBFFF5",  # Creamy mint
    #     "secondaryBackgroundColor": "#DFFCEF",  # Slight contrast
    #     "textColor": "#1A3C34",
    # },
    # "Lavender Haze": {
    #     "primaryColor": "#A78BFA",  # Lavender
    #     "backgroundColor": "#F4F0FA",  # Soft lavender mist
    #     "secondaryBackgroundColor": "#ECE4FF",
    #     "textColor": "#2E2B3D",
    # },
    # "Golden Sand": {
    #     "primaryColor": "#F5B041",  # Warm gold
    #     "backgroundColor": "#FFF8E1",  # Sand
    #     "secondaryBackgroundColor": "#FDE9C9",
    #     "textColor": "#4A3F29",
    # },
    # "Light Minimal": {
    #     "primaryColor": "#0A66C2",  # Deep blue
    #     "backgroundColor": "#F5F7FA",  # Very light gray
    #     "secondaryBackgroundColor": "#FFFFFF",  # True white
    #     "textColor": "#1C1C1C",  # Much darker for visibility
    # },
    # "Vintage Coffee": {
    #     "primaryColor": "#A9746E",  # Warm brown
    #     "backgroundColor": "#FDF6EC",  # Pale coffee cream
    #     "secondaryBackgroundColor": "#EFE6DC",  # Slightly darker for widgets
    #     "textColor": "#3B2F2F",  # Deep earthy brown
    # },
    "Dark Matter": {
        "primaryColor": "#FF5F6D",
        "backgroundColor": "#0F0F0F",
        "secondaryBackgroundColor": "#1E1E1E",
        "textColor": "#EEEEEE",
    },
    "Neon Luxe": {
        "primaryColor": "#39FF14",
        "backgroundColor": "#000000",
        "secondaryBackgroundColor": "#101010",
        "textColor": "#39FF14",
    },
}


def apply_theme(theme):
    """Apply selected theme dynamically using CSS"""
    st.markdown(
        f"""
        <style>
        /* 🔹 App Layout Backgrounds */
        header {{
            background-color: {theme['backgroundColor']} !important;
            color: {theme['textColor']} !important;
        }}

        .appview-container {{
            background-color: {theme['backgroundColor']} !important;
        }}

        .stSidebar {{
            background-color: {theme['secondaryBackgroundColor']} !important;
        }}

        /* 🔹 Text & Typography */
        html, body, .block-container, .main, .stApp, .stMarkdown, .stText, .stTextInput label,
        .stSelectbox label, .stRadio label, .stCheckbox label, label, p, span, div, h1, h2, h3, h4, h5, h6 {{
            color: {theme['textColor']} !important;
        }}

        # /* 🔹 Input & Widget Backgrounds */
        # input, textarea, select, .stTextInput, .stSelectbox, .stNumberInput input {{
        #     background-color: {theme['secondaryBackgroundColor']} !important;
        #     color: {theme['textColor']} !important;
        #     border-radius: 6px !important;
        #     border: 1px solid {theme['primaryColor']} !important;
        # }}
        /* 🔹 Input & Widget Backgrounds */
        input, textarea, select,
        .stTextInput input, .stSelectbox div[data-baseweb],
        .stNumberInput input, .stDateInput input {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
            border: 1px solid {theme['primaryColor']} !important;
            border-radius: 6px !important;
            padding: 6px 10px;
            box-shadow: none !important;
        }}

        /* 🔹 Placeholder text */
        input::placeholder,
        textarea::placeholder {{
            color: rgba(100, 100, 100, 0.6);
            opacity: 1;
        }}

        /* 🔹 Focus styles */
        input:focus, textarea:focus, select:focus {{
            outline: none !important;
            border-color: {theme['primaryColor']} !important;
            box-shadow: 0 0 4px {theme['primaryColor']}50;
        }}


        # /* 🔹 Input & Widget Backgrounds (Main + Sidebar) */
        # input, textarea, select,
        # .stTextInput input, .stNumberInput input, .stDateInput input,
        # .stSelectbox > div > div, .stSelectbox label,
        # .stMultiSelect, .stMultiSelect label,
        # .stSlider, .stSlider label {{
        #     background-color: {theme['secondaryBackgroundColor']} !important;
        #     color: {theme['textColor']} !important;
        #     border: 1px solid {theme['primaryColor']} !important;
        #     border-radius: 6px !important;
        # }}

        /* ✅ Fix: Dropdown Panel + Options (Light theme visibility) */

        /* Selectbox main input (value area) */
        .css-1jqq78o-control,  
        .css-1uccc91-singleValue,  
        .css-1n76uvr, .css-1d391kg, .css-14el2xx-placeholder {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
            border: 1px solid {theme['primaryColor']} !important;
        }}

        /* Listbox dropdown menu (the full list of options) */
        div[data-baseweb="select"] > div[role="listbox"] {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
            border: 1px solid {theme['primaryColor']} !important;
            z-index: 9999 !important;
        }}

        /* Options inside dropdown */
        .css-1r6slb0-option, .css-1n7v3ny-option {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
        }}

        /* Option hover and selected */
        .css-1r6slb0-option:hover,
        .css-1n7v3ny-option:hover,
        .css-1r6slb0-option[aria-selected="true"],
        .css-1n7v3ny-option[aria-selected="true"] {{
            background-color: {theme['primaryColor']}30 !important;
            color: {theme['textColor']} !important;
        }}

        /* Fix selectbox dropdown options */
        .css-1wa3eu0-placeholder, .css-1okebmr-indicatorSeparator {{
            color: {theme['textColor']} !important;
            background-color: transparent !important;
        }}

        /* Sidebar-specific targeting for widgets */
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] select,
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] .stTextInput,
        section[data-testid="stSidebar"] .stDateInput > div > input,
        # section[data-testid="stSidebar"] .stSelectbox > div > div,
        section[data-testid="stSidebar"] .stNumberInput {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
            border: 1px solid {theme['primaryColor']} !important;
        }}
        
        # /* 🧱 More Specific Sidebar Input Fixes */
        # section[data-testid="stSidebar"] .stTextInput > div > input,
        # section[data-testid="stSidebar"] .stNumberInput > div > input,
        # section[data-testid="stSidebar"] .stDateInput > div > input,
        # section[data-testid="stSidebar"] .stSelectbox > div > div,
        # section[data-testid="stSidebar"] textarea {{
        #     border: 1px solid {theme['primaryColor']} !important;
        #     background-color: {theme['secondaryBackgroundColor']} !important;
        #     color: {theme['textColor']} !important;
        # }}


        /* Dropdown options */
        div[role="listbox"] {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
        }}
        
        /* 🔹 Placeholder text */
        input::placeholder,
        textarea::placeholder {{
            color: rgba(100, 100, 100, 0.6);
            opacity: 1;
        }}

        /* 🔹 Focus styles */
        input:focus, textarea:focus, select:focus {{
            outline: none !important;
            border-color: {theme['primaryColor']} !important;
            box-shadow: 0 0 4px {theme['primaryColor']}50;
        }}

        /* 🎯 Selectbox Dropdown Menu Text + Background */
        div[role="listbox"] {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
            border: 1px solid {theme['primaryColor']} !important;
        }}

        /* Listbox options */
        div[role="option"] {{
            color: {theme['textColor']} !important;
            background-color: {theme['secondaryBackgroundColor']} !important;
        }}

        /* Option highlight (hovered/selected) */
        div[role="option"]:hover,
        div[role="option"][aria-selected="true"] {{
            background-color: {theme['primaryColor']}30 !important;
            color: {theme['textColor']} !important;
        }}

        /* 🔹 Number input spin buttons */
        input[type="number"]::-webkit-inner-spin-button,
        input[type="number"]::-webkit-outer-spin-button {{
            filter: invert(0.5);
        }}

        /* 🔹 Radio buttons and checkboxes */
        .stRadio > div, .stCheckbox > div {{
            color: {theme['textColor']} !important;
        }}

        /* 🔹 Buttons */
        .stButton > button, .stForm button {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid {theme['primaryColor']} !important;
            color: {theme['textColor']} !important;
            border-radius: 8px;
            transition: all 0.2s ease-in-out;
            backdrop-filter: blur(8px);
        }}

        .stButton > button:hover, .stForm button:hover {{
            background: {theme['primaryColor']} !important;
            color: white !important;
            transform: translateY(-2px);
        }}

        /* 🔹 DataFrames */
        .stDataFrame {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
        }}

        /* 🔹 Floating Theme Button */
        .theme-button {{
            position: fixed;
            top: 12px;
            right: 80px;
            background: rgba(255, 255, 255, 0.1);
            color: {theme['textColor']} !important;
            border: 1px solid {theme['primaryColor']};
            padding: 8px 20px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 20px;
            cursor: pointer;
            transition: 0.3s ease-in-out;
            backdrop-filter: blur(8px);
        }}

        .theme-button:hover {{
            background: {theme['primaryColor']} !important;
            color: white !important;
            transform: scale(1.05);
        }}
        
        /* ✅ Enhanced Theme Selector Dropdown Fix for Light Themes */
        .css-1jqq78o-control,  /* main select box */
        .css-1uccc91-singleValue,  /* selected value */
        .css-1n76uvr, .css-1d391kg, .css-14el2xx-placeholder{{
            background-color: white !important;
            color: black !important;
            border: 1px solid {theme['primaryColor']} !important;
        }}

        /* Dropdown list */
        .css-1r6slb0-option, .css-1n7v3ny-option,
        div[data-baseweb="select"] > div[role="listbox"] {{
            background-color: white !important;
            color: black !important;
        }}

        /* Hover & selected */
        .css-1r6slb0-option:hover,
        .css-1n7v3ny-option:hover,
        .css-1r6slb0-option[aria-selected="true"],
        .css-1n7v3ny-option[aria-selected="true"] {{
            background-color: {theme['primaryColor']}30 !important;
            color: black !important;
        }}

        /* ✅ Enhanced Theme Selector Dropdown Fix for Contrast */
        .css-1n76uvr, .css-1d391kg, .css-1uccc91-singleValue, .css-14el2xx-placeholder, .css-1jqq78o-control {{
            color: {{theme.get('textColor', '#f5f5f5')}} !important;
            background-color: {{theme.get('secondaryBackgroundColor', '#1e1e1e')}} !important;
        }}

        .css-1r6slb0-option, .css-1n7v3ny-option {{
            color: #f5f5f5 !important;  /* Use lighter text specifically in dropdown items */
            background-color: {{theme.get('secondaryBackgroundColor', '#1e1e1e')}} !important;
        }}

        .css-1r6slb0-option:hover, .css-1n7v3ny-option:hover {{
            background-color: {{theme.get('primaryColor', '#4f46e5')}}30 !important;
            color: white !important;
        }}


        .css-1n76uvr, .css-1d391kg {{  /* These classes often target selectbox text */
            color: {theme['textColor']} !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def update_config(theme_name, theme_values):
    """Optional: Update Streamlit config file (for static themes)."""
    config_path = os.path.expanduser("~/.streamlit/config.toml")
    config_content = f"""[theme]
primaryColor = "{theme_values['primaryColor']}"
backgroundColor = "{theme_values['backgroundColor']}"
secondaryBackgroundColor = "{theme_values['secondaryBackgroundColor']}"
textColor = "{theme_values['textColor']}"
font = "sans serif"
"""
    with open(config_path, "w") as config_file:
        config_file.write(config_content)
