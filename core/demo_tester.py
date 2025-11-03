import MetaTrader5 as mt5
import time
import pandas as pd
from datetime import datetime, timedelta
from config.settings import Config

class DemoTester:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        self.config = Config()
        self.trade_log = []
        self.start_balance = 0
        
    def run_demo_test(self, duration_hours=24, check_interval=300):
        """
        Run demo testing for specified duration
        duration_hours: Total test duration
        check_interval: Seconds between market checks
        """
        print(f"🚀 Starting Demo Test - Duration: {duration_hours} hours")
        
        if not self.mt5.connect():
            print("❌ Failed to connect to MT5")
            return
            
        # Get starting balance
        account_info = mt5.account_info()
        self.start_balance = account_info.balance
        print(f"💰 Starting Balance: ${self.start_balance:.2f}")
        print(f"⏰ Check Interval: {check_interval} seconds")
        print(f"🎯 Trading Pairs: {self.config.get_market_settings()['default_pairs']}")
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        trade_count = 0
        
        while time.time() < end_time:
            try:
                current_time = datetime.now()
                print(f"\n⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 50)
                
                # Check market and execute trades
                trades_executed = self._check_and_trade()
                trade_count += trades_executed
                
                # Print current status
                self._print_status()
                
                # Wait for next check
                print(f"💤 Waiting {check_interval} seconds...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n⏹️ Demo test stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry
        
        # Final report
        self._generate_report(trade_count, duration_hours)
        self.mt5.disconnect()
    
    def _check_and_trade(self):
        """Check market conditions and execute trades"""
        from core.market_data import MarketData
        from core.trading_strategy import TradingStrategy
        from core.trade_executor import TradeExecutor
        
        market_data = MarketData(self.mt5)
        strategy = TradingStrategy(market_data)
        executor = TradeExecutor(self.mt5)
        
        pairs = self.config.get_market_settings()['default_pairs']
        trades_executed = 0
        
        for pair in pairs:
            print(f"\n📊 Analyzing {pair}...")
            
            try:
                signal = strategy.analyze_market(pair)
                
                if signal != "NO_SIGNAL":
                    print(f"🚨 SIGNAL: {signal} {pair}")
                    
                    # Check if we should execute (avoid overtrading)
                    if self._should_execute_trade(pair, signal):
                        print(f"✅ EXECUTING: {signal} {pair}")
                        
                        # EXECUTE TRADE (REAL DEMO ACCOUNT)
                        if executor.execute_trade(pair, signal):
                            trades_executed += 1
                            # Log trade
                            self._log_trade(pair, signal, executor.open_positions[-1])
                        else:
                            print(f"❌ Trade execution failed for {pair}")
                    else:
                        print(f"⏸️ Skipping trade (cooldown/filter)")
                else:
                    print(f"➖ No signal for {pair}")
                    
            except Exception as e:
                print(f"❌ Error analyzing {pair}: {e}")
        
        return trades_executed
    
    def _should_execute_trade(self, symbol, signal):
        """Check if we should execute trade (avoid overtrading)"""
        # Check if we already have position for this symbol
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            print(f"⏸️ Already have position for {symbol}")
            return False
            
        # Check time-based cooldown (avoid multiple signals in short time)
        recent_trades = [t for t in self.trade_log 
                        if t['symbol'] == symbol 
                        and time.time() - t['timestamp'] < 600]  # 10 minutes cooldown
        
        if recent_trades:
            print(f"⏸️ Cooldown active for {symbol}")
            return False
            
        return True
    
    def _log_trade(self, symbol, signal, position_info):
        """Log trade details"""
        trade_data = {
            'timestamp': time.time(),
            'symbol': symbol,
            'signal': signal,
            'ticket': position_info.get('ticket'),
            'volume': position_info.get('volume'),
            'price': position_info.get('open_price'),
            'time': datetime.now().isoformat()
        }
        self.trade_log.append(trade_data)
        print(f"📝 Logged trade: {symbol} {signal} at {trade_data['price']}")
    
    def _print_status(self):
        """Print current trading status"""
        account_info = mt5.account_info()
        if account_info:
            current_balance = account_info.balance
            equity = account_info.equity
            positions = mt5.positions_get()
            
            print(f"\n📈 CURRENT STATUS:")
            print(f"   Balance: ${current_balance:.2f}")
            print(f"   Equity: ${equity:.2f}")
            print(f"   Open Positions: {len(positions) if positions else 0}")
            print(f"   Total Trades: {len(self.trade_log)}")
            
            if self.start_balance > 0:
                pnl = current_balance - self.start_balance
                pnl_percent = (pnl / self.start_balance) * 100
                print(f"   PnL: ${pnl:.2f} ({pnl_percent:+.2f}%)")
    
    def _generate_report(self, total_trades, duration_hours):
        """Generate final test report"""
        print("\n" + "="*60)
        print("📊 DEMO TESTING FINAL REPORT")
        print("="*60)
        
        account_info = mt5.account_info()
        if account_info:
            final_balance = account_info.balance
            total_pnl = final_balance - self.start_balance
            pnl_percent = (total_pnl / self.start_balance) * 100
            
            print(f"💰 Starting Balance: ${self.start_balance:.2f}")
            print(f"💰 Final Balance: ${final_balance:.2f}")
            print(f"📈 Total PnL: ${total_pnl:.2f} ({pnl_percent:+.2f}%)")
            print(f"🎯 Total Trades: {total_trades}")
            print(f"⏱️ Test Duration: {duration_hours} hours")
            print(f"📊 Avg Trades/Hour: {total_trades/duration_hours:.2f}" if duration_hours > 0 else "N/A")
            
            # Calculate win rate from closed positions
            if self.trade_log:
                print(f"📝 Trade Log Entries: {len(self.trade_log)}")
            
            # Risk Management Assessment
            max_drawdown = self._calculate_max_drawdown()
            print(f"📉 Max Drawdown: {max_drawdown:.2f}%")
            
            # Recommendations
            print("\n💡 RECOMMENDATIONS:")
            if total_trades == 0:
                print("   ⚠️ No trades executed - check strategy parameters")
            elif pnl_percent < -5:
                print("   ⚠️ Significant losses - review strategy")
            elif pnl_percent > 5:
                print("   ✅ Good performance - consider longer testing")
            else:
                print("   🔄 Moderate performance - continue testing")
    
    def _calculate_max_drawdown(self):
        """Calculate maximum drawdown during test"""
        # Simplified version - in real implementation, track equity curve
        account_info = mt5.account_info()
        if account_info:
            current_drawdown = (self.start_balance - account_info.equity) / self.start_balance * 100
            return max(0, current_drawdown)
        return 0
    
    def show_logs(self):
        """Show recent logs and performance"""
        from utils.logger import AdvancedLogger
        
        logger = AdvancedLogger()
        
        print("\n" + "="*50)
        print("📊 TRADING LOGS & PERFORMANCE")
        print("="*50)
        
        # Show performance
        performance = logger.get_performance_report()
        if performance:
            print(f"Total Trades: {performance['total_trades']}")
            print(f"Win Rate: {performance['win_rate']:.1f}%")
            print(f"Total Profit: ${performance['total_profit']:.2f}")
            print(f"Avg Profit/Trade: ${performance['avg_profit_per_trade']:.2f}")
            print(f"Max Drawdown: {performance['max_drawdown']:.1f}%")
        
        # Show recent trades
        recent_trades = logger.get_trade_history()[-5:]  # Last 5 trades
        if recent_trades:
            print(f"\n📝 Recent Trades (Last 5):")
            for trade in recent_trades:
                print(f"  {trade['date']} {trade['time']} - {trade['symbol']} {trade['action']} at {trade['entry_price']}")

# Test function
def test_demo():
    from core.mt5_connector import MT5Connector
    
    print("Testing Demo System...")
    connector = MT5Connector()
    tester = DemoTester(connector)
    
    # Run short test (1 hour) for demonstration
    tester.run_demo_test(duration_hours=1, check_interval=60)  # 1 hour test, check every 1 minute

if __name__ == "__main__":
    test_demo()