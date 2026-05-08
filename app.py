import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from yahooquery import Ticker

# =========================================================================
# 1. PAGE CONFIGURATION & SESSION STATE
# =========================================================================
st.set_page_config(page_title="Live Nifty Screener", layout="wide")
st.title("📈 Live Nifty Technical Screener")

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
    df['DEMA_14'] = (2 * ema1) - ema1.ewm(span=14, adjust=False).mean()

    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    lowest_low = df['Low'].rolling(window=14).min()
    highest_high = df['High'].rolling(window=14).max()
    df['Stoch_%K'] = ((df['Close'] - lowest_low) / (highest_high - lowest_low).replace(0, 1e-9)) * 100
    df['Stoch_%D'] = df['Stoch_%K'].rolling(window=3).mean()

    tp = (df['High'] + df['Low'] + df['Close']) / 3
    sma_tp = tp.rolling(window=20).mean()
    mad = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    df['CCI_20'] = (tp - sma_tp) / (0.015 * mad.replace(0, 1e-9))

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, 1e-9)
    df['RSI_14'] = 100 - (100 / (1 + rs))

    raw_money_flow = tp * df['Volume']
    pos_flow = raw_money_flow.where(tp.diff() > 0, 0.0).rolling(14).sum()
    neg_flow = raw_money_flow.where(tp.diff() < 0, 0.0).rolling(14).sum()
    df['MFI_14'] = 100 - (100 / (1 + (pos_flow / neg_flow.replace(0, 1e-9))))
    df['Williams_%R'] = ((highest_high - df['Close']) / (highest_high - lowest_low).replace(0, 1e-9)) * -100

    df['Ichimoku_Tenkan'] = (df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2
    df['Ichimoku_Kijun'] = (df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2
    df['Ichimoku_Span_A'] = ((df['Ichimoku_Tenkan'] + df['Ichimoku_Kijun']) / 2).shift(26)
    df['Ichimoku_Span_B'] = ((df['High'].rolling(52).max() + df['Low'].rolling(52).min()) / 2).shift(26)
    
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['BB_Upper'] = df['SMA_20'] + (df['Close'].rolling(20).std() * 2)
    df['BB_Lower'] = df['SMA_20'] - (df['Close'].rolling(20).std() * 2)

    tr = pd.concat([df['High'] - df['Low'], np.abs(df['High'] - df['Close'].shift()), np.abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR_14'] = tr.rolling(window=14).mean()
    df['Donchian_High_20'] = df['High'].rolling(window=20).max()
    df['Donchian_Low_20'] = df['Low'].rolling(window=20).min()

    obv = np.where(df['Close'] > df['Close'].shift(1), df['Volume'], np.where(df['Close'] < df['Close'].shift(1), -df['Volume'], 0))
    df['OBV'] = pd.Series(obv, index=df.index).cumsum()
    df['MVWAP_20'] = (tp * df['Volume']).rolling(20).sum() / df['Volume'].rolling(20).sum().replace(0, 1e-9)
    df['ROC_14'] = ((df['Close'] - df['Close'].shift(14)) / df['Close'].shift(14).replace(0, 1e-9)) * 100
    df['Hist_Volatility_20'] = np.log(df['Close'] / df['Close'].shift(1).replace(0, np.nan)).rolling(20).std() * np.sqrt(252) * 100

    up_move = df['High'] - df['High'].shift(1)
    down_move = df['Low'].shift(1) - df['Low']
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_smooth = df['ATR_14'].ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * (pd.Series(plus_dm).ewm(alpha=1/14, adjust=False).mean() / atr_smooth.replace(0, 1e-9))
    minus_di = 100 * (pd.Series(minus_dm).ewm(alpha=1/14, adjust=False).mean() / atr_smooth.replace(0, 1e-9))
    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1e-9)) * 100
    df['ADX_14'] = dx.ewm(alpha=1/14, adjust=False).mean()

    aroon_up = df['High'].rolling(14).apply(np.argmax, raw=True) / 14 * 100
    aroon_down = df['Low'].rolling(14).apply(np.argmin, raw=True) / 14 * 100
    df['Aroon_Osc'] = aroon_up - aroon_down

    hl2 = (df['High'] + df['Low']) / 2
    df['Awesome_Osc'] = hl2.rolling(5).mean() - hl2.rolling(34).mean()

    mfv = df['Volume'] * ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low']).replace(0, 1e-9)
    df['CMF_20'] = mfv.rolling(20).sum() / df['Volume'].rolling(20).sum().replace(0, 1e-9)

    df['CMO_14'] = 100 * ((gain * 14) - (loss * 14)) / ((gain * 14) + (loss * 14)).replace(0, 1e-9)

    roc_14 = ((df['Close'] - df['Close'].shift(14)) / df['Close'].shift(14).replace(0, 1e-9)) * 100
    roc_11 = ((df['Close'] - df['Close'].shift(11)) / df['Close'].shift(11).replace(0, 1e-9)) * 100
    df['Coppock'] = (roc_14 + roc_11).ewm(span=10, adjust=False).mean()

    df['Keltner_Upper'] = df['EMA_14'] + (1.5 * df['ATR_14'])
    df['Keltner_Lower'] = df['EMA_14'] - (1.5 * df['ATR_14'])

    high_low_ema = (df['High'] - df['Low']).ewm(span=9, adjust=False).mean()
    high_low_dema = high_low_ema.ewm(span=9, adjust=False).mean()
    df['Mass_Index'] = (high_low_ema / high_low_dema.replace(0, 1e-9)).rolling(25).sum()

    df['PPO'] = ((ema_12 - ema_26) / ema_26.replace(0, 1e-9)) * 100

    rsi_min = df['RSI_14'].rolling(14).min()
    rsi_max = df['RSI_14'].rolling(14).max()
    df['Stoch_RSI'] = (df['RSI_14'] - rsi_min) / (rsi_max - rsi_min).replace(0, 1e-9)

    ema_1 = df['Close'].ewm(span=15, adjust=False).mean()
    ema_2 = ema_1.ewm(span=15, adjust=False).mean()
    ema_3 = ema_2.ewm(span=15, adjust=False).mean()
    df['TRIX'] = ((ema_3 - ema_3.shift(1)) / ema_3.shift(1).replace(0, 1e-9)) * 100

    bp = df['Close'] - pd.concat([df['Low'], df['Close'].shift()], axis=1).min(axis=1)
    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum().replace(0, 1e-9)
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum().replace(0, 1e-9)
    df['Ultimate_Osc'] = 100 * ((4 * avg7) + (2 * avg14) + avg28) / 7

    vol_sma_14 = df['Volume'].rolling(14).mean()
    vol_sma_28 = df['Volume'].rolling(28).mean()
    df['Volume_Osc'] = ((vol_sma_14 - vol_sma_28) / vol_sma_28.replace(0, 1e-9)) * 100

    vmp = np.abs(df['High'] - df['Low'].shift())
    vmm = np.abs(df['Low'] - df['High'].shift())
    df['Vortex_Pos'] = pd.Series(vmp).rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)
    df['Vortex_Neg'] = pd.Series(vmm).rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)

    df['Force_Index'] = (df['Close'] - df['Close'].shift(1)) * df['Volume']
    df['Force_Index_EMA'] = df['Force_Index'].ewm(span=13, adjust=False).mean()

    high, low, close = df['High'].values, df['Low'].values, df['Close'].values
    psar, af, ep, trend = np.zeros(len(df)), np.zeros(len(df)), np.zeros(len(df)), np.zeros(len(df))
    af_step, af_max = 0.02, 0.20
    
    if len(df) > 1:
        trend[1] = 1 if close[1] > close[0] else -1
        psar[1] = low[0] if trend[1] == 1 else high[0]
        ep[1] = high[1] if trend[1] == 1 else low[1]
        af[1] = af_step

        for i in range(2, len(df)):
            psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])
            if trend[i-1] == 1 and low[i] < psar[i]:
                trend[i], psar[i], ep[i], af[i] = -1, ep[i-1], low[i], af_step
            elif trend[i-1] == -1 and high[i] > psar[i]:
                trend[i], psar[i], ep[i], af[i] = 1, ep[i-1], high[i], af_step
            else:
                trend[i], ep[i], af[i] = trend[i-1], ep[i-1], af[i-1]
                if trend[i] == 1:
                    if high[i] > ep[i]:
                        ep[i], af[i] = high[i], min(af[i] + af_step, af_max)
                    psar[i] = min(psar[i], low[i-1], low[i-2])
                else:
                    if low[i] < ep[i]:
                        ep[i], af[i] = low[i], min(af[i] + af_step, af_max)
                    psar[i] = max(psar[i], high[i-1], high[i-2])
    df['PSAR'] = psar
    return df

# =========================================================================
# 4. YAHOOQUERY HIGH-SPEED ASYNC BACKEND (Bypasses IP Blocks)
# =========================================================================
def fetch_all_data(tickers_list):
    st.write("### Live Fetch Log")
    log_container = st.empty()
    
    log_container.info("🚀 Initiating high-speed asynchronous fetch via Mobile APIs...")

    try:
        # asynchronous=True handles all the messy request batching automatically
        t = Ticker(tickers_list, asynchronous=True)
        df = t.history(period='2y')
        
        if df.empty or isinstance(df, dict):
            log_container.error("❌ Failed to pull market data.")
            return pd.DataFrame()
            
        # Format the output to match our math engine
        df = df.reset_index()
        
        # Drop rows where data failed to fetch (yq puts a string in 'error' column)
        if 'error' in df.columns:
            df = df[df['error'].isnull()]
            
        # Rename the lowercase columns to our required Title Case
        df = df.rename(columns={
            'symbol': 'Ticker',
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        # Ensure 'Date' handles timezones safely
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

        processed_dfs = []
        valid_tickers = df['Ticker'].unique()
        
        log_container.info("🧮 Calculating 33 indicators for the market...")
        progress_bar = st.progress(0)

        for i, ticker in enumerate(valid_tickers):
            progress_bar.progress((i + 1) / len(valid_tickers))
            
            ticker_data = df[df['Ticker'] == ticker].copy()
            
            # Require at least 100 days of history so our 52-day math doesn't crash
            if len(ticker_data) >= 100:
                ticker_data = ticker_data.set_index('Date')
                try:
                    calc_df = calculate_indicators(ticker_data)
                    calc_df['Ticker'] = ticker
                    calc_df = calc_df.reset_index() # Bring Date back out of the index
                    processed_dfs.append(calc_df)
                except Exception:
                    pass

        progress_bar.empty()
        log_container.success("✅ Data fetch and calculations complete!")

        if processed_dfs:
            final_combined_df = pd.concat(processed_dfs)
            final_combined_df.dropna(subset=['Ichimoku_Span_B', 'SMA_20', 'ADX_14'], inplace=True)
            return final_combined_df
            
        return pd.DataFrame()

    except Exception as e:
        log_container.error(f"❌ Execution Error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_all_market_data():
    # Only fetch Nifty 200, then extract Nifty 100 from it.
    df_200 = fetch_all_data(NIFTY_200_TICKERS)
    
    if df_200.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    df_100 = df_200[df_200['Ticker'].isin(NIFTY_100_TICKERS)]
    
    return df_100, df_200

# =====================================================================
# 5. UI: EXPLICIT FETCH BUTTON
# =====================================================================
if not st.session_state.data_fetched:
    st.info("👋 Welcome to the Nifty Technical Screener.")
    if st.button("🚀 Fetch Live Market Data", use_container_width=True):
        st.session_state.data_fetched = True
        st.rerun()  
    st.stop()  

df_100, df_200 = load_all_market_data()

if df_100.empty or df_200.empty:
    st.error("🚨 CRITICAL FAILURE: API returned empty data.")
    st.stop()

# =====================================================================
# 6. TOP PANEL
# =====================================================================
selected_index = st.radio("Select Index to Screen", ["Nifty 100", "Nifty 200"], horizontal=True)
df = df_100 if selected_index == "Nifty 100" else df_200

# Safety reset just in case there's an overlapping index
df = df.reset_index(drop=True)
df['Date'] = pd.to_datetime(df['Date']).dt.date

min_available_date = df['Date'].min()
max_available_date = df['Date'].max()

st.divider()

# =====================================================================
# 7. DYNAMIC SIDEBAR: ADD OR REMOVE FILTERS
# =====================================================================
st.sidebar.header("🗓️ Timeframe")
selected_dates = st.sidebar.date_input("Select Date Range", value=(max_available_date, max_available_date), min_value=min_available_date, max_value=max_available_date)
start_date, end_date = selected_dates if len(selected_dates) == 2 else (selected_dates[0], selected_dates[0])

st.sidebar.divider()
st.sidebar.header("🎛️ Add Filters")

FILTER_OPTIONS = [
    "RSI (14)", "MACD", "Bollinger Bands", "SMA (14)", "EMA (14)", "Parabolic SAR", 
    "Ichimoku Cloud", "Stochastic %K", "MFI (14)", "CCI (20)", "Williams %R",
    "ADX (14)", "Aroon Oscillator", "Awesome Oscillator", "Chaikin Money Flow",
    "Chande Momentum (CMO)", "Keltner Channels", "PPO", "Stochastic RSI",
    "Ultimate Oscillator", "Volume Oscillator", "Vortex Index"
]

active_filters = st.sidebar.multiselect("Select indicators to add to your screener:", FILTER_OPTIONS)

# =====================================================================
# 8. APPLYING DYNAMIC FILTERS
# =====================================================================
filtered_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()
display_cols = ['Date', 'Ticker', 'Close']

st.sidebar.markdown("### Active Settings")
if not active_filters:
    st.sidebar.info("Select a filter from the dropdown above to start screening.")

if "RSI (14)" in active_filters:
    min_rsi, max_rsi = st.sidebar.slider("RSI Range", 0.0, 100.0, (30.0, 70.0))
    filtered_data = filtered_data[(filtered_data['RSI_14'] >= min_rsi) & (filtered_data['RSI_14'] <= max_rsi)]
    display_cols.append('RSI_14')

if "MACD" in active_filters:
    macd_status = st.sidebar.selectbox("MACD Signal", ["Bullish (MACD > Signal)", "Bearish (MACD < Signal)"])
    if macd_status == "Bullish (MACD > Signal)":
        filtered_data = filtered_data[filtered_data['MACD'] > filtered_data['MACD_Signal']]
    else:
        filtered_data = filtered_data[filtered_data['MACD'] < filtered_data['MACD_Signal']]
    display_cols.extend(['MACD', 'MACD_Signal'])

if "Bollinger Bands" in active_filters:
    bb_status = st.sidebar.selectbox("Bollinger Bands (20,2)", ["Bullish Breakout (Above Upper)", "Bearish Breakout (Below Lower)", "Inside Bands"])
    if bb_status == "Bullish Breakout (Above Upper)":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data['BB_Upper']]
    elif bb_status == "Bearish Breakout (Below Lower)":
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data['BB_Lower']]
    else:
        filtered_data = filtered_data[(filtered_data['Close'] <= filtered_data['BB_Upper']) & (filtered_data['Close'] >= filtered_data['BB_Lower'])]
    display_cols.extend(['BB_Upper', 'BB_Lower'])

if "SMA (14)" in active_filters:
    sma_status = st.sidebar.selectbox("Price vs SMA (14)", ["Above SMA", "Below SMA"])
    if sma_status == "Above SMA":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data['SMA_14']]
    else:
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data['SMA_14']]
    display_cols.append('SMA_14')

if "ADX (14)" in active_filters:
    min_adx = st.sidebar.slider("Minimum ADX (Trend Strength)", 0.0, 100.0, 25.0)
    filtered_data = filtered_data[filtered_data['ADX_14'] >= min_adx]
    display_cols.append('ADX_14')

if "MFI (14)" in active_filters:
    min_mfi, max_mfi = st.sidebar.slider("Money Flow Index", 0.0, 100.0, (20.0, 80.0))
    filtered_data = filtered_data[(filtered_data['MFI_14'] >= min_mfi) & (filtered_data['MFI_14'] <= max_mfi)]
    display_cols.append('MFI_14')

if "Williams %R" in active_filters:
    min_will, max_will = st.sidebar.slider("Williams %R", -100.0, 0.0, (-80.0, -20.0))
    filtered_data = filtered_data[(filtered_data['Williams_%R'] >= min_will) & (filtered_data['Williams_%R'] <= max_will)]
    display_cols.append('Williams_%R')

if "Parabolic SAR" in active_filters:
    psar_status = st.sidebar.selectbox("Parabolic SAR", ["Bullish (Price > PSAR)", "Bearish (Price < PSAR)"])
    if psar_status == "Bullish (Price > PSAR)":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data['PSAR']]
    else:
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data['PSAR']]
    display_cols.append('PSAR')

# =====================================================================
# 9. MAIN VIEW: DISPLAY RESULTS
# =====================================================================
if start_date == end_date:
    st.markdown(f"### Screened Results for **{start_date}**")
else:
    st.markdown(f"### Screened Results from **{start_date}** to **{end_date}**")

st.write(f"Showing **{len(filtered_data)}** rows matching your criteria.")

if not filtered_data.empty:
    filtered_data = filtered_data.sort_values(by=['Date', 'Ticker'], ascending=[False, True])
    display_df = filtered_data[display_cols].copy()

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
        filtered_data.to_excel(writer, index=False, sheet_name='Screened Stocks')

    file_name_tag = f"{start_date}" if start_date == end_date else f"{start_date}_to_{end_date}"
    
    st.download_button(
        label="📥 Download Full Screened Data (Excel)",
        data=buffer.getvalue(),
        file_name=f"Screened_{selected_index.replace(' ', '_')}_{file_name_tag}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
