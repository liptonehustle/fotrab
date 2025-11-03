import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config.settings import Config

class MarketData:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        self.config = Config()
        
    def get_symbol_data(self, symbol, timeframe=mt5.TIMEFRAME_M5, count=100):
        """Get historical data for a symbol"""
        try:
            if not self.mt5.connected:
                print("❌ Not connected to MT5")
                return None
                
            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                print(f"❌ No data for {symbol}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            print(f"✅ Got {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            print(f"❌ Error getting data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol):
        """Get current bid/ask price"""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid
            }
        except Exception as e:
            print(f"❌ Error getting price for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Calculate basic technical indicators for scalping"""
        try:
            # RSI
            df['rsi'] = self.calculate_rsi(df['close'])
            
            # Moving Averages
            df['sma_10'] = df['close'].rolling(10).mean()
            df['sma_20'] = df['close'].rolling(20).mean()
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(20).mean()
            bb_std = df['close'].rolling(20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # Stochastic
            df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(df)
            
            return df
            
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return df
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_stochastic(self, df, period=14):
        """Calculate Stochastic oscillator"""
        low_min = df['low'].rolling(period).min()
        high_max = df['high'].rolling(period).max()
        
        stoch_k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(3).mean()
        
        return stoch_k, stoch_d

# Test function
def test_market_data():
    from core.mt5_connector import MT5Connector
    
    print("Testing Market Data...")
    connector = MT5Connector()
    
    if connector.connect():
        market_data = MarketData(connector)
        
        # Test get EURUSD data
        df = market_data.get_symbol_data("EURUSD", mt5.TIMEFRAME_M5, 50)
        if df is not None:
            df = market_data.calculate_technical_indicators(df)
            print(f"Latest EURUSD data:")
            print(f"  Close: {df['close'].iloc[-1]}")
            print(f"  RSI: {df['rsi'].iloc[-1]:.2f}")
            print(f"  SMA10: {df['sma_10'].iloc[-1]:.5f}")
            print(f"  SMA20: {df['sma_20'].iloc[-1]:.5f}")
        
        # Test current price
        price = market_data.get_current_price("EURUSD")
        if price:
            print(f"Current EURUSD - Bid: {price['bid']:.5f}, Ask: {price['ask']:.5f}, Spread: {price['spread']:.5f}")
        
        connector.disconnect()

if __name__ == "__main__":
    test_market_data()