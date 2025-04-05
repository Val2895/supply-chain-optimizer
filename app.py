import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import openai
import toml
import inflect
from io import BytesIO

# --- Load Theme Settings
theme_config = toml.load('streamlit_config.toml')

st.set_page_config(
    page_title="Supply Chain Tariff Optimization AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Branding Header
st.markdown("<h1 style='text-align: center; color: #003366;'>Supply Chain Tariff Optimization AI</h1>", unsafe_allow_html=True)
st.caption("Helping you source smarter in a shifting trade landscape — Powered by Groq AI")

# --- Tariff Data
annex_tariffs = {
    'China': 34, 'Vietnam': 46, 'India': 26, 'Bangladesh': 37, 'Cambodia': 49,
    'Malaysia': 24, 'Indonesia': 32, 'South Korea': 25, 'Mexico': 10, 'Taiwan': 32,
    'Thailand': 36, 'European Union': 20, 'Canada': 0, 'Hong Kong': 34
}

# --- Product Categories
products = {
    'Apparel': ['Cotton/Natural', 'Synthetic'],
    'Electronics': ['Chips', 'EV Batteries', 'Consumer Devices'],
    'Furniture': [],
    'Steel/Aluminum': [],
    'Chemicals': ['Plastics', 'Industrial Chemicals'],
    'Automotive Parts': ['EV Components', 'Traditional Components'],
    'Semiconductors': [],
    'Food': [],
    'Medicine': [],
    'Energy/Critical Minerals': [],
}

excluded_categories = [
    'Food', 'Medicine', 'Humanitarian Goods', 'Steel/Aluminum',
    'Autos/Auto Parts', 'Semiconductors', 'Lumber', 'Pharmaceuticals',
    'Energy/Critical Minerals', 'Precious Metals'
]

# --- Supply Strength Mapping
supply_strength_mapping = {
    ('China', 'Apparel'): 'High', ('Vietnam', 'Apparel'): 'High',
    ('Bangladesh', 'Apparel'): 'High', ('India', 'Apparel'): 'High',
    ('Cambodia', 'Apparel'): 'Medium', ('Indonesia', 'Apparel'): 'Medium',
    ('China', 'Electronics'): 'High', ('South Korea', 'Electronics'): 'High',
    ('Malaysia', 'Electronics'): 'High', ('Taiwan', 'Electronics'): 'High',
    ('Thailand', 'Electronics'): 'Medium', ('Indonesia', 'Electronics'): 'Medium',
    ('China', 'Furniture'): 'High', ('Vietnam', 'Furniture'): 'High',
    ('Malaysia', 'Furniture'): 'Medium', ('Indonesia', 'Furniture'): 'Medium',
    ('China', 'Steel/Aluminum'): 'High', ('South Korea', 'Steel/Aluminum'): 'High',
    ('India', 'Steel/Aluminum'): 'Medium',
    ('China', 'Chemicals'): 'High', ('India', 'Chemicals'): 'High',
    ('Malaysia', 'Chemicals'): 'Medium',
    ('Mexico', 'Automotive Parts'): 'High', ('China', 'Automotive Parts'): 'High',
    ('South Korea', 'Automotive Parts'): 'High', ('Thailand', 'Automotive Parts'): 'Medium',
    ('Taiwan', 'Semiconductors'): 'High', ('South Korea', 'Semiconductors'): 'High',
    ('Malaysia', 'Semiconductors'): 'Medium', ('Singapore', 'Semiconductors'): 'Medium',
}

# --- Functions
def get_tariff(country):
    return annex_tariffs.get(country, 10)

def get_supply_strength(country, category):
    return supply_strength_mapping.get((country, category), 'Low')

def number_to_words(value):
    p = inflect.engine()
    try:
        return p.number_to_words(int(value)).capitalize() + " dollars"
    except:
        return ""

def convert_df(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

# --- Sidebar Inputs
with st.sidebar:
    st.header("📋 Input Your Data")

    if "opt_inputs" not in st.session_state:
        st.session_state.opt_inputs = {}

    category = st.selectbox("Select Product Category:", sorted(products.keys()), key="category")
    subcategory = None
    if products[category]:
        subcategory = st.selectbox("Select Subcategory:", sorted(products[category]), key="subcategory")

    country = st.selectbox("Select Current Import Country:", sorted(list(annex_tariffs.keys())), key="country")
    annual_import_value = st.number_input("Annual Import Value ($):", min_value=0, step=1000, value=100000, key="import_value")
    if annual_import_value:
        st.caption(f"_In Words: {number_to_words(annual_import_value)}_")
    individual_shipment_value = st.number_input("Individual Shipment Value ($) (Optional):", min_value=0, step=100, key="shipment_value")

    if st.button("🔍 Optimize Supply Chain"):
        st.session_state.opt_inputs = {
            "category": category,
            "subcategory": subcategory,
            "country": country,
            "import_value": annual_import_value,
            "shipment_value": individual_shipment_value,
            "run_optimization": True
        }

# --- Optimization Logic
if st.session_state.opt_inputs.get("run_optimization"):

    inputs = st.session_state.opt_inputs
    clean_category = inputs["category"].split(' (')[0]
    current_tariff = get_tariff(inputs["country"])

    st.subheader("📈 Current Tariff Situation")

    if clean_category in excluded_categories:
        st.success(f"✅ {clean_category} is excluded from new tariff rules. No optimization needed.")
        st.markdown("""
        **Note:** Semiconductors are excluded from the new April 2025 reciprocal tariffs.  
        Existing base tariffs (if any) under prior HS Code rules may still apply at low rates (typically 0–4%) depending on specific product classification.
        """)
    else:
        output_rows = []
        for alt_country in annex_tariffs.keys():
            alt_tariff = get_tariff(alt_country)
            savings_percentage = current_tariff - alt_tariff
            if alt_country == inputs["country"] or savings_percentage <= 0:
                continue
            savings_amount = (savings_percentage / 100) * inputs["import_value"]
            strength = get_supply_strength(alt_country, clean_category)

            if clean_category in excluded_categories or (alt_country == "Canada" and alt_tariff == 0):
                excluded_status = "✅ Excluded"
            else:
                excluded_status = "❗ Subject to Tariffs"

            output_rows.append({
                "Alternative Country": alt_country,
                "New Tariff %": alt_tariff,
                "Saving %": round(savings_percentage, 1),
                "Estimated Annual Savings ($)": savings_amount,
                "Supply Strength": strength,
                "Tariff Status": excluded_status
            })

        if output_rows:
            result_df = pd.DataFrame(output_rows)
            strength_priority = {"High": 1, "Medium": 2, "Low": 3}
            result_df['Priority'] = result_df['Supply Strength'].map(strength_priority)
            result_df = result_df.sort_values(by=['Priority', 'Saving %'], ascending=[True, False])

            st.subheader("📊 All Alternative Country Recommendations")
            st.dataframe(result_df.style.format({
                "Estimated Annual Savings ($)": "${:,.2f}",
                "Saving %": "{:.1f}%"
            }))

            st.download_button("📥 Download Results as Excel", data=convert_df(result_df), file_name="tariff_optimization_full.xlsx")

            top5_df = result_df.head(5)

            st.subheader("💰 Estimated Savings by Top 5 Countries")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(top5_df['Alternative Country'], top5_df['Estimated Annual Savings ($)'], color='skyblue')
            ax.set_xlabel('Estimated Annual Savings ($)')
            ax.set_title('Top 5 Savings Opportunity by Country')
            ax.invert_yaxis()
            st.pyplot(fig)

            top_option = top5_df.iloc[0]
            st.success(f"🏆 Best Option: **{top_option['Alternative Country']}** — Save **{top_option['Saving %']}%** = **${top_option['Estimated Annual Savings ($)']:,.2f}** per year! (Supply Strength: {top_option['Supply Strength']}, {top_option['Tariff Status']})")
        else:
            st.warning("❗ No better alternative countries found.")

# --- About Section
st.markdown("---")
with st.expander("ℹ️ About this App"):
    st.write("""
    **Supply Chain Tariff Optimization AI** is a smart platform designed to help businesses navigate the evolving global trade environment, especially in light of the 2025 US tariff updates.

    Built to empower sourcing and procurement leaders, the tool analyzes tariff impacts, identifies alternative sourcing opportunities, estimates potential savings, and offers AI-powered vendor discovery — all within a clean, executive-ready experience.

    **About the Creator:**

    Vishal Singh — a passionate Supply Chain Professional and current Graduate Student at **SUNY Buffalo** — developed this platform to bridge real-world trade challenges with modern AI capabilities. 

    His mission is to help companies make smarter sourcing decisions, turn tariff disruptions into competitive advantage, and embrace AI in practical, business-driven ways.

    **Powered by:** Groq AI + Streamlit
    """)
    st.caption("Created with care for the global sourcing community.")
