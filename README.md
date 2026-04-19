# WRDS Financial Explorer
**ACC102 Mini Assignment - Track 4 (Interactive Data Analysis Tool)**

---

## 1. Problem & User
People often struggle with the acquisition of reliable financial data. For instance, manually obtaining data from WRDS takes too much time, and manually calculating multiple financial indicators is prone to errors.

This product aims to solve such problems. It is an interactive financial data query and analysis platform. It can obtain real-time financial data of a company from WRDS through queries and fully automate the work of financial indicator calculation and chart analysis, thereby liberating users' hands and allowing them to focus on the judgment and insight of the data.

The target users mainly include business students, junior financial analysts, and individual investors.

---

## 2. Data
- **Source**: WRDS Compustat Fundamental Annual Database
- **Access Date**: April 18, 2026
- **Coverage**: Over 90,000 public companies worldwide
- **Time Range**: 2014-2024 (11 years of standardized historical data)
- **Key Variables**: Revenue, Net Income, Total Assets, Total Equity, Current Assets, Current Liabilities, Long-term Debt, Retained Earnings, Working Capital, SIC Industry Code

---

## 3. Methods
The platform is built entirely with Python and implements a complete end-to-end analytical process:
- **Authentication**: Secure connection to WRDS database, with session management provided
- **Data Processing**: Automatically perform data cleaning, remove duplicate values, and handle missing data
- **Industry Benchmarking**: Automatic 2-digit SIC industry classification and average calculation
- **Financial Analysis**: Calculation of 14 core financial ratios, including profitability, solvency, and efficiency metrics
- **Advanced Analytics**: DuPont ROE decomposition, Altman Z-Score bankruptcy risk assessment, and linear regression revenue forecasting
- **Visualization**: Interactive charts and tables created with Plotly for dynamic data exploration
- **User Interface**: Simple and practical web interface built with Streamlit, consisting of three core modules

---

## 4. Key Features
1. **Single Company Financial Dashboard**: Comprehensive overview of 20+ financial indicators with various charts and trend analysis
2. **Multi-Company Comparison**: Automated comparison of financial data for up to five companies, with visualization via line and radar charts
3. **Advanced Analysis**: DuPont analysis, Altman Z-Score financial health assessment, and 3-year revenue forecast
4. **Data Export**: One-click export of all analysis results in CSV format
5. **Real-time Data**: Access to up-to-date financial data from WRDS
6. **Industry Benchmarking**: Obtain the latest industry benchmark data for comparison
---

## 5. How to Run
1. Clone this repository
2. Install dependencies: pip install -r requirements.txt
3. Run the application: streamlit run Home.py
4. Enter your valid WRDS username and password to authenticate
5. Start exploring financial data for any public company in the database

---

## 6. Live Demo
You can access the deployed application here:  
(https://curly-barnacle-v6x45wpxj7w6fjv7-8501.app.github.dev/)

---

## 7. Limitations & Future Improvements

### Limitations
1. Currently only supports annual financial data
2. The forecast model is based on simple linear regression
3. Only supports 2-digit SIC industry grouping

### Future Improvements
1. Add quarterly data support
2. Implement ARIMA time series forecasting
3. Integrate 4-digit SIC industry classification system
