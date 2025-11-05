import MetaTrader5 as mt5
import pandas as pd
from config.settings import Config
from utils.logger import AdvancedLogger
from utils.telegram_notifier import TelegramNotifier  # ✅ Telegram only

class TradingStrategy:
    def is_good_trading_session(self):
        """Filter untuk trade hanya di session yang volatile"""
        from datetime import datetime
        current_hour = datetime.now().hour
        current_minute = datetime.now().minute
        
        # ✅ TRADE HANYA DI HIGH VOLATILITY SESSIONS:
        # London Open: 8:00-12:00 GMT
        # New York Open: 13:00-17:00 GMT  
        # Overlap: 13:00-16:00 GMT (Best volatility)
        
        if (8 <= current_hour <= 12) or (13 <= current_hour <= 17):
            return True
        return False
    def get_multi_timeframe_data(self, symbol, count=50):
        """Get data from multiple timeframes untuk confirmation"""
        try:
            # M5 - untuk entry
            m5_data = self.get_symbol_data(symbol, mt5.TIMEFRAME_M5, count)
            
            # M15 - untuk trend confirmation  
            m15_data = self.get_symbol_data(symbol, mt5.TIMEFRAME_M15, count)
            
            if m5_data is not None and m15_data is not None:
                m5_data = self.calculate_technical_indicators(m5_data)
                m15_data = self.calculate_technical_indicators(m15_data)
                
                return {
                    'm5': m5_data,
                    'm15': m15_data
                }
            return None
            
        except Exception as e:
            print(f"❌ Error getting multi timeframe data: {e}")
            return None

    def __init__(self, market_data):
        self.market_data = market_data
        self.config = Config()
        self.logger = AdvancedLogger()
        self.notifier = TelegramNotifier()  # ✅ Telegram only
        
    def analyze_market(self, symbol):
        """Analyze market and generate trading signals"""
        try:
            # Get market data dengan indicators
            df = self.market_data.get_symbol_data(symbol, mt5.TIMEFRAME_M5, 50)
            if df is None or df.empty:
                return "NO_SIGNAL"
                
            df = self.market_data.calculate_technical_indicators(df)
            current_price = self.market_data.get_current_price(symbol)
            
            if current_price is None:
                return "NO_SIGNAL"
                
            # Get latest data point
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # SCALPING STRATEGY: Momentum + Mean Reversion
            signal = self._scalping_strategy(latest, prev, current_price)
            
            # Log the signal (even if no trade)
            if current_price:
                indicators = {
                    'rsi': latest['rsi'],
                    'sma_10': latest['sma_10'],
                    'sma_20': latest['sma_20'],
                    'stoch_k': latest['stoch_k'],
                    'stoch_d': latest['stoch_d']
                }
                self.logger.log_market_signal(symbol, signal, current_price['bid'], indicators)
                
                # ✅ TELEGRAM NOTIFICATION - Trading signals
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
    
    def _scalping_strategy(self, latest, prev, current_price):
        """Improved with trend confirmation"""
        # Get all signals
        rsi_signal = self._rsi_strategy(latest, prev)
        ma_signal = self._ma_crossover_strategy(latest, prev)
        bb_signal = self._bollinger_bands_strategy(latest, current_price)
        stoch_signal = self._stochastic_strategy(latest, prev)
        momentum_signal = self._momentum_strategy(latest, prev)
        
        # Add trend confirmation (you'll need to pass df to this method)
        # trend_signal = self._trend_confirmation(df)
        
        signals = [rsi_signal, ma_signal, bb_signal, stoch_signal, momentum_signal]
        
        # Count only valid signals
        valid_signals = [s for s in signals if s != "NO_SIGNAL"]
        
        if not valid_signals:
            return "NO_SIGNAL"
        
        buy_signals = valid_signals.count("BUY")
        sell_signals = valid_signals.count("SELL")
        
        print(f"  Valid signals: {len(valid_signals)}/{len(signals)} (BUY: {buy_signals}, SELL: {sell_signals})")
        
        # ✅ MAJORITY RULES: Execute if majority of valid signals agree
        total_valid = len(valid_signals)
        if buy_signals / total_valid >= 0.6:  # 60% of valid signals are BUY
            return "BUY"
        elif sell_signals / total_valid >= 0.6:  # 60% of valid signals are SELL
            return "SELL"
        else:
            return "NO_SIGNAL"

    def _rsi_strategy(self, latest, prev):
        """More sensitive RSI levels"""
        rsi = latest['rsi']
        
        if pd.isna(rsi):
            return "NO_SIGNAL"
        
        # ✅ WIDER RSI RANGE: 20-80 (dari 25-75)
        if rsi < 35:  # More sensitive oversold
            return "BUY"
        elif rsi > 65:  # More sensitive overbought
            return "SELL"
        else:
            return "NO_SIGNAL"

    def _bollinger_bands_strategy(self, latest, current_price):
        """More sensitive Bollinger Bands"""
        price = current_price['bid']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        
        if pd.isna(bb_upper) or pd.isna(bb_lower):
            return "NO_SIGNAL"
        
        bb_middle = latest['bb_middle']
        bb_width = bb_upper - bb_lower
        
        # ✅ MORE SENSITIVE: Price within 20% of bands (dari 10%)
        if price <= (bb_lower + bb_width * 0.2):
            return "BUY"
        elif price >= (bb_upper - bb_width * 0.2):
            return "SELL"
        else:
            return "NO_SIGNAL"

    def _stochastic_strategy(self, latest, prev):
        """More sensitive Stochastic"""
        stoch_k = latest['stoch_k']
        stoch_d = latest['stoch_d']
        
        if pd.isna(stoch_k) or pd.isna(stoch_d):
            return "NO_SIGNAL"
        
        # ✅ WIDER STOCHASTIC RANGE: 15-85 (dari 20-80)
        if stoch_k < 25 or stoch_d < 25:  # More sensitive oversold
            return "BUY"
        elif stoch_k > 75 or stoch_d > 75:  # More sensitive overbought
            return "SELL"
        else:
            return "NO_SIGNAL"
        
    def _trend_confirmation(self, df):
        """Simple trend confirmation"""
        if len(df) < 10:
            return "NO_SIGNAL"
        
        # Calculate short-term trend using last 5 candles
        recent_closes = df['close'].tail(5)
        if len(recent_closes) < 5:
            return "NO_SIGNAL"
        
        # Simple linear regression for trend
        price_change = recent_closes.iloc[-1] - recent_closes.iloc[0]
        avg_price = recent_closes.mean()
        
        if price_change > (avg_price * 0.0005):  # 0.05% uptrend
            return "BUY"
        elif price_change < -(avg_price * 0.0005):  # 0.05% downtrend
            return "SELL"
        else:
            return "NO_SIGNAL"

# Test function
def test_strategy():
    from core.mt5_connector import MT5Connector
    from core.market_data import MarketData
    
    print("Testing Trading Strategy...")
    connector = MT5Connector()
    
    if connector.connect():
        market_data = MarketData(connector)
        strategy = TradingStrategy(market_data)
        
        # Test strategy untuk semua pairs
        pairs = connector.config.get_market_settings()['default_pairs']
        
        for pair in pairs:
            print(f"\n🎯 Analyzing {pair}...")
            signal = strategy.analyze_market(pair)
            print(f"  Final Signal: {signal}")
        
        connector.disconnect()

if __name__ == "__main__":
    test_strategy()