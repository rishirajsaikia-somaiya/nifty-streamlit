import streamlit as st
import pandas as pd
import numpy as np
import io
import os

# =========================================================================
# 1. PAGE CONFIGURATION 
# =========================================================================
st.set_page_config(page_title="Live Nifty Screener", layout="wide")
st.title("📈 Nifty Technical Screener")

# =========================================================================
# 2. DATA LOADING (REAL-TIME READ)
# =========================================================================
@st.cache_data(ttl=3600)
def load_data():
    file_path = "nifty_data.csv.gz"
    
    if not os.path.exists(file_path):
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(file_path, compression='gzip')
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⏳ Data file not found. Please ensure the GitHub Action has successfully run and saved 'nifty_data.csv.gz' to your repository.")
    st.stop()
    
# =====================================================================
# 3. TOP PANEL (INDEX SELECTION)
# =====================================================================
selected_index = st.radio("Select Index to Screen", ["Nifty 100", "Nifty 200"], horizontal=True)

if selected_index == "Nifty 100":
    df = df[df['Index'] == 'Nifty 100']

min_available_date = df['Date'].min()
max_available_date = df['Date'].max()

st.divider()

# =====================================================================
# 4. MARKET OVERVIEW DASHBOARD (MARKET INTERNALS)
# =====================================================================
unique_dates = sorted(df['Date'].unique())

if len(unique_dates) >= 2:
    latest_date = unique_dates[-1]
    prev_date = unique_dates[-2]
    
    st.markdown(f"## 📊 Market Pulse ({latest_date})")
    
    last_20_days = unique_dates[-20:] if len(unique_dates) >= 20 else unique_dates
    recent_data = df[df['Date'].isin(last_20_days)].copy()
    
    avg_vol = recent_data.groupby('Ticker')['Volume'].mean()
    recent_data['Daily_Range'] = ((recent_data['High'] - recent_data['Low']) / recent_data['Low'].replace(0, 1e-9)) * 100
    avg_adr = recent_data.groupby('Ticker')['Daily_Range'].mean()

    latest_data = df[df['Date'] == latest_date].set_index('Ticker')
    prev_data = df[df['Date'] == prev_date].set_index('Ticker')
    
    merged = latest_data.join(prev_data[['Close']], rsuffix='_prev')
    merged['Pct_Change'] = ((merged['Close'] - merged['Close_prev']) / merged['Close_prev'].replace(0, 1e-9)) * 100
    
    merged['Turnover'] = merged['Close'] * merged['Volume']
    total_turnover_cr = merged['Turnover'].sum() / 10000000  
    
    gap_ups = len(merged[merged['Open'] > merged['Close_prev']])
    gap_downs = len(merged[merged['Open'] < merged['Close_prev']])
    
    merged = merged.join(avg_vol.rename('Avg_Vol_20')).join(avg_adr.rename('ADR_20'))
    merged['RVOL'] = merged['Volume'] / merged['Avg_Vol_20'].replace(0, 1e-9)
    avg_rvol = merged['RVOL'].mean()
    avg_market_adr = merged['ADR_20'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌅 Gap Ups vs Downs", f"{gap_ups} / {gap_downs}")
    col2.metric("💸 Total Index Turnover", f"₹{total_turnover_cr:,.0f} Cr")
    col3.metric("📊 Average RVOL", f"{avg_rvol:.2f}x")
    col4.metric("🎢 Average Daily Range", f"{avg_market_adr:.2f}%")
    
    st.write("")
    
    col_g, col_l, col_v = st.columns(3)
    
    with col_g:
        st.markdown("#### 🔥 Top Gainers")
        top_gainers = merged.nlargest(5, 'Pct_Change')[['Close', 'Pct_Change']]
        top_gainers.columns = ['Close (₹)', 'Change (%)']
        st.dataframe(
            top_gainers.style.format({'Close (₹)': '{:.2f}', 'Change (%)': '{:.2f}%'})
                       .map(lambda x: 'color: #00FF00' if x > 0 else '', subset=['Change (%)']),
            use_container_width=True
        )

    with col_l:
        st.markdown("#### 🩸 Top Losers")
        top_losers = merged.nsmallest(5, 'Pct_Change')[['Close', 'Pct_Change']]
        top_losers.columns = ['Close (₹)', 'Change (%)']
        st.dataframe(
            top_losers.style.format({'Close (₹)': '{:.2f}', 'Change (%)': '{:.2f}%'})
                      .map(lambda x: 'color: #FF4B4B' if x < 0 else '', subset=['Change (%)']),
            use_container_width=True
        )
        
    with col_v:
        st.markdown("#### 💸 Highest Turnover")
        top_volume = merged.nlargest(5, 'Turnover')[['Close', 'Turnover']]
        top_volume['Turnover (Cr)'] = top_volume['Turnover'] / 10000000 
        top_volume = top_volume[['Close', 'Turnover (Cr)']]
        top_volume.columns = ['Close (₹)', 'Turnover (Cr)']
        st.dataframe(
            top_volume.style.format({'Close (₹)': '{:.2f}', 'Turnover (Cr)': '₹{:.2f} Cr'}),
            use_container_width=True
        )

st.divider()

# =====================================================================
# 5. DYNAMIC SIDEBAR: ADD OR REMOVE FILTERS
# =====================================================================
st.sidebar.header("🗓️ Timeframe")
selected_dates = st.sidebar.date_input("Select Date Range", value=(max_available_date, max_available_date), min_value=min_available_date, max_value=max_available_date)
start_date, end_date = selected_dates if len(selected_dates) == 2 else (selected_dates[0], selected_dates[0])

st.sidebar.divider()
st.sidebar.header("🎛️ Add Filters")

# Fully Dynamic List (Period-dependent tools marked as Dynamic)
FILTER_OPTIONS = [
    "Accumulation/Distribution", 
    "ADX (Dynamic)", 
    "Aroon Oscillator (Dynamic)", 
    "Awesome Oscillator (Dynamic)", 
    "Balance of Power", 
    "Bollinger Bands (Dynamic)", 
    "CCI (Dynamic)", 
    "Chaikin Money Flow (Dynamic)", 
    "Chaikin Volatility (Dynamic)", 
    "Chande Momentum (Dynamic)", 
    "Detrended Price Oscillator (Dynamic)", 
    "Disparity Index (Dynamic)", 
    "Ease of Movement (Dynamic)", 
    "Elder Ray Index (Dynamic)", 
    "EMA (Dynamic)", 
    "High Low Bands (Dynamic)", 
    "Highest High Value (Dynamic)", 
    "Ichimoku Cloud", 
    "Keltner Channels (Dynamic)", 
    "Lowest Low Value (Dynamic)", 
    "MACD (Dynamic)", 
    "Median Price", 
    "MFI (Dynamic)", 
    "Momentum (Dynamic)", 
    "Moving Average Envelope (Dynamic)", 
    "Negative Volume Index", 
    "Parabolic SAR", 
    "Performance Index", 
    "Positive Volume Index", 
    "PPO (Dynamic)", 
    "Price Volume Trend", 
    "RSI (Dynamic)", 
    "SMA (Dynamic)", 
    "Standard Deviation (Dynamic)", 
    "Stochastic %K (Dynamic)", 
    "Stochastic RSI (Dynamic)", 
    "True Range", 
    "Typical Price", 
    "Ulcer Index (Dynamic)", 
    "Ultimate Oscillator (Dynamic)", 
    "Volume Oscillator (Dynamic)", 
    "Volume ROC (Dynamic)", 
    "Vortex Index (Dynamic)", 
    "Williams %R (Dynamic)"
]

active_filters = st.sidebar.multiselect("Select indicators to add to your screener:", FILTER_OPTIONS)

# =====================================================================
# 6. DYNAMIC RUNTIME CALCULATIONS & FILTERING
# =====================================================================
st.sidebar.markdown("### Active Settings")
if not active_filters:
    st.sidebar.info("Select an indicator from the dropdown above to start.")

# MUST SORT BY TICKER AND DATE FOR ROLLING MATH TO WORK ACCURATELY
df = df.sort_values(['Ticker', 'Date'])
display_cols = ['Date', 'Ticker', 'Close']

# --- HELPER VARS ---
delta = df.groupby('Ticker')['Close'].diff()
tp = (df['High'] + df['Low'] + df['Close']) / 3

# ---------------------------------------------------------
# LIVE CALCULATIONS (Only runs if the user selects the tool)
# ---------------------------------------------------------

if "ADX (Dynamic)" in active_filters:
    p = st.sidebar.number_input("ADX Period", 5, 100, 14)
    col = f'ADX_{p}'
    df['up_move'] = df.groupby('Ticker')['High'].diff()
    df['down_move'] = df.groupby('Ticker')['Low'].shift(1) - df['Low']
    df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0.0)
    df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0.0)
    tr1 = df['High'] - df['Low']
    tr2 = np.abs(df['High'] - df.groupby('Ticker')['Close'].shift(1))
    tr3 = np.abs(df['Low'] - df.groupby('Ticker')['Close'].shift(1))
    df['tr'] = np.maximum(tr1, np.maximum(tr2, tr3))
    df['tr_s'] = df.groupby('Ticker')['tr'].transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
    df['plus_dm_s'] = df.groupby('Ticker')['plus_dm'].transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
    df['minus_dm_s'] = df.groupby('Ticker')['minus_dm'].transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
    df['plus_di'] = 100 * (df['plus_dm_s'] / df['tr_s'].replace(0, 1e-9))
    df['minus_di'] = 100 * (df['minus_dm_s'] / df['tr_s'].replace(0, 1e-9))
    df['dx'] = (np.abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di']).replace(0, 1e-9)) * 100
    df[col] = df.groupby('Ticker')['dx'].transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
    min_adx = st.sidebar.slider(f"Minimum ADX ({p})", 0.0, 100.0, 25.0)
    display_cols.append(col)

if "Aroon Oscillator (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Aroon Period", 5, 100, 14)
    col = f'Aroon_{p}'
    aroon_up = df.groupby('Ticker')['High'].transform(lambda x: x.rolling(p).apply(np.argmax, raw=True))
    aroon_down = df.groupby('Ticker')['Low'].transform(lambda x: x.rolling(p).apply(np.argmin, raw=True))
    df[col] = ((aroon_up / p) * 100) - ((aroon_down / p) * 100)
    aroon_status = st.sidebar.selectbox(f"Aroon ({p})", ["Positive (Bullish)", "Negative (Bearish)"])
    display_cols.append(col)

if "Awesome Oscillator (Dynamic)" in active_filters:
    p_short = st.sidebar.number_input("AO Short Period", 2, 50, 5)
    p_long = st.sidebar.number_input("AO Long Period", 10, 200, 34)
    col = f'AO_{p_short}_{p_long}'
    hl2 = (df['High'] + df['Low']) / 2
    sma_s = hl2.groupby(df['Ticker']).transform(lambda x: x.rolling(p_short).mean())
    sma_l = hl2.groupby(df['Ticker']).transform(lambda x: x.rolling(p_long).mean())
    df[col] = sma_s - sma_l
    ao_status = st.sidebar.selectbox(f"Awesome Osc ({p_short},{p_long})", ["Above Zero", "Below Zero"])
    display_cols.append(col)

if "Bollinger Bands (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Bollinger Period", 5, 100, 20)
    std = st.sidebar.number_input("Standard Deviations", 1.0, 4.0, 2.0, 0.1)
    upper = f'BB_Up_{p}'
    lower = f'BB_Low_{p}'
    sma_t = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).mean())
    std_t = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).std())
    df[upper] = sma_t + (std_t * std)
    df[lower] = sma_t - (std_t * std)
    bb_status = st.sidebar.selectbox(f"BBands ({p},{std})", ["Above Upper", "Below Lower", "Inside Bands"])
    display_cols.extend([upper, lower])

if "CCI (Dynamic)" in active_filters:
    p = st.sidebar.number_input("CCI Period", 5, 100, 20)
    col = f'CCI_{p}'
    sma_tp = tp.groupby(df['Ticker']).transform(lambda x: x.rolling(p).mean())
    mad = tp.groupby(df['Ticker']).transform(lambda x: x.rolling(p).apply(lambda y: np.mean(np.abs(y - np.mean(y))), raw=True))
    df[col] = (tp - sma_tp) / (0.015 * mad.replace(0, 1e-9))
    min_cci, max_cci = st.sidebar.slider(f"CCI ({p}) Range", -300.0, 300.0, (-100.0, 100.0))
    display_cols.append(col)

if "Chaikin Money Flow (Dynamic)" in active_filters:
    p = st.sidebar.number_input("CMF Period", 5, 100, 20)
    col = f'CMF_{p}'
    mfv = df['Volume'] * ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low']).replace(0, 1e-9)
    df[col] = mfv.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum()) / df.groupby('Ticker')['Volume'].transform(lambda x: x.rolling(p).sum()).replace(0, 1e-9)
    cmf_status = st.sidebar.selectbox(f"CMF ({p})", ["Positive (Buying)", "Negative (Selling)"])
    display_cols.append(col)

if "Chaikin Volatility (Dynamic)" in active_filters:
    p = st.sidebar.number_input("CV Period", 5, 100, 10)
    col = f'CV_{p}'
    hl_ema = (df['High'] - df['Low']).groupby(df['Ticker']).transform(lambda x: x.ewm(span=10, adjust=False).mean())
    df[col] = ((hl_ema - hl_ema.groupby(df['Ticker']).shift(p)) / hl_ema.groupby(df['Ticker']).shift(p).replace(0, 1e-9)) * 100
    min_cv = st.sidebar.slider(f"Min Chaikin Volatility ({p})", -50.0, 50.0, 0.0)
    display_cols.append(col)

if "Chande Momentum (Dynamic)" in active_filters:
    p = st.sidebar.number_input("CMO Period", 5, 100, 14)
    col = f'CMO_{p}'
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    sum_g = gain.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum())
    sum_l = loss.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum())
    df[col] = 100 * ((sum_g - sum_l) / (sum_g + sum_l).replace(0, 1e-9))
    cmo_status = st.sidebar.selectbox(f"CMO ({p})", ["Overbought (> 50)", "Oversold (< -50)", "Neutral"])
    display_cols.append(col)

if "Detrended Price Oscillator (Dynamic)" in active_filters:
    p = st.sidebar.number_input("DPO Period", 5, 100, 20)
    col = f'DPO_{p}'
    shift_val = int((p/2) + 1)
    shifted_mean = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).mean().shift(shift_val))
    df[col] = df['Close'] - shifted_mean
    dpo_status = st.sidebar.selectbox(f"DPO ({p})", ["Above Zero", "Below Zero"])
    display_cols.append(col)

if "Disparity Index (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Disparity Period", 5, 100, 14)
    col = f'Disp_{p}'
    sma_t = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).mean())
    df[col] = ((df['Close'] - sma_t) / sma_t.replace(0, 1e-9)) * 100
    display_cols.append(col)

if "Ease of Movement (Dynamic)" in active_filters:
    p = st.sidebar.number_input("EOM Period", 5, 100, 14)
    col = f'EOM_{p}'
    dm = ((df['High'] + df['Low']) / 2) - ((df.groupby('Ticker')['High'].shift(1) + df.groupby('Ticker')['Low'].shift(1)) / 2)
    br = (df['Volume'] / 100000000) / (df['High'] - df['Low']).replace(0, 1e-9)
    df[col] = (dm / br.replace(0, 1e-9)).groupby(df['Ticker']).transform(lambda x: x.rolling(p).mean())
    eom_status = st.sidebar.selectbox(f"EOM ({p})", ["Positive", "Negative"])
    display_cols.append(col)

if "Elder Ray Index (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Elder Ray EMA Period", 5, 100, 13)
    bull = f'Elder_Bull_{p}'
    bear = f'Elder_Bear_{p}'
    ema_t = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=p, adjust=False).mean())
    df[bull] = df['High'] - ema_t
    df[bear] = df['Low'] - ema_t
    display_cols.extend([bull, bear])

if "EMA (Dynamic)" in active_filters:
    p = st.sidebar.number_input("EMA Period", 2, 500, 21)
    col = f'EMA_{p}'
    df[col] = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=p, adjust=False).mean())
    ema_status = st.sidebar.selectbox(f"Price vs EMA ({p})", ["Above EMA", "Below EMA"])
    display_cols.append(col)

if "High Low Bands (Dynamic)" in active_filters:
    p = st.sidebar.number_input("HL Bands Period", 5, 100, 14)
    hb = f'HighBand_{p}'
    lb = f'LowBand_{p}'
    df[hb] = df.groupby('Ticker')['High'].transform(lambda x: x.rolling(p).mean())
    df[lb] = df.groupby('Ticker')['Low'].transform(lambda x: x.rolling(p).mean())
    display_cols.extend([hb, lb])

if "Highest High Value (Dynamic)" in active_filters:
    p = st.sidebar.number_input("HHV Period", 5, 100, 14)
    col = f'HHV_{p}'
    df[col] = df.groupby('Ticker')['High'].transform(lambda x: x.rolling(p).max())
    display_cols.append(col)

if "Keltner Channels (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Keltner Period", 5, 100, 20)
    mult = st.sidebar.number_input("ATR Multiplier", 1.0, 4.0, 1.5, 0.1)
    ku = f'KC_Up_{p}'
    kl = f'KC_Low_{p}'
    ema_t = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=p, adjust=False).mean())
    tr_t = np.maximum(df['High'] - df['Low'], np.maximum(np.abs(df['High'] - df.groupby('Ticker')['Close'].shift(1)), np.abs(df['Low'] - df.groupby('Ticker')['Close'].shift(1))))
    atr_t = tr_t.groupby(df['Ticker']).transform(lambda x: x.rolling(p).mean())
    df[ku] = ema_t + (mult * atr_t)
    df[kl] = ema_t - (mult * atr_t)
    kc_status = st.sidebar.selectbox(f"Keltner ({p})", ["Above Upper", "Below Lower"])
    display_cols.extend([ku, kl])

if "Lowest Low Value (Dynamic)" in active_filters:
    p = st.sidebar.number_input("LLV Period", 5, 100, 14)
    col = f'LLV_{p}'
    df[col] = df.groupby('Ticker')['Low'].transform(lambda x: x.rolling(p).min())
    display_cols.append(col)

if "MACD (Dynamic)" in active_filters:
    fast = st.sidebar.number_input("MACD Fast", 2, 50, 12)
    slow = st.sidebar.number_input("MACD Slow", 5, 100, 26)
    sig = st.sidebar.number_input("MACD Signal", 2, 50, 9)
    col_m = f'MACD_{fast}_{slow}'
    col_s = f'MACDSig_{sig}'
    fast_e = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=fast, adjust=False).mean())
    slow_e = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=slow, adjust=False).mean())
    df[col_m] = fast_e - slow_e
    df[col_s] = df.groupby('Ticker')[col_m].transform(lambda x: x.ewm(span=sig, adjust=False).mean())
    macd_status = st.sidebar.selectbox(f"MACD ({fast},{slow},{sig})", ["Bullish (> Signal)", "Bearish (< Signal)"])
    display_cols.extend([col_m, col_s])

if "MFI (Dynamic)" in active_filters:
    p = st.sidebar.number_input("MFI Period", 5, 100, 14)
    col = f'MFI_{p}'
    rmf = tp * df['Volume']
    pos_flow = rmf.where(tp.groupby(df['Ticker']).diff() > 0, 0.0)
    neg_flow = rmf.where(tp.groupby(df['Ticker']).diff() < 0, 0.0)
    pos_sum = pos_flow.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum())
    neg_sum = neg_flow.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum())
    df[col] = 100 - (100 / (1 + (pos_sum / neg_sum.replace(0, 1e-9))))
    min_mfi, max_mfi = st.sidebar.slider(f"MFI ({p}) Range", 0.0, 100.0, (20.0, 80.0))
    display_cols.append(col)

if "Momentum (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Momentum Period", 5, 100, 10)
    col = f'Mom_{p}'
    df[col] = df['Close'] - df.groupby('Ticker')['Close'].shift(p)
    mom_status = st.sidebar.selectbox(f"Momentum ({p})", ["Positive", "Negative"])
    display_cols.append(col)

if "Moving Average Envelope (Dynamic)" in active_filters:
    p = st.sidebar.number_input("MAE Period", 5, 100, 20)
    pct = st.sidebar.number_input("MAE Envelope %", 1.0, 20.0, 5.0, 0.5) / 100
    eu = f'MAE_Up_{p}'
    el = f'MAE_Low_{p}'
    sma_t = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).mean())
    df[eu] = sma_t * (1 + pct)
    df[el] = sma_t * (1 - pct)
    mae_status = st.sidebar.selectbox(f"MAE ({p})", ["Above Upper", "Below Lower", "Inside"])
    display_cols.extend([eu, el])

if "PPO (Dynamic)" in active_filters:
    fast = st.sidebar.number_input("PPO Fast", 2, 50, 12)
    slow = st.sidebar.number_input("PPO Slow", 5, 100, 26)
    col = f'PPO_{fast}_{slow}'
    fast_e = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=fast, adjust=False).mean())
    slow_e = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=slow, adjust=False).mean())
    df[col] = ((fast_e - slow_e) / slow_e.replace(0, 1e-9)) * 100
    ppo_status = st.sidebar.selectbox(f"PPO ({fast},{slow})", ["Positive Momentum", "Negative Momentum"])
    display_cols.append(col)

if "RSI (Dynamic)" in active_filters:
    p = st.sidebar.number_input("RSI Period", 2, 100, 14)
    col = f'RSI_{p}'
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.groupby(df['Ticker']).transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
    avg_loss = loss.groupby(df['Ticker']).transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    df[col] = 100 - (100 / (1 + rs))
    min_rsi, max_rsi = st.sidebar.slider(f"RSI ({p}) Range", 0.0, 100.0, (30.0, 70.0))
    display_cols.append(col)

if "SMA (Dynamic)" in active_filters:
    p = st.sidebar.number_input("SMA Period", 2, 500, 20)
    col = f'SMA_{p}'
    df[col] = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).mean())
    sma_status = st.sidebar.selectbox(f"Price vs SMA ({p})", ["Above SMA", "Below SMA"])
    display_cols.append(col)

if "Standard Deviation (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Std Dev Period", 5, 100, 20)
    col = f'StdDev_{p}'
    df[col] = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).std())
    display_cols.append(col)

if "Stochastic %K (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Stoch %K Period", 5, 100, 14)
    col = f'StochK_{p}'
    ll = df.groupby('Ticker')['Low'].transform(lambda x: x.rolling(p).min())
    hh = df.groupby('Ticker')['High'].transform(lambda x: x.rolling(p).max())
    df[col] = ((df['Close'] - ll) / (hh - ll).replace(0, 1e-9)) * 100
    min_stoch, max_stoch = st.sidebar.slider(f"Stoch %K ({p}) Range", 0.0, 100.0, (20.0, 80.0))
    display_cols.append(col)

if "Stochastic RSI (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Stoch RSI Period", 5, 100, 14)
    col = f'StochRSI_{p}'
    if f'RSI_{p}' not in df.columns:
        g = delta.where(delta > 0, 0.0).groupby(df['Ticker']).transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
        l = (-delta.where(delta < 0, 0.0)).groupby(df['Ticker']).transform(lambda x: x.ewm(alpha=1/p, adjust=False).mean())
        rsi = 100 - (100 / (1 + (g / l.replace(0, 1e-9))))
    else:
        rsi = df[f'RSI_{p}']
    rsi_ll = rsi.groupby(df['Ticker']).transform(lambda x: x.rolling(p).min())
    rsi_hh = rsi.groupby(df['Ticker']).transform(lambda x: x.rolling(p).max())
    df[col] = ((rsi - rsi_ll) / (rsi_hh - rsi_ll).replace(0, 1e-9)) * 100
    min_srsi, max_srsi = st.sidebar.slider(f"Stoch RSI ({p})", 0.0, 100.0, (20.0, 80.0))
    display_cols.append(col)

if "Ulcer Index (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Ulcer Period", 5, 100, 14)
    col = f'Ulcer_{p}'
    max_c = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(p).max())
    pd_down = ((df['Close'] - max_c) / max_c.replace(0, 1e-9)) * 100
    df[col] = np.sqrt((pd_down ** 2).groupby(df['Ticker']).transform(lambda x: x.rolling(p).mean()))
    max_ulcer = st.sidebar.slider(f"Max Ulcer Index ({p})", 0.0, 50.0, 10.0)
    display_cols.append(col)

if "Ultimate Oscillator (Dynamic)" in active_filters:
    p1 = st.sidebar.number_input("UO Short", 2, 20, 7)
    p2 = st.sidebar.number_input("UO Med", 5, 50, 14)
    p3 = st.sidebar.number_input("UO Long", 10, 100, 28)
    col = f'UO_{p1}_{p2}_{p3}'
    tr_t = np.maximum(df['High'] - df['Low'], np.maximum(np.abs(df['High'] - df.groupby('Ticker')['Close'].shift(1)), np.abs(df['Low'] - df.groupby('Ticker')['Close'].shift(1))))
    bp = df['Close'] - np.minimum(df['Low'], df.groupby('Ticker')['Close'].shift(1))
    a1 = bp.groupby(df['Ticker']).transform(lambda x: x.rolling(p1).sum()) / tr_t.groupby(df['Ticker']).transform(lambda x: x.rolling(p1).sum()).replace(0, 1e-9)
    a2 = bp.groupby(df['Ticker']).transform(lambda x: x.rolling(p2).sum()) / tr_t.groupby(df['Ticker']).transform(lambda x: x.rolling(p2).sum()).replace(0, 1e-9)
    a3 = bp.groupby(df['Ticker']).transform(lambda x: x.rolling(p3).sum()) / tr_t.groupby(df['Ticker']).transform(lambda x: x.rolling(p3).sum()).replace(0, 1e-9)
    df[col] = 100 * ((4 * a1) + (2 * a2) + a3) / 7
    min_uo, max_uo = st.sidebar.slider(f"Ultimate Osc ({p1},{p2},{p3})", 0.0, 100.0, (30.0, 70.0))
    display_cols.append(col)

if "Volume Oscillator (Dynamic)" in active_filters:
    s = st.sidebar.number_input("Vol Osc Short", 2, 50, 14)
    l = st.sidebar.number_input("Vol Osc Long", 5, 100, 28)
    col = f'VolOsc_{s}_{l}'
    vs = df.groupby('Ticker')['Volume'].transform(lambda x: x.rolling(s).mean())
    vl = df.groupby('Ticker')['Volume'].transform(lambda x: x.rolling(l).mean())
    df[col] = ((vs - vl) / vl.replace(0, 1e-9)) * 100
    vo_status = st.sidebar.selectbox(f"Vol Osc ({s},{l})", ["Expanding (> 0)", "Contracting (< 0)"])
    display_cols.append(col)

if "Volume ROC (Dynamic)" in active_filters:
    p = st.sidebar.number_input("VROC Period", 2, 100, 14)
    col = f'VROC_{p}'
    df[col] = df.groupby('Ticker')['Volume'].transform(lambda x: x.pct_change(periods=p)) * 100
    min_vroc = st.sidebar.slider(f"Min VROC ({p}) %", -100.0, 500.0, 50.0)
    display_cols.append(col)

if "Vortex Index (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Vortex Period", 5, 100, 14)
    vp = f'Vortex_P_{p}'
    vn = f'Vortex_N_{p}'
    vmp = np.abs(df['High'] - df.groupby('Ticker')['Low'].shift(1))
    vmm = np.abs(df['Low'] - df.groupby('Ticker')['High'].shift(1))
    tr_t = np.maximum(df['High'] - df['Low'], np.maximum(np.abs(df['High'] - df.groupby('Ticker')['Close'].shift(1)), np.abs(df['Low'] - df.groupby('Ticker')['Close'].shift(1))))
    tr_sum = tr_t.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum())
    df[vp] = vmp.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum()) / tr_sum.replace(0, 1e-9)
    df[vn] = vmm.groupby(df['Ticker']).transform(lambda x: x.rolling(p).sum()) / tr_sum.replace(0, 1e-9)
    vi_status = st.sidebar.selectbox(f"Vortex ({p})", ["Bullish (VI+ > VI-)", "Bearish (VI- > VI+)"])
    display_cols.extend([vp, vn])

if "Williams %R (Dynamic)" in active_filters:
    p = st.sidebar.number_input("Williams Period", 5, 100, 14)
    col = f'WillR_{p}'
    hh = df.groupby('Ticker')['High'].transform(lambda x: x.rolling(p).max())
    ll = df.groupby('Ticker')['Low'].transform(lambda x: x.rolling(p).min())
    df[col] = ((hh - df['Close']) / (hh - ll).replace(0, 1e-9)) * -100
    min_will, max_will = st.sidebar.slider(f"Will %R ({p})", -100.0, 0.0, (-80.0, -20.0))
    display_cols.append(col)


# ---------------------------------------------------------
# SLICE TIMEFRAME & APPLY FILTERS
# ---------------------------------------------------------
filtered_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()

# Filter checks
if "ADX (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'ADX_{adx_period}'] >= min_adx]
if "Aroon Oscillator (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'Aroon_{p}'] > 0] if aroon_status == "Positive (Bullish)" else filtered_data[filtered_data[f'Aroon_{p}'] < 0]
if "Awesome Oscillator (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'AO_{p_short}_{p_long}'] > 0] if ao_status == "Above Zero" else filtered_data[filtered_data[f'AO_{p_short}_{p_long}'] < 0]
if "Bollinger Bands (Dynamic)" in active_filters:
    if bb_status == "Above Upper": filtered_data = filtered_data[filtered_data['Close'] > filtered_data[f'BB_Up_{p}']]
    elif bb_status == "Below Lower": filtered_data = filtered_data[filtered_data['Close'] < filtered_data[f'BB_Low_{p}']]
    else: filtered_data = filtered_data[(filtered_data['Close'] <= filtered_data[f'BB_Up_{p}']) & (filtered_data['Close'] >= filtered_data[f'BB_Low_{p}'])]
if "CCI (Dynamic)" in active_filters: filtered_data = filtered_data[(filtered_data[f'CCI_{p}'] >= min_cci) & (filtered_data[f'CCI_{p}'] <= max_cci)]
if "Chaikin Money Flow (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'CMF_{p}'] > 0] if cmf_status == "Positive (Buying)" else filtered_data[filtered_data[f'CMF_{p}'] < 0]
if "Chaikin Volatility (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'CV_{p}'] >= min_cv]
if "Chande Momentum (Dynamic)" in active_filters:
    if cmo_status == "Overbought (> 50)": filtered_data = filtered_data[filtered_data[f'CMO_{p}'] > 50]
    elif cmo_status == "Oversold (< -50)": filtered_data = filtered_data[filtered_data[f'CMO_{p}'] < -50]
    else: filtered_data = filtered_data[(filtered_data[f'CMO_{p}'] <= 50) & (filtered_data[f'CMO_{p}'] >= -50)]
if "Detrended Price Oscillator (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'DPO_{p}'] > 0] if dpo_status == "Above Zero" else filtered_data[filtered_data[f'DPO_{p}'] < 0]
if "Ease of Movement (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'EOM_{p}'] > 0] if eom_status == "Positive" else filtered_data[filtered_data[f'EOM_{p}'] < 0]
if "EMA (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data['Close'] > filtered_data[f'EMA_{p}']] if ema_status == "Above EMA" else filtered_data[filtered_data['Close'] < filtered_data[f'EMA_{p}']]
if "Keltner Channels (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data['Close'] > filtered_data[f'KC_Up_{p}']] if kc_status == "Above Upper" else filtered_data[filtered_data['Close'] < filtered_data[f'KC_Low_{p}']]
if "MACD (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'MACD_{fast}_{slow}'] > filtered_data[f'MACDSig_{sig}']] if macd_status == "Bullish (> Signal)" else filtered_data[filtered_data[f'MACD_{fast}_{slow}'] < filtered_data[f'MACDSig_{sig}']]
if "MFI (Dynamic)" in active_filters: filtered_data = filtered_data[(filtered_data[f'MFI_{p}'] >= min_mfi) & (filtered_data[f'MFI_{p}'] <= max_mfi)]
if "Momentum (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'Mom_{p}'] > 0] if mom_status == "Positive" else filtered_data[filtered_data[f'Mom_{p}'] < 0]
if "Moving Average Envelope (Dynamic)" in active_filters:
    if mae_status == "Above Upper": filtered_data = filtered_data[filtered_data['Close'] > filtered_data[f'MAE_Up_{p}']]
    elif mae_status == "Below Lower": filtered_data = filtered_data[filtered_data['Close'] < filtered_data[f'MAE_Low_{p}']]
    else: filtered_data = filtered_data[(filtered_data['Close'] <= filtered_data[f'MAE_Up_{p}']) & (filtered_data['Close'] >= filtered_data[f'MAE_Low_{p}'])]
if "PPO (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'PPO_{fast}_{slow}'] > 0] if ppo_status == "Positive Momentum" else filtered_data[filtered_data[f'PPO_{fast}_{slow}'] < 0]
if "RSI (Dynamic)" in active_filters: filtered_data = filtered_data[(filtered_data[f'RSI_{rsi_period}'] >= min_rsi) & (filtered_data[f'RSI_{rsi_period}'] <= max_rsi)]
if "SMA (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data['Close'] > filtered_data[f'SMA_{p}']] if sma_status == "Above SMA" else filtered_data[filtered_data['Close'] < filtered_data[f'SMA_{p}']]
if "Stochastic %K (Dynamic)" in active_filters: filtered_data = filtered_data[(filtered_data[f'StochK_{p}'] >= min_stoch) & (filtered_data[f'StochK_{p}'] <= max_stoch)]
if "Stochastic RSI (Dynamic)" in active_filters: filtered_data = filtered_data[(filtered_data[f'StochRSI_{p}'] >= min_srsi) & (filtered_data[f'StochRSI_{p}'] <= max_srsi)]
if "Ulcer Index (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'Ulcer_{p}'] <= max_ulcer]
if "Ultimate Oscillator (Dynamic)" in active_filters: filtered_data = filtered_data[(filtered_data[f'UO_{p1}_{p2}_{p3}'] >= min_uo) & (filtered_data[f'UO_{p1}_{p2}_{p3}'] <= max_uo)]
if "Volume Oscillator (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'VolOsc_{s}_{l}'] > 0] if vo_status == "Expanding (> 0)" else filtered_data[filtered_data[f'VolOsc_{s}_{l}'] < 0]
if "Volume ROC (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'VROC_{p}'] >= min_vroc]
if "Vortex Index (Dynamic)" in active_filters: filtered_data = filtered_data[filtered_data[f'Vortex_P_{p}'] > filtered_data[f'Vortex_N_{p}']] if vi_status == "Bullish (VI+ > VI-)" else filtered_data[filtered_data[f'Vortex_P_{p}'] < filtered_data[f'Vortex_N_{p}']]
if "Williams %R (Dynamic)" in active_filters: filtered_data = filtered_data[(filtered_data[f'WillR_{p}'] >= min_will) & (filtered_data[f'WillR_{p}'] <= max_will)]

# Non-Dynamic (Static Math) Applications
if "Accumulation/Distribution" in active_filters: display_cols.append('Acc_Dist')
if "Balance of Power" in active_filters:
    filtered_data = filtered_data[filtered_data['Balance_Of_Power'] > 0] if st.sidebar.selectbox("Balance of Power", ["Buyers (> 0)", "Sellers (< 0)"]) == "Buyers (> 0)" else filtered_data[filtered_data['Balance_Of_Power'] < 0]
    display_cols.append('Balance_Of_Power')
if "Ichimoku Cloud" in active_filters:
    stat = st.sidebar.selectbox("Ichimoku Trend", ["Above Cloud", "Below Cloud"])
    filtered_data = filtered_data[(filtered_data['Close'] > filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] > filtered_data['Ichimoku_Span_B'])] if stat == "Above Cloud" else filtered_data[(filtered_data['Close'] < filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] < filtered_data['Ichimoku_Span_B'])]
    display_cols.extend(['Ichimoku_Span_A', 'Ichimoku_Span_B'])
if "Median Price" in active_filters: display_cols.append('Median_Price')
if "Negative Volume Index" in active_filters: display_cols.append('NVI')
if "Parabolic SAR" in active_filters:
    filtered_data = filtered_data[filtered_data['Close'] > filtered_data['PSAR']] if st.sidebar.selectbox("PSAR", ["Price > PSAR", "Price < PSAR"]) == "Price > PSAR" else filtered_data[filtered_data['Close'] < filtered_data['PSAR']]
    display_cols.append('PSAR')
if "Performance Index" in active_filters: display_cols.append('Performance_Index')
if "Positive Volume Index" in active_filters: display_cols.append('PVI')
if "Price Volume Trend" in active_filters: display_cols.append('PVT')
if "True Range" in active_filters: display_cols.append('True_Range')
if "Typical Price" in active_filters: display_cols.append('Typical_Price')

# =====================================================================
# 7. MAIN VIEW: DISPLAY SCREENED RESULTS
# =====================================================================
st.markdown("## 🔍 Screener Results")

if start_date == end_date:
    st.markdown(f"Results for **{start_date}**")
else:
    st.markdown(f"Results from **{start_date}** to **{end_date}**")

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
# 8. EXPORT FEATURE
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
