import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Financial Dashboard | WRDS Financial Explorer", layout="wide")

col1, col2 = st.columns([0.1, 0.9])
with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("Home.py")
with col2:
    st.title("📊 Financial Dashboard")

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
    .metric-card {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        text-align: center;
        border: 1px solid var(--border-color);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("### 20+ Core Financial Indicators | WRDS Live Data | Industry Benchmark")
st.divider()

if not st.session_state.get("is_authenticated", False) or not st.session_state.get("wrds_conn"):
    st.error("🔐 Authentication Required: Please log in via Home Page")
    st.stop()

conn = st.session_state["wrds_conn"]

if "dashboard_data" not in st.session_state:
    st.session_state["dashboard_data"] = None
if "selected_company" not in st.session_state:
    st.session_state["selected_company"] = None
if "search_results" not in st.session_state:
    st.session_state["search_results"] = None
if "industry_data" not in st.session_state:
    st.session_state["industry_data"] = None

col_search, col_year, col_refresh = st.columns([3, 2, 1])
with col_search:
    keyword = st.text_input(
        "🔍 Search Company (Name / Ticker / GVKEY)",
        placeholder="e.g., Apple, AAPL, 16909, 001690"
    )
with col_year:
    year_range = st.slider("Year Range", 2014, 2024, (2015, 2024), step=1)
with col_refresh:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state["dashboard_data"] = None
        st.session_state["selected_company"] = None
        st.session_state["search_results"] = None
        st.session_state["industry_data"] = None
        st.rerun()

indicator_desc = {
    "Revenue": "Total annual revenue from sales (Million USD)",
    "Net Income": "Profit after all expenses and taxes (Million USD)",
    "Gross Profit": "Revenue minus cost of goods sold (Million USD)",
    "Total Assets": "Total assets owned by the company (Million USD)",
    "Total Equity": "Shareholders' equity (Million USD)",
    "Gross Margin": "Gross profit as percentage of revenue (%)",
    "Net Margin": "Net income as percentage of revenue (%)",
    "ROE": "Return on Equity: Profit generated from shareholders' equity (%)",
    "ROA": "Return on Assets: Profit generated from total assets (%)",
    "Current Ratio": "Ability to pay short-term obligations (x)",
    "Debt to Equity": "Financial leverage ratio (x)",
    "Asset Turnover": "Efficiency of using assets to generate revenue (x)",
    "Revenue Growth": "Year-over-year revenue growth rate (%)",
    "Net Income Growth": "Year-over-year net income growth rate (%)"
}

if keyword:
    if st.session_state["search_results"] is None or st.session_state.get("last_keyword") != keyword:
        with st.spinner("Searching WRDS Compustat Database..."):
            try:
                start_year, end_year = year_range
                
                gvkey_candidates = [keyword]
                if keyword.isdigit() and len(keyword) == 5:
                    gvkey_candidates.append(f"0{keyword}")
                
                gvkey_conditions = " OR ".join([f"gvkey = %s" for _ in gvkey_candidates])
                params = tuple([f"%{keyword}%", f"%{keyword}%"] + gvkey_candidates + [start_year, end_year])
                
                query = f"""
                    SELECT DISTINCT gvkey, conm, tic
                    FROM comp.funda
                    WHERE (conm ILIKE %s OR tic ILIKE %s OR {gvkey_conditions})
                    AND fyear BETWEEN %s AND %s
                    AND revt > 0
                    ORDER BY conm
                """
                
                search_results = conn.raw_sql(query, params=params)
                
                if search_results.empty:
                    st.warning("⚠️ No matching companies found in WRDS")
                    st.session_state["search_results"] = None
                    st.session_state["last_keyword"] = keyword
                    st.stop()
                
                st.session_state["search_results"] = search_results
                st.session_state["last_keyword"] = keyword
                st.session_state["dashboard_data"] = None
                st.session_state["selected_company"] = None
                st.session_state["industry_data"] = None
                
            except Exception as e:
                st.error("❌ Search Failed")
                st.code(f"Error: {str(e)}", language="text")
                st.stop()
    
    if st.session_state["search_results"] is not None and not st.session_state["search_results"].empty:
        search_results = st.session_state["search_results"]
        
        if len(search_results) == 1:
            selected_gvkey = search_results.iloc[0]["gvkey"]
            st.session_state["selected_company"] = selected_gvkey
        else:
            company_options = [f"{row['conm']} ({row['tic']}) - GVKEY: {row['gvkey']}" 
                              for _, row in search_results.iterrows()]
            
            selected_index = st.selectbox(
                "Multiple companies found. Please select one:",
                options=range(len(company_options)),
                format_func=lambda x: company_options[x]
            )
            
            selected_gvkey = search_results.iloc[selected_index]["gvkey"]
            st.session_state["selected_company"] = selected_gvkey
    
    if st.session_state["selected_company"] is not None:
        selected_gvkey = st.session_state["selected_company"]
        
        if st.session_state["dashboard_data"] is None or st.session_state.get("last_gvkey") != selected_gvkey:
            with st.spinner("Loading financial data and industry benchmarks..."):
                try:
                    start_year, end_year = year_range
                    
                    # 修复：连接company表获取sic代码
                    query = """
                        SELECT f.gvkey, f.conm, f.tic, f.fyear, c.sic,
                               f.revt, f.ni, f.gp, f.at, f.ceq, f.act, f.lct, f.dltt, f.dlc
                        FROM comp.funda f
                        JOIN comp.company c ON f.gvkey = c.gvkey
                        WHERE f.gvkey = %s
                        AND f.fyear BETWEEN %s AND %s
                        AND f.revt > 0 AND f.at > 0 AND f.ceq > 0 AND f.lct > 0
                        ORDER BY f.fyear
                    """
                    
                    df = conn.raw_sql(
                        query,
                        params=(selected_gvkey, start_year, end_year)
                    )
                    
                    if df.empty:
                        st.warning("⚠️ No financial data found for the selected year range")
                        st.stop()
                    
                    df.columns = [
                        "GVKEY", "Company", "Ticker", "Year", "SIC",
                        "revt", "ni", "gp", "at", "ceq", "act", "lct", "dltt", "dlc"
                    ]
                    
                    df["Year"] = df["Year"].astype(int)
                    industry_sic = str(df["SIC"].iloc[0])[:2] if pd.notna(df["SIC"].iloc[0]) else None
                    
                    df["Revenue"] = df["revt"]
                    df["Net Income"] = df["ni"]
                    df["Gross Profit"] = df["gp"]
                    df["Total Assets"] = df["at"]
                    df["Total Equity"] = df["ceq"]
                    df["Current Assets"] = df["act"]
                    df["Current Liabilities"] = df["lct"]
                    df["Long-term Debt"] = df["dltt"]
                    df["Short-term Debt"] = df["dlc"]
                    
                    df["Gross Margin"] = df.apply(lambda x: (x["gp"]/x["revt"])*100 if x["revt"] != 0 else None, axis=1)
                    df["Net Margin"] = df.apply(lambda x: (x["ni"]/x["revt"])*100 if x["revt"] != 0 else None, axis=1)
                    df["ROE"] = df.apply(lambda x: (x["ni"]/x["ceq"])*100 if x["ceq"] != 0 else None, axis=1)
                    df["ROA"] = df.apply(lambda x: (x["ni"]/x["at"])*100 if x["at"] != 0 else None, axis=1)
                    df["Current Ratio"] = df.apply(lambda x: x["act"]/x["lct"] if x["lct"] != 0 else None, axis=1)
                    df["Debt to Equity"] = df.apply(lambda x: (x["dltt"]+x["dlc"])/x["ceq"] if x["ceq"] != 0 else None, axis=1)
                    df["Asset Turnover"] = df.apply(lambda x: x["revt"]/x["at"] if x["at"] != 0 else None, axis=1)
                    df["Revenue Growth"] = df["revt"].pct_change() * 100
                    df["Net Income Growth"] = df["ni"].pct_change() * 100
                    
                    df = df.round(2)
                    df = df.dropna()
                    
                    if df.empty:
                        st.warning("⚠️ No valid data after cleaning. Please try a different year range.")
                        st.stop()
                    
                    industry_df = pd.DataFrame()
                    if industry_sic:
                        industry_query = """
                            SELECT fyear,
                                   AVG(revt) as industry_revenue,
                                   AVG(ni) as industry_net_income,
                                   AVG(gp/revt*100) as industry_gross_margin,
                                   AVG(ni/revt*100) as industry_net_margin,
                                   AVG(ni/ceq*100) as industry_roe,
                                   AVG(ni/at*100) as industry_roa,
                                   AVG(act/lct) as industry_current_ratio,
                                   AVG((dltt+dlc)/ceq) as industry_debt_to_equity,
                                   AVG(revt/at) as industry_asset_turnover
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
                            params=(industry_sic, start_year, end_year)
                        )
                        
                        industry_df.columns = [
                            "Year", "Industry Revenue", "Industry Net Income",
                            "Industry Gross Margin", "Industry Net Margin",
                            "Industry ROE", "Industry ROA",
                            "Industry Current Ratio", "Industry Debt to Equity",
                            "Industry Asset Turnover"
                        ]
                        
                        industry_df["Year"] = industry_df["Year"].astype(int)
                        industry_df = industry_df.round(2)
                        
                        df = pd.merge(df, industry_df, on="Year", how="left")
                    
                    st.session_state["dashboard_data"] = df
                    st.session_state["last_gvkey"] = selected_gvkey
                    st.session_state["industry_data"] = industry_df
                    
                except Exception as e:
                    st.error("❌ Data Loading Failed")
                    st.code(f"Error: {str(e)}", language="text")
                    st.stop()
        
        if st.session_state["dashboard_data"] is not None:
            df = st.session_state["dashboard_data"]
            latest = df.iloc[-1]
            company_name = latest["Company"]
            industry_sic = str(latest["SIC"])[:2] if pd.notna(latest["SIC"]) else "N/A"
            
            st.markdown(f'<div class="card">', unsafe_allow_html=True)
            st.subheader(f"🏢 {company_name} ({latest['Ticker']}) - Financial Overview")
            st.markdown(f"**GVKEY: {latest['GVKEY']} | SIC: {industry_sic} | Latest Data: {int(latest['Year'])}**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    label="💰 Revenue",
                    value=f"${latest['Revenue']:,.0f}M",
                    delta=f"{latest['Revenue Growth']:.1f}%" if not pd.isna(latest['Revenue Growth']) else "N/A"
                )
                if "Industry Revenue" in latest and pd.notna(latest["Industry Revenue"]):
                    st.caption(f"Industry Avg: ${latest['Industry Revenue']:,.0f}M")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    label="💵 Net Income",
                    value=f"${latest['Net Income']:,.0f}M",
                    delta=f"{latest['Net Income Growth']:.1f}%" if not pd.isna(latest['Net Income Growth']) else "N/A"
                )
                if "Industry Net Income" in latest and pd.notna(latest["Industry Net Income"]):
                    st.caption(f"Industry Avg: ${latest['Industry Net Income']:,.0f}M")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    label="📈 ROE",
                    value=f"{latest['ROE']:.1f}%",
                    delta=f"{latest['ROE'] - df.iloc[-2]['ROE']:.1f}pp" if len(df) >= 2 else "N/A"
                )
                if "Industry ROE" in latest and pd.notna(latest["Industry ROE"]):
                    st.caption(f"Industry Avg: {latest['Industry ROE']:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    label="⚖️ Current Ratio",
                    value=f"{latest['Current Ratio']:.2f}x",
                    delta=f"{latest['Current Ratio'] - df.iloc[-2]['Current Ratio']:.2f}x" if len(df) >= 2 else "N/A"
                )
                if "Industry Current Ratio" in latest and pd.notna(latest["Industry Current Ratio"]):
                    st.caption(f"Industry Avg: {latest['Industry Current Ratio']:.2f}x")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📈 Financial Trend Analysis vs Industry Benchmark")
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "💰 Profitability", 
                "⚖️ Solvency", 
                "🏃 Operational Efficiency", 
                "📈 Growth"
            ])
            
            with tab1:
                profitability_indicators = ["Revenue", "Net Income", "Gross Profit", "Gross Margin", "Net Margin", "ROE", "ROA"]
                selected_indicator = st.selectbox(
                    "Select Indicator",
                    options=profitability_indicators,
                    index=0
                )
                
                if f"Industry {selected_indicator}" in df.columns and not df[f"Industry {selected_indicator}"].isna().all():
                    plot_df = df[["Year", selected_indicator, f"Industry {selected_indicator}"]].melt(
                        id_vars="Year", var_name="Type", value_name="Value"
                    )
                    color_map = {selected_indicator: "#165DFF", f"Industry {selected_indicator}": "#FF7D00"}
                else:
                    plot_df = df[["Year", selected_indicator]].melt(
                        id_vars="Year", var_name="Type", value_name="Value"
                    )
                    color_map = {selected_indicator: "#165DFF"}
                
                fig = px.line(
                    plot_df, x="Year", y="Value", color="Type",
                    title=f"{company_name} {selected_indicator} Trend",
                    markers=True,
                    template="plotly_white",
                    color_discrete_map=color_map
                )
                fig.update_layout(height=400)
                fig.update_traces(line=dict(width=3))
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"**{selected_indicator}**: {indicator_desc[selected_indicator]}")
            
            with tab2:
                solvency_indicators = ["Current Ratio", "Debt to Equity", "Total Assets", "Total Equity"]
                selected_indicator = st.selectbox(
                    "Select Indicator",
                    options=solvency_indicators,
                    index=0
                )
                
                if selected_indicator in ["Current Ratio", "Debt to Equity"] and f"Industry {selected_indicator}" in df.columns and not df[f"Industry {selected_indicator}"].isna().all():
                    plot_df = df[["Year", selected_indicator, f"Industry {selected_indicator}"]].melt(
                        id_vars="Year", var_name="Type", value_name="Value"
                    )
                    color_map = {selected_indicator: "#165DFF", f"Industry {selected_indicator}": "#FF7D00"}
                else:
                    plot_df = df[["Year", selected_indicator]].melt(
                        id_vars="Year", var_name="Type", value_name="Value"
                    )
                    color_map = {selected_indicator: "#165DFF"}
                
                fig = px.line(
                    plot_df, x="Year", y="Value", color="Type",
                    title=f"{company_name} {selected_indicator} Trend",
                    markers=True,
                    template="plotly_white",
                    color_discrete_map=color_map
                )
                fig.update_layout(height=400)
                fig.update_traces(line=dict(width=3))
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"**{selected_indicator}**: {indicator_desc[selected_indicator]}")
            
            with tab3:
                operational_indicators = ["Asset Turnover", "Gross Profit", "Current Assets", "Current Liabilities"]
                selected_indicator = st.selectbox(
                    "Select Indicator",
                    options=operational_indicators,
                    index=0
                )
                
                if selected_indicator == "Asset Turnover" and f"Industry {selected_indicator}" in df.columns and not df[f"Industry {selected_indicator}"].isna().all():
                    plot_df = df[["Year", selected_indicator, f"Industry {selected_indicator}"]].melt(
                        id_vars="Year", var_name="Type", value_name="Value"
                    )
                    color_map = {selected_indicator: "#165DFF", f"Industry {selected_indicator}": "#FF7D00"}
                else:
                    plot_df = df[["Year", selected_indicator]].melt(
                        id_vars="Year", var_name="Type", value_name="Value"
                    )
                    color_map = {selected_indicator: "#165DFF"}
                
                fig = px.line(
                    plot_df, x="Year", y="Value", color="Type",
                    title=f"{company_name} {selected_indicator} Trend",
                    markers=True,
                    template="plotly_white",
                    color_discrete_map=color_map
                )
                fig.update_layout(height=400)
                fig.update_traces(line=dict(width=3))
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"**{selected_indicator}**: {indicator_desc[selected_indicator]}")
            
            with tab4:
                growth_indicators = ["Revenue Growth", "Net Income Growth"]
                selected_indicator = st.selectbox(
                    "Select Indicator",
                    options=growth_indicators,
                    index=0
                )
                
                fig = px.line(
                    df, x="Year", y=selected_indicator,
                    title=f"{company_name} {selected_indicator} Trend",
                    markers=True,
                    template="plotly_white",
                    color_discrete_sequence=["#165DFF"]
                )
                fig.update_layout(height=400)
                fig.update_traces(line=dict(width=3))
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"**{selected_indicator}**: {indicator_desc[selected_indicator]}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📋 Complete Financial Dataset")
            
            display_df = df.copy()
            
            for col in ["Revenue", "Net Income", "Gross Profit", "Total Assets", "Total Equity", 
                       "Current Assets", "Current Liabilities", "Long-term Debt", "Short-term Debt",
                       "Industry Revenue", "Industry Net Income"]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}M" if not pd.isna(x) else "N/A")
            
            for col in ["Gross Margin", "Net Margin", "ROE", "ROA", "Revenue Growth", "Net Income Growth",
                       "Industry Gross Margin", "Industry Net Margin", "Industry ROE", "Industry ROA"]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%" if not pd.isna(x) else "N/A")
            
            for col in ["Current Ratio", "Debt to Equity", "Asset Turnover",
                       "Industry Current Ratio", "Industry Debt to Equity", "Industry Asset Turnover"]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}x" if not pd.isna(x) else "N/A")
            
            display_columns = [
                "Year", "Revenue", "Net Income", "Gross Profit", "Total Assets", "Total Equity",
                "Gross Margin", "Net Margin", "ROE", "ROA", "Current Ratio", "Debt to Equity"
            ]
            
            st.dataframe(
                display_df[display_columns],
                use_container_width=True,
                hide_index=True
            )
            
            st.download_button(
                label="📥 Export Full Dataset as CSV",
                data=df.to_csv(index=False),
                file_name=f"{company_name.replace(' ', '_')}_Financial_Data_with_Industry.csv",
                mime="text/csv"
            )
            
            with st.expander("📊 Descriptive Statistics"):
                st.dataframe(df[list(indicator_desc.keys())].describe().round(2), use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.markdown("© 2026 WRDS Financial Explorer | Data Source: WRDS Compustat Database | Version 1.0.0")
