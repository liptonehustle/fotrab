from utils.logger import AdvancedLogger
import pandas as pd
from datetime import datetime

def view_logs():
    logger = AdvancedLogger()
    
    print("📊 TRADING LOGS VIEWER")
    print("="*50)
    
    # Show performance
    performance = logger.get_performance_report()
    if performance:
        print("🎯 PERFORMANCE SUMMARY:")
        print(f"   Total Trades: {performance['total_trades']}")
        print(f"   Winning Trades: {performance['winning_trades']}")
        print(f"   Win Rate: {performance['win_rate']:.1f}%")
        print(f"   Total Profit: ${performance['total_profit']:.2f}")
        print(f"   Avg Profit/Trade: ${performance['avg_profit_per_trade']:.2f}")
        print(f"   Max Drawdown: {performance['max_drawdown']:.1f}%")
        print(f"   Peak Balance: ${performance['peak_balance']:.2f}")
    
    # Show all trades
    trades = logger.get_trade_history()
    if trades:
        print(f"\n📝 ALL TRADES ({len(trades)} total):")
        for trade in trades[-10:]:  # Show last 10 trades
            profit_str = f"Profit: ${float(trade.get('profit', 0)):.2f}" if trade.get('profit') else ""
            print(f"   {trade['date']} {trade['time']} - {trade['symbol']} {trade['action']} "
                  f"at {trade.get('entry_price', 'N/A')} {profit_str}")
    
    # Show recent signals
    try:
        signals_df = pd.read_csv('logs/signals.csv')
        if not signals_df.empty:
            print(f"\n📈 RECENT SIGNALS ({len(signals_df)} total):")
            recent_signals = signals_df.tail(5)
            for _, signal in recent_signals.iterrows():
                print(f"   {signal['date']} {signal['time']} - {signal['symbol']} {signal['signal']} "
                      f"(RSI: {signal['rsi']:.1f})")
    except FileNotFoundError:
        print("\n📈 No signals logged yet")
    except Exception as e:
        print(f"\n❌ Error reading signals: {e}")

if __name__ == "__main__":
    view_logs()