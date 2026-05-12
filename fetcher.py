import pandas as pd
import numpy as np
from yahooquery import Ticker
import time

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

def calculate_indicators(df):
    df = df.copy()
    
    # ==========================================
    # 1. ORIGINAL 33 INDICATORS (WITH BUG FIXES)
    # ==========================================
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

    # ADX FIX applied
    up_move = df['High'] - df['High'].shift(1)
    down_move = df['Low'].shift(1) - df['Low']
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)
    atr_smooth = df['ATR_14'].ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_smooth.replace(0, 1e-9))
    minus_di = 100 * (minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_smooth.replace(0, 1e-9))
    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1e-9)) * 100
    df['ADX_14'] = dx.ewm(alpha=1/14, adjust=False).mean()

    # Aroon FIX applied
    aroon_up = df['High'].rolling(14).apply(lambda x: x.argmax(), raw=True)
    aroon_down = df['Low'].rolling(14).apply(lambda x: x.argmin(), raw=True)
    df['Aroon_Osc'] = ((aroon_up + 1) / 14 * 100) - ((aroon_down + 1) / 14 * 100)

    hl2 = (df['High'] + df['Low']) / 2
    df['Awesome_Osc'] = hl2.rolling(5).mean() - hl2.rolling(34).mean()

    mfv = df['Volume'] * ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low']).replace(0, 1e-9)
    df['CMF_20'] = mfv.rolling(20).sum() / df['Volume'].rolling(20).sum().replace(0, 1e-9)

    # CMO FIX applied
    cmo_gain = delta.where(delta > 0, 0.0).rolling(window=14).sum()
    cmo_loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).sum()
    df['CMO_14'] = 100 * ((cmo_gain - cmo_loss) / (cmo_gain + cmo_loss).replace(0, 1e-9))

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
    # Stochastic RSI FIX applied
    df['Stoch_RSI'] = ((df['RSI_14'] - rsi_min) / (rsi_max - rsi_min).replace(0, 1e-9)) * 100

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

    # Vortex FIX applied
    vmp = np.abs(df['High'] - df['Low'].shift())
    vmm = np.abs(df['Low'] - df['High'].shift())
    df['Vortex_Pos'] = pd.Series(vmp, index=df.index).rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)
    df['Vortex_Neg'] = pd.Series(vmm, index=df.index).rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)

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

    # ==========================================
    # 2. THE MIDDLE 10 INDICATORS
    # ==========================================
    df['Typical_Price'] = tp
    df['Median_Price'] = (df['High'] + df['Low']) / 2
    clv = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low']).replace(0, 1e-9)
    df['Acc_Dist'] = (clv * df['Volume']).cumsum()
    pvt_calc = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1).replace(0, 1e-9)) * df['Volume']
    df['PVT'] = pvt_calc.cumsum()
    df['Std_Dev_20'] = df['Close'].rolling(window=20).std()
    shifted_mean = df['Close'].rolling(window=20).mean().shift(int((20/2) + 1))
    df['DPO_20'] = df['Close'] - shifted_mean
    dm = ((df['High'] + df['Low']) / 2) - ((df['High'].shift(1) + df['Low'].shift(1)) / 2)
    br = (df['Volume'] / 100000000) / ((df['High'] - df['Low']).replace(0, 1e-9))
    df['EOM_14'] = (dm / br.replace(0, 1e-9)).rolling(14).mean()
    df['Volume_ROC_14'] = df['Volume'].pct_change(periods=14) * 100
    hl_ema = (df['High'] - df['Low']).ewm(span=10, adjust=False).mean()
    df['Chaikin_Volatility_10'] = ((hl_ema - hl_ema.shift(10)) / hl_ema.shift(10).replace(0, 1e-9)) * 100
    df['Momentum_10'] = df['Close'] - df['Close'].shift(10)

    # ==========================================
    # 3. THE FINAL 13 CAPSTONE INDICATORS
    # ==========================================
    df['Bollinger_Bandwidth'] = ((df['BB_Upper'] - df['BB_Lower']) / df['SMA_20'].replace(0, 1e-9)) * 100
    df['Balance_Of_Power'] = (df['Close'] - df['Open']) / (df['High'] - df['Low']).replace(0, 1e-9)
    df['Disparity_Index_14'] = ((df['Close'] - df['SMA_14']) / df['SMA_14'].replace(0, 1e-9)) * 100
    ema_13 = df['Close'].ewm(span=13, adjust=False).mean()
    df['Elder_Ray_Bull'] = df['High'] - ema_13
    df['Elder_Ray_Bear'] = df['Low'] - ema_13
    df['High_Band_14'] = df['High'].rolling(14).mean()
    df['Low_Band_14'] = df['Low'].rolling(14).mean()
    df['Highest_High_14'] = df['High'].rolling(14).max()
    df['Lowest_Low_14'] = df['Low'].rolling(14).min()
    df['MAE_Upper_20'] = df['SMA_20'] * 1.05
    df['MAE_Lower_20'] = df['SMA_20'] * 0.95
    roc_close = df['Close'].pct_change()
    vol_down = df['Volume'] < df['Volume'].shift(1)
    df['NVI'] = 1000.0 * (1 + np.where(vol_down, roc_close, 0.0)).cumprod()
    vol_up = df['Volume'] > df['Volume'].shift(1)
    df['PVI'] = 1000.0 * (1 + np.where(vol_up, roc_close, 0.0)).cumprod()
    df['Performance_Index'] = (df['Close'] / df['Close'].iloc[0]) * 100
    df['True_Range'] = tr
    max_close_14 = df['Close'].rolling(14).max()
    percent_drawdown = ((df['Close'] - max_close_14) / max_close_14.replace(0, 1e-9)) * 100
    df['Ulcer_Index_14'] = np.sqrt((percent_drawdown ** 2).rolling(14).mean())

    return df

def run_fetcher():
    tickers = NIFTY_100_TICKERS + NIFTY_MIDCAP_100_TICKERS
    print(f"Initiating ISOLATED fetch for {len(tickers)} stocks via YahooQuery mobile API...")

    all_data = []
    
    for ticker in tickers:
        try:
            t = Ticker(ticker)
            df = t.history(start="2021-01-01")
            
            if isinstance(df, pd.DataFrame) and not df.empty and 'error' not in df.columns:
                df = df.reset_index()
                
                df = df.rename(columns={
                    'symbol': 'Ticker',
                    'date': 'Date',
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                
                df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
                
                if len(df) > 100:
                    df = df.set_index('Date')
                    calc_df = calculate_indicators(df)
                    calc_df['Ticker'] = ticker
                    calc_df['Index'] = "Nifty 100" if ticker in NIFTY_100_TICKERS else "Nifty Midcap 100"
                    calc_df = calc_df.reset_index()
                    all_data.append(calc_df)
                    print(f"✅ Processed {ticker}")
                else:
                    print(f"⚠️ Not enough data for {ticker}")
            else:
                print(f"⚠️ Yahoo returned invalid/empty data for {ticker}")
                
        except Exception as e:
            print(f"❌ Failed to fetch/calculate {ticker}: {e}")
            
        time.sleep(0.5)

    if all_data:
        final_df = pd.concat(all_data)
        
        for col in final_df.select_dtypes(include=['float64']).columns:
            final_df[col] = final_df[col].round(2)
            
        # SAVING AS COMPRESSED GZIP TO BYPASS GITHUB 100MB LIMIT
        final_df.to_csv("nifty_data.csv.gz", index=False, compression="gzip")
        print(f"\n🎉 Success! Saved {len(final_df)} rows of compressed data to nifty_data.csv.gz")
    else:
        print("\n💥 CRITICAL FAILURE: No stocks were processed successfully.")

if __name__ == "__main__":
    run_fetcher()
