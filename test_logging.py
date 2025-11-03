from utils.logger import AdvancedLogger

def test_logging():
    print("Testing Advanced Logging System...")
    
    logger = AdvancedLogger()
    
    # Test trade logging
    test_trades = [
        {
            'symbol': 'EURUSD',
            'signal': 'BUY',
            'action': 'OPEN',
            'volume': 0.01,
            'entry_price': 1.0850,
            'balance': 5000.0,
            'equity': 5000.0,
            'ticket': '1001'
        },
        {
            'symbol': 'GBPUSD', 
            'signal': 'SELL',
            'action': 'OPEN',
            'volume': 0.02,
            'entry_price': 1.2650,
            'balance': 4980.0,
            'equity': 4985.0,
            'ticket': '1002'
        }
    ]
    
    for trade in test_trades:
        logger.log_trade(trade)
    
    # Test performance report
    performance = logger.get_performance_report()
    print(f"\nPerformance Report: {performance}")
    
    # Test trade history
    trades = logger.get_trade_history()
    print(f"\nTotal trades in log: {len(trades)}")

if __name__ == "__main__":
    test_logging()