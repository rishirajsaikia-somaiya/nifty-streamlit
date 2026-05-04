import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import os
import gc
import time
import streamlit as st
from io import BytesIO
from plotly import graph_objects as go
import pandas_ta as ta

# === Manual Indicator Functions ===
def manual_rsi(close_prices, length=14):
    if len(close_prices) < length:
        return pd.Series(dtype=float)
    delta = close_prices.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=length).mean()
    avg_loss = loss.rolling(window=length).mean()
    avg_gain = avg_gain.fillna(0)
    avg_loss = avg_loss.fillna(0)
    with np.errstate(divide='ignore', invalid='ignore'):
        rs = avg_loss / avg_gain
        rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def manual_mfi(high, low, close, volume, length=14):
    if len(close) < length or volume is None or volume.empty:
        return pd.Series(dtype=float)
    typical_price = (high + low + close) / 3
    price_change = close.diff()
    is_positive = price_change > 0
    money_flow = typical_price * volume
    mask = volume > 0
    pos_mf = money_flow.where(mask, 0) * is_positive
    neg_mf = money_flow.where(mask, 0) * (1 - is_positive)
    avg_pos_mf = pos_mf.rolling(window=length).mean()
    avg_neg_mf = neg_mf.rolling(window=length).mean()
    avg_pos_mf = avg_pos = avg_pos_mf.fillna(0)
    avg_neg_mf = avg_neg_mf.fillna(0)
    with np.errstate(divide='ignore', invalid='ignore'):
        mfr = avg_pos_mf / avg_neg_mf
        mfi = 100.0 - (100.0 / (1.0 + mfr))
    return mfi

# === Data Fetch Functions ===
def get_nifty_100_list():
    nifty_100_list = [
        'RELIANCE.NS','TCS.NS','HDFCBANK.NS','BHARTIARTL.NS','ICICIBANK.NS',
        'INFOSYS.NS','SBIN.NS','HINDUNILVR.NS','ITC.NS','LT.NS',
        'KOTAKBANK.NS','AXISBANK.NS','BAJFINANCE.NS','MARUTI.NS','ASIANPAINT.NS',
        'TITAN.NS','SUNPHARMA.NS','NESTLEIND.NS','WIPRO.NS','HCLTECH.NS',
        'NTPC.NS','POWERGRID.NS','TECHM.NS','ONGC.NS','COALINDIA.NS',
        'BAJAJFINSV.NS','ADANIENT.NS','ADANIPORTS.NS','ULTRACEMCO.NS','JSWSTEEL.NS',
        'TATAMOTORS.NS','TATASTEEL.NS','INDUSINDBK.NS','HDFCLIFE.NS','SBILIFE.NS',
        'DIVISLAB.NS','DRREDDY.NS','CIPLA.NS','APOLLOHOSP.NS','EICHERMOT.NS',
        'GRASIM.NS','HINDALCO.NS','HEROMOTOCO.NS','BPCL.NS','BAJAJ-AUTO.NS',
        'TATACONSUM.NS','BRITANNIA.NS','VEDL.NS','UPL.NS','SHREECEM.NS',
        'ICICIGI.NS','BOSCHLTD.NS','SIEMENS.NS','HAVELLS.NS','PIIND.NS',
        'GODREJCP.NS','DABUR.NS','MARICO.NS','MCDOWELL-N.NS','COLPAL.NS',
        'AMBUJACEM.NS','ACC.NS','INDIGO.NS','TATAPOWER.NS','GAIL.NS',
        'IOC.NS','SBICARD.NS','BANDHANBNK.NS','BANKBARODA.NS','PNB.NS',
        'MUTHOOTFIN.NS','CHOLAFIN.NS','TORNTPHARM.NS','LUPIN.NS','BIOCON.NS',
        'ALKEM.NS','AUROPHARMA.NS','ZYDUSLIFE.NS','GLAXO.NS','PAGEIND.NS',
        'VOLTAS.NS','CROMPTON.NS','POLYCAB.NS','CUMMINSIND.NS','ABB.NS',
        'BHEL.NS','HAL.NS','BEL.NS','CONCOR.NS','ADANIGREEN.NS',
        'IRFC.NS','PFC.NS','RECLTD.NS','M&M.NS','TRENT.NS',
    ]
    return nifty_100_list

def get_nifty_large_midcap_250_list():
    base = get_nifty_100_list()
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
    combined_list = base + midcaps
    unique_list = list(dict.fromkeys(combined_list))
    if len(unique_list) > 250:
        return unique_list[:250]
    else:
        return unique_list

def fetch_stock_data_bulk(tickers, start_date='2021-01-01', end_date=None):
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # yfinance works perfectly with a list of strings
        data = yf.download(
            tickers,
            start=start_date,
            end=end_date,
            group_by='ticker',
            auto_adjust=True,
            progress=False
        )
        
        dfs_list = []
        for ticker in tickers:
            df_ticker = pd.DataFrame()
            
            # Handle MultiIndex (multiple tickers downloaded) vs Single Index (one ticker)
            if isinstance(data.columns, pd.MultiIndex):
                if ticker in data.columns.get_level_values(0):
                    df_ticker = data[ticker].copy()
            else:
                # If columns aren't MultiIndex, yfinance returned a flat DataFrame for a single ticker
                if len(tickers) == 1 or len(data.columns.intersection(['Open', 'Close'])) > 0:
                    df_ticker = data.copy()
            
            if not df_ticker.empty:
                df_ticker = df_ticker.reset_index()
                df_ticker['Ticker'] = ticker
                
                # Rename columns to snake case to match your indicator functions
                df_ticker.columns = df_ticker.columns.str.lower()
                
                # Convert date to proper format
                if 'date' in df_ticker.columns:
                    df_ticker['date'] = pd.to_datetime(df_ticker['date']).dt.tz_localize(None)
                
                dfs_list.append(df_ticker)
        
        if dfs_list:
            return pd.concat(dfs_list, ignore_index=True)
        return None
        
    except Exception as e:
        print(f"Error in bulk fetch: {str(e)}")
        return None

def fetch_stock_data(ticker: str, start_date='2021-01-01', end_date=None):
    try:
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Try bulk download first
        if ',' in ticker:
            return fetch_stock_data_bulk(ticker, start_date, end_date)
        
        ticker_obj = yf.Ticker(ticker)
        history = ticker_obj.history(start=start_date, end=end_date)
        if history.empty:
            return None
        history = history.reset_index()
        history['Ticker'] = ticker
        history['Date'] = pd.to_datetime(history['Date'])
        history['Date'] = history['Date'].dt.tz_localize(None)
        history = history.rename(columns={
            'Open': 'open', 
            'High': 'high', 
            'Low': 'low', 
            'Close': 'close', 
            'Volume': 'volume',
            'Dividends': 'dividends',
            'Stock Splits': 'stock_splits'
        })
        return history
    except Exception as e:
        print(f"Error fetching {ticker}: {str(e)}")
        return None

# === Helper Functions ===
def normalize_columns(df):
    if df.empty:
        return df
    df.columns = df.columns.str.lower()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.tz_localize(None)
    else:
        df['date'] = pd.NaT
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].fillna('UNKNOWN')
    else:
        df['ticker'] = 'UNKNOWN'
    required_price_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_price_cols:
        if col not in df.columns:
            df[col] = np.nan
    return df

def remove_timezones(df):
    if df.empty:
        return df
    datetime_cols = df.select_dtypes(include=['datetime64[ns]']).columns
    for col in datetime_cols:
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            df = df.copy()
            df[col] = df[col].dt.tz_localize(None)
    return df

def calculate_technical_indicators(df: pd.DataFrame):
    if df.empty or 'ticker' not in df.columns or 'date' not in df.columns:
        return df
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    # Check if we have enough data for indicators
    if len(df) < 20:
        return df.copy()
    
    df_with_indicators = []
    for ticker_name, group in df.groupby('ticker'):
        if group.empty:
            continue
        
        # Ensure proper sorting
        group = group.sort_values('date', ascending=True).reset_index(drop=True)
        seg = 'UNKNOWN'
        if 'source' in group.columns:
            seg = group['source'].iloc[0]
        
        # Calculate SMA and EMA
        for w in [10, 20, 50, 200]:
            if len(group) >= w:
                group[f'sma_{w}'] = ta.sma(group['close'], length=w)
                group[f'ema_{w}'] = ta.ema(group['close'], length=w)
        
        # Calculate DEMA
        if len(group) >= 12:
            group['dema_12'] = ta.dema(group['close'], length=12)
        
        # Calculate ROC
        for w in [10, 20, 50]:
            if len(group) >= w:
                group[f'roc_{w}'] = ta.roc(group['close'], length=w)
        
        # Calculate MACD
        try:
            if len(group) >= 26:
                macd_result = ta.macd(group['close'], fast=12, slow=26, signal=9)
                if macd_result is not None and not macd_result.empty:
                    group['macd'] = macd_result.iloc[:, 0]
                    group['macd_hist'] = macd_result.iloc[:, 1]
                    group['macd_signal'] = macd_result.iloc[:, 2]
                else:
                    group['macd'] = np.nan
                    group['macd_hist'] = np.nan
                    group['macd_signal'] = np.nan
            else:
                group['macd'] = np.nan
                group['macd_hist'] = np.nan
                group['macd_signal'] = np.nan
        except Exception as e:
            print(f"MACD calculation error for {ticker_name}: {str(e)}")
            group['macd'] = np.nan
            group['macd_hist'] = np.nan
            group['macd_signal'] = np.nan
        
        # Calculate ADX
        try:
            adx_result = ta.adx(group['high'], group['low'], group['close'], length=14)
            if adx_result is not None and not adx_result.empty:
                group['adx_14'] = adx_result.iloc[:, 0]
            else:
                group['adx_14'] = np.nan
        except Exception as e:
            print(f"ADX calculation error for {ticker_name}: {str(e)}")
            group['adx_14'] = np.nan
        
        # Calculate SAR
        try:
            psar_result = ta.psar(group['high'], group['low'], group['close'], af0=0.02, af=0.02, max_af=0.2)
            if psar_result is not None and not psar_result.empty:
                group['sar'] = psar_result.iloc[:, 0]
            else:
                group['sar'] = np.nan
        except Exception as e:
            print(f"SAR calculation error for {ticker_name}: {str(e)}")
            group['sar'] = np.nan
        
        # Calculate SuperTrend
        try:
            st_result = ta.supertrend(group['high'], group['low'], group['close'], length=10, multiplier=3.0)
            if st_result is not None and not st_result.empty:
                group['supertrend'] = st_result.iloc[:, 0]
            else:
                group['supertrend'] = np.nan
        except Exception as e:
            print(f"Supertrend calculation error for {ticker_name}: {str(e)}")
            group['supertrend'] = np.nan
        
        # Calculate Stochastic
        try:
            stoch_result = ta.stoch(group['high'], group['low'], group['close'], k=14, d=3, smooth_d=3)
            if stoch_result is not None and not stoch_result.empty:
                group['stoch_k_14'] = stoch_result.iloc[:, 0]
                group['stoch_d_14'] = stoch_result.iloc[:, 1]
            else:
                group['stoch_k_14'] = np.nan
                group['stoch_d_14'] = np.nan
        except Exception as e:
            print(f"Stochastic calculation error for {ticker_name}: {str(e)}")
            group['stoch_k_14'] = np.nan
            group['stoch_d_14'] = np.nan
        
        # Calculate CCI
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
            print(f"CCI calculation error for {ticker_name}: {str(e)}")
            group['cci_20'] = np.nan
        
        # Calculate Williams R
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
            print(f"Williams R calculation error for {ticker_name}: {str(e)}")
            group['williams_r_14'] = np.nan
        
        # Calculate Ichimoku
        try:
            if len(group) >= 26:
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
            print(f"Ichimoku calculation error for {ticker_name}: {str(e)}")
            group['ichimoku_tenkan_sen'] = np.nan
            group['ichimoku_kijun_sen'] = np.nan
            group['ichimoku_senkou_span_a'] = np.nan
            group['ichimoku_senkou_span_b'] = np.nan
            group['ichimoku_chikou_span'] = np.nan
        
        # Calculate RSI
        try:
            group['rsi_14'] = manual_rsi(group['close'], length=14)
        except Exception as e:
            print(f"RSI calculation error for {ticker_name}: {str(e)}")
            group['rsi_14'] = np.nan
        
        # Calculate MFI
        try:
            if 'volume' in group.columns and group['volume'].notna().any():
                group['mfi_14'] = manual_mfi(group['high'], group['low'], group['close'], group['volume'], length=14)
            else:
                group['mfi_14'] = np.nan
        except Exception as e:
            print(f"MFI calculation error for {ticker_name}: {str(e)}")
            group['mfi_14'] = np.nan
        
        if 'source' not in group.columns:
            group['source'] = seg
        
        df_with_indicators.append(group)
    
    if df_with_indicators:
        full_df_calculated = pd.concat(df_with_indicators, ignore_index=True)
        return full_df_calculated
    else:
        return pd.DataFrame()

def sort_dataframe(df):
    if df.empty:
        return df
    df = df.sort_values(by=['date', 'ticker'], ascending=[False, True])
    return df

def save_and_download_excel(df, filename):
    try:
        # Create a copy to avoid SettingWithCopyWarning
        df_copy = df.copy()
        
        # Convert date columns properly
        if 'date' in df_copy.columns:
            df_copy['date'] = df_copy['date'].dt.strftime('%d-%m-%Y')
        
        # Create a new Excel file with proper formatting
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write each source to separate sheet
            for source in df_copy['source'].unique():
                source_df = df_copy[df_copy['source'] == source]
                if not source_df.empty:
                    sheet_name = source[:30]  # Excel sheet names can't be longer than 30 characters
                    source_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error saving Excel file: {str(e)}")
        return None

# === Dashboard Functions ===
def show_screener(df):
    st.header("📈 Stock Screener")
    
    # Filter by index
    index_filter = st.selectbox("Select Index", ["Nifty 100", "Nifty 250"])
    if index_filter == "Nifty 100":
        df_screen = df[df['source'] == 'NIFTY_100']
    else:
        df_screen = df[df['source'] == 'NIFTY_250']
    
    # Filter by performance
    performance_col = st.selectbox("Filter by Performance", ["All", "Up", "Down"])
    if performance_col == "Up":
        df_screen = df_screen[df_screen['close'] > df_screen['close'].shift(1)]
    elif performance_col == "Down":
        df_screen = df_screen[df_screen['close'] < df_screen['close'].shift(1)]
    
    # Show data table
    st.subheader("Stock Data")
    st.dataframe(df_screen[['ticker', 'date', 'close', 'volume']])
    
    # Show indicator filters
    st.subheader("Indicator Filters")
    indicator = st.selectbox("Select Indicator", ["RSI", "MFI", "ADX", "Volume"])
    
    if indicator == "RSI":
        rsi_level = st.slider("RSI Level", 0, 100, 50)
        filtered_rsi = df_screen.dropna(subset=['rsi_14'])
        filtered_rsi = filtered_rsi[filtered_rsi['rsi_14'] > rsi_level]
        st.dataframe(filtered_rsi[['ticker', 'rsi_14']])
    
    elif indicator == "MFI":
        mfi_level = st.slider("MFI Level", 0, 100, 50)
        filtered_mfi = df_screen.dropna(subset=['mfi_14'])
        filtered_mfi = filtered_mfi[filtered_mfi['mfi_14'] > mfi_level]
        st.dataframe(filtered_mfi[['ticker', 'mfi_14']])
    
    elif indicator == "ADX":
        adx_level = st.slider("ADX Level", 0, 100, 20)
        filtered_adx = df_screen.dropna(subset=['adx_14'])
        filtered_adx = filtered_adx[filtered_adx['adx_14'] > adx_level]
        st.dataframe(filtered_adx[['ticker', 'adx_14']])
    
    elif indicator == "Volume":
        volume_level = st.slider("Volume Level", 0, 5000000, 1000000)
        filtered_volume = df_screen.dropna(subset=['volume'])
        filtered_volume = filtered_volume[filtered_volume['volume'] > volume_level]
        st.dataframe(filtered_volume[['ticker', 'volume']])

def show_stock_analysis(df):
    st.header("🔍 Stock Analysis")
    
    # Select stock
    available_tickers = df['ticker'].unique()
    selected_ticker = st.selectbox("Select Stock", available_tickers)
    
    if selected_ticker:
        stock_data = df[df['ticker'] == selected_ticker].sort_values('date', ascending=True)
        if not stock_data.empty:
            st.subheader(f"📊 Analysis for {selected_ticker}")
            
            # Show key statistics
            st.subheader("Key Statistics")
            st.write(f"Latest Close: {stock_data['close'].iloc[-1]:.2f}")
            st.write(f"20-Day Average Volume: {stock_data['volume'].rolling(20).mean().iloc[-1]:.2f}")
            st.write(f"RSI (14-day): {stock_data['rsi_14'].iloc[-1]:.2f}")
            st.write(f"MFI (14-day): {stock_data['mfi_14'].iloc[-1]:.2f}")
            st.write(f"ADX (14-day): {stock_data['adx_14'].iloc[-1]:.2f}")
            
            # Show technical indicators
            st.subheader("Technical Indicators")
            indicator = st.selectbox("Select Indicator", ["RSI", "MACD", "ADX", "Supertrend", "Stochastic"])
            
            if indicator == "RSI":
                st.line_chart(stock_data['rsi_14'].tail(50), use_container_width=True)
            
            elif indicator == "MACD":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=stock_data['date'].tail(50),
                    y=stock_data['macd'].tail(50),
                    name='MACD'
                ))
                fig.add_trace(go.Scatter(
                    x=stock_data['date'].tail(50),
                    y=stock_data['macd_signal'].tail(50),
                    name='Signal'
                ))
                fig.add_trace(go.Scatter(
                    x=stock_data['date'].tail(50),
                    y=stock_data['macd_hist'].tail(50),
                    name='Histogram'
                ))
                st.plotly_chart(fig, use_container_width=True)
            
            elif indicator == "ADX":
                st.line_chart(stock_data['adx_14'].tail(50), use_container_width=True)
            
            elif indicator == "Supertrend":
                st.line_chart(stock_data['close'].tail(50), use_container_width=True)
                st.line_chart(stock_data['supertrend'].tail(50), use_container_width=True)
            
            elif indicator == "Stochastic":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=stock_data['date'].tail(50),
                    y=stock_data['stoch_k_14'].tail(50),
                    name='K'
                ))
                fig.add_trace(go.Scatter(
                    x=stock_data['date'].tail(50),
                    y=stock_data['stoch_d_14'].tail(50),
                    name='D'
                ))
                st.plotly_chart(fig, use_container_width=True)
            
            # Show price chart
            st.subheader("Price Chart")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=stock_data['date'].tail(50),
                open=stock_data['open'].tail(50),
                high=stock_data['high'].tail(50),
                low=stock_data['low'].tail(50),
                close=stock_data['close'].tail(50)
            ))
            st.plotly_chart(fig, use_container_width=True)

def main():
    # Setup
    st.set_page_config(page_title="Nifty Analytics", layout="wide")

    # Initialize session state
    if 'nifty_data' not in st.session_state:
        st.session_state['nifty_data'] = None
    if 'selected_stocks' not in st.session_state:
        st.session_state['selected_stocks'] = []
    if 'nifty_filter' not in st.session_state:
        st.session_state['nifty_filter'] = 'Nifty 250'
    if 'available_tickers' not in st.session_state:
        st.session_state['available_tickers'] = []
    if 'show_charts' not in st.session_state:
        st.session_state['show_charts'] = False

    # Title
    st.title("📊 Nifty 100 & Large Midcap Analytics Dashboard")
    st.markdown("Select filter options to fetch and visualize technical indicators for Nifty 100/250")

    # Main fetch button
    if st.button("🚀 Fetch Data", use_container_width=True, type="primary"):
        with st.spinner('📡 Fetching data and calculating indicators... This may take 2-5 minutes'):
            try:
                # Get all tickers
                tickers_nifty_100 = get_nifty_100_list()
                tickers_nifty_250 = get_nifty_large_midcap_250_list()
                all_tickers = list(dict.fromkeys(tickers_nifty_100 + tickers_nifty_250))
                
                # Fetch data in chunks
                dfs_list = []
                chunk_size = 10  # Reduce chunk size to avoid rate limits
                
                for i in range(0, len(all_tickers), chunk_size):
                    chunk = all_tickers[i:i+chunk_size]
                    print(f"Fetching chunk {i+1}-{i+chunk_size} of {len(all_tickers)}")
                    
                    if chunk:
                        df_chunk = fetch_stock_data_bulk(chunk)
                        if df_chunk is not None and not df_chunk.empty:
                            dfs_list.append(df_chunk)
                            time.sleep(1)  # Add delay between chunks to avoid rate limits
                
                if dfs_list:
                    full_df = pd.concat(dfs_list, ignore_index=True)
                    full_df = normalize_columns(full_df)
                    full_df = remove_timezones(full_df)
                    full_df = calculate_technical_indicators(full_df)
                    full_df = remove_timezones(full_df)
                    full_df = sort_dataframe(full_df)
                    
                    st.session_state['nifty_data'] = full_df
                    st.session_state['available_tickers'] = list(full_df['ticker'].unique())
                    
                    # Download button
                    if st.session_state['nifty_data'] is not None:
                        output = save_and_download_excel(st.session_state['nifty_data'], "nifty_data.xlsx")
                        st.download_button(
                            label="📥 Download All Data (Excel)",
                            data=output.getvalue(),
                            file_name="nifty_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    st.success("✅ Data fetched successfully!")
                    st.info(f"Total Tickers: {len(st.session_state['available_tickers'])}")
                else:
                    st.error("❌ No data fetched. Check console for errors.")
            except Exception as e:
                st.error(f"Error during data fetch: {str(e)}")
    
    # Show controls only if data is available
    if st.session_state['nifty_data'] is not None:
        # Sidebar filters
        with st.sidebar:
            st.header("🎛️ Filter Settings")
            
            # Nifty filter
            nifty_filter = st.selectbox(
                "Filter: Nifty 100 or Nifty 250",
                ['Nifty 100', 'Nifty 250'],
                index=['Nifty 100', 'Nifty 250'].index(st.session_state.get('nifty_filter', 'Nifty 250'))
            )
            st.session_state['nifty_filter'] = nifty_filter
            
            # Get available tickers for this filter
            df_session = st.session_state['nifty_data']
            filter_tickers = df_session[df_session['source'] == nifty_filter]['ticker'].unique()
            ticker_list = list(filter_tickers)
            
            if len(ticker_list) > 0:
                # Stock selection
                selected_stocks = st.multiselect(
                    "Select Stock(s) to Show:",
                    ticker_list,
                    default=['RELIANCE.NS'] if len(ticker_list) > 0 else []
                )
                st.session_state['selected_stocks'] = selected_stocks
            else:
                selected_stocks = []
            
            # Show charts button
            show_charts = st.button("📊 Show Charts", use_container_width=True)
            st.session_state['show_charts'] = show_charts
        
        # Display charts if button is clicked and data is available
        if st.session_state['show_charts'] and len(st.session_state['selected_stocks']) > 0:
            df_filtered = st.session_state['nifty_data']
            df_filtered = df_filtered[df_filtered['source'] == st.session_state['nifty_filter']]
            df_selected = df_filtered[df_filtered['ticker'].isin(st.session_state['selected_stocks'])]
            
            if df_selected.empty:
                st.warning("⚠️ No data for selected stocks in current filter.")
            else:
                st.subheader(f"📊 Data for {st.session_state['nifty_filter']}: {len(df_selected['ticker'].unique())} Stocks")
                
                # Create columns for charts
                num_charts = min(len(st.session_state['selected_stocks']), 4)
                num_rows = 2
                
                # Create grid of charts
                cols = st.columns(min(num_charts, 4))
                
                for idx, stock in enumerate(st.session_state['selected_stocks']):
                    if idx < len(cols):
                        with cols[idx]:
                            st.plotly_chart(
                                go.Figure().add_trace(go.Candlestick(
                                    x=df_selected[df_selected['ticker'] == stock].tail(50).set_index('date').index,
                                    open=df_selected[df_selected['ticker'] == stock].tail(50).set_index('date')['open'],
                                    high=df_selected[df_selected['ticker'] == stock].tail(50).set_index('date')['high'],
                                    low=df_selected[df_selected['ticker'] == stock].tail(50).set_index('date')['low'],
                                    close=df_selected[df_selected['ticker'] == stock].tail(50).set_index('date')['close']
                                )),
                                use_container_width=True
                            )
        
        # Show screener and analysis
        show_screener(st.session_state['nifty_data'])
        show_stock_analysis(st.session_state['nifty_data'])

if __name__ == "__main__":
    main()
