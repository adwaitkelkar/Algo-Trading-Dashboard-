import streamlit as st
import yfinance as yf
from backtesting import Backtest, Strategy
import pandas as pd
import plotly.graph_objects as go
import importlib.util
import sys
import os
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
import screener
import inspect

st.set_page_config(layout="wide", page_title="Algo Terminal")

# --- MARKET CONFIG ---
MARKET_CONFIG = {
    "IND": {
        "timezone": "Asia/Kolkata",
        "open": dtime(9, 15),
        "close": dtime(15, 30),
        "suffix": ".NS",
        "name": "Indian Markets"
    },
    "US": {
        "timezone": "America/New_York",
        "open": dtime(9, 30),
        "close": dtime(16, 0),
        "suffix": "",
        "name": "US Markets"
    }
}

# --- DYNAMIC LOADER ---
def load_strategies_from_file(file_path):
    if not os.path.exists(file_path): return {}, f"File '{file_path}' not found."
    try:
        spec = importlib.util.spec_from_file_location("local_strategy", file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["local_strategy"] = module
        spec.loader.exec_module(module)
        return _extract_strategies(module), None
    except Exception as e: return {}, str(e)

def load_strategies_from_upload(uploaded_file):
    try:
        file_content = uploaded_file.read()
        module_name = "uploaded_strategy"
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)
        exec(file_content, module.__dict__)
        sys.modules[module_name] = module
        return _extract_strategies(module), None
    except Exception as e:
        return {}, f"Error loading file: {str(e)}"

def _extract_strategies(module):
    strategies = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            if issubclass(obj, Strategy) and obj is not Strategy:
                strategies[name] = obj
    return strategies

def get_market_status(market_code):
    config = MARKET_CONFIG[market_code]
    tz = ZoneInfo(config["timezone"])
    now = datetime.now(tz)
    current_time = now.time()
    is_weekday = now.weekday() < 5 
    is_open = is_weekday and (config["open"] <= current_time <= config["close"])
    return is_open, now, config["name"]

def resample_data(df, interval):
    if interval == "4h" and not df.empty:
        agg_dict = {'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}
        return df.resample('4h').agg(agg_dict).dropna()
    return df

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚀 Algo Terminal")
    
    st.header("1. Select Market")
    market_mode = st.radio("Region", ["🇮🇳 India", "🇺🇸 USA"], horizontal=True)
    market_code = "IND" if "India" in market_mode else "US"
    
    st.header("2. Screener")
    if st.button(f"🔍 Scan {market_code} Stocks"):
        with st.spinner(f"Scanning {market_code} Universe (Top 500)..."):
            try:
                screened_df = screener.get_screened_stocks(market=market_code)
                if not screened_df.empty:
                    top_pick = screened_df.iloc[0]['Ticker']
                    st.session_state['ticker'] = top_pick
                    st.success(f"Found {len(screened_df)} setups!")
                    st.dataframe(screened_df[['Ticker', 'Price', 'Vol_Mult', 'RSI']], hide_index=True)
                else:
                    st.warning("No stocks found.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    st.header("3. Config")
    default_ticker = st.session_state.get('ticker', "TATASTEEL.NS" if market_code == "IND" else "AAPL")
    user_ticker = st.text_input("Stock Symbol", default_ticker).upper()
    
    if market_code == "IND" and not user_ticker.endswith(".NS"): final_ticker = user_ticker + ".NS"
    elif market_code == "US": final_ticker = user_ticker.replace(".NS", "")
    else: final_ticker = user_ticker

    initial_cash = st.number_input("Capital", value=5000 if market_code=="IND" else 10000)
    
    # --- STRATEGY SOURCE ---
    st.divider()
    st.header("4. Strategy Source")
    strat_source = st.radio("Load Strategy From:", ["Default File (strategy.py)", "Upload Custom File"])
    
    strategies_dict = {}
    load_error = None

    if strat_source == "Default File (strategy.py)":
        strategies_dict, load_error = load_strategies_from_file("strategy.py")
    else:
        # --- AI PROMPT HELPER ---
        with st.expander("🤖 Use this prompt to Generate Strategy with AI"):
            st.caption("Copy this prompt to ChatGPT/Claude to generate a compatible strategy file:")
            ai_prompt = """
You are an expert Python developer for Algorithmic Trading. 
Write a complete Python script that defines a trading strategy class compatible with the `backtesting.py` library.

REQUIREMENTS:
1. Import necessary libraries: `from backtesting import Strategy`, `from backtesting.lib import crossover`, `import pandas as pd`, `import numpy as np`.
2. Define helper functions for indicators (EMA, RSI, ADX) at the top of the file. IMPORTANT: These functions must accept raw numpy arrays (from `backtesting.py`) but convert them to `pd.Series` internally before calculating, to avoid AttributeError.
3. Create a class inheriting from `Strategy`.
4. In `init()`, calculate indicators using `self.I(IndicatorFunc, self.data.Close, period)`.
5. In `next()`, implement the trading logic (Entry/Exit).
6. Ensure the code is bug-free and handles Stop Loss / Take Profit correctly.

MY STRATEGY IDEA:
[TYPE YOUR STRATEGY HERE, e.g., Buy when RSI < 30 and Price > 200 EMA]
            """
            st.code(ai_prompt, language="text")
        
        uploaded_file = st.file_uploader("Upload .py file", type=["py"])
        if uploaded_file:
            strategies_dict, load_error = load_strategies_from_upload(uploaded_file)
            if not load_error and strategies_dict:
                st.success(f"Loaded {len(strategies_dict)} strategies!")
        else:
            st.info("Upload your AI-generated strategy file here.")

    st.divider()
    
    st.header("5. Backtest Settings")
    timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h", "4h", "1d", "1wk"])
    
    if timeframe in ["5m", "15m"]: 
        dur_options = ["1mo", "60d"]
        default_dur = 1
    elif timeframe in ["1h", "4h"]: 
        dur_options = ["1mo", "6mo", "1y", "2y"]
        default_dur = 2
    else: 
        dur_options = ["1y", "2y", "3y", "5y", "10y", "max"]
        default_dur = 2

    duration = st.selectbox("Duration", dur_options, index=default_dur)
    
    if st.button("🔄 Reload App"): st.cache_data.clear(); st.rerun()

    st.divider()
    is_open, now_tz, market_name = get_market_status(market_code)
    st.caption(f"{market_name}")
    if is_open: st.success(f"🟢 OPEN ({now_tz.strftime('%H:%M %Z')})")
    else: st.error(f"🔴 CLOSED ({now_tz.strftime('%H:%M %Z')})")

# --- MAIN ---
st.title(f"📈 {final_ticker} ({market_code})")

if load_error:
    st.error(f"Strategy Error: {load_error}")
    st.stop()
if not strategies_dict:
    st.warning("No strategies found. Please ensure your file defines a class inheriting from 'Backtesting.Strategy'.")
    st.stop()

tab1, tab2 = st.tabs(["📊 Backtest Engine", "⚡ Live Monitor"])

with tab1:
    mode = st.radio("Operation Mode", ["Single Strategy", "Compare Two Strategies"], horizontal=True)
    
    def fetch_data():
        with st.spinner(f"Fetching {timeframe} data..."):
            fetch_int = "1h" if timeframe == "4h" else timeframe
            try:
                df = yf.download(final_ticker, period=duration, interval=fetch_int, progress=False)
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                if timeframe == "4h": df = resample_data(df, "4h")
                return df
            except Exception as e:
                st.error(f"Error: {e}")
                return pd.DataFrame()

    if mode == "Single Strategy":
        selected_strat_name = st.selectbox("Select Strategy", list(strategies_dict.keys()))
        StrategyClass = strategies_dict[selected_strat_name]
        
        if st.button(f"Run {selected_strat_name}"):
            df = fetch_data()
            if not df.empty:
                bt = Backtest(df, StrategyClass, cash=initial_cash, commission=0.001)
                stats = bt.run()
                
                c1, c2, c3, c4 = st.columns(4)
                sym = "₹" if market_code == "IND" else "$"
                c1.metric("Equity", f"{sym}{stats['Equity Final [$]']:.2f}", f"{stats['Return [%]']:.2f}%")
                c2.metric("Drawdown", f"{stats['Max. Drawdown [%]']:.2f}%")
                c3.metric("Win Rate", f"{stats['Win Rate [%]']:.1f}%")
                c4.metric("Trades", stats['# Trades'])
                st.line_chart(stats['_equity_curve']['Equity'])
                st.dataframe(stats['_trades'])

    elif mode == "Compare Two Strategies":
        if len(strategies_dict) < 2:
            st.error("Need at least 2 strategies to compare.")
        else:
            c1, c2 = st.columns(2)
            with c1: strat_a_name = st.selectbox("Strategy A", list(strategies_dict.keys()), index=0)
            with c2: strat_b_name = st.selectbox("Strategy B", list(strategies_dict.keys()), index=min(1, len(strategies_dict)-1))
            
            if st.button("⚔️ Run Comparison"):
                df = fetch_data()
                if not df.empty:
                    bt_a = Backtest(df, strategies_dict[strat_a_name], cash=initial_cash, commission=0.001)
                    stats_a = bt_a.run()
                    bt_b = Backtest(df, strategies_dict[strat_b_name], cash=initial_cash, commission=0.001)
                    stats_b = bt_b.run()
                    
                    col_a, col_b = st.columns(2)
                    sym = "₹" if market_code == "IND" else "$"
                    
                    with col_a:
                        st.subheader(f"🅰️ {strat_a_name}")
                        st.metric("Equity", f"{sym}{stats_a['Equity Final [$]']:.2f}", f"{stats_a['Return [%]']:.2f}%")
                        st.metric("Drawdown", f"{stats_a['Max. Drawdown [%]']:.2f}%")
                        st.metric("Win Rate", f"{stats_a['Win Rate [%]']:.1f}%")
                        st.line_chart(stats_a['_equity_curve']['Equity'])
                        
                    with col_b:
                        st.subheader(f"🅱️ {strat_b_name}")
                        st.metric("Equity", f"{sym}{stats_b['Equity Final [$]']:.2f}", f"{stats_b['Return [%]']:.2f}%")
                        st.metric("Drawdown", f"{stats_b['Max. Drawdown [%]']:.2f}%")
                        st.metric("Win Rate", f"{stats_b['Win Rate [%]']:.1f}%")
                        st.line_chart(stats_b['_equity_curve']['Equity'])

with tab2:
    if not is_open: st.warning(f"{market_name} is Closed. Live monitor inactive.")
    else:
        st_autorefresh(interval=60000)
        live_strat_name = st.selectbox("Live Strategy", list(strategies_dict.keys()))
        LiveStrategy = strategies_dict[live_strat_name]
        
        try:
            t = yf.Ticker(final_ticker)
            price = t.fast_info['last_price']
        except: price = 0.0
            
        df_live = yf.download(final_ticker, period="1d", interval="1m", progress=False)
        if isinstance(df_live.columns, pd.MultiIndex): df_live.columns = df_live.columns.get_level_values(0)
        
        if not df_live.empty:
            bt = Backtest(df_live, LiveStrategy, cash=initial_cash, commission=0.001)
            stats = bt.run()
            c1, c2, c3 = st.columns(3)
            sym = "₹" if market_code == "IND" else "$"
            c1.metric("Price", f"{sym}{price:.2f}")
            c2.metric("Day Equity", f"{sym}{stats['Equity Final [$]']:.2f}")
            tr = stats['_trades']
            sig = "🟢 LONG" if not tr.empty and pd.isna(tr.iloc[-1]['ExitTime']) else "⚪ WAIT"
            c3.metric("Signal", sig)
            fig = go.Figure(data=[go.Candlestick(x=df_live.index, open=df_live['Open'], high=df_live['High'], low=df_live['Low'], close=df_live['Close'])])
            fig.update_layout(height=450, title="Real-Time (1m)")
            st.plotly_chart(fig, use_container_width=True)
