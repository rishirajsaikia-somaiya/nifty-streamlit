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
@st.cache_data(ttl=3600) # Cache for 1 hour to speed up UI interactions
def load_data():
    file_path = "nifty_data.csv.gz"
    
    if not os.path.exists(file_path):
        return pd.DataFrame()
        
    try:
        # Pandas natively reads compressed gzip files
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
    
    # Grab the last 20 days of data to establish baselines for RVOL and ADR
    last_20_days = unique_dates[-20:] if len(unique_dates) >= 20 else unique_dates
    recent_data = df[df['Date'].isin(last_20_days)].copy()
    
    # Calculate 20-day Average Volume 
    avg_vol = recent_data.groupby('Ticker')['Volume'].mean()
    
    # Calculate 20-day Average Daily Range (ADR as a percentage)
    recent_data['Daily_Range'] = ((recent_data['High'] - recent_data['Low']) / recent_data['Low']) * 100
    avg_adr = recent_data.groupby('Ticker')['Daily_Range'].mean()

    # Isolate today's and yesterday's data
    latest_data = df[df['Date'] == latest_date].set_index('Ticker')
    prev_data = df[df['Date'] == prev_date].set_index('Ticker')
    
    # Join today and yesterday to calculate daily metrics
    merged = latest_data.join(prev_data[['Close']], rsuffix='_prev')
    merged['Pct_Change'] = ((merged['Close'] - merged['Close_prev']) / merged['Close_prev']) * 100
    
    # 1. Turnover (Total Rupee value traded today)
    merged['Turnover'] = merged['Close'] * merged['Volume']
    total_turnover_cr = merged['Turnover'].sum() / 10000000  # Convert to Crores
    
    # 2. Gap Ups / Gap Downs (Overnight Sentiment)
    gap_ups = len(merged[merged['Open'] > merged['Close_prev']])
    gap_downs = len(merged[merged['Open'] < merged['Close_prev']])
    
    # 3. Relative Volume (RVOL)
    merged = merged.join(avg_vol.rename('Avg_Vol_20')).join(avg_adr.rename('ADR_20'))
    merged['RVOL'] = merged['Volume'] / merged['Avg_Vol_20']
    avg_rvol = merged['RVOL'].mean()
    
    # 4. Average Daily Range
    avg_market_adr = merged['ADR_20'].mean()
    
    # --- ROW 1: KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌅 Gap Ups vs Downs", f"{gap_ups} / {gap_downs}")
    col2.metric("💸 Total Index Turnover", f"₹{total_turnover_cr:,.0f} Cr")
    col3.metric("📊 Average RVOL", f"{avg_rvol:.2f}x")
    col4.metric("🎢 Average Daily Range", f"{avg_market_adr:.2f}%")
    
    st.write("") # Spacer
    
    # --- ROW 2: Top Movers & Money Flow ---
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

# Alphabetical List combining Dynamic and Static indicators
FILTER_OPTIONS = [
    "Accumulation/Distribution", 
    "ADX (Dynamic)", 
    "Aroon Oscillator", 
    "Awesome Oscillator", 
    "Balance of Power", 
    "Bollinger Bands (Dynamic)", 
    "CCI (20)", 
    "Chaikin Money Flow", 
    "Chaikin Volatility (10)", 
    "Chande Momentum (CMO)", 
    "Detrended Price Oscillator (20)", 
    "Disparity Index (14)", 
    "Ease of Movement (14)", 
    "Elder Ray Index", 
    "EMA (Dynamic)", 
    "High Low Bands", 
    "Highest High Value (14)", 
    "Ichimoku Cloud", 
    "Keltner Channels", 
    "Lowest Low Value (14)", 
    "MACD", 
    "Median Price", 
    "MFI (14)", 
    "Momentum (10)", 
    "Moving Average Envelope (20)", 
    "Negative Volume Index", 
    "Parabolic SAR", 
    "Performance Index", 
    "Positive Volume Index", 
    "PPO", 
    "Price Volume Trend", 
    "RSI (Dynamic)", 
    "SMA (Dynamic)", 
    "Standard Deviation (20)", 
    "Stochastic %K", 
    "Stochastic RSI", 
    "True Range", 
    "Typical Price", 
    "Ulcer Index (14)", 
    "Ultimate Oscillator", 
    "Volume Oscillator", 
    "Volume ROC (14)", 
    "Vortex Index", 
    "Williams %R"
]

active_filters = st.sidebar.multiselect("Select indicators to add to your screener:", FILTER_OPTIONS)

# =====================================================================
# 6. DYNAMIC RUNTIME CALCULATIONS & FILTERING
# =====================================================================
st.sidebar.markdown("### Active Settings")
if not active_filters:
    st.sidebar.info("Select an indicator from the dropdown above to start.")

# IMPORTANT: Sort by Ticker and Date to ensure on-the-fly rolling math is accurate
df = df.sort_values(['Ticker', 'Date'])
display_cols = ['Date', 'Ticker', 'Close']

# ---------------------------------------------------------
# DYNAMIC INDICATORS (Calculated Live based on User Input)
# ---------------------------------------------------------
if "SMA (Dynamic)" in active_filters:
    sma_period = st.sidebar.number_input("SMA Period", min_value=2, max_value=500, value=20, step=1)
    col_name = f'SMA_{sma_period}'
    df[col_name] = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(sma_period).mean())
    sma_status = st.sidebar.selectbox(f"Price vs SMA ({sma_period})", ["Above SMA", "Below SMA"])
    display_cols.append(col_name)

if "EMA (Dynamic)" in active_filters:
    ema_period = st.sidebar.number_input("EMA Period", min_value=2, max_value=500, value=21, step=1)
    col_name = f'EMA_{ema_period}'
    df[col_name] = df.groupby('Ticker')['Close'].transform(lambda x: x.ewm(span=ema_period, adjust=False).mean())
    ema_status = st.sidebar.selectbox(f"Price vs EMA ({ema_period})", ["Above EMA", "Below EMA"])
    display_cols.append(col_name)

if "RSI (Dynamic)" in active_filters:
    rsi_period = st.sidebar.number_input("RSI Period", min_value=2, max_value=100, value=14, step=1)
    col_name = f'RSI_{rsi_period}'
    
    delta = df.groupby('Ticker')['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.groupby(df['Ticker']).transform(lambda x: x.ewm(alpha=1/rsi_period, adjust=False).mean())
    avg_loss = loss.groupby(df['Ticker']).transform(lambda x: x.ewm(alpha=1/rsi_period, adjust=False).mean())
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    df[col_name] = 100 - (100 / (1 + rs))
    
    min_rsi, max_rsi = st.sidebar.slider(f"RSI ({rsi_period}) Range", 0.0, 100.0, (30.0, 70.0))
    display_cols.append(col_name)

if "Bollinger Bands (Dynamic)" in active_filters:
    bb_period = st.sidebar.number_input("Bollinger Period", min_value=5, max_value=100, value=20, step=1)
    bb_std = st.sidebar.number_input("Standard Deviations", min_value=1.0, max_value=4.0, value=2.0, step=0.1)
    
    upper_col = f'BB_Upper_{bb_period}'
    lower_col = f'BB_Lower_{bb_period}'
    
    sma_temp = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(bb_period).mean())
    std_temp = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(bb_period).std())
    
    df[upper_col] = sma_temp + (std_temp * bb_std)
    df[lower_col] = sma_temp - (std_temp * bb_std)
    
    bb_status = st.sidebar.selectbox(f"Bollinger Bands ({bb_period},{bb_std})", ["Bullish Breakout (Above Upper)", "Bearish Breakout (Below Lower)", "Inside Bands"])
    display_cols.extend([upper_col, lower_col])

if "ADX (Dynamic)" in active_filters:
    adx_period = st.sidebar.number_input("ADX Period", min_value=5, max_value=100, value=14, step=1)
    col_name = f'ADX_{adx_period}'
    
    df['up_move'] = df.groupby('Ticker')['High'].diff()
    df['down_move'] = df.groupby('Ticker')['Low'].shift(1) - df['Low']
    df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0.0)
    df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0.0)
    
    tr1 = df['High'] - df['Low']
    tr2 = np.abs(df['High'] - df.groupby('Ticker')['Close'].shift(1))
    tr3 = np.abs(df['Low'] - df.groupby('Ticker')['Close'].shift(1))
    df['tr'] = np.maximum(tr1, np.maximum(tr2, tr3))
    
    df['tr_smooth'] = df.groupby('Ticker')['tr'].transform(lambda x: x.ewm(alpha=1/adx_period, adjust=False).mean())
    df['plus_dm_smooth'] = df.groupby('Ticker')['plus_dm'].transform(lambda x: x.ewm(alpha=1/adx_period, adjust=False).mean())
    df['minus_dm_smooth'] = df.groupby('Ticker')['minus_dm'].transform(lambda x: x.ewm(alpha=1/adx_period, adjust=False).mean())
    
    df['plus_di'] = 100 * (df['plus_dm_smooth'] / df['tr_smooth'])
    df['minus_di'] = 100 * (df['minus_dm_smooth'] / df['tr_smooth'])
    df['dx'] = (np.abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])) * 100
    df[col_name] = df.groupby('Ticker')['dx'].transform(lambda x: x.ewm(alpha=1/adx_period, adjust=False).mean())
    
    min_adx = st.sidebar.slider(f"Minimum ADX ({adx_period}) Strength", 0.0, 100.0, 25.0)
    display_cols.append(col_name)

# ---------------------------------------------------------
# APPLY ALL FILTERS AND SLICE TIMEFRAME
# ---------------------------------------------------------
# Slice timeframe AFTER rolling calculations are complete to prevent data loss
filtered_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()

# Apply Dynamic Filters
if "SMA (Dynamic)" in active_filters:
    col = f'SMA_{sma_period}'
    if sma_status == "Above SMA":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data[col]]
    else:
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data[col]]

if "EMA (Dynamic)" in active_filters:
    col = f'EMA_{ema_period}'
    if ema_status == "Above EMA":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data[col]]
    else:
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data[col]]

if "RSI (Dynamic)" in active_filters:
    col = f'RSI_{rsi_period}'
    filtered_data = filtered_data[(filtered_data[col] >= min_rsi) & (filtered_data[col] <= max_rsi)]

if "Bollinger Bands (Dynamic)" in active_filters:
    upper = f'BB_Upper_{bb_period}'
    lower = f'BB_Lower_{bb_period}'
    if bb_status == "Bullish Breakout (Above Upper)":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data[upper]]
    elif bb_status == "Bearish Breakout (Below Lower)":
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data[lower]]
    else:
        filtered_data = filtered_data[(filtered_data['Close'] <= filtered_data[upper]) & (filtered_data['Close'] >= filtered_data[lower])]

if "ADX (Dynamic)" in active_filters:
    col = f'ADX_{adx_period}'
    filtered_data = filtered_data[filtered_data[col] >= min_adx]

# Apply Static Filters
if "Accumulation/Distribution" in active_filters:
    display_cols.append('Acc_Dist')

if "Aroon Oscillator" in active_filters:
    aroon_status = st.sidebar.selectbox("Aroon Oscillator", ["Positive (Bullish)", "Negative (Bearish)"])
    if aroon_status == "Positive (Bullish)":
        filtered_data = filtered_data[filtered_data['Aroon_Osc'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['Aroon_Osc'] < 0]
    display_cols.append('Aroon_Osc')

if "Awesome Oscillator" in active_filters:
    ao_status = st.sidebar.selectbox("Awesome Oscillator", ["Above Zero (Bullish)", "Below Zero (Bearish)"])
    if ao_status == "Above Zero (Bullish)":
        filtered_data = filtered_data[filtered_data['Awesome_Osc'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['Awesome_Osc'] < 0]
    display_cols.append('Awesome_Osc')

if "Balance of Power" in active_filters:
    bop_status = st.sidebar.selectbox("Balance of Power", ["Buyers in Control (> 0)", "Sellers in Control (< 0)"])
    if bop_status == "Buyers in Control (> 0)":
        filtered_data = filtered_data[filtered_data['Balance_Of_Power'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['Balance_Of_Power'] < 0]
    display_cols.append('Balance_Of_Power')

if "CCI (20)" in active_filters:
    min_cci, max_cci = st.sidebar.slider("CCI (20) Range", -300.0, 300.0, (-100.0, 100.0))
    filtered_data = filtered_data[(filtered_data['CCI_20'] >= min_cci) & (filtered_data['CCI_20'] <= max_cci)]
    display_cols.append('CCI_20')

if "Chaikin Money Flow" in active_filters:
    cmf_status = st.sidebar.selectbox("Chaikin Money Flow (20)", ["Positive (Buying Pressure)", "Negative (Selling Pressure)"])
    if cmf_status == "Positive (Buying Pressure)":
        filtered_data = filtered_data[filtered_data['CMF_20'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['CMF_20'] < 0]
    display_cols.append('CMF_20')

if "Chaikin Volatility (10)" in active_filters:
    min_cv = st.sidebar.slider("Minimum Chaikin Volatility %", -50.0, 50.0, 0.0)
    filtered_data = filtered_data[filtered_data['Chaikin_Volatility_10'] >= min_cv]
    display_cols.append('Chaikin_Volatility_10')

if "Chande Momentum (CMO)" in active_filters:
    cmo_status = st.sidebar.selectbox("CMO Trend", ["Overbought (> 50)", "Oversold (< -50)", "Neutral"])
    if cmo_status == "Overbought (> 50)":
        filtered_data = filtered_data[filtered_data['CMO_14'] > 50]
    elif cmo_status == "Oversold (< -50)":
        filtered_data = filtered_data[filtered_data['CMO_14'] < -50]
    else:
        filtered_data = filtered_data[(filtered_data['CMO_14'] <= 50) & (filtered_data['CMO_14'] >= -50)]
    display_cols.append('CMO_14')

if "Detrended Price Oscillator (20)" in active_filters:
    dpo_status = st.sidebar.selectbox("DPO (20) Zero-Line", ["Above Zero (Bullish)", "Below Zero (Bearish)"])
    if dpo_status == "Above Zero (Bullish)":
        filtered_data = filtered_data[filtered_data['DPO_20'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['DPO_20'] < 0]
    display_cols.append('DPO_20')

if "Disparity Index (14)" in active_filters:
    display_cols.append('Disparity_Index_14')

if "Ease of Movement (14)" in active_filters:
    eom_status = st.sidebar.selectbox("EOM (14)", ["Positive (Accumulation)", "Negative (Distribution)"])
    if eom_status == "Positive (Accumulation)":
        filtered_data = filtered_data[filtered_data['EOM_14'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['EOM_14'] < 0]
    display_cols.append('EOM_14')

if "Elder Ray Index" in active_filters:
    display_cols.extend(['Elder_Ray_Bull', 'Elder_Ray_Bear'])

if "High Low Bands" in active_filters:
    display_cols.extend(['High_Band_14', 'Low_Band_14'])

if "Highest High Value (14)" in active_filters:
    display_cols.append('Highest_High_14')

if "Ichimoku Cloud" in active_filters:
    ichimoku_status = st.sidebar.selectbox("Ichimoku Trend", ["Price Above Cloud (Bullish)", "Price Below Cloud (Bearish)"])
    if ichimoku_status == "Price Above Cloud (Bullish)":
        filtered_data = filtered_data[(filtered_data['Close'] > filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] > filtered_data['Ichimoku_Span_B'])]
    else:
        filtered_data = filtered_data[(filtered_data['Close'] < filtered_data['Ichimoku_Span_A']) & (filtered_data['Close'] < filtered_data['Ichimoku_Span_B'])]
    display_cols.extend(['Ichimoku_Span_A', 'Ichimoku_Span_B'])

if "Keltner Channels" in active_filters:
    kc_status = st.sidebar.selectbox("Keltner Channels", ["Above Upper Band", "Below Lower Band"])
    if kc_status == "Above Upper Band":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data['Keltner_Upper']]
    else:
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data['Keltner_Lower']]
    display_cols.extend(['Keltner_Upper', 'Keltner_Lower'])

if "Lowest Low Value (14)" in active_filters:
    display_cols.append('Lowest_Low_14')

if "MACD" in active_filters:
    macd_status = st.sidebar.selectbox("MACD Signal", ["Bullish (MACD > Signal)", "Bearish (MACD < Signal)"])
    if macd_status == "Bullish (MACD > Signal)":
        filtered_data = filtered_data[filtered_data['MACD'] > filtered_data['MACD_Signal']]
    else:
        filtered_data = filtered_data[filtered_data['MACD'] < filtered_data['MACD_Signal']]
    display_cols.extend(['MACD', 'MACD_Signal'])

if "Median Price" in active_filters:
    display_cols.append('Median_Price')

if "MFI (14)" in active_filters:
    min_mfi, max_mfi = st.sidebar.slider("Money Flow Index", 0.0, 100.0, (20.0, 80.0))
    filtered_data = filtered_data[(filtered_data['MFI_14'] >= min_mfi) & (filtered_data['MFI_14'] <= max_mfi)]
    display_cols.append('MFI_14')

if "Momentum (10)" in active_filters:
    mom_status = st.sidebar.selectbox("Momentum (10)", ["Positive", "Negative"])
    if mom_status == "Positive":
        filtered_data = filtered_data[filtered_data['Momentum_10'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['Momentum_10'] < 0]
    display_cols.append('Momentum_10')

if "Moving Average Envelope (20)" in active_filters:
    mae_status = st.sidebar.selectbox("MAE (20, 5%)", ["Above Upper Band", "Below Lower Band", "Inside Bands"])
    if mae_status == "Above Upper Band":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data['MAE_Upper_20']]
    elif mae_status == "Below Lower Band":
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data['MAE_Lower_20']]
    else:
        filtered_data = filtered_data[(filtered_data['Close'] <= filtered_data['MAE_Upper_20']) & (filtered_data['Close'] >= filtered_data['MAE_Lower_20'])]
    display_cols.extend(['MAE_Upper_20', 'MAE_Lower_20'])

if "Negative Volume Index" in active_filters:
    display_cols.append('NVI')

if "Parabolic SAR" in active_filters:
    psar_status = st.sidebar.selectbox("Parabolic SAR", ["Bullish (Price > PSAR)", "Bearish (Price < PSAR)"])
    if psar_status == "Bullish (Price > PSAR)":
        filtered_data = filtered_data[filtered_data['Close'] > filtered_data['PSAR']]
    else:
        filtered_data = filtered_data[filtered_data['Close'] < filtered_data['PSAR']]
    display_cols.append('PSAR')

if "Performance Index" in active_filters:
    display_cols.append('Performance_Index')

if "Positive Volume Index" in active_filters:
    display_cols.append('PVI')

if "PPO" in active_filters:
    ppo_status = st.sidebar.selectbox("PPO Signal", ["Positive Momentum (> 0)", "Negative Momentum (< 0)"])
    if ppo_status == "Positive Momentum (> 0)":
        filtered_data = filtered_data[filtered_data['PPO'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['PPO'] < 0]
    display_cols.append('PPO')

if "Price Volume Trend" in active_filters:
    display_cols.append('PVT')

if "Standard Deviation (20)" in active_filters:
    display_cols.append('Std_Dev_20')

if "Stochastic %K" in active_filters:
    min_stoch, max_stoch = st.sidebar.slider("Stochastic %K Range", 0.0, 100.0, (20.0, 80.0))
    filtered_data = filtered_data[(filtered_data['Stoch_%K'] >= min_stoch) & (filtered_data['Stoch_%K'] <= max_stoch)]
    display_cols.append('Stoch_%K')

if "Stochastic RSI" in active_filters:
    min_srsi, max_srsi = st.sidebar.slider("Stochastic RSI Range", 0.0, 100.0, (20.0, 80.0))
    filtered_data = filtered_data[(filtered_data['Stoch_RSI'] >= min_srsi) & (filtered_data['Stoch_RSI'] <= max_srsi)]
    display_cols.append('Stoch_RSI')

if "True Range" in active_filters:
    display_cols.append('True_Range')

if "Typical Price" in active_filters:
    display_cols.append('Typical_Price')

if "Ulcer Index (14)" in active_filters:
    max_ulcer = st.sidebar.slider("Max Ulcer Index (Risk/Drawdown %)", 0.0, 50.0, 10.0)
    filtered_data = filtered_data[filtered_data['Ulcer_Index_14'] <= max_ulcer]
    display_cols.append('Ulcer_Index_14')

if "Ultimate Oscillator" in active_filters:
    min_uo, max_uo = st.sidebar.slider("Ultimate Oscillator Range", 0.0, 100.0, (30.0, 70.0))
    filtered_data = filtered_data[(filtered_data['Ultimate_Osc'] >= min_uo) & (filtered_data['Ultimate_Osc'] <= max_uo)]
    display_cols.append('Ultimate_Osc')

if "Volume Oscillator" in active_filters:
    vo_status = st.sidebar.selectbox("Volume Oscillator", ["Positive (Expanding)", "Negative (Contracting)"])
    if vo_status == "Positive (Expanding)":
        filtered_data = filtered_data[filtered_data['Volume_Osc'] > 0]
    else:
        filtered_data = filtered_data[filtered_data['Volume_Osc'] < 0]
    display_cols.append('Volume_Osc')

if "Volume ROC (14)" in active_filters:
    min_vroc = st.sidebar.slider("Minimum Volume Spike % (VROC)", -100.0, 500.0, 50.0)
    filtered_data = filtered_data[filtered_data['Volume_ROC_14'] >= min_vroc]
    display_cols.append('Volume_ROC_14')

if "Vortex Index" in active_filters:
    vi_status = st.sidebar.selectbox("Vortex Trend", ["Bullish (VI+ > VI-)", "Bearish (VI- > VI+)"])
    if vi_status == "Bullish (VI+ > VI-)":
        filtered_data = filtered_data[filtered_data['Vortex_Pos'] > filtered_data['Vortex_Neg']]
    else:
        filtered_data = filtered_data[filtered_data['Vortex_Pos'] < filtered_data['Vortex_Neg']]
    display_cols.extend(['Vortex_Pos', 'Vortex_Neg'])

if "Williams %R" in active_filters:
    min_will, max_will = st.sidebar.slider("Williams %R", -100.0, 0.0, (-80.0, -20.0))
    filtered_data = filtered_data[(filtered_data['Williams_%R'] >= min_will) & (filtered_data['Williams_%R'] <= max_will)]
    display_cols.append('Williams_%R')

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
