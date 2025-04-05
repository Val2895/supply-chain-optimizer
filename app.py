# --- Supply Chain Tariff Optimization AI App (Final Version) ---

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import toml
from io import BytesIO

# --- Load Theme Settings Manually
theme_config = toml.load('streamlit_config.toml')

st.set_page_config(
    page_title="Supply Chain Tariff Optimization AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Branding Header
# (Optional: Remove this if logo not ready)
# st.image('branding/logo.png', width=180)
st.markdown("<h1 style='text-align: center; color: #003366;'>Supply Chain Tariff Optimization AI</h1>", unsafe_allow_html=True)
st.caption("Helping you source smarter in a shifting trade landscape — Powered by Gemini AI")

# --- Tariff Data (Annex I)
annex_tariffs = {
    'Algeria': 30, 'Angola': 32, 'Bangladesh': 37, 'Bosnia and Herzegovina': 35,
    'Botswana': 37, 'Brunei': 24, 'Cambodia': 49, 'Cameroon': 11, 'Chad': 13,
    'China': 34, 'Côte d`Ivoire': 21, 'Democratic Republic of the Congo': 11,
    'Equatorial Guinea': 13, 'European Union': 20, 'Falkland Islands': 41, 'Fiji': 32,
    'Guyana': 38, 'India': 26, 'Indonesia': 32, 'Iraq': 39, 'Israel': 17, 'Japan': 24,
    'Jordan': 20, 'Kazakhstan': 27, 'Laos': 48, 'Lesotho': 50, 'Libya': 31,
    'Liechtenstein': 37, 'Madagascar': 47, 'Malawi': 17, 'Malaysia': 24, 'Mauritius': 40,
    'Moldova': 31, 'Mozambique': 16, 'Myanmar (Burma)': 44, 'Namibia': 21, 'Nauru': 30,
    'Nicaragua': 18, 'Nigeria': 14, 'North Macedonia': 33, 'Norway': 15, 'Pakistan': 29,
    'Philippines': 17, 'Serbia': 37, 'South Africa': 30, 'South Korea': 25,
    'Sri Lanka': 44, 'Switzerland': 31, 'Syria': 41, 'Taiwan': 32, 'Thailand': 36,
    'Tunisia': 28, 'Vanuatu': 22, 'Venezuela': 15, 'Vietnam': 46, 'Zambia': 17,
    'Zimbabwe': 18
}

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

supply_strength_mapping = {
    # Apparel
    ('China', 'Apparel'): 'High',
    ('Vietnam', 'Apparel'): 'High',
    ('Bangladesh', 'Apparel'): 'High',
    ('India', 'Apparel'): 'High',
    ('Cambodia', 'Apparel'): 'Medium',
    ('Indonesia', 'Apparel'): 'Medium',

    # Electronics
    ('China', 'Electronics'): 'High',
    ('South Korea', 'Electronics'): 'High',
    ('Malaysia', 'Electronics'): 'High',
    ('Taiwan', 'Electronics'): 'High',
    ('Thailand', 'Electronics'): 'Medium',
    ('Indonesia', 'Electronics'): 'Medium',

    # Furniture
    ('China', 'Furniture'): 'High',
    ('Vietnam', 'Furniture'): 'High',
    ('Malaysia', 'Furniture'): 'Medium',
    ('Indonesia', 'Furniture'): 'Medium',

    # Steel/Aluminum
    ('China', 'Steel/Aluminum'): 'High',
    ('South Korea', 'Steel/Aluminum'): 'High',
    ('India', 'Steel/Aluminum'): 'Medium',

    # Chemicals
    ('China', 'Chemicals'): 'High',
    ('India', 'Chemicals'): 'High',
    ('Malaysia', 'Chemicals'): 'Medium',

    # Automotive Parts
    ('Mexico', 'Automotive Parts'): 'High',
    ('China', 'Automotive Parts'): 'High',
    ('South Korea', 'Automotive Parts'): 'High',
    ('Thailand', 'Automotive Parts'): 'Medium',

    # Semiconductors
    ('Taiwan', 'Semiconductors'): 'High',
    ('South Korea', 'Semiconductors'): 'High',
    ('Malaysia', 'Semiconductors'): 'Medium',
    ('Singapore', 'Semiconductors'): 'Medium',

    # Food
    ('USA', 'Food'): 'High',
    ('Canada', 'Food'): 'High',
    ('Mexico', 'Food'): 'High',
    ('European Union', 'Food'): 'High',
    ('Brazil', 'Food'): 'Medium',
    ('Argentina', 'Food'): 'Medium',

    # Medicine
    ('USA', 'Medicine'): 'High',
    ('European Union', 'Medicine'): 'High',
    ('India', 'Medicine'): 'High',
    ('China', 'Medicine'): 'Medium',

    # Energy/Critical Minerals
    ('Australia', 'Energy/Critical Minerals'): 'High',
    ('Canada', 'Energy/Critical Minerals'): 'High',
    ('USA', 'Energy/Critical Minerals'): 'High',
    ('Chile', 'Energy/Critical Minerals'): 'Medium',
    ('South Africa', 'Energy/Critical Minerals'): 'Medium',
}

excluded_categories = [
    'Food', 'Medicine', 'Humanitarian Goods', 'Steel/Aluminum',
    'Autos/Auto Parts', 'Semiconductors', 'Lumber', 'Pharmaceuticals',
    'Energy/Critical Minerals', 'Precious Metals'
]

def get_tariff(country):
    return annex_tariffs.get(country, 10)

def get_supply_strength(country, category):
    return supply_strength_mapping.get((country, category), 'Low')

def convert_df(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

# --- Sidebar Inputs
st.sidebar.header("📋 Input Your Data")

category = st.sidebar.selectbox("Select Product Category:", sorted(products.keys()))
subcategory = None
if products[category]:
    subcategory = st.sidebar.selectbox("Select Subcategory:", sorted(products[category]))

country = st.sidebar.selectbox("Select Current Import Country:", sorted(list(annex_tariffs.keys()) + ['Canada', 'Mexico', 'Hong Kong', 'USA']))
annual_import_value = st.sidebar.number_input("Annual Import Value ($):", value=100000, step=5000)
individual_shipment_value = st.sidebar.number_input("Individual Shipment Value ($) (Optional):", value=0, step=100)

search = st.sidebar.button("🔍 Optimize Supply Chain")





# --- Main Panel Outputs
if search:

    st.subheader("📈 Current Tariff Situation")
    if category in excluded_categories:
        st.success(f"✅ {category} is an excluded category. No new tariffs apply.")
    else:
        if individual_shipment_value and country in ['China', 'Hong Kong'] and individual_shipment_value < 800:
            st.warning("⚠️ De Minimis eliminated for China/Hong Kong under $800 shipments. Full duties now apply.")

        current_tariff = get_tariff(country)
        st.info(f"Current Tariff from **{country}**: **{current_tariff}%**")

        output_rows = []
        for alt_country in annex_tariffs.keys():
            if alt_country == country:
                continue
            alt_tariff = get_tariff(alt_country)
            savings_percentage = current_tariff - alt_tariff
            if savings_percentage <= 0:
                continue
            savings_amount = (savings_percentage / 100) * annual_import_value
            strength = get_supply_strength(alt_country, category)

            output_rows.append({
                "Alternative Country": alt_country,
                "New Tariff %": alt_tariff,
                "Saving %": round(savings_percentage, 1),
                "Estimated Annual Savings ($)": savings_amount,
                "Supply Strength": strength
            })

        if output_rows:
            result_df = pd.DataFrame(output_rows)
            strength_priority = {"High": 1, "Medium": 2, "Low": 3}
            result_df['Priority'] = result_df['Supply Strength'].map(strength_priority)
            result_df = result_df.sort_values(by=['Priority', 'Saving %'], ascending=[True, False])

            st.subheader("📊 Alternative Country Recommendations")
            st.dataframe(result_df.style.format({
                "Estimated Annual Savings ($)": "${:,.2f}",
                "Saving %": "{:.1f}%"
            }))

            # Download Excel
            st.download_button("📥 Download Results as Excel", data=convert_df(result_df), file_name="tariff_optimization_results.xlsx")

            # --- Bar Chart
            st.subheader("💰 Estimated Savings by Country")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(result_df['Alternative Country'], result_df['Estimated Annual Savings ($)'], color='skyblue')
            ax.set_xlabel('Estimated Annual Savings ($)')
            ax.set_title('Savings Opportunity by Country')
            ax.invert_yaxis()
            st.pyplot(fig)

            # --- Scatter Plot
            st.subheader("🏭 Supply Strength vs Savings")
            strength_map = {"High": 3, "Medium": 2, "Low": 1}
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            ax2.scatter(result_df['Estimated Annual Savings ($)'], result_df['Supply Strength'].map(strength_map), c='green', s=100)
            ax2.set_yticks([1,2,3])
            ax2.set_yticklabels(['Low','Medium','High'])
            ax2.set_xlabel('Estimated Annual Savings ($)')
            ax2.set_ylabel('Supply Strength')
            ax2.set_title('Supply Strength vs Savings')
            st.pyplot(fig2)

            # Best Option
            top_option = result_df.iloc[0]
            st.success(f"🏆 Best Option: **{top_option['Alternative Country']}** — Save **{top_option['Saving %']}%** = **${top_option['Estimated Annual Savings ($)']:,.2f}** per year! (Supply Strength: {top_option['Supply Strength']})")

        else:
            st.warning("❗ No better alternative countries found.")

# --- Gemini LLM Chat Feature
st.markdown("---")
st.header("💬 Ask About Tariffs and Sourcing")

# Get Gemini API Key securely
api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else st.text_input("Enter your Gemini API Key:")

if api_key:
    user_question = st.chat_input("Ask your question about tariffs, sourcing, vendors...")

    if user_question:
        st.info(f"💬 You asked: **{user_question}**")

        # Build the LLM prompt
        system_prompt = """
        You are a highly knowledgeable global trade advisor specializing in international tariffs, sourcing optimization, and supply chain strategy.
        Provide accurate, strategic, and detailed advice to businesses impacted by 2025 US trade policy changes.
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        body = {
            "contents": [{"role": "user", "parts": [f"{system_prompt} \n\n{user_question}"]}]
        }

        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            headers=headers,
            json=body,
            timeout=30
        )

        if response.status_code == 200:
            reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            st.success(reply)
        else:
            st.error("⚠️ Failed to get a response from Gemini. Check your API key or try again later.")

# --- About Section
st.markdown("---")
with st.expander("ℹ️ About this App"):
    st.write("""
    This tool helps businesses optimize their global sourcing strategies by analyzing tariff impacts introduced by the 2025 US trade policy updates.
    It highlights potential savings, evaluates supplier ecosystem strength, and provides AI-powered advisory to help companies make smarter supply chain moves.
    """)
    st.caption("Powered by Gemini AI + Streamlit")

