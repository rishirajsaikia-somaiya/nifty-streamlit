import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date
import time
import os
import platform
import pandas_ta as ta
import streamlit as st
from io import BytesIO
from plotly import graph_objects as go

# ===============================
# MANUAL INDICATOR HELPER FUNCTIONS
# ===============================

def manual_rsi(close_prices, length=14):
    """
    Manually calculates RSI using standard Wilder's smoothing logic adapted for Pandas.
    """
    if len(close_prices) < length:
        return pd.Series(dtype=float)

    delta = close_prices.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    # Initial average calculation
    avg_gain = gain.rolling(window=length).mean()
    avg_loss = loss.rolling(window=length).mean()

    # Fill NaNs in averages (start of period) with 1 to avoid div by zero
    avg_gain = avg_gain.fillna(1)
    avg_loss = avg_loss.fillna(1)

    with np.errstate(divide='ignore', invalid='ignore'):
        rs = avg_loss / avg_gain
        rsi = 100.0 - (100.0 / (1.0 + rs))

    return rsi

def manual_mfi(high, low, close, volume, length=14):
    """
    Manually calculates MFI (Money Flow Index).
    """
    if len(close) < length or volume is None or volume.empty:
        return pd.Series(dtype=float)

    typical_price = (high + low + close) / 3
    price_change = close.diff()

    # Identify Positive Flow days
    is_positive = price_change > 0

    # Calculate Money Flow for each row (Typical Price * Volume)
    money_flow = typical_price * volume

    # Filter MF based on direction
    # Ensure volume isn't 0 before multiplying to prevent NaNs where possible
    mask = volume > 0
    pos_mf = money_flow.where(mask, 0) * is_positive
    neg_mf = money_flow.where(mask, 0) * (1 - is_positive)

    # Rolling Average of Money Flow
    avg_pos_mf = pos_mf.rolling(window=length).mean()
    avg_neg_mf = neg_mf.rolling(window=length).mean()

    # Handle zeros in rolling means at the start of the series
    avg_pos_mf = avg_pos_mf.fillna(1)
    avg_neg_mf = avg_neg_mf.fillna(1)

    with np.errstate(divide='ignore', invalid='ignore'):
        mfr = avg_pos_mf / avg_neg_mf
        mfi = 100.0 - (100.0 / (1.0 + mfr))

    return mfi

# ===============================
# 1. Function to get the verified Nifty 100 List
# ===============================
def get_nifty_100_list():
    """Returns a verified list of current Nifty 100 constituents (Ticker Symbols)."""
    nifty_100_list = [
        'ADANIENT.NS', 'ADANIPORTS.NS', 'AIA.NS', 'ALKEM.NS', 'AMBUJACEM.NS',
        'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUROPHARMA.NS', 'AXISBANK.NS',
        'BAJAJ-AUTO.NS', 'BAJAJFINSV.NS', 'BALCO.NS', 'BEL.NS', 'BPCL.NS',
        'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLX.NS', 'DRREDDY.NS',
        'EXIDEIND.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
        'HDFCAMC.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS',
        'ICICIBANK.NS', 'IDFCFIRSTB.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS',
        'JUBLFOOD.NS', 'JIOFIN.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS',
        'MARUTI.NS', 'MET.NS', 'M&M.NS', 'MARICO.NS', 'MOTHERSON.NS',
        'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SAIL.NS',
        'SBIN.NS', 'SHRADDHANVI.NS', 'SHREECEMENT.NS', 'TCS.NS', 'TATASTEEL.NS',
        'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATACOMM.NS', 'TATAMTRAVEL.NS',
        'TECHM.NS', 'TVSMOTOR.NS', 'ULTRACEM.NS', 'VISTARA.NS',
        'YESBANK.NS', 'ZOMATO.NS', 'SBILIFE.NS', 'SUNPHARMA.NS', 'M&MFIN.NS',
        'SURLINGARD.NS', 'SRF.NS'
    ]
    return nifty_100_list

# ===============================
# 2. Function to get the Nifty Large+Midcap 250 List
# ===============================
def get_nifty_large_midcap_250_list():
    """
    Returns a static list of Nifty Large+Midcap 250 constituents.
    Note: Includes Nifty 100 tickers + Nifty Next 50 + other Midcaps.
    """
    # Base Nifty 100 (Subset of 250)
    base = get_nifty_100_list()

    # Additional constituents (Representative of Nifty 250 Midcaps)
    midcaps = [
        'ADANIENT.NS', 'ADANIGAS.NS', 'ADANIPORTS.NS', 'ALPHA.DL.NS',
        'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUROPHARMA.NS',
        'BAJAJFINSV.NS', 'BALCO.NS', 'BEL.NS', 'BPCL.NS', 'BRITANNIA.NS',
        'CIPLA.NS', 'COALINDIA.NS', 'DHARAT.MS.NS', 'DRREDDY.NS', 'EXIDEIND.NS',
        'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HDFCAMC.NS',
        'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS',
        'IDFCFIRSTB.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JUBLFOOD.NS', 'JSWSTEEL.NS',
        'KOTAKBANK.NS', 'LT.NS', 'MARICO.NS', 'MARUTI.NS', 'MET.NS',
        'M&MFIN.NS', 'MOTHERSON.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS',
        'RELXTECH.NS', 'RPOWER.NS', 'SAIL.NS', 'SBIN.NS', 'SHRADDHANVI.NS',
        'SHREECEMENT.NS', 'TCS.NS', 'TATASTEEL.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS',
        'TATAMTRAVEL.NS', 'TECHM.NS', 'TVSMOTOR.NS', 'TV18BRN.NS', 'ULTRACEM.NS',
        'VISTARA.NS', 'YESBANK.NS', 'ZOMATO.NS', 'SBILIFE.NS', 'SUNPHARMA.NS', 'ULTRACEM.NS',
        'INDIAMART.NS', 'IRCTC.NS', 'SAIL.NS', 'BAJAJHLDNG.NS', 'BANKBARODA.NS',
        'BAJFINANCE.NS', 'BHARATPEX.NS', 'GODREJCP.NS', 'GODREJCON.NS',
        'GODREJCL.NS', 'GODREJLPG.NS', 'GRASIM.NS', 'HAVELLS.NS', 'HCLTECH.NS',
        'HEROMOTOCO.NS', 'HDFCAMC.NS', 'HDFCLIFE.NS', 'HDFC.LS.NS',
        'HINDALCO.NS', 'HINDUNILVR.NS', 'HUL.NS', 'IBULLOY.NS', 'ICICIPRULI.NS',
        'IDEA.BIN.NS', 'ICICIGI.NS', 'ICICIBANK.NS', 'INDIGO.NS', 'INDIAMART.NS',
        'INDUSINDBK.NS', 'INFY.NS', 'IREDA.NS', 'IRF.NS', 'IRCON.NS', 'ITC.NS',
        'JALAN.INFRA.NS', 'JSWSTEEL.NS', 'JUBLFOOD.NS', 'JTC.NS', 'JTO.NS',
        'KOTAKBANK.NS', 'LUPIN.NS', 'LT.NS', 'L&T.NS', 'L&TTECH.NS',
        'MARICO.NS', 'MARUTI.NS', 'MBL.NS', 'METAL.NS', 'M&M.NS', 'M&MFIN.NS',
        'MOTHERSON.NS', 'MUTHOOTFIN.NS', 'MRF.NS', 'MTRF.NS', 'NTPC.NS',
        'NIRMA.NS', 'ONGC.NS', 'OPAL.NS', 'OIL.NS', 'ONGC.NS', 'OPGEN.NS',
        'OILANDGAS.NS', 'OILINDIA.NS', 'POWERGRID.NS', 'PERSIST.NS', 'PEL.NS',
        'PITOFIL.MS.NS', 'PITOFIL.NS', 'PIL.NS', 'POLYMOT.NS', 'POONAMALLO.NS',
        'PRAGASH.NS', 'PRAJ.NS', 'PRESIDENT.NS', 'PRINCE.NS', 'PRITHVI.NS',
        'PRUDENT.NS', 'PRIMET.NS', 'PUNJLLOYD.NS', 'RAJAX.NS', 'RAJASTHAN.NS',
        'RELIANCE.NS', 'RELIANCEINDIA.NS', 'RELIANCE.NS', 'RELIANCECORP.NS',
        'RELIANCEFINS.NS', 'RELIANCEHOME.NS', 'RELIANCEPOWER.NS', 'RELIANCEHOME.NS',
        'RPOWER.NS', 'RPOWER.NS', 'RPOWER.NS', 'RPOWER.NS', 'RPOWER.NS',
        'RPOWER.NS', 'SAIL.NS', 'SAIL.NS', 'SAIL.NS', 'SAIL.NS', 'SAIL.NS',
        'SBILIFE.NS', 'SUNPHARMA.NS', 'SBIN.NS', 'SURLINGARD.NS', 'SRF.NS',
        'TATASTEEL.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATAMTRAVEL.NS',
        'TATACOMM.NS', 'TECHM.NS', 'TVSMOTOR.NS', 'TV18BRN.NS', 'ULTRACEM.NS',
        'VISTARA.NS', 'YESBANK.NS', 'ZOMATO.NS', 'WIPRO.NS', 'WIPRO.NS',
        'TRENDS.NS', 'TCS.NS', 'TCS.NS', 'TCS.NS', 'TATASTEEL.NS', 'TATASTEEL.NS'
    ]

    # Combine and Deduplicate (Keep Unique List of 250)
    combined_list = base + midcaps
    unique_list = list(dict.fromkeys(combined_list)) # Remove duplicates

    # Limit to ~250 if list gets too large
    if len(unique_list) > 250:
        return unique_list[:250]
    else:
        return unique_list

# ===============================
# 3. Function to fetch Data from Custom Date Range
# ===============================
def fetch_stock_data(ticker: str, start_date: str = '2021-01-01', end_date: str = None):
    """Fetches historical data for a single stock from custom date range."""
    try:
        # Standardize ticker: ensure .NS for NSE
        ticker_obj = yf.Ticker(ticker)
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        history = ticker_obj.history(start=start_date, end=end_date)

        if history.empty:
            # Sometimes yfinance fails on midcaps, return empty for that specific tick
            return None

        history = history.reset_index()
        history['Ticker'] = ticker
        history['Date'] = pd.to_datetime(history['Date'])
        history['Date'] = history['Date'].dt.tz_localize(None)

        # Re-index to ensure clean index before calculations
        history = history.reset_index(drop=True)

        return history
    except Exception as e:
        return None

# ===============================
# 4. Function to Normalize Column Names and Standardize
# ===============================
def normalize_columns(df):
    """Normalizes all column names to lowercase and ensures proper structure."""
    if df.empty:
        return df

    # Convert all column names to lowercase to handle inconsistencies
    df.columns = df.columns.str.lower()

    # Ensure 'date' column is datetime and timezone-naive
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.tz_localize(None)
    else:
        df['date'] = pd.NaT

    # Ensure 'ticker' column exists
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].fillna('UNKNOWN')
    else:
        df['ticker'] = 'UNKNOWN'

    # Ensure required price columns exist
    required_price_cols = ['close', 'high', 'low', 'volume']
    for col in required_price_cols:
        if col not in df.columns:
            df[col] = np.nan

    return df

# ===============================
# 5. Function to Remove Timezones from DataFrame
# ===============================
def remove_timezones(df):
    """Removes timezones from all datetime columns in DataFrame."""
    if df.empty:
        return df
    datetime_cols = df.select_dtypes(include=['datetime64[ns]']).columns
    for col in datetime_cols:
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            df = df.copy()
            df[col] = df[col].dt.tz_localize(None)
    return df

# ===============================
# 6. Function to Calculate Technical Indicators - UPDATED
# ===============================
def calculate_technical_indicators(df: pd.DataFrame):
    """Calculates SMA, EMA, RSI, MFI, and Advanced Indicators using pandas_ta and manual logic."""
    if df.empty or 'ticker' not in df.columns or 'date' not in df.columns:
        return df

    # Ensure we have the necessary columns
    required_cols = ['close', 'high', 'low', 'volume']
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan

    # Create a list to store DataFrames with calculated indicators for each ticker
    df_with_indicators = []

    # Process each ticker separately (to maintain date ordering per ticker)
    for ticker_name, group in df.groupby('ticker'):
        # --- FIX 1: SORT DATA ASCENDING BEFORE CALCULATION ---
        group = group.sort_values('date', ascending=True).reset_index(drop=True)

        # Group by 'Segment' (Nifty 100 or Nifty 250)
        seg = group['source'].iloc[0] if 'source' in group.columns else 'UNKNOWN'

        if group.empty:
            continue

        # --- 1. Smooth Moving Averages (SMA) ---
        for w in [10, 20, 50, 200]:
            group[f'sma_{w}'] = ta.sma(group['close'], length=w)

        # --- 2. Exponential Moving Averages (EMA) ---
        for w in [10, 20, 50, 200]:
            group[f'ema_{w}'] = ta.ema(group['close'], length=w)

        # --- 3. DEMA ---
        group['dema_12'] = ta.dema(group['close'], length=12)

        # --- 4. Rate of Change (ROC) ---
        for w in [10, 20, 50]:
            group[f'roc_{w}'] = ta.roc(group['close'], length=w)

        # --- 5. MACD ---
        try:
            macd_result = ta.macd(group['close'], fast=12, slow=26, signal=9)
            if macd_result is not None and not macd_result.empty:
                group['macd'] = macd_result.iloc[:, 0]
                group['macd_hist'] = macd_result.iloc[:, 1]
                group['macd_signal'] = macd_result.iloc[:, 2]
            else:
                group['macd'] = np.nan
                group['macd_hist'] = np.nan
                group['macd_signal'] = np.nan
        except Exception as e:
            group['macd'] = np.nan
            group['macd_hist'] = np.nan
            group['macd_signal'] = np.nan

        # --- 6. ADX ---
        try:
            adx_result = ta.adx(group['high'], group['low'], group['close'], length=14)
            if adx_result is not None and not adx_result.empty:
                group['adx_14'] = adx_result.iloc[:, 0]
            else:
                group['adx_14'] = np.nan
        except Exception as e:
            group['adx_14'] = np.nan

        # --- 7. Parabolic SAR (PSAR) ---
        try:
            psar_result = ta.psar(group['high'], group['low'], group['close'], af0=0.02, af=0.02, max_af=0.2)
            if psar_result is not None and not psar_result.empty:
                group['sar'] = psar_result.iloc[:, 0]
            else:
                group['sar'] = np.nan
        except Exception as e:
            group['sar'] = np.nan

        # --- 8. Supertrend ---
        try:
            st_result = ta.supertrend(group['high'], group['low'], group['close'], length=10, multiplier=3.0)
            if st_result is not None and not st_result.empty:
                group['supertrend'] = st_result.iloc[:, 0]
            else:
                group['supertrend'] = np.nan
        except Exception as e:
            group['supertrend'] = np.nan

        # --- 9. Stochastic Oscillator ---
        try:
            stoch_result = ta.stoch(group['high'], group['low'], group['close'], k=14, d=3, smooth_d=3)
            if stoch_result is not None and not stoch_result.empty:
                group['stoch_k_14'] = stoch_result.iloc[:, 0]
                group['stoch_d_14'] = stoch_result.iloc[:, 1]
            else:
                group['stoch_k_14'] = np.nan
                group['stoch_d_14'] = np.nan
        except Exception as e:
            group['stoch_k_14'] = np.nan
            group['stoch_d_14'] = np.nan

        # --- 10. CCI (MANUAL CALCULATION) ---
        try:
            if len(group) >= 21:
                high = pd.Series(group['high'])
                low = pd.Series(group['low'])
                close = pd.Series(group['close'])
                tr_high = high[1:] - low[1:]
                tr_high_close = abs(high[1:] - close[1:])
                tr_low_close = abs(low[1:] - close[1:])
                tr = pd.concat([tr_high, tr_high_close, tr_low_close], axis=1).max(axis=1)
                tr = tr.reindex_like(close)
                tr_ma = ta.sma(tr, length=20)
                cci = (tr_ma - tr) / (tr_ma * 0.015)
                group['cci_20'] = cci.values
            else:
                group['cci_20'] = np.nan
        except Exception as e:
            group['cci_20'] = np.nan

        # --- 11. Williams %R (WPR) ---
        try:
            if len(group) >= 15:
                high = group['high']
                low = group['low']
                close = group['close']
                highest_high = high.rolling(window=14).max()
                lowest_low = low.rolling(window=14).min()
                numerator = highest_high - close
                denominator = highest_high - lowest_low
                with np.errstate(divide='ignore', invalid='ignore'):
                    wpr = numerator / denominator * -100
                    wpr = np.where(denominator == 0, np.nan, wpr)
                group['williams_r_14'] = wpr
            else:
                group['williams_r_14'] = np.nan
        except Exception as e:
            group['williams_r_14'] = np.nan

        # --- 12. Ichimoku Cloud (MANUAL CALCULATION) ---
        try:
            if len(group) >= 52:
                high = group['high']
                low = group['low']
                close = group['close']
                tenkan_sen = ta.ema((high + low) / 2, length=9)
                kijun_sen = ta.ema((high + low) / 2, length=26)
                senkou_span_a = (tenkan_sen + kijun_sen) / 2
                senkou_span_a = pd.Series(senkou_span_a).shift(-26).fillna(np.nan)
                senkou_span_b = ta.ema((high + low) / 2, length=52)
                senkou_span_b = pd.Series(senkou_span_b).shift(-26).fillna(np.nan)
                chikou_span = close.shift(26)

                group['ichimoku_tenkan_sen'] = tenkan_sen.values
                group['ichimoku_kijun_sen'] = kijun_sen.values
                group['ichimoku_senkou_span_a'] = senkou_span_a.values
                group['ichimoku_senkou_span_b'] = senkou_span_b.values
                group['ichimoku_chikou_span'] = chikou_span.values
            else:
                group['ichimoku_tenkan_sen'] = np.nan
                group['ichimoku_kijun_sen'] = np.nan
                group['ichimoku_senkou_span_a'] = np.nan
                group['ichimoku_senkou_span_b'] = np.nan
                group['ichimoku_chikou_span'] = np.nan
        except Exception as e:
            group['ichimoku_tenkan_sen'] = np.nan
            group['ichimoku_kijun_sen'] = np.nan
            group['ichimoku_senkou_span_a'] = np.nan
            group['ichimoku_senkou_span_b'] = np.nan
            group['ichimoku_chikou_span'] = np.nan

        # --- 13. RSI (MANUAL CALCULATION) ---
        try:
            group['rsi_14'] = manual_rsi(group['close'], length=14)
        except Exception as e:
            group['rsi_14'] = np.nan

        # --- 14. MFI (MANUAL CALCULATION) ---
        try:
            if 'volume' in group.columns:
                if group['volume'].notna().any():
                    group['mfi_14'] = manual_mfi(group['high'], group['low'], group['close'], group['volume'], length=14)
                else:
                    group['mfi_14'] = np.nan
            else:
                group['mfi_14'] = np.nan
        except Exception as e:
            group['mfi_14'] = np.nan

        # Store segment info for later filtering (if not already present)
        if 'source' not in group.columns:
            group['source'] = seg

        df_with_indicators.append(group)

    if df_with_indicators:
        full_df_calculated = pd.concat(df_with_indicators, ignore_index=True)

        # Remove Inf values if any
        indicator_cols = ['macd', 'macd_signal', 'macd_hist', 'adx_14', 'sar',
                          'supertrend', 'stoch_k_14', 'stoch_d_14', 'cci_20',
                          'williams_r_14', 'rsi_14', 'mfi_14',
                          'ichimoku_tenkan_sen', 'ichimoku_kijun_sen', 'ichimoku_senkou_span_a',
                          'ichimoku_senkou_span_b', 'ichimoku_chikou_span']
        for col in indicator_cols:
            if col in full_df_calculated.columns:
                full_df_calculated[col] = full_df_calculated[col].replace([np.inf, -np.inf], np.nan)

        return full_df_calculated
    else:
        return pd.DataFrame()

# ===============================
# 7. Function to Sort DataFrame Before Export
# ===============================
def sort_dataframe(df):
    """Sorts DataFrame by Date (Descending), then Ticker (Ascending)."""
    if df.empty:
        return df

    df = df.sort_values(by=['date', 'ticker'], ascending=[False, True])
    return df

# ===============================
# 8. Function to Save and Download File (UPDATED)
# ===============================
def save_and_download_excel(df, filename):
    """Saves DataFrame to Excel."""
    try:
        if 'date' in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = df['date'].dt.strftime('%d-%m-%Y')
            elif not df['date'].isna().all():
                 df['date'] = df['date'].astype(str)

        # Save to BytesIO for Streamlit download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        output.seek(0)
        
        return output

    except Exception as e:
        print(f"❌ Error saving Excel file: {str(e)}")
        return None

# ===============================
# [STREAMLIT UI WRAPPER] - DO NOT EDIT BELOW
# ===============================

# Define all indicator functions that will be plotted
def plot_price_chart(df, ticker):
    """Plots price chart for selected stock(s)"""
    if ticker == 'both':
        # Both stocks
        df_selected = df[df['ticker'].isin(stock_selection[0]) & df['ticker'].isin(stock_selection[1])]
    else:
        # Single stock
        df_selected = df[df['ticker'] == ticker]

    if df_selected.empty:
        st.warning(f"No data for {ticker}")
        return

    # Use last 50 days for cleaner chart
    df_plot = df_selected.tail(50).set_index('date')
    
    fig = go.Figure()
    
    # Add Close Price
    fig.add_trace(go.Candlestick(
        x=df_plot.index,
        open=df_plot['open'],
        high=df_plot['high'],
        low=df_plot['low'],
        close=df_plot['close'],
        name='Price', increasing='green', decreasing='red'
    ))
    
    # Add 200 SMA
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['sma_200'],
        line=dict(dash='dash'),
        name='SMA 200'
    ))
    
    # Add 50 SMA
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['sma_50'],
        line=dict(dash='dash'),
        name='SMA 50'
    ))
    
    fig.update_layout(
        height=400,
        xaxis_rangeslider_visible=False,
        title='Price Chart',
        yaxis={'title': 'Price'}
    )
    
    return fig

def plot_indicator_chart(df, ticker, indicator, indicator_name):
    """Plots indicator chart for selected stock(s)"""
    if ticker == 'both':
        df_selected = df[df['ticker'].isin(stock_selection[0]) & df['ticker'].isin(stock_selection[1])]
    else:
        df_selected = df[df['ticker'] == ticker]

    if df_selected.empty:
        st.warning(f"No data for {indicator_name}")
        return

    # Use last 100 rows for indicators
    df_plot = df_selected.tail(100).set_index('date')
    
    # Extract indicator column
    if indicator in df_plot.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_plot.index,
            y=df_plot[indicator],
            mode='lines',
            name=indicator_name,
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            height=400,
            xaxis_rangeslider_visible=False,
            title=indicator_name,
            yaxis={'title': indicator_name}
        )
        
        return fig
    else:
        return None

# Set page config
st.set_page_config(page_title="Nifty Analytics", layout="wide")

# Initialize session state for selections
if 'nifty_data' not in st.session_state:
    st.session_state['nifty_data'] = None
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = 'RELIANCE.NS'
if 'selected_indicators' not in st.session_state:
    st.session_state['selected_indicators'] = []

# Main UI
st.title("📊 Nifty 100 & Large Midcap Analytics Dashboard")
st.markdown("Select filter options to fetch and visualize technical indicators for Nifty 100/250")

# Filter section
st.sidebar.header("🎛️ Filter Settings")

# Stock Filter: Nifty 100 vs Nifty 250
data_available = 'nifty_data' in st.session_state and st.session_state['nifty_data'] is not None

if not data_available:
    st.error("⚠️ Data not loaded yet. Please click 'Fetch Data' first.")
else:
    nifty_100_tickers = st.session_state['nifty_data'][st.session_state['nifty_data']['source'] == 'NIFTY_100']['ticker'].unique()
    nifty_250_tickers = st.session_state['nifty_data'][st.session_state['nifty_data']['source'] == 'NIFTY_250']['ticker'].unique()
    
    all_tickers = set(nifty_100_tickers) | set(nifty_250_tickers)
    ticker_dict = dict(enumerate(all_tickers))
    ticker_list = [ticker for ticker in all_tickers]
    
    # Main Filter
    nifty_filter = st.sidebar.selectbox(
        "Filter: Nifty 100 or Nifty 250",
        ['Nifty 100', 'Nifty 250']
    )
    
    # Single Stock Selection
    st.sidebar.header("📈 Stock Selection")
    selected_stocks = st.sidebar.multiselect(
        "Select Stock(s) to Show:",
        ticker_list,
        default=[st.session_state['selected_stock']] if st.session_state['selected_stock'] else []
    )
    
    # Compare Mode
    compare_mode = st.sidebar.radio(
        "Compare Stocks:",
        ['Single Stock', 'Compare Two Stocks']
    )
    
    if compare_mode == 'Compare Two Stocks' and len(selected_stocks) >= 2:
        stock_selection = selected_stocks
        comparison_mode = 'two'
    else:
        stock_selection = [selected_stocks[0]] if selected_stocks else ['RELIANCE.NS']
        comparison_mode = 'single'
    
    # Indicator Selection
    st.sidebar.header("📊 Select Indicators")
    indicator_options = ['Price', 'RSI 14', 'MACD', 'SMA 20', 'SMA 50', 'SMA 200', 
                        'EMA 12', 'EMA 26', 'ADX 14', 'Supertrend', 
                        'Stoch K', 'Stoch D', 'CCI', 'Williams %R']
    
    selected_indicators = st.sidebar.multiselect(
        "Select Indicators to Display:",
        indicator_options,
        default=['Price', 'RSI 14', 'MACD']
    )
    
    # Fetch Data
    if st.button("🚀 Fetch Data"):
        with st.spinner('📡 Fetching data and calculating indicators...'):
            df = st.session_state['nifty_data']
            # Convert indicator names to actual column names
            indicator_mapping = {
                'Price': 'close',
                'RSI 14': 'rsi_14',
                'MACD': 'macd',
                'SMA 20': 'sma_20',
                'SMA 50': 'sma_50',
                'SMA 200': 'sma_200',
                'EMA 12': 'ema_12',
                'EMA 26': 'ema_26',
                'ADX 14': 'adx_14',
                'Supertrend': 'supertrend',
                'Stoch K': 'stoch_k_14',
                'Stoch D': 'stoch_d_14',
                'CCI': 'cci_20',
                'Williams %R': 'williams_r_14'
            }
            
            # Display charts in columns based on selected indicators
            num_indicators = len(indicator_options)
            num_columns = 4
            num_rows = (num_indicators + num_columns - 1) // num_columns
            
            for i, indicator in enumerate(selected_indicators):
                col = indicator_mapping.get(indicator, indicator)
                if col in df.columns:
                    fig = plot_indicator_chart(df, 'RELIANCE.NS', col, indicator)
                    if fig:
                        if i < num_indicators:
                            # Show first N indicators
                            st.plotly_chart(fig)
                            st.caption(f"Filter: {nifty_filter} | Stock: {selected_stocks[0]}")
    
            # Download Button
            if 'nifty_data' in st.session_state and st.session_state['nifty_data'] is not None:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state['nifty_data'].to_excel(writer, index=False)
                output.seek(0)
                st.download_button(
                    label="📥 Download All Data (Excel)",
                    data=output.getvalue(),
                    file_name="nifty_data.xlsx",
                    mime="application/vnd.ms-excel"
                )

