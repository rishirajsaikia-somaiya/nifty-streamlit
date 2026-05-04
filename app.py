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

# === Manual Indicator Functions ===

def manual_rsi(close_prices, length=14):
    if len(close_prices) < length:
        return pd.Series(dtype=float)
    delta = close_prices.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=length).mean()
    avg_loss = loss.rolling(window=length).mean()
    avg_gain = avg_gain.fillna(1)
    avg_loss = avg_loss.fillna(1)
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
    avg_pos_mf = avg_pos_mf.fillna(1)
    avg_neg_mf = avg_neg_mf.fillna(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        mfr = avg_pos_mf / avg_neg_mf
        mfi = 100.0 - (100.0 / (1.0 + mfr))
    return mfi

# === Data Fetch Functions ===

def get_nifty_100_list():
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

def fetch_stock_data(ticker: str, start_date: str = '2021-01-01', end_date: str = None):
    try:
        ticker_obj = yf.Ticker(ticker)
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        history = ticker_obj.history(start=start_date, end=end_date)
        if history.empty:
            return None
        history = history.reset_index()
        history['Ticker'] = ticker
        history['Date'] = pd.to_datetime(history['Date'])
        history['Date'] = history['Date'].dt.tz_localize(None)
        history = history.reset_index(drop=True)
        return history
    except Exception as e:
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
    required_price_cols = ['close', 'high', 'low', 'volume']
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
    required_cols = ['close', 'high', 'low', 'volume']
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan
    df_with_indicators = []
    for ticker_name, group in df.groupby('ticker'):
        group = group.sort_values('date', ascending=True).reset_index(drop=True)
        seg = group['source'].iloc[0] if 'source' in group.columns else 'UNKNOWN'
        if group.empty:
            continue
        for w in [10, 20, 50, 200]:
            group[f'sma_{w}'] = ta.sma(group['close'], length=w)
        for w in [10, 20, 50, 200]:
            group[f'ema_{w}'] = ta.ema(group['close'], length=w)
        group['dema_12'] = ta.dema(group['close'], length=12)
        for w in [10, 20, 50]:
            group[f'roc_{w}'] = ta.roc(group['close'], length=w)
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
        try:
            adx_result = ta.adx(group['high'], group['low'], group['close'], length=14)
            if adx_result is not None and not adx_result.empty:
                group['adx_14'] = adx_result.iloc[:, 0]
            else:
                group['adx_14'] = np.nan
        except Exception as e:
            group['adx_14'] = np.nan
        try:
            psar_result = ta.psar(group['high'], group['low'], group['close'], af0=0.02, af=0.02, max_af=0.2)
            if psar_result is not None and not psar_result.empty:
                group['sar'] = psar_result.iloc[:, 0]
            else:
                group['sar'] = np.nan
        except Exception as e:
            group['sar'] = np.nan
        try:
            st_result = ta.supertrend(group['high'], group['low'], group['close'], length=10, multiplier=3.0)
            if st_result is not None and not st_result.empty:
                group['supertrend'] = st_result.iloc[:, 0]
            else:
                group['supertrend'] = np.nan
        except Exception as e:
            group['supertrend'] = np.nan
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
        try:
            group['rsi_14'] = manual_rsi(group['close'], length=14)
        except Exception as e:
            group['rsi_14'] = np.nan
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
        if 'source' not in group.columns:
            group['source'] = seg
        df_with_indicators.append(group)
    if df_with_indicators:
        full_df_calculated = pd.concat(df_with_indicators, ignore_index=True)
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

def sort_dataframe(df):
    if df.empty:
        return df
    df = df.sort_values(by=['date', 'ticker'], ascending=[False, True])
    return df

def save_and_download_excel(df, filename):
    try:
        if 'date' in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = df['date'].dt.strftime('%d-%m-%Y')
            elif not df['date'].isna().all():
                df['date'] = df['date'].astype(str)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error saving Excel file: {str(e)}")
        return None

# === === STREAMLIT UI WRAPPER === ===
# Streamlit runs the entire file on every render

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
        tickers_nifty_100 = get_nifty_100_list()
        tickers_nifty_250 = get_nifty_large_midcap_250_list()
        unique_tickers = list(dict.fromkeys(tickers_nifty_100 + tickers_nifty_250))
        
        all_tickers = list(dict.fromkeys(unique_tickers))
        nifty_100_set = set(tickers_nifty_100)
        nifty_250_set = set(tickers_nifty_250)
        
        # Fetch data for all stocks
        data_frames_list = []
        for ticker in all_tickers:
            df = fetch_stock_data(ticker, start_date='2021-01-01')
            if df is not None:
                df = normalize_columns(df)
                is_nifty_100 = ticker in tickers_nifty_100
                source = 'NIFTY_100' if is_nifty_100 else 'NIFTY_250'
                df['source'] = source
                data_frames_list.append(df)
        
        if data_frames_list:
            full_df = pd.concat(data_frames_list, ignore_index=True)
            full_df = normalize_columns(full_df)
            full_df = remove_timezones(full_df)
            full_df = calculate_technical_indicators(full_df)
            full_df = remove_timezones(full_df)
            full_df = sort_dataframe(full_df)
            
            st.session_state['nifty_data'] = full_df
            st.session_state['available_tickers'] = list(full_df['ticker'].unique())
            
            # Download button
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                full_df.to_excel(writer, index=False)
            output.seek(0)
            st.download_button(
                label="📥 Download All Data (Excel)",
                data=output.getvalue(),
                file_name="nifty_data.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
            
            st.success("✅ Data fetched successfully!")
            st.info(f"Total Tickers: {len(full_df['ticker'].unique())}")
        else:
            st.error("❌ No data fetched. Check console for errors.")
else:
    st.write("")  # Add blank line for layout

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
        df_filtered = df_filtered[df_filtered['source'] == nifty_filter]
        df_selected = df_filtered[df_filtered['ticker'].isin(st.session_state['selected_stocks'])]
        
        if df_selected.empty:
            st.warning("⚠️ No data for selected stocks in current filter.")
        else:
            st.subheader(f"📊 Data for {nifty_filter}: {len(df_selected['ticker'].unique())} Stocks")
            
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
