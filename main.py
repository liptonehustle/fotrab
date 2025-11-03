import MetaTrader5 as mt5
import time
from datetime import datetime
from core.mt5_connector import MT5Connector
from core.market_data import MarketData
from core.trading_strategy import TradingStrategy
from core.trade_executor import TradeExecutor
from core.position_manager import PositionManager
from core.demo_tester import DemoTester
from utils.logger import AdvancedLogger
from utils.telegram_notifier import TelegramNotifier

def main():
    print("🚀 MT5 AI SCALPING SYSTEM")
    print("=" * 50)
    
    # Show menu
    print("1. Quick Market Analysis")
    print("2. Demo Trading Test")
    print("3. Position Management")
    print("4. View Logs & Performance")
    print("5. Run Live Trading")
    print("6. Exit")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == "1":
        quick_analysis()
    elif choice == "2":
        demo_testing()
    elif choice == "3":
        position_management()
    elif choice == "4":
        view_logs()
    elif choice == "5":
        live_trading()
    elif choice == "6":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice!")
        main()

def quick_analysis():
    """Quick market analysis without trading"""
    print("\n" + "="*50)
    print("QUICK MARKET ANALYSIS")
    print("="*50)
    
    connector = MT5Connector()
    
    if connector.connect():
        market_data = MarketData(connector)
        strategy = TradingStrategy(market_data)
        logger = AdvancedLogger()
        
        pairs = connector.config.get_market_settings()['default_pairs']
        
        for pair in pairs:
            print(f"\n🎯 Analyzing {pair}...")
            signal = strategy.analyze_market(pair)
            
            if signal != "NO_SIGNAL":
                print(f"🚨 TRADING SIGNAL: {signal} {pair}")
            else:
                print(f"➖ No signal for {pair}")
        
        # Show performance summary
        performance = logger.get_performance_report()
        print(f"\n📊 Historical Performance:")
        print(f"   Total Trades: {performance['total_trades']}")
        print(f"   Win Rate: {performance['win_rate']:.1f}%")
        print(f"   Total Profit: ${performance['total_profit']:.2f}")
        
        connector.disconnect()
    else:
        print("❌ Connection failed!")
    
    input("\nPress Enter to continue...")
    main()

def demo_testing():
    """Run demo trading test"""
    print("\n" + "="*50)
    print("DEMO TRADING TEST")
    print("="*50)
    
    print("1. Quick Test (5 minutes)")
    print("2. Short Test (1 hour)")
    print("3. Full Test (24 hours)")
    print("4. Back to Main Menu")
    
    choice = input("\nSelect test duration: ").strip()
    
    connector = MT5Connector()
    
    if choice == "1":
        tester = DemoTester(connector)
        tester.run_demo_test(duration_hours=0.08, check_interval=30)  # 5 minutes
    elif choice == "2":
        tester = DemoTester(connector)
        tester.run_demo_test(duration_hours=1, check_interval=60)  # 1 hour
    elif choice == "3":
        tester = DemoTester(connector)
        tester.run_demo_test(duration_hours=24, check_interval=300)  # 24 hours
    elif choice == "4":
        main()
        return
    else:
        print("❌ Invalid choice!")
    
    input("\nPress Enter to continue...")
    main()

def position_management():
    """Manage open positions"""
    print("\n" + "="*50)
    print("POSITION MANAGEMENT")
    print("="*50)
    
    connector = MT5Connector()
    
    if connector.connect():
        executor = TradeExecutor(connector)
        manager = PositionManager(connector, executor)
        logger = AdvancedLogger()
        
        # Get position summary
        summary = manager.get_position_summary()
        
        if summary['total_positions'] > 0:
            print(f"📊 Open Positions: {summary['total_positions']}")
            print("-" * 40)
            
            for pos in summary['positions']:
                profit_color = "🟢" if pos['profit_pips'] > 0 else "🔴"
                print(f"{profit_color} {pos['symbol']} {pos['type']}")
                print(f"   Volume: {pos['volume']}")
                print(f"   Open Price: {pos['open_price']:.5f}")
                print(f"   Current Price: {pos['current_price']:.5f}")
                print(f"   Profit: {pos['profit_pips']:.1f} pips (${pos['profit_usd']:.2f})")
                print(f"   Age: {pos['age_minutes']:.1f} minutes")
                print()
            
            # Manage positions
            print("🔍 Managing positions (TP/SL/Time-based close)...")
            manager.manage_open_positions()
            
        else:
            print("📊 No open positions")
        
        # Show performance
        performance = logger.get_performance_report()
        closed_trades = logger.get_trade_history()
        closed_trades = [t for t in closed_trades if t.get('status') == 'CLOSED']
        
        if closed_trades:
            print(f"\n📝 Recently Closed Trades:")
            for trade in closed_trades[-3:]:
                profit = float(trade.get('profit', 0))
                profit_str = f"+${profit:.2f}" if profit > 0 else f"${profit:.2f}"
                print(f"   {trade['date']} {trade['time']} - {trade['symbol']}: {profit_str}")
        
        connector.disconnect()
    else:
        print("❌ Connection failed!")
    
    input("\nPress Enter to continue...")
    main()

def view_logs():
    """View trading logs and performance"""
    print("\n" + "="*50)
    print("TRADING LOGS & PERFORMANCE")
    print("="*50)
    
    logger = AdvancedLogger()
    
    # Performance summary
    performance = logger.get_performance_report()
    print("🎯 PERFORMANCE SUMMARY:")
    print(f"   Total Trades: {performance['total_trades']}")
    print(f"   Winning Trades: {performance['winning_trades']}")
    print(f"   Win Rate: {performance['win_rate']:.1f}%")
    print(f"   Total Profit: ${performance['total_profit']:.2f}")
    print(f"   Average Profit/Trade: ${performance['avg_profit_per_trade']:.2f}")
    print(f"   Max Drawdown: {performance['max_drawdown']:.1f}%")
    print(f"   Peak Balance: ${performance['peak_balance']:.2f}")
    
    # Recent trades
    trades = logger.get_trade_history()
    if trades:
        print(f"\n📝 RECENT TRADES (Last 10):")
        for trade in trades[-10:]:
            status = trade.get('status', 'OPEN')
            profit = float(trade.get('profit', 0))
            profit_str = f"Profit: ${profit:.2f}" if profit != 0 else ""
            status_icon = "🟢" if profit > 0 else "🔴" if profit < 0 else "🟡"
            print(f"   {status_icon} {trade['date']} {trade['time']} - "
                  f"{trade['symbol']} {trade.get('action', '')} {profit_str} ({status})")
    
    # Recent signals
    try:
        import pandas as pd
        signals_df = pd.read_csv('logs/signals.csv')
        if not signals_df.empty:
            print(f"\n📈 RECENT SIGNALS (Last 5):")
            recent_signals = signals_df.tail()
            for _, signal in recent_signals.iterrows():
                signal_icon = "🚨" if signal['signal'] != 'NO_SIGNAL' else "➖"
                print(f"   {signal_icon} {signal['date']} {signal['time']} - "
                      f"{signal['symbol']} {signal['signal']} (RSI: {signal['rsi']:.1f})")
    except FileNotFoundError:
        print("\n📈 No signals logged yet")
    except Exception as e:
        print(f"\n📈 Error reading signals: {e}")
    
    input("\nPress Enter to continue...")
    main()

def live_trading():
    """Live trading mode (USE WITH CAUTION)"""
    print("\n" + "="*50)
    print("🚨 LIVE TRADING MODE")
    print("="*50)
    print("⚠️  WARNING: This will execute real trades!")
    print("⚠️  Make sure you're using DEMO account!")
    print("="*50)
    
    confirm = input("Type 'YES' to confirm live trading: ").strip()
    
    if confirm != 'YES':
        print("❌ Live trading cancelled!")
        main()
        return
    
    print("\n🔧 Starting Live Trading System...")
    
    connector = MT5Connector()
    
    if connector.connect():
        market_data = MarketData(connector)
        strategy = TradingStrategy(market_data)
        executor = TradeExecutor(connector)
        manager = PositionManager(connector, executor)
        logger = AdvancedLogger()
        notifier = TelegramNotifier()
        
        # ✅ SEND STARTUP NOTIFICATION
        account_info = mt5.account_info()
        if account_info:
            notifier.send_startup_notification(
                account_info={
                    'server': connector.config.get_broker_settings()['server'],
                    'login': account_info.login,
                    'balance': account_info.balance,
                    'equity': account_info.equity
                },
                pairs=connector.config.get_market_settings()['default_pairs']
            )
        
        print("✅ Live Trading Activated!")
        print("💡 System will run until stopped (Ctrl+C)")
        
        start_time = time.time()
        trade_count = 0
        
        try:
            while True:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n⏰ {current_time}")
                print("-" * 40)
                
                # Manage existing positions
                manager.manage_open_positions()
                
                # Analyze market for new signals
                pairs = connector.config.get_market_settings()['default_pairs']
                trades_this_cycle = 0
                
                for pair in pairs:
                    signal = strategy.analyze_market(pair)
                    
                    if signal != "NO_SIGNAL":
                        print(f"🚨 EXECUTING: {signal} {pair}")
                        
                        # Execute real trade
                        if executor.execute_trade(pair, signal):
                            print(f"✅ Trade executed successfully!")
                            trades_this_cycle += 1
                            trade_count += 1
                        else:
                            print(f"❌ Trade execution failed!")
                
                # Show status
                account_info = mt5.account_info()
                if account_info:
                    print(f"\n📊 Status: {trade_count} trades executed | Balance: ${account_info.balance:.2f}")
                
                # Wait before next iteration
                print(f"💤 Waiting 60 seconds...")
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n⏹️ Live trading stopped by user")
            
            # ✅ SEND SHUTDOWN NOTIFICATION
            duration_minutes = (time.time() - start_time) / 60
            performance = logger.get_performance_report()
            notifier.send_shutdown_notification(duration_minutes, performance)
            
        except Exception as e:
            print(f"❌ Error in live trading: {e}")
            
            # ✅ SEND ERROR NOTIFICATION
            notifier.send_error_notification(str(e))
        
        finally:
            connector.disconnect()
    
    else:
        print("❌ Connection failed!")
    
    input("\nPress Enter to continue...")
    main()

if __name__ == "__main__":
    main()