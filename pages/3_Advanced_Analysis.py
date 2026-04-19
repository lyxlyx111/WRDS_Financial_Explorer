import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Advanced Analysis | WRDS Financial Explorer", layout="wide")

col1, col2 = st.columns([0.1, 0.9])
with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("Home.py")
with col2:
    st.title("🔬 Advanced Financial Analysis")

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
</style>
""", unsafe_allow_html=True)

st.markdown("### DuPont Analysis, Z-Score Financial Health, and Time Series Forecast | Industry Benchmark")
st.divider()

if not st.session_state.get("is_authenticated", False) or not st.session_state.get("wrds_conn"):
    st.error("🔐 Authentication Required")
    st.stop()

conn = st.session_state["wrds_conn"]

keyword = st.text_input(
    "🔍 Search Company (Name / Ticker / GVKEY)",
    placeholder="e.g., Apple, AAPL, 16909"
)
year_range = st.slider("Year Range", 2014, 2024, (2015, 2024), step=1)

if keyword:
    with st.spinner("Performing advanced financial analysis with industry benchmarks..."):
        try:
            start_year, end_year = year_range
            
            # 修复：连接company表获取sic代码
            query = """
                SELECT f.gvkey, f.conm, f.tic, f.fyear, c.sic, f.revt, f.ni, f.at, f.ceq, f.act, f.lct, f.dltt, f.re, f.wcap
                FROM comp.funda f
                JOIN comp.company c ON f.gvkey = c.gvkey
                WHERE (f.conm ILIKE %s OR f.tic ILIKE %s OR f.gvkey = %s)
                AND f.fyear BETWEEN %s AND %s
                AND f.revt > 0 AND f.at > 0 AND f.ceq > 0 AND f.lct > 0
                ORDER BY f.fyear
            """
            
            df = conn.raw_sql(
                query,
                params=(f"%{keyword}%", f"%{keyword}%", keyword, start_year, end_year)
            )
            
            if df.empty:
                st.warning("⚠️ No matching data found in WRDS")
                st.stop()
            
            df.columns = ["GVKEY", "Company", "Ticker", "Year", "SIC", "revt", "ni", "at", "ceq", "act", "lct", "dltt", "re", "wcap"]
            df["Year"] = df["Year"].astype(int)
            df = df.drop_duplicates(subset=["Year"])
            industry_sic = str(df["SIC"].iloc[0])[:2] if pd.notna(df["SIC"].iloc[0]) else None
            
            df["Net Margin"] = df.apply(lambda row: (row["ni"] / row["revt"]) * 100 if row["revt"] != 0 else None, axis=1)
            df["Asset Turnover"] = df.apply(lambda row: row["revt"] / row["at"] if row["at"] != 0 else None, axis=1)
            df["Equity Multiplier"] = df.apply(lambda row: row["at"] / row["ceq"] if row["ceq"] != 0 else None, axis=1)
            df["ROE"] = df["Net Margin"] * df["Asset Turnover"] * df["Equity Multiplier"] / 100
            
            df["Working Capital / Total Assets"] = df.apply(lambda row: row["wcap"] / row["at"] if row["at"] != 0 else None, axis=1)
            df["Retained Earnings / Total Assets"] = df.apply(lambda row: row["re"] / row["at"] if row["at"] != 0 else None, axis=1)
            df["EBIT / Total Assets"] = df.apply(lambda row: row["ni"] / row["at"] if row["at"] != 0 else None, axis=1)
            df["Market Value of Equity / Total Liabilities"] = df.apply(lambda row: row["ceq"] / (row["dltt"] + row["lct"]) if (row["dltt"] + row["lct"]) != 0 else None, axis=1)
            df["Sales / Total Assets"] = df.apply(lambda row: row["revt"] / row["at"] if row["at"] != 0 else None, axis=1)
            
            df["Z-Score"] = (
                1.2 * df["Working Capital / Total Assets"] +
                1.4 * df["Retained Earnings / Total Assets"] +
                3.3 * df["EBIT / Total Assets"] +
                0.6 * df["Market Value of Equity / Total Liabilities"] +
                1.0 * df["Sales / Total Assets"]
            )
            
            df = df.dropna()
            df = df.round(4)
            
            if df.empty:
                st.warning("⚠️ No valid data after cleaning. Please try a different year range.")
                st.stop()
            
            industry_df = pd.DataFrame()
            if industry_sic:
                industry_query = """
                    SELECT fyear,
                           AVG(ni/revt*100) as industry_net_margin,
                           AVG(revt/at) as industry_asset_turnover,
                           AVG(at/ceq) as industry_equity_multiplier,
                           AVG((ni/revt*100)*(revt/at)*(at/ceq)/100) as industry_roe,
                           AVG(
                               1.2*(wcap/at) +
                               1.4*(re/at) +
                               3.3*(ni/at) +
                               0.6*(ceq/(dltt+lct)) +
                               1.0*(revt/at)
                           ) as industry_z_score
                    FROM comp.funda f
                    JOIN comp.company c ON f.gvkey = c.gvkey
                    WHERE LEFT(c.sic, 2) = %s
                    AND f.fyear BETWEEN %s AND %s
                    AND f.revt > 0 AND f.at > 0 AND f.ceq > 0 AND f.lct > 0 AND f.dltt + f.lct > 0
                    GROUP BY fyear
                    ORDER BY fyear
                """
                
                industry_df = conn.raw_sql(
                    industry_query,
                    params=(industry_sic, start_year, end_year)
                )
                
                industry_df.columns = [
                    "Year", "Industry Net Margin", "Industry Asset Turnover",
                    "Industry Equity Multiplier", "Industry ROE", "Industry Z-Score"
                ]
                
                industry_df["Year"] = industry_df["Year"].astype(int)
                industry_df = industry_df.round(4)
                
                df = pd.merge(df, industry_df, on="Year", how="left")
            
            company_name = df.iloc[-1]["Company"]
            latest = df.iloc[-1]
            
            st.subheader(f"🏢 {company_name} Advanced Analysis")
            st.markdown(f"**SIC Industry: {industry_sic if industry_sic else 'N/A'}**")
            st.divider()
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📊 DuPont Analysis (ROE Decomposition) vs Industry Benchmark")
            st.markdown("**ROE = Net Margin × Asset Turnover × Equity Multiplier**")
            
            dupont_cols = ["Year", "Net Margin", "Asset Turnover", "Equity Multiplier", "ROE"]
            if not industry_df.empty:
                dupont_cols += ["Industry Net Margin", "Industry Asset Turnover", "Industry Equity Multiplier", "Industry ROE"]
            
            dupont_df = df[dupont_cols].melt(
                id_vars="Year", var_name="Component", value_name="Value"
            )
            
            fig = px.line(
                dupont_df, x="Year", y="Value", color="Component",
                title="DuPont Analysis Components Trend vs Industry Average",
                markers=True,
                template="plotly_white",
                color_discrete_sequence=["#165DFF", "#36CFC9", "#722ED1", "#F5222D", "#FF7D00", "#FFC107", "#20B2AA", "#8B008B"]
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"**Latest Year ({int(latest['Year'])}) DuPont Breakdown:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Net Margin", f"{latest['Net Margin']:.2f}%")
                if "Industry Net Margin" in latest and pd.notna(latest["Industry Net Margin"]):
                    st.caption(f"Industry Avg: {latest['Industry Net Margin']:.2f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Asset Turnover", f"{latest['Asset Turnover']:.2f}x")
                if "Industry Asset Turnover" in latest and pd.notna(latest["Industry Asset Turnover"]):
                    st.caption(f"Industry Avg: {latest['Industry Asset Turnover']:.2f}x")
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Equity Multiplier", f"{latest['Equity Multiplier']:.2f}x")
                if "Industry Equity Multiplier" in latest and pd.notna(latest["Industry Equity Multiplier"]):
                    st.caption(f"Industry Avg: {latest['Industry Equity Multiplier']:.2f}x")
                st.markdown('</div>', unsafe_allow_html=True)
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("ROE", f"{latest['ROE']:.2f}%")
                if "Industry ROE" in latest and pd.notna(latest["Industry ROE"]):
                    st.caption(f"Industry Avg: {latest['Industry ROE']:.2f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("⚠️ Altman Z-Score Financial Health Assessment vs Industry Benchmark")
            st.markdown("""
            **Z-Score Interpretation:**
            - ✅ Z > 2.99: Safe Zone (Low bankruptcy risk)
            - ⚠️ 1.81 < Z < 2.99: Grey Zone (Moderate risk)
            - ❌ Z < 1.81: Distress Zone (High bankruptcy risk)
            """)
            
            zscore_cols = ["Year", "Z-Score"]
            if not industry_df.empty and "Industry Z-Score" in df.columns:
                zscore_cols.append("Industry Z-Score")
            
            zscore_df = df[zscore_cols].melt(
                id_vars="Year", var_name="Type", value_name="Value"
            )
            
            fig = px.line(
                zscore_df, x="Year", y="Value", color="Type",
                title=f"{company_name} Altman Z-Score vs Industry Average",
                markers=True,
                template="plotly_white",
                color_discrete_map={"Z-Score": "#165DFF", "Industry Z-Score": "#FF7D00"}
            )
            
            fig.add_hline(y=2.99, line_dash="dash", line_color="green", annotation_text="Safe Zone")
            fig.add_hline(y=1.81, line_dash="dash", line_color="red", annotation_text="Distress Zone")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            latest_z = latest["Z-Score"]
            industry_z = latest["Industry Z-Score"] if "Industry Z-Score" in latest and pd.notna(latest["Industry Z-Score"]) else "N/A"
            if latest_z > 2.99:
                st.success(f"✅ Current Z-Score: {latest_z:.2f} - Safe Zone | Industry Avg: {industry_z}")
            elif latest_z > 1.81:
                st.warning(f"⚠️ Current Z-Score: {latest_z:.2f} - Grey Zone | Industry Avg: {industry_z}")
            else:
                st.error(f"❌ Current Z-Score: {latest_z:.2f} - Distress Zone | Industry Avg: {industry_z}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📈 Revenue Forecast (Next 3 Years)")
            
            if len(df) >= 5:
                X = df["Year"].values.reshape(-1, 1)
                y = df["revt"].values
                
                slope, intercept, r_value, p_value, std_err = stats.linregress(X.flatten(), y)
                
                future_years = pd.DataFrame({"Year": [end_year+1, end_year+2, end_year+3]})
                future_years["Revenue"] = slope * future_years["Year"] + intercept
                
                forecast_df = pd.concat([
                    df[["Year", "revt"]].rename(columns={"revt": "Revenue"}).assign(Type="Historical"),
                    future_years.assign(Type="Forecast")
                ])
                
                fig = px.line(
                    forecast_df, x="Year", y="Revenue", color="Type",
                    title=f"{company_name} Revenue Forecast (Linear Regression)",
                    markers=True,
                    template="plotly_white",
                    color_discrete_map={"Historical": "#165DFF", "Forecast": "#FF7D00"}
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"Forecast based on linear regression (R² = {r_value**2:.2f})")
            else:
                st.warning("⚠️ Not enough data for forecasting. Please select a longer year range (at least 5 years).")
            
            st.download_button(
                label="📥 Export Advanced Analysis Data as CSV",
                data=df.to_csv(index=False),
                file_name=f"{company_name.replace(' ', '_')}_Advanced_Analysis_with_Industry.csv",
                mime="text/csv"
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error("❌ Advanced Analysis Failed")
            st.code(f"Error: {str(e)}", language="text")
            st.info("This may be due to missing data for some years. Try adjusting the year range.")

st.divider()
st.markdown("© 2026 WRDS Financial Explorer | Data Source: WRDS Compustat Database | Version 1.0.0")
