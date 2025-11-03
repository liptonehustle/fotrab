from utils.telegram_notifier import TelegramNotifier

def test_telegram():
    print("Testing Telegram notifications...")
    
    notifier = TelegramNotifier()
    
    # Test trade notification
    success1 = notifier.send_trade_notification("EURUSD", "BUY", 1.0850, 0.01, "1001")
    
    # Test signal notification  
    success2 = notifier.send_signal_notification("GBPUSD", "SELL", 1.2650, 
                                               {'rsi': 70.5, 'sma_10': 1.2640, 'stoch_k': 80.1})
    
    if success1 and success2:
        print("✅ All Telegram tests passed!")
    else:
        print("❌ Telegram tests failed - check credentials")

if __name__ == "__main__":
    test_telegram()