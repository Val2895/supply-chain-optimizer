import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import openai
import toml
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

country = st.sidebar.selectbox("Select Current Import Country:", sorted(list(annex_tariffs.keys())))

annual_import_value = st.sidebar.number_input("Annual Import Value ($):", min_value=0, step=1000, value=100000)
individual_shipment_value = st.sidebar.number_input("Individual Shipment Value ($) (Optional):", min_value=0, step=100)

search = st.sidebar.button("🔍 Optimize Supply Chain")

# --- Main Panel Outputs
if search:

    st.subheader("📈 Current Tariff Situation")

    clean_category = category.split(' (')[0]

    if clean_category in excluded_categories:
        st.success(f"✅ {clean_category} is excluded from new tariff rules.")
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
            strength = get_supply_strength(alt_country, clean_category)

            excluded = "✅ Excluded" if clean_category in excluded_categories else "❗ Subject to Tariffs"

            output_rows.append({
                "Alternative Country": alt_country,
                "New Tariff %": alt_tariff,
                "Saving %": round(savings_percentage, 1),
                "Estimated Annual Savings ($)": savings_amount,
                "Supply Strength": strength,
                "Tariff Status": excluded
            })

        if output_rows:
            result_df = pd.DataFrame(output_rows)
            strength_priority = {"High": 1, "Medium": 2, "Low": 3}
            result_df['Priority'] = result_df['Supply Strength'].map(strength_priority)
            result_df = result_df.sort_values(by=['Priority', 'Saving %'], ascending=[True, False])

            top5_df = result_df.head(5)

            st.subheader("📊 Alternative Country Recommendations (Top 5)")
            st.dataframe(top5_df.style.format({
                "Estimated Annual Savings ($)": "${:,.2f}",
                "Saving %": "{:.1f}%"
            }))

            st.download_button("📥 Download Results as Excel", data=convert_df(top5_df), file_name="tariff_optimization_top5.xlsx")

            st.subheader("💰 Estimated Savings by Top 5 Countries")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(top5_df['Alternative Country'], top5_df['Estimated Annual Savings ($)'], color='skyblue')
            ax.set_xlabel('Estimated Annual Savings ($)')
            ax.set_title('Top 5 Savings Opportunity by Country')
            ax.invert_yaxis()
            st.pyplot(fig)

            # Top Recommendation
            top_option = top5_df.iloc[0]
            st.success(f"🏆 Best Option: **{top_option['Alternative Country']}** — Save **{top_option['Saving %']}%** = **${top_option['Estimated Annual Savings ($)']:,.2f}** per year! (Supply Strength: {top_option['Supply Strength']}, {top_option['Tariff Status']})")

            # --- New Vendor Help Search (Groq Chat)
            st.subheader("🚀 Sourcing Help")

            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            with st.form("vendor_search_form"):
                vendor_query = st.text_input("What sourcing help do you want? (e.g., 'Find furniture vendors in Vietnam')")
                submitted = st.form_submit_button("Search")

                if submitted and vendor_query:
                    api_key = st.secrets["GROQ_API_KEY"]
                    openai.api_key = api_key
                    openai.api_base = "https://api.groq.com/openai/v1"

                    with st.spinner("Fetching sourcing suggestions..."):
                        try:
                            response = openai.ChatCompletion.create(
                                model="llama3-70b-8192",
                                messages=[
                                    {"role": "system", "content": "You are a global sourcing expert helping businesses find vendors and platforms for international trade."},
                                    {"role": "user", "content": vendor_query},
                                ],
                                temperature=0.3,
                                max_tokens=1000
                            )
                            reply = response['choices'][0]['message']['content']
                            st.session_state.chat_history.append((vendor_query, reply))
                        except Exception as e:
                            st.error(f"⚠️ Failed to get a response: {str(e)}")

            # Display full chat history
            if st.session_state.chat_history:
                for i, (q, a) in enumerate(st.session_state.chat_history[::-1]):
                    with st.expander(f"💬 Q{i+1}: {q}", expanded=False):
                        st.write(a)

        else:
            st.warning("❗ No better alternative countries found.")

# --- About Section
st.markdown("---")
with st.expander("ℹ️ About this App"):
    st.write("""
    This tool helps businesses optimize their global sourcing strategies by analyzing tariff impacts introduced by the 2025 US trade policy updates.
    It highlights potential savings, evaluates supplier ecosystem strength, and provides AI-powered advisory to help companies make smarter supply chain moves.
    """)
    st.caption("Powered by Groq AI + Streamlit")
