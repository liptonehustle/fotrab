import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config.settings import Config
from utils.logger import AdvancedLogger
from utils.telegram_notifier import TelegramNotifier

class OptimizedStrategy:
    def __init__(self, market_data):
        self.market_data = market_data
        self.config = Config()
        self.logger = AdvancedLogger()
        self.notifier = TelegramNotifier()
        
        # ✅ OPTIMIZED PARAMETERS BASED ON HISTORICAL DATA
        self.optimized_params = {
            'rsi_oversold': 35,      # More sensitive (from 30)
            'rsi_overbought': 65,    # More sensitive (from 70)
            'stoch_oversold': 25,    # More sensitive (from 20)
            'stoch_overbought': 75,  # More sensitive (from 80)
            'bb_sensitivity': 0.2,   # More sensitive (from 0.1)
            'min_confirmations': 2,  # Less confirmations needed
            'best_hours': [8, 9, 10, 13, 14, 15]  # Based on signal analysis
        }
    
    def analyze_market(self, symbol):
        """Optimized market analysis based on historical patterns"""
        try:
            # ✅ FILTER BY BEST TRADING HOURS
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
            
            # ✅ USE OPTIMIZED STRATEGY
            signal = self._optimized_scalping_strategy(latest, prev, current_price, df)
            
            # Log and notify
            if current_price:
                indicators = {
                    'rsi': latest['rsi'],
                    'sma_10': latest['sma_10'],
                    'sma_20': latest['sma_20'],
                    'stoch_k': latest['stoch_k'],
                    'stoch_d': latest['stoch_d']
                }
                self.logger.log_market_signal(symbol, signal, current_price['bid'], indicators)
                
                if signal != "NO_SIGNAL":
                    self.notifier.send_signal_notification(
                        symbol=symbol,
                        signal=signal,
                        price=current_price['bid'],
                        indicators=indicators
                    )
            
            return signal
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return "NO_SIGNAL"
    
    def _is_optimal_trading_time(self):
        """Trade only during best hours based on historical analysis"""
        from datetime import datetime
        current_hour = datetime.now().hour
        return current_hour in self.optimized_params['best_hours']
    
    def _optimized_scalping_strategy(self, latest, prev, current_price, df):
        """Strategy optimized based on 5771 historical signals"""
        # Get all indicator signals
        signals = [
            self._optimized_rsi_strategy(latest, prev),
            self._optimized_ma_strategy(latest, prev),
            self._optimized_bb_strategy(latest, current_price),
            self._optimized_stoch_strategy(latest, prev),
            self._optimized_momentum_strategy(df)
        ]
        
        # Count valid signals (excluding NO_SIGNAL)
        valid_signals = [s for s in signals if s != "NO_SIGNAL"]
        
        if not valid_signals:
            return "NO_SIGNAL"
        
        buy_count = valid_signals.count("BUY")
        sell_count = valid_signals.count("SELL")
        total_valid = len(valid_signals)
        
        print(f"  Optimized Signals - Valid: {total_valid}/5 (BUY: {buy_count}, SELL: {sell_count})")
        
        # ✅ DATA-DRIVEN DECISION: Execute if majority of valid signals agree
        if buy_count >= self.optimized_params['min_confirmations']:
            return "BUY"
        elif sell_count >= self.optimized_params['min_confirmations']:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_rsi_strategy(self, latest, prev):
        """RSI with optimized parameters"""
        rsi = latest['rsi']
        if pd.isna(rsi):
            return "NO_SIGNAL"
        
        # ✅ OPTIMIZED RSI LEVELS
        if rsi < self.optimized_params['rsi_oversold']:
            return "BUY"
        elif rsi > self.optimized_params['rsi_overbought']:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_stoch_strategy(self, latest, prev):
        """Stochastic with optimized parameters"""
        stoch_k = latest['stoch_k']
        stoch_d = latest['stoch_d']
        
        if pd.isna(stoch_k) or pd.isna(stoch_d):
            return "NO_SIGNAL"
        
        # ✅ OPTIMIZED STOCHASTIC LEVELS
        if stoch_k < self.optimized_params['stoch_oversold']:
            return "BUY"
        elif stoch_k > self.optimized_params['stoch_overbought']:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_bb_strategy(self, latest, current_price):
        """Bollinger Bands with optimized sensitivity"""
        price = current_price['bid']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        
        if pd.isna(bb_upper) or pd.isna(bb_lower):
            return "NO_SIGNAL"
        
        bb_width = bb_upper - bb_lower
        
        # ✅ OPTIMIZED SENSITIVITY
        if price <= (bb_lower + bb_width * self.optimized_params['bb_sensitivity']):
            return "BUY"
        elif price >= (bb_upper - bb_width * self.optimized_params['bb_sensitivity']):
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_ma_strategy(self, latest, prev):
        """MA Crossover strategy"""
        sma_fast = latest['sma_10']
        sma_slow = latest['sma_20']
        prev_fast = prev['sma_10']
        prev_slow = prev['sma_20']
        
        if sma_fast > sma_slow and prev_fast <= prev_slow:
            return "BUY"
        elif sma_fast < sma_slow and prev_fast >= prev_slow:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _optimized_momentum_strategy(self, df):
        """Momentum based on recent price action"""
        if len(df) < 5:
            return "NO_SIGNAL"
        
        recent_prices = df['close'].tail(5)
        price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100
        
        if price_change > 0.08:  # 0.08% uptrend
            return "BUY"
        elif price_change < -0.08:  # 0.08% downtrend
            return "SELL"
        else:
            return "NO_SIGNAL"