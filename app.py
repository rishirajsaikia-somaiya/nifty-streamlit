import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import io

# =========================================================================
# 1. PAGE CONFIGURATION & SESSION STATE
# =========================================================================
st.set_page_config(page_title="Live Nifty Screener", layout="wide")
st.title("📈 Live Nifty Technical Screener")

# Initialize session state so the app doesn't fetch data until requested
if 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = False

# =========================================================================
# 2. TICKER LISTS
# =========================================================================
NIFTY_100_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", 
    "SBIN.NS", "INFY.NS", "LT.NS", "ITC.NS", "HINDUNILVR.NS", "AXISBANK.NS", 
    "BAJFINANCE.NS", "MARUTI.NS", "KOTAKBANK.NS", "HCLTECH.NS", "TATAMOTORS.NS", 
    "SUNPHARMA.NS", "ONGC.NS", "NTPC.NS", "M&M.NS", "POWERGRID.NS", "TITAN.NS", 
    "ULTRACEMCO.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "ADANIPORTS.NS", 
    "TATASTEEL.NS", "ASIANPAINT.NS", "WIPRO.NS", "NESTLEIND.NS", "BAJAJ-AUTO.NS", 
    "LTIM.NS", "GRASIM.NS", "TECHM.NS", "HINDALCO.NS", "ADANIENT.NS", "INDIGO.NS", 
    "EICHERMOT.NS", "DRREDDY.NS", "TRENT.NS", "CIPLA.NS", "DIVISLAB.NS", 
    "APOLLOHOSP.NS", "BRITANNIA.NS", "SHRIRAMFIN.NS", "HEROMOTOCO.NS", 
    "TATACONSUM.NS", "BPCL.NS", "HDFCLIFE.NS", "SBILIFE.NS", "HAL.NS", "ZOMATO.NS", 
    "JIOFIN.NS", "SIEMENS.NS", "DLF.NS", "VBL.NS", "GODREJCP.NS", "PIDILITIND.NS", 
    "ADANIGREEN.NS", "ADANIPOWER.NS", "TATAPOWER.NS", "AMBUJACEM.NS", "CHOLAFIN.NS", 
    "LODHA.NS", "IOC.NS", "BANKBARODA.NS", "HAVELLS.NS", "TVSMOTOR.NS", "GAIL.NS", 
    "BOSCHLTD.NS", "BEL.NS", "PNB.NS", "CANBK.NS", "RECLTD.NS", "PFC.NS", 
    "POLYCAB.NS", "ABB.NS", "ICICIGI.NS", "TIINDIA.NS", "CUMMINSIND.NS", 
    "TORNTPHARM.NS", "SRF.NS", "ATGL.NS", "MAXHEALTH.NS", "MUTHOOTFIN.NS", 
    "ZYDUSLIFE.NS", "ICICIPRULI.NS", "ALKEM.NS", "INDIANB.NS", "YESBANK.NS", 
    "IDFCFIRSTB.NS", "CGPOWER.NS", "APLAPOLLO.NS", "UPL.NS", "MARICO.NS", 
    "DABUR.NS", "TATACOMM.NS", "COLPAL.NS", "PGHH.NS", "BERGEPAINT.NS"
]

NIFTY_MIDCAP_100_TICKERS = [
    "LUPIN.NS", "AUBANK.NS", "IDEA.NS", "NMDC.NS", "SAIL.NS", "OBEROIRLTY.NS", 
    "COROMANDEL.NS", "PRESTIGE.NS", "SUZLON.NS", "PAYTM.NS", "DIXON.NS", "MRF.NS", 
    "LINDEINDIA.NS", "PETRONET.NS", "KPITTECH.NS", "PERSISTENT.NS", "COFORGE.NS", 
    "CONCOR.NS", "ASTRAL.NS", "MFSL.NS", "PAGEIND.NS", "VOLTAS.NS", "MPHASIS.NS", 
    "JUBLFOOD.NS", "UBL.NS", "IGL.NS", "GMRINFRA.NS", "BIOCON.NS", "AIAENG.NS", 
    "LICHSGFIN.NS", "BANDHANBNK.NS", "BANKINDIA.NS", "UNIONBANK.NS", "POONAWALLA.NS", 
    "STARHEALTH.NS", "M&MFIN.NS", "GLENMARK.NS", "TORNTPOWER.NS", "MINDSPACE.NS", 
    "FEDERALBNK.NS", "GICRE.NS", "SONACOMS.NS", "BALKRISIND.NS", "NIACL.NS", 
    "CRISIL.NS", "TATAELXSI.NS", "HONAUT.NS", "PBFINTECH.NS", "ABBOTINDIA.NS", 
    "SUPREMEIND.NS", "BSE.NS", "MCX.NS", "IRFC.NS", "RVNL.NS", "IRCTC.NS", 
    "MAZDOCK.NS", "COCHINSHIP.NS", "FACT.NS", "NHPC.NS", "SJVN.NS", "TATACHEM.NS", 
    "DEEPAKNTR.NS", "GUJGASLTD.NS", "AARTIIND.NS", "NAVINFLUOR.NS", "SYNGENE.NS", 
    "LAURUSLABS.NS", "IPCALAB.NS", "FORTIS.NS", "LALPATHLAB.NS", "DEVYANI.NS", 
    "ABFRL.NS", "ZEEL.NS", "SUNTV.NS", "BATAINDIA.NS", "RELAXO.NS", "KPRMILL.NS", 
    "TRIDENT.NS", "WELSPUNLIV.NS", "RADICO.NS", "ESCORTS.NS", "ASHOKLEY.NS", 
    "ENDURANCE.NS", "UNOMINDA.NS", "EXIDEIND.NS", "KALYANKJIL.NS", "APOLLOTYRE.NS", 
    "CEATLTD.NS", "RAMCOCEM.NS", "DALBHARAT.NS", "JKCEMENT.NS", "INDIACEM.NS", 
    "GODREJPROP.NS", "PHOENIXLTD.NS", "BRIGADE.NS", "NBCC.NS", "HUDCO.NS", 
    "JINDALSTEL.NS", "NATIONALUM.NS", "HINDCOPPER.NS"
]

NIFTY_200_TICKERS = NIFTY_100_TICKERS + NIFTY_MIDCAP_100_TICKERS

# =========================================================================
# 3. TECHNICAL INDICATOR ENGINE
# =========================================================================
def calculate_indicators(df):
    df = df.copy()
    
    df['SMA_14'] = df['Close'].rolling(window=14).mean()
    df['EMA_14'] = df['Close'].ewm(span=14, adjust=False).mean()

    ema1 = df['Close'].ewm(span=14, adjust=False).mean()
    ema2 = ema1.ewm(span=14, adjust=False).mean()
    df['DEMA_14'] = (2 * ema1) - ema2

    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    lowest_low = df['Low'].rolling(window=14).min()
    highest_high = df['High'].rolling(window=14).max()
    df['Stoch_%K'] = ((df['Close'] - lowest_low) / (highest_high - lowest_low)) * 100
    df['Stoch_%D'] = df['Stoch_%K'].rolling(window=3).mean()

    tp = (df['High'] + df['Low'] + df['Close']) / 3
    sma_tp = tp.rolling(window=20).mean()
    mad = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    df['CCI_20'] = (tp - sma_tp) / (0.015 * mad)

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    raw_money_flow = tp * df['Volume']
    flow_direction = tp.diff()
    positive_flow = raw_money_flow.where(flow_direction > 0, 0.0)
    negative_flow = raw_money_flow.where(flow_direction < 0, 0.0)
    pos_flow_sum = positive_flow.rolling(window=14).sum()
    neg_flow_sum = negative_flow.rolling(window=14).sum()
    money_ratio = pos_flow_sum / neg_flow_sum
    df['MFI_14'] = 100 - (100 / (1 + money_ratio))

    hh_14 = df['High'].rolling(window=14).max()
    ll_14 = df['Low'].rolling(window=14).min()
    df['Williams_%R'] = ((hh_14 - df['Close']) / (hh_14 - ll_14)) * -100

    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['Ichimoku_Tenkan'] = (high_9 + low_9) / 2

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['Ichimoku_Kijun'] = (high_26 + low_26) / 2

    df['Ichimoku_Span_A'] = ((df['Ichimoku_Tenkan'] + df['Ichimoku_Kijun']) / 2).shift(26)

    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['Ichimoku_Span_B'] = ((high_52 + low_52) / 2).shift(26)

    high, low, close = df['High'].values, df['Low'].values, df['Close'].values
    psar = np.zeros(len(df))
    af = np.zeros(len(df)) 
    ep = np.zeros(len(df)) 
    trend = np.zeros(len(df)) 

    af_step = 0.02
    af_max = 0.20
    
    if len(df) > 1:
        trend[1] = 1 if close[1] > close[0] else -1
        psar[1] = low[0] if trend[1] == 1 else high[0]
        ep[1] = high[1] if trend[1] == 1 else low[1]
        af[1] = af_step

        for i in range(2, len(df)):
            psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])
            if trend[i-1] == 1 and low[i] < psar[i]:
                trend[i] = -1
                psar[i] = ep[i-1]
                ep[i] = low[i]
                af[i] = af_step
            elif trend[i-1] == -1 and high[i] > psar[i]:
                trend[i] = 1
                psar[i] = ep[i-1]
                ep[i] = high[i]
                af[i] = af_step
            else:
                trend[i] = trend[i-1]
                ep[i] = ep[i-1]
                af[i] = af[i-1]
                if trend[i] == 1:
                    if high[i] > ep[i]:
                        ep[i] = high[i]
                        af[i] = min(af[i] + af_step, af_max)
                    psar[i] = min(psar[i], low[i-1], low[i-2])
                else:
                    if low[i] < ep[i]:
                        ep[i] = low[i]
                        af[i] = min(af[i] + af_step, af_max)
                    psar[i] = max(psar[i], high[i-1], high[i-2])
    df['PSAR'] = psar
    return df

# =========================================================================
# 4. LIVE DATA FETCHING & CACHING (In-Memory)
# =========================================================================
def fetch_and_process_group(tickers_list):
    if not tickers_list:
        return pd.DataFrame()
        
    data = yf.download(tickers_list, start="2021-01-01", group_by='ticker', progress=False)
    processed_dfs = []
    
    if isinstance(data.columns, pd.MultiIndex):
        valid_tickers = data.columns.get_level_values(0).unique()
        for ticker in valid_tickers:
            ticker_df = data[ticker].copy()
            ticker_df.dropna(how='all', inplace=True) 
            if not ticker_df.empty and len(ticker_df) > 50: 
                try:
                    ticker_df = calculate_indicators(ticker_df)
                    ticker_df['Ticker'] = ticker
                    processed_dfs.append(ticker_df)
                except Exception:
                    pass
    else:
        if not data.empty:
            df = calculate_indicators(data)
            df['Ticker'] = tickers_list[0]
            processed_dfs.append(df)

    if processed_dfs:
        final_combined_df = pd.concat(processed_dfs)
        final_combined_df.index.name = 'Date'
        # Drop rows with NaN (like the first 52 days for Ichimoku)
        final_combined_df.dropna(subset=['Ichimoku_Span_B', 'SMA_14'], inplace=True)
        return final_combined_df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_all_market_data():
    n100 = fetch_and_process_group(NIFTY_100_TICKERS)
    n200 = fetch_and_process_group(NIFTY_200_TICKERS)
    return n100, n200

# =====================================================================
# 5. UI: EXPLICIT FETCH BUTTON
# =====================================================================
if not st.session_state.data_fetched:
    st.info("👋 Welcome to the Nifty Technical Screener. Click the button below to pull the latest data from Yahoo Finance.")
    if st.button("🚀 Fetch Live Market Data (Takes ~45 seconds)", use_container_width=True):
        st.session_state.data_fetched = True
        st.rerun()  # Forces the page to reload and bypass this block
    st.stop()  # Stops the rest of the page from rendering until button is clicked

# If we made it here, data_fetched is True. Let's load the data.
with st.spinner("Processing technical indicators..."):
    df_100, df_200 = load_all_market_data()

if df_100.empty or df_200.empty:
    st.error("Failed to fetch live data from Yahoo Finance. Please try again later.")
    st.stop()

# =====================================================================
# 6. TOP PANEL: OVERVIEW METRICS & INDEX SELECTION
# =====================================================================
selected_index = st.radio("Select Index to Screen", ["Nifty 100", "Nifty 200"], horizontal=True)
df = df_100 if selected_index == "Nifty 100" else df_200

# Reset index so 'Date' is a column we can filter easily
df = df.reset_index()
# Convert datetime to date for easier filtering
df['Date'] = pd.to_datetime(df['Date']).dt.date

min_available_date = df['Date'].min()
max_available_date = df['Date'].max()

st.divider()

# =====================================================================
# 7. SIDEBAR: SCREENER CONTROLS
# =====================================================================
st.sidebar.header("🗓️ Timeframe")

# User can pick a single date OR a range
selected_dates = st.sidebar.date_input(
    "Select Date or Date Range",
    value=(max_available_date, max_available_date),
    min_value=min_available_date,
    max_value=max_available_date
)

# Handle the tuple return of date_input
if len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates[0]
    end_date = selected_dates[0]

st.sidebar.divider()
st.sidebar.header("🎛️ Filter Criteria")

# --- OSCILLATORS (Grouped in an expander) ---
with st.sidebar.expander("Momentum & Oscillators", expanded=True):
    min_rsi, max_rsi = st.slider("RSI (14)", 0.0, 100.0, (0.0, 100.0))
    min_mfi, max_mfi = st.slider("Money Flow Index (14)", 0.0, 100.0, (0.0, 100.0))
    min_cci, max_cci = st.slider("CCI (20)", -300.0, 300.0, (-300.0, 300.0))
    min_will, max_will = st.slider("Williams %R", -100.0, 0.0, (-100.0, 0.0))

# --- TREND INDICATORS (Grouped in an expander) ---
with st.sidebar.expander("Trend & Moving Averages", expanded=False):
    macd_status = st.selectbox("MACD Signal", ["All", "Bullish (MACD > Signal)", "Bearish (MACD < Signal)"])
    sma_status = st.selectbox("Price vs SMA (14)", ["All", "Above SMA", "Below SMA"])
    psar_status = st.selectbox("Parabolic SAR", ["All", "Bullish (Price > PSAR)", "Bearish (Price < PSAR)"])
    ichimoku_status = st.selectbox("Ichimoku Cloud", ["All", "Price Above Cloud", "Price Below Cloud", "Price Inside Cloud"])

# =====================================================================
# 8. APPLYING THE FILTERS
# =====================================================================
# 1. Filter by Date Range
filtered_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()

# 2. Filter by Oscillators
filtered_data = filtered_data[
    (filtered_data['RSI_14'] >= min_rsi) & (filtered_data['RSI_14'] <= max_rsi) &
    (filtered_data['MFI_14'] >= min_mfi) & (filtered_data['MFI_14'] <= max_mfi) &
    (filtered_data['CCI_20'] >= min_cci) & (filtered_data['CCI_20'] <= max_cci) &
    (filtered_data['Williams_%R'] >= min_will) & (filtered_data['Williams_%R'] <= max_will)
]

# 3. Filter by Trend
if macd_status == "Bullish (MACD > Signal)":
    filtered_data = filtered_data[filtered_data['MACD'] > filtered_data['MACD_Signal']]
elif macd_status == "Bearish (MACD < Signal)":
    filtered_data = filtered_data[filtered_data['MACD'] < filtered_data['MACD_Signal']]

if sma_status == "Above SMA":
    filtered_data = filtered_data[filtered_data['Close'] > filtered_data['SMA_14']]
elif sma_status == "Below SMA":
    filtered_data = filtered_data[filtered_data['Close'] < filtered_data['SMA_14']]

if psar_status == "Bullish (Price > PSAR)":
    filtered_data = filtered_data[filtered_data['Close'] > filtered_data['PSAR']]
elif psar_status == "Bearish (Price < PSAR)":
    filtered_data = filtered_data[filtered_data['Close'] < filtered_data['PSAR']]

if ichimoku_status == "Price Above Cloud":
    filtered_data = filtered_data[(filtered_data['Close'] > filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] > filtered_data['Ichimoku_Span_B'])]
elif ichimoku_status == "Price Below Cloud":
    filtered_data = filtered_data[(filtered_data['Close'] < filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] < filtered_data['Ichimoku_Span_B'])]
elif ichimoku_status == "Price Inside Cloud":
    # Inside cloud means it's between Span A and Span B
    condition_1 = (filtered_data['Close'] <= filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] >= filtered_data['Ichimoku_Span_B'])
    condition_2 = (filtered_data['Close'] >= filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] <= filtered_data['Ichimoku_Span_B'])
    filtered_data = filtered_data[condition_1 | condition_2]

# =====================================================================
# 9. MAIN VIEW: DISPLAY RESULTS
# =====================================================================
# Header changes based on if it's a single day or a range
if start_date == end_date:
    st.markdown(f"### Screened Results for **{start_date}**")
else:
    st.markdown(f"### Screened Results from **{start_date}** to **{end_date}**")

st.write(f"Showing **{len(filtered_data)}** rows matching your criteria.")

if not filtered_data.empty:
    # Sort by Date (newest first) then Ticker
    filtered_data = filtered_data.sort_values(by=['Date', 'Ticker'], ascending=[False, True])

    # Select columns to display
    display_cols = ['Date', 'Ticker', 'Close', 'RSI_14', 'MFI_14', 'CCI_20', 'MACD', 'MACD_Signal', 'SMA_14', 'PSAR']
    display_df = filtered_data[display_cols].copy()

    # Round all numerical columns for cleaner display
    for col in display_df.select_dtypes(include=['float64']).columns:
        display_df[col] = display_df[col].round(2)

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.warning("No stocks match the current filter criteria for the selected timeframe.")

st.divider()

# =====================================================================
# 10. EXPORT FEATURE
# =====================================================================
st.markdown("### Export Data")

if not filtered_data.empty:
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Exporting ALL indicators (not just the summary display columns)
        filtered_data.to_excel(writer, index=False, sheet_name='Screened Stocks')

    file_name_tag = f"{start_date}" if start_date == end_date else f"{start_date}_to_{end_date}"
    
    st.download_button(
        label="📥 Download Screened Stocks as Excel",
        data=buffer.getvalue(),
        file_name=f"Screened_{selected_index.replace(' ', '_')}_{file_name_tag}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
