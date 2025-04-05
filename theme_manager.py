import streamlit as st
import os

import streamlit as st

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
}


def apply_theme(theme):
    """Apply selected theme dynamically using CSS"""
    st.markdown(
        f"""
        <style>
        /* 🔹 Floating Transparent Theme Button */
        .theme-button {{
            position: fixed;
            top: 12px;  /* Align with top bar */
            right: 80px;
            background: rgba(255, 255, 255, 0.1);  /* Transparent glass effect */
            color: {theme['textColor']} !important;
            border: 1px solid {theme['primaryColor']}; /* Thin elegant border */
            padding: 8px 20px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 20px;
            cursor: pointer;
            transition: 0.3s ease-in-out;
            backdrop-filter: blur(8px);  /* Frosted glass effect */
        }}
        .theme-button:hover {{
            background: {theme['primaryColor']} !important;
            color: white !important;
            transform: scale(1.05);
        }}

        /* 🔹 Fix Top Bar Background */
        header {{
            background-color: {theme['backgroundColor']} !important;
            color: {theme['textColor']} !important;
        }}

        /* 🔹 Background */
        .appview-container {{
            background-color: {theme['backgroundColor']} !important;
        }}

        /* 🔹 Sidebar */
        .stSidebar {{
            background-color: {theme['secondaryBackgroundColor']} !important;
        }}

        /* 🔹 Widgets */
        .stTextInput, .stSelectbox, .stMultiSelect {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
            border-radius: 6px !important;
            border: 1px solid {theme['primaryColor']} !important;
        }}

        /* 🔹 DataFrame */
        .stDataFrame {{
            background-color: {theme['secondaryBackgroundColor']} !important;
            color: {theme['textColor']} !important;
        }}

        /* 🔹 Buttons */
        .stButton>button {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid {theme['primaryColor']} !important;
            color: {theme['textColor']} !important;
            border-radius: 8px;
            transition: all 0.2s ease-in-out;
            backdrop-filter: blur(8px);
        }}
        .stButton>button:hover {{
            background: {theme['primaryColor']} !important;
            color: white !important;
            transform: translateY(-2px);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def update_config(theme_name, theme_values):
    """Update the Streamlit config.toml file with the selected theme."""
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
