import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Multi-Company Comparison | WRDS Financial Explorer", layout="wide")

if "comparison_data" not in st.session_state:
    st.session_state["comparison_data"] = None
if "companies_input" not in st.session_state:
    st.session_state["companies_input"] = ""
if "year_range" not in st.session_state:
    st.session_state["year_range"] = (2019, 2024)
if "industry_benchmark" not in st.session_state:
    st.session_state["industry_benchmark"] = None

col1, col2 = st.columns([0.1, 0.9])
with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("Home.py")
with col2:
    st.title("🔄 Multi-Company Financial Comparison")

st.markdown("""
<style>
    .main {
        background-color: var(--background-color);
    }
    .stButton>button {
        background-color: #165DFF;
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0e42c9;
        border: none;
    }
    .card {
        background-color: var(--secondary-background-color);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        border: 1px solid var(--border-color);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("### Compare up to 5 companies side by side | WRDS Live Data | Industry Benchmark")
st.divider()

if not st.session_state.get("is_authenticated", False) or not st.session_state.get("wrds_conn"):
    st.error("🔐 Authentication Required")
    st.stop()

conn = st.session_state["wrds_conn"]

st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Enter Companies to Compare")
st.info("Enter company names, tickers, or GVKEYs separated by commas (e.g., AAPL, MSFT, GOOGL)")
companies_input = st.text_input(
    "Companies (max 5)",
    placeholder="AAPL, MSFT, AMZN, GOOGL, META",
    value=st.session_state["companies_input"]
)
year_range = st.slider("Year Range", 2014, 2024, st.session_state["year_range"], step=1)
force_industry_benchmark = st.checkbox("Force industry benchmark (use first company's industry)", value=False)

if companies_input != st.session_state["companies_input"] or year_range != st.session_state["year_range"] or force_industry_benchmark != st.session_state.get("force_industry_benchmark", False):
    st.session_state["comparison_data"] = None
    st.session_state["companies_input"] = companies_input
    st.session_state["year_range"] = year_range
    st.session_state["industry_benchmark"] = None
    st.session_state["force_industry_benchmark"] = force_industry_benchmark

if st.button("🔍 Start Comparison", use_container_width=True):
    if companies_input:
        companies = [c.strip() for c in companies_input.split(",")][:5]
        
        if len(companies) < 2:
            st.warning("⚠️ Please enter at least 2 companies to compare")
            st.stop()
        
        with st.spinner(f"Fetching data for {len(companies)} companies and industry benchmarks..."):
            try:
                start_year, end_year = year_range
                all_data = []
                all_sics = []
                
                for company in companies:
                    query = """
                        SELECT f.gvkey, f.conm, f.tic, f.fyear, c.sic, f.revt, f.ni, f.gp, f.at, f.ceq, f.act, f.lct, f.dltt, f.dlc
                        FROM comp.funda f
                        JOIN comp.company c ON f.gvkey = c.gvkey
                        WHERE (f.conm ILIKE %s OR f.tic ILIKE %s OR f.gvkey = %s)
                        AND f.fyear BETWEEN %s AND %s
                        AND f.revt > 0 AND f.at > 0 AND f.ceq > 0 AND f.lct > 0
                        ORDER BY f.fyear
                    """
                    
                    df = conn.raw_sql(
                        query,
                        params=(f"%{company}%", f"%{company}%", company, start_year, end_year)
                    )
                    
                    if not df.empty:
                        df.columns = ["GVKEY", "Company", "Ticker", "Year", "SIC", "revt", "ni", "gp", "at", "ceq", "act", "lct", "dltt", "dlc"]
                        df["Year"] = df["Year"].astype(int)
                        df = df.drop_duplicates(subset=["Year"])
                        
                        df["Revenue"] = df["revt"]
                        df["Net Income"] = df["ni"]
                        df["Gross Margin"] = df.apply(lambda x: (x["gp"]/x["revt"])*100 if x["revt"] != 0 else None, axis=1)
                        df["Net Margin"] = df.apply(lambda x: (x["ni"]/x["revt"])*100 if x["revt"] != 0 else None, axis=1)
                        df["ROE"] = df.apply(lambda x: (x["ni"]/x["ceq"])*100 if x["ceq"] != 0 else None, axis=1)
                        df["ROA"] = df.apply(lambda x: (x["ni"]/x["at"])*100 if x["at"] != 0 else None, axis=1)
                        df["Current Ratio"] = df.apply(lambda x: x["act"]/x["lct"] if x["lct"] != 0 else None, axis=1)
                        df["Debt to Equity"] = df.apply(lambda x: (x["dltt"]+x["dlc"])/x["ceq"] if x["ceq"] != 0 else None, axis=1)
                        
                        all_data.append(df)
                        if pd.notna(df["SIC"].iloc[0]):
                            sic_code = str(int(df["SIC"].iloc[0]))
                            all_sics.append(sic_code[:2])
                
                if not all_data:
                    st.warning("⚠️ No valid data found for any of the companies")
                    st.stop()
                
                combined_df = pd.concat(all_data, ignore_index=True)
                combined_df = combined_df.round(2)
                combined_df = combined_df.dropna()
                
                common_sic = None
                if all_sics:
                    if force_industry_benchmark:
                        common_sic = all_sics[0]
                    elif all(s == all_sics[0] for s in all_sics):
                        common_sic = all_sics[0]
                
                industry_df = None
                if common_sic:
                    industry_query = """
                        SELECT fyear,
                               AVG(revt) as industry_revenue,
                               AVG(ni) as industry_net_income,
                               AVG(gp/revt*100) as industry_gross_margin,
                               AVG(ni/revt*100) as industry_net_margin,
                               AVG(ni/ceq*100) as industry_roe,
                               AVG(ni/at*100) as industry_roa,
                               AVG(act/lct) as industry_current_ratio,
                               AVG((dltt+dlc)/ceq) as industry_debt_to_equity
                        FROM comp.funda f
                        JOIN comp.company c ON f.gvkey = c.gvkey
                        WHERE LEFT(c.sic, 2) = %s
                        AND f.fyear BETWEEN %s AND %s
                        AND f.revt > 0 AND f.at > 0 AND f.ceq > 0 AND f.lct > 0
                        GROUP BY fyear
                        ORDER BY fyear
                    """
                    
                    industry_df = conn.raw_sql(
                        industry_query,
                        params=(common_sic, start_year, end_year)
                    )
                    
                    industry_df.columns = [
                        "Year", "Industry Revenue", "Industry Net Income",
                        "Industry Gross Margin", "Industry Net Margin",
                        "Industry ROE", "Industry ROA",
                        "Industry Current Ratio", "Industry Debt to Equity"
                    ]
                    
                    industry_df["Year"] = industry_df["Year"].astype(int)
                    industry_df = industry_df.round(2)
                    industry_df["Company"] = "Industry Average"
                
                st.session_state["comparison_data"] = combined_df
                st.session_state["industry_benchmark"] = industry_df
                
            except Exception as e:
                st.error("❌ Comparison Failed")
                st.code(f"Error: {str(e)}", language="text")
    else:
        st.warning("⚠️ Please enter at least 2 companies to compare")

if st.session_state["comparison_data"] is not None:
    combined_df = st.session_state["comparison_data"]
    industry_df = st.session_state["industry_benchmark"]
    unique_companies = combined_df["Company"].unique()
    
    success_msg = f"✅ Successfully loaded data for {len(unique_companies)} companies"
    if industry_df is not None and not industry_df.empty:
        success_msg += " | Industry benchmark included"
    st.success(success_msg)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Latest Year Comparison")
    latest_year = combined_df["Year"].max()
    latest_data = combined_df[combined_df["Year"] == latest_year]
    
    if industry_df is not None and not industry_df.empty:
        industry_latest = industry_df[industry_df["Year"] == latest_year].copy()
        if not industry_latest.empty:
            industry_latest["Ticker"] = "IND"
            latest_data = pd.concat([latest_data, industry_latest], ignore_index=True)
    
    comparison_table = latest_data[["Company", "Ticker", "Revenue", "Net Income", "Gross Margin", "Net Margin", "ROE", "ROA", "Current Ratio", "Debt to Equity"]].copy()
    comparison_table = comparison_table.set_index("Company")
    
    formatted_table = comparison_table.copy()
    for col in ["Revenue", "Net Income"]:
        formatted_table[col] = formatted_table[col].apply(lambda x: f"${x:,.0f}M" if not pd.isna(x) else "N/A")
    for col in ["Gross Margin", "Net Margin", "ROE", "ROA"]:
        formatted_table[col] = formatted_table[col].apply(lambda x: f"{x:.2f}%" if not pd.isna(x) else "N/A")
    for col in ["Current Ratio", "Debt to Equity"]:
        formatted_table[col] = formatted_table[col].apply(lambda x: f"{x:.2f}x" if not pd.isna(x) else "N/A")
    
    st.dataframe(formatted_table, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 Trend Comparison vs Industry Benchmark")
    
    indicators = ["Revenue", "Net Income", "Gross Margin", "Net Margin", "ROE", "ROA", "Current Ratio", "Debt to Equity"]
    selected_indicator = st.selectbox(
        "Select Indicator to Compare",
        options=indicators,
        index=0
    )
    
    plot_df = combined_df[["Year", "Company", selected_indicator]]
    if industry_df is not None and not industry_df.empty and f"Industry {selected_indicator}" in industry_df.columns:
        industry_plot = industry_df[["Year", "Company", f"Industry {selected_indicator}"]].rename(columns={f"Industry {selected_indicator}": selected_indicator})
        plot_df = pd.concat([plot_df, industry_plot], ignore_index=True)
    
    fig = px.line(
        plot_df, x="Year", y=selected_indicator, color="Company",
        title=f"{selected_indicator} Comparison",
        markers=True,
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.D3
    )
    fig.update_layout(height=500)
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎯 Performance Radar Chart with Industry Benchmark")
    
    radar_data = latest_data.copy()
    for col in indicators:
        min_val = radar_data[col].min()
        max_val = radar_data[col].max()
        if max_val != min_val:
            radar_data[col] = (radar_data[col] - min_val) / (max_val - min_val)
        else:
            radar_data[col] = 0.5
    
    fig = go.Figure()
    
    for _, row in radar_data.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row[ind] for ind in indicators],
            theta=indicators,
            name=row["Company"],
            fill="toself"
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Normalized Financial Performance Comparison",
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.download_button(
        label="📥 Export Comparison Data as CSV",
        data=combined_df.to_csv(index=False),
        file_name="Multi_Company_Comparison_Data_with_Industry.csv",
        mime="text/csv"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.markdown("© 2026 WRDS Financial Explorer | Data Source: WRDS Compustat Database | Version 1.0.0")
