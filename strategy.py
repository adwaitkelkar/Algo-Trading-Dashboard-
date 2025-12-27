import pandas as pd
import numpy as np
import math
from backtesting import Strategy
from backtesting.lib import crossover

# --- INDICATORS ---
def EMA(values, period):
    series = pd.Series(values)
    return series.ewm(span=period, adjust=False).mean().values

def RSI(values, period=14):
    series = pd.Series(values)
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return (100 - (100 / (1 + rs))).values

def ADX(high, low, close, period=14):
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
    minus_di = 100 * (abs(minus_dm).ewm(alpha=1/period).mean() / atr)
    
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()
    return adx.fillna(0).values

# --- STRATEGY 1: MOMENTUM SWING ---
class MomentumSwing(Strategy):
    n1 = 20
    n2 = 50
    rsi_period = 14
    adx_period = 14
    adx_threshold = 25
    stop_loss_pct = 0.05
    take_profit_pct = 0.15
    max_risk_amount = 1000

    def init(self):
        self.ema1 = self.I(EMA, self.data.Close, self.n1)
        self.ema2 = self.I(EMA, self.data.Close, self.n2)
        self.rsi = self.I(RSI, self.data.Close, self.rsi_period)
        self.adx = self.I(ADX, self.data.High, self.data.Low, self.data.Close, self.adx_period)

    def next(self):
        price = self.data.Close[-1]
        
        is_trending = self.adx[-1] > self.adx_threshold
        has_momentum = self.rsi[-1] > 50
        trend_up = self.ema1[-1] > self.ema2[-1]
        crossover_up = crossover(self.ema1, self.ema2)
        
        if is_trending and has_momentum and not self.position:
            if crossover_up or (trend_up and self.rsi[-1] < 70):
                sl_price = price * (1 - self.stop_loss_pct)
                risk_per_share = price - sl_price
                if risk_per_share > 0:
                    qty_risk = self.max_risk_amount / risk_per_share
                else:
                    qty_risk = 0
                qty_cash = (self.equity * 0.95) / price
                final_qty = math.floor(min(qty_risk, qty_cash))
                
                if final_qty > 0:
                    self.buy(size=final_qty, sl=sl_price, tp=price * (1 + self.take_profit_pct))

        elif self.position:
            if crossover(self.ema2, self.ema1):
                self.position.close()

# --- STRATEGY 2: MEAN REVERSION ---
class MeanReversion(Strategy):
    rsi_period = 14
    oversold = 30
    overbought = 70
    
    def init(self):
        self.rsi = self.I(RSI, self.data.Close, self.rsi_period)

    def next(self):
        if not self.position:
            if self.rsi[-1] < self.oversold:
                self.buy()
        elif self.position:
            if self.rsi[-1] > self.overbought:
                self.position.close()

# --- STRATEGY 3: EMA SPREAD ---
class EMASpread(Strategy):
    n_fast = 21
    n_mid = 50
    n_slow = 100
    n_adx = 14
    adx_threshold = 25
    max_risk = 1000          
    sl_swing_lookback = 10   

    def init(self):
        self.ema21 = self.I(EMA, self.data.Close, self.n_fast)
        self.ema50 = self.I(EMA, self.data.Close, self.n_mid)
        self.ema100 = self.I(EMA, self.data.Close, self.n_slow)
        self.adx = self.I(ADX, self.data.High, self.data.Low, self.data.Close, self.n_adx)

    def next(self):
        price = self.data.Close[-1]
        
        is_uptrend = (self.ema21[-1] > self.ema50[-1]) and (self.ema21[-1] > self.ema100[-1])
        is_reversal = (self.ema21[-1] < self.ema50[-1]) and (self.ema21[-1] < self.ema100[-1])
        strong_trend = self.adx[-1] > self.adx_threshold

        # ENTRY
        if not self.position:
            if is_uptrend and strong_trend:
                lookback_idx = min(len(self.data.Low), self.sl_swing_lookback)
                if lookback_idx > 0:
                    recent_lows = self.data.Low[-lookback_idx:]
                    sl_price = min(recent_lows)
                else:
                    sl_price = price * 0.98

                if sl_price >= price:
                    sl_price = price * 0.98
                
                risk_per_share = price - sl_price
                
                if risk_per_share > 0:
                    qty_risk = self.max_risk / risk_per_share
                    qty_cash = (self.equity * 0.98) / price
                    final_qty = math.floor(min(qty_risk, qty_cash))
                    
                    if final_qty > 0:
                        self.buy(size=final_qty, sl=sl_price)
        
        # EXIT
        elif self.position:
            if is_reversal:
                self.position.close()
            
            else:
                # --- BULLETPROOF TRAILING STOP LOSS ---
                try:
                    # Safely access current Stop Loss
                    current_sl = self.position.sl
                    
                    # If SL exists and is valid number
                    if current_sl is not None and not math.isnan(current_sl):
                        # Move SL up if 50 EMA is higher than current SL
                        if self.ema50[-1] > current_sl:
                            self.position.sl = self.ema50[-1]
                            
                except Exception:
                    # If anything goes wrong reading/setting SL, ignore and continue
                    pass
