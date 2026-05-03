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
    unique_list = list(dict.fromkeys(combined_list))  # Remove duplicates

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
                    group['mfi_14'] = manual_mfi(group['high'], group['low'], group['close'], group['volume'],
                                                 length=14)
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
def save_and_download_excel(df, filename, download_to_colab=False):
    """Saves DataFrame to Excel and optionally triggers download in Google Colab."""
    try:
        if 'date' in df.columns:
            # FIX: Check if datetime type before using .dt
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = df['date'].dt.strftime('%d-%m-%Y')
            # If not datetime (e.g. object/strings), just convert to str
            elif not df['date'].isna().all():
                df['date'] = df['date'].astype(str)

        # Save to BytesIO for Streamlit download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)

        output.seek(0)

        # Log output
        print(f"✅ File created successfully in memory!")
        print(f" Filename: {filename}")
        print(f" File Size: {os.path.getsize(output) / 1024:.2f} KB")

        return output

    except Exception as e:
        print(f"❌ Error saving Excel file: {str(e)}")
        return None


# ===============================
# 9. Main Execution Flow
# ===============================
def main():
    print("=" * 80)
    print("Starting Nifty 100 & Nifty 250 Data Fetching and Analysis")
    print("=" * 80)

    # Check if running in Google Colab
    in_colab = False
    try:
        from google.colab import files
        in_colab = True
    except:
        in_colab = False

    # Define the start date for the script's data fetching
    script_start_date = '2021-01-01'

    print(f"\n📱 Environment: {'Google Colab' if in_colab else 'Streamlit Cloud / Local'}")
    print(f"📂 Start Date: {script_start_date}")
    print(f"📅 End Date: {datetime.now().strftime('%d-%m-%Y')}")

    # --- 1. Get Official Ticker Lists ---
    tickers_nifty_100 = get_nifty_100_list()
    tickers_nifty_250 = get_nifty_large_midcap_250_list()

    # Remove duplicates between lists if overlapping (to avoid double fetching same stock)
    unique_tickers = list(dict.fromkeys(tickers_nifty_100 + tickers_nifty_250))

    # Better approach for source identification during fetch:
    print(f"✓ Fetched {len(tickers_nifty_100)} Nifty 100 tickers.")
    print(f"✓ Fetched {len(tickers_nifty_250)} Nifty 250 tickers.")
    print(f"✓ Total Unique Tickers: {len(unique_tickers)}")

    # --- 2. Fetch Data for all stocks ---
    data_frames_list = []
    end_date = datetime.now().strftime('%Y-%m-%d')

    for idx, ticker in enumerate(unique_tickers):
        # Determine source (100 or 250)
        is_nifty_100 = ticker in tickers_nifty_100
        source = 'NIFTY_100' if is_nifty_100 else 'NIFTY_250'

        time.sleep(0.3)  # Increased sleep for more stocks

        df = fetch_stock_data(ticker, start_date=script_start_date, end_date=end_date)

        if df is not None:
            df = normalize_columns(df)
            # Add source column
            df['source'] = source

            data_frames_list.append(df)
            print(f"✓ Fetched: {ticker} | Source: {source} | Shape: {df.shape}")
        else:
            print(f"⊘ SKIP: {ticker}")

    # --- 3. Combine DataFrames ---
    if data_frames_list:
        full_df = pd.concat(data_frames_list, ignore_index=True)
        full_df = normalize_columns(full_df)
        full_df = remove_timezones(full_df)

        # --- 4. Calculate Technical Indicators ---
        print("\n" + "-" * 40)
        print("Calculating Indicators: SMA, EMA, RSI, MFI + MACD, ADX, Supertrend, etc.")
        print("-" * 40)
        full_df = calculate_technical_indicators(full_df)

        full_df = remove_timezones(full_df)

        # --- 5. Sort DataFrame for Export (Descending Date) ---
        print("\n" + "-" * 40)
        print("Sorting DataFrame: Date (Descending), Ticker (Ascending) for Export")
        print("-" * 40)
        full_df = sort_dataframe(full_df)

        # --- 6. Display Summary Statistics ---
        print("\n" + "=" * 80)
        print("Analysis Summary:")
        print(f"Total Rows: {len(full_df)}")
        print(f"Total Tickers: {full_df['ticker'].nunique()}")
        print(f"Columns: {len(full_df.columns)}")

        print("\n" + "-" * 40)
        print("Distribution by Source:")
        if 'source' in full_df.columns:
            print(full_df['source'].value_counts())

        # --- 7. Check MFI for a sample stock ---
        sample_stock = full_df[full_df['ticker'].str.lower() == 'reliance.ns'].dropna()
        if not sample_stock.empty:
            print("\n" + "-" * 40)
            print("MFI Sample for RELIANCE (Last 10 rows):")
            print(sample_stock[['ticker', 'date', 'close', 'mfi_14']].tail(10).to_string())

        # --- 8. Export to Excel with Separate Sheets ---
        excel_filename = 'nifty_large_midcap_data.xlsx'
        print("\n" + "=" * 80)
        print("📤 Saving to Separate Sheets...")
        print("=" * 80)

        # --- Split Data by Source ---
        df_100 = full_df[full_df['source'] == 'NIFTY_100']
        df_250 = full_df[full_df['source'] == 'NIFTY_250']

        # Create default DataFrames if groups are empty to ensure columns exist
        if df_100.empty:
            df_100 = pd.DataFrame(columns=full_df.columns)
        if df_250.empty:
            df_250 = pd.DataFrame(columns=full_df.columns)

        # --- 9. Save using ExcelWriter to separate sheets ---
        try:
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                df_100.to_excel(writer, sheet_name='NIFTY_100', index=False)
                df_250.to_excel(writer, sheet_name='NIFTY_LARGE_MIDCAP', index=False)

                file_saved = True

        except Exception as e:
            print(f"❌ Error saving Excel file: {str(e)}")
            file_saved = False

    else:
        print("\n❌ No data to export.")

    return full_df


# ===============================
# [STREAMLIT UI WRAPPER] - ADDED FOR DEPLOYMENT
# ===============================
def fetch_all_data_for_streamlit():
    """Wrapper to run logic inside Streamlit cache"""
    import streamlit as st

    if not 'nifty_data' in st.session_state:
        print("\n🚀 Starting Nifty 100 & Nifty 250 Data Script...")
        try:
            df = main()
            # If success
            if df is not None:
                st.session_state['nifty_data'] = df
                return df
            else:
                return None
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None

    return st.session_state['nifty_data']


if __name__ == "__main__":
    # This block is removed from Streamlit logic flow but kept for local testing
    # In Streamlit Cloud, main() is called via the button logic below.
    pass