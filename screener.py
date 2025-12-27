import yfinance as yf
import pandas as pd
import streamlit as st

# --- INDIAN MARKET (NIFTY 500 Representative) ---
# Top 500 Liquid Stocks on NSE
IND_STOCKS = [
    # NIFTY 50
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS",
    "AXISBANK.NS", "HCLTECH.NS", "ADANIENT.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "TATAMOTORS.NS", "ONGC.NS", "NTPC.NS",
    "BAJFINANCE.NS", "M&M.NS", "POWERGRID.NS", "ASIANPAINT.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "WIPRO.NS", "COALINDIA.NS", "ADANIPORTS.NS", "BAJAJFINSV.NS",
    "GRASIM.NS", "HINDALCO.NS", "TECHM.NS", "EICHERMOT.NS", "NESTLEIND.NS", "HINDUNILVR.NS", "TATACONSUM.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
    "APOLLOHOSP.NS", "BRITANNIA.NS", "INDUSINDBK.NS", "HEROMOTOCO.NS", "SBILIFE.NS", "BPCL.NS", "UPL.NS", "LTIM.NS",
    
    # NIFTY NEXT 50 & MIDCAP 150 (Top Liquid)
    "ABB.NS", "ACC.NS", "ADANIENSOL.NS", "ADANIGREEN.NS", "ADANIPOWER.NS", "ATGL.NS", "AMBUJACEM.NS", "APLAPOLLO.NS", "AUBANK.NS", "AUROPHARMA.NS",
    "BANKBARODA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHEL.NS", "BIOCON.NS", "BOSCHLTD.NS", "CANBK.NS", "CHOLAFIN.NS", "COLPAL.NS",
    "CONCOR.NS", "DLF.NS", "DMART.NS", "GAIL.NS", "GODREJCP.NS", "HAL.NS", "HAVELLS.NS", "HDFCAMC.NS", "HDFCLIFE.NS", "HINDPETRO.NS",
    "ICICIGI.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", "IGL.NS", "INDHOTEL.NS", "IOC.NS", "IRCTC.NS", "JINDALSTEL.NS", "JIOFIN.NS", "JUBLFOOD.NS",
    "LICI.NS", "LUPIN.NS", "MARICO.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NAUKRI.NS", "NMDC.NS", "OBEROIRLTY.NS", "OFSS.NS",
    "PAGEIND.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PGHH.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POONAWALLA.NS",
    "RECLTD.NS", "SAIL.NS", "SBICARD.NS", "SHRIRAMFIN.NS", "SIEMENS.NS", "SRF.NS", "SUPREMEIND.NS", "TATACHEM.NS", "TATAELXSI.NS", "TATAPOWER.NS",
    "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UNIONBANK.NS", "UNITDSPR.NS", "VBL.NS", "VEDL.NS", "VOLTAS.NS", "ZOMATO.NS", "ZYDUSLIFE.NS",
    
    # SMALLCAP 250 & OTHERS (High Volume)
    "AARTIIND.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "ASHOKLEY.NS", "ASTRAL.NS", "ATUL.NS", "BALKRISIND.NS", "BALRAMCHIN.NS",
    "BANDHANBNK.NS", "BANKINDIA.NS", "BATAINDIA.NS", "BSOFT.NS", "CANFINHOME.NS", "CASTROLIND.NS", "CDSL.NS", "CENTURYTEX.NS", "CESC.NS", "CGPOWER.NS",
    "CHAMBLFERT.NS", "CUB.NS", "CUMMINSIND.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DEVYANI.NS", "DIXON.NS", "ESCORTS.NS", "EXIDEIND.NS",
    "FEDERALBNK.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJPROP.NS", "GRANULES.NS", "GSPL.NS", "GUJGASLTD.NS", "HAPPSTMNDS.NS", "HFCL.NS",
    "HONAUT.NS", "HUDCO.NS", "IDBI.NS", "IDFC.NS", "INDIAMART.NS", "INDIANB.NS", "INDIGOPNTS.NS", "IPCALAB.NS", "IRFC.NS", "ISEC.NS", "JBCHEPHARM.NS",
    "JSL.NS", "JSWENERGY.NS", "KARURVYSYA.NS", "KEI.NS", "KPITTECH.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "LICHSGFIN.NS", "MAHABANK.NS", "MANAPPURAM.NS",
    "MAXHEALTH.NS", "MAZDOCK.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "NAM-INDIA.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NBCC.NS",
    "NCC.NS", "NHPC.NS", "OIL.NS", "ORACLE.NS", "PATANJALI.NS", "PHOENIXLTD.NS", "POLICYBZR.NS", "PRESTIGE.NS", "PVRINOX.NS", "RADICO.NS", "RAIN.NS",
    "RAMCOCEM.NS", "RATNAMANI.NS", "RAYMOND.NS", "RBLBANK.NS", "RITES.NS", "RVNL.NS", "SANOFI.NS", "SCHAEFFLER.NS", "SJVN.NS", "SKFINDIA.NS",
    "SONACOMS.NS", "STARHEALTH.NS", "SUMICHEM.NS", "SUNDARMFIN.NS", "SUNTV.NS", "SUZLON.NS", "SYNGENE.NS", "TANLA.NS", "TATACOMM.NS", "TATATECH.NS",
    "TEJASNET.NS", "THERMAX.NS", "TIINDIA.NS", "TORNTPOWER.NS", "TRIDENT.NS", "TRITURBINE.NS", "UBL.NS", "VGUARD.NS", "WELCORP.NS", "WHIRLPOOL.NS",
    "YESBANK.NS", "ZEEL.NS", "EPL.NS", "FSL.NS", "GMMPFAUDLR.NS", "INTELLECT.NS", "JBCHEPHARM.NS", "JINDALSAW.NS", "JKCEMENT.NS", "JKLAKSHMI.NS",
    "JKPAPER.NS", "JKTYRE.NS", "JWL.NS", "KEC.NS", "KNRCON.NS", "KPIL.NS", "KRBL.NS", "LATENTVIEW.NS", "LXCHEM.NS", "MAHLIFE.NS", "MAHLOG.NS",
    "MANINFRA.NS", "MAPMYINDIA.NS", "MASTEK.NS", "MOTILALOFS.NS", "MRPL.NS", "MSTCLTD.NS", "MTARTECH.NS", "NBVENTURES.NS", "NLCINDIA.NS", "NUVOCO.NS",
    "OLECTRA.NS", "PARADEEP.NS", "PCJEWELLER.NS", "PRAJIND.NS", "PRICOLLTD.NS", "PRINCEPIPE.NS", "RAILTEL.NS", "RAINBOW.NS", "RALLIS.NS", "RATEGAIN.NS",
    "RBA.NS", "RCF.NS", "REDINGTON.NS", "RENUKA.NS", "RKFORGE.NS", "ROUTE.NS", "RVNL.NS", "SAFARI.NS", "SAPPHIRE.NS", "SAREGAMA.NS", "SJVN.NS",
    "SOBHA.NS", "SONATSOFTW.NS", "SPARC.NS", "STARCEMENT.NS", "STLTECH.NS", "SUDARSCHEM.NS", "SUZLON.NS", "SWANENERGY.NS", "TEGA.NS", "TITAGARH.NS",
    "TRIVENI.NS", "TTKPRESTIG.NS", "UJJIVANSFB.NS", "UTIAMC.NS", "VAIBHAVGBL.NS", "VARROC.NS", "VIPIND.NS", "WESTLIFE.NS"
]

# --- US MARKET (S&P 500 Representative) ---
US_STOCKS = [
    # TECH & MAG 7
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "TSM", "UNH", "JNJ", "XOM", "JPM", "PG", "V",
    "LLY", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "AVGO", "COST", "MCD", "WMT", "CSCO", "ACN", "ADBE",
    "DIS", "LIN", "CRM", "NFLX", "AMD", "ORCL", "NKE", "INTC", "QCOM", "TXN", "UPS", "LOW", "PM", "INTU", "AMAT",
    "BA", "IBM", "GE", "CAT", "GS", "HON", "MS", "SBUX", "DE", "PLD", "BLK", "AXP", "MDLZ", "GILD", "BKNG", "ISRG",
    "ADI", "LRCX", "TJX", "MMC", "VRTX", "REGN", "LMT", "UBER", "ABNB", "PANW", "SNOW", "PLTR", "COIN", "MAR",
    "FI", "SQ", "PYPL", "MO", "T", "VZ", "CMCSA", "PFE", "C", "WFC", "BAC", "RTX", "NEE", "SCHW", "MDT", "BMY",
    "CVS", "CI", "GGE", "EL", "ADP", "MMC", "CB", "SO", "DUK", "PGR", "SLB", "EOG", "BDX", "ITW", "CL", "APD",
    "ETN", "PH", "HUM", "BSX", "EW", "ILMN", "AON", "ICE", "MCO", "WM", "NOC", "GD", "FDX", "NSC", "CSX", "EMR",
    "SHW", "CTAS", "TT", "APH", "ECL", "ROP", "KLAC", "SNPS", "CDNS", "MAR", "HLT", "ORLY", "AZO", "ROST", "FAST",
    # ... PLUS MORE S&P 500 COMPONENTS
    "MMM", "A", "AAL", "AAP", "ABT", "ACGL", "ADM", "AEE", "AEP", "AES", "AFL", "AIG", "AIZ", "AJG", "AKAM", "ALB",
    "ALGN", "ALK", "ALL", "ALLE", "AMCR", "AME", "AMGN", "AMP", "AMT", "ANET", "ANSS", "AOS", "APA", "APTV", "ARE",
    "ATO", "AVB", "AVY", "AWK", "AXON", "BKR", "BALL", "BAX", "BBWI", "BBY", "BEN", "BF-B", "BG", "BIIB", "BIO",
    "BK", "BWA", "BXP", "CAG", "CAH", "CARR", "CBOE", "CBRE", "CCI", "CCL", "CDW", "CE", "CF", "CFG", "CHD", "CHRW",
    "CHTR", "CINF", "CLX", "CMA", "CMG", "CMI", "CMS", "CNA", "CNP", "COO", "CPB", "CPT", "CRL", "CTRA", "CTSH",
    "CTVA", "D", "DAL", "DAR", "DAY", "DD", "DFS", "DG", "DGX", "DHI", "DHR", "DLR", "DLTR", "DOC", "DOV", "DOW",
    "DPZ", "DRI", "DTE", "DVA", "DVN", "DXCM", "EA", "EBAY", "EFX", "EIX", "ELV", "ENPH", "ENTR", "EONG", "EPAM",
    "EQIX", "EQR", "EQT", "ESS", "ETR", "ETSY", "EVRG", "EXC", "EXPD", "EXPE", "EXR", "F", "FANG", "FDS", "FE",
    "FFIV", "FIS", "FITB", "FLT", "FMC", "FOX", "FOXA", "FRT", "FSLR", "FTV", "GEN", "GPC", "GRMN", "HAS", "HBAN",
    "HCA", "HES", "HIG", "HII", "HOLX", "HPE", "HPQ", "HRL", "HSY", "HWM", "IDXX", "IEX", "IFF", "INCY", "INVH",
    "IP", "IPG", "IQV", "IRM", "IVZ", "J", "JBHT", "JCI", "JKHY", "JNPR", "K", "KEY", "KEYS", "KHC", "KIM", "KMI",
    "KMX", "KR", "LDOS", "LEN", "LH", "LHX", "LKQ", "LNT", "LUV", "LVS", "LW", "LYB", "LYV", "MAA", "MAS", "MGM",
    "MHK", "MKC", "MKTX", "MLM", "MNST", "MOS", "MPC", "MPWR", "MRO", "MTB", "MTCH", "MTD", "MU", "NCLH", "NDAQ",
    "NDSN", "NEM", "NI", "NVR", "NWL", "NWS", "NWSA", "O", "ODFL", "OGN", "OKE", "OMC", "ON", "OTIS", "OXY", "PARA",
    "PAYC", "PAYX", "PCAR", "PCG", "PEAK", "PEG", "PEN", "PFG", "PHM", "PKG", "PLD", "PNR", "PNW", "PODD", "POOL",
    "PPG", "PPL", "PRU", "PSA", "PTC", "PWR", "PXD", "QRVO", "RCL", "RE", "REG", "RF", "RHI", "RJF", "RL", "RMD",
    "ROK", "ROL", "RSG", "SBAC", "SJM", "SNA", "SEDG", "SEE", "STX", "STE", "STT", "STZ", "SWK", "SWKS", "SYF",
    "SYY", "T", "TAP", "TDG", "TDY", "TECH", "TEL", "TER", "TFC", "TFX", "TGT", "TRGP", "TRMB", "TROW", "TRV",
    "TSCO", "TSN", "TTWO", "TYL", "UDR", "UHS", "ULTA", "URI", "USB", "VFC", "VICI", "VLO", "VMC", "VRSK", "VRSN",
    "VTR", "VTRS", "WAB", "WAT", "WBD", "WDC", "WEC", "WELL", "WST", "WTW", "WY", "WYNN", "XEL", "XYL", "YUM",
    "ZBH", "ZBRA", "ZION", "ZTS"
]

# Merge and Dedup
IND_STOCKS = list(set(IND_STOCKS))
US_STOCKS = list(set(US_STOCKS))

@st.cache_data(ttl=3600)  # Cache results for 1 hour to speed up
def get_screened_stocks(market="IND"):
    """
    Scans Top 500 stocks based on the selected market.
    """
    if market == "US":
        stock_list = US_STOCKS
        st.info(f"Scanning {len(stock_list)} Top US Stocks...")
    else:
        stock_list = IND_STOCKS
        st.info(f"Scanning {len(stock_list)} Top Indian Stocks...")

    valid_stocks = []
    
    # 1. BATCH DOWNLOAD
    # We use threads to download 500+ stocks efficiently
    try:
        data = yf.download(stock_list, period="3mo", progress=True, group_by='ticker', threads=True)
    except Exception as e:
        st.error(f"Download failed: {e}")
        return pd.DataFrame() 

    # 2. FILTER LOOP
    progress_bar = st.progress(0)
    total = len(stock_list)
    
    for idx, ticker in enumerate(stock_list):
        try:
            # Check if data exists for this ticker
            if ticker not in data.columns.levels[0]: continue
            
            df = data[ticker].dropna()
            if len(df) < 60: continue # Need at least 60 days for 50 EMA
            
            close = df['Close']
            volume = df['Volume']
            
            current_price = close.iloc[-1]
            current_vol = volume.iloc[-1]
            
            # --- FILTERS ---
            # 1. Price > $5 (US) or ₹20 (IN) to avoid penny stocks
            min_price = 5 if market == "US" else 20
            if current_price < min_price: continue
            
            # 2. Liquid only
            if current_vol < 50000: continue
            
            # 3. Technicals
            ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
            
            avg_vol = volume.rolling(20).mean().iloc[-1]
            if avg_vol == 0: continue
            
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
            
            # 4. Strategy: Uptrend + Momentum + Volume
            if (current_price > ema_50) and (55 < rsi < 75) and (current_vol > 1.2 * avg_vol):
                valid_stocks.append({
                    "Ticker": ticker,
                    "Price": round(current_price, 2),
                    "RSI": round(rsi, 1),
                    "Vol_Mult": round(current_vol / avg_vol, 1),
                })
        except:
            continue
        
        # Update progress less frequently to save UI redraw time
        if idx % 20 == 0:
            progress_bar.progress((idx + 1) / total)
            
    progress_bar.empty()
    
    # 3. RETURN SORTED DF
    res_df = pd.DataFrame(valid_stocks)
    if not res_df.empty:
        res_df = res_df.sort_values(by="Vol_Mult", ascending=False)
    
    return res_df
