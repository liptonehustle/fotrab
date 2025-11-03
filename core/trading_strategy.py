import MetaTrader5 as mt5
import pandas as pd
from config.settings import Config
from utils.logger import AdvancedLogger
from utils.telegram_notifier import TelegramNotifier  # ✅ Telegram only

class TradingStrategy:
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
        """Improved scalping strategy with better signal combination"""
        # Strategy 1: RSI Mean Reversion
        rsi_signal = self._rsi_strategy(latest, prev)
        
        # Strategy 2: Moving Average Crossover
        ma_signal = self._ma_crossover_strategy(latest, prev)
        
        # Strategy 3: Bollinger Bands
        bb_signal = self._bollinger_bands_strategy(latest, current_price)
        
        # Strategy 4: Stochastic
        stoch_signal = self._stochastic_strategy(latest, prev)
        
        # Strategy 5: Price Action Momentum
        momentum_signal = self._momentum_strategy(latest, prev)
        
        # Combine signals (OR logic - lebih aggressive untuk scalping)
        signals = [rsi_signal, ma_signal, bb_signal, stoch_signal, momentum_signal]
        buy_signals = signals.count("BUY")
        sell_signals = signals.count("SELL")
        
        print(f"  Signals - RSI: {rsi_signal}, MA: {ma_signal}, BB: {bb_signal}, "
            f"Stoch: {stoch_signal}, Momentum: {momentum_signal}")
        
        # Modified: Lebih aggressive untuk scalping (2/5 signals cukup)
        if buy_signals >= 2:
            return "BUY"
        elif sell_signals >= 2:
            return "SELL"
        else:
            return "NO_SIGNAL"

    def _momentum_strategy(self, latest, prev):
        """Price action momentum strategy"""
        # Check for strong momentum moves
        price_change = latest['close'] - prev['close']
        price_range = latest['high'] - latest['low']
        
        # Strong bullish momentum
        if price_change > 0 and price_change > (price_range * 0.3):
            return "BUY"
        # Strong bearish momentum  
        elif price_change < 0 and abs(price_change) > (price_range * 0.3):
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _rsi_strategy(self, latest, prev):
        """RSI Mean Reversion Strategy"""
        rsi = latest['rsi']
        
        if pd.isna(rsi):
            return "NO_SIGNAL"
            
        # RSI oversold dengan konfirmasi reversal
        if rsi < 30 and latest['rsi'] > prev['rsi']:
            return "BUY"
        # RSI overbought dengan konfirmasi reversal  
        elif rsi > 70 and latest['rsi'] < prev['rsi']:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _ma_crossover_strategy(self, latest, prev):
        """Moving Average Crossover Strategy"""
        # Fast MA crossing above slow MA
        if (latest['sma_10'] > latest['sma_20'] and 
            prev['sma_10'] <= prev['sma_20']):
            return "BUY"
        # Fast MA crossing below slow MA
        elif (latest['sma_10'] < latest['sma_20'] and 
              prev['sma_10'] >= prev['sma_20']):
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _bollinger_bands_strategy(self, latest, current_price):
        """Bollinger Bands Strategy"""
        price = current_price['bid']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        bb_middle = latest['bb_middle']
        
        if pd.isna(bb_upper) or pd.isna(bb_lower):
            return "NO_SIGNAL"
        
        # Price touching lower band (oversold)
        if price <= bb_lower:
            return "BUY"
        # Price touching upper band (overbought)
        elif price >= bb_upper:
            return "SELL"
        else:
            return "NO_SIGNAL"
    
    def _stochastic_strategy(self, latest, prev):
        """Stochastic Oscillator Strategy"""
        stoch_k = latest['stoch_k']
        stoch_d = latest['stoch_d']
        
        if pd.isna(stoch_k) or pd.isna(stoch_d):
            return "NO_SIGNAL"
            
        # Stochastic crossover dari oversold
        if (stoch_k < 20 and stoch_d < 20 and 
            stoch_k > stoch_d and prev['stoch_k'] <= prev['stoch_d']):
            return "BUY"
        # Stochastic crossover dari overbought
        elif (stoch_k > 80 and stoch_d > 80 and 
              stoch_k < stoch_d and prev['stoch_k'] >= prev['stoch_d']):
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