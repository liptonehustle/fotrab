import csv
import os
import json
from datetime import datetime
import time

class AdvancedLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.trade_log_file = f"{log_dir}/trades.csv"
        self.performance_log_file = f"{log_dir}/performance.json"
        self.setup_logging()
        
    def setup_logging(self):
        """Create log directory and files with headers"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create trades CSV with headers if not exists
        if not os.path.exists(self.trade_log_file):
            with open(self.trade_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'date', 'time', 'symbol', 'signal', 
                    'action', 'volume', 'entry_price', 'exit_price',
                    'profit', 'balance', 'equity', 'ticket', 'status'
                ])
        
        # Create performance JSON if not exists
        if not os.path.exists(self.performance_log_file):
            with open(self.performance_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "session_start": datetime.now().isoformat(),
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_profit": 0.0,
                    "peak_balance": 0.0,
                    "max_drawdown": 0.0,
                    "sessions": []
                }, f, indent=2)
    
    def log_trade(self, trade_data):
        """Log trade execution"""
        try:
            current_time = datetime.now()
            
            log_entry = {
                'timestamp': time.time(),
                'date': current_time.strftime('%Y-%m-%d'),
                'time': current_time.strftime('%H:%M:%S'),
                'symbol': trade_data.get('symbol', ''),
                'signal': trade_data.get('signal', ''),
                'action': trade_data.get('action', ''),
                'volume': trade_data.get('volume', 0),
                'entry_price': trade_data.get('entry_price', 0),
                'exit_price': trade_data.get('exit_price', 0),
                'profit': trade_data.get('profit', 0),
                'balance': trade_data.get('balance', 0),
                'equity': trade_data.get('equity', 0),
                'ticket': trade_data.get('ticket', ''),
                'status': trade_data.get('status', 'OPEN')
            }
            
            # Append to CSV
            with open(self.trade_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(log_entry.values())
            
            # Update performance JSON
            self._update_performance(log_entry)
            
            print(f"📝 Trade logged: {log_entry['symbol']} {log_entry['action']} at {log_entry['entry_price']}")
            
        except Exception as e:
            print(f"❌ Error logging trade: {e}")
    
    def _update_performance(self, trade_entry):
        """Update performance metrics"""
        try:
            with open(self.performance_log_file, 'r', encoding='utf-8') as f:
                performance = json.load(f)
            
            # Update metrics
            performance["total_trades"] += 1
            
            if trade_entry.get('profit', 0) > 0:
                performance["winning_trades"] += 1
            
            performance["total_profit"] += trade_entry.get('profit', 0)
            performance["peak_balance"] = max(
                performance.get("peak_balance", 0), 
                trade_entry.get('balance', 0)
            )
            
            # Calculate drawdown
            current_balance = trade_entry.get('balance', 0)
            peak = performance["peak_balance"]
            if peak > 0:
                drawdown = ((peak - current_balance) / peak) * 100
                performance["max_drawdown"] = max(performance["max_drawdown"], drawdown)
            
            # Save updated performance
            with open(self.performance_log_file, 'w', encoding='utf-8') as f:
                json.dump(performance, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error updating performance: {e}")
    
    def log_market_signal(self, symbol, signal, price, indicators):
        """Log market analysis signals (even if not executed)"""
        try:
            signal_file = f"{self.log_dir}/signals.csv"
            
            # Create file with headers if not exists
            if not os.path.exists(signal_file):
                with open(signal_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'date', 'time', 'symbol', 'signal',
                        'price', 'rsi', 'sma_10', 'sma_20', 'stoch_k', 'stoch_d'
                    ])
            
            current_time = datetime.now()
            signal_entry = [
                time.time(),
                current_time.strftime('%Y-%m-%d'),
                current_time.strftime('%H:%M:%S'),
                symbol,
                signal,
                price,
                indicators.get('rsi', 0),
                indicators.get('sma_10', 0),
                indicators.get('sma_20', 0),
                indicators.get('stoch_k', 0),
                indicators.get('stoch_d', 0)
            ]
            
            with open(signal_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(signal_entry)
                
            print(f"📊 Signal logged: {symbol} {signal}")
            
        except Exception as e:
            print(f"❌ Error logging signal: {e}")
    
    def get_trade_history(self, symbol=None, date=None):
        """Retrieve trade history with filters"""
        try:
            trades = []
            with open(self.trade_log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Apply filters
                    if symbol and row['symbol'] != symbol:
                        continue
                    if date and row['date'] != date:
                        continue
                    trades.append(row)
            return trades
        except Exception as e:
            print(f"❌ Error reading trade history: {e}")
            return []
    
    def get_performance_report(self):
        """Generate performance report"""
        try:
            with open(self.performance_log_file, 'r', encoding='utf-8') as f:
                performance = json.load(f)
            
            if performance["total_trades"] > 0:
                win_rate = (performance["winning_trades"] / performance["total_trades"]) * 100
                avg_profit = performance["total_profit"] / performance["total_trades"]
            else:
                win_rate = 0
                avg_profit = 0
            
            return {
                "total_trades": performance["total_trades"],
                "winning_trades": performance["winning_trades"],
                "win_rate": win_rate,
                "total_profit": performance["total_profit"],
                "avg_profit_per_trade": avg_profit,
                "max_drawdown": performance["max_drawdown"],
                "peak_balance": performance["peak_balance"]
            }
        except Exception as e:
            print(f"❌ Error generating performance report: {e}")
            return {}

# Test function
def test_logger():
    logger = AdvancedLogger()
    
    # Test trade logging
    test_trade = {
        'symbol': 'EURUSD',
        'signal': 'BUY',
        'action': 'OPEN',
        'volume': 0.01,
        'entry_price': 1.0850,
        'balance': 5000.0,
        'equity': 5000.0,
        'ticket': '12345'
    }
    
    logger.log_trade(test_trade)
    print("✅ Logger test completed")

if __name__ == "__main__":
    test_logger()