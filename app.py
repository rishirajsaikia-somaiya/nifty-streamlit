import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import io

# =========================================================================
# 1. PAGE CONFIGURATION
# =========================================================================
st.set_page_config(page_title="Live Nifty Screener", layout="wide")
st.title("📈 Live Nifty Technical Screener")

# =========================================================================
# 2. TICKER LISTS
# =========================================================================
NIFTY_100_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", 
    "SBIN.NS", "INFY.NS", "LT.NS", "ITC.NS", "HINDUNILVR.NS", 
    "AXISBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "KOTAKBANK.NS", "HCLTECH.NS", 
    "TATAMOTORS.NS", "SUNPHARMA.NS", "ONGC.NS", "NTPC.NS", "M&M.NS", 
    "POWERGRID.NS", "TITAN.NS", "ULTRACEMCO.NS", "COALINDIA.NS", "BAJAJFINSV.NS", 
    "ADANIPORTS.NS", "TATASTEEL.NS", "ASIANPAINT.NS", "WIPRO.NS", "NESTLEIND.NS", 
    "BAJAJ-AUTO.NS", "LTIM.NS", "GRASIM.NS", "TECHM.NS", "HINDALCO.NS", 
    "ADANIENT.NS", "INDIGO.NS", "EICHERMOT.NS", "DRREDDY.NS", "TRENT.NS", 
    "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "BRITANNIA.NS", "SHRIRAMFIN.NS", 
    "HEROMOTOCO.NS", "TATACONSUM.NS", "BPCL.NS", "HDFCLIFE.NS", "SBILIFE.NS",
    "HAL.NS", "ZOMATO.NS", "JIOFIN.NS", "SIEMENS.NS", "DLF.NS", 
    "VBL.NS", "GODREJCP.NS", "PIDILITIND.NS", "ADANIGREEN.NS", "ADANIPOWER.NS", 
    "TATAPOWER.NS", "AMBUJACEM.NS", "CHOLAFIN.NS", "LODHA.NS", "IOC.NS", 
    "BANKBARODA.NS", "HAVELLS.NS", "TVSMOTOR.NS", "GAIL.NS", "BOSCHLTD.NS", 
    "BEL.NS", "PNB.NS", "CANBK.NS", "RECLTD.NS", "PFC.NS", 
    "POLYCAB.NS", "ABB.NS", "ICICIGI.NS", "TIINDIA.NS", "CUMMINSIND.NS", 
    "TORNTPHARM.NS", "SRF.NS", "ATGL.NS", "MAXHEALTH.NS", "MUTHOOTFIN.NS", 
    "ZYDUSLIFE.NS", "ICICIPRULI.NS", "ALKEM.NS", "INDIANB.NS", "YESBANK.NS", 
    "IDFCFIRSTB.NS", "CGPOWER.NS", "APLAPOLLO.NS", "UPL.NS", "MARICO.NS", 
    "DABUR.NS", "TATACOMM.NS", "COLPAL.NS", "PGHH.NS", "BERGEPAINT.NS"
]

NIFTY_MIDCAP_100_TICKERS = [
    "LUPIN.NS", "AUBANK.NS", "IDEA.NS", "NMDC.NS", "SAIL.NS", 
    "OBEROIRLTY.NS", "COROMANDEL.NS", "PRESTIGE.NS", "SUZLON.NS", "PAYTM.NS", 
    "DIXON.NS", "MRF.NS", "LINDEINDIA.NS", "PETRONET.NS", "KPITTECH.NS", 
    "PERSISTENT.NS", "COFORGE.NS", "CONCOR.NS", "ASTRAL.NS", "MFSL.NS", 
    "PAGEIND.NS", "VOLTAS.NS", "MPHASIS.NS", "JUBLFOOD.NS", "UBL.NS", 
    "IGL.NS", "GMRINFRA.NS", "BIOCON.NS", "AIAENG.NS", "LICHSGFIN.NS", 
    "BANDHANBNK.NS", "BANKINDIA.NS", "UNIONBANK.NS", "POONAWALLA.NS", "STARHEALTH.NS", 
    "M&MFIN.NS", "GLENMARK.NS", "TORNTPOWER.NS", "MINDSPACE.NS", "FEDERALBNK.NS", 
    "GICRE.NS", "SONACOMS.NS", "BALKRISIND.NS", "NIACL.NS", "CRISIL.NS", 
    "TATAELXSI.NS", "HONAUT.NS", "PBFINTECH.NS", "ABBOTINDIA.NS", "SUPREMEIND.NS", 
    "BSE.NS", "MCX.NS", "IRFC.NS", "RVNL.NS", "IRCTC.NS", 
    "MAZDOCK.NS", "COCHINSHIP.NS", "FACT.NS", "NHPC.NS", "SJVN.NS", 
    "TATACHEM.NS", "DEEPAKNTR.NS", "GUJGASLTD.NS", "AARTIIND.NS", "NAVINFLUOR.NS", 
    "SYNGENE.NS", "LAURUSLABS.NS", "IPCALAB.NS", "FORTIS.NS", "LALPATHLAB.NS", 
    "DEVYANI.NS", "ABFRL.NS", "ZEEL.NS", "SUNTV.NS", "BATAINDIA.NS", 
    "RELAXO.NS", "KPRMILL.NS", "TRIDENT.NS", "WELSPUNLIV.NS", "RADICO.NS", 
    "ESCORTS.NS", "ASHOKLEY.NS", "ENDURANCE.NS", "UNOMINDA.NS", "EXIDEIND.NS", 
    "KALYANKJIL.NS", "APOLLOTYRE.NS", "CEATLTD.NS", "RAMCOCEM.NS", "DALBHARAT.NS", 
    "JKCEMENT.NS", "INDIACEM.NS", "GODREJPROP.NS", "PHOENIXLTD.NS", "BRIGADE.NS", 
    "NBCC.NS", "HUDCO.NS", "JINDALSTEL.NS", "NATIONALUM.NS", "HINDCOPPER.NS"
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
    df['Ichimoku_Tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['Ichimoku_Kijun_sen'] = (high_26 + low_26) / 2

    df['Ichimoku_Senkou_Span_A'] = ((df['Ichimoku_Tenkan_sen'] + df['Ichimoku_Kijun_sen']) / 2).shift(26)

    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['Ichimoku_Senkou_Span_B'] = ((high_52 + low_52) / 2).shift(26)

    df['Ichimoku_Chikou_Span'] = df['Close'].shift(-26)

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
        final_combined_df = final_combined_df.reset_index()
        final_combined_df = final_combined_df.sort_values(by=['Date', 'Ticker'], ascending=[False, True])
        final_combined_df = final_combined_df.set_index('Date')
        cols = ['Ticker'] + [col for col in final_combined_df.columns if col != 'Ticker']
        return final_combined_df[cols]
    else:
        return pd.DataFrame()

# TTL=3600 means this function will only hit Yahoo Finance once per hour.
# For the rest of the hour, it instantly serves the dataframe from memory!
@st.cache_data(ttl=3600, show_spinner=False)
def load_all_market_data():
    n100 = fetch_and_process_group(NIFTY_100_TICKERS)
    n200 = fetch_and_process_group(NIFTY_200_TICKERS)
    return n100, n200

# =====================================================================
# 5. UI: FETCH DATA BUTTON
# =====================================================================
# This creates a friendly user experience, showing a loading bar 
# while the server fetches the 200 stocks in the background.
with st.spinner("Connecting to live market data... (This takes about 45-60 seconds on the first run)"):
    df_100, df_200 = load_all_market_data()

if df_100.empty or df_200.empty:
    st.error("Failed to fetch live data from Yahoo Finance. Please try again later.")
    st.stop()

# =====================================================================
# 6. TOP PANEL: OVERVIEW METRICS
# =====================================================================
selected_index = st.radio("Select Index to Screen", ["Nifty 100", "Nifty 200"], horizontal=True)
df = df_100 if selected_index == "Nifty 100" else df_200

latest_date = df.index.max()
# Isolate just the rows matching the most recent trading day
current_data = df[df.index == latest_date]

st.markdown(f"### Index Overview (As of {pd.to_datetime(latest_date).strftime('%Y-%m-%d')})")
col1, col2, col3 = st.columns(3)
col1.metric("Total Stocks Tracked", len(current_data['Ticker'].unique()))
col2.metric("Average RSI", round(current_data['RSI_14'].mean(), 2))
col3.metric("Stocks Above SMA (14)", len(current_data[current_data['Close'] > current_data['SMA_14']]))

st.divider()

# =====================================================================
# 7. SIDEBAR: SCREENER CONTROLS
# =====================================================================
st.sidebar.header("Filter Criteria")

min_rsi, max_rsi = st.sidebar.slider(
    "RSI (14) Range", 
    min_value=0.0, max_value=100.0, value=(30.0, 70.0)
)

macd_status = st.sidebar.selectbox(
    "MACD Signal", 
    ["All", "Bullish (MACD > Signal)", "Bearish (MACD < Signal)"]
)

# =====================================================================
# 8. FILTERING LOGIC
# =====================================================================
filtered_data = current_data[
    (current_data['RSI_14'] >= min_rsi) & 
    (current_data['RSI_14'] <= max_rsi)
]

if macd_status == "Bullish (MACD > Signal)":
    filtered_data = filtered_data[filtered_data['MACD'] > filtered_data['MACD_Signal']]
elif macd_status == "Bearish (MACD < Signal)":
    filtered_data = filtered_data[filtered_data['MACD'] < filtered_data['MACD_Signal']]

# =====================================================================
# 9. MAIN VIEW: DISPLAY RESULTS
# =====================================================================
st.markdown(f"### Screened Results")
st.write(f"Showing **{len(filtered_data)}** stocks matching your criteria.")

# Display clean dataframe to the user
display_cols = ['Ticker', 'Close', 'SMA_14', 'RSI_14', 'MACD', 'MACD_Signal']
display_df = filtered_data[display_cols].copy()

# Round numbers purely for visual display
display_df['Close'] = display_df['Close'].round(2)
display_df['SMA_14'] = display_df['SMA_14'].round(2)
display_df['RSI_14'] = display_df['RSI_14'].round(2)
display_df['MACD'] = display_df['MACD'].round(2)
display_df['MACD_Signal'] = display_df['MACD_Signal'].round(2)

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()

# =====================================================================
# 10. EXPORT FEATURE: IN-MEMORY DOWNLOAD (NO LOCAL FILES!)
# =====================================================================
st.markdown("### Export Data")

if not filtered_data.empty:
    buffer = io.BytesIO()
    
    # We reset the index here so the exact Date is pushed into a normal column for Excel
    export_df = filtered_data.reset_index()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Screened Stocks')

    file_name_date = pd.to_datetime(latest_date).strftime('%Y-%m-%d')
    st.download_button(
        label="📥 Download Screened Stocks as Excel",
        data=buffer.getvalue(),
        file_name=f"Screened_{selected_index.replace(' ', '_')}_{file_name_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No stocks match your current filters. Adjust the sliders to download data.")
