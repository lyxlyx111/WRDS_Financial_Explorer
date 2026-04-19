import streamlit as st
import wrds
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="WRDS Financial Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for both light and dark mode
st.markdown("""
<style>
    .main {
        background-color: var(--background-color);
    }
    .stButton>button {
        background-color: #165DFF;
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: 500;
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
st.title("📊 WRDS Financial Explorer")
st.markdown("### Corporate Financial Intelligence Platform")
st.markdown("**Built for: Financial Analysts, Business Students, Institutional Investors**")
st.markdown("**Powered by: WRDS Compustat Live Data**")

session_defaults = {
    "wrds_conn": None,
    "is_authenticated": False,
    "username": None
}

for key, val in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.divider()

if st.session_state["is_authenticated"] and st.session_state["wrds_conn"]:
    st.success(f"✅ WRDS Connected | User: {st.session_state['username']} | Live Data Active")
    st.divider()
    
    st.markdown("## 🚀 Quick Access")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📊 Financial Dashboard")
        st.markdown("View 20+ core financial indicators for any company")
        if st.button("Go to Dashboard", use_container_width=True):
            st.switch_page("pages/1_Financial_Dashboard.py")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🔄 Multi-Company Comparison")
        st.markdown("Compare up to 5 companies side by side")
        if st.button("Go to Comparison", use_container_width=True):
            st.switch_page("pages/2_Multi_Company_Comparison.py")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🔬 Advanced Analysis")
        st.markdown("DuPont analysis, Z-score, and forecasting")
        if st.button("Go to Advanced Analysis", use_container_width=True):
            st.switch_page("pages/3_Advanced_Analysis.py")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔌 Disconnect WRDS", use_container_width=True):
        for key in session_defaults:
            st.session_state[key] = None
        st.rerun()

else:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🔐 WRDS Authentication")
    st.info("This tool requires a valid WRDS account to access real financial data from Compustat database.")
    
    username = st.text_input("WRDS Username", placeholder="Enter your WRDS ID")
    password = st.text_input("WRDS Password", type="password", placeholder="Enter your WRDS Password")
    
    if st.button("🔐 Connect to WRDS", use_container_width=True, type="primary"):
        if not username or not password:
            st.error("❌ Username and Password cannot be empty")
            st.stop()
        
        with st.spinner("Establishing secure WRDS connection..."):
            try:
                conn = wrds.Connection(
                    wrds_username=username,
                    wrds_password=password,
                    timeout=30
                )
                
                st.session_state["wrds_conn"] = conn
                st.session_state["username"] = username
                st.session_state["is_authenticated"] = True
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ WRDS Connection Failed")
                st.code(f"Error: {str(e)}", language="text")
                st.info("Please check your credentials and ensure you have access to WRDS Compustat database.")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.markdown("© 2026 WRDS Financial Explorer | Data Source: WRDS Compustat Database | Version 1.0.0")