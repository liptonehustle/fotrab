import pandas as pd
import numpy as np
from datetime import datetime

class SignalAnalyzer:
    def __init__(self):
        self.log_dir = "logs"
    
    def analyze_signal_patterns(self):
        """Analyze patterns in generated signals"""
        print("🔍 ANALYZING SIGNAL PATTERNS...")
        print("=" * 60)
        
        try:
            signals_df = pd.read_csv(f'{self.log_dir}/signals.csv')
            
            if signals_df.empty:
                print("❌ No signals data found")
                return
            
            # Convert timestamp to datetime
            signals_df['datetime'] = pd.to_datetime(signals_df['timestamp'], unit='s')
            signals_df['hour'] = signals_df['datetime'].dt.hour
            
            print(f"📊 Total Signals: {len(signals_df)}")
            print(f"📈 BUY Signals: {len(signals_df[signals_df['signal'] == 'BUY'])}")
            print(f"📉 SELL Signals: {len(signals_df[signals_df['signal'] == 'SELL'])}")
            print(f"➖ NO_SIGNAL: {len(signals_df[signals_df['signal'] == 'NO_SIGNAL'])}")
            
            # Analyze by hour
            print(f"\n🕒 SIGNALS BY HOUR:")
            hourly_stats = signals_df.groupby('hour')['signal'].value_counts().unstack(fill_value=0)
            print(hourly_stats)
            
            # Analyze RSI patterns for BUY vs SELL signals
            if 'rsi' in signals_df.columns:
                buy_rsi = signals_df[signals_df['signal'] == 'BUY']['rsi']
                sell_rsi = signals_df[signals_df['signal'] == 'SELL']['rsi']
                
                print(f"\n📈 RSI ANALYSIS:")
                print(f"   BUY Signals - Avg RSI: {buy_rsi.mean():.1f}, Range: {buy_rsi.min():.1f}-{buy_rsi.max():.1f}")
                print(f"   SELL Signals - Avg RSI: {sell_rsi.mean():.1f}, Range: {sell_rsi.min():.1f}-{sell_rsi.max():.1f}")
            
            # Best performing hours
            best_hours = hourly_stats[['BUY', 'SELL']].sum(axis=1).nlargest(3)
            print(f"\n🎯 BEST TRADING HOURS:")
            for hour, count in best_hours.items():
                print(f"   {hour:02d}:00 - {count} signals")
            
            return signals_df
            
        except Exception as e:
            print(f"❌ Error analyzing signals: {e}")
            return None

def main():
    analyzer = SignalAnalyzer()
    analyzer.analyze_signal_patterns()

if __name__ == "__main__":
    main()