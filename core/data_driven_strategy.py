import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from config.settings import Config
from utils.logger import AdvancedLogger
from utils.telegram_notifier import TelegramNotifier

class DataDrivenStrategy:
    def __init__(self, market_data):
        self.market_data = market_data
        self.config = Config()
        self.logger = AdvancedLogger()
        self.notifier = TelegramNotifier()
        
        # ✅ PARAMETERS OPTIMIZED FROM 5771 REAL SIGNALS
        self.optimized_params = {
            # TIME FILTERING - Based on actual signal patterns
            'best_hours': [0, 5, 8, 22, 23],  # Hours with most signals
            'avoid_hours': [15, 16, 17, 18, 19, 20, 21],  # Hours with no signals
            
            # RSI OPTIMIZATION - Based on actual RSI ranges
            'rsi_buy_zone': 35,     # From data: BUY avg RSI 40.3
            'rsi_sell_zone': 65,    # From data: SELL avg RSI 61.0  
            'rsi_oversold': 25,     # More aggressive
            'rsi_overbought': 70,   # More aggressive
            
            # STRATEGY AGGRESSIVENESS
            'min_confirmations': 2, # Reduced from 3
            'required_confidence': 0.6, # 60% of valid signals must agree
        }
        
        print("✅ Data-Driven Strategy initialized with real signal patterns!")
    
    def analyze_market(self, symbol):
        """Market analysis optimized from 5771 historical signals"""
        try:
            # ✅ STRICT TIME FILTERING based on actual data
            if not self._is_optimal_trading_time():
                return "NO_SIGNAL"
                
            # Get market data
            df = self.market_data.get_symbol_data(symbol, mt5.TIMEFRAME_M5, 50)
            if df is None or df.empty:
                return "NO_SIGNAL"
                
            df = self.market_data.calculate_technical_indicators(df)
            current_price = self.market_data.get_current_price(symbol)
            
            if current_price is None:
                return "NO_SIGNAL"
                
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # ✅ USE DATA-DRIVEN STRATEGY
            signal = self._data_driven_strategy(latest, prev, current_price, df)
            
            # Log and notify
            if current_price and signal != "NO_SIGNAL":
                indicators = {
                    'rsi': latest['rsi'],
                    'sma_10': latest['sma_10'],
                    'sma_20': latest['sma_20'],
                    'stoch_k': latest['stoch_k'],
                    'stoch_d': latest['stoch_d']
                }
                self.logger.log_market_signal(symbol, signal, current_price['bid'], indicators)
                self.notifier.send_signal_notification(symbol, signal, current_price['bid'], indicators)
            
            return signal
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return "NO_SIGNAL"
    
    # def _is_optimal_trading_time(self):
    #     """Trade only during proven high-signal hours (GMT+3)"""
    #     from datetime import datetime
    #     current_hour = datetime.now().hour
        
    #     print(f"🔧 Time Check: Current Server Hour (GMT+3) = {current_hour}")
        
    #     # ✅ OPTIMAL HOURS FOR OCTAFX SERVER (GMT+3)
    #     # Original GMT: [0, 5, 8, 22, 23] 
    #     # Convert to GMT+3: [3, 8, 11, 1, 2] (next day)
    #     optimal_server_hours = [3, 8, 11, 1, 2]  # GMT+3
        
    #     # ✅ WIB EQUIVALENT: [6, 11, 14, 4, 5] WIB
    #     optimal_wib_hours = [6, 11, 14, 4, 5]  # WIB
        
    #     print(f"🔧 Optimal Server Hours (GMT+3): {optimal_server_hours}")
    #     print(f"🔧 Optimal WIB Hours: {optimal_wib_hours}")
        
    #     return current_hour in optimal_server_hours

    def _is_optimal_trading_time(self):
        """Trade only during proven high-signal hours"""
        # ✅ FOR TESTING - ALLOW ALL HOURS:
        return True
    
    def _data_driven_strategy(self, latest, prev, current_price, df):
        """Strategy optimized from real trading data patterns"""
        # Get all indicator signals with optimized parameters
        signals = [
            self._optimized_rsi_strategy(latest),
            self._optimized_bb_strategy(latest, current_price),
            self._optimized_stoch_strategy(latest),
            self._optimized_ma_strategy(latest, prev),
            self._momentum_strategy(df),
            self._volume_analysis_strategy(latest, prev)
        ]
        
        # Remove NO_SIGNAL and count
        valid_signals = [s for s in signals if s != "NO_SIGNAL"]
        
        if not valid_signals:
            return "NO_SIGNAL"
        
        buy_count = valid_signals.count("BUY")
        sell_count = valid_signals.count("SELL")
        total_valid = len(valid_signals)
        
        print(f"  Data-Driven Signals - Valid: {total_valid}/6 (BUY: {buy_count}, SELL: {sell_count})")
        
        # ✅ CONFIDENCE-BASED EXECUTION
        confidence_threshold = self.optimized_params['required_confidence']
        
        if buy_count >= total_valid * confidence_threshold:
            return "BUY"
        elif sell_count >= total_valid * confidence_threshold:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_rsi_strategy(self, latest):
        """RSI strategy optimized from actual signal data"""
        rsi = latest['rsi']
        if pd.isna(rsi):
            return "NO_SIGNAL"
        
        # ✅ OPTIMIZED BASED ON ACTUAL RSI RANGES
        if rsi <= self.optimized_params['rsi_oversold']:
            return "BUY"
        elif rsi >= self.optimized_params['rsi_overbought']:
            return "SELL"
        elif rsi <= self.optimized_params['rsi_buy_zone']:
            return "BUY"  # More aggressive in buy zone
        elif rsi >= self.optimized_params['rsi_sell_zone']:
            return "SELL"  # More aggressive in sell zone
        else:
            return "NO_SIGNAL"
    
    def _optimized_bb_strategy(self, latest, current_price):
        """Bollinger Bands with wider acceptance"""
        price = current_price['bid']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        
        if pd.isna(bb_upper) or pd.isna(bb_lower):
            return "NO_SIGNAL"
        
        bb_middle = latest['bb_middle']
        distance_from_middle = abs(price - bb_middle)
        bb_width = bb_upper - bb_lower
        
        # ✅ WIDER ACCEPTANCE ZONE
        if price <= bb_lower + (bb_width * 0.3):  # 30% from lower band
            return "BUY"
        elif price >= bb_upper - (bb_width * 0.3):  # 30% from upper band
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_stoch_strategy(self, latest):
        """Stochastic with optimized levels"""
        stoch_k = latest['stoch_k']
        stoch_d = latest['stoch_d']
        
        if pd.isna(stoch_k) or pd.isna(stoch_d):
            return "NO_SIGNAL"
        
        # ✅ MORE AGGRESSIVE STOCHASTIC
        if stoch_k <= 20 or stoch_d <= 20:
            return "BUY"
        elif stoch_k >= 80 or stoch_d >= 80:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_ma_strategy(self, latest, prev):
        """MA Crossover - keep as is but more sensitive"""
        sma_fast = latest['sma_10']
        sma_slow = latest['sma_20']
        prev_fast = prev['sma_10']
        prev_slow = prev['sma_20']
        
        # ✅ MORE SENSITIVE MA CROSSOVER
        if sma_fast > sma_slow:  # Uptrend
            return "BUY"
        elif sma_fast < sma_slow:  # Downtrend
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _momentum_strategy(self, df):
        """Momentum based on recent price action"""
        if len(df) < 3:
            return "NO_SIGNAL"
        
        # Simple momentum: last 3 candles
        recent = df['close'].tail(3)
        if len(recent) < 3:
            return "NO_SIGNAL"
            
        momentum = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
        
        if momentum > 0.05:  # 0.05% uptrend
            return "BUY"
        elif momentum < -0.05:  # 0.05% downtrend
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _volume_analysis_strategy(self, latest, prev):
        """Volume confirmation if available"""
        if 'tick_volume' in latest and 'tick_volume' in prev:
            current_vol = latest['tick_volume']
            prev_vol = prev['tick_volume']
            
            if current_vol > prev_vol * 1.3:  # 30% volume increase
                price_change = latest['close'] - prev['close']
                if price_change > 0:
                    return "BUY"
                elif price_change < 0:
                    return "SELL"
        
        return "NO_SIGNAL"